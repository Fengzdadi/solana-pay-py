"""Tests for utility functions."""

import pytest
from decimal import Decimal, InvalidOperation
from solanapay.utils.decimal import (
    normalize_amount_str,
    parse_amount,
    decimal_to_u64_units,
    u64_units_to_decimal,
    validate_amount_precision,
    safe_decimal_from_float
)
from solanapay.utils.errors import (
    SolanaPayError,
    ValidationError,
    URLError,
    TransactionBuildError,
    RPCError,
    ErrorContext,
    ErrorCollector
)
from solanapay.utils.url_validation import (
    validate_url_format,
    validate_solana_url_recipient,
    normalize_url,
    is_solana_pay_url
)


class TestDecimalUtils:
    """Test decimal utility functions."""
    
    def test_normalize_amount_str(self):
        """Test amount string normalization."""
        test_cases = [
            (Decimal("1.0000"), "1"),
            (Decimal("0.01000"), "0.01"),
            (Decimal("1.50"), "1.5"),
            (Decimal("0"), "0"),
            (Decimal("123.456"), "123.456"),
            (Decimal("0.000001"), "0.000001")
        ]
        
        for amount, expected in test_cases:
            result = normalize_amount_str(amount)
            assert result == expected
    
    def test_normalize_amount_str_invalid(self):
        """Test normalize_amount_str with invalid input."""
        with pytest.raises(ValidationError, match="Amount must be a Decimal"):
            normalize_amount_str("not_decimal")
        
        with pytest.raises(ValidationError, match="Amount must be non-negative"):
            normalize_amount_str(Decimal("-1"))
    
    def test_parse_amount(self):
        """Test amount parsing."""
        test_cases = [
            ("1.0", Decimal("1.0")),
            ("0.01", Decimal("0.01")),
            ("123.456", Decimal("123.456")),
            ("0", Decimal("0"))
        ]
        
        for amount_str, expected in test_cases:
            result = parse_amount(amount_str)
            assert result == expected
    
    def test_parse_amount_invalid(self):
        """Test parse_amount with invalid input."""
        invalid_amounts = ["", "  ", "abc", "1.2.3", "-1"]
        
        for invalid in invalid_amounts:
            with pytest.raises(ValidationError):
                parse_amount(invalid)
    
    def test_decimal_to_u64_units(self):
        """Test decimal to u64 units conversion."""
        test_cases = [
            (Decimal("1.0"), 9, 1_000_000_000),  # 1 SOL
            (Decimal("0.01"), 9, 10_000_000),    # 0.01 SOL
            (Decimal("1.5"), 6, 1_500_000),      # 1.5 USDC
            (Decimal("0"), 9, 0)                 # 0 SOL
        ]
        
        for amount, decimals, expected in test_cases:
            result = decimal_to_u64_units(amount, decimals)
            assert result == expected
    
    def test_decimal_to_u64_units_invalid(self):
        """Test decimal_to_u64_units with invalid input."""
        with pytest.raises(ValidationError, match="Amount must be a Decimal"):
            decimal_to_u64_units("1.0", 9)
        
        with pytest.raises(ValidationError, match="Decimals must be an integer"):
            decimal_to_u64_units(Decimal("1.0"), "9")
        
        with pytest.raises(ValidationError, match="Amount must be non-negative"):
            decimal_to_u64_units(Decimal("-1"), 9)
    
    def test_u64_units_to_decimal(self):
        """Test u64 units to decimal conversion."""
        test_cases = [
            (1_000_000_000, 9, Decimal("1.0")),    # 1 SOL
            (10_000_000, 9, Decimal("0.01")),      # 0.01 SOL
            (1_500_000, 6, Decimal("1.5")),        # 1.5 USDC
            (0, 9, Decimal("0"))                   # 0 SOL
        ]
        
        for units, decimals, expected in test_cases:
            result = u64_units_to_decimal(units, decimals)
            assert result == expected
    
    def test_validate_amount_precision(self):
        """Test amount precision validation."""
        # Valid cases
        validate_amount_precision(Decimal("1.123456"), 6)  # Should not raise
        validate_amount_precision(Decimal("1.0"), 9)       # Should not raise
        
        # Invalid case
        with pytest.raises(ValidationError, match="too many decimal places"):
            validate_amount_precision(Decimal("1.1234567"), 6)
    
    def test_safe_decimal_from_float(self):
        """Test safe decimal conversion from various types."""
        test_cases = [
            (1, Decimal("1")),
            (1.5, Decimal("1.5")),
            ("1.5", Decimal("1.5")),
            (Decimal("1.5"), Decimal("1.5"))
        ]
        
        for value, expected in test_cases:
            result = safe_decimal_from_float(value)
            assert result == expected
        
        # Invalid case
        with pytest.raises(ValidationError):
            safe_decimal_from_float(object())


class TestErrorHandling:
    """Test error handling utilities."""
    
    def test_solana_pay_error(self):
        """Test base SolanaPayError."""
        error = SolanaPayError(
            "Test error",
            error_code="TEST_ERROR",
            context={"key": "value"}
        )
        
        assert str(error) == "[TEST_ERROR] Test error"
        assert error.error_code == "TEST_ERROR"
        assert error.context["key"] == "value"
        
        error.add_context("new_key", "new_value")
        assert error.context["new_key"] == "new_value"
    
    def test_validation_error(self):
        """Test ValidationError with field context."""
        error = ValidationError(
            "Invalid field",
            field="amount",
            value="invalid"
        )
        
        assert error.error_code == "VALIDATION_ERROR"
        assert error.context["field"] == "amount"
        assert error.context["value"] == "invalid"
    
    def test_url_error(self):
        """Test URLError with URL context."""
        error = URLError(
            "Invalid URL",
            url="invalid://url"
        )
        
        assert error.error_code == "URL_ERROR"
        assert error.context["url"] == "invalid://url"
    
    def test_error_context_manager(self):
        """Test ErrorContext context manager."""
        with pytest.raises(ValidationError) as exc_info:
            with ErrorContext("test_operation", user_id="123"):
                raise ValueError("Original error")
        
        error = exc_info.value
        assert "test_operation" in error.message
        assert error.context["operation"] == "test_operation"
        assert error.context["user_id"] == "123"
    
    def test_error_collector(self):
        """Test ErrorCollector utility."""
        collector = ErrorCollector()
        
        assert not collector.has_errors()
        assert not collector.has_warnings()
        
        collector.add_error("Error 1")
        collector.add_error(ValidationError("Error 2"))
        collector.add_warning("Warning 1")
        
        assert collector.has_errors()
        assert collector.has_warnings()
        
        summary = collector.get_summary()
        assert "Error 1" in summary
        assert "Error 2" in summary
        assert "Warning 1" in summary
        
        # Test raising combined error
        with pytest.raises(SolanaPayError, match="Multiple errors occurred"):
            collector.raise_if_errors()


class TestURLValidation:
    """Test URL validation utilities."""
    
    def test_validate_url_format_valid(self):
        """Test valid URL format validation."""
        valid_urls = [
            "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01",
            "https://merchant.com/pay?amount=1.0"
        ]
        
        for url in valid_urls:
            is_valid, error = validate_url_format(url)
            assert is_valid, f"URL should be valid: {url}, error: {error}"
    
    def test_validate_url_format_invalid(self):
        """Test invalid URL format validation."""
        invalid_urls = [
            ("", "URL cannot be empty"),
            ("bitcoin:address", "Unsupported URL scheme: bitcoin"),
            ("solana:", "solana: URL must contain a recipient"),
            ("https://", "https: URL must contain a domain")
        ]
        
        for url, expected_error in invalid_urls:
            is_valid, error = validate_url_format(url)
            assert not is_valid
            assert expected_error in error
    
    def test_validate_solana_url_recipient(self):
        """Test Solana URL recipient validation."""
        valid_recipients = [
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "11111111111111111111111111111112"
        ]
        
        for recipient in valid_recipients:
            assert validate_solana_url_recipient(recipient)
        
        invalid_recipients = [
            "invalid",
            "too_short",
            "way_too_long_to_be_a_valid_solana_public_key_address",
            "contains_invalid_chars_0OIl"
        ]
        
        for recipient in invalid_recipients:
            assert not validate_solana_url_recipient(recipient)
    
    def test_normalize_url(self):
        """Test URL normalization."""
        test_cases = [
            ("  solana:9Wz...  ", "solana:9Wz..."),
            ("SOLANA:9Wz...", "solana:9Wz..."),
            ("HTTPS://example.com", "https://example.com")
        ]
        
        for original, expected in test_cases:
            result = normalize_url(original)
            assert result == expected
    
    def test_is_solana_pay_url(self):
        """Test Solana Pay URL detection."""
        solana_pay_urls = [
            "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            "https://merchant.com/pay"
        ]
        
        for url in solana_pay_urls:
            assert is_solana_pay_url(url)
        
        non_solana_pay_urls = [
            "bitcoin:address",
            "mailto:test@example.com",
            "ftp://files.example.com"
        ]
        
        for url in non_solana_pay_urls:
            assert not is_solana_pay_url(url)


class TestErrorDecorators:
    """Test error handling decorators."""
    
    def test_error_handler_decorator(self):
        """Test error_handler decorator."""
        from solanapay.utils.errors import error_handler
        
        @error_handler("test_operation", error_mapping={ValueError: ValidationError})
        def test_function():
            raise ValueError("Test error")
        
        with pytest.raises(ValidationError) as exc_info:
            test_function()
        
        error = exc_info.value
        assert "test_operation" in error.message
        assert "Test error" in error.message
    
    def test_async_error_handler_decorator(self):
        """Test error_handler decorator with async function."""
        from solanapay.utils.errors import error_handler
        
        @error_handler("async_operation")
        async def async_test_function():
            raise ValueError("Async test error")
        
        async def run_test():
            with pytest.raises(SolanaPayError) as exc_info:
                await async_test_function()
            
            error = exc_info.value
            assert "async_operation" in error.message
        
        import asyncio
        asyncio.run(run_test())


class TestUtilityFunctions:
    """Test miscellaneous utility functions."""
    
    def test_format_error_for_logging(self):
        """Test error formatting for logging."""
        from solanapay.utils.errors import format_error_for_logging
        
        error = ValidationError(
            "Test validation error",
            field="amount",
            value="invalid"
        )
        
        formatted = format_error_for_logging(error)
        
        assert "ValidationError" in formatted
        assert "Test validation error" in formatted
        assert "VALIDATION_ERROR" in formatted
        assert "amount" in formatted
        assert "invalid" in formatted
    
    def test_create_error_report(self):
        """Test error report creation."""
        from solanapay.utils.errors import create_error_report
        
        error = ValidationError("Test error")
        report = create_error_report(
            operation="test_op",
            inputs={"key": "value"},
            error=error,
            context={"user": "test"}
        )
        
        assert report["operation"] == "test_op"
        assert report["inputs"]["key"] == "value"
        assert report["success"] is False
        assert report["error"]["type"] == "ValidationError"
        assert report["context"]["user"] == "test"