"""Tests for redaction module."""

from dt_toolbox.redaction import Redactor
from dt_toolbox.types import RedactionConfig


def test_redactor_basic():
    """Test basic redaction."""
    config = RedactionConfig(
        enabled=True,
        patterns=[r"password\s*=\s*\w+"],
        replacement="***REDACTED***",
    )
    redactor = Redactor(config)

    text = "Login with password=secret123 to continue"
    result = redactor.redact(text)

    assert "secret123" not in result
    assert "***REDACTED***" in result


def test_redactor_disabled():
    """Test redaction when disabled."""
    config = RedactionConfig(enabled=False)
    redactor = Redactor(config)

    text = "password=secret123"
    result = redactor.redact(text)

    assert result == text


def test_redactor_multiple_patterns():
    """Test redaction with multiple patterns."""
    config = RedactionConfig(
        enabled=True,
        patterns=[
            r"password['\"]?\s*[:=]\s*['\"]?[\w!@#$%^&*()]+",
            r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[\w-]+",
        ],
        replacement="***",
    )
    redactor = Redactor(config)

    text = 'Config: password="mysecret", api_key=abc123def'
    result = redactor.redact(text)

    assert "mysecret" not in result
    assert "abc123def" not in result
    assert "***" in result


def test_redactor_dict():
    """Test dictionary redaction."""
    config = RedactionConfig(
        enabled=True,
        patterns=[r"secret\d+"],
        replacement="XXX",
    )
    redactor = Redactor(config)

    data = {
        "username": "john",
        "password": "secret123",
        "nested": {
            "token": "secret456",
        },
        "items": ["secret789", "normal_value"],
    }

    result = redactor.redact_dict(data)

    assert "secret123" not in result["password"]
    assert "secret456" not in result["nested"]["token"]
    assert "secret789" not in result["items"][0]
    assert result["username"] == "john"
    assert result["items"][1] == "normal_value"


def test_redactor_ssn_pattern():
    """Test SSN redaction with default patterns."""
    config = RedactionConfig(enabled=True)
    redactor = Redactor(config)

    text = "User SSN: 123-45-6789"
    result = redactor.redact(text)

    assert "123-45-6789" not in result


def test_redactor_credit_card():
    """Test credit card redaction with default patterns."""
    config = RedactionConfig(enabled=True)
    redactor = Redactor(config)

    text = "Card: 1234-5678-9012-3456"
    result = redactor.redact(text)

    assert "1234-5678-9012-3456" not in result
