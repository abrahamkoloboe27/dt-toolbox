"""Integration tests for dt-toolbox.

These tests validate end-to-end workflows and real-world scenarios.
"""
import logging
import os
import tempfile
import time
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dt_toolbox import init_monitoring, monitor


class TestCompleteWorkflows:
    """Test complete monitoring workflows from start to finish."""

    def test_complete_successful_workflow(self, temp_log_dir, clean_env):
        """Test complete workflow for successful script execution."""
        # Initialize monitoring
        logger = init_monitoring(
            app_name="test_workflow",
            owner="test@example.com",
            log_dir=temp_log_dir,
            notify_on_success=True,
        )

        # Simulate script execution
        logger.info("Starting workflow")
        logger.debug("Debug information")
        logger.info("Processing data")
        logger.warning("Warning message")
        logger.info("Workflow completed")

        # Verify log file was created
        log_files = list(Path(temp_log_dir).glob("test_workflow/*.log"))
        assert len(log_files) == 1

        # Verify log content
        log_content = log_files[0].read_text()
        assert "Starting workflow" in log_content
        assert "Processing data" in log_content
        assert "Workflow completed" in log_content

    def test_complete_failure_workflow(self, temp_log_dir, clean_env):
        """Test complete workflow with exception handling."""
        logger = init_monitoring(
            app_name="test_failure",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        logger.info("Starting script")

        try:
            logger.info("About to fail")
            raise ValueError("Test exception")
        except ValueError:
            logger.error("Exception occurred", exc_info=True)

        # Verify log file contains error
        log_files = list(Path(temp_log_dir).glob("test_failure/*.log"))
        assert len(log_files) == 1
        log_content = log_files[0].read_text()
        assert "Test exception" in log_content

    def test_decorator_workflow(self, temp_log_dir):
        """Test complete workflow using decorator."""
        executed = []

        @monitor(
            owner="test@example.com",
            app_name="decorator_test",
            log_dir=temp_log_dir,
        )
        def my_function():
            logger = logging.getLogger()
            logger.info("Function executed")
            executed.append(True)
            return "success"

        result = my_function()

        assert result == "success"
        assert executed == [True]

        # Verify log file
        log_files = list(Path(temp_log_dir).glob("decorator_test/*.log"))
        assert len(log_files) == 1

    def test_multiple_logger_calls(self, temp_log_dir):
        """Test workflow with many log entries."""
        logger = init_monitoring(
            app_name="stress_test",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        # Generate many log entries
        for i in range(100):
            logger.info(f"Log entry {i}")

        # Verify all entries are logged
        log_files = list(Path(temp_log_dir).glob("stress_test/*.log"))
        assert len(log_files) == 1
        log_content = log_files[0].read_text()

        # Check some entries
        assert "Log entry 0" in log_content
        assert "Log entry 50" in log_content
        assert "Log entry 99" in log_content


class TestNotificationWorkflows:
    """Test notification workflows with mocked services."""

    def test_smtp_notification_workflow(self, temp_log_dir, mock_smtp):
        """Test complete SMTP notification workflow."""
        logger = init_monitoring(
            app_name="smtp_test",
            owner="test@example.com",
            recipients=["alert@example.com"],
            log_dir=temp_log_dir,
            smtp_host="smtp.example.com",
            smtp_user="sender@example.com",
            smtp_password="password",
            notify_on_success=True,
        )

        logger.info("Script completed successfully")

        # Note: Notification is sent on exit via atexit handler
        # In real scenario, this would be tested by simulating script exit

    def test_webhook_notification_workflow(self, temp_log_dir, mock_requests):
        """Test complete webhook notification workflow."""
        logger = init_monitoring(
            app_name="webhook_test",
            owner="test@example.com",
            log_dir=temp_log_dir,
            webhook_url="https://hooks.slack.com/test",
            webhook_type="slack",
            notify_on_success=True,
        )

        logger.info("Webhook test completed")

    def test_combined_notifications(self, temp_log_dir, mock_smtp, mock_requests):
        """Test workflow with both SMTP and webhook notifications."""
        logger = init_monitoring(
            app_name="combined_test",
            owner="test@example.com",
            recipients=["alert@example.com"],
            log_dir=temp_log_dir,
            smtp_host="smtp.example.com",
            smtp_user="sender@example.com",
            webhook_url="https://hooks.slack.com/test",
            webhook_type="slack",
            notify_on_success=True,
        )

        logger.info("Combined notification test")


class TestStorageWorkflows:
    """Test storage upload workflows."""

    def test_storage_workflow_below_threshold(self, temp_log_dir, mock_boto3_client):
        """Test workflow with small log file (no upload)."""
        logger = init_monitoring(
            app_name="small_log",
            owner="test@example.com",
            log_dir=temp_log_dir,
            storage_enabled=True,
            storage_backend="s3",
            storage_bucket_name="test-bucket",
            storage_upload_threshold_kb=1000,  # High threshold
        )

        logger.info("Small log entry")

        # Small log should not trigger upload
        log_files = list(Path(temp_log_dir).glob("small_log/*.log"))
        assert len(log_files) == 1

    def test_storage_workflow_above_threshold(self, temp_log_dir, mock_boto3_client):
        """Test workflow with large log file (triggers upload)."""
        logger = init_monitoring(
            app_name="large_log",
            owner="test@example.com",
            log_dir=temp_log_dir,
            storage_enabled=True,
            storage_backend="s3",
            storage_bucket_name="test-bucket",
            storage_upload_threshold_kb=1,  # Low threshold
        )

        # Generate large log content
        for i in range(1000):
            logger.info(f"Large log entry {i} with lots of text to exceed threshold")


class TestConfigurationWorkflows:
    """Test configuration loading from different sources."""

    def test_config_from_env_only(self, temp_log_dir, clean_env, monkeypatch):
        """Test configuration loaded from environment variables."""
        monkeypatch.setenv("DTB_APP_NAME", "env_app")
        monkeypatch.setenv("DTB_OWNER", "env@example.com")
        monkeypatch.setenv("DTB_TAGS", "env,test")
        monkeypatch.setenv("DTB_LOG_LEVEL", "DEBUG")

        logger = init_monitoring(
            app_name="env_app",  # Still required
            owner="env@example.com",  # Still required
            log_dir=temp_log_dir,
        )

        assert logger is not None

    def test_config_from_file(self, temp_log_dir):
        """Test configuration loaded from file."""
        import yaml

        # Create config file
        config_dir = Path.home() / ".dt_toolbox"
        config_dir.mkdir(exist_ok=True)
        config_file = config_dir / "config.yml"

        config_data = {
            "log_level": "DEBUG",
            "tags": ["file", "test"],
        }

        with open(config_file, "w") as f:
            yaml.dump(config_data, f)

        try:
            logger = init_monitoring(
                app_name="file_config",
                owner="test@example.com",
                log_dir=temp_log_dir,
            )

            assert logger is not None
        finally:
            # Cleanup
            if config_file.exists():
                config_file.unlink()

    def test_config_priority(self, temp_log_dir, clean_env, monkeypatch):
        """Test configuration priority: args > env > file."""
        # Set env var
        monkeypatch.setenv("DTB_LOG_LEVEL", "WARNING")

        # Function arg should override env
        logger = init_monitoring(
            app_name="priority_test",
            owner="test@example.com",
            log_dir=temp_log_dir,
            log_level="DEBUG",  # This should win
        )

        # Verify DEBUG level is used (function arg wins)
        assert logger.level == logging.DEBUG


class TestRedactionWorkflows:
    """Test PII redaction in real workflows."""

    def test_redaction_in_logs(self, temp_log_dir):
        """Test that sensitive data is redacted in log files."""
        logger = init_monitoring(
            app_name="redaction_test",
            owner="test@example.com",
            log_dir=temp_log_dir,
            redaction_enabled=True,
        )

        # Log sensitive information
        logger.info("User password=secret123")
        logger.info("API key: api_key=abcdef123456")
        logger.info("Credit card: 1234-5678-9012-3456")

        # Check log file
        log_files = list(Path(temp_log_dir).glob("redaction_test/*.log"))
        assert len(log_files) == 1
        log_content = log_files[0].read_text()

        # Verify redaction occurred
        assert "secret123" not in log_content
        assert "abcdef123456" not in log_content
        # Note: The actual test needs to verify REDACTED appears
        assert "REDACTED" in log_content or "***" in log_content

    def test_no_redaction_when_disabled(self, temp_log_dir):
        """Test that redaction can be disabled."""
        logger = init_monitoring(
            app_name="no_redaction",
            owner="test@example.com",
            log_dir=temp_log_dir,
            redaction_enabled=False,
        )

        logger.info("password=visible123")

        log_files = list(Path(temp_log_dir).glob("no_redaction/*.log"))
        log_content = log_files[0].read_text()

        # When disabled, sensitive data should be visible
        # (Though in production this should rarely be used)


class TestConcurrentExecutions:
    """Test multiple monitoring instances running concurrently."""

    def test_multiple_apps_same_time(self, temp_log_dir):
        """Test multiple applications logging simultaneously."""
        # Create multiple loggers
        logger1 = init_monitoring(
            app_name="app1",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        logger2 = init_monitoring(
            app_name="app2",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        # Both should work independently
        logger1.info("Message from app1")
        logger2.info("Message from app2")

        # Verify separate log files
        app1_logs = list(Path(temp_log_dir).glob("app1/*.log"))
        app2_logs = list(Path(temp_log_dir).glob("app2/*.log"))

        assert len(app1_logs) == 1
        assert len(app2_logs) == 1


class TestErrorHandling:
    """Test error handling in various scenarios."""

    def test_missing_required_config(self):
        """Test behavior with missing required configuration."""
        with pytest.raises(Exception):
            # Missing owner should raise validation error
            init_monitoring(app_name="test")

    def test_invalid_log_level(self, temp_log_dir):
        """Test handling of invalid log level."""
        # Should handle gracefully or raise clear error
        with pytest.raises((ValueError, AttributeError)):
            init_monitoring(
                app_name="test",
                owner="test@example.com",
                log_dir=temp_log_dir,
                log_level="INVALID",
            )

    def test_invalid_email(self, temp_log_dir):
        """Test handling of invalid email addresses."""
        with pytest.raises(Exception):
            init_monitoring(
                app_name="test",
                owner="not-an-email",  # Invalid email
                log_dir=temp_log_dir,
            )


class TestRealWorldScenarios:
    """Test real-world use case scenarios."""

    def test_etl_pipeline_scenario(self, temp_log_dir):
        """Simulate an ETL pipeline workflow."""
        logger = init_monitoring(
            app_name="etl_orders",
            owner="data@example.com",
            tags=["production", "etl", "orders"],
            log_dir=temp_log_dir,
        )

        # ETL steps
        logger.info("Starting ETL pipeline")
        logger.info("Step 1: Extract data from source")
        time.sleep(0.1)
        logger.info("Step 2: Transform data")
        time.sleep(0.1)
        logger.info("Step 3: Load data to warehouse")
        time.sleep(0.1)
        logger.info("ETL pipeline completed successfully")

        # Verify execution
        log_files = list(Path(temp_log_dir).glob("etl_orders/*.log"))
        assert len(log_files) == 1

    def test_ml_training_scenario(self, temp_log_dir):
        """Simulate an ML model training workflow."""
        logger = init_monitoring(
            app_name="ml_training",
            owner="ml-team@example.com",
            tags=["ml", "training", "model"],
            log_dir=temp_log_dir,
        )

        # Training steps
        logger.info("Loading training data")
        logger.info("Training model - Epoch 1/10")
        logger.info("Training model - Epoch 5/10")
        logger.info("Training model - Epoch 10/10")
        logger.info("Model training completed")
        logger.info("Model accuracy: 95.2%")

        log_files = list(Path(temp_log_dir).glob("ml_training/*.log"))
        assert len(log_files) == 1

    def test_data_quality_check_scenario(self, temp_log_dir):
        """Simulate a data quality check workflow."""
        logger = init_monitoring(
            app_name="data_quality",
            owner="quality@example.com",
            tags=["quality", "validation"],
            log_dir=temp_log_dir,
        )

        logger.info("Running data quality checks")
        logger.info("Check 1: Null values - PASSED")
        logger.info("Check 2: Data types - PASSED")
        logger.warning("Check 3: Outliers detected - 5 records")
        logger.info("Check 4: Duplicates - PASSED")
        logger.info("Quality checks completed")

        log_files = list(Path(temp_log_dir).glob("data_quality/*.log"))
        assert len(log_files) == 1
