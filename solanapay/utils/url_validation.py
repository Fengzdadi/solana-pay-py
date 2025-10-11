"""URL format validation utilities for Solana Pay URLs."""

from __future__ import annotations

import re
from urllib.parse import urlparse
from typing import Tuple

from .errors import URLError


def validate_url_format(url: str) -> Tuple[bool, str]:
    """Validate URL format without full parsing.
    
    Performs basic format validation on a URL string to check if it could
    be a valid Solana Pay URL before attempting full parsing.
    
    Args:
        url: URL string to validate
        
    Returns:
        Tuple of (is_valid, error_message). If is_valid is True, error_message is empty.
        
    Example:
        >>> validate_url_format("solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
        (True, "")
        >>> validate_url_format("invalid-scheme:test")
        (False, "Unsupported URL scheme: invalid-scheme")
    """
    if not isinstance(url, str):
        return False, "URL must be a string"
    
    url = url.strip()
    if not url:
        return False, "URL cannot be empty"
    
    # Basic URL structure validation
    try:
        parsed = urlparse(url)
    except Exception as e:
        return False, f"Invalid URL format: {str(e)}"
    
    # Check scheme
    scheme = parsed.scheme.lower()
    if scheme not in ("solana", "https"):
        return False, f"Unsupported URL scheme: {parsed.scheme}"
    
    # Validate solana: URLs
    if scheme == "solana":
        # Must have recipient in netloc or path
        recipient = parsed.netloc or parsed.path.lstrip("/")
        if not recipient:
            return False, "solana: URL must contain a recipient"
        
        # Basic recipient format check (should look like a base58 public key)
        if not _is_valid_base58_format(recipient):
            return False, f"Invalid recipient format: {recipient}"
    
    # Validate https: URLs
    elif scheme == "https":
        # Must have a valid domain
        if not parsed.netloc:
            return False, "https: URL must contain a domain"
    
    return True, ""


def validate_solana_url_recipient(recipient: str) -> bool:
    """Validate that a recipient looks like a valid Solana public key.
    
    Args:
        recipient: Recipient string to validate
        
    Returns:
        True if the recipient appears to be a valid base58 public key
    """
    return _is_valid_base58_format(recipient)


def validate_https_url_domain(url: str) -> bool:
    """Validate that an https URL has a valid domain.
    
    Args:
        url: HTTPS URL to validate
        
    Returns:
        True if the URL has a valid domain
    """
    try:
        parsed = urlparse(url)
        return parsed.scheme.lower() == "https" and bool(parsed.netloc)
    except Exception:
        return False


def extract_url_components(url: str) -> dict:
    """Extract components from a URL for debugging purposes.
    
    Args:
        url: URL to extract components from
        
    Returns:
        Dictionary containing URL components
        
    Raises:
        URLError: If the URL cannot be parsed
    """
    try:
        parsed = urlparse(url)
        return {
            "scheme": parsed.scheme,
            "netloc": parsed.netloc,
            "path": parsed.path,
            "params": parsed.params,
            "query": parsed.query,
            "fragment": parsed.fragment,
        }
    except Exception as e:
        raise URLError(f"Failed to extract URL components: {str(e)}", url=url) from e


def normalize_url(url: str) -> str:
    """Normalize a URL by removing extra whitespace and standardizing format.
    
    Args:
        url: URL to normalize
        
    Returns:
        Normalized URL string
        
    Raises:
        URLError: If the URL cannot be normalized
    """
    if not isinstance(url, str):
        raise URLError("URL must be a string")
    
    # Remove leading/trailing whitespace
    url = url.strip()
    
    if not url:
        raise URLError("URL cannot be empty")
    
    # Basic normalization - ensure scheme is lowercase
    try:
        parsed = urlparse(url)
        if parsed.scheme:
            # Reconstruct with lowercase scheme
            scheme = parsed.scheme.lower()
            if scheme == "solana":
                # Solana URLs use single colon, not double slash
                normalized = f"{scheme}:{parsed.netloc}{parsed.path}"
                if parsed.query:
                    normalized += f"?{parsed.query}"
                if parsed.fragment:
                    normalized += f"#{parsed.fragment}"
                return normalized
            elif scheme == "https":
                # HTTPS URLs use double slash
                normalized = f"{scheme}://{parsed.netloc}{parsed.path}"
                if parsed.query:
                    normalized += f"?{parsed.query}"
                if parsed.fragment:
                    normalized += f"#{parsed.fragment}"
                return normalized
    except Exception as e:
        raise URLError(f"Failed to normalize URL: {str(e)}", url=url) from e
    
    # If we can't normalize, return the original (trimmed)
    return url


def _is_valid_base58_format(value: str) -> bool:
    """Check if a string has valid base58 format for a Solana public key.
    
    This is a format check only - it doesn't validate that the key actually
    decodes to a valid 32-byte public key.
    
    Args:
        value: String to check
        
    Returns:
        True if the string has valid base58 format
    """
    if not isinstance(value, str):
        return False
    
    # Solana public keys are 32 bytes, which encode to 43-44 base58 characters
    if not (32 <= len(value) <= 44):
        return False
    
    # Check if string contains only valid base58 characters
    # Base58 alphabet: 123456789ABCDEFGHJKLMNPQRSTUVWXYZabcdefghijkmnopqrstuvwxyz
    # (excludes 0, O, I, l to avoid confusion)
    base58_pattern = re.compile(r"^[1-9A-HJ-NP-Za-km-z]+$")
    return bool(base58_pattern.match(value))


def is_solana_pay_url(url: str) -> bool:
    """Check if a URL is a Solana Pay URL (solana: or https: scheme).
    
    Args:
        url: URL to check
        
    Returns:
        True if the URL appears to be a Solana Pay URL
    """
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme.lower() in ("solana", "https")
    except Exception:
        return False


def get_url_scheme(url: str) -> str:
    """Get the scheme from a URL.
    
    Args:
        url: URL to extract scheme from
        
    Returns:
        URL scheme in lowercase
        
    Raises:
        URLError: If the URL cannot be parsed
    """
    try:
        parsed = urlparse(url.strip())
        return parsed.scheme.lower()
    except Exception as e:
        raise URLError(f"Failed to extract URL scheme: {str(e)}", url=url) from e