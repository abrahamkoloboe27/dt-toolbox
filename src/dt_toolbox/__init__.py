"""dt-toolbox: Monitoring and alerting toolbox for data teams.

This package provides a simple API for adding monitoring, logging,
and alerting to data scripts and applications.

Example:
    >>> from dt_toolbox import init_monitoring
    >>>
    >>> logger = init_monitoring(
    ...     app_name="etl_orders",
    ...     owner="data-team@company.com",
    ...     recipients=["alerts@company.com"],
    ...     tags=["daily", "etl"],
    ... )
    >>>
    >>> logger.info("Processing started")
    >>> # Your code here
    >>> logger.info("Processing complete")
"""

__version__ = "0.1.0"

from .monitor import get_current_logger, init_monitoring, monitor

__all__ = [
    "init_monitoring",
    "monitor",
    "get_current_logger",
    "__version__",
]
