from pathlib import Path

from fastapi import APIRouter, Depends, File, HTTPException, UploadFile
from sqlalchemy.orm import Session


from app.db.postgres import get_db
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.patient import Patient
from app.services.chunker import chunk_text
from app.services.metadata_extractor import (
    extract_document_type,
    extract_report_date,
)
from app.services.neo4j_sync import sync_document_to_neo4j
from app.services.medical_extractor import extract_medical_data
from app.services.medical_persistence import persist_medical_data
from app.services.pdf_extractor import extract_text_from_pdf
from app.services.vector_sync import sync_document_chunks_to_neo4j


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

    extracted_text = extract_text_from_pdf(str(file_path))

    if not extracted_text:
        raise HTTPException(
            status_code=400,
            detail="Could not extract text from PDF",
        )

    document_type = extract_document_type(extracted_text)
    report_date = extract_report_date(extracted_text)

    chunks = chunk_text(extracted_text)

    document = Document(
        patient_id=patient_id,
        filename=file.filename,
        document_type=document_type,
        report_date=report_date,
        file_path=str(file_path),
    )

    db.add(document)
    db.commit()
    db.refresh(document)

    for index, chunk in enumerate(chunks):
        document_chunk = DocumentChunk(
            document_id=document.id,
            chunk_index=index,
            text=chunk,
        )

        db.add(document_chunk)

    db.commit()
    
    extraction = extract_medical_data(
        extracted_text,
        report_date,
    )

    persist_medical_data(
        db=db,
        patient_id=patient_id,
        document_id=document.id,
        extraction=extraction,
    )
    sync_document_to_neo4j(
        db=db,
        document_id=document.id,
    )
    sync_document_chunks_to_neo4j(
        db=db,
        document_id=document.id,
    )

    return {
        "message": "Document uploaded, extracted, and chunked successfully",
        "document_id": document.id,
        "patient_id": patient_id,
        "filename": document.filename,
        "document_type": document.document_type,
        "report_date": document.report_date,
        "observations_extracted": len(extraction.observations),
        "medications_extracted": len(extraction.medications),
        "treatment_events_extracted": len(extraction.treatment_events),
        "chunk_count": len(chunks),
        "text_preview": extracted_text[:1000],
    }