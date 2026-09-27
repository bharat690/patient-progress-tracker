from app.services.embedding import embed_document


text = """
Patient medical report dated 2026-01-24.
HbA1c was 7.2 percent.
Fasting glucose was 108 mg/dL.
Total cholesterol was 214 mg/dL.
"""


embedding = embed_document(text)

print("Embedding dimensions:", len(embedding))
print("First 5:", embedding[:5])