"""Transaction-related data models."""

from __future__ import annotations

from dataclasses import dataclass
from typing import List, Optional


@dataclass
class TransactionBuildResult:
    """Result of a transaction building operation.
    
    This model contains all the information about a successfully built transaction,
    including the serialized transaction data and metadata about the transaction.
    
    Attributes:
        transaction: Base64 encoded serialized transaction
        signers_required: List of public keys that must sign the transaction
        instructions_count: Number of instructions in the transaction
        estimated_fee: Estimated transaction fee in lamports
        uses_lookup_tables: Whether the transaction uses Address Lookup Tables
        compute_units: Estimated compute units required for the transaction
    """
    
    transaction: str
    signers_required: List[str]
    instructions_count: int
    estimated_fee: int
    uses_lookup_tables: bool = False
    compute_units: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate the transaction build result after initialization."""
        if not isinstance(self.transaction, str):
            raise ValueError("transaction must be a base64 encoded string")
        
        if not isinstance(self.signers_required, list):
            raise ValueError("signers_required must be a list")
        
        if not all(isinstance(signer, str) for signer in self.signers_required):
            raise ValueError("all signers_required must be strings")
        
        if not isinstance(self.instructions_count, int) or self.instructions_count < 0:
            raise ValueError("instructions_count must be a non-negative integer")
        
        if not isinstance(self.estimated_fee, int) or self.estimated_fee < 0:
            raise ValueError("estimated_fee must be a non-negative integer")


@dataclass
class TransactionOptions:
    """Options for customizing transaction building behavior.
    
    This model allows users to customize various aspects of how transactions
    are built, including fees, compute limits, and feature flags.
    
    Attributes:
        priority_fee: Additional priority fee in lamports (None for default)
        auto_create_ata: Whether to automatically create Associated Token Accounts
        use_versioned_tx: Whether to use versioned transactions (v0)
        compute_unit_limit: Maximum compute units for the transaction
        compute_unit_price: Price per compute unit in micro-lamports
        use_lookup_tables: Whether to use Address Lookup Tables when beneficial
        max_retries: Maximum number of RPC retries for transaction building
        timeout: Timeout in seconds for RPC operations
    """
    
    priority_fee: Optional[int] = None
    auto_create_ata: bool = True
    use_versioned_tx: bool = True
    compute_unit_limit: Optional[int] = None
    compute_unit_price: Optional[int] = None
    use_lookup_tables: bool = False
    max_retries: int = 3
    timeout: int = 30

    def __post_init__(self) -> None:
        """Validate transaction options after initialization."""
        if self.priority_fee is not None and (not isinstance(self.priority_fee, int) or self.priority_fee < 0):
            raise ValueError("priority_fee must be a non-negative integer or None")
        
        if not isinstance(self.auto_create_ata, bool):
            raise ValueError("auto_create_ata must be a boolean")
        
        if not isinstance(self.use_versioned_tx, bool):
            raise ValueError("use_versioned_tx must be a boolean")
        
        if self.compute_unit_limit is not None and (not isinstance(self.compute_unit_limit, int) or self.compute_unit_limit <= 0):
            raise ValueError("compute_unit_limit must be a positive integer or None")
        
        if self.compute_unit_price is not None and (not isinstance(self.compute_unit_price, int) or self.compute_unit_price < 0):
            raise ValueError("compute_unit_price must be a non-negative integer or None")
        
        if not isinstance(self.use_lookup_tables, bool):
            raise ValueError("use_lookup_tables must be a boolean")
        
        if not isinstance(self.max_retries, int) or self.max_retries < 0:
            raise ValueError("max_retries must be a non-negative integer")
        
        if not isinstance(self.timeout, int) or self.timeout <= 0:
            raise ValueError("timeout must be a positive integer")


@dataclass
class TransactionMetadata:
    """Metadata about a transaction request for the GET /tx endpoint.
    
    This model represents the metadata that merchants provide to wallets
    when they make a GET request to the transaction request endpoint.
    
    Attributes:
        label: Human-readable label for the merchant or transaction
        icon: Optional URL to an icon image for the merchant
    """
    
    label: str
    icon: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate transaction metadata after initialization."""
        if not isinstance(self.label, str) or not self.label.strip():
            raise ValueError("label must be a non-empty string")
        
        if self.icon is not None:
            if not isinstance(self.icon, str):
                raise ValueError("icon must be a string URL or None")
            
            # Validate URL format
            if not (self.icon.startswith('http://') or self.icon.startswith('https://')):
                raise ValueError("Icon must be a valid HTTP/HTTPS URL")