from sqlalchemy.orm import Session

from app.services.observations import get_patient_observations


def get_patient_metrics(db: Session, patient_id: int):
    metrics = {}
    for row in get_patient_observations(db, patient_id):
        test_key = row["test_name"].casefold()
        metric = metrics.setdefault(test_key, {
            "test_name": row["test_name"],
            "observations": [],
        })
        metric["observations"].append({
            "value": row["value"],
            "unit": row["unit"],
            "date": row["report_date"],
            "document_id": row["document_id"],
            "filename": row["filename"],
        })

    response = []
    for metric in metrics.values():
        test_name = metric["test_name"]
        observations = metric["observations"]

        latest = observations[-1]

        previous = (
            observations[-2]
            if len(observations) >= 2
            else None
        )

        change = None
        trend = "stable"

        if previous is not None:
            change = round(
                latest["value"] - previous["value"],
                4,
            )

            if change > 0:
                trend = "increasing"
            elif change < 0:
                trend = "decreasing"

        response.append({
            "test_name": test_name,
            "latest": latest,
            "previous": previous,
            "change": change,
            "trend": trend,
            "history": observations,
        })

    response.sort(
        key=lambda item: item["test_name"]
    )

    return response