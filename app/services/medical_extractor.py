import json

from groq import Groq

from app.core.config import GROQ_API_KEY
from app.schemas.medical import MedicalExtraction


if not GROQ_API_KEY:
    raise RuntimeError("GROQ_API_KEY is not configured")


client = Groq(api_key=GROQ_API_KEY)


SYSTEM_PROMPT = """
You are a medical document information extraction system.

Your job is ONLY to extract information explicitly documented in the
provided medical document.

Do not diagnose the patient.
Do not infer medical conditions.
Do not invent values, dates, medications, or treatment events.

Extract:

1. Observations
   - test_name
   - value
   - unit
   - observation_date

2. Medications
   - name
   - dosage
   - frequency
   - start_date
   - end_date

3. Treatment events
   - event_type
   - description
   - event_date

If a field is not explicitly documented, use null.

Use the document report date as the observation/event date when the
document clearly indicates that the observation or event belongs to
that report date.

Return ONLY the requested JSON structure.
"""


def extract_medical_data(
    text: str,
    report_date: str | None = None,
) -> MedicalExtraction:

    prompt = f"""
Document report date: {report_date}

Medical document:

{text}
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
        response_format={
            "type": "json_schema",
            "json_schema": {
                "name": "medical_extraction",
                "strict": True,
                "schema": MedicalExtraction.model_json_schema(),
            },
        },
        temperature=0,
    )

    content = response.choices[0].message.content

    if not content:
        raise RuntimeError("LLM returned empty response")

    try:
        data = json.loads(content)
    except json.JSONDecodeError as exc:
        raise RuntimeError(
            "LLM returned invalid JSON"
        ) from exc

    return MedicalExtraction.model_validate(data)