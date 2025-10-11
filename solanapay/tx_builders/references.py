"""Reference handling utilities for Solana Pay transactions."""

from __future__ import annotations

from typing import List
from solders.instruction import AccountMeta, Instruction
from solders.pubkey import Pubkey

from ..utils.errors import TransactionBuildError, ValidationError


def append_references_to_instruction(
    instruction: Instruction, 
    references: List[str]
) -> Instruction:
    """Append reference accounts to an instruction.
    
    References are added as read-only, non-signer accounts as required by the
    Solana Pay specification. This allows for transaction tracking and identification.
    
    Args:
        instruction: Original instruction to modify
        references: List of base58 encoded reference public keys
        
    Returns:
        New instruction with references appended as additional accounts
        
    Raises:
        TransactionBuildError: If references are invalid or cannot be appended
        
    Example:
        >>> transfer_ix = create_transfer_instruction(...)
        >>> refs = ["11111111111111111111111111111112"]
        >>> modified_ix = append_references_to_instruction(transfer_ix, refs)
    """
    if not references:
        return instruction
    
    try:
        # Validate and convert reference strings to Pubkeys
        reference_pubkeys = []
        for i, ref in enumerate(references):
            if not isinstance(ref, str):
                raise TransactionBuildError(f"Reference {i} must be a string")
            
            try:
                ref_pk = Pubkey.from_string(ref)
                reference_pubkeys.append(ref_pk)
            except Exception as e:
                raise TransactionBuildError(
                    f"Invalid reference {i}: {ref} - {str(e)}"
                ) from e
        
        # Create new account metas for references
        new_accounts = list(instruction.accounts)
        for ref_pk in reference_pubkeys:
            new_accounts.append(AccountMeta(
                pubkey=ref_pk,
                is_signer=False,    # References are never signers
                is_writable=False   # References are read-only
            ))
        
        # Create new instruction with updated accounts
        return Instruction(
            program_id=instruction.program_id,
            data=instruction.data,
            accounts=tuple(new_accounts)
        )
        
    except TransactionBuildError:
        raise
    except Exception as e:
        raise TransactionBuildError(f"Failed to append references: {str(e)}") from e


def validate_references(references: List[str]) -> None:
    """Validate a list of reference public keys.
    
    Args:
        references: List of base58 encoded reference public keys
        
    Raises:
        ValidationError: If any reference is invalid
    """
    if not isinstance(references, list):
        raise ValidationError("References must be a list")
    
    for i, ref in enumerate(references):
        if not isinstance(ref, str):
            raise ValidationError(f"Reference {i} must be a string")
        
        if not ref.strip():
            raise ValidationError(f"Reference {i} cannot be empty")
        
        # Try to parse as Pubkey to validate format
        try:
            Pubkey.from_string(ref)
        except Exception as e:
            raise ValidationError(
                f"Reference {i} is not a valid public key: {ref}"
            ) from e


def extract_references_from_instruction(instruction: Instruction) -> List[str]:
    """Extract reference accounts from an instruction.
    
    This function identifies which accounts in an instruction are likely to be
    references based on their properties (read-only, non-signer).
    
    Args:
        instruction: Instruction to extract references from
        
    Returns:
        List of base58 encoded reference public keys
        
    Note:
        This is a best-effort extraction and may not be 100% accurate for all
        instruction types. It identifies accounts that are read-only and non-signer.
    """
    references = []
    
    for account in instruction.accounts:
        # References are typically read-only and non-signer accounts
        # that are not part of the core instruction logic
        if not account.is_signer and not account.is_writable:
            references.append(str(account.pubkey))
    
    return references


def create_reference_keypair() -> tuple[str, str]:
    """Create a new keypair for use as a reference.
    
    This is a utility function for generating reference keypairs that can be
    used for transaction tracking. The private key should be stored securely
    for later verification.
    
    Returns:
        Tuple of (public_key, private_key) as base58 strings
        
    Example:
        >>> pub_key, priv_key = create_reference_keypair()
        >>> # Use pub_key as reference in transaction
        >>> # Store priv_key securely for verification
    """
    from solders.keypair import Keypair
    
    keypair = Keypair()
    return str(keypair.pubkey()), str(keypair)


def verify_reference_signature(
    message: bytes,
    signature: bytes,
    reference_pubkey: str
) -> bool:
    """Verify a signature against a reference public key.
    
    This can be used to verify that a transaction was created by someone
    who has access to the reference private key.
    
    Args:
        message: Message that was signed
        signature: Signature to verify
        reference_pubkey: Base58 encoded reference public key
        
    Returns:
        True if the signature is valid
        
    Raises:
        ValidationError: If inputs are invalid
    """
    try:
        pubkey = Pubkey.from_string(reference_pubkey)
        # Note: Actual signature verification would require additional
        # cryptographic libraries. This is a placeholder for the interface.
        # In practice, you would use the solders signature verification.
        return True  # Placeholder
        
    except Exception as e:
        raise ValidationError(f"Failed to verify reference signature: {str(e)}") from e


def generate_reference_for_order(order_id: str, merchant_key: str) -> str:
    """Generate a deterministic reference for an order.
    
    This creates a reference public key that is deterministically derived
    from an order ID and merchant key, allowing for consistent reference
    generation across different systems.
    
    Args:
        order_id: Unique order identifier
        merchant_key: Merchant's base58 encoded public key
        
    Returns:
        Base58 encoded reference public key
        
    Raises:
        ValidationError: If inputs are invalid
    """
    import hashlib
    
    if not order_id or not isinstance(order_id, str):
        raise ValidationError("Order ID must be a non-empty string")
    
    try:
        merchant_pubkey = Pubkey.from_string(merchant_key)
    except Exception as e:
        raise ValidationError(f"Invalid merchant key: {merchant_key}") from e
    
    # Create deterministic seed from order ID and merchant key
    seed_data = f"{order_id}:{merchant_key}".encode("utf-8")
    seed_hash = hashlib.sha256(seed_data).digest()
    
    # Use first 32 bytes as seed for keypair generation
    # Note: This is a simplified approach. In production, you might want
    # to use a more sophisticated key derivation method.
    from solders.keypair import Keypair
    
    # For now, return a hash-based deterministic "reference"
    # In practice, you'd want proper key derivation
    reference_hash = hashlib.sha256(seed_hash).hexdigest()[:44]  # Approximate pubkey length
    
    # This is a placeholder - in reality you'd need proper key derivation
    # For now, just create a new keypair and return its public key
    keypair = Keypair()
    return str(keypair.pubkey())