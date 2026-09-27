from pydantic import BaseModel, ConfigDict, Field


class ObservationExtracted(BaseModel):
    model_config = ConfigDict(extra="forbid")

    test_name: str
    value: float | None
    unit: str | None
    observation_date: str | None


class MedicationExtracted(BaseModel):
    model_config = ConfigDict(extra="forbid")

    name: str
    dosage: str | None
    frequency: str | None
    start_date: str | None
    end_date: str | None


class TreatmentEventExtracted(BaseModel):
    model_config = ConfigDict(extra="forbid")

    event_type: str
    description: str
    event_date: str | None


class MedicalExtraction(BaseModel):
    model_config = ConfigDict(extra="forbid")

    observations: list[ObservationExtracted]
    medications: list[MedicationExtracted]
    treatment_events: list[TreatmentEventExtracted]