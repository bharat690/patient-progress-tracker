from datetime import date

from fastapi import APIRouter, Depends, HTTPException, Request, status
from sqlalchemy import select
from sqlalchemy.orm import Session

from app.core.config import MAX_QUESTION_LENGTH
from app.core.rate_limit import enforce_rate_limit
from app.db.postgres import get_db
from app.dependencies.auth import get_current_user
from app.models.patient import Patient
from app.models.user import User
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


def get_patient_for_user(
    db: Session,
    current_user: User,
    patient_id: int,
) -> Patient:
    patient = db.get(Patient, patient_id)
    if patient is None:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Patient not found",
        )
    if patient.created_by != current_user.id:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="You do not have access to this patient",
        )
    return patient


@router.post(
    "/{patient_id}/ask",
    response_model=PatientQuestionResponse,
)
def ask_patient(
    patient_id: int,
    request: PatientQuestion,
    request_context: Request,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    if len(request.question) > MAX_QUESTION_LENGTH:
        raise HTTPException(
            status_code=422,
            detail=f"Question exceeds maximum length of {MAX_QUESTION_LENGTH} characters",
        )

    client_key = (
        f"user:{current_user.id}"
        if current_user is not None
        else (request_context.client.host if request_context.client else "anonymous")
    )
    try:
        enforce_rate_limit("RAG", client_key)
    except PermissionError as exc:
        raise HTTPException(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=str(exc),
        ) from exc

    get_patient_for_user(db, current_user, patient_id)
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
    current_user: User = Depends(get_current_user),
):
    get_patient_for_user(db, current_user, patient_id)
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
    current_user: User = Depends(get_current_user),
):
    get_patient_for_user(db, current_user, patient_id)
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
    current_user: User = Depends(get_current_user),
):
    get_patient_for_user(db, current_user, patient_id)
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
def patient_timeline(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    get_patient_for_user(db, current_user, patient_id)
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
    current_user: User = Depends(get_current_user),
):
    patient = Patient(
        name=patient_data.name,
        date_of_birth=patient_data.date_of_birth,
        gender=patient_data.gender,
        created_by=current_user.id,
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
    current_user: User = Depends(get_current_user),
):
    return db.scalars(
        select(Patient)
        .where(Patient.created_by == current_user.id)
        .order_by(Patient.id)
    ).all()


@router.get(
    "/{patient_id}",
    response_model=PatientResponse,
)
def get_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = get_patient_for_user(db, current_user, patient_id)
    return patient


@router.delete(
    "/{patient_id}",
    status_code=204,
)
def delete_patient(
    patient_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    patient = get_patient_for_user(db, current_user, patient_id)
    db.delete(patient)
    db.commit()