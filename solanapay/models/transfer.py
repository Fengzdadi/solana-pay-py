"""Transfer request data model with validation."""

from __future__ import annotations

import re
from dataclasses import dataclass
from decimal import Decimal, InvalidOperation
from typing import List, Optional

from ..utils.errors import ValidationError


@dataclass
class TransferRequest:
    """Core model representing a Solana Pay transfer request.
    
    This model represents all the parameters that can be included in a Solana Pay
    transfer request, whether encoded as a solana: URL or used for transaction building.
    
    Attributes:
        recipient: Base58 encoded public key of the payment recipient
        amount: Payment amount as a Decimal (None for variable amounts)
        spl_token: Base58 encoded mint address for SPL token transfers (None for SOL)
        references: List of base58 encoded reference public keys for tracking
        label: Human-readable label for the payment request
        message: Human-readable message describing the payment
        memo: On-chain memo to be included in the transaction
    """
    
    recipient: str
    amount: Optional[Decimal] = None
    spl_token: Optional[str] = None
    references: Optional[List[str]] = None
    label: Optional[str] = None
    message: Optional[str] = None
    memo: Optional[str] = None

    def __post_init__(self) -> None:
        """Validate the transfer request after initialization."""
        self.validate()

    def validate(self) -> None:
        """Validate all fields according to Solana Pay SPEC requirements.
        
        Raises:
            ValidationError: If any field contains invalid data
        """
        # Validate recipient (required)
        if not self.recipient:
            raise ValidationError("recipient is required")
        
        if not self._is_valid_base58_pubkey(self.recipient):
            raise ValidationError(f"recipient must be a valid base58 public key: {self.recipient}")

        # Validate amount (optional, but must be valid if provided)
        if self.amount is not None:
            if not isinstance(self.amount, Decimal):
                try:
                    self.amount = Decimal(str(self.amount))
                except (InvalidOperation, ValueError) as e:
                    raise ValidationError(f"amount must be a valid decimal: {self.amount}") from e
            
            if self.amount < 0:
                raise ValidationError("amount must be non-negative")

        # Validate spl_token (optional, but must be valid if provided)
        if self.spl_token is not None:
            if not self._is_valid_base58_pubkey(self.spl_token):
                raise ValidationError(f"spl_token must be a valid base58 public key: {self.spl_token}")

        # Validate references (optional, but each must be valid if provided)
        if self.references is not None:
            if not isinstance(self.references, list):
                raise ValidationError("references must be a list")
            
            for i, ref in enumerate(self.references):
                if not isinstance(ref, str):
                    raise ValidationError(f"reference[{i}] must be a string")
                if not self._is_valid_base58_pubkey(ref):
                    raise ValidationError(f"reference[{i}] must be a valid base58 public key: {ref}")

        # Validate text fields (optional, but must be strings if provided)
        for field_name in ("label", "message", "memo"):
            field_value = getattr(self, field_name)
            if field_value is not None and not isinstance(field_value, str):
                raise ValidationError(f"{field_name} must be a string")

    @staticmethod
    def _is_valid_base58_pubkey(pubkey: str) -> bool:
        """Check if a string is a valid base58 encoded Solana public key.
        
        Args:
            pubkey: String to validate
            
        Returns:
            True if valid base58 public key, False otherwise
        """
        if not isinstance(pubkey, str):
            return False
        
        # Solana public keys are 32 bytes, which encode to 43-44 base58 characters
        if not (32 <= len(pubkey) <= 44):
            return False
        
        # Check if string contains only valid base58 characters
        # Base58 alphabet: 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz
        base58_pattern = re.compile(r"^[1-9A-HJ-NP-Za-km-z]+$")
        if not base58_pattern.match(pubkey):
            return False
        
        # Additional validation could include actual base58 decoding and length check
        # but for now we'll rely on the pattern and length checks
        return True

    def to_dict(self) -> dict:
        """Convert the transfer request to a dictionary.
        
        Returns:
            Dictionary representation of the transfer request
        """
        result = {"recipient": self.recipient}
        
        if self.amount is not None:
            result["amount"] = str(self.amount)
        if self.spl_token is not None:
            result["spl_token"] = self.spl_token
        if self.references is not None:
            result["references"] = self.references.copy()
        if self.label is not None:
            result["label"] = self.label
        if self.message is not None:
            result["message"] = self.message
        if self.memo is not None:
            result["memo"] = self.memo
            
        return result

    @classmethod
    def from_dict(cls, data: dict) -> TransferRequest:
        """Create a TransferRequest from a dictionary.
        
        Args:
            data: Dictionary containing transfer request data
            
        Returns:
            TransferRequest instance
            
        Raises:
            ValidationError: If the dictionary contains invalid data
        """
        # Convert amount string back to Decimal if present
        if "amount" in data and data["amount"] is not None:
            try:
                data["amount"] = Decimal(str(data["amount"]))
            except (InvalidOperation, ValueError) as e:
                raise ValidationError(f"Invalid amount in data: {data['amount']}") from e
        
        return cls(**data)

    def __str__(self) -> str:
        """String representation of the transfer request."""
        parts = [f"recipient={self.recipient}"]
        
        if self.amount is not None:
            parts.append(f"amount={self.amount}")
        if self.spl_token is not None:
            parts.append(f"spl_token={self.spl_token}")
        if self.references:
            parts.append(f"references={len(self.references)} items")
        if self.label is not None:
            parts.append(f"label='{self.label}'")
        if self.message is not None:
            parts.append(f"message='{self.message}'")
        if self.memo is not None:
            parts.append(f"memo='{self.memo}'")
            
        return f"TransferRequest({', '.join(parts)})"