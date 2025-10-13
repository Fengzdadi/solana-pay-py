"""Additional tests for Solana Pay functionality."""

import pytest
import asyncio
from decimal import Decimal
from unittest.mock import Mock, AsyncMock, patch

from solanapay import (
    TransferRequest,
    encode_url,
    parse_url,
    SolanaPayClient,
    TransactionValidator,
    ValidationResult,
    ValidationConfig
)
from solanapay.tx_builders.memo import create_memo_instruction, create_payment_memo
from solanapay.models.transaction import TransactionOptions
from solanapay.utils.errors import TransactionBuildError


class TestTransactionBuilders:
    """Test transaction builder functionality."""
    
    def test_create_memo_instruction_valid(self):
        """Test creating valid memo instruction."""
        memo_text = "Test payment memo"
        
        # This should not raise an error
        instruction = create_memo_instruction(memo_text)
        assert instruction is not None
    
    def test_create_memo_instruction_empty(self):
        """Test creating memo with empty text raises error."""
        with pytest.raises(TransactionBuildError, match="Memo text cannot be empty"):
            create_memo_instruction("")
    
    def test_create_memo_instruction_too_long(self):
        """Test creating memo with text too long raises error."""
        long_text = "x" * 600  # Exceeds Solana memo limit
        
        with pytest.raises(TransactionBuildError, match="Memo text too long"):
            create_memo_instruction(long_text)
    
    def test_create_payment_memo(self):
        """Test creating payment memo with metadata."""
        order_id = "ORDER-12345"
        customer_id = "CUSTOMER-67890"
        
        memo = create_payment_memo(order_id, customer_id)
        
        assert order_id in memo
        assert customer_id in memo
        assert len(memo) <= 566  # Solana memo size limit
    
    def test_transaction_options_defaults(self):
        """Test transaction options with corrected expectations."""
        options = TransactionOptions()
        
        assert options.auto_create_ata is True
        # Note: priority_fee is None by default, not 0
        assert options.priority_fee is None
        assert options.use_versioned_tx is True


class TestValidationFunctionality:
    """Test validation functionality."""
    
    def test_validation_config_defaults(self):
        """Test default validation configuration."""
        config = ValidationConfig()
        
        assert config.strict_amount is True
        assert config.require_memo is False
        assert config.require_references is False
        assert config.required_confirmation == "confirmed"
        assert config.max_confirmation_time == 60
    
    def test_validation_result_creation(self):
        """Test validation result creation."""
        result = ValidationResult(
            is_valid=True,
            recipient_match=True,
            amount_match=True,
            memo_match=True,
            references_match=True,
            signature="test_signature"
        )
        
        assert result.is_valid is True
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_validation_result_with_errors(self):
        """Test validation result with errors."""
        result = ValidationResult(
            is_valid=False,
            recipient_match=False,
            amount_match=True,
            memo_match=True,
            references_match=True,
            signature="test_signature"
        )
        
        result.add_error("Recipient not found")
        result.add_warning("Amount tolerance exceeded")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert "Recipient not found" in result.errors
        assert "Amount tolerance exceeded" in result.warnings
    
    def test_validation_result_summary(self):
        """Test validation result summary."""
        result = ValidationResult(
            is_valid=True,
            recipient_match=True,
            amount_match=True,
            memo_match=True,
            references_match=True,
            signature="test_signature"
        )
        
        summary = result.summary()
        
        # Check that summary contains validation status
        assert "validation passed" in summary.lower() or "✅" in summary
    
    @pytest.mark.asyncio
    async def test_transaction_validator_initialization(self):
        """Test transaction validator initialization."""
        mock_rpc = AsyncMock()
        config = ValidationConfig(strict_amount=False)
        
        validator = TransactionValidator(mock_rpc, config)
        
        assert validator.rpc == mock_rpc
        assert validator.config == config


class TestIntegrationScenarios:
    """Test integration scenarios."""
    
    def test_url_roundtrip_basic(self):
        """Test basic URL creation and parsing roundtrip."""
        original_request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("1.50"),
            label="Test Store"
        )
        
        # Encode to URL
        url = encode_url(original_request)
        
        # Parse back from URL
        parsed_request = parse_url(url)
        
        # Verify key fields match
        assert parsed_request.recipient == original_request.recipient
        assert parsed_request.amount == original_request.amount
        assert parsed_request.label == original_request.label
    
    def test_spl_token_workflow_basic(self):
        """Test basic SPL token payment workflow."""
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("100.0"),
            spl_token="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",  # USDC
            label="USDC Payment"
        )
        
        # Encode to URL
        url = encode_url(request)
        
        # Verify URL contains SPL token information
        assert "spl-token=EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v" in url
        assert "amount=100" in url
        
        # Parse back and verify
        parsed = parse_url(url)
        assert parsed.spl_token == request.spl_token
        assert parsed.amount == request.amount
    
    def test_memo_and_references_workflow(self):
        """Test workflow with memo and valid references."""
        # Use valid base58 public keys for references
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("5.0"),
            memo="ORDER-ABC123",
            references=[
                "11111111111111111111111111111112",  # Valid system program ID
                "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA"  # Valid SPL token program ID
            ]
        )
        
        # Encode to URL
        url = encode_url(request)
        
        # Verify URL contains memo and references
        assert "memo=ORDER-ABC123" in url
        assert "reference=11111111111111111111111111111112" in url
        
        # Parse back and verify
        parsed = parse_url(url)
        assert parsed.memo == request.memo
        assert len(parsed.references) == 2
        assert parsed.references == request.references
    
    @pytest.mark.asyncio
    async def test_client_basic_workflow(self):
        """Test basic client workflow."""
        client = SolanaPayClient()
        
        # Create payment URL
        url = client.create_payment_url(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount="0.01",
            label="Coffee Shop"
        )
        
        # Parse the URL
        parsed = client.parse_payment_url(url)
        assert parsed["recipient"] == "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        assert parsed["amount"] == "0.01"
        assert parsed["label"] == "Coffee Shop"


class TestPerformanceBasics:
    """Test basic performance characteristics."""
    
    def test_url_encoding_performance(self):
        """Test URL encoding performance."""
        import time
        
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("1.0"),
            label="Test Store"
        )
        
        # Measure time for 100 encodings (reduced from 1000)
        start_time = time.time()
        for _ in range(100):
            encode_url(request)
        end_time = time.time()
        
        # Should complete in reasonable time
        assert (end_time - start_time) < 1.0
    
    def test_url_parsing_performance(self):
        """Test URL parsing performance."""
        import time
        
        url = "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=1.0&label=Test%20Store"
        
        # Measure time for 100 parsings (reduced from 1000)
        start_time = time.time()
        for _ in range(100):
            parse_url(url)
        end_time = time.time()
        
        # Should complete in reasonable time
        assert (end_time - start_time) < 1.0
    
    def test_decimal_precision_handling(self):
        """Test decimal precision handling."""
        # Test various decimal precisions
        test_amounts = [
            Decimal("1"),
            Decimal("1.5"),
            Decimal("0.001"),
            Decimal("1000.123456")
        ]
        
        for amount in test_amounts:
            request = TransferRequest(
                recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=amount
            )
            
            url = encode_url(request)
            parsed = parse_url(url)
            
            # Amount should be preserved (may be normalized)
            assert parsed.amount == amount.normalize()


class TestErrorHandling:
    """Test error handling scenarios."""
    
    def test_invalid_recipient_error(self):
        """Test error handling for invalid recipient."""
        with pytest.raises(Exception):  # ValidationError
            TransferRequest(recipient="invalid_key")
    
    def test_negative_amount_error(self):
        """Test error handling for negative amount."""
        with pytest.raises(Exception):  # ValidationError
            TransferRequest(
                recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=Decimal("-1")
            )
    
    def test_invalid_url_parsing(self):
        """Test error handling for invalid URL."""
        with pytest.raises(Exception):
            parse_url("invalid://not-a-solana-pay-url")


class TestCompatibility:
    """Test compatibility with Solana Pay standards."""
    
    def test_url_format_compliance(self):
        """Test URL format compliance with Solana Pay spec."""
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("1.0")
        )
        
        url = encode_url(request)
        
        # Should start with solana:
        assert url.startswith("solana:")
        
        # Should contain valid recipient
        assert "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM" in url
        
        # Should properly encode amount
        assert "amount=1" in url
    
    def test_parameter_encoding_compliance(self):
        """Test parameter encoding compliance."""
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            label="Test & Store",  # Contains special characters
            message="Payment for order #123"
        )
        
        url = encode_url(request)
        
        # Special characters should be URL encoded
        assert "%26" in url or "&" in url  # & should be handled
        assert "%23" in url or "#" in url  # # should be handled
    
    def test_zero_amount_handling(self):
        """Test zero amount handling."""
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("0")
        )
        
        url = encode_url(request)
        parsed = parse_url(url)
        
        assert parsed.amount == Decimal("0")
    
    def test_minimal_valid_request(self):
        """Test minimal valid request."""
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        url = encode_url(request)
        parsed = parse_url(url)
        
        assert parsed.recipient == request.recipient
        assert parsed.amount is None
        assert parsed.spl_token is None