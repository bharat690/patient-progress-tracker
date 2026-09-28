from app.db.neo4j import driver


def get_patient_metrics(patient_id: int):
    query = """
    MATCH (p:Patient {patient_id: toString($patient_id)})
          -[:HAS_REPORT]->(r:Report)
          -[:CONTAINS]->(o:Observation)

    WHERE o.value IS NOT NULL

    RETURN
        o.test_name AS test_name,
        o.value AS value,
        o.unit AS unit,
        r.report_date AS report_date,
        r.document_id AS document_id,
        r.filename AS filename

    ORDER BY
        o.test_name ASC,
        r.report_date ASC,
        r.document_id ASC
    """

    with driver.session() as session:
        result = session.run(
            query,
            patient_id=patient_id,
        )

        rows = [record.data() for record in result]

    metrics = {}

    for row in rows:
        test_name = row["test_name"]

        if test_name not in metrics:
            metrics[test_name] = {}

        report_date = row["report_date"]

        # Keep only one observation for the same metric/report date.
        # The first document encountered is retained.
        if report_date not in metrics[test_name]:
            metrics[test_name][report_date] = {
                "value": row["value"],
                "unit": row["unit"],
                "date": report_date,
                "document_id": row["document_id"],
                "filename": row["filename"],
            }

    response = []

    for test_name, dated_observations in metrics.items():

        observations = list(dated_observations.values())

        observations.sort(
            key=lambda item: item["date"] or ""
        )

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