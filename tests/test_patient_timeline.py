import sys
import unittest
from types import ModuleType
from unittest.mock import MagicMock, patch


class PatientTimelineTests(unittest.TestCase):
    def test_optional_medication_end_date_uses_properties_map(self):
        record_data = {
            "medications": [{
                "name": "Medication A",
                "dosage": "10 mg",
                "frequency": "daily",
                "start_date": "2026-01-01",
                "end_date": None,
            }],
        }
        record = MagicMock()
        record.data.return_value = record_data
        driver = MagicMock()
        session = MagicMock()
        session.run.return_value = [record]
        driver.session.return_value.__enter__.return_value = session
        neo4j_module = ModuleType("app.db.neo4j")
        neo4j_module.driver = driver

        with patch.dict(sys.modules, {"app.db.neo4j": neo4j_module}):
            from app.services.patient_timeline import get_patient_timeline

        result = get_patient_timeline(4)

        query = session.run.call_args.args[0]
        self.assertIn("end_date: properties(m).end_date", query)
        self.assertNotIn("end_date: m.end_date", query)
        self.assertEqual(result, [record_data])


if __name__ == "__main__":
    unittest.main()
