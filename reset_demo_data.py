"""
RESET DEMO DATA
----------------
Deletes all application/demo data while preserving:

- PostgreSQL tables/schema
- PostgreSQL indexes
- Neo4j database itself
- Neo4j indexes
- Neon Object Storage bucket
- application configuration

After reset, a fresh demo user with ID=1 is created.

WARNING:
This is DESTRUCTIVE. It deletes ALL current patient/document data.
"""

import os
import sys

from dotenv import load_dotenv

load_dotenv()


# ---------------------------------------------------------
# Configuration
# ---------------------------------------------------------

DATABASE_URL = os.getenv("DATABASE_URL")

NEO4J_URI = os.getenv("NEO4J_URI")
NEO4J_USERNAME = os.getenv("NEO4J_USERNAME")
NEO4J_PASSWORD = os.getenv("NEO4J_PASSWORD")

AWS_ACCESS_KEY_ID = os.getenv("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.getenv("AWS_SECRET_ACCESS_KEY")
AWS_REGION = os.getenv("AWS_REGION")
AWS_ENDPOINT_URL_S3 = os.getenv("AWS_ENDPOINT_URL_S3")
AWS_S3_BUCKET = os.getenv("AWS_S3_BUCKET", "patient-reports")


# ---------------------------------------------------------
# Safety check
# ---------------------------------------------------------

print("=" * 60)
print("PATIENT PROGRESS TRACKER — DEMO DATA RESET")
print("=" * 60)

print()
print("THIS WILL DELETE:")
print("  • All PostgreSQL application data")
print("  • All Neo4j nodes and relationships")
print("  • All PDFs from Neon Object Storage")
print()
print("THIS WILL KEEP:")
print("  • Database schema")
print("  • Database tables")
print("  • Indexes")
print("  • Neo4j vector index")
print("  • Object Storage bucket")
print("  • Environment configuration")
print()

confirmation = input("Type RESET to continue: ").strip()

if confirmation != "RESET":
    print("\nReset cancelled.")
    sys.exit(0)


# ---------------------------------------------------------
# 1. Reset Neo4j
# ---------------------------------------------------------

print("\n[1/3] Resetting Neo4j...")

# Your Neo4j connection previously required this TLS workaround.
try:
    import certifi

    os.environ["SSL_CERT_FILE"] = certifi.where()
except ImportError:
    pass

from neo4j import GraphDatabase

if not all([
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD,
]):
    raise RuntimeError("Neo4j configuration is incomplete.")


neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
)

try:
    with neo4j_driver.session() as session:

        result = session.run(
            """
            MATCH (n)
            DETACH DELETE n
            RETURN count(n) AS deleted_nodes
            """
        )

        record = result.single()

        deleted_nodes = (
            record["deleted_nodes"]
            if record
            else 0
        )

    print(f"    Deleted Neo4j nodes: {deleted_nodes}")

finally:
    neo4j_driver.close()


# ---------------------------------------------------------
# 2. Reset Neon Object Storage
# ---------------------------------------------------------

print("\n[2/3] Resetting Neon Object Storage...")

import boto3
from botocore.client import Config


if not all([
    AWS_ACCESS_KEY_ID,
    AWS_SECRET_ACCESS_KEY,
    AWS_REGION,
    AWS_ENDPOINT_URL_S3,
    AWS_S3_BUCKET,
]):
    raise RuntimeError(
        "Neon Object Storage configuration is incomplete."
    )


s3_client = boto3.client(
    "s3",
    endpoint_url=AWS_ENDPOINT_URL_S3,
    aws_access_key_id=AWS_ACCESS_KEY_ID,
    aws_secret_access_key=AWS_SECRET_ACCESS_KEY,
    region_name=AWS_REGION,
    config=Config(signature_version="s3v4"),
)


deleted_objects = 0

paginator = s3_client.get_paginator("list_objects_v2")

for page in paginator.paginate(Bucket=AWS_S3_BUCKET):

    objects = page.get("Contents", [])

    if not objects:
        continue

    keys = [
        {"Key": obj["Key"]}
        for obj in objects
    ]

    s3_client.delete_objects(
        Bucket=AWS_S3_BUCKET,
        Delete={
            "Objects": keys,
        },
    )

    deleted_objects += len(keys)


print(f"    Deleted Object Storage objects: {deleted_objects}")


# ---------------------------------------------------------
# 3. Reset PostgreSQL
# ---------------------------------------------------------

print("\n[3/3] Resetting PostgreSQL...")

from sqlalchemy import create_engine, text


if not DATABASE_URL:
    raise RuntimeError("DATABASE_URL is not configured.")


engine = create_engine(DATABASE_URL)


with engine.begin() as connection:

    # -----------------------------------------------------
    # Delete dependent/child records first
    # -----------------------------------------------------

    tables = [
        "document_chunks",
        "observations",
        "medications",
        "treatment_events",
        "documents",
        "patients",
        "users",
    ]

    for table in tables:

        result = connection.execute(
            text(f'DELETE FROM "{table}"')
        )

        print(
            f"    {table}: "
            f"{result.rowcount if result.rowcount is not None else 0} deleted"
        )


    # -----------------------------------------------------
    # Reset PostgreSQL sequences
    # -----------------------------------------------------

    sequence_tables = [
        "document_chunks",
        "observations",
        "medications",
        "treatment_events",
        "documents",
        "patients",
        "users",
    ]

    for table in sequence_tables:

        sequence_result = connection.execute(
            text(
                """
                SELECT pg_get_serial_sequence(
                    :table_name,
                    'id'
                )
                """
            ),
            {
                "table_name": table,
            },
        )

        sequence_name = sequence_result.scalar()

        if sequence_name:

            connection.execute(
                text(
                    """
                    SELECT setval(
                        :sequence_name,
                        1,
                        false
                    )
                    """
                ),
                {
                    "sequence_name": sequence_name,
                },
            )


    # -----------------------------------------------------
    # Create fresh demo user
    # -----------------------------------------------------

    connection.execute(
        text(
            """
            INSERT INTO users (
                id,
                name,
                email,
                role
            )
            VALUES (
                1,
                'Demo Doctor',
                'demo@patienttracker.local',
                'doctor'
            )
            """
        )
    )


# ---------------------------------------------------------
# Verification
# ---------------------------------------------------------

print("\n" + "=" * 60)
print("VERIFYING RESET")
print("=" * 60)


# PostgreSQL verification

with engine.connect() as connection:

    tables = [
        "users",
        "patients",
        "documents",
        "document_chunks",
        "observations",
        "medications",
        "treatment_events",
    ]

    for table in tables:

        result = connection.execute(
            text(f'SELECT COUNT(*) FROM "{table}"')
        )

        count = result.scalar()

        print(f"  PostgreSQL {table}: {count}")


# Neo4j verification

neo4j_driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
)

try:

    with neo4j_driver.session() as session:

        nodes_result = session.run(
            """
            MATCH (n)
            RETURN count(n) AS count
            """
        )

        nodes = nodes_result.single()["count"]

        relationships_result = session.run(
            """
            MATCH ()-[r]->()
            RETURN count(r) AS count
            """
        )

        relationships = relationships_result.single()["count"]

    print(f"  Neo4j nodes: {nodes}")
    print(f"  Neo4j relationships: {relationships}")

finally:
    neo4j_driver.close()


engine.dispose()


print("\n" + "=" * 60)
print("RESET COMPLETE")
print("=" * 60)

print()
print("Fresh demo user:")
print("  ID:    1")
print("  Name:  Demo Doctor")
print("  Email: demo@patienttracker.local")
print("  Role:  doctor")
print()
print("You can now start adding fresh patients.")
print("=" * 60)