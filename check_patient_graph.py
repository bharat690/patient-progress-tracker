from app.db.neo4j import driver

with driver.session() as session:
    result = session.run("""
        MATCH (p:Patient)
        RETURN p.patient_id AS patient_id
        ORDER BY p.patient_id
    """)

    print("Patients in Neo4j:")
    for record in result:
        print(record.data())

driver.close()