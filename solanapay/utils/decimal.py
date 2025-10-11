"""Decimal handling utilities for precise amount calculations."""

from __future__ import annotations

from decimal import Decimal, InvalidOperation, ROUND_HALF_UP
from typing import Union

from .errors import ValidationError


def normalize_amount_str(amount: Decimal) -> str:
    """Convert a Decimal amount to a normalized string representation.
    
    This function ensures that amounts are represented in a consistent format
    without scientific notation and with trailing zeros removed, as required
    by the Solana Pay specification.
    
    Args:
        amount: Decimal amount to normalize
        
    Returns:
        Normalized string representation of the amount
        
    Raises:
        ValidationError: If the amount is invalid
    """
    if not isinstance(amount, Decimal):
        raise ValidationError("Amount must be a Decimal", field="amount", value=amount)
    
    if amount < 0:
        raise ValidationError("Amount must be non-negative", field="amount", value=amount)
    
    # Normalize to remove trailing zeros and avoid scientific notation
    normalized = amount.normalize()
    
    # Convert to string using fixed-point notation
    amount_str = format(normalized, "f")
    
    # Remove trailing zeros and decimal point if not needed
    if "." in amount_str:
        amount_str = amount_str.rstrip("0").rstrip(".")
    
    # Handle the case where we end up with an empty string (should be "0")
    return amount_str or "0"


def parse_amount(amount_str: str) -> Decimal:
    """Parse an amount string into a Decimal.
    
    This function safely parses amount strings from URLs or user input
    into Decimal objects, with proper error handling.
    
    Args:
        amount_str: String representation of the amount
        
    Returns:
        Decimal representation of the amount
        
    Raises:
        ValidationError: If the amount string is invalid
    """
    if not isinstance(amount_str, str):
        raise ValidationError("Amount must be a string", field="amount", value=amount_str)
    
    if not amount_str.strip():
        raise ValidationError("Amount cannot be empty", field="amount", value=amount_str)
    
    try:
        amount = Decimal(amount_str.strip())
    except (InvalidOperation, ValueError) as e:
        raise ValidationError(
            f"Invalid amount format: {amount_str}",
            field="amount",
            value=amount_str
        ) from e
    
    if amount < 0:
        raise ValidationError(
            "Amount must be non-negative",
            field="amount", 
            value=amount_str
        )
    
    return amount


def decimal_to_u64_units(amount: Decimal, decimals: int) -> int:
    """Convert a decimal amount to u64 units for blockchain operations.
    
    This function converts human-readable decimal amounts to the integer
    units used by Solana tokens, handling the decimal places correctly.
    
    Args:
        amount: Decimal amount to convert
        decimals: Number of decimal places for the token
        
    Returns:
        Integer amount in token's base units
        
    Raises:
        ValidationError: If the conversion would result in overflow or invalid values
    """
    if not isinstance(amount, Decimal):
        raise ValidationError("Amount must be a Decimal", field="amount", value=amount)
    
    if not isinstance(decimals, int) or decimals < 0 or decimals > 18:
        raise ValidationError(
            "Decimals must be an integer between 0 and 18",
            field="decimals",
            value=decimals
        )
    
    if amount < 0:
        raise ValidationError("Amount must be non-negative", field="amount", value=amount)
    
    # Calculate the scaling factor
    scale = Decimal(10) ** decimals
    
    # Scale the amount and round to nearest integer
    scaled_amount = (amount * scale).quantize(Decimal("1"), rounding=ROUND_HALF_UP)
    
    # Convert to integer
    try:
        units = int(scaled_amount)
    except (ValueError, OverflowError) as e:
        raise ValidationError(
            f"Amount too large for conversion: {amount}",
            field="amount",
            value=amount
        ) from e
    
    # Check for u64 overflow (2^64 - 1)
    if units > 18_446_744_073_709_551_615:
        raise ValidationError(
            f"Amount exceeds maximum u64 value: {units}",
            field="amount",
            value=amount
        )
    
    return units


def u64_units_to_decimal(units: int, decimals: int) -> Decimal:
    """Convert u64 units from blockchain to decimal amount.
    
    This function converts integer token units from the blockchain back
    to human-readable decimal amounts.
    
    Args:
        units: Integer amount in token's base units
        decimals: Number of decimal places for the token
        
    Returns:
        Decimal amount
        
    Raises:
        ValidationError: If the inputs are invalid
    """
    if not isinstance(units, int) or units < 0:
        raise ValidationError("Units must be a non-negative integer", field="units", value=units)
    
    if not isinstance(decimals, int) or decimals < 0 or decimals > 18:
        raise ValidationError(
            "Decimals must be an integer between 0 and 18",
            field="decimals",
            value=decimals
        )
    
    # Calculate the scaling factor
    scale = Decimal(10) ** decimals
    
    # Convert to decimal
    return Decimal(units) / scale


def validate_amount_precision(amount: Decimal, max_decimals: int) -> None:
    """Validate that an amount doesn't exceed the maximum decimal precision.
    
    Args:
        amount: Decimal amount to validate
        max_decimals: Maximum number of decimal places allowed
        
    Raises:
        ValidationError: If the amount has too many decimal places
    """
    if not isinstance(amount, Decimal):
        raise ValidationError("Amount must be a Decimal", field="amount", value=amount)
    
    if not isinstance(max_decimals, int) or max_decimals < 0:
        raise ValidationError(
            "Max decimals must be a non-negative integer",
            field="max_decimals",
            value=max_decimals
        )
    
    # Get the number of decimal places in the amount
    sign, digits, exponent = amount.as_tuple()
    
    if exponent < 0:
        decimal_places = -exponent
        if decimal_places > max_decimals:
            raise ValidationError(
                f"Amount has too many decimal places: {decimal_places} > {max_decimals}",
                field="amount",
                value=amount
            )


def safe_decimal_from_float(value: Union[float, int, str]) -> Decimal:
    """Safely convert various numeric types to Decimal.
    
    This function provides a safe way to convert floats, integers, and strings
    to Decimal objects, avoiding floating-point precision issues.
    
    Args:
        value: Numeric value to convert
        
    Returns:
        Decimal representation of the value
        
    Raises:
        ValidationError: If the value cannot be converted to Decimal
    """
    if isinstance(value, Decimal):
        return value
    
    if isinstance(value, int):
        return Decimal(value)
    
    if isinstance(value, float):
        # Convert float to string first to avoid precision issues
        return Decimal(str(value))
    
    if isinstance(value, str):
        return parse_amount(value)
    
    raise ValidationError(
        f"Cannot convert {type(value).__name__} to Decimal",
        field="value",
        value=value
    )