from app.db.neo4j import driver


def get_patient_timeline(patient_id: int):
    query = """
    MATCH (p:Patient {patient_id: toString($patient_id)})
    OPTIONAL MATCH (p)-[:HAS_REPORT]->(r:Report)

    OPTIONAL MATCH (r)-[:CONTAINS]->(o:Observation)
    OPTIONAL MATCH (r)-[:PRESCRIBES]->(m:Medication)
    OPTIONAL MATCH (r)-[:RECORDS]->(t:TreatmentEvent)

    RETURN
        r.document_id AS document_id,
        r.report_date AS report_date,
        r.filename AS filename,
        r.document_type AS document_type,

        collect(DISTINCT {
            test_name: o.test_name,
            value: o.value,
            unit: o.unit,
            observation_date: o.observation_date
        }) AS observations,

        collect(DISTINCT {
            name: m.name,
            dosage: m.dosage,
            frequency: m.frequency,
            start_date: m.start_date,
            end_date: m.end_date
        }) AS medications,

        collect(DISTINCT {
            event_type: t.event_type,
            description: t.description,
            event_date: t.event_date
        }) AS treatment_events

    ORDER BY report_date ASC
    """

    with driver.session() as session:
        result = session.run(
            query,
            patient_id=patient_id,
        )

        return [record.data() for record in result]