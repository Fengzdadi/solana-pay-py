"""Pydantic schemas for Solana Pay transaction request API."""

from __future__ import annotations

from typing import List, Optional
from pydantic import BaseModel, Field, field_validator
from decimal import Decimal

from ..utils.errors import ValidationError


class TransactionRequest(BaseModel):
    """Request schema for POST /tx endpoint.
    
    This represents the request that wallets send to merchants to request
    a transaction to be created.
    """
    
    account: str = Field(
        ...,
        description="Base58 encoded public key of the payer account",
        min_length=32,
        max_length=44
    )
    
    @field_validator('account')
    @classmethod
    def validate_account(cls, v):
        """Validate that account is a valid base58 public key."""
        if not v or not isinstance(v, str):
            raise ValueError("Account must be a non-empty string")
        
        # Basic validation - could be enhanced with actual base58 decoding
        if not (32 <= len(v) <= 44):
            raise ValueError("Account must be a valid base58 public key")
        
        return v


class TransactionResponse(BaseModel):
    """Response schema for POST /tx endpoint.
    
    This represents the response that merchants send back to wallets
    containing the serialized transaction.
    """
    
    transaction: str = Field(
        ...,
        description="Base64 encoded serialized transaction"
    )
    
    message: Optional[str] = Field(
        None,
        description="Optional message to display to the user"
    )


class TransactionMetadata(BaseModel):
    """Response schema for GET /tx endpoint.
    
    This represents the metadata that merchants provide about their
    transaction request endpoint.
    """
    
    label: str = Field(
        ...,
        description="Human-readable label for the merchant",
        min_length=1,
        max_length=100
    )
    
    icon: Optional[str] = Field(
        None,
        description="URL to an icon image for the merchant",
        max_length=500
    )
    
    @field_validator('icon')
    @classmethod
    def validate_icon_url(cls, v):
        """Validate that icon is a valid URL if provided."""
        if v is not None:
            if not isinstance(v, str):
                raise ValueError("Icon must be a string URL")
            
            # Basic URL validation
            if not (v.startswith('http://') or v.startswith('https://')):
                raise ValueError("Icon must be a valid HTTP/HTTPS URL")
        
        return v


class MerchantConfig(BaseModel):
    """Configuration for a merchant's transaction request server.
    
    This model contains all the configuration needed to set up a
    transaction request server for a merchant.
    """
    
    label: str = Field(
        ...,
        description="Human-readable merchant name",
        min_length=1,
        max_length=100
    )
    
    icon: Optional[str] = Field(
        None,
        description="URL to merchant icon image",
        max_length=500
    )
    
    recipient: str = Field(
        ...,
        description="Base58 encoded recipient public key",
        min_length=32,
        max_length=44
    )
    
    amount: Optional[Decimal] = Field(
        None,
        description="Fixed payment amount (None for variable amounts)",
        ge=0
    )
    
    spl_token: Optional[str] = Field(
        None,
        description="SPL token mint address (None for SOL)",
        min_length=32,
        max_length=44
    )
    
    memo: Optional[str] = Field(
        None,
        description="Fixed memo for all transactions",
        max_length=566
    )
    
    references: Optional[List[str]] = Field(
        None,
        description="Reference public keys for transaction tracking"
    )
    
    require_memo: bool = Field(
        False,
        description="Whether memo is required from the client"
    )
    
    @field_validator('recipient', 'spl_token')
    @classmethod
    def validate_pubkey_fields(cls, v, info):
        """Validate public key fields."""
        field = info.field_name
        if v is not None:
            if not isinstance(v, str):
                raise ValueError(f"{field.name} must be a string")
            
            if not (32 <= len(v) <= 44):
                raise ValueError(f"{field.name} must be a valid base58 public key")
        
        return v
    
    @field_validator('references')
    @classmethod
    def validate_references(cls, v):
        """Validate reference public keys."""
        if v is not None:
            if not isinstance(v, list):
                raise ValueError("References must be a list")
            
            for i, ref in enumerate(v):
                if not isinstance(ref, str):
                    raise ValueError(f"Reference {i} must be a string")
                
                if not (32 <= len(ref) <= 44):
                    raise ValueError(f"Reference {i} must be a valid base58 public key")
        
        return v


class ErrorResponse(BaseModel):
    """Error response schema for API endpoints."""
    
    error: str = Field(
        ...,
        description="Error message"
    )
    
    code: Optional[str] = Field(
        None,
        description="Error code for programmatic handling"
    )
    
    details: Optional[dict] = Field(
        None,
        description="Additional error details"
    )


# Legacy schemas for backward compatibility
TxGetResp = TransactionMetadata
TxPostReq = TransactionRequest  
TxPostResp = TransactionResponse