"""Validation result data models."""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import List, Optional


@dataclass
class ValidationResult:
    """Result of transaction validation against expected parameters.
    
    This model contains the results of validating a completed transaction
    against the expected payment parameters, including detailed information
    about what matched and what didn't.
    
    Attributes:
        is_valid: Overall validation result (True if all checks passed)
        recipient_match: Whether the recipient matches expected value
        amount_match: Whether the amount matches expected value
        memo_match: Whether the memo matches expected value (if provided)
        references_match: Whether references match expected values (if provided)
        spl_token_match: Whether SPL token mint matches expected value (if provided)
        confirmation_status: Transaction confirmation level on blockchain
        signature: Transaction signature that was validated
        errors: List of validation error messages
        warnings: List of validation warning messages
        block_time: Block time when transaction was confirmed (if available)
        slot: Slot number when transaction was confirmed (if available)
    """
    
    is_valid: bool
    recipient_match: bool
    amount_match: bool
    memo_match: bool
    references_match: bool
    spl_token_match: bool = True  # Default to True for SOL transfers
    confirmation_status: str = "unknown"
    signature: Optional[str] = None
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)
    block_time: Optional[int] = None
    slot: Optional[int] = None

    def __post_init__(self) -> None:
        """Validate the validation result after initialization."""
        # Ensure confirmation_status is valid
        valid_statuses = {"processed", "confirmed", "finalized", "unknown"}
        if self.confirmation_status not in valid_statuses:
            raise ValueError(f"confirmation_status must be one of {valid_statuses}")
        
        # Ensure errors and warnings are lists of strings
        if not isinstance(self.errors, list):
            raise ValueError("errors must be a list")
        if not all(isinstance(error, str) for error in self.errors):
            raise ValueError("all errors must be strings")
        
        if not isinstance(self.warnings, list):
            raise ValueError("warnings must be a list")
        if not all(isinstance(warning, str) for warning in self.warnings):
            raise ValueError("all warnings must be strings")

    def add_error(self, error: str) -> None:
        """Add an error message to the validation result.
        
        Args:
            error: Error message to add
        """
        self.errors.append(error)
        self.is_valid = False

    def add_warning(self, warning: str) -> None:
        """Add a warning message to the validation result.
        
        Args:
            warning: Warning message to add
        """
        self.warnings.append(warning)

    def summary(self) -> str:
        """Get a human-readable summary of the validation result.
        
        Returns:
            String summary of the validation result
        """
        if self.is_valid:
            return f"✅ Transaction validation passed ({self.confirmation_status})"
        
        error_count = len(self.errors)
        warning_count = len(self.warnings)
        
        parts = [f"❌ Transaction validation failed with {error_count} error(s)"]
        if warning_count > 0:
            parts.append(f"and {warning_count} warning(s)")
        
        return " ".join(parts)

    def detailed_report(self) -> str:
        """Get a detailed report of the validation result.
        
        Returns:
            Detailed string report of all validation checks
        """
        lines = [self.summary()]
        
        if self.signature:
            lines.append(f"Signature: {self.signature}")
        
        lines.append(f"Confirmation: {self.confirmation_status}")
        
        # Individual check results
        checks = [
            ("Recipient", self.recipient_match),
            ("Amount", self.amount_match),
            ("Memo", self.memo_match),
            ("References", self.references_match),
            ("SPL Token", self.spl_token_match),
        ]
        
        lines.append("\nValidation Checks:")
        for check_name, passed in checks:
            status = "✅" if passed else "❌"
            lines.append(f"  {status} {check_name}")
        
        if self.errors:
            lines.append("\nErrors:")
            for error in self.errors:
                lines.append(f"  • {error}")
        
        if self.warnings:
            lines.append("\nWarnings:")
            for warning in self.warnings:
                lines.append(f"  • {warning}")
        
        return "\n".join(lines)


@dataclass
class ValidationConfig:
    """Configuration for transaction validation behavior.
    
    This model allows customization of how strict the validation should be
    and what aspects of the transaction to validate.
    
    Attributes:
        strict_amount: Whether to require exact amount matches (vs minimum)
        require_memo: Whether memo presence is required for validation
        require_references: Whether references are required for validation
        allow_extra_instructions: Whether extra instructions are allowed
        max_confirmation_time: Maximum time to wait for confirmation (seconds)
        required_confirmation: Minimum confirmation level required
        validate_fees: Whether to validate transaction fees are reasonable
    """
    
    strict_amount: bool = True
    require_memo: bool = False
    require_references: bool = False
    allow_extra_instructions: bool = True
    max_confirmation_time: int = 60
    required_confirmation: str = "confirmed"
    validate_fees: bool = False

    def __post_init__(self) -> None:
        """Validate the validation configuration after initialization."""
        valid_confirmations = {"processed", "confirmed", "finalized"}
        if self.required_confirmation not in valid_confirmations:
            raise ValueError(f"required_confirmation must be one of {valid_confirmations}")
        
        if not isinstance(self.max_confirmation_time, int) or self.max_confirmation_time <= 0:
            raise ValueError("max_confirmation_time must be a positive integer")