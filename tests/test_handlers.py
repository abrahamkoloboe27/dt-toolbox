"""Tests for handlers module."""
import logging
from pathlib import Path

import pytest

from dt_toolbox.handlers import JSONFormatter, setup_logging
from dt_toolbox.types import MonitorConfig


def test_json_formatter():
    """Test JSON formatter."""
    formatter = JSONFormatter(
        run_id="test_run_123",
        trace_id="trace_456",
        tags=["test", "unit"],
    )
    
    record = logging.LogRecord(
        name="test_logger",
        level=logging.INFO,
        pathname="test.py",
        lineno=42,
        msg="Test message",
        args=(),
        exc_info=None,
    )
    
    result = formatter.format(record)
    
    assert "test_run_123" in result
    assert "trace_456" in result
    assert "Test message" in result
    assert "INFO" in result
    assert '"tags": ["test", "unit"]' in result


def test_setup_logging(temp_log_dir):
    """Test logging setup."""
    config = MonitorConfig(
        app_name="test_app",
        owner="test@example.com",
        run_id="run_123",
        trace_id="trace_456",
        tags=["test"],
        log_dir=temp_log_dir,
    )
    
    log_file = Path(temp_log_dir) / "test_app" / "test.log"
    log_file.parent.mkdir(parents=True, exist_ok=True)
    
    logger = setup_logging(config, str(log_file))
    
    assert logger is not None
    assert len(logger.handlers) == 2  # File + Console
    
    # Test logging
    logger.info("Test log message")
    
    # Check log file was created and written
    assert log_file.exists()
    content = log_file.read_text()
    assert "Test log message" in content


def test_setup_logging_creates_directory(temp_log_dir):
    """Test that setup_logging creates log directory if it doesn't exist."""
    config = MonitorConfig(
        app_name="test_app",
        owner="test@example.com",
        run_id="run_123",
        trace_id="trace_456",
    )
    
    log_file = Path(temp_log_dir) / "new_dir" / "test.log"
    
    logger = setup_logging(config, str(log_file))
    
    # Directory should be created
    assert log_file.parent.exists()
    
    # Test writing
    logger.info("Test message")
    assert log_file.exists()
