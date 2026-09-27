import re


def extract_report_date(text: str) -> str | None:
    match = re.search(
        r"Report Date:\s*(\d{4}-\d{2}-\d{2})",
        text,
        re.IGNORECASE,
    )

    if match:
        return match.group(1)

    return None


def extract_document_type(text: str) -> str | None:
    lines = [
        line.strip()
        for line in text.splitlines()
        if line.strip()
    ]

    for line in lines:
        if line == "Complete Blood Count & Metabolic Panel":
            return "blood_report"

        if line == "Follow-up Blood Report":
            return "blood_report"

        if line == "Prescription / Treatment Record":
            return "prescription"

        if line == "Follow-up Clinical Summary":
            return "clinical_summary"

    return None