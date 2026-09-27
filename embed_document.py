from app.db.postgres import SessionLocal
from app.services.vector_sync import sync_document_chunks_to_neo4j


db = SessionLocal()

try:
    sync_document_chunks_to_neo4j(
        db=db,
        document_id=9,
    )
finally:
    db.close()