from groq import Groq

from app.core.config import GROQ_API_KEY
from app.services.retrieval import retrieve_patient_context


client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
You are a medical-record retrieval assistant.

You are NOT a doctor.

Answer ONLY from the retrieved patient records.

Do not diagnose.
Do not prescribe.
Do not infer medical conditions.
Do not invent missing information.

When answering:

1. Prefer structured graph facts for exact values and dates.
2. Use document chunks for supporting context.
3. Clearly distinguish documented facts from missing information.
4. Include the relevant source document and date.
5. If the records do not contain the answer, say so.

The records are synthetic demonstration data.
"""


def answer_patient_question(
    patient_id: int,
    question: str,
):

    context = retrieve_patient_context(
        patient_id=patient_id,
        question=question,
    )

    prompt = f"""
Patient ID:
{patient_id}

Question:
{question}

STRUCTURED PATIENT HISTORY:

{context["graph_results"]}

RELEVANT DOCUMENT CHUNKS:

{context["vector_results"]}
"""

    response = client.chat.completions.create(
        model="openai/gpt-oss-20b",
        messages=[
            {
                "role": "system",
                "content": SYSTEM_PROMPT,
            },
            {
                "role": "user",
                "content": prompt,
            },
        ],
        temperature=0,
    )

    answer = response.choices[0].message.content

    return {
        "answer": answer,
        "sources": context["vector_results"],
    }