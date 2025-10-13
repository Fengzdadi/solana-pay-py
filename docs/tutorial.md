# Solana Pay Python Tutorial

This tutorial will guide you through building a complete Solana Pay integration from scratch. We'll create a coffee shop that accepts SOL payments using QR codes.

## Table of Contents

1. [Setup and Installation](#setup-and-installation)
2. [Creating Payment URLs](#creating-payment-urls)
3. [Generating QR Codes](#generating-qr-codes)
4. [Building a Merchant Server](#building-a-merchant-server)
5. [Transaction Validation](#transaction-validation)
6. [Complete Example](#complete-example)
7. [Testing with Wallets](#testing-with-wallets)
8. [Production Deployment](#production-deployment)

## Setup and Installation

### Prerequisites

- Python 3.11 or higher
- A Solana wallet (Phantom, Solflare, etc.)
- Basic knowledge of Python and async programming

### Installation

```bash
# Install the library
pip install solana-pay-py

# Install additional dependencies for this tutorial
pip install qrcode[pil] fastapi uvicorn
```

### Verify Installation

```bash
# Check if everything is working
solana-pay check-compat
```

## Creating Payment URLs

Let's start by creating simple payment URLs for our coffee shop.

### Basic Payment URL

```python
from solanapay import create_payment_url

# Create a simple payment URL
url = create_payment_url(
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",  # Your wallet address
    amount="0.01",  # 0.01 SOL (~$1 at current prices)
    label="Coffee Shop",
    message="Thanks for buying coffee!"
)

print(f"Payment URL: {url}")
```

### Advanced Payment URL with References

```python
from solanapay import create_payment_url
import uuid

# Generate a unique reference for this order
order_id = str(uuid.uuid4())
reference_keypair = "11111111111111111111111111111112"  # Example reference

url = create_payment_url(
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    amount="0.01",
    label="Coffee Shop",
    message=f"Order #{order_id[:8]}",
    memo=f"coffee-order-{order_id}",
    references=[reference_keypair]
)

print(f"Payment URL with tracking: {url}")
```

## Generating QR Codes

QR codes make it easy for customers to scan and pay with their mobile wallets.

### Simple QR Code Generation

```python
import qrcode
from solanapay import create_payment_url

def create_payment_qr(recipient, amount, label):
    """Create a QR code for a Solana Pay URL."""
    
    # Create payment URL
    url = create_payment_url(
        recipient=recipient,
        amount=amount,
        label=label
    )
    
    # Generate QR code
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    # Create image
    img = qr.make_image(fill_color="black", back_color="white")
    return img, url

# Create QR code for coffee payment
qr_image, payment_url = create_payment_qr(
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
    amount="0.01",
    label="Coffee Shop"
)

# Save QR code
qr_image.save("coffee_payment.png")
print(f"QR code saved! URL: {payment_url}")
```

### Dynamic QR Code with Order Tracking

```python
import qrcode
from solanapay import create_payment_url
from datetime import datetime
import uuid

class CoffeeShop:
    def __init__(self, recipient_address):
        self.recipient = recipient_address
        self.orders = {}
    
    def create_order(self, item, price):
        """Create a new order and return QR code."""
        order_id = str(uuid.uuid4())[:8]
        
        # Store order details
        self.orders[order_id] = {
            "item": item,
            "price": price,
            "created_at": datetime.now(),
            "status": "pending"
        }
        
        # Create payment URL with order tracking
        url = create_payment_url(
            recipient=self.recipient,
            amount=str(price),
            label="Coffee Shop",
            message=f"{item} - Order #{order_id}",
            memo=f"order-{order_id}"
        )
        
        # Generate QR code
        qr = qrcode.QRCode(version=1, box_size=10, border=4)
        qr.add_data(url)
        qr.make(fit=True)
        
        img = qr.make_image(fill_color="black", back_color="white")
        
        return {
            "order_id": order_id,
            "qr_image": img,
            "payment_url": url,
            "amount": price
        }
    
    def get_order(self, order_id):
        """Get order details."""
        return self.orders.get(order_id)

# Example usage
shop = CoffeeShop("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")

# Create order for a latte
order = shop.create_order("Latte", 0.015)  # 0.015 SOL
order["qr_image"].save(f"order_{order['order_id']}.png")

print(f"Order created: {order['order_id']}")
print(f"Amount: {order['amount']} SOL")
print(f"QR code saved as: order_{order['order_id']}.png")
```

## Building a Merchant Server

Now let's create a server that can handle transaction requests from wallets.

### Basic Merchant Server

```python
from solanapay import create_app, MerchantConfig
from decimal import Decimal
import uvicorn

# Configure your merchant
config = MerchantConfig(
    label="Coffee Shop",
    icon="https://example.com/coffee-icon.png",
    recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",  # Your wallet
    amount=Decimal("0.01"),  # Fixed price
    memo="Coffee purchase"
)

# Create FastAPI app
app = create_app(
    merchant_config=config,
    cluster="devnet",  # Use devnet for testing
    enable_rate_limiting=True,
    cors_origins=["*"]  # Allow all origins for testing
)

if __name__ == "__main__":
    print("🚀 Starting Coffee Shop Payment Server")
    print("📍 Merchant: Coffee Shop")
    print("💰 Price: 0.01 SOL")
    print("🌐 Server: http://localhost:8000")
    print("📋 API Docs: http://localhost:8000/docs")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
```

### Advanced Server with Order Management

```python
from solanapay import TransactionRequestServer, MerchantConfig
from solanapay.server.schemas import TransactionRequest, TransactionResponse
from fastapi import FastAPI, HTTPException
from decimal import Decimal
import uuid
from datetime import datetime

class CoffeeShopServer:
    def __init__(self, recipient_address):
        self.recipient = recipient_address
        self.orders = {}
        self.menu = {
            "espresso": Decimal("0.008"),
            "latte": Decimal("0.015"),
            "cappuccino": Decimal("0.012"),
            "americano": Decimal("0.010")
        }
        
        # Create base merchant config
        self.base_config = MerchantConfig(
            label="Coffee Shop",
            recipient=recipient_address,
            memo="Coffee purchase"
        )
        
        # Create FastAPI app
        self.app = FastAPI(title="Coffee Shop API")
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/menu")
        async def get_menu():
            """Get coffee menu with prices."""
            return {
                "menu": {
                    item: str(price) for item, price in self.menu.items()
                }
            }
        
        @self.app.post("/order")
        async def create_order(item: str):
            """Create a new order."""
            if item not in self.menu:
                raise HTTPException(status_code=400, detail="Item not available")
            
            order_id = str(uuid.uuid4())[:8]
            price = self.menu[item]
            
            # Store order
            self.orders[order_id] = {
                "item": item,
                "price": price,
                "created_at": datetime.now(),
                "status": "pending"
            }
            
            # Create transaction request server for this order
            order_config = MerchantConfig(
                label=f"Coffee Shop - {item.title()}",
                recipient=self.recipient,
                amount=price,
                memo=f"order-{order_id}"
            )
            
            server = TransactionRequestServer(order_config, cluster="devnet")
            
            return {
                "order_id": order_id,
                "item": item,
                "price": str(price),
                "payment_url": f"https://your-domain.com/pay/{order_id}"
            }
        
        @self.app.get("/order/{order_id}")
        async def get_order(order_id: str):
            """Get order status."""
            if order_id not in self.orders:
                raise HTTPException(status_code=404, detail="Order not found")
            
            order = self.orders[order_id]
            return {
                "order_id": order_id,
                "item": order["item"],
                "price": str(order["price"]),
                "status": order["status"],
                "created_at": order["created_at"].isoformat()
            }
        
        # Add payment endpoints for each order
        @self.app.get("/pay/{order_id}/tx")
        async def get_tx_metadata(order_id: str):
            """Get transaction metadata for order."""
            if order_id not in self.orders:
                raise HTTPException(status_code=404, detail="Order not found")
            
            order = self.orders[order_id]
            return {
                "label": f"Coffee Shop - {order['item'].title()}",
                "icon": "https://example.com/coffee-icon.png"
            }
        
        @self.app.post("/pay/{order_id}/tx")
        async def create_transaction(order_id: str, request: TransactionRequest):
            """Create transaction for order."""
            if order_id not in self.orders:
                raise HTTPException(status_code=404, detail="Order not found")
            
            order = self.orders[order_id]
            
            # Create order-specific config
            order_config = MerchantConfig(
                label=f"Coffee Shop - {order['item'].title()}",
                recipient=self.recipient,
                amount=order["price"],
                memo=f"order-{order_id}"
            )
            
            # Create transaction server and handle request
            server = TransactionRequestServer(order_config, cluster="devnet")
            # Implementation would create actual transaction here
            
            return TransactionResponse(
                transaction="base64_encoded_transaction_here",
                message=f"Payment for {order['item']}"
            )

# Create and run server
shop_server = CoffeeShopServer("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")

if __name__ == "__main__":
    uvicorn.run(shop_server.app, host="0.0.0.0", port=8000)
```

## Transaction Validation

After a customer pays, you need to validate that the payment was successful.

### Basic Payment Validation

```python
import asyncio
from solanapay import verify_payment

async def validate_coffee_payment(signature, expected_amount="0.01"):
    """Validate a coffee shop payment."""
    
    result = await verify_payment(
        signature=signature,
        expected_recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        expected_amount=expected_amount,
        timeout=60  # Wait up to 60 seconds for confirmation
    )
    
    if result["is_valid"]:
        print("✅ Payment validated successfully!")
        print(f"Confirmation status: {result['confirmation_status']}")
        return True
    else:
        print("❌ Payment validation failed:")
        for error in result["errors"]:
            print(f"  • {error}")
        return False

# Example usage
async def main():
    # Replace with actual transaction signature
    tx_signature = "your_transaction_signature_here"
    
    is_valid = await validate_coffee_payment(tx_signature)
    if is_valid:
        print("Coffee order confirmed! ☕")
    else:
        print("Payment failed. Please try again.")

# Run validation
# asyncio.run(main())
```

### Advanced Validation with Order Tracking

```python
import asyncio
from solanapay import TransactionValidator, TransferRequest, ValidationConfig
from solanapay.utils.rpc import create_rpc_client
from decimal import Decimal

class PaymentValidator:
    def __init__(self, rpc_endpoint="https://api.devnet.solana.com"):
        self.rpc_endpoint = rpc_endpoint
        self.validated_payments = set()
    
    async def validate_order_payment(self, order_id, signature, expected_amount, expected_memo):
        """Validate payment for a specific order."""
        
        # Prevent double-validation
        if signature in self.validated_payments:
            return {"valid": False, "error": "Payment already processed"}
        
        # Create expected transfer request
        expected = TransferRequest(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount=Decimal(str(expected_amount)),
            memo=expected_memo
        )
        
        # Configure validation
        config = ValidationConfig(
            strict_amount=True,
            require_memo=True,
            max_confirmation_time=60,
            required_confirmation="confirmed"
        )
        
        try:
            async with create_rpc_client(self.rpc_endpoint) as rpc:
                validator = TransactionValidator(rpc, config)
                
                result = await validator.wait_and_verify(
                    signature=signature,
                    expected=expected,
                    timeout=60
                )
                
                if result.is_valid:
                    # Mark as validated
                    self.validated_payments.add(signature)
                    
                    return {
                        "valid": True,
                        "order_id": order_id,
                        "signature": signature,
                        "confirmation_status": result.confirmation_status,
                        "amount": str(expected_amount),
                        "memo": expected_memo
                    }
                else:
                    return {
                        "valid": False,
                        "errors": result.errors,
                        "warnings": result.warnings
                    }
                    
        except Exception as e:
            return {
                "valid": False,
                "error": f"Validation failed: {str(e)}"
            }

# Example usage
async def validate_coffee_order():
    validator = PaymentValidator()
    
    result = await validator.validate_order_payment(
        order_id="abc123",
        signature="transaction_signature_here",
        expected_amount="0.015",  # Latte price
        expected_memo="order-abc123"
    )
    
    if result["valid"]:
        print(f"✅ Order {result['order_id']} payment confirmed!")
        print(f"Amount: {result['amount']} SOL")
        print(f"Status: {result['confirmation_status']}")
    else:
        print("❌ Payment validation failed:")
        if "errors" in result:
            for error in result["errors"]:
                print(f"  • {error}")
        if "error" in result:
            print(f"  • {result['error']}")

# asyncio.run(validate_coffee_order())
```

## Complete Example

Here's a complete coffee shop implementation that ties everything together:

```python
import asyncio
import qrcode
import uvicorn
from datetime import datetime
from decimal import Decimal
from fastapi import FastAPI, HTTPException, BackgroundTasks
from pydantic import BaseModel
import uuid

from solanapay import (
    create_payment_url,
    TransactionRequestServer,
    MerchantConfig,
    verify_payment
)

class OrderRequest(BaseModel):
    item: str
    customer_name: str = "Anonymous"

class CoffeeShop:
    def __init__(self, recipient_address):
        self.recipient = recipient_address
        self.orders = {}
        self.menu = {
            "espresso": {"price": Decimal("0.008"), "name": "Espresso"},
            "latte": {"price": Decimal("0.015"), "name": "Latte"},
            "cappuccino": {"price": Decimal("0.012"), "name": "Cappuccino"},
            "americano": {"price": Decimal("0.010"), "name": "Americano"}
        }
        
        self.app = FastAPI(title="☕ Coffee Shop API")
        self.setup_routes()
    
    def setup_routes(self):
        @self.app.get("/")
        async def root():
            return {
                "message": "Welcome to Coffee Shop!",
                "menu_endpoint": "/menu",
                "order_endpoint": "/order"
            }
        
        @self.app.get("/menu")
        async def get_menu():
            """Get coffee menu."""
            return {
                "menu": {
                    key: {
                        "name": item["name"],
                        "price_sol": str(item["price"]),
                        "price_usd": f"${float(item['price']) * 100:.2f}"  # Rough conversion
                    }
                    for key, item in self.menu.items()
                }
            }
        
        @self.app.post("/order")
        async def create_order(order_request: OrderRequest):
            """Create a new coffee order."""
            if order_request.item not in self.menu:
                raise HTTPException(status_code=400, detail="Item not available")
            
            order_id = str(uuid.uuid4())[:8]
            item_info = self.menu[order_request.item]
            
            # Create order
            order = {
                "id": order_id,
                "item": order_request.item,
                "item_name": item_info["name"],
                "customer_name": order_request.customer_name,
                "price": item_info["price"],
                "status": "pending",
                "created_at": datetime.now(),
                "payment_signature": None
            }
            
            self.orders[order_id] = order
            
            # Create payment URL
            payment_url = create_payment_url(
                recipient=self.recipient,
                amount=str(item_info["price"]),
                label=f"Coffee Shop - {item_info['name']}",
                message=f"Order for {order_request.customer_name}",
                memo=f"order-{order_id}"
            )
            
            # Generate QR code
            qr = qrcode.QRCode(version=1, box_size=10, border=4)
            qr.add_data(payment_url)
            qr.make(fit=True)
            
            # Save QR code (in production, you'd return the image data)
            qr_img = qr.make_image(fill_color="black", back_color="white")
            qr_filename = f"qr_order_{order_id}.png"
            qr_img.save(qr_filename)
            
            return {
                "order_id": order_id,
                "item": item_info["name"],
                "customer": order_request.customer_name,
                "price": str(item_info["price"]),
                "payment_url": payment_url,
                "qr_code_file": qr_filename,
                "status": "pending"
            }
        
        @self.app.get("/order/{order_id}")
        async def get_order(order_id: str):
            """Get order details."""
            if order_id not in self.orders:
                raise HTTPException(status_code=404, detail="Order not found")
            
            order = self.orders[order_id]
            return {
                "order_id": order_id,
                "item": order["item_name"],
                "customer": order["customer_name"],
                "price": str(order["price"]),
                "status": order["status"],
                "created_at": order["created_at"].isoformat(),
                "payment_signature": order["payment_signature"]
            }
        
        @self.app.post("/order/{order_id}/verify")
        async def verify_order_payment(order_id: str, signature: str, background_tasks: BackgroundTasks):
            """Verify payment for an order."""
            if order_id not in self.orders:
                raise HTTPException(status_code=404, detail="Order not found")
            
            order = self.orders[order_id]
            
            if order["status"] == "paid":
                return {"message": "Order already paid", "status": "paid"}
            
            # Add verification to background tasks
            background_tasks.add_task(self.verify_payment_background, order_id, signature)
            
            return {"message": "Payment verification started", "order_id": order_id}
        
        @self.app.get("/orders")
        async def list_orders():
            """List all orders."""
            return {
                "orders": [
                    {
                        "order_id": order_id,
                        "item": order["item_name"],
                        "customer": order["customer_name"],
                        "status": order["status"],
                        "created_at": order["created_at"].isoformat()
                    }
                    for order_id, order in self.orders.items()
                ]
            }
    
    async def verify_payment_background(self, order_id: str, signature: str):
        """Background task to verify payment."""
        order = self.orders[order_id]
        
        try:
            result = await verify_payment(
                signature=signature,
                expected_recipient=self.recipient,
                expected_amount=str(order["price"]),
                expected_memo=f"order-{order_id}",
                timeout=60
            )
            
            if result["is_valid"]:
                # Update order status
                order["status"] = "paid"
                order["payment_signature"] = signature
                print(f"✅ Order {order_id} payment confirmed!")
            else:
                order["status"] = "payment_failed"
                print(f"❌ Order {order_id} payment failed: {result['errors']}")
                
        except Exception as e:
            order["status"] = "verification_error"
            print(f"💥 Order {order_id} verification error: {str(e)}")

# Create coffee shop instance
coffee_shop = CoffeeShop("9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM")

if __name__ == "__main__":
    print("☕ Starting Coffee Shop Server")
    print("🌐 Server: http://localhost:8000")
    print("📋 API Docs: http://localhost:8000/docs")
    print("📱 Menu: http://localhost:8000/menu")
    
    uvicorn.run(coffee_shop.app, host="0.0.0.0", port=8000)
```

## Testing with Wallets

### Using the CLI Tool

```bash
# Create a payment URL
solana-pay create-url \
  --recipient 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM \
  --amount 0.01 \
  --label "Coffee Shop" \
  --message "Thanks for your purchase!"

# Parse a payment URL
solana-pay parse-url "solana:9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM?amount=0.01"

# Verify a payment
solana-pay verify \
  --signature your_transaction_signature_here \
  --recipient 9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM \
  --amount 0.01
```

### Testing Flow

1. **Create Order**: POST to `/order` with item name
2. **Get QR Code**: Use the returned payment URL to generate QR code
3. **Scan with Wallet**: Use Phantom, Solflare, or other Solana Pay compatible wallet
4. **Confirm Transaction**: Wallet will show transaction details
5. **Submit Payment**: Wallet submits transaction to blockchain
6. **Verify Payment**: Use transaction signature to verify payment

### Wallet Compatibility

The library is compatible with:
- **Phantom Wallet** ✅
- **Solflare Wallet** ✅
- **Backpack Wallet** ✅
- **Glow Wallet** ✅
- Any wallet supporting Solana Pay specification

## Production Deployment

### Environment Configuration

```bash
# .env file
SOLANA_PAY_CLUSTER=mainnet
SOLANA_PAY_RPC_ENDPOINT=https://your-rpc-provider.com
MERCHANT_RECIPIENT=your_mainnet_wallet_address
MERCHANT_LABEL="Your Business Name"
SOLANA_PAY_ENABLE_LOGGING=true
SOLANA_PAY_LOG_LEVEL=INFO
```

### Security Considerations

1. **Use HTTPS**: Always use HTTPS in production
2. **Rate Limiting**: Enable rate limiting to prevent abuse
3. **Input Validation**: Validate all inputs thoroughly
4. **Error Handling**: Don't expose internal errors to users
5. **Logging**: Log all transactions for audit purposes
6. **Monitoring**: Monitor for failed transactions and errors

### Deployment Example (Docker)

```dockerfile
FROM python:3.11-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

EXPOSE 8000

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Health Checks

```python
from solanapay import check_compatibility

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    compat = check_compatibility(warn_on_issues=False)
    
    return {
        "status": "healthy" if compat else "degraded",
        "timestamp": datetime.now().isoformat(),
        "version": __version__,
        "compatible": compat
    }
```

## Next Steps

- Explore [SPL Token payments](spl-tokens.md) for custom tokens
- Learn about [advanced validation](validation.md) techniques
- Check out [performance optimization](performance.md) tips
- Read about [error handling](error-handling.md) best practices

## Troubleshooting

See our [troubleshooting guide](troubleshooting.md) for common issues and solutions.