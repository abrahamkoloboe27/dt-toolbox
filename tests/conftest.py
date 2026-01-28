"""Pytest configuration and fixtures."""

import os
import smtplib
import tempfile
from collections.abc import Generator
from unittest.mock import MagicMock

import pytest
import requests


@pytest.fixture
def temp_log_dir() -> Generator[str, None, None]:
    """Create temporary directory for logs."""
    with tempfile.TemporaryDirectory() as tmpdir:
        yield tmpdir


@pytest.fixture
def mock_smtp(monkeypatch: pytest.MonkeyPatch) -> Generator[MagicMock, None, None]:
    """Mock SMTP server."""
    mock_server = MagicMock()
    mock_smtp_class = MagicMock(return_value=mock_server)

    # Mock SMTP context manager
    mock_server.__enter__ = MagicMock(return_value=mock_server)
    mock_server.__exit__ = MagicMock(return_value=None)

    monkeypatch.setattr(smtplib, "SMTP", mock_smtp_class)
    yield mock_server


@pytest.fixture
def mock_requests(monkeypatch: pytest.MonkeyPatch) -> Generator[MagicMock, None, None]:
    """Mock requests.post for webhook testing."""
    mock_response = MagicMock()
    mock_response.status_code = 200
    mock_response.raise_for_status = MagicMock()

    mock_post = MagicMock(return_value=mock_response)
    monkeypatch.setattr(requests, "post", mock_post)
    yield mock_post


@pytest.fixture
def mock_boto3_client(monkeypatch: pytest.MonkeyPatch) -> Generator[MagicMock, None, None]:
    """Mock boto3 S3 client."""
    import boto3

    mock_client = MagicMock()
    mock_boto3 = MagicMock(return_value=mock_client)
    monkeypatch.setattr(boto3, "client", mock_boto3)
    yield mock_client


@pytest.fixture
def sample_config_dict() -> dict:
    """Sample configuration dictionary."""
    return {
        "app_name": "test_app",
        "owner": "test@example.com",
        "tags": ["test", "unit"],
        "log_dir": "logs",
        "log_level": "INFO",
        "notification": {
            "enabled": True,
            "notify_on_success": False,
            "notify_on_failure": True,
            "recipients": ["alerts@example.com"],
        },
        "storage": {
            "enabled": False,
        },
        "redaction": {
            "enabled": True,
        },
    }


@pytest.fixture
def clean_env(monkeypatch: pytest.MonkeyPatch) -> None:
    """Clean environment variables with DTB_ prefix."""
    for key in list(os.environ.keys()):
        if key.startswith("DTB_"):
            monkeypatch.delenv(key, raising=False)
