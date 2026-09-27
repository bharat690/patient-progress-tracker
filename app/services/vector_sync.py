from sqlalchemy.orm import Session

from app.db.neo4j import driver
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.services.embedding import embed_document


def sync_document_chunks_to_neo4j(
    db: Session,
    document_id: int,
) -> None:

    document = db.get(Document, document_id)

    if document is None:
        raise ValueError(
            f"Document {document_id} not found"
        )

    chunks = (
        db.query(DocumentChunk)
        .filter(
            DocumentChunk.document_id == document_id
        )
        .order_by(DocumentChunk.chunk_index)
        .all()
    )

    with driver.session() as session:

        for chunk in chunks:

            embedding = embed_document(chunk.text)

            session.run(
                """
                MATCH (r:Report {
                    document_id: $document_id
                })

                MERGE (c:Chunk {
                    chunk_id: $chunk_id
                })

                SET c.text = $text,
                    c.chunk_index = $chunk_index,
                    c.page_number = $page_number,
                    c.patient_id = $patient_id,
                    c.document_id = $document_id,
                    c.report_date = $report_date,
                    c.embedding = $embedding

                MERGE (r)-[:HAS_CHUNK]->(c)
                """,
                chunk_id=str(chunk.id),
                text=chunk.text,
                chunk_index=chunk.chunk_index,
                page_number=chunk.page_number,
                patient_id=str(document.patient_id),
                document_id=str(document.id),
                report_date=document.report_date,
                embedding=embedding,
            )

    print(
        f"Embedded {len(chunks)} chunks "
        f"for document {document_id}"
    )