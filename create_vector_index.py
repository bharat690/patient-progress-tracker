from app.db.neo4j import driver


query = """
CREATE VECTOR INDEX document_chunk_embeddings IF NOT EXISTS
FOR (c:Chunk)
ON c.embedding
OPTIONS {
    indexConfig: {
        `vector.dimensions`: 768,
        `vector.similarity_function`: 'cosine'
    }
}
"""


with driver.session() as session:
    session.run(query)

print("Vector index creation requested.")

driver.close()