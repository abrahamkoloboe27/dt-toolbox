"""Main monitoring module with init_monitoring and @monitor decorator."""

import atexit
import functools
import logging
import sys
import traceback
from collections.abc import Callable
from datetime import datetime
from typing import Any, Optional, TypeVar

from .config import build_config
from .handlers import setup_logging
from .notifier import create_notifiers
from .redaction import Redactor
from .storage import create_storage_backend
from .types import ExecutionSummary, MonitorConfig, NotificationLevel
from .utils import generate_run_id, generate_trace_id, get_file_size_kb, get_log_file_path

logger = logging.getLogger(__name__)

# Global state for monitoring
_monitor_state: Optional["MonitorState"] = None

F = TypeVar("F", bound=Callable[..., Any])


class MonitorState:
    """Holds monitoring state for the current run."""

    def __init__(self, config: MonitorConfig, log_file: str):
        """Initialize monitor state.

        Args:
            config: Monitor configuration.
            log_file: Path to log file.
        """
        self.config = config
        self.log_file = log_file
        self.start_time = datetime.now()
        self.summary: ExecutionSummary | None = None

        # Setup components
        self.redactor = Redactor(config.redaction)
        self.notifiers = create_notifiers(config.notification)

        if config.storage.enabled:
            self.storage_backend = create_storage_backend(config.storage)
        else:
            self.storage_backend = None

    def create_summary(
        self,
        exit_code: int = 0,
        error_message: str | None = None,
        stacktrace: str | None = None,
    ) -> ExecutionSummary:
        """Create execution summary.

        Args:
            exit_code: Process exit code.
            error_message: Optional error message.
            stacktrace: Optional stack trace.

        Returns:
            Execution summary.
        """
        end_time = datetime.now()
        duration = (end_time - self.start_time).total_seconds()

        # Upload log file if enabled and size threshold exceeded
        log_url = None
        if self.storage_backend and self.log_file:
            file_size_kb = get_file_size_kb(self.log_file)
            if file_size_kb > self.config.storage.upload_threshold_kb:
                try:
                    import os

                    remote_path = f"{self.config.app_name}/{os.path.basename(self.log_file)}"
                    log_url = self.storage_backend.upload_file(self.log_file, remote_path)
                except Exception as e:
                    logger.error(f"Failed to upload log file: {e}")

        summary = ExecutionSummary(
            app_name=self.config.app_name,
            owner=self.config.owner,
            run_id=self.config.run_id or "",
            trace_id=self.config.trace_id or "",
            start_time=self.start_time,
            end_time=end_time,
            duration_seconds=duration,
            exit_code=exit_code,
            success=exit_code == 0 and error_message is None,
            error_message=error_message,
            stacktrace=stacktrace,
            tags=self.config.tags,
            log_file=self.log_file,
            log_url=log_url,
        )

        self.summary = summary
        return summary

    def send_notifications(self, summary: ExecutionSummary) -> None:
        """Send notifications based on execution summary.

        Args:
            summary: Execution summary to send.
        """
        # Determine notification level
        if summary.success:
            level = NotificationLevel.SUCCESS
            should_notify = self.config.notification.notify_on_success
        else:
            level = NotificationLevel.ERROR
            should_notify = self.config.notification.notify_on_failure

        if not should_notify:
            logger.debug(f"Skipping notification for {level.value}")
            return

        # Send via all configured notifiers
        for notifier in self.notifiers:
            try:
                notifier.send(summary, level, self.config.notification.recipients)
            except Exception as e:
                logger.error(f"Failed to send notification via {type(notifier).__name__}: {e}")


def _exception_handler(exc_type: type, exc_value: BaseException, exc_traceback: Any) -> None:
    """Handle uncaught exceptions.

    Args:
        exc_type: Exception type.
        exc_value: Exception value.
        exc_traceback: Exception traceback.
    """
    if _monitor_state is None:
        # Fall back to default handler
        sys.__excepthook__(exc_type, exc_value, exc_traceback)
        return

    # Log the exception
    logger.critical("Uncaught exception", exc_info=(exc_type, exc_value, exc_traceback))

    # Create summary with error info
    error_message = str(exc_value)
    stacktrace = "".join(traceback.format_exception(exc_type, exc_value, exc_traceback))

    summary = _monitor_state.create_summary(
        exit_code=1,
        error_message=error_message,
        stacktrace=stacktrace,
    )

    # Send notifications
    _monitor_state.send_notifications(summary)


def _exit_handler() -> None:
    """Handle normal program exit."""
    if _monitor_state is None:
        return

    # If summary not yet created (no exception), create success summary
    if _monitor_state.summary is None:
        summary = _monitor_state.create_summary(exit_code=0)
        _monitor_state.send_notifications(summary)


def init_monitoring(
    app_name: str,
    owner: str,
    recipients: list[str] | None = None,
    tags: list[str] | None = None,
    notify_on_success: bool = False,
    log_dir: str = "logs",
    config_file: str | None = None,
    **kwargs: Any,
) -> logging.Logger:
    """Initialize monitoring for the application.

    This function sets up logging, exception handling, and notifications.
    Call this at the beginning of your script.

    Args:
        app_name: Application name.
        owner: Owner email address.
        recipients: List of notification recipients.
        tags: List of tags for categorization.
        notify_on_success: Whether to send notifications on success.
        log_dir: Directory for log files.
        config_file: Path to configuration file.
        **kwargs: Additional configuration options.

    Returns:
        Configured logger instance.

    Example:
        >>> from dt_toolbox import init_monitoring
        >>> logger = init_monitoring(
        ...     app_name="etl_orders",
        ...     owner="data-team@company.com",
        ...     recipients=["alerts@company.com"],
        ...     tags=["daily", "etl"],
        ... )
        >>> logger.info("Processing started")
    """
    global _monitor_state

    # Build configuration
    config = build_config(
        app_name=app_name,
        owner=owner,
        recipients=recipients,
        tags=tags or [],
        notify_on_success=notify_on_success,
        config_file=config_file,
        log_dir=log_dir,
        **kwargs,
    )

    # Generate IDs if not provided
    if not config.run_id:
        config.run_id = generate_run_id()
    if not config.trace_id:
        config.trace_id = generate_trace_id()

    # Create log file path
    log_file = get_log_file_path(config.app_name, config.log_dir, config.run_id)

    # Initialize monitor state
    _monitor_state = MonitorState(config, log_file)

    # Setup logging
    logger_instance = setup_logging(config, log_file, _monitor_state.redactor)

    # Install exception hook
    sys.excepthook = _exception_handler

    # Register exit handler
    atexit.register(_exit_handler)

    logger.info(f"Monitoring initialized for {app_name} (run_id: {config.run_id})")

    return logger_instance


def monitor(
    owner: str,
    app_name: str | None = None,
    recipients: list[str] | None = None,
    tags: list[str] | None = None,
    notify_on_success: bool = False,
    **kwargs: Any,
) -> Callable[[F], F]:
    """Decorator for monitoring a function.

    Args:
        owner: Owner email address.
        app_name: Application name (defaults to function name).
        recipients: List of notification recipients.
        tags: List of tags for categorization.
        notify_on_success: Whether to send notifications on success.
        **kwargs: Additional configuration options.

    Returns:
        Decorated function.

    Example:
        >>> from dt_toolbox import monitor
        >>>
        >>> @monitor(owner="data-team@company.com", tags=["ad-hoc"])
        ... def main():
        ...     print("Processing data...")
        ...     # Your code here
        >>>
        >>> if __name__ == "__main__":
        ...     main()
    """

    def decorator(func: F) -> F:
        @functools.wraps(func)
        def wrapper(*args: Any, **func_kwargs: Any) -> Any:
            # Use function name as app_name if not provided
            actual_app_name = app_name or func.__name__

            # Initialize monitoring
            init_monitoring(
                app_name=actual_app_name,
                owner=owner,
                recipients=recipients,
                tags=tags or [],
                notify_on_success=notify_on_success,
                **kwargs,
            )

            # Execute function
            try:
                result = func(*args, **func_kwargs)
                return result
            except Exception:
                # Exception will be handled by exception hook
                raise

        return wrapper  # type: ignore

    return decorator


def get_current_logger() -> logging.Logger:
    """Get the current logger instance.

    Returns:
        Logger instance.
    """
    return logging.getLogger()
