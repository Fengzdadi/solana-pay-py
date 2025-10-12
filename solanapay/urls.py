"""URL encoding and parsing for Solana Pay protocol.

This module provides functions to encode and parse Solana Pay URLs according to
the official specification, supporting both solana: and https: schemes.
"""

from __future__ import annotations

from typing import Optional
from urllib.parse import urlencode, urlparse, parse_qs, quote

from .models.transfer import TransferRequest
from .utils.decimal import normalize_amount_str, parse_amount
from .utils.errors import URLError, ValidationError

# Supported URL schemes
_SCHEME_SOLANA = "solana"
_SCHEME_HTTPS = "https"

def encode_url(request: TransferRequest) -> str:
    """Generate a solana: Transfer URL from a TransferRequest.
    
    Creates a properly formatted solana: URL according to the Solana Pay specification.
    The recipient is placed in the authority (netloc) portion of the URL, and all
    optional parameters are included as query parameters with proper encoding.
    
    Args:
        request: TransferRequest containing the payment parameters
        
    Returns:
        Properly formatted solana: URL string
        
    Raises:
        URLError: If the request is invalid or URL generation fails
        
    Example:
        >>> request = TransferRequest(
        ...     recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        ...     amount=Decimal("0.01"),
        ...     label="Coffee Shop"
        ... )
        >>> encode_url(request)
        'solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01&label=Coffee%20Shop'
    """
    try:
        # Validate the request (this will raise ValidationError if invalid)
        request.validate()
    except ValidationError as e:
        raise URLError(f"Invalid transfer request: {e.message}") from e
    
    if not request.recipient:
        raise URLError("recipient is required for solana: URL")

    # Build query parameters in the correct order
    query_items: list[tuple[str, str]] = []

    # Add amount with proper decimal formatting
    if request.amount is not None:
        try:
            amount_str = normalize_amount_str(request.amount)
            query_items.append(("amount", amount_str))
        except ValidationError as e:
            raise URLError(f"Invalid amount for URL encoding: {e.message}") from e

    # Add SPL token mint (use SPEC field name "spl-token")
    if request.spl_token:
        query_items.append(("spl-token", request.spl_token))

    # Add references in order (preserve ordering as required by SPEC)
    if request.references:
        for ref in request.references:
            query_items.append(("reference", ref))

    # Add text fields with proper encoding
    if request.label:
        query_items.append(("label", request.label))
    if request.message:
        query_items.append(("message", request.message))
    if request.memo:
        query_items.append(("memo", request.memo))

    # Encode query string (don't convert spaces to '+', use proper URL encoding)
    query_str = urlencode(query_items, doseq=True, quote_via=quote, safe="")

    # Build the final URL with recipient in authority position
    base_url = f"{_SCHEME_SOLANA}://{request.recipient}"
    return base_url + (f"?{query_str}" if query_str else "")

def parse_url(url: str) -> TransferRequest:
    """Parse a solana: or https: URL into a TransferRequest.
    
    Parses URLs according to the Solana Pay specification, supporting both
    solana: URLs for direct transfers and https: URLs for transaction request discovery.
    
    Args:
        url: URL string to parse
        
    Returns:
        TransferRequest object containing the parsed parameters
        
    Raises:
        URLError: If the URL is malformed or contains invalid parameters
        
    Example:
        >>> url = "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01"
        >>> request = parse_url(url)
        >>> request.recipient
        '9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM'
        >>> request.amount
        Decimal('0.01')
    """
    if not isinstance(url, str) or not url.strip():
        raise URLError("URL must be a non-empty string", url=url)
    
    try:
        parsed = urlparse(url.strip())
    except Exception as e:
        raise URLError(f"Failed to parse URL: {str(e)}", url=url) from e
    
    scheme = parsed.scheme.lower()
    if scheme not in (_SCHEME_SOLANA, _SCHEME_HTTPS):
        raise URLError(
            f"Unsupported URL scheme: {parsed.scheme}. Must be 'solana' or 'https'",
            url=url
        )

    # Parse query parameters
    try:
        qs = parse_qs(parsed.query, keep_blank_values=False, strict_parsing=False)
    except Exception as e:
        raise URLError(f"Failed to parse query parameters: {str(e)}", url=url) from e

    def _pick_one(key: str) -> Optional[str]:
        """Extract the first value for a query parameter."""
        values = qs.get(key)
        return values[0] if values else None

    # Parse amount with proper error handling
    amount = None
    amount_str = _pick_one("amount")
    if amount_str is not None:
        try:
            amount = parse_amount(amount_str)
        except ValidationError as e:
            raise URLError(f"Invalid amount in URL: {e.message}", url=url) from e

    # Parse references (preserve order as required by SPEC)
    references = qs.get("reference", None)  # Returns list or None

    # Extract recipient based on scheme
    if scheme == _SCHEME_SOLANA:
        # For solana: URLs, recipient is in netloc or path
        recipient = parsed.netloc or parsed.path.lstrip("/")
        if not recipient:
            raise URLError("solana: URL requires a recipient", url=url)
    else:
        # For https: URLs, recipient is typically empty (used for transaction request discovery)
        recipient = ""

    # Extract text fields (already URL-decoded by parse_qs)
    label = _pick_one("label")
    message = _pick_one("message")
    memo = _pick_one("memo")
    spl_token = _pick_one("spl-token")

    # Create and validate the TransferRequest
    try:
        request = TransferRequest(
            recipient=recipient,
            amount=amount,
            spl_token=spl_token,
            references=references,
            label=label,
            message=message,
            memo=memo,
        )
        # Validation happens in __post_init__
        return request
    except ValidationError as e:
        raise URLError(f"Invalid parameters in URL: {e.message}", url=url) from e


def encode_https_url(request: TransferRequest, base_url: str) -> str:
    """Generate an https: URL for transaction request discovery.
    
    Creates an https: URL that can be used for transaction request discovery,
    where wallets will make GET and POST requests to retrieve transaction details.
    
    Args:
        request: TransferRequest containing the payment parameters
        base_url: Base HTTPS URL for the transaction request endpoint
        
    Returns:
        Properly formatted https: URL string
        
    Raises:
        URLError: If the base URL is invalid or URL generation fails
        
    Example:
        >>> request = TransferRequest(
        ...     recipient="",  # Empty for https URLs
        ...     amount=Decimal("0.01"),
        ...     label="Coffee Shop"
        ... )
        >>> encode_https_url(request, "https://merchant.com/pay")
        'https://merchant.com/pay?amount=0.01&label=Coffee%20Shop'
    """
    if not isinstance(base_url, str) or not base_url.strip():
        raise URLError("base_url must be a non-empty string")
    
    # Validate base URL is https
    try:
        parsed_base = urlparse(base_url.strip())
    except Exception as e:
        raise URLError(f"Invalid base URL: {str(e)}", url=base_url) from e
    
    if parsed_base.scheme.lower() != _SCHEME_HTTPS:
        raise URLError(f"base_url must use https scheme, got: {parsed_base.scheme}", url=base_url)
    
    # Build query parameters (similar to encode_url but without recipient)
    query_items: list[tuple[str, str]] = []

    if request.amount is not None:
        try:
            amount_str = normalize_amount_str(request.amount)
            query_items.append(("amount", amount_str))
        except ValidationError as e:
            raise URLError(f"Invalid amount for URL encoding: {e.message}") from e

    if request.spl_token:
        query_items.append(("spl-token", request.spl_token))

    if request.references:
        for ref in request.references:
            query_items.append(("reference", ref))

    if request.label:
        query_items.append(("label", request.label))
    if request.message:
        query_items.append(("message", request.message))
    if request.memo:
        query_items.append(("memo", request.memo))

    # Encode query string
    query_str = urlencode(query_items, doseq=True, quote_via=quote, safe="")
    
    # Combine base URL with query parameters
    return base_url + (f"?{query_str}" if query_str else "")

def validate_url(url: str) -> bool:
    """Validate a Solana Pay URL format without full parsing.
    
    Args:
        url: URL string to validate
        
    Returns:
        True if the URL appears to be a valid Solana Pay URL
        
    Example:
        >>> validate_url("solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
        True
        >>> validate_url("invalid:url")
        False
    """
    from .utils.url_validation import validate_url_format
    
    is_valid, _ = validate_url_format(url)
    return is_valid


def get_url_type(url: str) -> str:
    """Get the type of Solana Pay URL (solana or https).
    
    Args:
        url: URL to check
        
    Returns:
        URL scheme ("solana" or "https")
        
    Raises:
        URLError: If the URL is not a valid Solana Pay URL
    """
    from .utils.url_validation import get_url_scheme
    
    scheme = get_url_scheme(url)
    if scheme not in (_SCHEME_SOLANA, _SCHEME_HTTPS):
        raise URLError(f"Not a Solana Pay URL: {scheme}")
    
    return scheme


# Convenience functions for backward compatibility and ease of use
def create_transfer_url(
    recipient: str,
    amount: Optional[str] = None,
    spl_token: Optional[str] = None,
    references: Optional[list[str]] = None,
    label: Optional[str] = None,
    message: Optional[str] = None,
    memo: Optional[str] = None,
) -> str:
    """Create a solana: transfer URL from individual parameters.
    
    This is a convenience function that creates a TransferRequest and encodes it as a URL.
    
    Args:
        recipient: Base58 encoded recipient public key
        amount: Payment amount as string (will be converted to Decimal)
        spl_token: SPL token mint address (None for SOL)
        references: List of reference public keys
        label: Human-readable label
        message: Payment description
        memo: On-chain memo
        
    Returns:
        Encoded solana: URL
        
    Raises:
        URLError: If parameters are invalid
    """
    try:
        # Convert amount string to Decimal if provided
        decimal_amount = None
        if amount is not None:
            decimal_amount = parse_amount(amount)
        
        request = TransferRequest(
            recipient=recipient,
            amount=decimal_amount,
            spl_token=spl_token,
            references=references,
            label=label,
            message=message,
            memo=memo,
        )
        
        return encode_url(request)
    except (ValidationError, ValueError) as e:
        raise URLError(f"Failed to create transfer URL: {str(e)}") from e


def parse_transfer_url(url: str) -> dict:
    """Parse a Solana Pay URL and return parameters as a dictionary.
    
    This is a convenience function that parses a URL and returns the parameters
    as a dictionary with string values for easier integration.
    
    Args:
        url: Solana Pay URL to parse
        
    Returns:
        Dictionary containing the parsed parameters
        
    Raises:
        URLError: If the URL is invalid
    """
    request = parse_url(url)
    
    result = {"recipient": request.recipient}
    
    if request.amount is not None:
        result["amount"] = str(request.amount)
    if request.spl_token is not None:
        result["spl_token"] = request.spl_token
    if request.references is not None:
        result["references"] = request.references.copy()
    if request.label is not None:
        result["label"] = request.label
    if request.message is not None:
        result["message"] = request.message
    if request.memo is not None:
        result["memo"] = request.memo
    
    return result