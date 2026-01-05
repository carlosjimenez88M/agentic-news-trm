"""Structured logging configuration."""

import logging
import sys
import json
from datetime import datetime
from pathlib import Path
from typing import Any, Dict

from src.config.settings import settings


class JSONFormatter(logging.Formatter):
    """JSON formatter for structured logging."""

    def format(self, record: logging.LogRecord) -> str:
        """Format log record as JSON.

        Args:
            record: Log record

        Returns:
            JSON-formatted log string
        """
        log_data: Dict[str, Any] = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }

        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)

        # Add extra fields if present
        if hasattr(record, "extra_fields"):
            log_data.update(record.extra_fields)

        return json.dumps(log_data)


class TextFormatter(logging.Formatter):
    """Text formatter for human-readable logs."""

    def __init__(self):
        """Initialize text formatter."""
        super().__init__(
            fmt="%(asctime)s | %(levelname)-8s | %(name)s | %(message)s",
            datefmt="%Y-%m-%d %H:%M:%S"
        )


def setup_logging(
    log_level: str = None,
    log_format: str = None,
    log_file: Path = None
) -> None:
    """Setup logging configuration.

    Args:
        log_level: Log level (default: from settings)
        log_format: Log format - "json" or "text" (default: from settings)
        log_file: Optional file path for logging
    """
    # Use settings if not provided
    log_level = log_level or settings.log_level
    log_format = log_format or settings.log_format

    # Convert log level string to logging constant
    numeric_level = getattr(logging, log_level.upper(), logging.INFO)

    # Choose formatter
    if log_format == "json":
        formatter = JSONFormatter()
    else:
        formatter = TextFormatter()

    # Setup root logger
    root_logger = logging.getLogger()
    root_logger.setLevel(numeric_level)

    # Remove existing handlers
    root_logger.handlers.clear()

    # Add console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(numeric_level)
    console_handler.setFormatter(formatter)
    root_logger.addHandler(console_handler)

    # Add file handler if log_file specified
    if log_file:
        log_file = Path(log_file)
        log_file.parent.mkdir(parents=True, exist_ok=True)

        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(numeric_level)
        file_handler.setFormatter(formatter)
        root_logger.addHandler(file_handler)

    # Reduce noise from verbose libraries
    logging.getLogger("anthropic").setLevel(logging.WARNING)
    logging.getLogger("httpx").setLevel(logging.WARNING)
    logging.getLogger("httpcore").setLevel(logging.WARNING)
    logging.getLogger("urllib3").setLevel(logging.WARNING)

    root_logger.info(f"Logging configured: level={log_level}, format={log_format}")


def log_with_context(logger: logging.Logger, level: str, message: str, **context):
    """Log message with additional context fields.

    Args:
        logger: Logger instance
        level: Log level ("debug", "info", "warning", "error", "critical")
        message: Log message
        **context: Additional context fields
    """
    log_func = getattr(logger, level.lower())

    # Create a log record with extra fields
    extra = {"extra_fields": context}
    log_func(message, extra=extra)


# Setup logging on module import
setup_logging()
