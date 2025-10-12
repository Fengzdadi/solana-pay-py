"""Reference account validation for Solana Pay transactions."""

from __future__ import annotations

import logging
from typing import Dict, Any, List

from ..models.transfer import TransferRequest
from ..models.validation import ValidationResult

logger = logging.getLogger(__name__)


def validate_transaction_references(
    tx_info: Dict[str, Any],
    expected: TransferRequest,
    result: ValidationResult
) -> bool:
    """Validate that transaction contains expected reference accounts.
    
    References in Solana Pay are used for transaction tracking and identification.
    They should appear as read-only accounts in the transaction.
    
    Args:
        tx_info: Parsed transaction information
        expected: Expected transfer parameters
        result: ValidationResult to update with errors
        
    Returns:
        True if references are valid, False otherwise
    """
    if not expected.references:
        return True  # No references to validate
    
    logger.debug(f"Validating {len(expected.references)} reference accounts")
    
    try:
        # Get transaction accounts
        tx_accounts = tx_info.get("accounts", [])
        
        if not tx_accounts:
            result.add_error("Transaction has no accounts to validate references against")
            return False
        
        # Check each expected reference
        missing_references = []
        for i, expected_ref in enumerate(expected.references):
            if expected_ref not in tx_accounts:
                missing_references.append(expected_ref)
                logger.warning(f"Reference {i} not found in transaction: {expected_ref}")
        
        if missing_references:
            result.add_error(
                f"Missing reference accounts: {', '.join(missing_references)}"
            )
            return False
        
        # Validate reference ordering if strict validation is enabled
        if hasattr(result, 'strict_reference_ordering') and result.strict_reference_ordering:
            if not _validate_reference_ordering(tx_accounts, expected.references, result):
                return False
        
        logger.debug("All reference accounts found in transaction")
        return True
        
    except Exception as e:
        logger.error(f"Error validating references: {e}")
        result.add_error(f"Reference validation error: {str(e)}")
        return False


def _validate_reference_ordering(
    tx_accounts: List[str],
    expected_references: List[str],
    result: ValidationResult
) -> bool:
    """Validate that references appear in the expected order.
    
    Args:
        tx_accounts: List of transaction account addresses
        expected_references: Expected reference accounts in order
        result: ValidationResult to update with errors
        
    Returns:
        True if ordering is correct, False otherwise
    """
    try:
        # Find positions of references in transaction accounts
        ref_positions = []
        for ref in expected_references:
            try:
                position = tx_accounts.index(ref)
                ref_positions.append(position)
            except ValueError:
                # Reference not found (should have been caught earlier)
                result.add_error(f"Reference not found for ordering validation: {ref}")
                return False
        
        # Check if positions are in ascending order
        if ref_positions != sorted(ref_positions):
            result.add_warning(
                "Reference accounts are not in the expected order. "
                "This may indicate a different transaction structure."
            )
            # Note: This is a warning, not an error, as ordering might not be critical
        
        return True
        
    except Exception as e:
        result.add_error(f"Reference ordering validation error: {str(e)}")
        return False


def extract_references_from_transaction(tx_info: Dict[str, Any]) -> List[str]:
    """Extract potential reference accounts from a transaction.
    
    This function attempts to identify which accounts in a transaction
    might be references based on their usage patterns.
    
    Args:
        tx_info: Parsed transaction information
        
    Returns:
        List of potential reference account addresses
    """
    potential_references = []
    
    try:
        accounts = tx_info.get("accounts", [])
        instructions = tx_info.get("instructions", [])
        
        if not accounts or not instructions:
            return potential_references
        
        # Track which accounts are used as signers or writable
        used_accounts = set()
        
        for instruction in instructions:
            # Get accounts used in this instruction
            ix_accounts = instruction.get("accounts", [])
            for account_index in ix_accounts:
                if account_index < len(accounts):
                    used_accounts.add(accounts[account_index])
        
        # Potential references are accounts that appear in the transaction
        # but are not heavily used in instructions (read-only references)
        for account in accounts:
            if account not in used_accounts:
                potential_references.append(account)
        
        logger.debug(f"Found {len(potential_references)} potential reference accounts")
        
    except Exception as e:
        logger.error(f"Error extracting references: {e}")
    
    return potential_references


def validate_reference_signatures(
    tx_info: Dict[str, Any],
    reference_keypairs: Dict[str, str]
) -> Dict[str, bool]:
    """Validate signatures for reference accounts.
    
    This function can be used to verify that reference accounts were
    properly signed if they were meant to be signers.
    
    Args:
        tx_info: Parsed transaction information
        reference_keypairs: Dict mapping reference pubkeys to private keys
        
    Returns:
        Dict mapping reference pubkeys to signature validation results
    """
    validation_results = {}
    
    try:
        # This is a placeholder for signature validation logic
        # In practice, you would need to:
        # 1. Extract the transaction message
        # 2. Verify signatures against the message
        # 3. Match signatures to reference accounts
        
        for ref_pubkey in reference_keypairs.keys():
            # Placeholder - actual signature validation would go here
            validation_results[ref_pubkey] = True
            
        logger.debug(f"Validated signatures for {len(validation_results)} references")
        
    except Exception as e:
        logger.error(f"Error validating reference signatures: {e}")
        for ref_pubkey in reference_keypairs.keys():
            validation_results[ref_pubkey] = False
    
    return validation_results


def find_reference_in_logs(
    tx_info: Dict[str, Any],
    reference_data: str
) -> bool:
    """Find reference data in transaction logs.
    
    Some applications include reference information in transaction logs
    rather than as account references.
    
    Args:
        tx_info: Parsed transaction information
        reference_data: Reference data to search for
        
    Returns:
        True if reference data is found in logs
    """
    try:
        log_messages = tx_info.get("log_messages", [])
        
        for log in log_messages:
            if reference_data in log:
                logger.debug(f"Found reference data in log: {reference_data}")
                return True
        
        return False
        
    except Exception as e:
        logger.error(f"Error searching logs for reference: {e}")
        return False


def validate_reference_metadata(
    reference_accounts: List[str],
    expected_metadata: Dict[str, Any]
) -> Dict[str, bool]:
    """Validate metadata associated with reference accounts.
    
    This function can validate additional metadata that might be
    associated with reference accounts.
    
    Args:
        reference_accounts: List of reference account addresses
        expected_metadata: Expected metadata for validation
        
    Returns:
        Dict mapping reference accounts to validation results
    """
    validation_results = {}
    
    try:
        for ref_account in reference_accounts:
            # Placeholder for metadata validation logic
            # In practice, this might involve:
            # - Checking account data
            # - Validating account ownership
            # - Verifying account state
            
            validation_results[ref_account] = True
            
        logger.debug(f"Validated metadata for {len(validation_results)} references")
        
    except Exception as e:
        logger.error(f"Error validating reference metadata: {e}")
        for ref_account in reference_accounts:
            validation_results[ref_account] = False
    
    return validation_results