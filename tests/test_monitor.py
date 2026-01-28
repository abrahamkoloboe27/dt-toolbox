"""Tests for monitor module."""
import logging
import sys
from pathlib import Path

import pytest

from dt_toolbox.monitor import init_monitoring, monitor


def test_init_monitoring_basic(temp_log_dir):
    """Test basic monitoring initialization."""
    logger = init_monitoring(
        app_name="test_app",
        owner="test@example.com",
        log_dir=temp_log_dir,
    )
    
    assert logger is not None
    assert isinstance(logger, logging.Logger)
    
    # Check log file was created
    log_files = list(Path(temp_log_dir).glob("test_app/*.log"))
    assert len(log_files) > 0


def test_init_monitoring_with_tags(temp_log_dir):
    """Test monitoring initialization with tags."""
    logger = init_monitoring(
        app_name="test_app",
        owner="test@example.com",
        tags=["test", "unit"],
        log_dir=temp_log_dir,
    )
    
    # Log a message
    logger.info("Test message with tags")
    
    # Check log file contains tags
    log_files = list(Path(temp_log_dir).glob("test_app/*.log"))
    assert len(log_files) > 0
    
    content = log_files[0].read_text()
    assert "test" in content
    assert "unit" in content


def test_init_monitoring_with_recipients(temp_log_dir):
    """Test monitoring initialization with recipients."""
    logger = init_monitoring(
        app_name="test_app",
        owner="test@example.com",
        recipients=["alert1@example.com", "alert2@example.com"],
        log_dir=temp_log_dir,
    )
    
    assert logger is not None


def test_monitor_decorator_basic(temp_log_dir):
    """Test @monitor decorator basic usage."""
    @monitor(
        owner="test@example.com",
        log_dir=temp_log_dir,
    )
    def test_function():
        logging.info("Inside decorated function")
        return "success"
    
    result = test_function()
    
    assert result == "success"
    
    # Check log files were created
    # Function name should be used as app_name
    log_files = list(Path(temp_log_dir).glob("test_function/*.log"))
    assert len(log_files) > 0


def test_monitor_decorator_with_app_name(temp_log_dir):
    """Test @monitor decorator with custom app_name."""
    @monitor(
        owner="test@example.com",
        app_name="custom_app",
        log_dir=temp_log_dir,
    )
    def test_function():
        logging.info("Inside decorated function")
        return 42
    
    result = test_function()
    
    assert result == 42
    
    # Check custom app_name was used
    log_files = list(Path(temp_log_dir).glob("custom_app/*.log"))
    assert len(log_files) > 0


def test_monitor_decorator_with_exception(temp_log_dir):
    """Test @monitor decorator handles exceptions."""
    @monitor(
        owner="test@example.com",
        log_dir=temp_log_dir,
    )
    def failing_function():
        logging.info("About to fail")
        raise ValueError("Test exception")
    
    with pytest.raises(ValueError, match="Test exception"):
        failing_function()
    
    # Check log files were created and contain error
    log_files = list(Path(temp_log_dir).glob("failing_function/*.log"))
    assert len(log_files) > 0
    
    content = log_files[0].read_text()
    assert "Test exception" in content or "About to fail" in content


def test_logging_writes_to_file(temp_log_dir):
    """Test that logging actually writes to file."""
    logger = init_monitoring(
        app_name="test_logging",
        owner="test@example.com",
        log_dir=temp_log_dir,
    )
    
    test_message = "This is a test log message"
    logger.info(test_message)
    logger.warning("Warning message")
    logger.error("Error message")
    
    # Find log file
    log_files = list(Path(temp_log_dir).glob("test_logging/*.log"))
    assert len(log_files) > 0
    
    content = log_files[0].read_text()
    assert test_message in content
    assert "Warning message" in content
    assert "Error message" in content
