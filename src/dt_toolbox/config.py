"""Configuration management for dt-toolbox."""

import os
from pathlib import Path
from typing import Any

import yaml
from dotenv import load_dotenv

from .types import MonitorConfig

# Load environment variables
load_dotenv()


def _get_env_with_prefix(key: str, prefix: str = "DTB_", default: Any = None) -> Any:
    """Get environment variable with prefix.

    Args:
        key: Variable key without prefix.
        prefix: Environment variable prefix.
        default: Default value if not found.

    Returns:
        Environment variable value or default.
    """
    return os.getenv(f"{prefix}{key}", default)


def load_config_from_file(config_path: str | None = None) -> dict[str, Any]:
    """Load configuration from YAML file.

    Args:
        config_path: Path to config file. If None, tries default location.

    Returns:
        Configuration dictionary.
    """
    if config_path is None:
        # Try default location
        default_path = Path.home() / ".dt_toolbox" / "config.yml"
        if not default_path.exists():
            return {}
        config_path = str(default_path)

    config_file = Path(config_path)
    if not config_file.exists():
        return {}

    with open(config_file) as f:
        return yaml.safe_load(f) or {}


def load_config_from_env() -> dict[str, Any]:
    """Load configuration from environment variables.

    Returns:
        Configuration dictionary from environment.
    """
    config: dict[str, Any] = {}

    # Basic config
    if app_name := _get_env_with_prefix("APP_NAME"):
        config["app_name"] = app_name
    if owner := _get_env_with_prefix("OWNER"):
        config["owner"] = owner
    if log_dir := _get_env_with_prefix("LOG_DIR"):
        config["log_dir"] = log_dir
    if log_level := _get_env_with_prefix("LOG_LEVEL"):
        config["log_level"] = log_level
    if tags := _get_env_with_prefix("TAGS"):
        config["tags"] = [t.strip() for t in tags.split(",")]

    # Notification config
    notification_config: dict[str, Any] = {}
    if smtp_host := _get_env_with_prefix("SMTP_HOST"):
        notification_config["smtp_host"] = smtp_host
    if smtp_port := _get_env_with_prefix("SMTP_PORT"):
        notification_config["smtp_port"] = int(smtp_port)
    if smtp_user := _get_env_with_prefix("SMTP_USER"):
        notification_config["smtp_user"] = smtp_user
    if smtp_password := _get_env_with_prefix("SMTP_PASSWORD"):
        notification_config["smtp_password"] = smtp_password
    if smtp_use_tls := _get_env_with_prefix("SMTP_USE_TLS"):
        notification_config["smtp_use_tls"] = smtp_use_tls.lower() == "true"
    if webhook_url := _get_env_with_prefix("WEBHOOK_URL"):
        notification_config["webhook_url"] = webhook_url
    if webhook_type := _get_env_with_prefix("WEBHOOK_TYPE"):
        notification_config["webhook_type"] = webhook_type
    if recipients := _get_env_with_prefix("RECIPIENTS"):
        notification_config["recipients"] = [r.strip() for r in recipients.split(",")]
    if notify_on_success := _get_env_with_prefix("NOTIFY_ON_SUCCESS"):
        notification_config["notify_on_success"] = notify_on_success.lower() == "true"

    if notification_config:
        config["notification"] = notification_config

    # Storage config
    storage_config: dict[str, Any] = {}
    if storage_enabled := _get_env_with_prefix("STORAGE_ENABLED"):
        storage_config["enabled"] = storage_enabled.lower() == "true"
    if backend := _get_env_with_prefix("STORAGE_BACKEND"):
        storage_config["backend"] = backend
    if bucket_name := _get_env_with_prefix("STORAGE_BUCKET"):
        storage_config["bucket_name"] = bucket_name
    if prefix := _get_env_with_prefix("STORAGE_PREFIX"):
        storage_config["prefix"] = prefix
    if aws_access_key := _get_env_with_prefix("AWS_ACCESS_KEY_ID"):
        storage_config["aws_access_key_id"] = aws_access_key
    if aws_secret_key := _get_env_with_prefix("AWS_SECRET_ACCESS_KEY"):
        storage_config["aws_secret_access_key"] = aws_secret_key
    if aws_region := _get_env_with_prefix("AWS_REGION"):
        storage_config["aws_region"] = aws_region

    if storage_config:
        config["storage"] = storage_config

    # Redaction config
    redaction_config: dict[str, Any] = {}
    if redaction_enabled := _get_env_with_prefix("REDACTION_ENABLED"):
        redaction_config["enabled"] = redaction_enabled.lower() == "true"

    if redaction_config:
        config["redaction"] = redaction_config

    return config


def merge_configs(*configs: dict[str, Any]) -> dict[str, Any]:
    """Merge multiple configuration dictionaries.

    Later configs override earlier ones.

    Args:
        *configs: Configuration dictionaries to merge.

    Returns:
        Merged configuration dictionary.
    """
    result: dict[str, Any] = {}

    for config in configs:
        for key, value in config.items():
            if isinstance(value, dict) and key in result and isinstance(result[key], dict):
                # Recursively merge nested dicts
                result[key] = {**result[key], **value}
            else:
                result[key] = value

    return result


def build_config(
    app_name: str,
    owner: str,
    recipients: list[str] | None = None,
    tags: list[str] | None = None,
    notify_on_success: bool = False,
    config_file: str | None = None,
    **kwargs: Any,
) -> MonitorConfig:
    """Build complete monitoring configuration.

    Priority: function args > env vars > config file

    Args:
        app_name: Application name.
        owner: Owner email.
        recipients: List of notification recipients.
        tags: List of tags for categorization.
        notify_on_success: Whether to notify on success.
        config_file: Path to config file.
        **kwargs: Additional configuration parameters.

    Returns:
        Complete MonitorConfig object.
    """
    # Start with config file
    file_config = load_config_from_file(config_file)

    # Override with env vars
    env_config = load_config_from_env()

    # Build function args config
    args_config: dict[str, Any] = {
        "app_name": app_name,
        "owner": owner,
    }

    if tags is not None:
        args_config["tags"] = tags

    # Handle notification config
    notification_config: dict[str, Any] = {"notify_on_success": notify_on_success}
    if recipients is not None:
        notification_config["recipients"] = recipients
    args_config["notification"] = notification_config

    # Process kwargs and group by prefix (storage_, notification_, redaction_, etc.)
    storage_config: dict[str, Any] = {}
    redaction_config: dict[str, Any] = {}
    
    for key, value in kwargs.items():
        if value is not None:
            if key.startswith("storage_"):
                # Extract storage config parameters
                storage_key = key[8:]  # Remove "storage_" prefix
                storage_config[storage_key] = value
            elif key.startswith("notification_") or key.startswith("smtp_") or key.startswith("webhook_"):
                # Extract notification config parameters
                notification_config[key] = value
            elif key.startswith("redaction_"):
                # Extract redaction config parameters
                redaction_key = key[10:]  # Remove "redaction_" prefix
                redaction_config[redaction_key] = value
            else:
                # Top-level config parameter
                args_config[key] = value
    
    # Add grouped configs if they have content
    if storage_config:
        args_config["storage"] = storage_config
    if redaction_config:
        args_config["redaction"] = redaction_config

    # Merge all configs (file < env < args)
    merged = merge_configs(file_config, env_config, args_config)

    # Build and validate with Pydantic
    return MonitorConfig(**merged)
