"""Enhanced transaction building for Solana Pay transfers.

This module provides comprehensive transaction building functionality for SOL and SPL token
transfers, with support for memos, references, priority fees, and proper error handling.
"""

from __future__ import annotations

from base64 import b64encode
from typing import List, Optional

from solana.rpc.async_api import AsyncClient
from solders.hash import Hash
from solders.instruction import AccountMeta, Instruction
from solders.message import MessageV0
from solders.transaction import VersionedTransaction
from solders.signature import Signature
from solders.pubkey import Pubkey
from solders.system_program import TransferParams, transfer
from solders.transaction import NullSigner
from solders.compute_budget import set_compute_unit_price, set_compute_unit_limit
from spl.token.constants import TOKEN_PROGRAM_ID
from spl.token.instructions import get_associated_token_address, create_associated_token_account
from spl.token.instructions import TransferCheckedParams, transfer_checked

from ..models.transfer import TransferRequest
from ..models.transaction import TransactionBuildResult, TransactionOptions
from ..utils.decimal import decimal_to_u64_units
from ..utils.errors import (
    TransactionBuildError, 
    RPCError, 
    AccountNotFoundError,
    wrap_rpc_error
)

# Constants
LAMPORTS_PER_SOL = 1_000_000_000
MEMO_PROGRAM_ID = Pubkey.from_string("MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr")

# Default transaction options
DEFAULT_COMPUTE_UNIT_LIMIT = 200_000
DEFAULT_PRIORITY_FEE = 0


async def build_transfer_transaction(
    rpc: AsyncClient,
    payer: str,
    request: TransferRequest,
    options: Optional[TransactionOptions] = None
) -> TransactionBuildResult:
    """Build a transfer transaction from a TransferRequest.
    
    This is the main entry point for building transfer transactions. It handles both
    SOL and SPL token transfers with comprehensive error handling and options support.
    
    Args:
        rpc: Async RPC client for blockchain communication
        payer: Base58 encoded payer public key
        request: TransferRequest containing payment parameters
        options: Optional transaction building options
        
    Returns:
        TransactionBuildResult containing the built transaction and metadata
        
    Raises:
        TransactionBuildError: If transaction building fails
        RPCError: If RPC communication fails
    """
    if options is None:
        options = TransactionOptions()
    
    try:
        # Validate inputs
        request.validate()
        payer_pk = Pubkey.from_string(payer)
        recipient_pk = Pubkey.from_string(request.recipient)
        
        # Build the appropriate transaction type
        if request.spl_token is None:
            # SOL transfer
            transaction = await _build_sol_transfer(
                rpc, payer_pk, recipient_pk, request, options
            )
        else:
            # SPL token transfer
            mint_pk = Pubkey.from_string(request.spl_token)
            transaction = await _build_spl_transfer(
                rpc, payer_pk, recipient_pk, mint_pk, request, options
            )
        
        # Serialize transaction
        serialized = b64encode(bytes(transaction)).decode("ascii")
        
        # Calculate metadata
        signers_required = [payer]  # Payer is always required
        instructions_count = len(transaction.message.instructions)
        
        # Estimate fee (basic calculation)
        estimated_fee = 5000  # Base fee in lamports
        if options.priority_fee:
            estimated_fee += options.priority_fee
        
        return TransactionBuildResult(
            transaction=serialized,
            signers_required=signers_required,
            instructions_count=instructions_count,
            estimated_fee=estimated_fee,
            uses_lookup_tables=options.use_lookup_tables,
            compute_units=options.compute_unit_limit
        )
        
    except Exception as e:
        if isinstance(e, (TransactionBuildError, RPCError)):
            raise
        raise TransactionBuildError(
            f"Failed to build transfer transaction: {str(e)}",
            transaction_type="transfer"
        ) from e


async def _build_sol_transfer(
    rpc: AsyncClient,
    payer: Pubkey,
    recipient: Pubkey,
    request: TransferRequest,
    options: TransactionOptions
) -> VersionedTransaction:
    """Build a SOL transfer transaction."""
    if request.amount is None:
        raise TransactionBuildError("Amount is required for SOL transfers")
    
    instructions: List[Instruction] = []
    
    # Add compute budget instructions if specified
    if options.compute_unit_limit:
        instructions.append(set_compute_unit_limit(options.compute_unit_limit))
    
    if options.compute_unit_price:
        instructions.append(set_compute_unit_price(options.compute_unit_price))
    
    # Build transfer instruction
    try:
        lamports = decimal_to_u64_units(request.amount, 9)  # SOL has 9 decimals
        transfer_ix = transfer(TransferParams(
            from_pubkey=payer,
            to_pubkey=recipient,
            lamports=lamports
        ))
        
        # Add references if provided
        if request.references:
            transfer_ix = _append_references(transfer_ix, request.references)
        
        instructions.append(transfer_ix)
        
    except Exception as e:
        raise TransactionBuildError(f"Failed to build SOL transfer instruction: {str(e)}") from e
    
    # Add memo instruction if provided
    if request.memo:
        instructions.append(_build_memo_instruction(request.memo))
    
    # Build and return transaction
    return await _build_versioned_transaction(rpc, payer, instructions, options)


async def _build_spl_transfer(
    rpc: AsyncClient,
    payer: Pubkey,
    recipient: Pubkey,
    mint: Pubkey,
    request: TransferRequest,
    options: TransactionOptions
) -> VersionedTransaction:
    """Build an SPL token transfer transaction."""
    if request.amount is None:
        raise TransactionBuildError("Amount is required for SPL token transfers")
    
    instructions: List[Instruction] = []
    
    # Add compute budget instructions if specified
    if options.compute_unit_limit:
        instructions.append(set_compute_unit_limit(options.compute_unit_limit))
    
    if options.compute_unit_price:
        instructions.append(set_compute_unit_price(options.compute_unit_price))
    
    try:
        # Get token decimals
        decimals = await _get_mint_decimals(rpc, mint)
        
        # Get Associated Token Accounts
        payer_ata = get_associated_token_address(payer, mint)
        recipient_ata = get_associated_token_address(recipient, mint)
        
        # Check if recipient ATA exists and create if needed
        if options.auto_create_ata:
            create_ata_ix = await _ensure_recipient_ata_instruction(
                rpc, payer, recipient, mint
            )
            if create_ata_ix:
                instructions.append(create_ata_ix)
        
        # Build transfer instruction
        amount_units = decimal_to_u64_units(request.amount, decimals)
        transfer_ix = transfer_checked(TransferCheckedParams(
            program_id=TOKEN_PROGRAM_ID,
            source=payer_ata,
            mint=mint,
            dest=recipient_ata,
            owner=payer,
            amount=amount_units,
            decimals=decimals,
            signers=[]
        ))
        
        # Add references if provided
        if request.references:
            transfer_ix = _append_references(transfer_ix, request.references)
        
        instructions.append(transfer_ix)
        
    except Exception as e:
        raise TransactionBuildError(f"Failed to build SPL transfer instruction: {str(e)}") from e
    
    # Add memo instruction if provided
    if request.memo:
        instructions.append(_build_memo_instruction(request.memo))
    
    # Build and return transaction
    return await _build_versioned_transaction(rpc, payer, instructions, options)


async def _build_versioned_transaction(
    rpc: AsyncClient,
    payer: Pubkey,
    instructions: List[Instruction],
    options: TransactionOptions
) -> VersionedTransaction:
    """Build a versioned transaction from instructions."""
    try:
        # Get recent blockhash
        recent_blockhash = await _get_latest_blockhash(rpc)
        
        # Build message
        if options.use_versioned_tx:
            # Use v0 message format
            message = MessageV0.try_compile(
                payer=payer,
                instructions=instructions,
                address_lookup_table_accounts=[],  # ALT support can be added later
                recent_blockhash=recent_blockhash
            )
        else:
            # Fallback to legacy message format would go here
            # For now, we always use v0
            message = MessageV0.try_compile(
                payer=payer,
                instructions=instructions,
                address_lookup_table_accounts=[],
                recent_blockhash=recent_blockhash
            )
        
        # Create transaction with placeholder signatures
        num_required = message.header.num_required_signatures
        placeholder_sigs = [Signature.default() for _ in range(num_required)]
        
        return VersionedTransaction(message, [NullSigner(payer)])
        
    except Exception as e:
        raise TransactionBuildError(f"Failed to build versioned transaction: {str(e)}") from e


def _build_memo_instruction(memo_text: str) -> Instruction:
    """Build a memo instruction.
    
    Args:
        memo_text: Text to include in the memo
        
    Returns:
        Memo instruction
    """
    if not isinstance(memo_text, str) or not memo_text.strip():
        raise TransactionBuildError("Memo text must be a non-empty string")
    
    data = memo_text.encode("utf-8")
    return Instruction(MEMO_PROGRAM_ID, data, ())


async def _get_latest_blockhash(rpc: AsyncClient) -> Hash:
    """Get the latest blockhash from the RPC."""
    try:
        resp = await rpc.get_latest_blockhash()
        return resp.value.blockhash  # type: ignore[attr-defined]
    except Exception as e:
        raise wrap_rpc_error(e, "get_latest_blockhash", str(rpc._provider.endpoint_uri))


async def _get_mint_decimals(rpc: AsyncClient, mint: Pubkey) -> int:
    """Get the decimal places for an SPL token mint."""
    try:
        resp = await rpc.get_token_supply(mint)
        return resp.value.decimals  # type: ignore[attr-defined]
    except Exception as e:
        raise wrap_rpc_error(e, "get_token_supply", str(rpc._provider.endpoint_uri))


async def _ensure_recipient_ata_instruction(
    rpc: AsyncClient, 
    payer: Pubkey, 
    owner: Pubkey, 
    mint: Pubkey
) -> Optional[Instruction]:
    """Check if recipient ATA exists and return create instruction if needed."""
    try:
        ata = get_associated_token_address(owner, mint)
        account_info = await rpc.get_account_info(ata)
        
        if account_info.value is None:
            # ATA doesn't exist, create instruction to create it
            return create_associated_token_account(payer=payer, owner=owner, mint=mint)
        
        return None  # ATA already exists
        
    except Exception as e:
        raise wrap_rpc_error(e, "get_account_info", str(rpc._provider.endpoint_uri))


def _append_references(instruction: Instruction, references: List[str]) -> Instruction:
    """Append reference accounts to an instruction.
    
    References are added as read-only, non-signer accounts as required by the SPEC.
    
    Args:
        instruction: Original instruction
        references: List of base58 encoded reference public keys
        
    Returns:
        New instruction with references appended
    """
    if not references:
        return instruction
    
    try:
        # Convert reference strings to Pubkeys
        reference_pubkeys = [Pubkey.from_string(ref) for ref in references]
        
        # Create new account metas for references
        new_accounts = list(instruction.accounts)
        for ref_pk in reference_pubkeys:
            new_accounts.append(AccountMeta(
                pubkey=ref_pk,
                is_signer=False,
                is_writable=False
            ))
        
        # Create new instruction with updated accounts
        return Instruction(
            program_id=instruction.program_id,
            data=instruction.data,
            accounts=tuple(new_accounts)
        )
        
    except Exception as e:
        raise TransactionBuildError(f"Failed to append references: {str(e)}") from e


async def build_transfer_tx(
    rpc: AsyncClient,
    *,
    payer: str,
    recipient: str,
    amount: Decimal,
    spl_token: Optional[str] = None,
    memo: Optional[str] = None,
    references: Optional[Iterable[str]] = None,
    auto_create_recipient_ata: bool = True,
) -> str:
    """
    使用 solders 构造未签名交易（Base64 编码）
    """
    payer_pk = Pubkey.from_string(payer)
    recipient_pk = Pubkey.from_string(recipient)
    refs: List[Pubkey] = [Pubkey.from_string(r) for r in references or []]

    ixs: List[Instruction] = []

    if spl_token is None:
        lamports = _decimal_to_u64_units(amount, 9)
        ix = transfer(TransferParams(from_pubkey=payer_pk, to_pubkey=recipient_pk, lamports=lamports))
        ix = _append_references(ix, refs)
        ixs.append(ix)
    else:
        mint_pk = Pubkey.from_string(spl_token)
        decimals = await _get_mint_decimals(rpc, mint_pk)

        payer_ata = get_associated_token_address(payer_pk, mint_pk)
        recipient_ata, create_ata_ix = await _ensure_recipient_ata_ix(
            rpc, payer=payer_pk, owner=recipient_pk, mint=mint_pk
        )
        if create_ata_ix and auto_create_recipient_ata:
            ixs.append(create_ata_ix)

        amt = _decimal_to_u64_units(amount, decimals)
        ix = transfer_checked(
            TransferCheckedParams(
                program_id=TOKEN_PROGRAM_ID,
                source=payer_ata,
                mint=mint_pk,
                dest=recipient_ata,
                owner=payer_pk,
                amount=amt,
                decimals=decimals,
                signers=[],
            )
        )
        ix = _append_references(ix, refs)
        ixs.append(ix)

    if memo:
        ixs.append(_build_memo_ix(memo))

    recent_blockhash = await _get_latest_blockhash(rpc)

    # 用 v0 消息编译器；第三个参数是 ALT（先不用，给空列表）
    msg = MessageV0.try_compile(
        payer=payer_pk,
        instructions=ixs,
        address_lookup_table_accounts=[],     # 先不用 ALT；以后要扩展再加
        recent_blockhash=recent_blockhash,
    )

    # 关键：用“占位签名”填充到与所需签名数一致
    num_required = msg.header.num_required_signatures
    placeholder_sigs = [Signature.default() for _ in range(num_required)]

    tx = VersionedTransaction(msg, [NullSigner(payer_pk)])
    raw = tx.serialize()
    return b64encode(bytes(raw)).decode("ascii")
# Leg
# acy function for backward compatibility
async def build_transfer_tx(
    rpc: AsyncClient,
    *,
    payer: str,
    recipient: str,
    amount,  # Can be Decimal or string
    spl_token: Optional[str] = None,
    memo: Optional[str] = None,
    references: Optional[List[str]] = None,
    auto_create_recipient_ata: bool = True,
) -> str:
    """Legacy function for building transfer transactions.
    
    This function maintains backward compatibility with the original API.
    New code should use build_transfer_transaction() instead.
    
    Args:
        rpc: Async RPC client
        payer: Base58 encoded payer public key
        recipient: Base58 encoded recipient public key
        amount: Transfer amount (Decimal or string)
        spl_token: Optional SPL token mint address
        memo: Optional memo text
        references: Optional list of reference public keys
        auto_create_recipient_ata: Whether to auto-create recipient ATA
        
    Returns:
        Base64 encoded transaction string
    """
    from decimal import Decimal
    from ..utils.decimal import safe_decimal_from_float
    
    # Convert amount to Decimal
    if not isinstance(amount, Decimal):
        amount = safe_decimal_from_float(amount)
    
    # Create TransferRequest
    request = TransferRequest(
        recipient=recipient,
        amount=amount,
        spl_token=spl_token,
        memo=memo,
        references=references
    )
    
    # Create options
    options = TransactionOptions(auto_create_ata=auto_create_recipient_ata)
    
    # Build transaction using new function
    result = await build_transfer_transaction(rpc, payer, request, options)
    return result.transaction