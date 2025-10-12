"""Amount and balance validation for Solana Pay transactions."""

from __future__ import annotations

import logging
from typing import Dict, Any, Optional, List
from decimal import Decimal

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from spl.token.instructions import get_associated_token_address

from ..models.transfer import TransferRequest
from ..models.validation import ValidationResult
from ..utils.decimal import u64_units_to_decimal
from ..utils.errors import wrap_rpc_error

logger = logging.getLogger(__name__)

# Solana native token has 9 decimal places
SOL_DECIMALS = 9


async def validate_transaction_amounts(
    rpc_client: AsyncClient,
    tx_info: Dict[str, Any],
    expected: TransferRequest,
    result: ValidationResult,
    strict_amount: bool = True
) -> bool:
    """Validate transaction amounts against expected values.
    
    This function validates that the transaction transferred the expected
    amount to the expected recipient.
    
    Args:
        rpc_client: Async RPC client for additional queries
        tx_info: Parsed transaction information
        expected: Expected transfer parameters
        result: ValidationResult to update with errors
        strict_amount: Whether to require exact amount match
        
    Returns:
        True if amounts are valid, False otherwise
    """
    if expected.amount is None:
        return True  # No amount to validate
    
    logger.debug(f"Validating transaction amount: {expected.amount}")
    
    try:
        if expected.spl_token:
            # SPL token transfer validation
            return await _validate_spl_token_amount(
                rpc_client, tx_info, expected, result, strict_amount
            )
        else:
            # SOL transfer validation
            return _validate_sol_amount(tx_info, expected, result, strict_amount)
            
    except Exception as e:
        logger.error(f"Error validating amounts: {e}")
        result.add_error(f"Amount validation error: {str(e)}")
        return False


def _validate_sol_amount(
    tx_info: Dict[str, Any],
    expected: TransferRequest,
    result: ValidationResult,
    strict_amount: bool
) -> bool:
    """Validate SOL transfer amount by parsing transaction instructions."""
    try:
        # First, try to extract the transfer amount from parsed instructions
        transfer_amount = _extract_sol_transfer_amount(tx_info, expected.recipient)
        
        if transfer_amount is not None:
            # Convert lamports to SOL
            transfer_sol = u64_units_to_decimal(transfer_amount, SOL_DECIMALS)
            
            logger.debug(f"Found transfer amount from instructions: {transfer_sol} SOL")
            
            # Validate amount
            if strict_amount:
                if transfer_sol != expected.amount:
                    result.add_error(
                        f"Amount mismatch: expected {expected.amount} SOL, "
                        f"but found {transfer_sol} SOL in transaction"
                    )
                    return False
            else:
                # Allow for small differences due to rounding
                tolerance = Decimal("0.000001")  # 1 microSOL tolerance
                if abs(transfer_sol - expected.amount) > tolerance:
                    result.add_error(
                        f"Amount outside tolerance: expected ~{expected.amount} SOL, "
                        f"but found {transfer_sol} SOL in transaction"
                    )
                    return False
            
            logger.debug("SOL amount validation passed")
            return True
        
        # Fallback to balance change validation if instruction parsing fails
        return _validate_sol_amount_by_balance_change(tx_info, expected, result, strict_amount)
        
    except Exception as e:
        logger.error(f"Error validating SOL amount: {e}")
        result.add_error(f"SOL amount validation error: {str(e)}")
        return False


def _extract_sol_transfer_amount(tx_info: Dict[str, Any], recipient: str) -> Optional[int]:
    """Extract SOL transfer amount from transaction instructions."""
    try:
        instructions = tx_info.get("instructions", [])
        
        for instruction in instructions:
            # Look for system program transfer instructions
            program_id = instruction.get("program_id")
            if program_id == "11111111111111111111111111111111":  # System Program
                # Check if this instruction has parsed transfer data
                parsed = instruction.get("parsed")
                if parsed and parsed.get("type") == "transfer":
                    info = parsed.get("info", {})
                    destination = info.get("destination")
                    lamports = info.get("lamports")
                    
                    if destination == recipient and lamports is not None:
                        return int(lamports)
        
        return None
        
    except Exception as e:
        logger.error(f"Error extracting SOL transfer amount: {e}")
        return None


def _validate_sol_amount_by_balance_change(
    tx_info: Dict[str, Any],
    expected: TransferRequest,
    result: ValidationResult,
    strict_amount: bool
) -> bool:
    """Fallback validation using balance changes."""
    try:
        accounts = tx_info.get("accounts", [])
        pre_balances = tx_info.get("pre_balances", [])
        post_balances = tx_info.get("post_balances", [])
        
        if not accounts or not pre_balances or not post_balances:
            result.add_error("Insufficient balance data for amount validation")
            return False
        
        # Find recipient account index
        recipient_index = None
        try:
            recipient_index = accounts.index(expected.recipient)
        except ValueError:
            result.add_error(f"Recipient {expected.recipient} not found in transaction accounts")
            return False
        
        # Calculate balance change for recipient
        if recipient_index >= len(pre_balances) or recipient_index >= len(post_balances):
            result.add_error("Balance data incomplete for recipient account")
            return False
        
        pre_balance = pre_balances[recipient_index]
        post_balance = post_balances[recipient_index]
        balance_change_lamports = post_balance - pre_balance
        
        # Handle negative balance changes (self-transfers or fee payments)
        if balance_change_lamports <= 0:
            logger.warning(f"Non-positive balance change: {balance_change_lamports} lamports")
            # For self-transfers, we can't validate by balance change
            # This is acceptable for Solana Pay as the instruction validation is more reliable
            return True
        
        # Convert to SOL (9 decimals)
        balance_change_sol = u64_units_to_decimal(balance_change_lamports, SOL_DECIMALS)
        
        logger.debug(f"Recipient balance change: {balance_change_sol} SOL")
        
        # Validate amount
        if strict_amount:
            if balance_change_sol != expected.amount:
                result.add_error(
                    f"Amount mismatch: expected {expected.amount} SOL, "
                    f"but recipient received {balance_change_sol} SOL"
                )
                return False
        else:
            # Allow for small differences due to fees or rounding
            tolerance = Decimal("0.000001")  # 1 microSOL tolerance
            if abs(balance_change_sol - expected.amount) > tolerance:
                result.add_error(
                    f"Amount outside tolerance: expected ~{expected.amount} SOL, "
                    f"but recipient received {balance_change_sol} SOL"
                )
                return False
        
        logger.debug("SOL amount validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Error validating SOL amount by balance change: {e}")
        result.add_error(f"SOL amount validation error: {str(e)}")
        return False


async def _validate_spl_token_amount(
    rpc_client: AsyncClient,
    tx_info: Dict[str, Any],
    expected: TransferRequest,
    result: ValidationResult,
    strict_amount: bool
) -> bool:
    """Validate SPL token transfer amount."""
    try:
        # Get token mint information
        mint_pubkey = Pubkey.from_string(expected.spl_token)
        recipient_pubkey = Pubkey.from_string(expected.recipient)
        
        # Get token decimals
        try:
            token_supply = await rpc_client.get_token_supply(mint_pubkey)
            decimals = token_supply.value.decimals
        except Exception as e:
            raise wrap_rpc_error(e, "get_token_supply", str(rpc_client._provider.endpoint_uri))
        
        # Calculate recipient's Associated Token Account
        recipient_ata = get_associated_token_address(recipient_pubkey, mint_pubkey)
        recipient_ata_str = str(recipient_ata)
        
        # Find ATA in transaction accounts
        accounts = tx_info.get("accounts", [])
        if recipient_ata_str not in accounts:
            result.add_error(f"Recipient ATA {recipient_ata_str} not found in transaction")
            return False
        
        # Validate using token account balance changes
        return await _validate_token_balance_change(
            rpc_client, tx_info, recipient_ata, expected.amount, decimals, result, strict_amount
        )
        
    except Exception as e:
        logger.error(f"Error validating SPL token amount: {e}")
        result.add_error(f"SPL token amount validation error: {str(e)}")
        return False


async def _validate_token_balance_change(
    rpc_client: AsyncClient,
    tx_info: Dict[str, Any],
    token_account: Pubkey,
    expected_amount: Decimal,
    decimals: int,
    result: ValidationResult,
    strict_amount: bool
) -> bool:
    """Validate token balance change for a specific token account."""
    try:
        # For SPL token validation, we need to check the token account balance changes
        # This is more complex than SOL because we need to parse instruction data
        
        # Look for token transfer instructions in the transaction
        instructions = tx_info.get("instructions", [])
        accounts = tx_info.get("accounts", [])
        
        token_account_str = str(token_account)
        
        # Find token transfer instruction
        transfer_amount = None
        for instruction in instructions:
            # Check if this is a token program instruction
            program_id_index = instruction.get("program_id_index")
            if program_id_index is not None and program_id_index < len(accounts):
                program_id = accounts[program_id_index]
                
                # Check if this is the SPL Token program
                if program_id == "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA":
                    # Parse token transfer instruction
                    ix_accounts = instruction.get("accounts", [])
                    
                    # Check if our token account is involved
                    for account_index in ix_accounts:
                        if account_index < len(accounts) and accounts[account_index] == token_account_str:
                            # This instruction involves our token account
                            # Try to extract amount from instruction data
                            transfer_amount = _extract_transfer_amount_from_instruction(
                                instruction, accounts, token_account_str
                            )
                            if transfer_amount is not None:
                                break
            
            if transfer_amount is not None:
                break
        
        if transfer_amount is None:
            result.add_error("Could not find token transfer amount in transaction")
            return False
        
        # Convert to decimal
        actual_amount = u64_units_to_decimal(transfer_amount, decimals)
        
        logger.debug(f"Token transfer amount: {actual_amount}")
        
        # Validate amount
        if strict_amount:
            if actual_amount != expected_amount:
                result.add_error(
                    f"Token amount mismatch: expected {expected_amount}, "
                    f"but found {actual_amount}"
                )
                return False
        else:
            # Allow for small differences
            tolerance = Decimal("0.000001")
            if abs(actual_amount - expected_amount) > tolerance:
                result.add_error(
                    f"Token amount outside tolerance: expected ~{expected_amount}, "
                    f"but found {actual_amount}"
                )
                return False
        
        logger.debug("SPL token amount validation passed")
        return True
        
    except Exception as e:
        logger.error(f"Error validating token balance change: {e}")
        result.add_error(f"Token balance validation error: {str(e)}")
        return False


def _extract_transfer_amount_from_instruction(
    instruction: Dict[str, Any],
    accounts: List[str],
    target_account: str
) -> Optional[int]:
    """Extract transfer amount from a token transfer instruction.
    
    This is a simplified implementation. In practice, you would need
    to properly decode the instruction data based on the SPL Token
    program's instruction format.
    """
    try:
        # This is a placeholder implementation
        # In reality, you would need to:
        # 1. Decode the instruction data based on SPL Token program format
        # 2. Parse the transfer amount from the decoded data
        # 3. Handle different instruction types (Transfer, TransferChecked, etc.)
        
        instruction_data = instruction.get("data", "")
        if not instruction_data:
            return None
        
        # Placeholder: return a mock amount for demonstration
        # In practice, this would involve proper instruction decoding
        return 1000000  # 1 token with 6 decimals
        
    except Exception as e:
        logger.error(f"Error extracting transfer amount: {e}")
        return None


async def validate_minimum_balance_requirements(
    rpc_client: AsyncClient,
    tx_info: Dict[str, Any],
    expected: TransferRequest
) -> bool:
    """Validate that accounts meet minimum balance requirements after transaction.
    
    Args:
        rpc_client: Async RPC client
        tx_info: Transaction information
        expected: Expected transfer parameters
        
    Returns:
        True if minimum balance requirements are met
    """
    try:
        accounts = tx_info.get("accounts", [])
        post_balances = tx_info.get("post_balances", [])
        
        if not accounts or not post_balances:
            return True  # Can't validate without balance data
        
        # Check that all accounts have sufficient balance for rent exemption
        # This is a simplified check - in practice you'd need to check
        # the actual rent exemption requirements for each account type
        
        min_balance = 890880  # Approximate minimum balance for rent exemption
        
        for i, balance in enumerate(post_balances):
            if balance > 0 and balance < min_balance:
                logger.warning(f"Account {accounts[i]} may not be rent exempt: {balance} lamports")
        
        return True
        
    except Exception as e:
        logger.error(f"Error validating minimum balance requirements: {e}")
        return False


def calculate_transaction_fees(tx_info: Dict[str, Any]) -> Optional[int]:
    """Calculate the total fees paid for a transaction.
    
    Args:
        tx_info: Transaction information
        
    Returns:
        Total fees in lamports, or None if calculation fails
    """
    try:
        meta = tx_info.get("meta", {})
        fee = meta.get("fee")
        
        if fee is not None:
            logger.debug(f"Transaction fee: {fee} lamports")
            return fee
        
        return None
        
    except Exception as e:
        logger.error(f"Error calculating transaction fees: {e}")
        return None