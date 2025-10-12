"""Solana Pay Python Library

A comprehensive Python implementation of the Solana Pay protocol for seamless
cryptocurrency payments in Python applications.

This library provides:
- URL encoding and parsing for Solana Pay URLs
- Transaction building for SOL and SPL token transfers  
- Transaction request server for merchant integration
- Transaction validation and confirmation
- Comprehensive error handling and logging

Example:
    >>> from solanapay import TransferRequest, encode_url
    >>> from decimal import Decimal
    >>> 
    >>> request = TransferRequest(
    ...     recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    ...     amount=Decimal("0.01"),
    ...     label="Coffee Shop"
    ... )
    >>> url = encode_url(request)
    >>> print(url)
"""

from .version import __version__

# Core data models
from .models import (
    TransferRequest,
    TransactionBuildResult,
    TransactionOptions,
    TransactionMetadata,
    ValidationResult,
    ValidationConfig,
)

# URL handling
from .urls import (
    encode_url,
    parse_url,
    encode_https_url,
    validate_url,
    create_transfer_url,
    parse_transfer_url,
)

# Transaction building
from .tx_builders import (
    build_transfer_transaction,
    build_transfer_tx,  # Legacy function
    create_memo_instruction,
    create_payment_memo,
)

# Transaction validation
from .validation import (
    TransactionValidator,
    wait_and_verify,
)

# Server components
from .server import (
    TransactionRequestServer,
    create_app,
    MerchantConfig,
)

# Configuration
from .config import (
    get_settings,
    configure_logging,
    get_default_rpc_endpoint,
    ClusterConfig,
    get_cluster_config,
)

# Utilities
from .utils import (
    setup_logging,
    get_logger,
    SolanaPayError,
    ValidationError,
    URLError,
    TransactionBuildError,
    RPCError,
)

# High-level convenience functions
from .convenience import (
    create_payment_url,
    parse_payment_url,
    create_payment_transaction,
    verify_payment,
    SolanaPayClient,
)

# Compatibility utilities
from .compat import (
    check_compatibility,
    get_compatibility_report,
    get_system_info,
)

# Version information
__all__ = [
    # Version
    "__version__",
    
    # Core models
    "TransferRequest",
    "TransactionBuildResult", 
    "TransactionOptions",
    "TransactionMetadata",
    "ValidationResult",
    "ValidationConfig",
    
    # URL handling
    "encode_url",
    "parse_url",
    "encode_https_url", 
    "validate_url",
    "create_transfer_url",
    "parse_transfer_url",
    
    # Transaction building
    "build_transfer_transaction",
    "build_transfer_tx",
    "create_memo_instruction",
    "create_payment_memo",
    
    # Transaction validation
    "TransactionValidator",
    "wait_and_verify",
    
    # Server components
    "TransactionRequestServer",
    "create_app",
    "MerchantConfig",
    
    # Configuration
    "get_settings",
    "configure_logging", 
    "get_default_rpc_endpoint",
    "ClusterConfig",
    "get_cluster_config",
    
    # Utilities
    "setup_logging",
    "get_logger",
    "SolanaPayError",
    "ValidationError",
    "URLError", 
    "TransactionBuildError",
    "RPCError",
    
    # High-level convenience functions
    "create_payment_url",
    "parse_payment_url", 
    "create_payment_transaction",
    "verify_payment",
    "SolanaPayClient",
    
    # Compatibility utilities
    "check_compatibility",
    "get_compatibility_report",
    "get_system_info",
]
