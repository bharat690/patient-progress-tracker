from sqlalchemy.orm import Session

from app.models.medication import Medication
from app.models.observation import Observation
from app.models.treatment_event import TreatmentEvent
from app.schemas.medical import MedicalExtraction


def persist_medical_data(
    db: Session,
    patient_id: int,
    document_id: int,
    extraction: MedicalExtraction,
) -> None:
    for item in extraction.observations:
        observation = Observation(
            patient_id=patient_id,
            document_id=document_id,
            test_name=item.test_name,
            value=item.value,
            unit=item.unit,
            observation_date=item.observation_date,
        )

        db.add(observation)

    for item in extraction.medications:
        medication = Medication(
            patient_id=patient_id,
            document_id=document_id,
            name=item.name,
            dosage=item.dosage,
            frequency=item.frequency,
            start_date=item.start_date,
            end_date=item.end_date,
        )

        db.add(medication)

    for item in extraction.treatment_events:
        treatment_event = TreatmentEvent(
            patient_id=patient_id,
            document_id=document_id,
            event_type=item.event_type,
            description=item.description,
            event_date=item.event_date,
        )

        db.add(treatment_event)

    db.commit()