from datetime import date

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.db.postgres import get_db
from app.models.patient import Patient
from app.schemas.patient import PatientCreate, PatientResponse
from app.schemas.rag import (
    PatientQuestion,
    PatientQuestionResponse,
)

from app.services.rag import answer_patient_question
from app.services.patient_timeline import get_patient_timeline
from app.services.trends import get_patient_trend
from app.services.comparison import compare_patient_reports
from app.services.metrics import get_patient_metrics



router = APIRouter(
    prefix="/patients",
    tags=["Patients"],
)

@router.post(
    "/{patient_id}/ask",
    response_model=PatientQuestionResponse,
)
def ask_patient(
    patient_id: int,
    request: PatientQuestion,
):
    result = answer_patient_question(
        patient_id=patient_id,
        question=request.question,
    )

    return {
        "patient_id": patient_id,
        "question": request.question,
        "answer": result["answer"],
        "sources": result["sources"],
    }


@router.get("/{patient_id}/metrics")
def patient_metrics(
    patient_id: int,
    db: Session = Depends(get_db),
):
    return {
        "patient_id": patient_id,
        "metrics": get_patient_metrics(db, patient_id),
    }

@router.get("/{patient_id}/compare")
def compare_reports(
    patient_id: int,
    from_date: date,
    to_date: date,
    db: Session = Depends(get_db),
):
    if from_date > to_date:
        raise HTTPException(
            status_code=422,
            detail="from_date must be on or before to_date",
        )

    return compare_patient_reports(
        db=db,
        patient_id=patient_id,
        from_date=from_date,
        to_date=to_date,
    )

@router.get("/{patient_id}/trends/{test_name}")
def patient_trend(
    patient_id: int,
    test_name: str,
    db: Session = Depends(get_db),
):
    return {
        "patient_id": patient_id,
        "test_name": test_name,
        "trend": get_patient_trend(
            db=db,
            patient_id=patient_id,
            test_name=test_name,
        ),
    }

@router.get("/{patient_id}/timeline")
def patient_timeline(patient_id: int):
    return {
        "patient_id": patient_id,
        "timeline": get_patient_timeline(patient_id),
    }

@router.post(
    "",
    response_model=PatientResponse,
    status_code=201,
)
def create_patient(
    patient_data: PatientCreate,
    db: Session = Depends(get_db),
):
    patient = Patient(
        name=patient_data.name,
        date_of_birth=patient_data.date_of_birth,
        gender=patient_data.gender,
        created_by=patient_data.created_by,
    )

    db.add(patient)
    db.commit()
    db.refresh(patient)

    return patient


@router.get(
    "",
    response_model=list[PatientResponse],
)
def get_patients(
    db: Session = Depends(get_db),
):
    patients = db.scalars(
        select(Patient).order_by(Patient.id)
    ).all()

    return patients


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    return patient


@router.delete(
    "/{patient_id}",
    status_code=204,
)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
):
    patient = db.get(Patient, patient_id)

    if patient is None:
        raise HTTPException(
            status_code=404,
            detail="Patient not found",
        )

    db.delete(patient)
    db.commit()