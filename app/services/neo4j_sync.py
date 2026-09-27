from sqlalchemy.orm import Session

from app.db.neo4j import driver
from app.models.document import Document
from app.models.medication import Medication
from app.models.observation import Observation
from app.models.patient import Patient
from app.models.treatment_event import TreatmentEvent


def sync_document_to_neo4j(
    db: Session,
    document_id: int,
) -> None:

    document = db.get(Document, document_id)

    if document is None:
        raise ValueError(f"Document {document_id} not found")

    patient = db.get(Patient, document.patient_id)

    if patient is None:
        raise ValueError(
            f"Patient {document.patient_id} not found"
        )

    observations = (
        db.query(Observation)
        .filter(
            Observation.document_id == document.id
        )
        .all()
    )

    medications = (
        db.query(Medication)
        .filter(
            Medication.document_id == document.id
        )
        .all()
    )

    treatment_events = (
        db.query(TreatmentEvent)
        .filter(
            TreatmentEvent.document_id == document.id
        )
        .all()
    )

    with driver.session() as session:

        # --------------------------------------------------
        # Patient
        # --------------------------------------------------

        session.run(
            """
            MERGE (p:Patient {patient_id: $patient_id})

            SET p.name = $name,
                p.date_of_birth = $date_of_birth,
                p.gender = $gender
            """,
            patient_id=str(patient.id),
            name=patient.name,
            date_of_birth=patient.date_of_birth,
            gender=patient.gender,
        )

        # --------------------------------------------------
        # Report
        # --------------------------------------------------

        session.run(
            """
            MATCH (p:Patient {patient_id: $patient_id})

            MERGE (r:Report {document_id: $document_id})

            SET r.filename = $filename,
                r.document_type = $document_type,
                r.report_date = $report_date

            MERGE (p)-[:HAS_REPORT]->(r)
            """,
            patient_id=str(patient.id),
            document_id=str(document.id),
            filename=document.filename,
            document_type=document.document_type,
            report_date=document.report_date,
        )

        # --------------------------------------------------
        # Observations
        # --------------------------------------------------

        for observation in observations:

            session.run(
                """
                MATCH (r:Report {document_id: $document_id})

                MERGE (o:Observation {
                    observation_id: $observation_id
                })

                SET o.test_name = $test_name,
                    o.value = $value,
                    o.unit = $unit,
                    o.observation_date = $observation_date

                MERGE (r)-[:CONTAINS]->(o)
                """,
                document_id=str(document.id),
                observation_id=str(observation.id),
                test_name=observation.test_name,
                value=observation.value,
                unit=observation.unit,
                observation_date=observation.observation_date,
            )

        # --------------------------------------------------
        # Medications
        # --------------------------------------------------

        for medication in medications:

            session.run(
                """
                MATCH (p:Patient {patient_id: $patient_id})
                MATCH (r:Report {document_id: $document_id})

                MERGE (m:Medication {
                    medication_id: $medication_id
                })

                SET m.name = $name,
                    m.dosage = $dosage,
                    m.frequency = $frequency,
                    m.start_date = $start_date,
                    m.end_date = $end_date

                MERGE (r)-[:PRESCRIBES]->(m)
                MERGE (p)-[:TAKES]->(m)
                """,
                patient_id=str(patient.id),
                document_id=str(document.id),
                medication_id=str(medication.id),
                name=medication.name,
                dosage=medication.dosage,
                frequency=medication.frequency,
                start_date=medication.start_date,
                end_date=medication.end_date,
            )

        # --------------------------------------------------
        # Treatment Events
        # --------------------------------------------------

        for event in treatment_events:

            session.run(
                """
                MATCH (p:Patient {patient_id: $patient_id})
                MATCH (r:Report {document_id: $document_id})

                MERGE (t:TreatmentEvent {
                    treatment_event_id: $treatment_event_id
                })

                SET t.event_type = $event_type,
                    t.description = $description,
                    t.event_date = $event_date

                MERGE (r)-[:RECORDS]->(t)
                MERGE (p)-[:HAS_TREATMENT_EVENT]->(t)
                """,
                patient_id=str(patient.id),
                document_id=str(document.id),
                treatment_event_id=str(event.id),
                event_type=event.event_type,
                description=event.description,
                event_date=event.event_date,
            )   