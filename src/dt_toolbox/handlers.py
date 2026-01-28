"""Logging handlers for dt-toolbox."""
import json
import logging
import sys
from datetime import datetime
from logging.handlers import TimedRotatingFileHandler
from pathlib import Path
from typing import Any, Dict, Optional

from .redaction import Redactor
from .types import MonitorConfig
from .utils import ensure_dir


class JSONFormatter(logging.Formatter):
    """JSON log formatter with structured output."""
    
    def __init__(
        self,
        run_id: str,
        trace_id: str,
        tags: list[str],
        redactor: Optional[Redactor] = None,
    ):
        """Initialize JSON formatter.
        
        Args:
            run_id: Unique run identifier.
            trace_id: Unique trace identifier.
            tags: List of tags for categorization.
            redactor: Optional redactor for PII masking.
        """
        super().__init__()
        self.run_id = run_id
        self.trace_id = trace_id
        self.tags = tags
        self.redactor = redactor
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.
        
        Args:
            record: Log record to format.
            
        Returns:
            JSON formatted log string.
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
            "message": record.getMessage(),
            "run_id": self.run_id,
            "trace_id": self.trace_id,
            "tags": self.tags,
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, "extra"):
            log_data.update(record.extra)
        
        # Redact sensitive information
        if self.redactor:
            log_data = self.redactor.redact_dict(log_data)
        
        return json.dumps(log_data)


def setup_logging(config: MonitorConfig, log_file: str, redactor: Optional[Redactor] = None) -> logging.Logger:
    """Setup logging with file and console handlers.
    
    Args:
        config: Monitor configuration.
        log_file: Path to log file.
        redactor: Optional redactor for PII masking.
        
    Returns:
        Configured root logger.
    """
    # Get root logger
    logger = logging.getLogger()
    logger.setLevel(getattr(logging, config.log_level.value))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    if config.log_format == "json":
        formatter = JSONFormatter(
            run_id=config.run_id or "",
            trace_id=config.trace_id or "",
            tags=config.tags,
            redactor=redactor,
        )
    else:
        # Standard text formatter
        formatter = logging.Formatter(
            '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
            datefmt='%Y-%m-%d %H:%M:%S'
        )
    
    # File handler with daily rotation
    log_dir = Path(log_file).parent
    ensure_dir(str(log_dir))
    
    file_handler = TimedRotatingFileHandler(
        log_file,
        when="midnight",
        interval=1,
        backupCount=30,
        encoding="utf-8",
    )
    file_handler.setLevel(logging.DEBUG)
    file_handler.setFormatter(formatter)
    logger.addHandler(file_handler)
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, config.log_level.value))
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    return logger
