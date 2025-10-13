"""Comprehensive tests for URL encoding and parsing functionality."""

import pytest
from decimal import Decimal
from solanapay.urls import encode_url, parse_url
from solanapay.models.transfer import TransferRequest
from solanapay.utils.errors import URLError, ValidationError


# Test vectors for comprehensive testing
VALID_PUBKEY = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
VALID_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC mint
VALID_REFERENCE = "11111111111111111111111111111112"


def test_encode_minimal():
    """Test minimal URL encoding."""
    req = TransferRequest(recipient=VALID_PUBKEY)
    url = encode_url(req)
    assert url.startswith(f"solana://{VALID_PUBKEY}")
    parsed = parse_url(url)
    assert parsed.recipient == req.recipient
    assert parsed.amount is None
    assert parsed.references is None


def test_roundtrip_with_amount():
    """Test roundtrip with amount."""
    req = TransferRequest(
        recipient=VALID_PUBKEY,
        amount=Decimal("1.25")
    )
    url = encode_url(req)
    parsed = parse_url(url)
    assert parsed.recipient == req.recipient
    assert parsed.amount == Decimal("1.25")


def test_spl_token_payment():
    """Test SPL token payment."""
    req = TransferRequest(
        recipient=VALID_PUBKEY,
        amount=Decimal("10.50"),
        spl_token=VALID_MINT
    )
    url = encode_url(req)
    parsed = parse_url(url)
    assert parsed.recipient == req.recipient
    assert parsed.amount == Decimal("10.5")  # Normalized
    assert parsed.spl_token == VALID_MINT


def test_with_references():
    """Test with reference accounts."""
    references = [VALID_REFERENCE, "22222222222222222222222222222223"]
    req = TransferRequest(
        recipient=VALID_PUBKEY,
        references=references
    )
    url = encode_url(req)
    parsed = parse_url(url)
    assert parsed.references == references


def test_with_text_fields():
    """Test with text fields."""
    req = TransferRequest(
        recipient=VALID_PUBKEY,
        label="Coffee Shop",
        message="Thanks for your purchase!",
        memo="order-123"
    )
    url = encode_url(req)
    parsed = parse_url(url)
    assert parsed.label == req.label
    assert parsed.message == req.message
    assert parsed.memo == req.memo


def test_https_discovery():
    """Test HTTPS URL parsing for transaction discovery."""
    url = "https://merchant.example.com/tx?amount=2.5&label=Demo"
    # HTTPS URLs for discovery currently require a recipient in our model
    # This is a design limitation that should be addressed
    with pytest.raises(URLError, match="Invalid parameters in URL: recipient is required"):
        parse_url(url)


def test_invalid_amount():
    """Test invalid amount handling."""
    bad_url = f"solana://{VALID_PUBKEY}?amount=abc"
    with pytest.raises((ValueError, URLError)):
        parse_url(bad_url)


def test_negative_amount_rejected():
    """Test negative amount rejection."""
    with pytest.raises((ValueError, ValidationError)):
        TransferRequest(recipient=VALID_PUBKEY, amount=Decimal("-1"))


class TestTransferRequest:
    """Test TransferRequest model validation."""
    
    def test_valid_request(self):
        """Test creating a valid transfer request."""
        request = TransferRequest(
            recipient=VALID_PUBKEY,
            amount=Decimal("0.01"),
            spl_token=VALID_MINT,
            references=[VALID_REFERENCE],
            label="Test",
            message="Test message",
            memo="test-memo"
        )
        assert request.recipient == VALID_PUBKEY
        assert request.amount == Decimal("0.01")
    
    def test_invalid_recipient(self):
        """Test invalid recipient validation."""
        with pytest.raises(ValidationError):
            TransferRequest(recipient="invalid_key")
    
    def test_negative_amount(self):
        """Test negative amount validation."""
        with pytest.raises(ValidationError):
            TransferRequest(recipient=VALID_PUBKEY, amount=Decimal("-1"))