from app.db.neo4j import driver
from app.services.embedding import embed_query


def search_documents(
    query: str,
    patient_id: int,
    limit: int = 5,
):
    query_embedding = embed_query(query)

    cypher = """
    CALL db.index.vector.queryNodes(
        'document_chunk_embeddings',
        $limit,
        $query_embedding
    )
    YIELD node AS c, score

    WHERE c.patient_id = $patient_id

    MATCH (r:Report {document_id: c.document_id})

    RETURN
        c.chunk_id AS chunk_id,
        c.document_id AS document_id,
        c.patient_id AS patient_id,
        c.report_date AS report_date,
        c.text AS text,
        r.filename AS filename,
        r.document_type AS document_type,
        score

    ORDER BY score DESC
    """

    with driver.session() as session:

        result = session.run(
            cypher,
            patient_id=str(patient_id),
            query_embedding=query_embedding,
            limit=limit,
        )

        return [dict(record) for record in result]