from app.db.neo4j import driver


def compare_patient_reports(
    patient_id: int,
    from_date: str,
    to_date: str,
):
    query = """
    MATCH (p:Patient {patient_id: toString($patient_id)})
          -[:HAS_REPORT]->(r:Report)
          -[:CONTAINS]->(o:Observation)

    WHERE r.report_date >= $from_date AND r.report_date <= $to_date

    RETURN
        r.report_date AS report_date,
        r.document_id AS document_id,
        r.filename AS filename,
        o.test_name AS test_name,
        o.value AS value,
        o.unit AS unit,
        o.observation_date AS observation_date

    ORDER BY r.report_date ASC, o.test_name ASC
    """

    with driver.session() as session:
        result = session.run(
            query,
            patient_id=patient_id,
            from_date=from_date,
            to_date=to_date,
        )

        rows = [record.data() for record in result]

        reports = {}

    for row in rows:
        report_date = row["report_date"]

        if report_date not in reports:
            reports[report_date] = {
                "document_id": row["document_id"],
                "filename": row["filename"],
                "observations": [],
            }

        reports[report_date]["observations"].append({
            "test_name": row["test_name"],
            "value": row["value"],
            "unit": row["unit"],
            "observation_date": row["observation_date"],
        })

    # Find earliest and latest report in the requested range
    report_dates = sorted(reports.keys())

    comparison = []

    if len(report_dates) >= 2:
        first_date = report_dates[0]
        last_date = report_dates[-1]

        first_observations = {
            item["test_name"]: item
            for item in reports[first_date]["observations"]
        }

        last_observations = {
            item["test_name"]: item
            for item in reports[last_date]["observations"]
        }

        common_tests = sorted(
            set(first_observations) & set(last_observations)
        )

        for test_name in common_tests:
            first = first_observations[test_name]
            last = last_observations[test_name]

            if (
                first["value"] is not None
                and last["value"] is not None
            ):
                comparison.append({
                    "test_name": test_name,
                    "unit": last["unit"],
                    "from": {
                        "date": first_date,
                        "value": first["value"],
                    },
                    "to": {
                        "date": last_date,
                        "value": last["value"],
                    },
                    "absolute_change": round(
                        last["value"] - first["value"],
                        4,
                    ),
                })

    return {
        "patient_id": patient_id,
        "from_date": from_date,
        "to_date": to_date,
        "reports": reports,
        "comparison": comparison,
    }