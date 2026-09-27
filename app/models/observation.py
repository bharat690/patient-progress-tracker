from sqlalchemy import ForeignKey, String, Float
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Observation(Base):
    __tablename__ = "observations"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        index=True,
    )

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        index=True,
    )

    test_name: Mapped[str] = mapped_column(String(100))
    value: Mapped[float | None] = mapped_column(Float, nullable=True)
    unit: Mapped[str | None] = mapped_column(String(30), nullable=True)

    observation_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )