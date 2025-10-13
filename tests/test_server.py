"""Tests for server components."""

import pytest
from decimal import Decimal
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch

from solanapay.server.schemas import (
    TransactionRequest,
    TransactionResponse,
    TransactionMetadata,
    MerchantConfig,
    ErrorResponse
)
from solanapay.server.api import TransactionRequestServer, create_app
from solanapay.utils.errors import ValidationError


class TestSchemas:
    """Test Pydantic schemas."""
    
    def test_transaction_request_valid(self):
        """Test valid transaction request."""
        request = TransactionRequest(
            account="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        assert request.account == "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
    
    def test_transaction_request_invalid_account(self):
        """Test transaction request with invalid account."""
        with pytest.raises(ValueError):
            TransactionRequest(account="invalid_account")
    
    def test_transaction_response(self):
        """Test transaction response schema."""
        response = TransactionResponse(
            transaction="base64_encoded_transaction",
            message="Payment processed"
        )
        assert response.transaction == "base64_encoded_transaction"
        assert response.message == "Payment processed"
    
    def test_transaction_metadata(self):
        """Test transaction metadata schema."""
        metadata = TransactionMetadata(
            label="Test Store",
            icon="https://example.com/icon.png"
        )
        assert metadata.label == "Test Store"
        assert metadata.icon == "https://example.com/icon.png"
    
    def test_transaction_metadata_invalid_icon(self):
        """Test transaction metadata with invalid icon URL."""
        with pytest.raises(ValueError, match="Icon must be a valid HTTP/HTTPS URL"):
            TransactionMetadata(
                label="Store",
                icon="invalid_url"
            )
    
    def test_merchant_config_valid(self):
        """Test valid merchant configuration."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("0.01"),
            memo="Test payment"
        )
        assert config.label == "Test Store"
        assert config.amount == Decimal("0.01")
    
    def test_merchant_config_invalid_recipient(self):
        """Test merchant config with invalid recipient."""
        with pytest.raises(ValueError):
            MerchantConfig(
                label="Store",
                recipient="invalid_recipient"
            )
    
    def test_merchant_config_invalid_references(self):
        """Test merchant config with invalid references."""
        with pytest.raises(ValueError):
            MerchantConfig(
                label="Store",
                recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
                references=["invalid_reference"]
            )
    
    def test_error_response(self):
        """Test error response schema."""
        error = ErrorResponse(
            error="Test error",
            code="TEST_ERROR",
            details={"field": "value"}
        )
        assert error.error == "Test error"
        assert error.code == "TEST_ERROR"
        assert error.details["field"] == "value"


class TestTransactionRequestServer:
    """Test TransactionRequestServer class."""
    
    def test_server_initialization(self):
        """Test server initialization."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        server = TransactionRequestServer(
            merchant_config=config,
            cluster="devnet"
        )
        
        assert server.merchant_config.label == "Test Store"
        assert "devnet" in server.rpc_endpoint
    
    def test_server_with_custom_rpc(self):
        """Test server with custom RPC endpoint."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        server = TransactionRequestServer(
            merchant_config=config,
            rpc_endpoint="https://custom.rpc.com"
        )
        
        assert server.rpc_endpoint == "https://custom.rpc.com"
    
    def test_get_app(self):
        """Test getting FastAPI app from server."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        server = TransactionRequestServer(config, cluster="devnet")
        app = server.get_app()
        
        assert app is not None
        assert hasattr(app, 'routes')


class TestAPIEndpoints:
    """Test API endpoints."""
    
    def setup_method(self):
        """Set up test client."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal("0.01")
        )
        
        app = create_app(
            merchant_config=config,
            cluster="devnet",
            enable_middleware=False  # Disable for testing
        )
        
        self.client = TestClient(app)
    
    def test_get_transaction_metadata(self):
        """Test GET /tx endpoint."""
        response = self.client.get("/tx")
        
        assert response.status_code == 200
        data = response.json()
        assert data["label"] == "Test Store"
    
    def test_post_transaction_request(self):
        """Test POST /tx endpoint."""
        with patch('solanapay.server.api.build_transfer_transaction') as mock_build, \
             patch('solanapay.server.api.create_rpc_client') as mock_rpc:
            
            # Mock RPC client
            mock_rpc.return_value.__aenter__ = AsyncMock()
            mock_rpc.return_value.__aexit__ = AsyncMock()
            
            # Mock transaction build result
            mock_result = AsyncMock()
            mock_result.transaction = "base64_encoded_transaction"
            mock_build.return_value = mock_result
            
            response = self.client.post("/tx", json={
                "account": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            })
            
            assert response.status_code == 200
            data = response.json()
            assert data["transaction"] == "base64_encoded_transaction"
            assert "message" in data
    
    def test_post_transaction_invalid_request(self):
        """Test POST /tx with invalid request."""
        response = self.client.post("/tx", json={
            "account": "invalid_account"
        })
        
        assert response.status_code == 422  # Validation error
    
    def test_health_endpoint(self):
        """Test health check endpoint."""
        response = self.client.get("/health")
        
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "timestamp" in data


class TestCreateApp:
    """Test create_app convenience function."""
    
    def test_create_app_basic(self):
        """Test basic app creation."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        app = create_app(merchant_config=config)
        
        assert app is not None
        assert hasattr(app, 'routes')
    
    def test_create_app_with_options(self):
        """Test app creation with options."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        app = create_app(
            merchant_config=config,
            cluster="devnet",
            enable_rate_limiting=True,
            cors_origins=["*"]
        )
        
        assert app is not None
    
    def test_create_app_with_custom_rpc(self):
        """Test app creation with custom RPC endpoint."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        app = create_app(
            merchant_config=config,
            rpc_endpoint="https://custom.rpc.com"
        )
        
        assert app is not None


class TestMiddleware:
    """Test middleware functionality."""
    
    def test_cors_middleware(self):
        """Test CORS middleware."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        app = create_app(
            merchant_config=config,
            cors_origins=["https://example.com"]
        )
        
        client = TestClient(app)
        
        # Test preflight request
        response = client.options("/tx", headers={
            "Origin": "https://example.com",
            "Access-Control-Request-Method": "POST"
        })
        
        assert response.status_code == 200
        assert "Access-Control-Allow-Origin" in response.headers
    
    def test_error_handling_middleware(self):
        """Test error handling middleware."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        app = create_app(merchant_config=config)
        client = TestClient(app)
        
        # Test with invalid JSON
        response = client.post("/tx", data="invalid json")
        
        assert response.status_code == 422


class TestErrorHandling:
    """Test error handling in server components."""
    
    def test_transaction_build_error(self):
        """Test handling of transaction build errors."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        app = create_app(merchant_config=config, enable_middleware=False)
        client = TestClient(app)
        
        with patch('solanapay.server.api.build_transfer_transaction') as mock_build:
            # Mock transaction build error
            from solanapay.utils.errors import TransactionBuildError
            mock_build.side_effect = TransactionBuildError("Build failed")
            
            response = client.post("/tx", json={
                "account": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            })
            
            assert response.status_code == 400
            data = response.json()
            assert "Build failed" in data["detail"]
    
    def test_rpc_error(self):
        """Test handling of RPC errors."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        app = create_app(merchant_config=config, enable_middleware=False)
        client = TestClient(app)
        
        with patch('solanapay.server.api.create_rpc_client') as mock_rpc:
            # Mock RPC error
            from solanapay.utils.errors import RPCError
            mock_rpc.return_value.__aenter__.side_effect = RPCError("RPC failed")
            
            response = client.post("/tx", json={
                "account": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            })
            
            assert response.status_code == 503
            data = response.json()
            assert "temporarily unavailable" in data["detail"]


class TestLegacyCompatibility:
    """Test legacy API compatibility."""
    
    def test_legacy_schemas(self):
        """Test legacy schema aliases."""
        from solanapay.server.schemas import TxGetResp, TxPostReq, TxPostResp
        
        # Test that legacy schemas are available
        assert TxGetResp == TransactionMetadata
        assert TxPostReq == TransactionRequest
        assert TxPostResp == TransactionResponse
    
    def test_legacy_endpoints(self):
        """Test that legacy endpoints still work."""
        config = MerchantConfig(
            label="Test Store",
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        )
        
        app = create_app(merchant_config=config, enable_middleware=False)
        client = TestClient(app)
        
        # Test legacy GET endpoint
        response = client.get("/tx")
        assert response.status_code == 200
        
        # Test legacy POST endpoint
        with patch('solanapay.server.api.build_transfer_transaction') as mock_build, \
             patch('solanapay.server.api.create_rpc_client') as mock_rpc:
            
            mock_rpc.return_value.__aenter__ = AsyncMock()
            mock_rpc.return_value.__aexit__ = AsyncMock()
            
            mock_result = AsyncMock()
            mock_result.transaction = "base64_tx"
            mock_build.return_value = mock_result
            
            response = client.post("/tx", json={
                "account": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
            })
            
            assert response.status_code == 200