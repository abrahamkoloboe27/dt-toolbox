"""Tests for storage module."""
import tempfile
from pathlib import Path

import pytest

from dt_toolbox.storage import (
    LocalStorageBackend,
    S3StorageBackend,
    create_storage_backend,
)
from dt_toolbox.types import StorageBackend, StorageConfig


def test_local_storage_backend():
    """Test local storage backend."""
    with tempfile.TemporaryDirectory() as tmpdir:
        backend = LocalStorageBackend(tmpdir)
        
        # Create a test file
        with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
            f.write("Test log content")
            test_file = f.name
        
        try:
            # Upload file
            result_url = backend.upload_file(test_file, "app/test.log")
            
            assert result_url is not None
            assert "file://" in result_url
            
            # Check file was copied
            dest_file = Path(tmpdir) / "app" / "test.log"
            assert dest_file.exists()
            assert dest_file.read_text() == "Test log content"
        finally:
            import os
            os.unlink(test_file)


def test_s3_storage_backend(mock_boto3_client):
    """Test S3 storage backend."""
    config = StorageConfig(
        enabled=True,
        backend=StorageBackend.S3,
        bucket_name="test-bucket",
        prefix="logs",
        aws_access_key_id="test_key",
        aws_secret_access_key="test_secret",
        aws_region="us-east-1",
    )
    
    backend = S3StorageBackend(config)
    
    # Create a test file
    with tempfile.NamedTemporaryFile(mode="w", delete=False) as f:
        f.write("Test log content")
        test_file = f.name
    
    try:
        # Upload file
        result_url = backend.upload_file(test_file, "app/test.log")
        
        assert result_url is not None
        assert "s3://" in result_url
        assert "test-bucket" in result_url
        
        # Check boto3 was called
        mock_boto3_client.upload_file.assert_called_once()
    finally:
        import os
        os.unlink(test_file)


def test_create_storage_backend_s3():
    """Test creating S3 storage backend."""
    config = StorageConfig(
        backend=StorageBackend.S3,
        bucket_name="test-bucket",
    )
    
    backend = create_storage_backend(config)
    
    assert isinstance(backend, S3StorageBackend)


def test_create_storage_backend_local():
    """Test creating local storage backend."""
    config = StorageConfig(backend=StorageBackend.LOCAL)
    
    backend = create_storage_backend(config)
    
    assert isinstance(backend, LocalStorageBackend)


def test_create_storage_backend_invalid():
    """Test creating storage backend with invalid type."""
    config = StorageConfig(backend="invalid")  # type: ignore
    
    with pytest.raises(ValueError, match="Unsupported storage backend"):
        create_storage_backend(config)
