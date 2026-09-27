from app.db.neo4j import driver


def get_patient_trend(patient_id: int, test_name: str):
    query = """
    MATCH (p:Patient {patient_id: toString($patient_id)})
          -[:HAS_REPORT]->(r:Report)
          -[:CONTAINS]->(o:Observation)

    WHERE toLower(o.test_name) = toLower($test_name)

    RETURN
        r.document_id AS document_id,
        r.report_date AS report_date,
        r.filename AS filename,
        o.test_name AS test_name,
        o.value AS value,
        o.unit AS unit,
        o.observation_date AS observation_date

    ORDER BY r.report_date ASC
    """

    with driver.session() as session:
        result = session.run(
            query,
            patient_id=patient_id,
            test_name=test_name,
        )

        return [record.data() for record in result]