"""High-level convenience functions for common Solana Pay operations."""

from __future__ import annotations

import asyncio
import decimal
from decimal import Decimal
from typing import Optional, List, Dict, Any

from .models import TransferRequest, TransactionOptions
from .urls import encode_url, parse_url
from .tx_builders import build_transfer_transaction
from .validation import wait_and_verify
from .utils.rpc import create_rpc_client
from .config import get_default_rpc_endpoint
from .utils import get_logger
from .utils.errors import URLError, ValidationError

logger = get_logger(__name__)


def create_payment_url(
    recipient: str,
    amount: Optional[str] = None,
    token: Optional[str] = None,
    label: Optional[str] = None,
    message: Optional[str] = None,
    memo: Optional[str] = None,
    references: Optional[List[str]] = None
) -> str:
    """Create a Solana Pay URL with simple parameters.
    
    This is a high-level convenience function for creating payment URLs
    without needing to work with the TransferRequest model directly.
    
    Args:
        recipient: Base58 encoded recipient public key
        amount: Payment amount as string (e.g., "0.01")
        token: SPL token mint address (None for SOL)
        label: Human-readable label
        message: Payment description
        memo: On-chain memo
        references: List of reference public keys
        
    Returns:
        Encoded solana: URL
        
    Example:
        >>> url = create_payment_url(
        ...     recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        ...     amount="0.01",
        ...     label="Coffee Shop"
        ... )
        >>> print(url)
    """
    decimal_amount = None
    if amount is not None:
        try:
            decimal_amount = Decimal(amount)
        except (ValueError, TypeError, decimal.InvalidOperation) as e:
            raise URLError(f"Invalid amount format: {amount}") from e
    
    try:
        request = TransferRequest(
            recipient=recipient,
            amount=decimal_amount,
            spl_token=token,
            label=label,
            message=message,
            memo=memo,
            references=references
        )
        
        return encode_url(request)
    except ValidationError as e:
        raise URLError(f"Invalid payment parameters: {e.message}") from e


def parse_payment_url(url: str) -> Dict[str, Any]:
    """Parse a Solana Pay URL into a simple dictionary.
    
    This is a high-level convenience function for parsing payment URLs
    without needing to work with the TransferRequest model directly.
    
    Args:
        url: Solana Pay URL to parse
        
    Returns:
        Dictionary containing payment parameters
        
    Example:
        >>> info = parse_payment_url("solana:9Wz...?amount=0.01&label=Coffee")
        >>> print(info["amount"])  # "0.01"
        >>> print(info["label"])   # "Coffee"
    """
    request = parse_url(url)
    
    result = {
        "recipient": request.recipient,
        "amount": str(request.amount) if request.amount else None,
        "token": request.spl_token,
        "label": request.label,
        "message": request.message,
        "memo": request.memo,
        "references": request.references
    }
    
    return result


async def create_payment_transaction(
    payer: str,
    recipient: str,
    amount: str,
    token: Optional[str] = None,
    memo: Optional[str] = None,
    references: Optional[List[str]] = None,
    rpc_endpoint: Optional[str] = None,
    auto_create_ata: bool = True
) -> str:
    """Create a payment transaction with simple parameters.
    
    This is a high-level convenience function for creating payment transactions
    without needing to work with the lower-level APIs directly.
    
    Args:
        payer: Base58 encoded payer public key
        recipient: Base58 encoded recipient public key
        amount: Payment amount as string
        token: SPL token mint address (None for SOL)
        memo: On-chain memo
        references: List of reference public keys
        rpc_endpoint: Custom RPC endpoint (uses default if None)
        auto_create_ata: Whether to auto-create recipient ATA
        
    Returns:
        Base64 encoded transaction
        
    Example:
        >>> tx = await create_payment_transaction(
        ...     payer="payer_pubkey_here",
        ...     recipient="recipient_pubkey_here", 
        ...     amount="0.01"
        ... )
        >>> print(tx)  # Base64 encoded transaction
    """
    endpoint = rpc_endpoint or get_default_rpc_endpoint()
    
    # Create transfer request
    request = TransferRequest(
        recipient=recipient,
        amount=Decimal(amount),
        spl_token=token,
        memo=memo,
        references=references
    )
    
    # Create transaction options
    options = TransactionOptions(auto_create_ata=auto_create_ata)
    
    # Build transaction
    async with create_rpc_client(endpoint) as rpc:
        result = await build_transfer_transaction(rpc, payer, request, options)
        return result.transaction


async def verify_payment(
    signature: str,
    expected_recipient: str,
    expected_amount: str,
    expected_token: Optional[str] = None,
    expected_memo: Optional[str] = None,
    timeout: int = 60,
    rpc_endpoint: Optional[str] = None
) -> Dict[str, Any]:
    """Verify a payment transaction with simple parameters.
    
    This is a high-level convenience function for verifying payments
    without needing to work with the lower-level validation APIs directly.
    
    Args:
        signature: Transaction signature to verify
        expected_recipient: Expected recipient public key
        expected_amount: Expected amount as string
        expected_token: Expected SPL token mint (None for SOL)
        expected_memo: Expected memo text
        timeout: Maximum wait time in seconds
        rpc_endpoint: Custom RPC endpoint (uses default if None)
        
    Returns:
        Dictionary containing verification results
        
    Example:
        >>> result = await verify_payment(
        ...     signature="transaction_signature_here",
        ...     expected_recipient="recipient_pubkey_here",
        ...     expected_amount="0.01"
        ... )
        >>> print(result["is_valid"])  # True or False
    """
    endpoint = rpc_endpoint or get_default_rpc_endpoint()
    
    # Create expected transfer request
    expected = TransferRequest(
        recipient=expected_recipient,
        amount=Decimal(expected_amount),
        spl_token=expected_token,
        memo=expected_memo
    )
    
    # Verify transaction
    async with create_rpc_client(endpoint) as rpc:
        validation_result = await wait_and_verify(
            rpc, signature, expected, timeout
        )
        
        return {
            "is_valid": validation_result.is_valid,
            "recipient_match": validation_result.recipient_match,
            "amount_match": validation_result.amount_match,
            "memo_match": validation_result.memo_match,
            "references_match": validation_result.references_match,
            "confirmation_status": validation_result.confirmation_status,
            "errors": validation_result.errors,
            "warnings": validation_result.warnings,
            "signature": validation_result.signature
        }


class SolanaPayClient:
    """High-level client for Solana Pay operations.
    
    This class provides a simple interface for common Solana Pay operations
    without requiring deep knowledge of the underlying APIs.
    
    Example:
        >>> client = SolanaPayClient()
        >>> url = client.create_payment_url(
        ...     recipient="9Wz...",
        ...     amount="0.01",
        ...     label="Coffee"
        ... )
        >>> 
        >>> # Later, verify the payment
        >>> result = await client.verify_payment(
        ...     signature="tx_sig...",
        ...     expected_recipient="9Wz...",
        ...     expected_amount="0.01"
        ... )
    """
    
    def __init__(self, rpc_endpoint: Optional[str] = None):
        """Initialize Solana Pay client.
        
        Args:
            rpc_endpoint: Custom RPC endpoint (uses default if None)
        """
        self.rpc_endpoint = rpc_endpoint or get_default_rpc_endpoint()
        logger.info(f"Initialized SolanaPayClient with endpoint: {self.rpc_endpoint}")
    
    def create_payment_url(
        self,
        recipient: str,
        amount: Optional[str] = None,
        **kwargs
    ) -> str:
        """Create a payment URL. See create_payment_url() for details."""
        return create_payment_url(recipient, amount, **kwargs)
    
    def parse_payment_url(self, url: str) -> Dict[str, Any]:
        """Parse a payment URL. See parse_payment_url() for details."""
        return parse_payment_url(url)
    
    async def create_transaction(
        self,
        payer: str,
        recipient: str,
        amount: str,
        **kwargs
    ) -> str:
        """Create a payment transaction. See create_payment_transaction() for details."""
        return await create_payment_transaction(
            payer, recipient, amount, rpc_endpoint=self.rpc_endpoint, **kwargs
        )
    
    async def verify_payment(
        self,
        signature: str,
        expected_recipient: str,
        expected_amount: str,
        **kwargs
    ) -> Dict[str, Any]:
        """Verify a payment. See verify_payment() for details."""
        return await verify_payment(
            signature, expected_recipient, expected_amount, 
            rpc_endpoint=self.rpc_endpoint, **kwargs
        )
    
    async def get_transaction_status(self, signature: str) -> Dict[str, Any]:
        """Get the status of a transaction.
        
        Args:
            signature: Transaction signature to check
            
        Returns:
            Dictionary containing transaction status
        """
        async with create_rpc_client(self.rpc_endpoint) as rpc:
            try:
                from solders.signature import Signature
                sig_obj = Signature.from_string(signature)
                
                # Get transaction status
                status_response = await rpc.get_signature_statuses([sig_obj])
                
                if status_response.value and status_response.value[0]:
                    status = status_response.value[0]
                    return {
                        "exists": True,
                        "confirmed": status.confirmation_status is not None,
                        "confirmation_status": str(status.confirmation_status) if status.confirmation_status else None,
                        "slot": status.slot,
                        "error": str(status.err) if status.err else None
                    }
                else:
                    return {
                        "exists": False,
                        "confirmed": False,
                        "confirmation_status": None,
                        "slot": None,
                        "error": None
                    }
                    
            except Exception as e:
                logger.error(f"Error getting transaction status: {e}")
                return {
                    "exists": False,
                    "confirmed": False,
                    "confirmation_status": None,
                    "slot": None,
                    "error": str(e)
                }


# Synchronous wrappers for async functions (for convenience)

def create_payment_transaction_sync(*args, **kwargs) -> str:
    """Synchronous wrapper for create_payment_transaction()."""
    return asyncio.run(create_payment_transaction(*args, **kwargs))


def verify_payment_sync(*args, **kwargs) -> Dict[str, Any]:
    """Synchronous wrapper for verify_payment()."""
    return asyncio.run(verify_payment(*args, **kwargs))