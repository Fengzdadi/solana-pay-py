"""Utility modules for Solana Pay Python library."""

from .errors import (
    SolanaPayError,
    ValidationError,
    URLError,
    TransactionBuildError,
    RPCError,
    ErrorContext,
    error_handler,
    ErrorCollector
)
from .logging import (
    setup_logging,
    get_logger,
    ContextLogger,
    OperationLogger,
    log_operation,
    LoggingConfig
)
from .debug import (
    TransactionDebugger,
    PaymentDebugger,
    format_debug_output,
    create_debug_report,
    DebugSession
)

__all__ = [
    # Error handling
    "SolanaPayError",
    "ValidationError", 
    "URLError",
    "TransactionBuildError",
    "RPCError",
    "ErrorContext",
    "error_handler",
    "ErrorCollector",
    
    # Logging
    "setup_logging",
    "get_logger",
    "ContextLogger",
    "OperationLogger", 
    "log_operation",
    "LoggingConfig",
    
    # Debugging
    "TransactionDebugger",
    "PaymentDebugger",
    "format_debug_output",
    "create_debug_report",
    "DebugSession",
]