from pydantic import BaseModel, ConfigDict


class DocumentResponse(BaseModel):
    id: int
    patient_id: int
    filename: str
    document_type: str | None
    report_date: str | None

    model_config = ConfigDict(from_attributes=True)