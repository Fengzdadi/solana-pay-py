# API Documentation

This document provides comprehensive API documentation for the Solana Pay Python library.

## Table of Contents

- [Quick Start](#quick-start)
- [Core Models](#core-models)
- [URL Handling](#url-handling)
- [Transaction Building](#transaction-building)
- [Transaction Validation](#transaction-validation)
- [Server Components](#server-components)
- [Configuration](#configuration)
- [Utilities](#utilities)
- [High-Level API](#high-level-api)

## Quick Start

### Installation

```bash
pip install solana-pay-py
```

### Basic Usage

```python
from solanapay import create_payment_url, parse_payment_url
from decimal import Decimal

# Create a payment URL
url = create_payment_url(
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    amount="0.01",
    label="Coffee Shop"
)
print(url)

# Parse a payment URL
info = parse_payment_url(url)
print(f"Amount: {info['amount']} SOL")
```

## Core Models

### TransferRequest

The core model representing a Solana Pay transfer request.

```python
from solanapay import TransferRequest
from decimal import Decimal

request = TransferRequest(
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    amount=Decimal("0.01"),
    spl_token=None,  # None for SOL, mint address for SPL tokens
    references=["ref1", "ref2"],  # Optional reference accounts
    label="Coffee Shop",
    message="Thanks for your purchase!",
    memo="Order #123"
)
```

**Attributes:**
- `recipient` (str): Base58 encoded recipient public key
- `amount` (Optional[Decimal]): Payment amount
- `spl_token` (Optional[str]): SPL token mint address (None for SOL)
- `references` (Optional[List[str]]): Reference public keys for tracking
- `label` (Optional[str]): Human-readable label
- `message` (Optional[str]): Payment description
- `memo` (Optional[str]): On-chain memo

### TransactionOptions

Configuration options for transaction building.

```python
from solanapay import TransactionOptions

options = TransactionOptions(
    priority_fee=5000,  # Additional priority fee in lamports
    auto_create_ata=True,  # Auto-create recipient ATA
    use_versioned_tx=True,  # Use versioned transactions (v0)
    compute_unit_limit=200_000,  # Compute unit limit
    compute_unit_price=1000,  # Price per compute unit
    max_retries=3,  # RPC retry attempts
    timeout=30  # RPC timeout in seconds
)
```

### ValidationResult

Result of transaction validation operations.

```python
from solanapay import ValidationResult

# ValidationResult attributes:
result.is_valid  # Overall validation result
result.recipient_match  # Recipient validation
result.amount_match  # Amount validation
result.memo_match  # Memo validation
result.references_match  # References validation
result.confirmation_status  # "processed", "confirmed", "finalized"
result.errors  # List of error messages
result.warnings  # List of warning messages
```

## URL Handling

### encode_url()

Generate a solana: URL from a TransferRequest.

```python
from solanapay import encode_url, TransferRequest
from decimal import Decimal

request = TransferRequest(
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    amount=Decimal("0.01"),
    label="Coffee Shop"
)

url = encode_url(request)
# Returns: solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01&label=Coffee%20Shop
```

### parse_url()

Parse a solana: or https: URL into a TransferRequest.

```python
from solanapay import parse_url

url = "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01"
request = parse_url(url)

print(request.recipient)  # 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
print(request.amount)     # Decimal('0.01')
```

### encode_https_url()

Generate an https: URL for transaction request discovery.

```python
from solanapay import encode_https_url, TransferRequest
from decimal import Decimal

request = TransferRequest(
    recipient="",  # Empty for https URLs
    amount=Decimal("0.01"),
    label="Coffee Shop"
)

url = encode_https_url(request, "https://merchant.com/pay")
# Returns: https://merchant.com/pay?amount=0.01&label=Coffee%20Shop
```

## Transaction Building

### build_transfer_transaction()

Build a transfer transaction from a TransferRequest.

```python
from solanapay import build_transfer_transaction, TransferRequest, TransactionOptions
from solanapay.utils.rpc import create_rpc_client
from decimal import Decimal

async def create_transaction():
    request = TransferRequest(
        recipient="recipient_pubkey_here",
        amount=Decimal("0.01")
    )
    
    options = TransactionOptions(auto_create_ata=True)
    
    async with create_rpc_client("https://api.devnet.solana.com") as rpc:
        result = await build_transfer_transaction(
            rpc=rpc,
            payer="payer_pubkey_here",
            request=request,
            options=options
        )
        
        print(f"Transaction: {result.transaction}")
        print(f"Estimated fee: {result.estimated_fee} lamports")
```

### create_memo_instruction()

Create a memo instruction for transactions.

```python
from solanapay import create_memo_instruction

memo_ix = create_memo_instruction("Payment for coffee")
# Returns a Solana instruction that can be added to transactions
```

## Transaction Validation

### TransactionValidator

Comprehensive transaction validation against expected parameters.

```python
from solanapay import TransactionValidator, TransferRequest, ValidationConfig
from solanapay.utils.rpc import create_rpc_client
from decimal import Decimal

async def validate_payment():
    expected = TransferRequest(
        recipient="expected_recipient_here",
        amount=Decimal("0.01")
    )
    
    config = ValidationConfig(
        strict_amount=True,
        max_confirmation_time=60,
        required_confirmation="confirmed"
    )
    
    async with create_rpc_client("https://api.devnet.solana.com") as rpc:
        validator = TransactionValidator(rpc, config)
        
        result = await validator.wait_and_verify(
            signature="transaction_signature_here",
            expected=expected,
            timeout=60
        )
        
        if result.is_valid:
            print("✅ Payment validated successfully!")
        else:
            print("❌ Payment validation failed:")
            for error in result.errors:
                print(f"  • {error}")
```

### wait_and_verify()

Convenience function for transaction validation.

```python
from solanapay import wait_and_verify, TransferRequest
from solanapay.utils.rpc import create_rpc_client
from decimal import Decimal

async def verify_payment():
    expected = TransferRequest(
        recipient="expected_recipient_here",
        amount=Decimal("0.01")
    )
    
    async with create_rpc_client("https://api.devnet.solana.com") as rpc:
        result = await wait_and_verify(
            rpc_client=rpc,
            signature="transaction_signature_here",
            expected=expected,
            timeout=60,
            commitment="confirmed"
        )
        
        return result.is_valid
```

## Server Components

### TransactionRequestServer

FastAPI server for handling transaction requests from wallets.

```python
from solanapay import TransactionRequestServer, MerchantConfig
from decimal import Decimal

# Create merchant configuration
config = MerchantConfig(
    label="My Coffee Shop",
    recipient="merchant_pubkey_here",
    amount=Decimal("0.01"),  # Fixed amount
    memo="Coffee purchase"
)

# Create server
server = TransactionRequestServer(
    merchant_config=config,
    cluster="devnet",
    enable_middleware=True
)

# Get FastAPI app
app = server.get_app()

# Run with uvicorn
# uvicorn main:app --host 0.0.0.0 --port 8000
```

### create_app()

Convenience function for creating a transaction request app.

```python
from solanapay import create_app, MerchantConfig
from decimal import Decimal

config = MerchantConfig(
    label="My Store",
    recipient="merchant_pubkey_here",
    amount=Decimal("0.01")
)

app = create_app(
    merchant_config=config,
    cluster="devnet",
    enable_rate_limiting=True,
    cors_origins=["*"]
)
```

## Configuration

### Cluster Configuration

```python
from solanapay import get_cluster_config, register_cluster, ClusterConfig

# Get predefined cluster
devnet = get_cluster_config("devnet")
print(devnet.rpc_endpoint)  # https://api.devnet.solana.com

# Register custom cluster
custom_cluster = ClusterConfig(
    name="my-rpc",
    rpc_endpoint="https://my-rpc-provider.com",
    commitment="confirmed"
)
register_cluster(custom_cluster)
```

### Settings Management

```python
from solanapay import get_settings, configure_logging

# Get global settings
settings = get_settings()
print(settings.default_cluster)  # devnet

# Configure logging
configure_logging(enable=True, level="INFO")
```

## Utilities

### Logging

```python
from solanapay import setup_logging, get_logger

# Set up logging
logger = setup_logging(
    level="INFO",
    format_type="json",  # or "text"
    log_file="solana-pay.log"
)

# Get module logger
module_logger = get_logger(__name__)
module_logger.info("Starting payment processing", recipient="abc123")
```

### Error Handling

```python
from solanapay import SolanaPayError, ValidationError, URLError

try:
    # Some operation
    pass
except ValidationError as e:
    print(f"Validation failed: {e.message}")
    print(f"Error code: {e.error_code}")
    print(f"Context: {e.context}")
except SolanaPayError as e:
    print(f"Solana Pay error: {e}")
```

## High-Level API

### SolanaPayClient

High-level client for all Solana Pay operations.

```python
from solanapay import SolanaPayClient

# Create client
client = SolanaPayClient(rpc_endpoint="https://api.devnet.solana.com")

# Create payment URL
url = client.create_payment_url(
    recipient="recipient_pubkey_here",
    amount="0.01",
    label="Coffee Shop"
)

# Parse payment URL
info = client.parse_payment_url(url)

# Create transaction
transaction = await client.create_transaction(
    payer="payer_pubkey_here",
    recipient="recipient_pubkey_here",
    amount="0.01"
)

# Verify payment
result = await client.verify_payment(
    signature="transaction_signature_here",
    expected_recipient="recipient_pubkey_here",
    expected_amount="0.01"
)

# Check transaction status
status = await client.get_transaction_status("transaction_signature_here")
print(f"Confirmed: {status['confirmed']}")
```

### Convenience Functions

```python
from solanapay import (
    create_payment_url,
    parse_payment_url,
    create_payment_transaction,
    verify_payment
)

# Simple payment URL creation
url = create_payment_url(
    recipient="recipient_pubkey_here",
    amount="0.01",
    label="Coffee"
)

# Simple URL parsing
info = parse_payment_url(url)

# Simple transaction creation
tx = await create_payment_transaction(
    payer="payer_pubkey_here",
    recipient="recipient_pubkey_here",
    amount="0.01"
)

# Simple payment verification
result = await verify_payment(
    signature="tx_signature_here",
    expected_recipient="recipient_pubkey_here",
    expected_amount="0.01"
)
```

## Error Handling

All functions in the library can raise `SolanaPayError` or its subclasses:

- `ValidationError`: Input validation failures
- `URLError`: URL encoding/parsing errors
- `TransactionBuildError`: Transaction building failures
- `RPCError`: RPC communication errors
- `NetworkError`: Network-level errors
- `TimeoutError`: Operation timeouts

```python
from solanapay import SolanaPayError, ValidationError

try:
    # Your code here
    pass
except ValidationError as e:
    print(f"Validation error: {e.message}")
    if e.context:
        print(f"Field: {e.context.get('field')}")
        print(f"Value: {e.context.get('value')}")
except SolanaPayError as e:
    print(f"Solana Pay error: {e.message}")
    print(f"Error code: {e.error_code}")
```

## Best Practices

1. **Always use Decimal for amounts** to avoid floating-point precision issues
2. **Handle errors appropriately** - all operations can fail
3. **Use async/await** for better performance with RPC operations
4. **Configure logging** for production deployments
5. **Validate inputs** before processing
6. **Use connection pooling** for high-throughput applications
7. **Set appropriate timeouts** for RPC operations
8. **Test on devnet** before deploying to mainnet