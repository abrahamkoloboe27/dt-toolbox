"""Storage backends for log uploads."""
import logging
from abc import ABC, abstractmethod
from pathlib import Path
from typing import Optional
from urllib.parse import urljoin

import boto3
from botocore.exceptions import ClientError

from .types import StorageConfig

logger = logging.getLogger(__name__)


class StorageBackend(ABC):
    """Abstract base class for storage backends."""
    
    @abstractmethod
    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """Upload file to storage.
        
        Args:
            local_path: Local file path.
            remote_path: Remote file path/key.
            
        Returns:
            URL to the uploaded file, or None if failed.
        """
        pass


class LocalStorageBackend(StorageBackend):
    """Local file system storage (for testing)."""
    
    def __init__(self, base_path: str = "/tmp/dt-toolbox-logs"):
        """Initialize local storage.
        
        Args:
            base_path: Base directory for stored logs.
        """
        self.base_path = Path(base_path)
        self.base_path.mkdir(parents=True, exist_ok=True)
    
    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """Copy file to local storage.
        
        Args:
            local_path: Local file path.
            remote_path: Destination path.
            
        Returns:
            File path URL.
        """
        try:
            import shutil
            
            dest = self.base_path / remote_path
            dest.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(local_path, dest)
            return f"file://{dest}"
        except Exception as e:
            logger.error(f"Failed to copy file locally: {e}")
            return None


class S3StorageBackend(StorageBackend):
    """AWS S3 storage backend."""
    
    def __init__(self, config: StorageConfig):
        """Initialize S3 storage.
        
        Args:
            config: Storage configuration.
        """
        self.config = config
        self.bucket_name = config.bucket_name
        self.prefix = config.prefix
        
        # Initialize S3 client
        session_kwargs = {}
        if config.aws_access_key_id:
            session_kwargs["aws_access_key_id"] = config.aws_access_key_id
        if config.aws_secret_access_key:
            session_kwargs["aws_secret_access_key"] = config.aws_secret_access_key
        if config.aws_region:
            session_kwargs["region_name"] = config.aws_region
        
        self.s3_client = boto3.client("s3", **session_kwargs)
    
    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """Upload file to S3.
        
        Args:
            local_path: Local file path.
            remote_path: S3 key (within bucket).
            
        Returns:
            S3 URL to the uploaded file, or None if failed.
        """
        try:
            full_key = f"{self.prefix}/{remote_path}".lstrip("/")
            
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                full_key,
                ExtraArgs={"ContentType": "text/plain"},
            )
            
            # Generate URL
            url = f"s3://{self.bucket_name}/{full_key}"
            logger.info(f"Uploaded log to S3: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to upload to S3: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading to S3: {e}")
            return None


class MinIOStorageBackend(StorageBackend):
    """MinIO storage backend (S3-compatible)."""
    
    def __init__(self, config: StorageConfig):
        """Initialize MinIO storage.
        
        Args:
            config: Storage configuration.
        """
        self.config = config
        self.bucket_name = config.bucket_name
        self.prefix = config.prefix
        
        # Initialize MinIO client (using boto3 with custom endpoint)
        self.s3_client = boto3.client(
            "s3",
            endpoint_url=config.minio_endpoint,
            aws_access_key_id=config.minio_access_key,
            aws_secret_access_key=config.minio_secret_key,
        )
    
    def upload_file(self, local_path: str, remote_path: str) -> Optional[str]:
        """Upload file to MinIO.
        
        Args:
            local_path: Local file path.
            remote_path: MinIO key.
            
        Returns:
            MinIO URL to the uploaded file, or None if failed.
        """
        try:
            full_key = f"{self.prefix}/{remote_path}".lstrip("/")
            
            self.s3_client.upload_file(
                local_path,
                self.bucket_name,
                full_key,
                ExtraArgs={"ContentType": "text/plain"},
            )
            
            # Generate URL
            url = f"{self.config.minio_endpoint}/{self.bucket_name}/{full_key}"
            logger.info(f"Uploaded log to MinIO: {url}")
            return url
            
        except ClientError as e:
            logger.error(f"Failed to upload to MinIO: {e}")
            return None
        except Exception as e:
            logger.error(f"Unexpected error uploading to MinIO: {e}")
            return None


def create_storage_backend(config: StorageConfig) -> StorageBackend:
    """Create appropriate storage backend based on configuration.
    
    Args:
        config: Storage configuration.
        
    Returns:
        Storage backend instance.
        
    Raises:
        ValueError: If backend type is not supported.
    """
    if config.backend == "s3":
        return S3StorageBackend(config)
    elif config.backend == "minio":
        return MinIOStorageBackend(config)
    elif config.backend == "local":
        return LocalStorageBackend()
    else:
        raise ValueError(f"Unsupported storage backend: {config.backend}")
