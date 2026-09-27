from app.db.neo4j import driver


def get_patient_timeline(patient_id: int):
    query = """
    MATCH (p:Patient {patient_id: $patient_id})
          -[:HAS_REPORT]->
          (r:Report)
          -[:CONTAINS]->
          (o:Observation)

    RETURN
        r.document_id AS document_id,
        r.report_date AS report_date,
        r.document_type AS document_type,
        o.test_name AS test_name,
        o.value AS value,
        o.unit AS unit,
        o.observation_date AS observation_date

    ORDER BY
        report_date ASC,
        test_name ASC
    """

    with driver.session() as session:
        result = session.run(
            query,
            patient_id=str(patient_id),
        )

        return [dict(record) for record in result]