"""Tests for configuration module."""

import os
import tempfile

import yaml

from dt_toolbox.config import (
    build_config,
    load_config_from_env,
    load_config_from_file,
    merge_configs,
)


def test_load_config_from_nonexistent_file():
    """Test loading config from non-existent file returns empty dict."""
    config = load_config_from_file("/nonexistent/path.yml")
    assert config == {}


def test_load_config_from_file():
    """Test loading config from YAML file."""
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yml", delete=False) as f:
        config_data = {
            "app_name": "test_app",
            "owner": "test@example.com",
            "tags": ["test"],
        }
        yaml.dump(config_data, f)
        config_path = f.name

    try:
        config = load_config_from_file(config_path)
        assert config["app_name"] == "test_app"
        assert config["owner"] == "test@example.com"
        assert config["tags"] == ["test"]
    finally:
        os.unlink(config_path)


def test_load_config_from_env(clean_env, monkeypatch):
    """Test loading config from environment variables."""
    monkeypatch.setenv("DTB_APP_NAME", "env_app")
    monkeypatch.setenv("DTB_OWNER", "env@example.com")
    monkeypatch.setenv("DTB_TAGS", "tag1,tag2,tag3")
    monkeypatch.setenv("DTB_SMTP_HOST", "smtp.example.com")
    monkeypatch.setenv("DTB_SMTP_PORT", "587")
    monkeypatch.setenv("DTB_NOTIFY_ON_SUCCESS", "true")

    config = load_config_from_env()

    assert config["app_name"] == "env_app"
    assert config["owner"] == "env@example.com"
    assert config["tags"] == ["tag1", "tag2", "tag3"]
    assert config["notification"]["smtp_host"] == "smtp.example.com"
    assert config["notification"]["smtp_port"] == 587
    assert config["notification"]["notify_on_success"] is True


def test_merge_configs():
    """Test merging multiple configuration dictionaries."""
    config1 = {
        "app_name": "app1",
        "owner": "owner1@example.com",
        "notification": {"smtp_host": "smtp1.com"},
    }

    config2 = {
        "app_name": "app2",
        "notification": {"smtp_port": 587},
    }

    config3 = {
        "tags": ["tag1"],
    }

    merged = merge_configs(config1, config2, config3)

    assert merged["app_name"] == "app2"  # Later config overrides
    assert merged["owner"] == "owner1@example.com"
    assert merged["notification"]["smtp_host"] == "smtp1.com"
    assert merged["notification"]["smtp_port"] == 587
    assert merged["tags"] == ["tag1"]


def test_build_config_basic():
    """Test building basic configuration."""
    config = build_config(
        app_name="test_app",
        owner="test@example.com",
        recipients=["alert@example.com"],
        tags=["test"],
    )

    assert config.app_name == "test_app"
    assert config.owner == "test@example.com"
    assert config.notification.recipients == ["alert@example.com"]
    assert config.tags == ["test"]
    assert config.notification.notify_on_success is False


def test_build_config_with_env_override(clean_env, monkeypatch):
    """Test that env vars override file config."""
    monkeypatch.setenv("DTB_SMTP_HOST", "env-smtp.example.com")

    config = build_config(
        app_name="test_app",
        owner="test@example.com",
    )

    assert config.notification.smtp_host == "env-smtp.example.com"


def test_build_config_notify_on_success():
    """Test notify_on_success parameter."""
    config = build_config(
        app_name="test_app",
        owner="test@example.com",
        notify_on_success=True,
    )

    assert config.notification.notify_on_success is True
