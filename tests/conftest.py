"""Test configuration and fixtures."""

import os
import sys
import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, MagicMock

# Add parent directory to path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

# Test constants
VALID_PUBKEY = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
VALID_MINT = "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"  # USDC mint
VALID_REFERENCE = "11111111111111111111111111111112"
TEST_SIGNATURE = "5VERv8NMvzbJMEkV8xnrLkEaWRtSz9CosKDYjCJjBRnbJLgp8uirBgmQpjKhoR4tjF3ZpRzrFmBV6UjKdiSZkQUW"


@pytest.fixture
def valid_pubkey():
    """Valid Solana public key for testing."""
    return VALID_PUBKEY


@pytest.fixture
def valid_mint():
    """Valid SPL token mint address for testing."""
    return VALID_MINT


@pytest.fixture
def valid_reference():
    """Valid reference public key for testing."""
    return VALID_REFERENCE


@pytest.fixture
def test_signature():
    """Valid transaction signature for testing."""
    return TEST_SIGNATURE


@pytest.fixture
def sample_transfer_request():
    """Sample TransferRequest for testing."""
    from solanapay.models.transfer import TransferRequest
    
    return TransferRequest(
        recipient=VALID_PUBKEY,
        amount=Decimal("0.01"),
        spl_token=None,
        references=[VALID_REFERENCE],
        label="Test Payment",
        message="Test message",
        memo="test-memo"
    )


@pytest.fixture
def sample_spl_transfer_request():
    """Sample SPL token TransferRequest for testing."""
    from solanapay.models.transfer import TransferRequest
    
    return TransferRequest(
        recipient=VALID_PUBKEY,
        amount=Decimal("1.50"),
        spl_token=VALID_MINT,
        references=[VALID_REFERENCE],
        label="USDC Payment",
        message="SPL token payment",
        memo="usdc-memo"
    )


@pytest.fixture
def sample_merchant_config():
    """Sample MerchantConfig for testing."""
    from solanapay.server.schemas import MerchantConfig
    
    return MerchantConfig(
        label="Test Store",
        recipient=VALID_PUBKEY,
        amount=Decimal("0.01"),
        memo="Test purchase"
    )


@pytest.fixture
def mock_rpc_client():
    """Mock RPC client for testing."""
    mock_client = AsyncMock()
    
    # Mock common RPC responses
    mock_client.get_slot.return_value = 12345
    mock_client.get_latest_blockhash.return_value = MagicMock(
        value=MagicMock(blockhash="test_blockhash")
    )
    mock_client.get_token_supply.return_value = MagicMock(
        value=MagicMock(decimals=6, ui_amount=1000000)
    )
    mock_client.get_account_info.return_value = MagicMock(value=None)
    
    return mock_client


@pytest.fixture
def mock_transaction_build_result():
    """Mock TransactionBuildResult for testing."""
    from solanapay.models.transaction import TransactionBuildResult
    
    return TransactionBuildResult(
        transaction="base64_encoded_test_transaction",
        signers_required=[VALID_PUBKEY],
        instructions_count=2,
        estimated_fee=5000
    )


@pytest.fixture
def mock_validation_result():
    """Mock ValidationResult for testing."""
    from solanapay.models.validation import ValidationResult
    
    return ValidationResult(
        is_valid=True,
        recipient_match=True,
        amount_match=True,
        memo_match=True,
        references_match=True,
        confirmation_status="confirmed",
        signature=TEST_SIGNATURE
    )


@pytest.fixture
def sample_urls():
    """Sample URLs for testing."""
    return {
        "sol_minimal": f"solana://{VALID_PUBKEY}",
        "sol_with_amount": f"solana://{VALID_PUBKEY}?amount=0.01",
        "sol_full": f"solana://{VALID_PUBKEY}?amount=0.01&label=Test&memo=test",
        "spl_token": f"solana://{VALID_PUBKEY}?amount=1.5&spl-token={VALID_MINT}",
        "https_discovery": "https://merchant.com/pay?amount=1.0&label=Store"
    }


@pytest.fixture
def test_vectors():
    """Test vectors for comprehensive testing."""
    return {
        "valid_amounts": [
            (Decimal("0.01"), "0.01"),
            (Decimal("1.0"), "1"),
            (Decimal("1.50"), "1.5"),
            (Decimal("0"), "0")
        ],
        "invalid_amounts": [
            "abc", "1.2.3", "", "  ", "-1"
        ],
        "valid_pubkeys": [
            VALID_PUBKEY,
            VALID_MINT,
            VALID_REFERENCE
        ],
        "invalid_pubkeys": [
            "invalid", "too_short", "way_too_long_to_be_valid", ""
        ]
    }


# Pytest configuration
def pytest_configure(config):
    """Configure pytest with custom markers."""
    config.addinivalue_line(
        "markers", "slow: marks tests as slow (deselect with '-m \"not slow\"')"
    )
    config.addinivalue_line(
        "markers", "integration: marks tests as integration tests"
    )
    config.addinivalue_line(
        "markers", "unit: marks tests as unit tests"
    )