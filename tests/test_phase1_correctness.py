import os
import unittest
from datetime import date

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db.postgres import Base
from app.models.document import Document
from app.models.observation import Observation
from app.schemas.document import DocumentResponse
from app.services.comparison import compare_patient_reports
from app.services.metadata_extractor import (
    extract_document_type,
    extract_report_date,
)
from app.services.metrics import get_patient_metrics
from app.services.observations import get_patient_observations
from app.services.trends import get_patient_trend


class PhaseOneCorrectnessTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")
        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.add_document(1, "january.pdf", "01/10/2026")
        self.add_document(2, "march.pdf", "2026-03-10")
        self.add_document(3, "duplicate.pdf", "2026-03-10")
        self.add_observation(1, 1, "HbA1c", 8.2, "2026-01-08")
        self.add_observation(2, 2, "HbA1c", 7.4, "2026-03-09")
        self.add_observation(3, 3, "hba1c", 7.1, "2026-03-10")
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    def add_document(self, document_id, filename, report_date):
        self.session.add(Document(
            id=document_id,
            patient_id=1,
            filename=filename,
            document_type="blood_report",
            report_date=report_date,
            file_path=f"uploads/{filename}",
        ))

    def add_observation(
        self,
        observation_id,
        document_id,
        test_name,
        value,
        observation_date,
    ):
        self.session.add(Observation(
            id=observation_id,
            patient_id=1,
            document_id=document_id,
            test_name=test_name,
            value=value,
            unit="%",
            observation_date=observation_date,
        ))

    def test_metrics_and_trends_share_the_same_canonical_series(self):
        metrics = get_patient_metrics(self.session, 1)
        trend = get_patient_trend(self.session, 1, "HBA1C")
        observations = get_patient_observations(self.session, 1)

        self.assertEqual(len(metrics), 1)
        self.assertEqual(
            [item["report_date"] for item in trend],
            ["2026-01-10", "2026-03-10"],
        )
        self.assertEqual(
            [item["date"] for item in metrics[0]["history"]],
            [item["report_date"] for item in trend],
        )
        self.assertEqual(metrics[0]["latest"]["value"], 7.4)
        self.assertEqual(metrics[0]["change"], -0.8)
        self.assertEqual(len(observations), 2)

    def test_comparison_uses_canonical_dates_and_deduplicated_observations(self):
        result = compare_patient_reports(
            self.session,
            1,
            date(2026, 1, 1),
            date(2026, 3, 31),
        )

        self.assertEqual(set(result["reports"]), {"2026-01-10", "2026-03-10"})
        self.assertEqual(
            result["comparison"],
            [{
                "test_name": "HbA1c",
                "unit": "%",
                "from": {"date": "2026-01-10", "value": 8.2},
                "to": {"date": "2026-03-10", "value": 7.4},
                "absolute_change": -0.8,
            }],
        )
        self.assertEqual(
            len(result["reports"]["2026-03-10"]["documents"]),
            1,
        )

    def test_report_date_falls_back_to_observation_date(self):
        document = self.session.get(Document, 1)
        document.report_date = "not a date"
        self.session.commit()

        rows = get_patient_observations(self.session, 1, "hba1c")

        self.assertEqual(rows[0]["report_date"], "2026-01-08")

    def test_report_date_extraction_normalizes_and_rejects_invalid_dates(self):
        self.assertEqual(
            extract_report_date("Report Date: January 10, 2026"),
            "2026-01-10",
        )
        self.assertIsNone(extract_report_date("Report Date: 2026-02-30"))

    def test_report_date_extraction_accepts_document_and_visit_date_labels(self):
        self.assertEqual(
            extract_report_date(
                "Document Date: 2026-01-15\n"
                "Sample Collection Date: 2026-01-14"
            ),
            "2026-01-15",
        )
        self.assertEqual(
            extract_report_date("Visit Date:\nApril 29, 2026"),
            "2026-04-29",
        )

    def test_document_response_normalizes_legacy_report_dates(self):
        response = DocumentResponse.model_validate({
            "id": 1,
            "patient_id": 1,
            "filename": "legacy.pdf",
            "document_type": "blood_report",
            "report_date": "01/10/2026",
        })

        self.assertEqual(response.report_date, "2026-01-10")

    def test_document_type_detection_is_case_and_whitespace_insensitive(self):
        self.assertEqual(
            extract_document_type("  FOLLOW-UP   BLOOD REPORT  "),
            "blood_report",
        )
        self.assertEqual(
            extract_document_type("  BLOOD / LABORATORY REPORT  "),
            "blood_report",
        )
        self.assertEqual(
            extract_document_type("Follow-up Blood / Laboratory Report"),
            "blood_report",
        )
        self.assertEqual(
            extract_document_type("Medication Prescription"),
            "prescription",
        )
        self.assertIsNone(extract_document_type("Discharge note"))


if __name__ == "__main__":
    unittest.main()
