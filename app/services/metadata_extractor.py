import re

from app.core.dates import normalize_date


def extract_report_date(text: str) -> str | None:
    match = re.search(
        r"Report Date:\s*([^\r\n]+)",
        text,
        re.IGNORECASE,
    )

    return normalize_date(match.group(1)) if match else None


def extract_document_type(text: str) -> str | None:
    document_types = {
        "complete blood count & metabolic panel": "blood_report",
        "follow-up blood report": "blood_report",
        "prescription / treatment record": "prescription",
        "follow-up clinical summary": "clinical_summary",
    }

    lines = [
        re.sub(r"\s+", " ", line).strip().casefold()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines:
        if line in document_types:
            return document_types[line]

    return None