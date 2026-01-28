"""Type definitions for dt-toolbox."""
from datetime import datetime
from enum import Enum
from typing import Any, Dict, List, Optional

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
    end_time: Optional[datetime] = None
    duration_seconds: Optional[float] = None
    exit_code: int = 0
    success: bool = True
    error_message: Optional[str] = None
    stacktrace: Optional[str] = None
    tags: List[str] = Field(default_factory=list)
    log_file: Optional[str] = None
    log_url: Optional[str] = None


class NotificationConfig(BaseModel):
    """Configuration for notifications."""

    enabled: bool = True
    notify_on_success: bool = False
    notify_on_failure: bool = True
    recipients: List[EmailStr] = Field(default_factory=list)
    smtp_host: Optional[str] = None
    smtp_port: int = 587
    smtp_user: Optional[str] = None
    smtp_password: Optional[str] = None
    smtp_use_tls: bool = True
    webhook_url: Optional[str] = None
    webhook_type: Optional[str] = None  # 'slack' or 'gchat'


class StorageConfig(BaseModel):
    """Configuration for log storage."""

    enabled: bool = False
    backend: StorageBackend = StorageBackend.LOCAL
    bucket_name: Optional[str] = None
    prefix: str = "logs"
    upload_threshold_kb: int = 200
    # AWS S3
    aws_access_key_id: Optional[str] = None
    aws_secret_access_key: Optional[str] = None
    aws_region: Optional[str] = None
    # GCS
    gcs_credentials_path: Optional[str] = None
    # MinIO
    minio_endpoint: Optional[str] = None
    minio_access_key: Optional[str] = None
    minio_secret_key: Optional[str] = None


class RedactionConfig(BaseModel):
    """Configuration for PII redaction."""

    enabled: bool = True
    patterns: List[str] = Field(
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
    tags: List[str] = Field(default_factory=list)
    log_dir: str = "logs"
    log_level: LogLevel = LogLevel.INFO
    log_format: str = "json"
    notification: NotificationConfig = Field(default_factory=NotificationConfig)
    storage: StorageConfig = Field(default_factory=StorageConfig)
    redaction: RedactionConfig = Field(default_factory=RedactionConfig)
    run_id: Optional[str] = None
    trace_id: Optional[str] = None
