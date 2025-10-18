# Solana Pay Python

> 🪙 Python implementation of [Solana Pay](https://github.com/solana-foundation/solana-pay) protocol.

A comprehensive Python library that implements the Solana Pay specification, enabling seamless cryptocurrency payments in Python applications. This library provides full compatibility with the official Solana Pay protocol and interoperability with existing Solana Pay wallets and applications.

## Features

- **URL Encoding/Parsing**: Generate and parse `solana:` and `https:` payment URLs
- **Transaction Building**: Create SOL and SPL token transfer transactions
- **Transaction Request Server**: FastAPI-based server for wallet integration
- **Transaction Validation**: Comprehensive payment verification and confirmation
- **Type Safety**: Full type hints and Pydantic model validation
- **Async Support**: Built with async/await for optimal performance
- **SPEC Compliant**: Strict adherence to official Solana Pay specification

## Installation

```bash
pip install solana-pay-py
```

Or with uv:
```bash
uv add solana-pay-py
```

## Quick Start

### Generate Payment URL

```python
from decimal import Decimal
from solanapay import TransferRequest, encode_url

# Create a payment request
request = TransferRequest(
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    amount=Decimal("0.01"),
    label="Coffee Shop",
    message="Thanks for your purchase!"
)

# Generate solana: URL
url = encode_url(request)
print(url)
# solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01&label=Coffee%20Shop&message=Thanks%20for%20your%20purchase!
```

### Parse Payment URL

```python
from solanapay import parse_url

url = "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01"
request = parse_url(url)
print(f"Recipient: {request.recipient}")
print(f"Amount: {request.amount} SOL")
```

### Transaction Request Server

```python
from fastapi import FastAPI
from solanapay.server import TransactionRequestServer

app = FastAPI()
server = TransactionRequestServer(
    rpc_endpoint="https://api.devnet.solana.com",
    merchant_config={
        "label": "My Store",
        "recipient": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
    }
)

app.include_router(server.router)
```

## Interoperability

This library is designed for full interoperability with the Solana Pay ecosystem:

- **Wallet Compatibility**: Works with Phantom, Solflare, and other Solana Pay compatible wallets
- **JavaScript Ecosystem**: Compatible with applications built using the official [@solana/pay](https://github.com/solana-foundation/solana-pay) JavaScript library
- **SPEC Compliance**: Implements the official [Solana Pay specification](https://github.com/solana-foundation/solana-pay/blob/master/SPEC.md)
- **Message Signing**: Supports the Solana wallet message signing specification

## Development

### Setup

```bash
# Clone the repository
git clone https://github.com/yourusername/solana-pay-py.git
cd solana-pay-py

# Install with development dependencies
uv sync --dev

# Install pre-commit hooks
uv run pre-commit install
```

### Testing

```bash
# Run all tests
uv run pytest

# Run with coverage
uv run pytest --cov=solanapay

# Run only unit tests
uv run pytest -m unit

# Run integration tests (requires devnet)
uv run pytest -m integration
```

### Code Quality

```bash
# Format code
uv run ruff format

# Lint code
uv run ruff check

# Type checking
uv run mypy solanapay
```

## Documentation

- [API Documentation](docs/api.md)
- [Examples](examples/)
- [Troubleshooting Guide](docs/troubleshooting.md)
- [Contributing Guidelines](CONTRIBUTING.md)

## Acknowledgments

This project was developed with the assistance of [Kiro](https://kiro.ai), an AI-powered development environment.

## License

MIT License - see [LICENSE](LICENSE) file for details.

## References

- [Solana Pay Specification](https://github.com/solana-foundation/solana-pay/blob/master/SPEC.md)
- [Solana Pay JavaScript Implementation](https://github.com/solana-foundation/solana-pay)
- [Solana Cookbook](https://solanacookbook.com/)
- [Solana Python SDK](https://michaelhly.com/solana-py/)