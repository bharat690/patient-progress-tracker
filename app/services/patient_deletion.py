import logging
from pathlib import Path

from sqlalchemy import delete, select
from sqlalchemy.orm import Session

from app.db.neo4j import driver
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.medication import Medication
from app.models.observation import Observation
from app.models.patient import Patient
from app.models.treatment_event import TreatmentEvent
from app.services.object_storage import delete_files

logger = logging.getLogger(__name__)
UPLOAD_DIR = Path("uploads")


def delete_patient_records(db: Session, patient: Patient) -> None:
    documents = db.scalars(
        select(Document).where(Document.patient_id == patient.id)
    ).all()
    document_ids = [document.id for document in documents]
    storage_keys = [
        document.storage_key
        for document in documents
        if document.storage_key
    ]
    file_paths = {Path(document.file_path) for document in documents}
    shared_file_paths = set()
    if file_paths:
        shared_file_paths = set(
            db.scalars(
                select(Document.file_path).where(
                    Document.patient_id != patient.id,
                    Document.file_path.in_([str(path) for path in file_paths]),
                )
            ).all()
        )

    try:
        if document_ids:
            db.execute(
                delete(DocumentChunk).where(
                    DocumentChunk.document_id.in_(document_ids)
                )
            )

        db.execute(
            delete(Observation).where(Observation.patient_id == patient.id)
        )
        db.execute(
            delete(Medication).where(Medication.patient_id == patient.id)
        )
        db.execute(
            delete(TreatmentEvent).where(
                TreatmentEvent.patient_id == patient.id
            )
        )
        db.execute(delete(Document).where(Document.patient_id == patient.id))
        db.delete(patient)
        db.flush()

        with driver.session() as session:
            session.run(
                """
                MATCH (p:Patient {patient_id: $patient_id})
                OPTIONAL MATCH (p)-[:HAS_REPORT]->(r:Report)
                OPTIONAL MATCH (r)-[:CONTAINS|PRESCRIBES|RECORDS|HAS_CHUNK]->(entity)
                WITH collect(DISTINCT p)
                     + collect(DISTINCT r)
                     + collect(DISTINCT entity) AS nodes
                UNWIND nodes AS node
                DETACH DELETE node
                """,
                patient_id=str(patient.id),
            )

        delete_files(storage_keys)
        db.commit()
    except Exception:
        db.rollback()
        logger.exception("Failed to delete all records for patient %s", patient.id)
        raise

    upload_root = UPLOAD_DIR.resolve()
    for file_path in file_paths:
        if str(file_path) in shared_file_paths:
            continue
        resolved_path = file_path.resolve()
        try:
            resolved_path.relative_to(upload_root)
        except ValueError:
            logger.warning(
                "Skipping patient upload outside the uploads directory: %s",
                resolved_path,
            )
            continue
        try:
            resolved_path.unlink(missing_ok=True)
        except OSError:
            logger.exception(
                "Failed to remove local upload for deleted patient %s: %s",
                patient.id,
                resolved_path,
            )
