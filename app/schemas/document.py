from pydantic import BaseModel, ConfigDict, field_validator

from app.core.dates import normalize_date


class DocumentResponse(BaseModel):
    id: int
    patient_id: int
    filename: str
    document_type: str | None
    report_date: str | None

    model_config = ConfigDict(from_attributes=True)

    @field_validator("report_date", mode="before")
    @classmethod
    def normalize_report_date(cls, value):
        return normalize_date(value) if value is not None else None