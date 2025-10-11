"""Memo instruction utilities for Solana Pay transactions."""

from __future__ import annotations

from solders.instruction import Instruction
from solders.pubkey import Pubkey

from ..utils.errors import TransactionBuildError

# Memo program ID
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

# Maximum memo length (practical limit for transaction size)
MAX_MEMO_LENGTH = 566  # Leaves room for other transaction data


def create_memo_instruction(memo_text: str) -> Instruction:
    """Create a memo instruction with the given text.
    
    Args:
        memo_text: Text to include in the memo instruction
        
    Returns:
        Memo instruction ready to be included in a transaction
        
    Raises:
        TransactionBuildError: If memo text is invalid
        
    Example:
        >>> memo_ix = create_memo_instruction("Payment for coffee")
        >>> # Add to transaction instructions
    """
    if not isinstance(memo_text, str):
        raise TransactionBuildError("Memo text must be a string")
    
    if not memo_text.strip():
        raise TransactionBuildError("Memo text cannot be empty")
    
    # Check length limit
    memo_bytes = memo_text.encode("utf-8")
    if len(memo_bytes) > MAX_MEMO_LENGTH:
        raise TransactionBuildError(
            f"Memo text too long: {len(memo_bytes)} bytes > {MAX_MEMO_LENGTH} bytes"
        )
    
    # Create instruction with memo data
    return Instruction(
        program_id=MEMO_PROGRAM_ID,
        data=memo_bytes,
        accounts=()  # Memo instructions don't require accounts
    )


def validate_memo_text(memo_text: str) -> bool:
    """Validate memo text without creating an instruction.
    
    Args:
        memo_text: Text to validate
        
    Returns:
        True if the memo text is valid
    """
    try:
        if not isinstance(memo_text, str) or not memo_text.strip():
            return False
        
        memo_bytes = memo_text.encode("utf-8")
        return len(memo_bytes) <= MAX_MEMO_LENGTH
        
    except Exception:
        return False


def get_memo_text_from_instruction(instruction: Instruction) -> str:
    """Extract memo text from a memo instruction.
    
    Args:
        instruction: Memo instruction to extract text from
        
    Returns:
        Decoded memo text
        
    Raises:
        TransactionBuildError: If instruction is not a valid memo instruction
    """
    if instruction.program_id != MEMO_PROGRAM_ID:
        raise TransactionBuildError("Instruction is not a memo instruction")
    
    try:
        return instruction.data.decode("utf-8")
    except UnicodeDecodeError as e:
        raise TransactionBuildError(f"Failed to decode memo text: {str(e)}") from e


def is_memo_instruction(instruction: Instruction) -> bool:
    """Check if an instruction is a memo instruction.
    
    Args:
        instruction: Instruction to check
        
    Returns:
        True if the instruction is a memo instruction
    """
    return instruction.program_id == MEMO_PROGRAM_ID


def create_payment_memo(
    merchant_name: str,
    order_id: Optional[str] = None,
    customer_id: Optional[str] = None
) -> str:
    """Create a standardized payment memo string.
    
    This creates a memo string following common patterns for payment tracking.
    
    Args:
        merchant_name: Name of the merchant
        order_id: Optional order identifier
        customer_id: Optional customer identifier
        
    Returns:
        Formatted memo string
        
    Example:
        >>> memo = create_payment_memo("Coffee Shop", "ORDER-123", "CUST-456")
        >>> memo
        'Coffee Shop | ORDER-123 | CUST-456'
    """
    parts = [merchant_name]
    
    if order_id:
        parts.append(order_id)
    
    if customer_id:
        parts.append(customer_id)
    
    memo = " | ".join(parts)
    
    # Validate the generated memo
    if not validate_memo_text(memo):
        raise TransactionBuildError(f"Generated memo is too long: {len(memo.encode('utf-8'))} bytes")
    
    return memo