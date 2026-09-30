from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.core.dates import normalize_date
from app.models.document import Document
from app.models.observation import Observation


def get_patient_observations(
    db: Session,
    patient_id: int,
    test_name: str | None = None,
) -> list[dict]:
    statement = (
        select(Observation, Document)
        .join(Document, Observation.document_id == Document.id)
        .where(Observation.patient_id == patient_id)
    )

    if test_name:
        statement = statement.where(
            func.lower(Observation.test_name) == test_name.strip().lower()
        )

    rows = db.execute(
        statement.order_by(Observation.id.asc())
    ).all()

    observations = []
    for observation, document in rows:
        report_date = (
            normalize_date(document.report_date)
            or normalize_date(observation.observation_date)
        )
        if report_date is None or observation.value is None:
            continue

        observations.append({
            "id": observation.id,
            "test_name": observation.test_name,
            "value": observation.value,
            "unit": observation.unit,
            "report_date": report_date,
            "observation_date": normalize_date(
                observation.observation_date
            ),
            "document_id": document.id,
            "filename": document.filename,
        })

    observations.sort(
        key=lambda item: (
            item["test_name"].casefold(),
            item["report_date"],
            item["document_id"],
            item["id"],
        )
    )

    unique_observations = []
    seen = set()
    for observation in observations:
        key = (
            observation["test_name"].casefold(),
            observation["report_date"],
        )
        if key in seen:
            continue

        seen.add(key)
        unique_observations.append(observation)

    return unique_observations
