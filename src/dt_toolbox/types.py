"""Type definitions for dt-toolbox."""

from datetime import datetime
from enum import Enum

from pydantic import BaseModel, EmailStr, Field


class LogLevel(str, Enum):
    """Log levels."""

    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class NotificationLevel(str, Enum):
    """Notification severity levels."""

    SUCCESS = "success"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class StorageBackend(str, Enum):
    """Storage backend types."""

    S3 = "s3"
    GCS = "gcs"
    MINIO = "minio"
    LOCAL = "local"


class ExecutionSummary(BaseModel):
    """Summary of script execution."""

    app_name: str
    owner: str
    run_id: str
    trace_id: str
    start_time: datetime
    end_time: datetime | None = None
    duration_seconds: float | None = None
    exit_code: int = 0
    success: bool = True
    error_message: str | None = None
    stacktrace: str | None = None
    tags: list[str] = Field(default_factory=list)
    log_file: str | None = None
    log_url: str | None = None


class NotificationConfig(BaseModel):
    """Configuration for notifications."""

    enabled: bool = True
    notify_on_success: bool = False
    notify_on_failure: bool = True
    recipients: list[EmailStr] = Field(default_factory=list)
    smtp_host: str | None = None
    smtp_port: int = 587
    smtp_user: str | None = None
    smtp_password: str | None = None
    smtp_use_tls: bool = True
    webhook_url: str | None = None
    webhook_type: str | None = None  # 'slack' or 'gchat'


class StorageConfig(BaseModel):
    """Configuration for log storage."""

    enabled: bool = False
    backend: StorageBackend = StorageBackend.LOCAL
    bucket_name: str | None = None
    prefix: str = "logs"
    upload_threshold_kb: int = 200
    # AWS S3
    aws_access_key_id: str | None = None
    aws_secret_access_key: str | None = None
    aws_region: str | None = None
    # GCS
    gcs_credentials_path: str | None = None
    # MinIO
    minio_endpoint: str | None = None
    minio_access_key: str | None = None
    minio_secret_key: str | None = None


class RedactionConfig(BaseModel):
    """Configuration for PII redaction."""

    enabled: bool = True
    patterns: list[str] = Field(
        default_factory=lambda: [
            r"password['\"]?\s*[:=]\s*['\"]?[\w!@#$%^&*()]+",
            r"api[_-]?key['\"]?\s*[:=]\s*['\"]?[\w-]+",
            r"secret['\"]?\s*[:=]\s*['\"]?[\w-]+",
            r"\b\d{3}-\d{2}-\d{4}\b",  # SSN
            r"\b\d{4}[- ]?\d{4}[- ]?\d{4}[- ]?\d{4}\b",  # Credit card
        ]
    )
    replacement: str = "***REDACTED***"


class MonitorConfig(BaseModel):
    """Complete monitoring configuration."""

    app_name: str
    owner: EmailStr
    tags: list[str] = Field(default_factory=list)
    log_dir: str = "logs"
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    redaction: RedactionConfig = Field(default_factory=RedactionConfig)
    run_id: str | None = None
    trace_id: str | None = None
