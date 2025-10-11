"""Custom exception classes for Solana Pay operations."""

from __future__ import annotations

from typing import Any, Dict, Optional


class SolanaPayError(Exception):
    """Base exception for all Solana Pay related errors.
    
    This is the base class for all exceptions raised by the Solana Pay library.
    It provides common functionality for error handling and context preservation.
    
    Attributes:
        message: Human-readable error message
        error_code: Optional error code for programmatic handling
        context: Additional context information about the error
    """
    
    def __init__(
        self, 
        message: str, 
        error_code: Optional[str] = None,
        context: Optional[Dict[str, Any]] = None
    ) -> None:
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.context = context or {}

    def __str__(self) -> str:
        """String representation of the error."""
        if self.error_code:
            return f"[{self.error_code}] {self.message}"
        return self.message

    def add_context(self, key: str, value: Any) -> None:
        """Add additional context to the error.
        
        Args:
            key: Context key
            value: Context value
        """
        self.context[key] = value


class ValidationError(SolanaPayError):
    """Raised when input validation fails.
    
    This exception is raised when user input or data fails validation checks,
    such as invalid public keys, malformed URLs, or out-of-range values.
    """
    
    def __init__(
        self, 
        message: str, 
        field: Optional[str] = None,
        value: Optional[Any] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="VALIDATION_ERROR", **kwargs)
        if field:
            self.add_context("field", field)
        if value is not None:
            self.add_context("value", value)


class URLError(SolanaPayError):
    """Raised when URL encoding or parsing fails.
    
    This exception is raised for errors related to Solana Pay URL handling,
    including malformed URLs, unsupported schemes, or encoding issues.
    """
    
    def __init__(
        self, 
        message: str, 
        url: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="URL_ERROR", **kwargs)
        if url:
            self.add_context("url", url)


class TransactionBuildError(SolanaPayError):
    """Raised when transaction building fails.
    
    This exception is raised when there are errors during transaction construction,
    such as insufficient account data, invalid parameters, or RPC failures.
    """
    
    def __init__(
        self, 
        message: str, 
        transaction_type: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="TRANSACTION_BUILD_ERROR", **kwargs)
        if transaction_type:
            self.add_context("transaction_type", transaction_type)


class TransactionValidationError(SolanaPayError):
    """Raised when transaction validation fails.
    
    This exception is raised when a completed transaction doesn't match
    the expected parameters or fails validation checks.
    """
    
    def __init__(
        self, 
        message: str, 
        signature: Optional[str] = None,
        validation_failures: Optional[list] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="TRANSACTION_VALIDATION_ERROR", **kwargs)
        if signature:
            self.add_context("signature", signature)
        if validation_failures:
            self.add_context("validation_failures", validation_failures)


class RPCError(SolanaPayError):
    """Raised when RPC communication fails.
    
    This exception is raised for errors related to Solana RPC communication,
    including network errors, RPC method failures, and timeout issues.
    """
    
    def __init__(
        self, 
        message: str, 
        rpc_method: Optional[str] = None,
        rpc_endpoint: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="RPC_ERROR", **kwargs)
        if rpc_method:
            self.add_context("rpc_method", rpc_method)
        if rpc_endpoint:
            self.add_context("rpc_endpoint", rpc_endpoint)
        if status_code:
            self.add_context("status_code", status_code)


class NetworkError(RPCError):
    """Raised when network communication fails.
    
    This is a specialized RPC error for network-level failures such as
    connection timeouts, DNS resolution failures, or connection refused errors.
    """
    
    def __init__(self, message: str, **kwargs) -> None:
        super().__init__(message, error_code="NETWORK_ERROR", **kwargs)


class BlockchainError(SolanaPayError):
    """Raised when blockchain operations fail.
    
    This exception is raised for errors that occur on the blockchain level,
    such as insufficient funds, account not found, or transaction failures.
    """
    
    def __init__(
        self, 
        message: str, 
        instruction_error: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="BLOCKCHAIN_ERROR", **kwargs)
        if instruction_error:
            self.add_context("instruction_error", instruction_error)


class ConfigurationError(SolanaPayError):
    """Raised when configuration is invalid or missing.
    
    This exception is raised for errors related to library configuration,
    such as missing required settings, invalid cluster configurations,
    or incompatible option combinations.
    """
    
    def __init__(
        self, 
        message: str, 
        config_key: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="CONFIGURATION_ERROR", **kwargs)
        if config_key:
            self.add_context("config_key", config_key)


class TimeoutError(SolanaPayError):
    """Raised when operations timeout.
    
    This exception is raised when operations take longer than the specified
    timeout period, such as waiting for transaction confirmation or RPC responses.
    """
    
    def __init__(
        self, 
        message: str, 
        timeout_seconds: Optional[int] = None,
        operation: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="TIMEOUT_ERROR", **kwargs)
        if timeout_seconds:
            self.add_context("timeout_seconds", timeout_seconds)
        if operation:
            self.add_context("operation", operation)


class InsufficientFundsError(BlockchainError):
    """Raised when account has insufficient funds for transaction.
    
    This is a specialized blockchain error for insufficient fund scenarios,
    providing additional context about required vs available amounts.
    """
    
    def __init__(
        self, 
        message: str, 
        required_amount: Optional[int] = None,
        available_amount: Optional[int] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="INSUFFICIENT_FUNDS_ERROR", **kwargs)
        if required_amount is not None:
            self.add_context("required_amount", required_amount)
        if available_amount is not None:
            self.add_context("available_amount", available_amount)


class AccountNotFoundError(BlockchainError):
    """Raised when a required account is not found on the blockchain.
    
    This is a specialized blockchain error for missing account scenarios,
    such as when an Associated Token Account doesn't exist.
    """
    
    def __init__(
        self, 
        message: str, 
        account_address: Optional[str] = None,
        account_type: Optional[str] = None,
        **kwargs
    ) -> None:
        super().__init__(message, error_code="ACCOUNT_NOT_FOUND_ERROR", **kwargs)
        if account_address:
            self.add_context("account_address", account_address)
        if account_type:
            self.add_context("account_type", account_type)


def wrap_rpc_error(original_error: Exception, rpc_method: str, rpc_endpoint: str) -> RPCError:
    """Wrap a generic exception as an RPCError with additional context.
    
    Args:
        original_error: The original exception that occurred
        rpc_method: The RPC method that was being called
        rpc_endpoint: The RPC endpoint that was being used
        
    Returns:
        RPCError with the original error as the cause
    """
    message = f"RPC call failed: {str(original_error)}"
    rpc_error = RPCError(
        message=message,
        rpc_method=rpc_method,
        rpc_endpoint=rpc_endpoint
    )
    rpc_error.__cause__ = original_error
    return rpc_error


def wrap_validation_error(original_error: Exception, field: str, value: Any) -> ValidationError:
    """Wrap a generic exception as a ValidationError with additional context.
    
    Args:
        original_error: The original exception that occurred
        field: The field that failed validation
        value: The value that failed validation
        
    Returns:
        ValidationError with the original error as the cause
    """
    message = f"Validation failed for {field}: {str(original_error)}"
    validation_error = ValidationError(
        message=message,
        field=field,
        value=value
    )
    validation_error.__cause__ = original_error
    return validation_error


# Enhanced error handling utilities
import traceback
import sys
from typing import Type, Union, Callable, Any
from functools import wraps


class ErrorContext:
    """Context manager for enhanced error handling with automatic context preservation."""
    
    def __init__(self, operation: str, **context):
        """Initialize error context.
        
        Args:
            operation: Name of the operation being performed
            **context: Additional context to preserve
        """
        self.operation = operation
        self.context = context
        self.original_exception: Optional[Exception] = None
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if exc_type is not None:
            self.original_exception = exc_val
            
            # If it's already a SolanaPayError, add context
            if isinstance(exc_val, SolanaPayError):
                exc_val.add_context("operation", self.operation)
                for key, value in self.context.items():
                    exc_val.add_context(key, value)
                return False  # Re-raise the enhanced error
            
            # Wrap other exceptions
            if issubclass(exc_type, ValueError):
                # Add operation to context
                full_context = {"operation": self.operation, **self.context}
                new_error = ValidationError(
                    f"Validation failed during {self.operation}: {str(exc_val)}",
                    context=full_context
                )
            elif issubclass(exc_type, (ConnectionError, TimeoutError)):
                # Add operation to context
                full_context = {"operation": self.operation, **self.context}
                new_error = NetworkError(
                    f"Network error during {self.operation}: {str(exc_val)}",
                    context=full_context
                )
            else:
                # Add operation to context
                full_context = {"operation": self.operation, **self.context}
                new_error = SolanaPayError(
                    f"Error during {self.operation}: {str(exc_val)}",
                    error_code="OPERATION_ERROR",
                    context=full_context
                )
            
            new_error.__cause__ = exc_val
            raise new_error from exc_val
        
        return False


def error_handler(
    operation: str,
    error_mapping: Optional[Dict[Type[Exception], Type[SolanaPayError]]] = None,
    **context
):
    """Decorator for automatic error handling and context preservation.
    
    Args:
        operation: Name of the operation
        error_mapping: Mapping of exception types to SolanaPayError types
        **context: Additional context to preserve
    """
    if error_mapping is None:
        error_mapping = {}
    
    def decorator(func: Callable) -> Callable:
        @wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except SolanaPayError:
                # Re-raise SolanaPayError as-is
                raise
            except Exception as e:
                # Map to appropriate SolanaPayError
                error_type = type(e)
                solana_pay_error_type = error_mapping.get(error_type, SolanaPayError)
                
                new_error = solana_pay_error_type(
                    f"Error in {operation}: {str(e)}",
                    context=context
                )
                new_error.__cause__ = e
                raise new_error from e
        
        @wraps(func)
        async def async_wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except SolanaPayError:
                # Re-raise SolanaPayError as-is
                raise
            except Exception as e:
                # Map to appropriate SolanaPayError
                error_type = type(e)
                solana_pay_error_type = error_mapping.get(error_type, SolanaPayError)
                
                new_error = solana_pay_error_type(
                    f"Error in {operation}: {str(e)}",
                    context=context
                )
                new_error.__cause__ = e
                raise new_error from e
        
        # Return appropriate wrapper based on function type
        import asyncio
        if asyncio.iscoroutinefunction(func):
            return async_wrapper
        else:
            return wrapper
    
    return decorator


def get_error_details(error: Exception) -> Dict[str, Any]:
    """Extract detailed information from an exception.
    
    Args:
        error: Exception to analyze
        
    Returns:
        Dictionary containing error details
    """
    details = {
        "type": type(error).__name__,
        "message": str(error),
        "module": getattr(error, "__module__", None),
    }
    
    # Add SolanaPayError specific details
    if isinstance(error, SolanaPayError):
        details.update({
            "error_code": error.error_code,
            "context": error.context,
        })
    
    # Add traceback information
    if hasattr(error, "__traceback__") and error.__traceback__:
        details["traceback"] = traceback.format_exception(
            type(error), error, error.__traceback__
        )
    
    # Add cause chain
    if error.__cause__:
        details["cause"] = get_error_details(error.__cause__)
    
    return details


def format_error_for_logging(error: Exception) -> str:
    """Format an exception for logging with full context.
    
    Args:
        error: Exception to format
        
    Returns:
        Formatted error string
    """
    lines = [f"Error: {type(error).__name__}: {str(error)}"]
    
    if isinstance(error, SolanaPayError):
        if error.error_code:
            lines.append(f"Code: {error.error_code}")
        
        if error.context:
            lines.append("Context:")
            for key, value in error.context.items():
                lines.append(f"  {key}: {value}")
    
    # Add cause chain
    current_error = error
    level = 0
    while current_error.__cause__:
        level += 1
        current_error = current_error.__cause__
        indent = "  " * level
        lines.append(f"{indent}Caused by: {type(current_error).__name__}: {str(current_error)}")
    
    return "\n".join(lines)


def create_error_report(
    error: Exception, 
    operation: Optional[str] = None,
    inputs: Optional[Dict[str, Any]] = None,
    context: Optional[Dict[str, Any]] = None,
    include_system_info: bool = True
) -> Dict[str, Any]:
    """Create a comprehensive error report.
    
    Args:
        error: Exception to report
        operation: Name of the operation that failed
        inputs: Input parameters that caused the error
        context: Additional context information
        include_system_info: Whether to include system information
        
    Returns:
        Comprehensive error report
    """
    report = {
        "timestamp": __import__("time").time(),
        "success": False,
        "error": get_error_details(error),
    }
    
    # Add optional fields if provided
    if operation is not None:
        report["operation"] = operation
    if inputs is not None:
        report["inputs"] = inputs
    if context is not None:
        report["context"] = context
    
    if include_system_info:
        report["system"] = {
            "python_version": sys.version,
            "platform": sys.platform,
        }
        
        # Add library version if available
        try:
            from .. import __version__
            report["library_version"] = __version__
        except ImportError:
            pass
    
    return report


class ErrorCollector:
    """Utility for collecting and managing multiple errors."""
    
    def __init__(self):
        self.errors: List[Exception] = []
        self.warnings: List[str] = []
    
    def add_error(self, error: Union[Exception, str]):
        """Add an error to the collection."""
        if isinstance(error, str):
            error = SolanaPayError(error)
        self.errors.append(error)
    
    def add_warning(self, warning: str):
        """Add a warning to the collection."""
        self.warnings.append(warning)
    
    def has_errors(self) -> bool:
        """Check if there are any errors."""
        return len(self.errors) > 0
    
    def has_warnings(self) -> bool:
        """Check if there are any warnings."""
        return len(self.warnings) > 0
    
    def get_summary(self) -> str:
        """Get a summary of all errors and warnings."""
        lines = []
        
        if self.errors:
            lines.append(f"Errors ({len(self.errors)}):")
            for i, error in enumerate(self.errors, 1):
                lines.append(f"  {i}. {str(error)}")
        
        if self.warnings:
            lines.append(f"Warnings ({len(self.warnings)}):")
            for i, warning in enumerate(self.warnings, 1):
                lines.append(f"  {i}. {warning}")
        
        return "\n".join(lines) if lines else "No errors or warnings"
    
    def raise_if_errors(self, message: str = "Multiple errors occurred"):
        """Raise a combined error if there are any errors."""
        if self.errors:
            if len(self.errors) == 1:
                raise self.errors[0]
            
            # Create a combined error
            error_messages = [str(e) for e in self.errors]
            combined_error = SolanaPayError(
                f"{message}: {'; '.join(error_messages)}",
                error_code="MULTIPLE_ERRORS",
                context={
                    "error_count": len(self.errors),
                    "warning_count": len(self.warnings),
                    "errors": error_messages,
                    "warnings": self.warnings
                }
            )
            raise combined_error


# Utility functions for common error scenarios

def handle_rpc_timeout(func: Callable) -> Callable:
    """Decorator to handle RPC timeout errors specifically."""
    return error_handler(
        operation=func.__name__,
        error_mapping={
            TimeoutError: SolanaPayTimeoutError,
            asyncio.TimeoutError: SolanaPayTimeoutError,
        }
    )(func)


def handle_validation_errors(func: Callable) -> Callable:
    """Decorator to handle validation errors specifically."""
    return error_handler(
        operation=func.__name__,
        error_mapping={
            ValueError: ValidationError,
            TypeError: ValidationError,
        }
    )(func)


def handle_network_errors(func: Callable) -> Callable:
    """Decorator to handle network errors specifically."""
    return error_handler(
        operation=func.__name__,
        error_mapping={
            ConnectionError: NetworkError,
            TimeoutError: NetworkError,
        }
    )(func)