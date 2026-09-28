from unittest.mock import MagicMock, patch
import os
from src.sheets import SheetsTracker, CSVTracker, WebhookTracker, get_tracker
from src.models import ApplicationRecord, JobStatus

def test_append_record():
    mock_client = MagicMock()
    mock_sheet = MagicMock()
    mock_client.open_by_key.return_value.sheet1 = mock_sheet

    tracker = SheetsTracker(client=mock_client, sheet_id="dummy_id")
    rec = ApplicationRecord(
        company="Tech Corp",
        position="Backend Dev",
        channel="Email",
        status=JobStatus.APPLIED,
        contact="hr@techcorp.com",
        notes="Applied via email"
    )
    tracker.append_record(rec)

    assert mock_sheet.append_row.called
    args, _ = mock_sheet.append_row.call_args
    row = args[0]
    assert row[0] == "Tech Corp"
    assert row[1] == "Backend Dev"
    assert row[2] == "Email"
    assert row[3] == "hr@techcorp.com"
    assert row[5] == "Applied"
    assert row[6] == "Applied via email"

def test_update_status():
    mock_client = MagicMock()
    mock_sheet = MagicMock()
    mock_client.open_by_key.return_value.sheet1 = mock_sheet

    mock_sheet.get_all_records.return_value = [
        {"Company": "Tech Corp", "Status": "Applied", "Notes": "Applied via email"}
    ]

    tracker = SheetsTracker(client=mock_client, sheet_id="dummy_id")
    updated = tracker.update_status(company="Tech Corp", new_status=JobStatus.ON_PROGRESS, note="Interview invite")

    assert updated is True
    mock_sheet.update_cell.assert_any_call(2, 6, "On Progress")
    mock_sheet.update_cell.assert_any_call(2, 7, "Applied via email | Interview invite")

def test_csv_tracker_append_and_update(tmp_path):
    csv_file = tmp_path / "test_applications.csv"
    tracker = CSVTracker(str(csv_file))

    rec = ApplicationRecord(
        company="Tokopedia",
        position="Software Engineer",
        channel="LinkedIn",
        status=JobStatus.APPLIED,
        contact="recruiter@tokopedia.com",
        notes="First apply"
    )
    tracker.append_record(rec)

    records = tracker.get_tracked_companies()
    assert len(records) == 1
    assert records[0]["Company"] == "Tokopedia"
    assert records[0]["Status"] == "Applied"

    updated = tracker.update_status("Tokopedia", JobStatus.ON_PROGRESS, note="Interview scheduled")
    assert updated is True

    records_after = tracker.get_tracked_companies()
    assert records_after[0]["Status"] == "On Progress"
    assert "Interview scheduled" in records_after[0]["Notes"]

def test_webhook_tracker():
    with patch("requests.post") as mock_post, patch("requests.get") as mock_get:
        mock_post.return_value.status_code = 200
        mock_post.return_value.json.return_value = {"status": "success"}
        mock_get.return_value.status_code = 200
        mock_get.return_value.json.return_value = [{"Company": "Gojek", "Status": "Applied"}]

        tracker = WebhookTracker("https://script.google.com/macros/s/xyz/exec")
        rec = ApplicationRecord(company="Gojek", position="Dev", channel="Email", status=JobStatus.APPLIED)
        tracker.append_record(rec)
        assert mock_post.called

        updated = tracker.update_status("Gojek", JobStatus.ON_PROGRESS, note="Technical Test")
        assert updated is True

        data = tracker.get_tracked_companies()
        assert len(data) == 1
        assert data[0]["Company"] == "Gojek"
