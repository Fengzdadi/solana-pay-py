#!/usr/bin/env python3
"""
SPL Token payment example using Solana Pay Python.

This example demonstrates how to create payments for SPL tokens (like USDC).

Usage:
    python examples/spl_token_payment.py
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
    create_payment_transaction,
    verify_payment,
    TransferRequest,
    TransactionOptions
)
from solanapay.utils.rpc import create_rpc_client


# Common SPL token mints (devnet)
TOKENS = {
    "USDC": "4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",  # Devnet USDC
    "USDT": "EJwZgeZrdC8TXTQbQBoL6bfuAnFUUy1PVCMB4DYPzVaS",  # Devnet USDT (example)
}


def create_qr_code(url: str, filename: str):
    """Create a QR code for the payment URL."""
    qr = qrcode.QRCode(version=1, box_size=10, border=4)
    qr.add_data(url)
    qr.make(fit=True)
    
    img = qr.make_image(fill_color="black", back_color="white")
    img.save(filename)
    print(f"📱 QR code saved as: {filename}")


async def get_token_info(mint_address: str):
    """Get information about an SPL token."""
    try:
        async with create_rpc_client("https://api.devnet.solana.com") as rpc:
            from solders.pubkey import Pubkey
            
            mint = Pubkey.from_string(mint_address)
            supply_info = await rpc.get_token_supply(mint)
            
            return {
                "mint": mint_address,
                "decimals": supply_info.value.decimals,
                "supply": supply_info.value.ui_amount
            }
    except Exception as e:
        print(f"❌ Error getting token info: {e}")
        return None


async def spl_payment_example():
    """Example of creating SPL token payment."""
    print("🪙 Solana Pay Python - SPL Token Payment Example")
    print("=" * 55)
    
    # Configuration
    recipient = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Replace with your wallet
    token_mint = TOKENS["USDC"]  # USDC on devnet
    amount = "1.50"  # 1.50 USDC
    
    print(f"💰 Recipient: {recipient}")
    print(f"🪙 Token: USDC (devnet)")
    print(f"🏷️  Mint: {token_mint}")
    print(f"💵 Amount: {amount} USDC")
    print()
    
    # Get token information
    print("🔍 Getting token information...")
    token_info = await get_token_info(token_mint)
    
    if token_info:
        print(f"✅ Token Info:")
        print(f"   Decimals: {token_info['decimals']}")
        print(f"   Total Supply: {token_info['supply']:,.0f}")
    else:
        print("⚠️  Could not fetch token info, continuing anyway...")
    print()
    
    # Create payment URL
    print("📝 Creating SPL token payment URL...")
    payment_url = create_payment_url(
        recipient=recipient,
        amount=amount,
        token=token_mint,  # This makes it an SPL token payment
        label="USDC Payment Demo",
        message="Thanks for testing SPL token payments!"
    )
    
    print(f"✅ Payment URL created:")
    print(f"   {payment_url}")
    print()
    
    # Generate QR code
    print("📱 Generating QR code...")
    create_qr_code(payment_url, "usdc_payment_qr.png")
    print()
    
    # Show instructions
    print("📋 Instructions:")
    print("   1. Make sure you have USDC in your devnet wallet")
    print("   2. Get devnet USDC from: https://spl-token-faucet.com/")
    print("   3. Scan the QR code with your wallet")
    print("   4. Confirm the USDC transfer")
    print()
    
    # Wait for payment
    signature = input("📋 Enter transaction signature (or 'skip'): ").strip()
    
    if signature.lower() == 'skip':
        print("⏭️  Skipping verification")
        return
    
    # Verify payment
    print("\n🔍 Verifying SPL token payment...")
    
    try:
        result = await verify_payment(
            signature=signature,
            expected_recipient=recipient,
            expected_amount=amount,
            expected_token=token_mint,  # Verify it's the right token
            timeout=60
        )
        
        if result["is_valid"]:
            print("✅ SPL token payment verified!")
            print(f"   💰 Amount: {amount} USDC")
            print(f"   🪙 Token: {token_mint}")
            print(f"   📍 Recipient: {recipient}")
            print(f"   ⚡ Status: {result['confirmation_status']}")
        else:
            print("❌ Payment verification failed!")
            for error in result["errors"]:
                print(f"   • {error}")
    
    except Exception as e:
        print(f"💥 Verification error: {e}")


async def create_spl_transaction_example():
    """Example of creating SPL token transaction programmatically."""
    print("\n" + "=" * 55)
    print("🔧 SPL Token Transaction Building Example")
    print("=" * 55)
    
    payer = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Replace with payer
    recipient = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"  # Replace with recipient
    
    print("🔨 Building SPL token transaction...")
    
    try:
        # Create transaction
        transaction = await create_payment_transaction(
            payer=payer,
            recipient=recipient,
            amount="0.50",  # 0.50 USDC
            token=TOKENS["USDC"],
            memo="Programmatic USDC transfer",
            auto_create_ata=True  # Automatically create recipient's token account
        )
        
        print("✅ Transaction created successfully!")
        print(f"📦 Transaction (first 50 chars): {transaction[:50]}...")
        print(f"📏 Transaction length: {len(transaction)} characters")
        
        print("\n📋 Next steps:")
        print("   1. Sign this transaction with the payer's private key")
        print("   2. Submit to the Solana network")
        print("   3. Wait for confirmation")
        
    except Exception as e:
        print(f"❌ Transaction creation failed: {e}")


async def multi_token_example():
    """Example showing multiple token types."""
    print("\n" + "=" * 55)
    print("🎯 Multiple Token Types Example")
    print("=" * 55)
    
    recipient = "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM"
    
    # Create URLs for different tokens
    payments = [
        {
            "name": "SOL Payment",
            "amount": "0.01",
            "token": None,  # None = SOL
            "filename": "sol_payment.png"
        },
        {
            "name": "USDC Payment", 
            "amount": "1.00",
            "token": TOKENS["USDC"],
            "filename": "usdc_payment.png"
        }
    ]
    
    for payment in payments:
        print(f"\n💰 Creating {payment['name']}...")
        
        url = create_payment_url(
            recipient=recipient,
            amount=payment["amount"],
            token=payment["token"],
            label=payment["name"],
            message=f"Pay {payment['amount']} {payment['name'].split()[0]}"
        )
        
        create_qr_code(url, payment["filename"])
        
        print(f"   ✅ {payment['name']} QR code: {payment['filename']}")
        print(f"   🔗 URL: {url}")
    
    print(f"\n🎉 Created {len(payments)} different payment types!")


if __name__ == "__main__":
    try:
        # Run SPL payment example
        asyncio.run(spl_payment_example())
        
        # Run transaction building example
        asyncio.run(create_spl_transaction_example())
        
        # Run multi-token example
        asyncio.run(multi_token_example())
        
        print("\n🎉 All SPL token examples completed!")
        
    except KeyboardInterrupt:
        print("\n👋 Goodbye!")
    except Exception as e:
        print(f"\n💥 Error: {str(e)}")
        sys.exit(1)