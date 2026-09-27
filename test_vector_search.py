from app.services.vector_search import search_documents


results = search_documents(
    query="What were the patient's glucose and HbA1c results?",
    patient_id=4,
    limit=5,
)


for result in results:
    print("\n--------------------")
    print("Score:", result["score"])
    print("Document:", result["document_id"])
    print("Date:", result["report_date"])
    print("Text:")
    print(result["text"])