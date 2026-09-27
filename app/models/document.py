from sqlalchemy import ForeignKey, String
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class Document(Base):
    __tablename__ = "documents"

    id: Mapped[int] = mapped_column(primary_key=True)

    patient_id: Mapped[int] = mapped_column(
        ForeignKey("patients.id"),
        index=True,
    )

    filename: Mapped[str] = mapped_column(String(255))

    document_type: Mapped[str | None] = mapped_column(
        String(50),
        nullable=True,
    )

    report_date: Mapped[str | None] = mapped_column(
        String(20),
        nullable=True,
    )

    file_path: Mapped[str] = mapped_column(String(500))