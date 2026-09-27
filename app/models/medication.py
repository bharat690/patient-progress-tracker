from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Medication(Base):
    __tablename__ = "medications"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        index=True,
    )

    document_id: Mapped[int | None] = mapped_column(
        ForeignKey("documents.id"),
        nullable=True,
    )

    name: Mapped[str] = mapped_column(String(100))
    dosage: Mapped[str | None] = mapped_column(String(100), nullable=True)
    frequency: Mapped[str | None] = mapped_column(String(100), nullable=True)

    start_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    end_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )