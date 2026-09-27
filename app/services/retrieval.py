from app.services.vector_search import search_documents
from app.services.graph_retrieval import get_patient_context


def retrieve_patient_context(
    patient_id: int,
    question: str,
    limit: int = 5,
):

    vector_results = search_documents(
        query=question,
        patient_id=patient_id,
        limit=limit,
    )

    graph_results = get_patient_context(
        patient_id=patient_id,
    )

    return {
        "vector_results": vector_results,
        "graph_results": graph_results,
    }