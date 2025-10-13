"""Tests for high-level convenience functions."""

import pytest
from decimal import Decimal
from unittest.mock import AsyncMock, patch
from solanapay.convenience import (
    create_payment_url,
    parse_payment_url,
    create_payment_transaction,
    verify_payment,
    SolanaPayClient
)
from solanapay.utils.errors import URLError, ValidationError


class TestConvenienceFunctions:
    """Test high-level convenience functions."""
    
    def test_create_payment_url_minimal(self):
        """Test creating minimal payment URL."""
        url = create_payment_url(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        assert url.startswith("solana://9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
        assert "amount=" not in url
    
    def test_create_payment_url_full(self):
        """Test creating full payment URL."""
        url = create_payment_url(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount="0.01",
            token="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            label="Test Store",
            message="Test payment",
            memo="test-memo",
            references=["11111111111111111111111111111112"]
        )
        
        assert "amount=0.01" in url
        assert "spl-token=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" in url
        assert "label=Test%20Store" in url
        assert "reference=11111111111111111111111111111112" in url
    
    def test_create_payment_url_invalid_amount(self):
        """Test creating payment URL with invalid amount."""
        with pytest.raises(URLError):
            create_payment_url(
                recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount="invalid"
            )
    
    def test_parse_payment_url(self):
        """Test parsing payment URL."""
        url = "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01&label=Test"
        result = parse_payment_url(url)
        
        assert result["recipient"] == "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        assert result["amount"] == "0.01"
        assert result["label"] == "Test"
        assert result["token"] is None
    
    def test_parse_payment_url_with_token(self):
        """Test parsing payment URL with SPL token."""
        url = ("solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
               "?amount=1.5&spl-token=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v")
        result = parse_payment_url(url)
        
        assert result["amount"] == "1.5"
        assert result["token"] == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
    
    @pytest.mark.asyncio
    async def test_create_payment_transaction(self):
        """Test creating payment transaction."""
        with patch('solanapay.convenience.create_rpc_client') as mock_rpc, \
             patch('solanapay.convenience.build_transfer_transaction') as mock_build:
            
            # Mock RPC client
            mock_rpc.return_value.__aenter__ = AsyncMock()
            mock_rpc.return_value.__aexit__ = AsyncMock()
            
            # Mock transaction build result
            mock_result = AsyncMock()
            mock_result.transaction = "base64_encoded_transaction"
            mock_build.return_value = mock_result
            
            transaction = await create_payment_transaction(
                payer="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                recipient="DL7GeJGi1BvX2QNSQ3Ceav25thDgo4EAYQX2x1ZVxJVr",
                amount="0.01"
            )
            
            assert transaction == "base64_encoded_transaction"
            mock_build.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_verify_payment(self):
        """Test payment verification."""
        with patch('solanapay.convenience.create_rpc_client') as mock_rpc, \
             patch('solanapay.convenience.wait_and_verify') as mock_verify:
            
            # Mock RPC client
            mock_rpc.return_value.__aenter__ = AsyncMock()
            mock_rpc.return_value.__aexit__ = AsyncMock()
            
            # Mock validation result
            mock_result = AsyncMock()
            mock_result.is_valid = True
            mock_result.recipient_match = True
            mock_result.amount_match = True
            mock_result.memo_match = True
            mock_result.references_match = True
            mock_result.confirmation_status = "confirmed"
            mock_result.errors = []
            mock_result.warnings = []
            mock_result.signature = "1111111111111111111111111111111111111111111111111111111111111111"
            mock_verify.return_value = mock_result
            
            result = await verify_payment(
                signature="1111111111111111111111111111111111111111111111111111111111111111",
                expected_recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                expected_amount="0.01"
            )
            
            assert result["is_valid"] is True
            assert result["confirmation_status"] == "confirmed"
            assert result["signature"] == "1111111111111111111111111111111111111111111111111111111111111111"


class TestSolanaPayClient:
    """Test SolanaPayClient high-level interface."""
    
    def test_client_initialization(self):
        """Test client initialization."""
        client = SolanaPayClient()
        assert client.rpc_endpoint is not None
        
        custom_client = SolanaPayClient(rpc_endpoint="https://custom.rpc.com")
        assert custom_client.rpc_endpoint == "https://custom.rpc.com"
    
    def test_client_create_payment_url(self):
        """Test client payment URL creation."""
        client = SolanaPayClient()
        url = client.create_payment_url(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount="0.01",
            label="Test"
        )
        
        assert "solana:" in url
        assert "amount=0.01" in url
        assert "label=Test" in url
    
    def test_client_parse_payment_url(self):
        """Test client payment URL parsing."""
        client = SolanaPayClient()
        url = "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01"
        result = client.parse_payment_url(url)
        
        assert result["recipient"] == "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        assert result["amount"] == "0.01"
    
    @pytest.mark.asyncio
    async def test_client_create_transaction(self):
        """Test client transaction creation."""
        client = SolanaPayClient()
        
        with patch('solanapay.convenience.create_payment_transaction') as mock_create:
            mock_create.return_value = "base64_transaction"
            
            transaction = await client.create_transaction(
                payer="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                recipient="DL7GeJGi1BvX2QNSQ3Ceav25thDgo4EAYQX2x1ZVxJVr",
                amount="0.01"
            )
            
            assert transaction == "base64_transaction"
            mock_create.assert_called_once_with(
                "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                "DL7GeJGi1BvX2QNSQ3Ceav25thDgo4EAYQX2x1ZVxJVr", 
                "0.01",
                rpc_endpoint=client.rpc_endpoint
            )
    
    @pytest.mark.asyncio
    async def test_client_verify_payment(self):
        """Test client payment verification."""
        client = SolanaPayClient()
        
        with patch('solanapay.convenience.verify_payment') as mock_verify:
            mock_verify.return_value = {"is_valid": True}
            
            result = await client.verify_payment(
                signature="1111111111111111111111111111111111111111111111111111111111111111",
                expected_recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                expected_amount="0.01"
            )
            
            assert result["is_valid"] is True
            mock_verify.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_client_get_transaction_status(self):
        """Test client transaction status checking."""
        client = SolanaPayClient()
        
        with patch('solanapay.convenience.create_rpc_client') as mock_rpc:
            # Mock RPC client and response
            mock_client = AsyncMock()
            mock_rpc.return_value.__aenter__.return_value = mock_client
            mock_rpc.return_value.__aexit__ = AsyncMock()
            
            # Mock signature status response
            mock_status = AsyncMock()
            mock_status.confirmation_status = "confirmed"
            mock_status.slot = 12345
            mock_status.err = None
            
            mock_response = AsyncMock()
            mock_response.value = [mock_status]
            mock_client.get_signature_statuses.return_value = mock_response
            
            result = await client.get_transaction_status("1111111111111111111111111111111111111111111111111111111111111111")
            
            assert result["exists"] is True
            assert result["confirmed"] is True
            assert result["confirmation_status"] == "confirmed"
            assert result["slot"] == 12345
            assert result["error"] is None
    
    @pytest.mark.asyncio
    async def test_client_get_transaction_status_not_found(self):
        """Test client transaction status for non-existent transaction."""
        client = SolanaPayClient()
        
        with patch('solanapay.convenience.create_rpc_client') as mock_rpc:
            # Mock RPC client
            mock_client = AsyncMock()
            mock_rpc.return_value.__aenter__.return_value = mock_client
            mock_rpc.return_value.__aexit__ = AsyncMock()
            
            # Mock empty response (transaction not found)
            mock_response = AsyncMock()
            mock_response.value = [None]
            mock_client.get_signature_statuses.return_value = mock_response
            
            result = await client.get_transaction_status("2222222222222222222222222222222222222222222222222222222222222222")
            
            assert result["exists"] is False
            assert result["confirmed"] is False
            assert result["confirmation_status"] is None


class TestRoundTripOperations:
    """Test round-trip operations using convenience functions."""
    
    def test_url_creation_and_parsing_roundtrip(self):
        """Test creating and parsing URLs maintains data integrity."""
        original_data = {
            "recipient": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "amount": "1.50",
            "token": "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            "label": "Test Store ☕",
            "message": "Thanks for your purchase!",
            "memo": "order-123",
            "references": ["11111111111111111111111111111112"]
        }
        
        # Create URL
        url = create_payment_url(**original_data)
        
        # Parse URL
        parsed_data = parse_payment_url(url)
        
        # Verify data integrity
        assert parsed_data["recipient"] == original_data["recipient"]
        # Compare decimal values (normalization is expected: "1.50" -> "1.5")
        from decimal import Decimal
        assert Decimal(parsed_data["amount"]) == Decimal(original_data["amount"])
        assert parsed_data["token"] == original_data["token"]
        assert parsed_data["label"] == original_data["label"]
        assert parsed_data["message"] == original_data["message"]
        assert parsed_data["memo"] == original_data["memo"]
        assert parsed_data["references"] == original_data["references"]
    
    def test_client_roundtrip_operations(self):
        """Test client round-trip operations."""
        client = SolanaPayClient()
        
        # Create URL
        url = client.create_payment_url(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount="0.01",
            label="Client Test"
        )
        
        # Parse URL
        parsed = client.parse_payment_url(url)
        
        # Verify
        assert parsed["recipient"] == "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        assert parsed["amount"] == "0.01"
        assert parsed["label"] == "Client Test"


class TestErrorHandling:
    """Test error handling in convenience functions."""
    
    def test_create_payment_url_validation_error(self):
        """Test validation error in payment URL creation."""
        with pytest.raises(URLError):
            create_payment_url(
                recipient="invalid_recipient",
                amount="0.01"
            )
    
    def test_parse_payment_url_invalid_url(self):
        """Test parsing invalid URL."""
        with pytest.raises(URLError):
            parse_payment_url("invalid://url")
    
    @pytest.mark.asyncio
    async def test_create_transaction_error_handling(self):
        """Test error handling in transaction creation."""
        with patch('solanapay.convenience.create_rpc_client') as mock_rpc:
            # Mock RPC client that raises an error
            mock_rpc.return_value.__aenter__.side_effect = Exception("RPC Error")
            
            with pytest.raises(Exception, match="RPC Error"):
                await create_payment_transaction(
                    payer="DL7GeJGi1BvX2QNSQ3Ceav25thDgo4EAYQX2x1ZVxJVr",
                    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM", 
                    amount="0.01"
                )
    
    @pytest.mark.asyncio
    async def test_verify_payment_error_handling(self):
        """Test error handling in payment verification."""
        with patch('solanapay.convenience.create_rpc_client') as mock_rpc:
            # Mock RPC client that raises an error
            mock_rpc.return_value.__aenter__.side_effect = Exception("Verification Error")
            
            with pytest.raises(Exception, match="Verification Error"):
                await verify_payment(
                    signature="signature",
                    expected_recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                    expected_amount="0.01"
                )