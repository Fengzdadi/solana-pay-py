"""Tests for data models and validation."""

import pytest
from decimal import Decimal
from solanapay.models.transfer import TransferRequest
from solanapay.models.transaction import TransactionBuildResult, TransactionOptions, TransactionMetadata
from solanapay.models.validation import ValidationResult, ValidationConfig
from solanapay.utils.errors import ValidationError


class TestTransferRequest:
    """Test TransferRequest model."""
    
    def test_valid_minimal_request(self):
        """Test creating minimal valid request."""
        request = TransferRequest(recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")
        assert request.recipient == "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        assert request.amount is None
        assert request.spl_token is None
    
    def test_valid_full_request(self):
        """Test creating full valid request."""
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("1.50"),
            spl_token="EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v",
            references=["11111111111111111111111111111112"],
            label="Test Store",
            message="Test payment",
            memo="test-memo"
        )
        assert request.amount == Decimal("1.50")
        assert request.spl_token == "EPjFWdd5AufqSSqeM2qN1xzybapC8G4wEGGkZwyTDt1v"
        assert len(request.references) == 1
    
    def test_empty_recipient(self):
        """Test empty recipient validation."""
        with pytest.raises(ValidationError, match="recipient is required"):
            TransferRequest(recipient="")
    
    def test_invalid_recipient_format(self):
        """Test invalid recipient format."""
        with pytest.raises(ValidationError, match="recipient must be a valid base58 public key"):
            TransferRequest(recipient="invalid_key_format")
    
    def test_negative_amount(self):
        """Test negative amount validation."""
        with pytest.raises(ValidationError, match="amount must be non-negative"):
            TransferRequest(
                recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                amount=Decimal("-1.0")
            )
    
    def test_invalid_spl_token(self):
        """Test invalid SPL token validation."""
        with pytest.raises(ValidationError, match="spl_token must be a valid base58 public key"):
            TransferRequest(
                recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                spl_token="invalid_token"
            )
    
    def test_invalid_references_type(self):
        """Test invalid references type."""
        with pytest.raises(ValidationError, match="references must be a list"):
            TransferRequest(
                recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                references="not_a_list"
            )
    
    def test_invalid_reference_format(self):
        """Test invalid reference format."""
        with pytest.raises(ValidationError, match="reference.*must be a valid base58 public key"):
            TransferRequest(
                recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                references=["invalid_ref"]
            )
    
    def test_to_dict(self):
        """Test converting to dictionary."""
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("1.50"),
            label="Test"
        )
        data = request.to_dict()
        
        assert data["recipient"] == request.recipient
        assert data["amount"] == "1.50"
        assert data["label"] == "Test"
        assert "spl_token" not in data  # None values excluded
    
    def test_from_dict(self):
        """Test creating from dictionary."""
        data = {
            "recipient": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "amount": "1.50",
            "label": "Test"
        }
        request = TransferRequest.from_dict(data)
        
        assert request.recipient == data["recipient"]
        assert request.amount == Decimal("1.50")
        assert request.label == "Test"
    
    def test_string_representation(self):
        """Test string representation."""
        request = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("1.50")
        )
        str_repr = str(request)
        
        assert "TransferRequest" in str_repr
        assert "recipient=" in str_repr
        assert "amount=1.50" in str_repr


class TestTransactionOptions:
    """Test TransactionOptions model."""
    
    def test_default_options(self):
        """Test default transaction options."""
        options = TransactionOptions()
        
        assert options.priority_fee is None
        assert options.auto_create_ata is True
        assert options.use_versioned_tx is True
        assert options.max_retries == 3
        assert options.timeout == 30
    
    def test_custom_options(self):
        """Test custom transaction options."""
        options = TransactionOptions(
            priority_fee=5000,
            auto_create_ata=False,
            compute_unit_limit=200_000,
            max_retries=5,
            timeout=60
        )
        
        assert options.priority_fee == 5000
        assert options.auto_create_ata is False
        assert options.compute_unit_limit == 200_000
        assert options.max_retries == 5
        assert options.timeout == 60
    
    def test_invalid_priority_fee(self):
        """Test invalid priority fee validation."""
        with pytest.raises(ValueError, match="priority_fee must be a non-negative integer"):
            TransactionOptions(priority_fee=-1000)
    
    def test_invalid_compute_unit_limit(self):
        """Test invalid compute unit limit validation."""
        with pytest.raises(ValueError, match="compute_unit_limit must be a positive integer"):
            TransactionOptions(compute_unit_limit=0)
    
    def test_invalid_timeout(self):
        """Test invalid timeout validation."""
        with pytest.raises(ValueError, match="timeout must be a positive integer"):
            TransactionOptions(timeout=0)


class TestTransactionBuildResult:
    """Test TransactionBuildResult model."""
    
    def test_valid_result(self):
        """Test creating valid transaction build result."""
        result = TransactionBuildResult(
            transaction="base64_encoded_transaction",
            signers_required=["signer1", "signer2"],
            instructions_count=3,
            estimated_fee=5000
        )
        
        assert result.transaction == "base64_encoded_transaction"
        assert len(result.signers_required) == 2
        assert result.instructions_count == 3
        assert result.estimated_fee == 5000
        assert result.uses_lookup_tables is False
    
    def test_invalid_transaction(self):
        """Test invalid transaction validation."""
        with pytest.raises(ValueError, match="transaction must be a base64 encoded string"):
            TransactionBuildResult(
                transaction=123,  # Not a string
                signers_required=[],
                instructions_count=1,
                estimated_fee=5000
            )
    
    def test_invalid_signers(self):
        """Test invalid signers validation."""
        with pytest.raises(ValueError, match="signers_required must be a list"):
            TransactionBuildResult(
                transaction="tx",
                signers_required="not_a_list",
                instructions_count=1,
                estimated_fee=5000
            )
    
    def test_negative_instructions_count(self):
        """Test negative instructions count validation."""
        with pytest.raises(ValueError, match="instructions_count must be a non-negative integer"):
            TransactionBuildResult(
                transaction="tx",
                signers_required=[],
                instructions_count=-1,
                estimated_fee=5000
            )


class TestTransactionMetadata:
    """Test TransactionMetadata model."""
    
    def test_valid_metadata(self):
        """Test creating valid transaction metadata."""
        metadata = TransactionMetadata(
            label="My Store",
            icon="https://example.com/icon.png"
        )
        
        assert metadata.label == "My Store"
        assert metadata.icon == "https://example.com/icon.png"
    
    def test_metadata_without_icon(self):
        """Test metadata without icon."""
        metadata = TransactionMetadata(label="My Store")
        
        assert metadata.label == "My Store"
        assert metadata.icon is None
    
    def test_empty_label(self):
        """Test empty label validation."""
        with pytest.raises(ValueError, match="label must be a non-empty string"):
            TransactionMetadata(label="")
    
    def test_invalid_icon_url(self):
        """Test invalid icon URL validation."""
        with pytest.raises(ValueError, match="Icon must be a valid HTTP/HTTPS URL"):
            TransactionMetadata(
                label="Store",
                icon="invalid_url"
            )


class TestValidationResult:
    """Test ValidationResult model."""
    
    def test_valid_result(self):
        """Test creating valid validation result."""
        result = ValidationResult(
            is_valid=True,
            recipient_match=True,
            amount_match=True,
            memo_match=True,
            references_match=True,
            signature="test_signature"
        )
        
        assert result.is_valid is True
        assert result.signature == "test_signature"
        assert len(result.errors) == 0
        assert len(result.warnings) == 0
    
    def test_failed_validation(self):
        """Test failed validation result."""
        result = ValidationResult(
            is_valid=False,
            recipient_match=False,
            amount_match=True,
            memo_match=True,
            references_match=True
        )
        
        result.add_error("Recipient mismatch")
        result.add_warning("Minor issue detected")
        
        assert result.is_valid is False
        assert len(result.errors) == 1
        assert len(result.warnings) == 1
        assert "Recipient mismatch" in result.errors
    
    def test_invalid_confirmation_status(self):
        """Test invalid confirmation status validation."""
        with pytest.raises(ValueError, match="confirmation_status must be one of"):
            ValidationResult(
                is_valid=True,
                recipient_match=True,
                amount_match=True,
                memo_match=True,
                references_match=True,
                confirmation_status="invalid_status"
            )
    
    def test_summary(self):
        """Test validation result summary."""
        result = ValidationResult(
            is_valid=True,
            recipient_match=True,
            amount_match=True,
            memo_match=True,
            references_match=True,
            confirmation_status="confirmed"
        )
        
        summary = result.summary()
        assert "✅" in summary
        assert "confirmed" in summary
    
    def test_detailed_report(self):
        """Test detailed validation report."""
        result = ValidationResult(
            is_valid=False,
            recipient_match=True,
            amount_match=False,
            memo_match=True,
            references_match=True,
            signature="test_sig"
        )
        result.add_error("Amount mismatch")
        result.add_warning("Minor issue")
        
        report = result.detailed_report()
        
        assert "test_sig" in report
        assert "Amount mismatch" in report
        assert "Minor issue" in report
        assert "✅ Recipient" in report
        assert "❌ Amount" in report


class TestValidationConfig:
    """Test ValidationConfig model."""
    
    def test_default_config(self):
        """Test default validation configuration."""
        config = ValidationConfig()
        
        assert config.strict_amount is True
        assert config.require_memo is False
        assert config.max_confirmation_time == 60
        assert config.required_confirmation == "confirmed"
    
    def test_custom_config(self):
        """Test custom validation configuration."""
        config = ValidationConfig(
            strict_amount=False,
            require_memo=True,
            max_confirmation_time=120,
            required_confirmation="finalized"
        )
        
        assert config.strict_amount is False
        assert config.require_memo is True
        assert config.max_confirmation_time == 120
        assert config.required_confirmation == "finalized"
    
    def test_invalid_confirmation_level(self):
        """Test invalid confirmation level validation."""
        with pytest.raises(ValueError, match="required_confirmation must be one of"):
            ValidationConfig(required_confirmation="invalid")
    
    def test_invalid_timeout(self):
        """Test invalid timeout validation."""
        with pytest.raises(ValueError, match="max_confirmation_time must be a positive integer"):
            ValidationConfig(max_confirmation_time=0)