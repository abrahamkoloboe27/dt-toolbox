"""Tests for notifier module."""

from datetime import datetime

import pytest

from dt_toolbox.notifier import SMTPNotifier, WebhookNotifier, create_notifiers
from dt_toolbox.types import ExecutionSummary, NotificationConfig, NotificationLevel


@pytest.fixture
def sample_summary():
    """Create sample execution summary."""
    return ExecutionSummary(
        app_name="test_app",
        owner="test@example.com",
        run_id="run_123",
        trace_id="trace_456",
        start_time=datetime(2024, 1, 1, 12, 0, 0),
        end_time=datetime(2024, 1, 1, 12, 5, 30),
        duration_seconds=330.0,
        exit_code=0,
        success=True,
        tags=["test", "unit"],
        log_file="/tmp/test.log",
    )


def test_smtp_notifier_success(mock_smtp, sample_summary):
    """Test SMTP notifier sends email successfully."""
    config = NotificationConfig(
        smtp_host="smtp.example.com",
        smtp_port=587,
        smtp_user="sender@example.com",
        smtp_password="password",
        recipients=["recipient@example.com"],
    )

    notifier = SMTPNotifier(config)
    result = notifier.send(sample_summary, NotificationLevel.SUCCESS)

    assert result is True
    mock_smtp.send_message.assert_called_once()


def test_smtp_notifier_no_config(sample_summary):
    """Test SMTP notifier with missing configuration."""
    config = NotificationConfig(
        smtp_host=None,
        smtp_user=None,
    )

    notifier = SMTPNotifier(config)
    result = notifier.send(sample_summary, NotificationLevel.SUCCESS)

    assert result is False


def test_smtp_notifier_error_summary(mock_smtp):
    """Test SMTP notifier with error summary."""
    config = NotificationConfig(
        smtp_host="smtp.example.com",
        smtp_user="sender@example.com",
        recipients=["recipient@example.com"],
    )

    summary = ExecutionSummary(
        app_name="test_app",
        owner="test@example.com",
        run_id="run_123",
        trace_id="trace_456",
        start_time=datetime(2024, 1, 1, 12, 0, 0),
        duration_seconds=10.0,
        exit_code=1,
        success=False,
        error_message="Test error",
        stacktrace="Traceback:\n  File test.py, line 1\n    error",
    )

    notifier = SMTPNotifier(config)
    result = notifier.send(summary, NotificationLevel.ERROR)

    assert result is True


def test_webhook_notifier_slack(mock_requests, sample_summary):
    """Test webhook notifier for Slack."""
    config = NotificationConfig(
        webhook_url="https://hooks.slack.com/test",
        webhook_type="slack",
    )

    notifier = WebhookNotifier(config)
    result = notifier.send(sample_summary, NotificationLevel.SUCCESS)

    assert result is True
    mock_requests.assert_called_once()

    # Check payload structure
    call_kwargs = mock_requests.call_args[1]
    payload = call_kwargs["json"]
    assert "attachments" in payload


def test_webhook_notifier_gchat(mock_requests, sample_summary):
    """Test webhook notifier for Google Chat."""
    config = NotificationConfig(
        webhook_url="https://chat.googleapis.com/test",
        webhook_type="gchat",
    )

    notifier = WebhookNotifier(config)
    result = notifier.send(sample_summary, NotificationLevel.SUCCESS)

    assert result is True
    mock_requests.assert_called_once()

    # Check payload structure
    call_kwargs = mock_requests.call_args[1]
    payload = call_kwargs["json"]
    assert "text" in payload


def test_webhook_notifier_no_url(sample_summary):
    """Test webhook notifier with missing URL."""
    config = NotificationConfig(webhook_url=None)

    notifier = WebhookNotifier(config)
    result = notifier.send(sample_summary, NotificationLevel.SUCCESS)

    assert result is False


def test_create_notifiers_both():
    """Test creating notifiers with both SMTP and webhook configured."""
    config = NotificationConfig(
        smtp_host="smtp.example.com",
        smtp_user="sender@example.com",
        webhook_url="https://hooks.slack.com/test",
    )

    notifiers = create_notifiers(config)

    assert len(notifiers) == 2
    assert any(isinstance(n, SMTPNotifier) for n in notifiers)
    assert any(isinstance(n, WebhookNotifier) for n in notifiers)


def test_create_notifiers_none():
    """Test creating notifiers with no configuration."""
    config = NotificationConfig()

    notifiers = create_notifiers(config)

    assert len(notifiers) == 0
