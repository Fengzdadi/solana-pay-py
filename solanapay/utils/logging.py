"""Comprehensive logging utilities for Solana Pay operations."""

from __future__ import annotations

import logging
import logging.handlers
import json
import time
import sys
from typing import Dict, Any, Optional, Union
from pathlib import Path
from contextlib import contextmanager

from .errors import SolanaPayError, format_error_for_logging


class SolanaPayFormatter(logging.Formatter):
    """Custom formatter for Solana Pay log messages."""
    
    def __init__(self, include_context: bool = True, json_format: bool = False):
        """Initialize formatter.
        
        Args:
            include_context: Whether to include additional context
            json_format: Whether to format as JSON
        """
        self.include_context = include_context
        self.json_format = json_format
        
        if json_format:
            super().__init__()
        else:
            super().__init__(
                fmt='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record."""
        if self.json_format:
            return self._format_json(record)
        else:
            return self._format_text(record)
    
    def _format_json(self, record: logging.LogRecord) -> str:
        """Format record as JSON."""
        log_data = {
            "timestamp": time.time(),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }
        
        # Add exception information
        if record.exc_info:
            log_data["exception"] = {
                "type": record.exc_info[0].__name__,
                "message": str(record.exc_info[1]),
                "traceback": self.formatException(record.exc_info)
            }
        
        # Add custom context if available
        if self.include_context and hasattr(record, 'context'):
            log_data["context"] = record.context
        
        return json.dumps(log_data, default=str)
    
    def _format_text(self, record: logging.LogRecord) -> str:
        """Format record as text."""
        formatted = super().format(record)
        
        # Add context if available
        if self.include_context and hasattr(record, 'context'):
            context_str = ", ".join(f"{k}={v}" for k, v in record.context.items())
            formatted += f" | Context: {context_str}"
        
        return formatted


class ContextLogger:
    """Logger with automatic context preservation."""
    
    def __init__(self, logger: logging.Logger, context: Optional[Dict[str, Any]] = None):
        """Initialize context logger.
        
        Args:
            logger: Base logger instance
            context: Default context to include in all messages
        """
        self.logger = logger
        self.context = context or {}
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Log message with context."""
        # Merge contexts
        full_context = {**self.context, **kwargs}
        
        # Create log record with context
        record = self.logger.makeRecord(
            self.logger.name, level, "", 0, message, (), None
        )
        record.context = full_context
        
        self.logger.handle(record)
    
    def debug(self, message: str, **context):
        """Log debug message with context."""
        self._log_with_context(logging.DEBUG, message, **context)
    
    def info(self, message: str, **context):
        """Log info message with context."""
        self._log_with_context(logging.INFO, message, **context)
    
    def warning(self, message: str, **context):
        """Log warning message with context."""
        self._log_with_context(logging.WARNING, message, **context)
    
    def error(self, message: str, **context):
        """Log error message with context."""
        self._log_with_context(logging.ERROR, message, **context)
    
    def critical(self, message: str, **context):
        """Log critical message with context."""
        self._log_with_context(logging.CRITICAL, message, **context)
    
    def exception(self, message: str, **context):
        """Log exception with context."""
        self._log_with_context(logging.ERROR, message, **context)
        
        # Add exception info if available
        exc_info = sys.exc_info()
        if exc_info[0] is not None:
            if isinstance(exc_info[1], SolanaPayError):
                formatted_error = format_error_for_logging(exc_info[1])
                self._log_with_context(logging.ERROR, f"Exception details: {formatted_error}", **context)
    
    def with_context(self, **additional_context) -> 'ContextLogger':
        """Create a new logger with additional context."""
        merged_context = {**self.context, **additional_context}
        return ContextLogger(self.logger, merged_context)


class OperationLogger:
    """Logger for tracking operations with timing and success/failure."""
    
    def __init__(self, logger: ContextLogger, operation: str, **context):
        """Initialize operation logger.
        
        Args:
            logger: Context logger instance
            operation: Name of the operation
            **context: Additional context
        """
        self.logger = logger.with_context(operation=operation, **context)
        self.operation = operation
        self.start_time = None
        self.success = False
    
    def start(self, message: Optional[str] = None):
        """Start the operation."""
        self.start_time = time.time()
        msg = message or f"Starting {self.operation}"
        self.logger.info(msg, start_time=self.start_time)
    
    def success(self, message: Optional[str] = None, **context):
        """Mark operation as successful."""
        self.success = True
        duration = time.time() - (self.start_time or time.time())
        msg = message or f"Completed {self.operation}"
        self.logger.info(msg, duration=duration, success=True, **context)
    
    def failure(self, error: Optional[Exception] = None, message: Optional[str] = None, **context):
        """Mark operation as failed."""
        self.success = False
        duration = time.time() - (self.start_time or time.time())
        msg = message or f"Failed {self.operation}"
        
        if error:
            self.logger.error(f"{msg}: {str(error)}", duration=duration, success=False, **context)
            if isinstance(error, SolanaPayError):
                self.logger.error(format_error_for_logging(error))
        else:
            self.logger.error(msg, duration=duration, success=False, **context)
    
    def __enter__(self):
        """Context manager entry."""
        self.start()
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        """Context manager exit."""
        if exc_type is None:
            self.success()
        else:
            self.failure(exc_val)
        return False


@contextmanager
def log_operation(logger: Union[logging.Logger, ContextLogger], operation: str, **context):
    """Context manager for logging operations.
    
    Args:
        logger: Logger instance
        operation: Operation name
        **context: Additional context
        
    Example:
        >>> with log_operation(logger, "build_transaction", recipient="abc123"):
        ...     # Operation code here
        ...     pass
    """
    if isinstance(logger, logging.Logger):
        context_logger = ContextLogger(logger)
    else:
        context_logger = logger
    
    op_logger = OperationLogger(context_logger, operation, **context)
    
    try:
        op_logger.start()
        yield op_logger
        op_logger.success()
    except Exception as e:
        op_logger.failure(e)
        raise


def setup_logging(
    level: str = "INFO",
    format_type: str = "text",  # "text" or "json"
    log_file: Optional[str] = None,
    max_file_size: int = 10 * 1024 * 1024,  # 10MB
    backup_count: int = 5,
    include_context: bool = True
) -> ContextLogger:
    """Set up comprehensive logging for Solana Pay.
    
    Args:
        level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        format_type: Format type ("text" or "json")
        log_file: Optional log file path
        max_file_size: Maximum log file size in bytes
        backup_count: Number of backup files to keep
        include_context: Whether to include context in logs
        
    Returns:
        Configured ContextLogger instance
    """
    # Get root logger for solanapay
    logger = logging.getLogger("solanapay")
    logger.setLevel(getattr(logging, level.upper()))
    
    # Clear existing handlers
    logger.handlers.clear()
    
    # Create formatter
    formatter = SolanaPayFormatter(
        include_context=include_context,
        json_format=(format_type == "json")
    )
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        log_path = Path(log_file)
        log_path.parent.mkdir(parents=True, exist_ok=True)
        
        file_handler = logging.handlers.RotatingFileHandler(
            log_file,
            maxBytes=max_file_size,
            backupCount=backup_count
        )
        file_handler.setFormatter(formatter)
        logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    logger.propagate = False
    
    return ContextLogger(logger)


def get_logger(name: str, **context) -> ContextLogger:
    """Get a context logger for a specific module or component.
    
    Args:
        name: Logger name (usually __name__)
        **context: Default context for this logger
        
    Returns:
        ContextLogger instance
    """
    base_logger = logging.getLogger(name)
    return ContextLogger(base_logger, context)


class LoggingConfig:
    """Configuration for logging setup."""
    
    def __init__(
        self,
        level: str = "INFO",
        format_type: str = "text",
        log_file: Optional[str] = None,
        max_file_size: int = 10 * 1024 * 1024,
        backup_count: int = 5,
        include_context: bool = True,
        enable_debug_logging: bool = False
    ):
        self.level = level
        self.format_type = format_type
        self.log_file = log_file
        self.max_file_size = max_file_size
        self.backup_count = backup_count
        self.include_context = include_context
        self.enable_debug_logging = enable_debug_logging
    
    def setup(self) -> ContextLogger:
        """Set up logging with this configuration."""
        return setup_logging(
            level=self.level,
            format_type=self.format_type,
            log_file=self.log_file,
            max_file_size=self.max_file_size,
            backup_count=self.backup_count,
            include_context=self.include_context
        )
    
    @classmethod
    def from_env(cls) -> 'LoggingConfig':
        """Create logging configuration from environment variables."""
        import os
        
        return cls(
            level=os.getenv("SOLANA_PAY_LOG_LEVEL", "INFO"),
            format_type=os.getenv("SOLANA_PAY_LOG_FORMAT", "text"),
            log_file=os.getenv("SOLANA_PAY_LOG_FILE"),
            enable_debug_logging=os.getenv("SOLANA_PAY_DEBUG", "false").lower() == "true"
        )


# Performance logging utilities

class PerformanceLogger:
    """Logger for performance metrics and timing."""
    
    def __init__(self, logger: ContextLogger):
        self.logger = logger
        self.timers: Dict[str, float] = {}
    
    def start_timer(self, name: str):
        """Start a named timer."""
        self.timers[name] = time.time()
        self.logger.debug(f"Started timer: {name}")
    
    def end_timer(self, name: str, log_result: bool = True) -> float:
        """End a named timer and return duration."""
        if name not in self.timers:
            self.logger.warning(f"Timer '{name}' was not started")
            return 0.0
        
        duration = time.time() - self.timers[name]
        del self.timers[name]
        
        if log_result:
            self.logger.info(f"Timer '{name}' completed", duration=duration)
        
        return duration
    
    @contextmanager
    def time_operation(self, name: str):
        """Context manager for timing operations."""
        self.start_timer(name)
        try:
            yield
        finally:
            self.end_timer(name)
    
    def log_performance_metrics(self, metrics: Dict[str, Any]):
        """Log performance metrics."""
        self.logger.info("Performance metrics", **metrics)