from pydantic import BaseModel, ConfigDict


class PatientCreate(BaseModel):
    name: str
    date_of_birth: str | None = None
    gender: str | None = None
    created_by: int


class PatientResponse(BaseModel):
    id: int
    name: str
    date_of_birth: str | None
    gender: str | None
    created_by: int

    model_config = ConfigDict(from_attributes=True)