from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.document import Document
from app.models.patient import Patient


router = APIRouter(
    prefix="/patients",
    tags=["Documents"],
)


UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)


@router.post("/{patient_id}/documents", status_code=201)
async def upload_document(
    patient_id: int,
    file: UploadFile = File(...),
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    if file.content_type != "application/pdf":
        raise HTTPException(
            status_code=400,
            detail="Only PDF files are supported",
        )

    file_path = UPLOAD_DIR / file.filename

    content = await file.read()
    file_path.write_bytes(content)

    document = Document(
        patient_id=patient_id,
        filename=file.filename,
        file_path=str(file_path),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    return {
        "message": "Document uploaded successfully",
        "document_id": document.id,
        "patient_id": patient_id,
        "filename": document.filename,
    }