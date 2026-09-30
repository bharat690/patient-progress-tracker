from datetime import date

from sqlalchemy.orm import Session

from app.services.observations import get_patient_observations


def compare_patient_reports(
    db: Session,
    patient_id: int,
    from_date: date,
    to_date: date,
):
    from_date_text = from_date.isoformat()
    to_date_text = to_date.isoformat()
    if from_date > to_date:
        raise ValueError("from_date must be on or before to_date")

    rows = [
        row
        for row in get_patient_observations(db, patient_id)
        if from_date_text <= row["report_date"] <= to_date_text
    ]

    reports = {}
    observations_by_test = {}
    for row in rows:
        report_date = row["report_date"]
        report = reports.setdefault(report_date, {
            "document_id": row["document_id"],
            "filename": row["filename"],
            "documents": [],
            "observations": [],
        })

        if not any(
            document["document_id"] == row["document_id"]
            for document in report["documents"]
        ):
            report["documents"].append({
                "document_id": row["document_id"],
                "filename": row["filename"],
            })

        observation = {
            "test_name": row["test_name"],
            "value": row["value"],
            "unit": row["unit"],
            "observation_date": row["observation_date"],
        }
        report["observations"].append(observation)
        observations_by_test.setdefault(
            row["test_name"].casefold(), []
        ).append({
            **observation,
            "report_date": report_date,
        })

    comparison = []
    for test_observations in observations_by_test.values():
        if len(test_observations) < 2:
            continue

        first = test_observations[0]
        last = test_observations[-1]
        comparison.append({
            "test_name": last["test_name"],
            "unit": last["unit"],
            "from": {
                "date": first["report_date"],
                "value": first["value"],
            },
            "to": {
                "date": last["report_date"],
                "value": last["value"],
            },
            "absolute_change": round(
                last["value"] - first["value"],
                4,
            ),
        })

    comparison.sort(key=lambda item: item["test_name"].casefold())

    return {
        "patient_id": patient_id,
        "from_date": from_date_text,
        "to_date": to_date_text,
        "reports": reports,
        "comparison": comparison,
    }