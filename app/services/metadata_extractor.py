import re

from app.core.dates import normalize_date


def extract_report_date(text: str) -> str | None:
    for label in (
        "Report Date",
        "Document Date",
        "Sample Collection Date",
        "Visit Date",
    ):
        match = re.search(
            rf"\b{label}\s*:\s*([^\r\n]+)",
            text,
            re.IGNORECASE,
        )
        if match:
            normalized = normalize_date(match.group(1))
            if normalized:
                return normalized
    return None


def extract_document_type(text: str) -> str | None:
    document_types = {
        "complete blood count & metabolic panel": "blood_report",
        "blood / laboratory report": "blood_report",
        "follow-up blood / laboratory report": "blood_report",
        "follow-up blood report": "blood_report",
        "medication prescription": "prescription",
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