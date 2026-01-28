"""Utility functions for dt-toolbox."""
import os
import uuid
from datetime import datetime
from pathlib import Path
from typing import Optional


def generate_run_id() -> str:
    """Generate a unique run ID.
    
    Returns:
        A unique run identifier combining timestamp and UUID.
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    unique_id = str(uuid.uuid4())[:8]
    return f"{timestamp}_{unique_id}"


def generate_trace_id() -> str:
    """Generate a unique trace ID.
    
    Returns:
        A unique trace identifier.
    """
    return str(uuid.uuid4())


def ensure_dir(path: str) -> Path:
    """Ensure directory exists, create if not.
    
    Args:
        path: Directory path to ensure.
        
    Returns:
        Path object for the directory.
    """
    dir_path = Path(path)
    dir_path.mkdir(parents=True, exist_ok=True)
    return dir_path


def get_log_file_path(app_name: str, log_dir: str = "logs", run_id: Optional[str] = None) -> str:
    """Generate log file path.
    
    Args:
        app_name: Application name.
        log_dir: Base directory for logs.
        run_id: Optional run ID. If not provided, generates one.
        
    Returns:
        Full path to the log file.
    """
    if run_id is None:
        run_id = generate_run_id()
    
    app_log_dir = Path(log_dir) / app_name
    ensure_dir(str(app_log_dir))
    
    log_file = app_log_dir / f"{run_id}.log"
    return str(log_file)


def format_duration(seconds: float) -> str:
    """Format duration in human-readable format.
    
    Args:
        seconds: Duration in seconds.
        
    Returns:
        Formatted duration string.
    """
    if seconds < 1:
        return f"{seconds * 1000:.2f}ms"
    elif seconds < 60:
        return f"{seconds:.2f}s"
    elif seconds < 3600:
        minutes = int(seconds // 60)
        secs = seconds % 60
        return f"{minutes}m {secs:.2f}s"
    else:
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = seconds % 60
        return f"{hours}h {minutes}m {secs:.2f}s"


def get_file_size_kb(file_path: str) -> float:
    """Get file size in KB.
    
    Args:
        file_path: Path to file.
        
    Returns:
        File size in KB.
    """
    try:
        return os.path.getsize(file_path) / 1024
    except OSError:
        return 0.0


def truncate_string(text: str, max_length: int = 1000, suffix: str = "...") -> str:
    """Truncate string to maximum length.
    
    Args:
        text: Text to truncate.
        max_length: Maximum length.
        suffix: Suffix to add if truncated.
        
    Returns:
        Truncated string.
    """
    if len(text) <= max_length:
        return text
    return text[: max_length - len(suffix)] + suffix
