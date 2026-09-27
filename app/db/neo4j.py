from neo4j import GraphDatabase

from app.core.config import (
    NEO4J_PASSWORD,
    NEO4J_URI,
    NEO4J_USERNAME,
)


if not all([
    NEO4J_URI,
    NEO4J_USERNAME,
    NEO4J_PASSWORD,
]):
    raise RuntimeError("Neo4j configuration is incomplete")


driver = GraphDatabase.driver(
    NEO4J_URI,
    auth=(NEO4J_USERNAME, NEO4J_PASSWORD),
)


def verify_neo4j():
    driver.verify_connectivity()
    return True


def close_neo4j():
    driver.close()