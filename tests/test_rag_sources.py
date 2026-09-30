import unittest

from app.services.rag_sources import select_answer_sources


class RAGSourceSelectionTests(unittest.TestCase):
    def test_includes_graph_reports_cited_by_the_answer(self):
        answer = (
            "Document 26 lists the prescription. "
            "Document 28 confirms the follow-up."
        )
        vector_results = [{
            "document_id": "26",
            "report_date": "2026-01-15",
            "filename": "prescription.pdf",
            "document_type": "prescription",
            "score": 0.9,
            "text": "retrieved chunk",
        }]
        graph_results = [
            {
                "document_id": "25",
                "report_date": "2026-01-12",
                "filename": "january.pdf",
            },
            {
                "document_id": "26",
                "report_date": "2026-01-15",
                "filename": "prescription.pdf",
            },
            {
                "document_id": "28",
                "report_date": "2026-04-29",
                "filename": "follow-up.pdf",
            },
        ]

        sources = select_answer_sources(
            answer,
            vector_results,
            graph_results,
        )

        self.assertEqual(
            [source["document_id"] for source in sources],
            ["26", "28"],
        )
        self.assertEqual(sources[0]["score"], 0.9)
        self.assertNotIn("text", sources[0])

    def test_falls_back_to_vector_sources_without_document_references(self):
        vector_results = [{
            "document_id": "26",
            "report_date": "2026-01-15",
            "filename": "prescription.pdf",
        }]

        sources = select_answer_sources(
            "The records do not contain that information.",
            vector_results,
            [],
        )

        self.assertEqual(sources, vector_results)


if __name__ == "__main__":
    unittest.main()
