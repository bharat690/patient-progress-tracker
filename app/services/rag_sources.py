import re


DOCUMENT_REFERENCE = re.compile(
    r"\b(?:document|doc)\s*(?:id\s*)?#?\s*(\d+)\b",
    re.IGNORECASE,
)

SOURCE_FIELDS = (
    "document_id",
    "report_date",
    "filename",
    "document_type",
    "score",
)


def select_answer_sources(
    answer: str,
    vector_results: list[dict],
    graph_results: list[dict],
) -> list[dict]:
    sources_by_document: dict[str, dict] = {}
    for source in [*graph_results, *vector_results]:
        document_id = source.get("document_id")
        if document_id is None:
            continue

        key = str(document_id)
        metadata = sources_by_document.setdefault(key, {"document_id": key})
        for field in SOURCE_FIELDS[1:]:
            value = source.get(field)
            if value is not None:
                metadata[field] = value

    referenced_ids = dict.fromkeys(
        DOCUMENT_REFERENCE.findall(answer)
    )
    if referenced_ids:
        matched_sources = [
            sources_by_document[document_id]
            for document_id in referenced_ids
            if document_id in sources_by_document
        ]
        if matched_sources:
            return matched_sources

    return vector_results
