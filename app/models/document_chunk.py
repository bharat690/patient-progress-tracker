from sqlalchemy import ForeignKey, Integer, Text
from sqlalchemy.orm import Mapped, mapped_column

from app.db.postgres import Base


class DocumentChunk(Base):
    __tablename__ = "document_chunks"

    id: Mapped[int] = mapped_column(primary_key=True)

    document_id: Mapped[int] = mapped_column(
        ForeignKey("documents.id"),
        index=True,
    )

    chunk_index: Mapped[int] = mapped_column(Integer)

    page_number: Mapped[int | None] = mapped_column(
        Integer,
        nullable=True,
    )

    text: Mapped[str] = mapped_column(Text)