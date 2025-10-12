"""Enhanced FastAPI server for Solana Pay transaction requests."""

from __future__ import annotations

import logging
from typing import Optional

from fastapi import FastAPI, HTTPException, Depends
from fastapi.responses import JSONResponse

from .schemas import (
    TransactionRequest,
    TransactionResponse, 
    TransactionMetadata,
    MerchantConfig,
    ErrorResponse,
    # Legacy schemas for backward compatibility
    TxGetResp,
    TxPostReq, 
    TxPostResp
)
from .middleware import setup_middleware, create_health_check_endpoint
from ..models.transfer import TransferRequest
from ..models.transaction import TransactionOptions
from ..tx_builders.transfer import build_transfer_transaction
from ..utils.rpc import create_rpc_client
from ..utils.errors import SolanaPayError, TransactionBuildError, RPCError
from ..config import get_settings

logger = logging.getLogger(__name__)


class TransactionRequestServer:
    """Enhanced transaction request server for Solana Pay.
    
    This class provides a complete FastAPI-based server implementation
    for handling Solana Pay transaction requests with proper error handling,
    middleware, and configuration management.
    """
    
    def __init__(
        self,
        merchant_config: MerchantConfig,
        rpc_endpoint: Optional[str] = None,
        cluster: Optional[str] = None,
        enable_middleware: bool = True,
        **middleware_kwargs
    ):
        """Initialize the transaction request server.
        
        Args:
            merchant_config: Merchant configuration
            rpc_endpoint: Custom RPC endpoint (overrides cluster)
            cluster: Solana cluster name (devnet, testnet, mainnet)
            enable_middleware: Whether to enable middleware
            **middleware_kwargs: Additional middleware configuration
        """
        self.merchant_config = merchant_config
        self.settings = get_settings()
        
        # Determine RPC endpoint
        if rpc_endpoint:
            self.rpc_endpoint = rpc_endpoint
        elif cluster:
            self.rpc_endpoint = self.settings.get_cluster_endpoint(cluster)
        else:
            self.rpc_endpoint = self.settings.get_cluster_endpoint()
        
        # Create FastAPI app
        self.app = FastAPI(
            title="Solana Pay Transaction Request Server",
            description="Server for handling Solana Pay transaction requests",
            version="1.0.0"
        )
        
        # Set up middleware
        if enable_middleware:
            setup_middleware(self.app, **middleware_kwargs)
        
        # Add health check
        create_health_check_endpoint(self.app)
        
        # Set up routes
        self._setup_routes()
        
        logger.info(f"Transaction request server initialized for {merchant_config.label}")

    def _setup_routes(self):
        """Set up API routes."""
        
        @self.app.get(
            "/tx",
            response_model=TransactionMetadata,
            summary="Get transaction metadata",
            description="Returns metadata about the merchant and transaction request"
        )
        async def get_transaction_metadata() -> TransactionMetadata:
            """Get transaction metadata for the merchant."""
            try:
                return TransactionMetadata(
                    label=self.merchant_config.label,
                    icon=self.merchant_config.icon
                )
            except Exception as e:
                logger.error(f"Failed to get transaction metadata: {e}")
                raise HTTPException(status_code=500, detail="Internal server error")

        @self.app.post(
            "/tx",
            response_model=TransactionResponse,
            summary="Create transaction",
            description="Creates a transaction for the wallet to sign and submit"
        )
        async def create_transaction(
            request: TransactionRequest
        ) -> TransactionResponse:
            """Create a transaction for the wallet."""
            try:
                # Create transfer request from merchant config and wallet request
                transfer_request = TransferRequest(
                    recipient=self.merchant_config.recipient,
                    amount=self.merchant_config.amount,
                    spl_token=self.merchant_config.spl_token,
                    memo=self.merchant_config.memo,
                    references=self.merchant_config.references,
                    label=self.merchant_config.label
                )
                
                # Create transaction options
                options = TransactionOptions(
                    auto_create_ata=True,
                    use_versioned_tx=True
                )
                
                # Build transaction
                async with create_rpc_client(
                    self.rpc_endpoint,
                    commitment=self.settings.default_commitment,
                    timeout=self.settings.default_timeout,
                    max_retries=self.settings.max_retries
                ) as rpc:
                    result = await build_transfer_transaction(
                        rpc=rpc,
                        payer=request.account,
                        request=transfer_request,
                        options=options
                    )
                    
                    logger.info(
                        f"Created transaction for {request.account} -> {transfer_request.recipient}"
                    )
                    
                    return TransactionResponse(
                        transaction=result.transaction,
                        message=f"Payment to {self.merchant_config.label}"
                    )
                
            except TransactionBuildError as e:
                logger.error(f"Transaction build error: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=f"Failed to build transaction: {e.message}"
                )
                
            except RPCError as e:
                logger.error(f"RPC error: {e}")
                raise HTTPException(
                    status_code=503,
                    detail="Blockchain service temporarily unavailable"
                )
                
            except SolanaPayError as e:
                logger.error(f"Solana Pay error: {e}")
                raise HTTPException(
                    status_code=400,
                    detail=e.message
                )
                
            except Exception as e:
                logger.exception(f"Unexpected error creating transaction: {e}")
                raise HTTPException(
                    status_code=500,
                    detail="Internal server error"
                )

        # Legacy endpoints for backward compatibility
        @self.app.get("/tx", response_model=TxGetResp, include_in_schema=False)
        async def get_tx_meta_legacy() -> TxGetResp:
            """Legacy endpoint for backward compatibility."""
            metadata = await get_transaction_metadata()
            return TxGetResp(label=metadata.label, icon=metadata.icon)

        @self.app.post("/tx", response_model=TxPostResp, include_in_schema=False)
        async def post_tx_legacy(req: TxPostReq) -> TxPostResp:
            """Legacy endpoint for backward compatibility."""
            transaction_req = TransactionRequest(account=req.account)
            response = await create_transaction(transaction_req)
            return TxPostResp(transaction=response.transaction, message=response.message)

    def get_app(self) -> FastAPI:
        """Get the FastAPI application instance.
        
        Returns:
            FastAPI application
        """
        return self.app


def create_app(
    merchant_config: MerchantConfig,
    rpc_endpoint: Optional[str] = None,
    cluster: Optional[str] = None,
    **kwargs
) -> FastAPI:
    """Create a FastAPI application for transaction requests.
    
    This is a convenience function for creating a transaction request server.
    
    Args:
        merchant_config: Merchant configuration
        rpc_endpoint: Custom RPC endpoint
        cluster: Solana cluster name
        **kwargs: Additional server configuration
        
    Returns:
        Configured FastAPI application
        
    Example:
        >>> config = MerchantConfig(
        ...     label="My Store",
        ...     recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
        ... )
        >>> app = create_app(config, cluster="devnet")
    """
    server = TransactionRequestServer(
        merchant_config=merchant_config,
        rpc_endpoint=rpc_endpoint,
        cluster=cluster,
        **kwargs
    )
    return server.get_app()


# Legacy app instance for backward compatibility
app = FastAPI(title="Solana Pay (Python) – Transaction Request")

# Set up basic middleware for legacy app
setup_middleware(app, enable_rate_limiting=False)

# Legacy configuration - can be overridden via environment
_legacy_config = MerchantConfig(
    label="Demo Merchant (Python)",
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Placeholder
)

_legacy_server = TransactionRequestServer(_legacy_config)

# Mount legacy routes
app.mount("/", _legacy_server.get_app())