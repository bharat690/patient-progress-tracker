from app.db.neo4j import driver

query = """
MATCH (p:Patient {patient_id: $patient_id})
      -[:HAS_REPORT]->
      (r:Report)
      -[:PRESCRIBES]->
      (m:Medication)

RETURN
    p.name AS patient,
    r.document_id AS document_id,
    r.report_date AS report_date,
    m.medication_id AS medication_id,
    m.name AS medication,
    m.dosage AS dosage,
    m.frequency AS frequency,
    m.start_date AS start_date,
    m.end_date AS end_date

ORDER BY report_date, medication
"""

with driver.session() as session:
    result = session.run(query, patient_id="4")

    for record in result:
        print(dict(record))

driver.close()