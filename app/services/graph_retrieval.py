from app.db.neo4j import driver


def get_patient_context(patient_id: int):

    query = """
    MATCH (p:Patient {patient_id: $patient_id})

    OPTIONAL MATCH (p)-[:HAS_REPORT]->(r:Report)

    OPTIONAL MATCH (r)-[:CONTAINS]->(o:Observation)

    OPTIONAL MATCH (r)-[:PRESCRIBES]->(m:Medication)

    OPTIONAL MATCH (r)-[:RECORDS]->(t:TreatmentEvent)

    RETURN
        r.document_id AS document_id,
        r.report_date AS report_date,
        r.filename AS filename,

        collect(DISTINCT {
            test: o.test_name,
            value: o.value,
            unit: o.unit,
            date: o.observation_date
        }) AS observations,

        collect(DISTINCT {
            name: m.name,
            dosage: m.dosage,
            frequency: m.frequency,
            start_date: m.start_date,
            end_date: m.end_date
        }) AS medications,

        collect(DISTINCT {
            type: t.event_type,
            description: t.description,
            date: t.event_date
        }) AS treatment_events

    ORDER BY report_date
    """

    with driver.session() as session:

        result = session.run(
            query,
            patient_id=str(patient_id),
        )

        return [dict(record) for record in result]