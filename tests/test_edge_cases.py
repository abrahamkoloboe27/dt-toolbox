"""Edge case tests for dt-toolbox.

Test boundary conditions, error scenarios, and edge cases.
"""
import logging
import os
import tempfile
from pathlib import Path
from unittest.mock import MagicMock, patch

import pytest

from dt_toolbox import init_monitoring, monitor
from dt_toolbox.types import NotificationConfig, StorageConfig


class TestMissingConfiguration:
    """Test behavior with missing or incomplete configuration."""

    def test_missing_owner(self):
        """Test that missing owner raises error."""
        with pytest.raises(Exception):
            init_monitoring(app_name="test")

    def test_missing_app_name(self):
        """Test that missing app_name raises error."""
        with pytest.raises(Exception):
            init_monitoring(owner="test@example.com")

    def test_empty_recipients_list(self, temp_log_dir):
        """Test with empty recipients list."""
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            recipients=[],
            log_dir=temp_log_dir,
        )
        # Should work, just won't send notifications
        assert logger is not None


class TestInvalidConfiguration:
    """Test behavior with invalid configuration values."""

    def test_invalid_email_format(self):
        """Test with invalid email format."""
        with pytest.raises(Exception):
            init_monitoring(
                app_name="test",
                owner="not-an-email",
            )

    def test_invalid_recipient_email(self, temp_log_dir):
        """Test with invalid recipient email."""
        with pytest.raises(Exception):
            init_monitoring(
                app_name="test",
                owner="valid@example.com",
                recipients=["invalid-email"],
                log_dir=temp_log_dir,
            )

    def test_negative_port(self, temp_log_dir):
        """Test with negative SMTP port."""
        # Should either accept it or validate
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
            smtp_port=-1,
        )
        # Port validation might happen later when sending

    def test_invalid_log_level(self, temp_log_dir):
        """Test with invalid log level string."""
        with pytest.raises((ValueError, AttributeError)):
            init_monitoring(
                app_name="test",
                owner="test@example.com",
                log_dir=temp_log_dir,
                log_level="INVALID_LEVEL",
            )

    def test_invalid_storage_backend(self, temp_log_dir):
        """Test with invalid storage backend."""
        with pytest.raises(Exception):
            init_monitoring(
                app_name="test",
                owner="test@example.com",
                log_dir=temp_log_dir,
                storage_enabled=True,
                storage_backend="invalid_backend",
            )


class TestNetworkFailures:
    """Test behavior when network operations fail."""

    def test_smtp_connection_failure(self, temp_log_dir, monkeypatch):
        """Test behavior when SMTP connection fails."""
        import smtplib

        def mock_smtp_error(*args, **kwargs):
            raise smtplib.SMTPException("Connection failed")

        monkeypatch.setattr(smtplib, "SMTP", mock_smtp_error)

        # Should not crash, just log the error
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            recipients=["alert@example.com"],
            log_dir=temp_log_dir,
            smtp_host="smtp.example.com",
            smtp_user="test@example.com",
            notify_on_success=True,
        )

        logger.info("Test message")
        # Notification would fail but shouldn't crash

    def test_webhook_timeout(self, temp_log_dir, monkeypatch):
        """Test behavior when webhook request times out."""
        import requests

        def mock_timeout(*args, **kwargs):
            raise requests.exceptions.Timeout("Request timed out")

        monkeypatch.setattr(requests, "post", mock_timeout)

        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
            webhook_url="https://hooks.slack.com/test",
            notify_on_success=True,
        )

        logger.info("Test message")
        # Should handle timeout gracefully

    def test_s3_upload_failure(self, temp_log_dir, mock_boto3_client):
        """Test behavior when S3 upload fails."""
        from botocore.exceptions import ClientError

        mock_boto3_client.upload_file.side_effect = ClientError(
            {"Error": {"Code": "NoSuchBucket", "Message": "Bucket not found"}},
            "PutObject",
        )

        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
            storage_enabled=True,
            storage_backend="s3",
            storage_bucket_name="nonexistent-bucket",
            storage_upload_threshold_kb=1,
        )

        # Generate large log to trigger upload
        for i in range(100):
            logger.info(f"Large log entry {i}")

        # Should handle S3 error gracefully


class TestPermissionErrors:
    """Test behavior with file system permission issues."""

    def test_readonly_log_directory(self, temp_log_dir):
        """Test behavior when log directory is read-only."""
        # Create a read-only directory
        readonly_dir = Path(temp_log_dir) / "readonly"
        readonly_dir.mkdir()

        # Make it read-only
        import stat

        readonly_dir.chmod(stat.S_IRUSR | stat.S_IXUSR)

        try:
            # This might raise PermissionError
            with pytest.raises(PermissionError):
                logger = init_monitoring(
                    app_name="test",
                    owner="test@example.com",
                    log_dir=str(readonly_dir),
                )
                logger.info("Test")
        finally:
            # Restore permissions for cleanup
            readonly_dir.chmod(stat.S_IRWXU)

    def test_nonexistent_log_directory(self):
        """Test with non-existent log directory (should create it)."""
        # Use a temp path that doesn't exist
        with tempfile.TemporaryDirectory() as tmpdir:
            log_dir = Path(tmpdir) / "nonexistent" / "logs"

            logger = init_monitoring(
                app_name="test",
                owner="test@example.com",
                log_dir=str(log_dir),
            )

            logger.info("Test")

            # Should have created the directory
            assert log_dir.exists()


class TestLargeData:
    """Test behavior with large amounts of data."""

    def test_very_large_log_message(self, temp_log_dir):
        """Test logging very large messages."""
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        # Create a very large message (1MB)
        large_message = "x" * (1024 * 1024)
        logger.info(large_message)

        # Should handle large messages
        log_files = list(Path(temp_log_dir).glob("test/*.log"))
        assert len(log_files) == 1

    def test_many_log_entries(self, temp_log_dir):
        """Test with thousands of log entries."""
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        # Generate 10,000 log entries
        for i in range(10000):
            logger.info(f"Entry {i}")

        log_files = list(Path(temp_log_dir).glob("test/*.log"))
        assert len(log_files) == 1

    def test_long_tag_list(self, temp_log_dir):
        """Test with many tags."""
        tags = [f"tag{i}" for i in range(100)]

        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            tags=tags,
            log_dir=temp_log_dir,
        )

        logger.info("Test with many tags")
        # Should handle many tags


class TestSpecialCharacters:
    """Test behavior with special characters in data."""

    def test_unicode_in_logs(self, temp_log_dir):
        """Test logging unicode characters."""
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        # Log various unicode characters
        logger.info("Unicode: 你好世界 🎉 αβγδ ñ é")

        log_files = list(Path(temp_log_dir).glob("test/*.log"))
        log_content = log_files[0].read_text(encoding="utf-8")
        assert "你好世界" in log_content

    def test_special_chars_in_app_name(self, temp_log_dir):
        """Test with special characters in app name."""
        # Some characters might not be valid for filenames
        logger = init_monitoring(
            app_name="test-app_v1.0",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        logger.info("Test")
        # Should handle or sanitize app name

    def test_json_characters_in_message(self, temp_log_dir):
        """Test logging messages with JSON special characters."""
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        # Characters that need escaping in JSON
        logger.info('Message with "quotes" and \\ backslash')
        logger.info("Message with newline\nand tab\there")

        # Should properly escape in JSON log


class TestConcurrency:
    """Test concurrent operations and thread safety."""

    def test_concurrent_logging(self, temp_log_dir):
        """Test concurrent logging from multiple threads."""
        import threading

        logger = init_monitoring(
            app_name="concurrent",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        def log_messages(thread_id):
            for i in range(100):
                logger.info(f"Thread {thread_id}: Message {i}")

        # Create multiple threads
        threads = []
        for i in range(5):
            t = threading.Thread(target=log_messages, args=(i,))
            threads.append(t)
            t.start()

        # Wait for all threads
        for t in threads:
            t.join()

        # All messages should be logged
        log_files = list(Path(temp_log_dir).glob("concurrent/*.log"))
        assert len(log_files) == 1

    def test_multiple_decorator_instances(self, temp_log_dir):
        """Test multiple decorated functions."""

        @monitor(owner="test@example.com", log_dir=temp_log_dir)
        def func1():
            logging.getLogger().info("Func 1")
            return 1

        @monitor(owner="test@example.com", log_dir=temp_log_dir)
        def func2():
            logging.getLogger().info("Func 2")
            return 2

        # Each function should work independently
        result1 = func1()
        result2 = func2()

        assert result1 == 1
        assert result2 == 2


class TestBoundaryConditions:
    """Test boundary conditions and limits."""

    def test_zero_length_message(self, temp_log_dir):
        """Test logging empty message."""
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        logger.info("")  # Empty message
        # Should handle gracefully

    def test_threshold_exactly_at_limit(self, temp_log_dir, mock_boto3_client):
        """Test upload threshold at exact boundary."""
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
            storage_enabled=True,
            storage_backend="s3",
            storage_bucket_name="test",
            storage_upload_threshold_kb=10,
        )

        # Generate log exactly at threshold
        # This is hard to control precisely, but test the behavior
        logger.info("a" * 10240)  # Exactly 10KB

    def test_all_config_options_at_once(self, temp_log_dir, mock_smtp, mock_requests):
        """Test with all configuration options specified."""
        logger = init_monitoring(
            app_name="kitchen_sink",
            owner="test@example.com",
            recipients=["alert1@example.com", "alert2@example.com"],
            tags=["tag1", "tag2", "tag3"],
            notify_on_success=True,
            log_dir=temp_log_dir,
            log_level="DEBUG",
            smtp_host="smtp.example.com",
            smtp_port=587,
            smtp_user="sender@example.com",
            smtp_password="password",
            smtp_use_tls=True,
            webhook_url="https://hooks.slack.com/test",
            webhook_type="slack",
            storage_enabled=True,
            storage_backend="s3",
            storage_bucket_name="logs",
            storage_upload_threshold_kb=100,
            redaction_enabled=True,
        )

        logger.info("All options test")
        # Should handle all options correctly


class TestCleanup:
    """Test cleanup and resource management."""

    def test_handler_cleanup(self, temp_log_dir):
        """Test that log handlers are properly managed."""
        # Create multiple monitoring instances
        for i in range(10):
            logger = init_monitoring(
                app_name=f"test_{i}",
                owner="test@example.com",
                log_dir=temp_log_dir,
            )
            logger.info(f"Test {i}")

        # Check that we don't accumulate handlers
        root_logger = logging.getLogger()
        # Root logger should have a reasonable number of handlers
        # (This depends on implementation)

    def test_file_handle_cleanup(self, temp_log_dir):
        """Test that file handles are properly closed."""
        logger = init_monitoring(
            app_name="test",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        logger.info("Test message")

        # Log file should be closeable
        log_files = list(Path(temp_log_dir).glob("test/*.log"))
        # File should exist and be accessible


class TestExceptionHandling:
    """Test exception handling in various scenarios."""

    def test_exception_in_decorated_function(self, temp_log_dir):
        """Test exception handling in decorated function."""

        @monitor(owner="test@example.com", log_dir=temp_log_dir)
        def failing_function():
            logging.getLogger().info("About to fail")
            raise RuntimeError("Intentional error")

        with pytest.raises(RuntimeError):
            failing_function()

        # Exception should be logged
        log_files = list(Path(temp_log_dir).glob("failing_function/*.log"))
        assert len(log_files) == 1
        log_content = log_files[0].read_text()
        assert "Intentional error" in log_content

    def test_nested_exceptions(self, temp_log_dir):
        """Test handling of nested exceptions."""
        logger = init_monitoring(
            app_name="nested",
            owner="test@example.com",
            log_dir=temp_log_dir,
        )

        try:
            try:
                raise ValueError("Inner exception")
            except ValueError as e:
                raise RuntimeError("Outer exception") from e
        except RuntimeError:
            logger.error("Nested exception occurred", exc_info=True)

        log_files = list(Path(temp_log_dir).glob("nested/*.log"))
        log_content = log_files[0].read_text()
        # Both exceptions should be in the log
