"""Scenario-based tests for dt-toolbox.

Test realistic use cases and scenarios that users will encounter.
"""
import logging
import time
from pathlib import Path

import pytest

from dt_toolbox import init_monitoring, monitor


class TestSuccessScenarios:
    """Test various successful execution scenarios."""

    def test_simple_etl_success(self, temp_log_dir):
        """Test a simple ETL job that completes successfully."""
        logger = init_monitoring(
            app_name="simple_etl",
            owner="data@example.com",
            tags=["etl", "hourly"],
            log_dir=temp_log_dir,
        )

        logger.info("ETL job started")
        logger.info("Extracting data from database")
        logger.info("Extracted 1000 records")
        logger.info("Transforming data")
        logger.info("Loading to warehouse")
        logger.info("ETL job completed successfully")

        log_files = list(Path(temp_log_dir).glob("simple_etl/*.log"))
        assert len(log_files) == 1

    def test_batch_processing_success(self, temp_log_dir):
        """Test batch processing scenario."""
        logger = init_monitoring(
            app_name="batch_processor",
            owner="data@example.com",
            tags=["batch", "processing"],
            log_dir=temp_log_dir,
        )

        logger.info("Starting batch processing")

        # Process multiple batches
        for batch_id in range(1, 6):
            logger.info(f"Processing batch {batch_id}/5")
            logger.debug(f"Batch {batch_id} contains 200 items")
            time.sleep(0.01)
            logger.info(f"Batch {batch_id} completed")

        logger.info("All batches processed successfully")

        log_files = list(Path(temp_log_dir).glob("batch_processor/*.log"))
        assert len(log_files) == 1

    def test_data_validation_success(self, temp_log_dir):
        """Test data validation scenario with all checks passing."""
        logger = init_monitoring(
            app_name="data_validator",
            owner="quality@example.com",
            tags=["validation", "quality"],
            log_dir=temp_log_dir,
        )

        checks = [
            "Schema validation",
            "Null check",
            "Data type check",
            "Range validation",
            "Uniqueness check",
        ]

        logger.info("Starting data validation")

        for check in checks:
            logger.info(f"Running: {check}")
            logger.info(f"{check}: PASSED ✓")

        logger.info("All validation checks passed")

        log_files = list(Path(temp_log_dir).glob("data_validator/*.log"))
        assert len(log_files) == 1


class TestFailureScenarios:
    """Test various failure scenarios."""

    def test_database_connection_failure(self, temp_log_dir):
        """Test scenario where database connection fails."""
        logger = init_monitoring(
            app_name="db_connector",
            owner="data@example.com",
            log_dir=temp_log_dir,
        )

        logger.info("Attempting to connect to database")

        try:
            # Simulate connection failure
            raise ConnectionError("Could not connect to database: Connection timeout")
        except ConnectionError as e:
            logger.error(f"Database connection failed: {e}", exc_info=True)

        log_files = list(Path(temp_log_dir).glob("db_connector/*.log"))
        log_content = log_files[0].read_text()
        assert "Connection timeout" in log_content

    def test_data_processing_error(self, temp_log_dir):
        """Test scenario with data processing error."""
        logger = init_monitoring(
            app_name="data_processor",
            owner="data@example.com",
            log_dir=temp_log_dir,
        )

        logger.info("Starting data processing")
        logger.info("Processing record 1 of 100")
        logger.info("Processing record 2 of 100")

        try:
            # Simulate data error
            raise ValueError("Invalid data format in record 3: missing required field")
        except ValueError as e:
            logger.error(f"Data processing error: {e}", exc_info=True)
            logger.info("Stopping processing due to error")

        log_files = list(Path(temp_log_dir).glob("data_processor/*.log"))
        assert len(log_files) == 1

    def test_partial_success_scenario(self, temp_log_dir):
        """Test scenario where some operations succeed and some fail."""
        logger = init_monitoring(
            app_name="partial_processor",
            owner="data@example.com",
            log_dir=temp_log_dir,
        )

        logger.info("Processing 10 files")

        for i in range(1, 11):
            if i == 7:
                logger.error(f"File {i}: Processing failed - file corrupted")
            else:
                logger.info(f"File {i}: Processed successfully")

        logger.warning("Completed with 1 error out of 10 files")

        log_files = list(Path(temp_log_dir).glob("partial_processor/*.log"))
        log_content = log_files[0].read_text()
        assert "failed" in log_content.lower()


class TestPIIRedactionScenarios:
    """Test scenarios involving PII data."""

    def test_redact_user_credentials(self, temp_log_dir):
        """Test redaction of user credentials in logs."""
        logger = init_monitoring(
            app_name="user_auth",
            owner="security@example.com",
            log_dir=temp_log_dir,
            redaction_enabled=True,
        )

        logger.info("User authentication attempt")
        logger.debug("Credentials: username=john, password=secret123")
        logger.info("Authentication successful")

        log_files = list(Path(temp_log_dir).glob("user_auth/*.log"))
        log_content = log_files[0].read_text()

        # Password should be redacted
        assert "secret123" not in log_content

    def test_redact_api_keys(self, temp_log_dir):
        """Test redaction of API keys."""
        logger = init_monitoring(
            app_name="api_client",
            owner="dev@example.com",
            log_dir=temp_log_dir,
            redaction_enabled=True,
        )

        logger.info("Connecting to external API")
        logger.debug("Using api_key=sk_live_abcdef123456789")
        logger.info("API call successful")

        log_files = list(Path(temp_log_dir).glob("api_client/*.log"))
        log_content = log_files[0].read_text()

        # API key should be redacted
        assert "sk_live_abcdef123456789" not in log_content

    def test_redact_payment_info(self, temp_log_dir):
        """Test redaction of payment information."""
        logger = init_monitoring(
            app_name="payment_processor",
            owner="finance@example.com",
            log_dir=temp_log_dir,
            redaction_enabled=True,
        )

        logger.info("Processing payment")
        logger.debug("Card number: 4532-1234-5678-9010")
        logger.debug("CVV: 123")
        logger.info("Payment processed successfully")

        log_files = list(Path(temp_log_dir).glob("payment_processor/*.log"))
        log_content = log_files[0].read_text()

        # Card number should be redacted
        assert "4532-1234-5678-9010" not in log_content


class TestNotificationScenarios:
    """Test notification scenarios."""

    def test_success_notification_disabled(self, temp_log_dir, mock_smtp):
        """Test that success notification is not sent when disabled."""
        logger = init_monitoring(
            app_name="no_success_notify",
            owner="test@example.com",
            recipients=["alert@example.com"],
            log_dir=temp_log_dir,
            smtp_host="smtp.example.com",
            smtp_user="sender@example.com",
            notify_on_success=False,  # Disabled
        )

        logger.info("Operation completed successfully")

        # Success notification should not be sent

    def test_failure_notification_enabled(self, temp_log_dir, mock_smtp):
        """Test that failure notification is sent."""
        logger = init_monitoring(
            app_name="failure_notify",
            owner="test@example.com",
            recipients=["alert@example.com"],
            log_dir=temp_log_dir,
            smtp_host="smtp.example.com",
            smtp_user="sender@example.com",
        )

        logger.info("Starting operation")

        try:
            raise RuntimeError("Critical error occurred")
        except RuntimeError:
            logger.error("Operation failed", exc_info=True)

        # Failure notification should be sent

    def test_multiple_recipients(self, temp_log_dir, mock_smtp):
        """Test notification to multiple recipients."""
        logger = init_monitoring(
            app_name="multi_recipient",
            owner="test@example.com",
            recipients=[
                "team1@example.com",
                "team2@example.com",
                "alert@example.com",
            ],
            log_dir=temp_log_dir,
            smtp_host="smtp.example.com",
            smtp_user="sender@example.com",
            notify_on_success=True,
        )

        logger.info("Task completed")
        # All recipients should receive notification


class TestStorageScenarios:
    """Test log storage scenarios."""

    def test_small_log_no_upload(self, temp_log_dir, mock_boto3_client):
        """Test that small logs are not uploaded."""
        logger = init_monitoring(
            app_name="small_log_app",
            owner="test@example.com",
            log_dir=temp_log_dir,
            storage_enabled=True,
            storage_backend="s3",
            storage_bucket_name="logs",
            storage_upload_threshold_kb=1000,  # High threshold
        )

        # Small amount of logging
        logger.info("Quick operation completed")

        # Should not trigger upload
        mock_boto3_client.upload_file.assert_not_called()

    def test_large_log_with_upload(self, temp_log_dir, mock_boto3_client):
        """Test that large logs are uploaded to S3."""
        logger = init_monitoring(
            app_name="large_log_app",
            owner="test@example.com",
            log_dir=temp_log_dir,
            storage_enabled=True,
            storage_backend="s3",
            storage_bucket_name="logs",
            storage_upload_threshold_kb=1,  # Very low threshold
        )

        # Generate large log
        for i in range(1000):
            logger.info(f"Processing item {i} with detailed information")

        # Should trigger upload


class TestDecoratorScenarios:
    """Test scenarios using the @monitor decorator."""

    def test_decorator_on_simple_function(self, temp_log_dir):
        """Test decorator on a simple function."""

        @monitor(owner="test@example.com", log_dir=temp_log_dir)
        def calculate_sum(a, b):
            logger = logging.getLogger()
            logger.info(f"Calculating sum of {a} and {b}")
            result = a + b
            logger.info(f"Result: {result}")
            return result

        result = calculate_sum(10, 20)
        assert result == 30

        log_files = list(Path(temp_log_dir).glob("calculate_sum/*.log"))
        assert len(log_files) == 1

    def test_decorator_with_exception(self, temp_log_dir):
        """Test decorator when function raises exception."""

        @monitor(owner="test@example.com", log_dir=temp_log_dir)
        def failing_task():
            logger = logging.getLogger()
            logger.info("Starting task")
            raise ValueError("Task failed")

        with pytest.raises(ValueError):
            failing_task()

        log_files = list(Path(temp_log_dir).glob("failing_task/*.log"))
        log_content = log_files[0].read_text()
        assert "Task failed" in log_content

    def test_decorator_with_custom_app_name(self, temp_log_dir):
        """Test decorator with custom app name."""

        @monitor(
            owner="test@example.com",
            app_name="custom_name",
            log_dir=temp_log_dir,
        )
        def my_function():
            logging.getLogger().info("Function executed")

        my_function()

        # Should use custom app name
        log_files = list(Path(temp_log_dir).glob("custom_name/*.log"))
        assert len(log_files) == 1


class TestTaggingScenarios:
    """Test scenarios with different tagging strategies."""

    def test_environment_tags(self, temp_log_dir):
        """Test tagging for different environments."""
        logger = init_monitoring(
            app_name="my_app",
            owner="test@example.com",
            tags=["production", "us-east-1", "critical"],
            log_dir=temp_log_dir,
        )

        logger.info("Application running")

        log_files = list(Path(temp_log_dir).glob("my_app/*.log"))
        log_content = log_files[0].read_text()
        assert "production" in log_content

    def test_feature_tags(self, temp_log_dir):
        """Test tagging for feature categorization."""
        logger = init_monitoring(
            app_name="feature_processor",
            owner="test@example.com",
            tags=["ml", "feature-engineering", "batch"],
            log_dir=temp_log_dir,
        )

        logger.info("Feature processing started")

        log_files = list(Path(temp_log_dir).glob("feature_processor/*.log"))
        log_content = log_files[0].read_text()
        assert "ml" in log_content

    def test_no_tags(self, temp_log_dir):
        """Test operation without any tags."""
        logger = init_monitoring(
            app_name="no_tags_app",
            owner="test@example.com",
            tags=[],
            log_dir=temp_log_dir,
        )

        logger.info("Running without tags")
        # Should work fine without tags


class TestLongRunningScenarios:
    """Test scenarios for long-running processes."""

    def test_long_running_job(self, temp_log_dir):
        """Test monitoring of a long-running job."""
        logger = init_monitoring(
            app_name="long_job",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        logger.info("Long-running job started")

        # Simulate long-running phases
        phases = ["Phase 1: Initialization", "Phase 2: Processing", "Phase 3: Finalization"]

        for phase in phases:
            logger.info(f"Starting {phase}")
            time.sleep(0.1)
            logger.info(f"Completed {phase}")

        logger.info("Long-running job completed")

        log_files = list(Path(temp_log_dir).glob("long_job/*.log"))
        assert len(log_files) == 1

    def test_progress_reporting(self, temp_log_dir):
        """Test progress reporting in long job."""
        logger = init_monitoring(
            app_name="progress_reporter",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        total_items = 100
        logger.info(f"Processing {total_items} items")

        for i in range(0, total_items + 1, 10):
            progress = (i / total_items) * 100
            logger.info(f"Progress: {progress:.1f}% ({i}/{total_items})")
            time.sleep(0.01)

        logger.info("Processing complete")

        log_files = list(Path(temp_log_dir).glob("progress_reporter/*.log"))
        log_content = log_files[0].read_text()
        assert "100.0%" in log_content


class TestMultiEnvironmentScenarios:
    """Test scenarios across different environments."""

    def test_development_environment(self, temp_log_dir):
        """Test configuration for development environment."""
        logger = init_monitoring(
            app_name="dev_app",
            owner="dev@example.com",
            tags=["development"],
            log_dir=temp_log_dir,
            log_level="DEBUG",  # Verbose in dev
            notify_on_success=True,  # Get all notifications in dev
        )

        logger.debug("Debug information visible in dev")
        logger.info("Development test")

    def test_production_environment(self, temp_log_dir):
        """Test configuration for production environment."""
        logger = init_monitoring(
            app_name="prod_app",
            owner="ops@example.com",
            tags=["production"],
            log_dir=temp_log_dir,
            log_level="INFO",  # Less verbose in prod
            notify_on_success=False,  # Only errors in prod
        )

        logger.info("Production operation")

    def test_staging_environment(self, temp_log_dir):
        """Test configuration for staging environment."""
        logger = init_monitoring(
            app_name="staging_app",
            owner="qa@example.com",
            tags=["staging", "pre-prod"],
            log_dir=temp_log_dir,
            log_level="INFO",
        )

        logger.info("Staging test")
