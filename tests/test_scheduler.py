from unittest.mock import MagicMock
from src.scheduler import PeriodicTaskRunner, JobAutomationScheduler
from src.models import JobStatus

def test_periodic_task_due():
    runner = PeriodicTaskRunner(interval_seconds=60)
    assert runner.is_due() is True

    runner.mark_executed()
    assert runner.is_due() is False

def test_periodic_execute_if_due():
    mock_fn = MagicMock()
    runner = PeriodicTaskRunner(interval_seconds=60)

    executed = runner.execute_if_due(mock_fn)
    assert executed is True
    assert mock_fn.called

    executed_again = runner.execute_if_due(mock_fn)
    assert executed_again is False
    assert mock_fn.call_count == 1

def test_scheduler_execute_auto_scan():
    mock_tracker = MagicMock()
    mock_tracker.get_tracked_companies.return_value = [
        {"Company": "Gojek", "Status": "Applied"}
    ]

    mock_mailer = MagicMock()
    mock_mailer.check_inbox_updates.return_value = [{
        "company": "Gojek",
        "detected_status": JobStatus.ON_PROGRESS,
        "subject": "Interview schedule",
        "snippet": "Join Google meet tomorrow"
    }]

    mock_notifier = MagicMock()

    scheduler = JobAutomationScheduler(mock_tracker, mock_mailer, mock_notifier, scan_interval_seconds=3600)
    count = scheduler.execute_auto_scan()

    assert count == 1
    assert mock_tracker.update_status.called
    assert mock_notifier.notify_interview_detected.called
