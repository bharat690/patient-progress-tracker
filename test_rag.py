from app.services.rag import answer_patient_question


result = answer_patient_question(
    patient_id=4,
    question="What were the patient's HbA1c and fasting glucose results?",
)

print("\nANSWER")
print(result["answer"])

print("\nSOURCES")

for source in result["sources"]:
    print(
        source["document_id"],
        source["report_date"],
        source["filename"],
        source["score"],
    )