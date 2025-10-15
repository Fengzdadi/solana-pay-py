#!/usr/bin/env python3
"""
Example FastAPI merchant server for Solana Pay transaction requests.

This example demonstrates how to set up a complete merchant server
that can handle Solana Pay transaction requests from wallets.

Usage:
    python examples/fastapi_merchant.py

Then test with:
    curl http://localhost:8000/tx
    curl -X POST http://localhost:8000/tx -H "Content-Type: application/json" -d '{"account":"9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"}'
"""

import os
import sys
import uvicorn
from decimal import Decimal

# Add parent directory to path so we can import solanapay
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solanapay.server.api import create_app
from solanapay.server.schemas import MerchantConfig
from solanapay.config import configure_logging


def create_merchant_config() -> MerchantConfig:
    """Create merchant configuration from environment variables or defaults."""
    
    # You can set these via environment variables:
    # MERCHANT_LABEL="My Coffee Shop"
    # MERCHANT_RECIPIENT="your_wallet_address_here"
    # MERCHANT_AMOUNT="0.01"  # Optional fixed amount
    # MERCHANT_SPL_TOKEN="mint_address_here"  # Optional for SPL tokens
    # MERCHANT_MEMO="Coffee purchase"  # Optional memo
    
    return MerchantConfig(
        label=os.getenv("MERCHANT_LABEL", "Coffee Shop Demo"),
        icon=os.getenv("MERCHANT_ICON", "https://example.com/coffee-icon.png"),
        recipient=os.getenv(
            "MERCHANT_RECIPIENT", 
            "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Replace with your wallet
        ),
        amount=Decimal(os.getenv("MERCHANT_AMOUNT", "0.01")),  # 0.01 SOL
        spl_token=os.getenv("MERCHANT_SPL_TOKEN"),  # None = SOL payments
        memo=os.getenv("MERCHANT_MEMO", "Coffee purchase"),
        references=None,  # Could add reference tracking
        require_memo=False
    )


def main():
    """Run the merchant server."""
    
    # Configure logging
    configure_logging(enable=True, level="INFO")
    
    # Create merchant configuration
    merchant_config = create_merchant_config()
    
    print("🚀 Starting Solana Pay Merchant Server")
    print(f"📍 Merchant: {merchant_config.label}")
    print(f"💰 Recipient: {merchant_config.recipient}")
    print(f"💵 Amount: {merchant_config.amount} SOL")
    print(f"📝 Memo: {merchant_config.memo}")
    print()
    
    # Create FastAPI app
    app = create_app(
        merchant_config=merchant_config,
        cluster=os.getenv("SOLANA_CLUSTER", "devnet"),  # Use devnet by default
        enable_middleware=True,
        enable_rate_limiting=True,
        enable_logging=True,
        rate_limit_rpm=100,  # 100 requests per minute
        cors_origins=["*"]  # Allow all origins for demo
    )
    
    # Get server configuration
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    
    print(f"🌐 Server starting at http://{host}:{port}")
    print("📋 API Documentation: http://localhost:8000/docs")
    print("🔍 Health Check: http://localhost:8000/health")
    print()
    print("Test endpoints:")
    print(f"  GET  http://localhost:{port}/tx")
    print(f"  POST http://localhost:{port}/tx")
    print()
    print("Example POST request:")
    print('  curl -X POST http://localhost:8000/tx \\')
    print('    -H "Content-Type: application/json" \\')
    print('    -d \'{"account":"9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"}\'')
    print()
    
    # Run the server
    uvicorn.run(
        app,
        host=host,
        port=port,
        log_level="info",
        access_log=True
    )


if __name__ == "__main__":
    main()