from sqlalchemy import ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class TreatmentEvent(Base):
    __tablename__ = "treatment_events"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        index=True,
    )

    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id"),
        nullable=True,
    )

    event_type: Mapped[str] = mapped_column(String(50))
    description: Mapped[str] = mapped_column(Text)

    event_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )