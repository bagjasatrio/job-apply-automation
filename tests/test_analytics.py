from src.analytics import compute_application_metrics

def test_compute_application_metrics_empty():
    metrics = compute_application_metrics([])
    assert metrics["total"] == 0
    assert metrics["interview_rate"] == 0.0

def test_compute_application_metrics_values():
    records = [
        {"Company": "A", "Channel": "Email", "Status": "Applied"},
        {"Company": "B", "Channel": "Email", "Status": "On Progress"},
        {"Company": "C", "Channel": "LinkedIn", "Status": "Rejected"},
        {"Company": "D", "Channel": "LinkedIn", "Status": "Offering"},
        {"Company": "E", "Channel": "Glints", "Status": "Applied"}
    ]
    metrics = compute_application_metrics(records)

    assert metrics["total"] == 5
    assert metrics["counts"]["Applied"] == 2
    assert metrics["counts"]["On Progress"] == 1
    assert metrics["counts"]["Rejected"] == 1
    assert metrics["counts"]["Offering"] == 1

    # Interview rate = (On Progress + Offering) / total = 2 / 5 = 40.0%
    assert metrics["interview_rate"] == 40.0
    # Response rate = (On Progress + Rejected + Offering) / total = 3 / 5 = 60.0%
    assert metrics["response_rate"] == 60.0
    # Offer rate = 1 / 5 = 20.0%
    assert metrics["offer_rate"] == 20.0

    # Channel stats check
    assert "Email" in metrics["channels"]
    assert metrics["channels"]["Email"]["total"] == 2
    assert metrics["channels"]["Email"]["interviews"] == 1
