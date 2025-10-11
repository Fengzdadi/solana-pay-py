"""Associated Token Account (ATA) management utilities."""

from __future__ import annotations

from typing import Optional, Tuple
from solana.rpc.async_api import AsyncClient
from solders.instruction import Instruction
from solders.pubkey import Pubkey
from spl.token.instructions import get_associated_token_address, create_associated_token_account

from .errors import AccountNotFoundError, RPCError, wrap_rpc_error


async def get_or_create_ata(
    rpc: AsyncClient,
    owner: str,
    mint: str,
    payer: Optional[str] = None
) -> Tuple[str, Optional[Instruction]]:
    """Get Associated Token Account address and create instruction if needed.
    
    This function checks if an ATA exists for the given owner and mint.
    If it doesn't exist, it returns an instruction to create it.
    
    Args:
        rpc: Async RPC client
        owner: Base58 encoded owner public key
        mint: Base58 encoded mint public key
        payer: Base58 encoded payer public key (defaults to owner)
        
    Returns:
        Tuple of (ata_address, create_instruction). create_instruction is None
        if the ATA already exists.
        
    Raises:
        RPCError: If RPC communication fails
        
    Example:
        >>> ata_addr, create_ix = await get_or_create_ata(rpc, owner, mint, payer)
        >>> if create_ix:
        ...     # ATA doesn't exist, include create_ix in transaction
        ...     instructions.append(create_ix)
    """
    try:
        owner_pk = Pubkey.from_string(owner)
        mint_pk = Pubkey.from_string(mint)
        payer_pk = Pubkey.from_string(payer) if payer else owner_pk
        
        # Calculate ATA address
        ata_address = get_associated_token_address(owner_pk, mint_pk)
        
        # Check if ATA exists
        account_info = await rpc.get_account_info(ata_address)
        
        if account_info.value is None:
            # ATA doesn't exist, create instruction
            create_ix = create_associated_token_account(
                payer=payer_pk,
                owner=owner_pk,
                mint=mint_pk
            )
            return str(ata_address), create_ix
        else:
            # ATA exists
            return str(ata_address), None
            
    except Exception as e:
        if isinstance(e, RPCError):
            raise
        raise wrap_rpc_error(e, "get_account_info", str(rpc._provider.endpoint_uri))


async def check_ata_exists(
    rpc: AsyncClient,
    owner: str,
    mint: str
) -> bool:
    """Check if an Associated Token Account exists.
    
    Args:
        rpc: Async RPC client
        owner: Base58 encoded owner public key
        mint: Base58 encoded mint public key
        
    Returns:
        True if the ATA exists, False otherwise
        
    Raises:
        RPCError: If RPC communication fails
    """
    try:
        owner_pk = Pubkey.from_string(owner)
        mint_pk = Pubkey.from_string(mint)
        
        ata_address = get_associated_token_address(owner_pk, mint_pk)
        account_info = await rpc.get_account_info(ata_address)
        
        return account_info.value is not None
        
    except Exception as e:
        raise wrap_rpc_error(e, "get_account_info", str(rpc._provider.endpoint_uri))


def calculate_ata_address(owner: str, mint: str) -> str:
    """Calculate the Associated Token Account address for an owner and mint.
    
    This is a pure function that doesn't require RPC calls.
    
    Args:
        owner: Base58 encoded owner public key
        mint: Base58 encoded mint public key
        
    Returns:
        Base58 encoded ATA address
        
    Example:
        >>> ata_addr = calculate_ata_address(owner_key, mint_key)
        >>> print(f"ATA address: {ata_addr}")
    """
    owner_pk = Pubkey.from_string(owner)
    mint_pk = Pubkey.from_string(mint)
    
    ata_address = get_associated_token_address(owner_pk, mint_pk)
    return str(ata_address)


def create_ata_instruction(
    payer: str,
    owner: str,
    mint: str
) -> Instruction:
    """Create an instruction to create an Associated Token Account.
    
    Args:
        payer: Base58 encoded payer public key (pays for account creation)
        owner: Base58 encoded owner public key (owns the ATA)
        mint: Base58 encoded mint public key (token type)
        
    Returns:
        Instruction to create the ATA
        
    Example:
        >>> create_ix = create_ata_instruction(payer_key, owner_key, mint_key)
        >>> instructions.append(create_ix)
    """
    payer_pk = Pubkey.from_string(payer)
    owner_pk = Pubkey.from_string(owner)
    mint_pk = Pubkey.from_string(mint)
    
    return create_associated_token_account(
        payer=payer_pk,
        owner=owner_pk,
        mint=mint_pk
    )


async def get_ata_balance(
    rpc: AsyncClient,
    owner: str,
    mint: str
) -> int:
    """Get the token balance of an Associated Token Account.
    
    Args:
        rpc: Async RPC client
        owner: Base58 encoded owner public key
        mint: Base58 encoded mint public key
        
    Returns:
        Token balance in base units (not decimal adjusted)
        
    Raises:
        AccountNotFoundError: If the ATA doesn't exist
        RPCError: If RPC communication fails
    """
    try:
        owner_pk = Pubkey.from_string(owner)
        mint_pk = Pubkey.from_string(mint)
        
        ata_address = get_associated_token_address(owner_pk, mint_pk)
        
        # Get token account balance
        balance_response = await rpc.get_token_account_balance(ata_address)
        
        if balance_response.value is None:
            raise AccountNotFoundError(
                f"Associated Token Account not found for owner {owner} and mint {mint}",
                account_address=str(ata_address),
                account_type="ATA"
            )
        
        return int(balance_response.value.amount)
        
    except AccountNotFoundError:
        raise
    except Exception as e:
        raise wrap_rpc_error(e, "get_token_account_balance", str(rpc._provider.endpoint_uri))


async def get_multiple_ata_balances(
    rpc: AsyncClient,
    accounts: list[Tuple[str, str]]  # List of (owner, mint) tuples
) -> dict[str, int]:
    """Get balances for multiple Associated Token Accounts.
    
    This is more efficient than calling get_ata_balance multiple times.
    
    Args:
        rpc: Async RPC client
        accounts: List of (owner, mint) tuples
        
    Returns:
        Dictionary mapping ATA addresses to balances
        
    Raises:
        RPCError: If RPC communication fails
    """
    if not accounts:
        return {}
    
    try:
        # Calculate all ATA addresses
        ata_addresses = []
        address_to_account = {}
        
        for owner, mint in accounts:
            owner_pk = Pubkey.from_string(owner)
            mint_pk = Pubkey.from_string(mint)
            ata_address = get_associated_token_address(owner_pk, mint_pk)
            ata_str = str(ata_address)
            
            ata_addresses.append(ata_address)
            address_to_account[ata_str] = (owner, mint)
        
        # Get multiple account infos
        account_infos = await rpc.get_multiple_accounts(ata_addresses)
        
        balances = {}
        for i, account_info in enumerate(account_infos.value):
            ata_str = str(ata_addresses[i])
            
            if account_info is None:
                # Account doesn't exist, balance is 0
                balances[ata_str] = 0
            else:
                # Get token account balance
                try:
                    balance_response = await rpc.get_token_account_balance(ata_addresses[i])
                    if balance_response.value:
                        balances[ata_str] = int(balance_response.value.amount)
                    else:
                        balances[ata_str] = 0
                except Exception:
                    balances[ata_str] = 0
        
        return balances
        
    except Exception as e:
        raise wrap_rpc_error(e, "get_multiple_accounts", str(rpc._provider.endpoint_uri))


def is_ata_address(address: str, owner: str, mint: str) -> bool:
    """Check if an address is the correct ATA for the given owner and mint.
    
    Args:
        address: Base58 encoded address to check
        owner: Base58 encoded owner public key
        mint: Base58 encoded mint public key
        
    Returns:
        True if the address is the correct ATA
    """
    try:
        expected_ata = calculate_ata_address(owner, mint)
        return address == expected_ata
    except Exception:
        return False