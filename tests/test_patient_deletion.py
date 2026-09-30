import os
import unittest
from pathlib import Path
from tempfile import TemporaryDirectory
from unittest.mock import patch

os.environ.setdefault("DATABASE_URL", "sqlite://")

from sqlalchemy import create_engine, event, select
from sqlalchemy.orm import sessionmaker

from app.db.postgres import Base
from app.models.document import Document
from app.models.document_chunk import DocumentChunk
from app.models.medication import Medication
from app.models.observation import Observation
from app.models.patient import Patient
from app.models.treatment_event import TreatmentEvent
from app.models.user import User
from app.services.patient_deletion import delete_patient_records


class PatientDeletionTests(unittest.TestCase):
    def setUp(self):
        self.engine = create_engine("sqlite://")

        @event.listens_for(self.engine, "connect")
        def enable_foreign_keys(connection, _record):
            cursor = connection.cursor()
            cursor.execute("PRAGMA foreign_keys=ON")
            cursor.close()

        Base.metadata.create_all(self.engine)
        self.session = sessionmaker(bind=self.engine)()
        self.user = User(
            id=1,
            name="Test User",
            email="test@example.com",
            password_hash="hash",
        )
        self.session.add(self.user)
        self.session.flush()
        self.patient = Patient(
            id=1,
            name="Test Patient",
            created_by=1,
        )
        self.other_patient = Patient(
            id=2,
            name="Other Patient",
            created_by=1,
        )
        self.session.add_all([self.patient, self.other_patient])
        self.session.flush()

        self.document = Document(
            id=1,
            patient_id=1,
            filename="report.pdf",
            document_type="blood_report",
            report_date="2026-01-12",
            file_path="uploads/report.pdf",
            storage_key="patients/1/documents/1/report.pdf",
        )
        self.shared_path_document = Document(
            id=2,
            patient_id=2,
            filename="report.pdf",
            file_path="uploads/report.pdf",
        )
        self.session.add_all([self.document, self.shared_path_document])
        self.session.flush()
        self.session.add_all([
            DocumentChunk(document_id=1, chunk_index=0, text="sample"),
            Observation(
                patient_id=1,
                document_id=1,
                test_name="HbA1c",
                value=7.2,
            ),
            Medication(
                patient_id=1,
                document_id=1,
                name="Medication",
            ),
            TreatmentEvent(
                patient_id=1,
                document_id=1,
                event_type="follow-up",
                description="Review",
            ),
        ])
        self.session.commit()

    def tearDown(self):
        self.session.close()
        self.engine.dispose()

    @patch("app.services.patient_deletion.delete_files")
    @patch("app.services.patient_deletion.driver")
    def test_deletes_patient_children_and_external_document_data(
        self,
        driver,
        delete_files,
    ):
        with TemporaryDirectory() as temp_dir:
            upload_dir = Path(temp_dir) / "uploads"
            upload_dir.mkdir()
            shared_file = upload_dir / "report.pdf"
            shared_file.write_bytes(b"still used by another patient")
            self.document.file_path = str(shared_file)
            self.shared_path_document.file_path = str(shared_file)
            self.session.commit()

            with patch(
                "app.services.patient_deletion.UPLOAD_DIR",
                upload_dir,
            ):
                delete_patient_records(
                    self.session,
                    self.session.get(Patient, 1),
                )

            self.assertIsNone(self.session.get(Patient, 1))
            self.assertIsNotNone(self.session.get(Patient, 2))
            self.assertEqual(
                self.session.scalars(select(Document).where(
                    Document.patient_id == 1
                )).all(),
                [],
            )
            self.assertEqual(
                self.session.scalars(select(DocumentChunk)).all(),
                [],
            )
            self.assertEqual(
                self.session.scalars(select(Observation)).all(),
                [],
            )
            self.assertEqual(
                self.session.scalars(select(Medication)).all(),
                [],
            )
            self.assertEqual(
                self.session.scalars(select(TreatmentEvent)).all(),
                [],
            )
            self.assertTrue(shared_file.exists())
            delete_files.assert_called_once_with([
                "patients/1/documents/1/report.pdf"
            ])
            driver.session.assert_called_once()

    @patch("app.services.patient_deletion.delete_files")
    @patch("app.services.patient_deletion.driver")
    def test_rolls_back_database_deletes_when_external_cleanup_fails(
        self,
        driver,
        delete_files,
    ):
        delete_files.side_effect = RuntimeError("storage unavailable")

        with self.assertLogs(
            "app.services.patient_deletion",
            level="ERROR",
        ):
            with self.assertRaisesRegex(RuntimeError, "storage unavailable"):
                delete_patient_records(
                    self.session,
                    self.session.get(Patient, 1),
                )

        self.assertIsNotNone(self.session.get(Patient, 1))
        self.assertIsNotNone(self.session.get(Document, 1))
        self.assertEqual(
            len(self.session.scalars(select(DocumentChunk)).all()),
            1,
        )
        driver.session.assert_called_once()


if __name__ == "__main__":
    unittest.main()
