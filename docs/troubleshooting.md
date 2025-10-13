# Troubleshooting Guide

This guide covers common issues and their solutions when using Solana Pay Python.

## Table of Contents

- [Installation Issues](#installation-issues)
- [RPC Connection Problems](#rpc-connection-problems)
- [Transaction Building Errors](#transaction-building-errors)
- [Validation Failures](#validation-failures)
- [Server Issues](#server-issues)
- [Wallet Integration Problems](#wallet-integration-problems)
- [Performance Issues](#performance-issues)
- [Debugging Tools](#debugging-tools)

## Installation Issues

### Python Version Compatibility

**Problem**: `RuntimeError: Solana Pay Python requires Python 3.11 or higher`

**Solution**:
```bash
# Check your Python version
python --version

# Install Python 3.11+ using pyenv (recommended)
pyenv install 3.11.0
pyenv global 3.11.0

# Or use conda
conda create -n solana-pay python=3.11
conda activate solana-pay
```

### Missing Dependencies

**Problem**: `ImportError: No module named 'solana'`

**Solution**:
```bash
# Install all dependencies
pip install solana-pay-py

# Or install with specific versions
pip install solana>=0.36.9 solders>=0.26.0

# Check dependency compatibility
solana-pay check-compat
```

### Build Errors on Apple Silicon

**Problem**: Build errors when installing on M1/M2 Macs

**Solution**:
```bash
# Use conda-forge for better ARM64 support
conda install -c conda-forge python=3.11

# Or use Rosetta 2
arch -x86_64 pip install solana-pay-py
```

## RPC Connection Problems

### Connection Timeouts

**Problem**: `RPCError: Request timed out after 30s`

**Solution**:
```python
from solanapay.config import get_settings

# Increase timeout
settings = get_settings()
settings.default_timeout = 60  # 60 seconds

# Or use custom RPC client
from solanapay.utils.rpc import create_rpc_client

async with create_rpc_client(
    "https://api.devnet.solana.com",
    timeout=60,
    max_retries=5
) as rpc:
    # Your code here
    pass
```

### Rate Limiting

**Problem**: `RPCError: Too many requests`

**Solution**:
```python
# Use connection pooling
from solanapay.utils.rpc import RPCConnectionPool

pool = RPCConnectionPool([
    "https://api.devnet.solana.com",
    "https://devnet.helius-rpc.com",  # Add backup endpoints
])

async with pool.get_client() as rpc:
    # Your code here
    pass
```

### Invalid RPC Endpoint

**Problem**: `RPCError: Failed to connect to RPC endpoint`

**Solution**:
```python
# Test RPC endpoint
from solanapay.utils.rpc import create_rpc_client

async def test_rpc(endpoint):
    try:
        async with create_rpc_client(endpoint) as rpc:
            slot = await rpc.get_slot()
            print(f"✅ RPC working, current slot: {slot}")
            return True
    except Exception as e:
        print(f"❌ RPC failed: {e}")
        return False

# Test different endpoints
endpoints = [
    "https://api.devnet.solana.com",
    "https://api.mainnet-beta.solana.com",
    "https://devnet.helius-rpc.com"
]

for endpoint in endpoints:
    await test_rpc(endpoint)
```

## Transaction Building Errors

### Account Not Found

**Problem**: `AccountNotFoundError: Associated Token Account not found`

**Solution**:
```python
from solanapay import TransactionOptions

# Enable automatic ATA creation
options = TransactionOptions(auto_create_ata=True)

# Or check if ATA exists first
from solanapay.utils.ata import check_ata_exists

async with create_rpc_client("https://api.devnet.solana.com") as rpc:
    exists = await check_ata_exists(rpc, owner_pubkey, mint_pubkey)
    if not exists:
        print("ATA doesn't exist, will be created automatically")
```

### Insufficient Funds

**Problem**: `InsufficientFundsError: Account has insufficient funds`

**Solution**:
```python
# Check account balance before transaction
from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey

async def check_balance(pubkey_str):
    async with AsyncClient("https://api.devnet.solana.com") as rpc:
        pubkey = Pubkey.from_string(pubkey_str)
        balance = await rpc.get_balance(pubkey)
        sol_balance = balance.value / 1_000_000_000  # Convert to SOL
        print(f"Balance: {sol_balance} SOL")
        return sol_balance

# For devnet testing, get SOL from faucet
# Visit: https://faucet.solana.com/
```

### Invalid Public Key

**Problem**: `ValidationError: Invalid base58 public key`

**Solution**:
```python
# Validate public key format
from solanapay.models.transfer import TransferRequest

def validate_pubkey(pubkey_str):
    try:
        # This will raise ValidationError if invalid
        request = TransferRequest(recipient=pubkey_str)
        return True
    except ValidationError as e:
        print(f"Invalid public key: {e.message}")
        return False

# Example usage
pubkey = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
if validate_pubkey(pubkey):
    print("✅ Valid public key")
```

### Decimal Precision Issues

**Problem**: `ValidationError: Amount has too many decimal places`

**Solution**:
```python
from decimal import Decimal

# Always use Decimal for amounts
amount = Decimal("0.01")  # ✅ Correct

# Avoid floats
amount = 0.01  # ❌ Can cause precision issues

# For SPL tokens, check decimal places
async def get_token_decimals(mint_address):
    async with create_rpc_client("https://api.devnet.solana.com") as rpc:
        from solders.pubkey import Pubkey
        mint = Pubkey.from_string(mint_address)
        supply = await rpc.get_token_supply(mint)
        return supply.value.decimals

# Validate amount precision
from solanapay.utils.decimal import validate_amount_precision

amount = Decimal("0.123456789")
decimals = 6  # USDC has 6 decimals
try:
    validate_amount_precision(amount, decimals)
except ValidationError as e:
    print(f"Amount precision error: {e.message}")
```

## Validation Failures

### Transaction Not Found

**Problem**: `ValidationError: Transaction not found`

**Solution**:
```python
# Wait longer for transaction confirmation
from solanapay import verify_payment

result = await verify_payment(
    signature="your_signature_here",
    expected_recipient="recipient_pubkey",
    expected_amount="0.01",
    timeout=120  # Wait 2 minutes instead of default 60s
)

# Check transaction status first
from solanapay import SolanaPayClient

client = SolanaPayClient()
status = await client.get_transaction_status("your_signature_here")
print(f"Transaction exists: {status['exists']}")
print(f"Confirmed: {status['confirmed']}")
```

### Amount Mismatch

**Problem**: `ValidationError: Amount mismatch: expected 0.01 SOL, but recipient received 0.009995 SOL`

**Solution**:
```python
from solanapay import ValidationConfig

# Use flexible amount validation
config = ValidationConfig(
    strict_amount=False,  # Allow small differences
    max_confirmation_time=60
)

# Or account for transaction fees
expected_amount = Decimal("0.01")
tolerance = Decimal("0.000005")  # 5 microSOL tolerance

# Manual validation
if abs(actual_amount - expected_amount) <= tolerance:
    print("✅ Amount within acceptable range")
```

### Memo Not Found

**Problem**: `ValidationError: Expected memo 'order-123' not found in transaction`

**Solution**:
```python
# Check if memo instruction was included
from solanapay.utils.debug import TransactionDebugger

async def debug_memo(signature):
    async with create_rpc_client("https://api.devnet.solana.com") as rpc:
        debugger = TransactionDebugger(rpc)
        debug_info = await debugger.debug_transaction(signature)
        
        # Check log messages for memo
        logs = debug_info.get("transaction_data", {}).get("meta", {}).get("logMessages", [])
        for log in logs:
            if "memo" in log.lower():
                print(f"Found memo in logs: {log}")
        
        return debug_info

# Make memo optional in validation
config = ValidationConfig(require_memo=False)
```

## Server Issues

### CORS Errors

**Problem**: `CORS policy: No 'Access-Control-Allow-Origin' header`

**Solution**:
```python
from solanapay import create_app

# Configure CORS properly
app = create_app(
    merchant_config=config,
    cors_origins=["https://your-frontend-domain.com"],  # Specific origins
    # or
    cors_origins=["*"]  # All origins (development only)
)

# Or manually configure CORS
from solanapay.server.middleware import setup_cors

setup_cors(
    app,
    allowed_origins=["https://your-domain.com"],
    allow_credentials=True,
    allowed_methods=["GET", "POST", "OPTIONS"],
    allowed_headers=["Content-Type", "Authorization"]
)
```

### Rate Limiting Issues

**Problem**: `HTTP 429: Rate limit exceeded`

**Solution**:
```python
# Adjust rate limiting
from solanapay.server.middleware import setup_middleware

setup_middleware(
    app,
    enable_rate_limiting=True,
    rate_limit_rpm=120,  # 120 requests per minute
    rate_limit_burst=20  # 20 requests in 10 seconds
)

# Or disable for development
setup_middleware(app, enable_rate_limiting=False)
```

### Server Won't Start

**Problem**: `OSError: [Errno 48] Address already in use`

**Solution**:
```bash
# Find process using port 8000
lsof -i :8000

# Kill the process
kill -9 <PID>

# Or use a different port
uvicorn main:app --port 8001
```

## Wallet Integration Problems

### QR Code Not Scanning

**Problem**: Wallet doesn't recognize QR code

**Solution**:
```python
# Ensure URL format is correct
from solanapay import create_payment_url

url = create_payment_url(
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    amount="0.01",  # Use string, not float
    label="Test Payment"
)

# Verify URL format
print(f"URL: {url}")
# Should start with "solana:" and be properly encoded

# Test with CLI
import subprocess
result = subprocess.run(["solana-pay", "parse-url", url], capture_output=True, text=True)
print(result.stdout)
```

### Transaction Request Fails

**Problem**: Wallet shows "Transaction request failed"

**Solution**:
```python
# Check server logs for errors
import logging
logging.basicConfig(level=logging.DEBUG)

# Ensure server is accessible
# Test endpoints manually:
# GET http://your-server.com/tx
# POST http://your-server.com/tx with {"account": "pubkey"}

# Verify merchant config
config = MerchantConfig(
    label="Your Store",  # Required
    recipient="valid_pubkey_here",  # Must be valid
    amount=Decimal("0.01")  # Must be positive
)
```

### Wallet Compatibility

**Problem**: Wallet doesn't support Solana Pay

**Solution**:
```python
# Check wallet compatibility
supported_wallets = [
    "Phantom",
    "Solflare", 
    "Backpack",
    "Glow",
    "Slope"
]

print("Supported wallets:")
for wallet in supported_wallets:
    print(f"  ✅ {wallet}")

# For testing, use Phantom wallet on devnet
# Download: https://phantom.app/
```

## Performance Issues

### Slow Transaction Building

**Problem**: Transaction building takes too long

**Solution**:
```python
# Use connection pooling
from solanapay.utils.rpc import RPCClientManager

manager = RPCClientManager(
    endpoint="https://api.devnet.solana.com",
    max_connections=10,  # Increase pool size
    timeout=30
)

# Cache mint decimals
mint_decimals_cache = {}

async def get_cached_decimals(rpc, mint):
    if mint not in mint_decimals_cache:
        supply = await rpc.get_token_supply(mint)
        mint_decimals_cache[mint] = supply.value.decimals
    return mint_decimals_cache[mint]
```

### High Memory Usage

**Problem**: Memory usage keeps increasing

**Solution**:
```python
# Properly close RPC connections
async with create_rpc_client(endpoint) as rpc:
    # Your code here
    pass  # Connection automatically closed

# Clear caches periodically
import gc
gc.collect()

# Use connection limits
manager = RPCClientManager(
    endpoint=endpoint,
    max_connections=5  # Limit connections
)
```

## Debugging Tools

### Enable Debug Logging

```python
from solanapay import setup_logging

# Enable debug logging
logger = setup_logging(
    level="DEBUG",
    format_type="text",
    log_file="debug.log"
)

# Or use environment variable
import os
os.environ["SOLANA_PAY_LOG_LEVEL"] = "DEBUG"
os.environ["SOLANA_PAY_ENABLE_LOGGING"] = "true"
```

### Transaction Debugging

```python
from solanapay.utils.debug import TransactionDebugger, PaymentDebugger

async def debug_transaction(signature):
    async with create_rpc_client("https://api.devnet.solana.com") as rpc:
        debugger = TransactionDebugger(rpc)
        debug_info = await debugger.debug_transaction(signature)
        
        print("=== Transaction Debug Info ===")
        print(f"Signature: {signature}")
        print(f"Accounts: {len(debug_info.get('account_info', {}))}")
        print(f"Instructions: {len(debug_info.get('instruction_analysis', []))}")
        
        # Print balance changes
        for account, change in debug_info.get('balance_changes', {}).items():
            if change['change'] != 0:
                print(f"  {account}: {change['change_sol']} SOL")

# Usage
await debug_transaction("your_signature_here")
```

### System Information

```bash
# Check system compatibility
solana-pay check-compat

# Get system information
solana-pay system-info

# Test RPC connectivity
solana-pay create-url --recipient 9Wz... --amount 0.01
```

### Error Reporting

```python
from solanapay.utils.errors import create_error_report

try:
    # Your code here
    pass
except Exception as e:
    report = create_error_report(
        operation="payment_processing",
        inputs={"recipient": "...", "amount": "0.01"},
        error=e,
        context={"user_id": "123", "order_id": "abc"}
    )
    
    # Log or send report
    print(json.dumps(report, indent=2, default=str))
```

## Getting Help

If you're still experiencing issues:

1. **Check the logs** - Enable debug logging to see detailed error information
2. **Test on devnet** - Always test on devnet before mainnet
3. **Use the CLI tools** - The `solana-pay` CLI can help diagnose issues
4. **Check RPC status** - Ensure your RPC endpoint is working
5. **Verify wallet compatibility** - Make sure you're using a supported wallet
6. **Review the examples** - Check the examples directory for working code

### Common Error Patterns

```python
# Pattern 1: Always use try-catch for RPC operations
try:
    result = await some_rpc_operation()
except RPCError as e:
    print(f"RPC failed: {e.message}")
    # Handle gracefully

# Pattern 2: Validate inputs early
from solanapay.utils.errors import ValidationError

try:
    request = TransferRequest(recipient=user_input)
except ValidationError as e:
    return {"error": f"Invalid input: {e.message}"}

# Pattern 3: Use proper decimal handling
from decimal import Decimal
amount = Decimal(str(user_amount))  # Convert to string first
```

Remember: When in doubt, check the debug logs and use the CLI tools to isolate the issue!