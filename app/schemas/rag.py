from pydantic import BaseModel, ConfigDict


class PatientQuestion(BaseModel):
    model_config = ConfigDict(extra="forbid")

    question: str


class RAGSource(BaseModel):
    document_id: str
    report_date: str | None
    filename: str
    document_type: str | None = None
    score: float | None = None


class PatientQuestionResponse(BaseModel):
    patient_id: int
    question: str
    answer: str
    sources: list[RAGSource]