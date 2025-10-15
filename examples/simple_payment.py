#!/usr/bin/env python3
"""
Simple payment example using Solana Pay Python.

This example demonstrates the basic flow:
1. Create a payment URL
2. Generate a QR code
3. Verify the payment after it's made

Usage:
    python examples/simple_payment.py
"""

import asyncio
import qrcode
from decimal import Decimal

# Add parent directory to path
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from solanapay import (
    create_payment_url,
    parse_payment_url,
    verify_payment,
    SolanaPayClient
)


def create_qr_code(url: str, filename: str = "payment_qr.png"):
    """Create a QR code for the payment URL."""
    qr = qrcode.QRCode(
        version=1,
        error_correction=qrcode.constants.ERROR_CORRECT_L,
        box_size=10,
        border=4,
    )
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"📱 QR code saved as: {filename}")
    return img


async def main():
    """Main example function."""
    print("🚀 Solana Pay Python - Simple Payment Example")
    print("=" * 50)
    
    # Configuration
    recipient = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Replace with your wallet
    amount = "0.01"  # 0.01 SOL
    label = "Simple Payment Demo"
    message = "Thanks for testing Solana Pay Python!"
    
    print(f"💰 Recipient: {recipient}")
    print(f"💵 Amount: {amount} SOL")
    print(f"🏷️  Label: {label}")
    print()
    
    # Step 1: Create payment URL
    print("📝 Step 1: Creating payment URL...")
    payment_url = create_payment_url(
        recipient=recipient,
        amount=amount,
        label=label,
        message=message
    )
    
    print(f"✅ Payment URL created:")
    print(f"   {payment_url}")
    print()
    
    # Step 2: Parse the URL to verify it's correct
    print("🔍 Step 2: Parsing payment URL...")
    parsed = parse_payment_url(payment_url)
    
    print(f"✅ Parsed URL:")
    print(f"   Recipient: {parsed['recipient']}")
    print(f"   Amount: {parsed['amount']} SOL")
    print(f"   Label: {parsed['label']}")
    print(f"   Message: {parsed['message']}")
    print()
    
    # Step 3: Generate QR code
    print("📱 Step 3: Generating QR code...")
    create_qr_code(payment_url, "simple_payment_qr.png")
    print()
    
    # Step 4: Wait for user to make payment
    print("⏳ Step 4: Waiting for payment...")
    print("   1. Scan the QR code with a Solana wallet (Phantom, Solflare, etc.)")
    print("   2. Confirm the transaction in your wallet")
    print("   3. Copy the transaction signature")
    print()
    
    # Get transaction signature from user
    signature = input("📋 Enter the transaction signature (or 'skip' to skip verification): ").strip()
    
    if signature.lower() == 'skip':
        print("⏭️  Skipping payment verification")
        return
    
    if not signature:
        print("❌ No signature provided, skipping verification")
        return
    
    # Step 5: Verify the payment
    print()
    print("🔍 Step 5: Verifying payment...")
    
    try:
        result = await verify_payment(
            signature=signature,
            expected_recipient=recipient,
            expected_amount=amount,
            timeout=60
        )
        
        print("📊 Verification Result:")
        if result["is_valid"]:
            print("   ✅ Payment verified successfully!")
            print(f"   💰 Amount: {amount} SOL")
            print(f"   📍 Recipient: {recipient}")
            print(f"   🔗 Signature: {signature}")
            print(f"   ⚡ Status: {result['confirmation_status']}")
        else:
            print("   ❌ Payment verification failed!")
            print("   Errors:")
            for error in result["errors"]:
                print(f"     • {error}")
            
            if result["warnings"]:
                print("   Warnings:")
                for warning in result["warnings"]:
                    print(f"     • {warning}")
    
    except Exception as e:
        print(f"   💥 Verification error: {str(e)}")
    
    print()
    print("🎉 Example completed!")


async def client_example():
    """Example using the high-level SolanaPayClient."""
    print("\n" + "=" * 50)
    print("🔧 High-Level Client Example")
    print("=" * 50)
    
    # Create client
    client = SolanaPayClient(rpc_endpoint="https://api.devnet.solana.com")
    
    # Create payment URL
    url = client.create_payment_url(
        recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        amount="0.005",
        label="Client Example",
        message="Testing the high-level client"
    )
    
    print(f"📝 Client URL: {url}")
    
    # Parse URL
    info = client.parse_payment_url(url)
    print(f"📋 Parsed: {info['amount']} SOL to {info['recipient']}")
    
    # Generate QR code
    create_qr_code(url, "client_example_qr.png")
    
    print("✅ Client example completed!")


if __name__ == "__main__":
    try:
        # Run main example
        asyncio.run(main())
        
        # Run client example
        asyncio.run(client_example())
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        sys.exit(1)