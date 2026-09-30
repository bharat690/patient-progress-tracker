from sqlalchemy.orm import Session

from app.services.observations import get_patient_observations


def get_patient_trend(db: Session, patient_id: int, test_name: str):
    return [
        {
            "document_id": row["document_id"],
            "report_date": row["report_date"],
            "filename": row["filename"],
            "test_name": row["test_name"],
            "value": row["value"],
            "unit": row["unit"],
            "observation_date": row["observation_date"],
        }
        for row in get_patient_observations(db, patient_id, test_name)
    ]