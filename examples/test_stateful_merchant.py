#!/usr/bin/env python3
"""
Test script for the stateful merchant server
"""

import requests
import qrcode
import time
import json

def create_order_and_qr():
    """Create an order and generate QR code"""
    
    print("🛒 Creating a new order...")
    
    # Create order
    response = requests.post("http://localhost:8000/create-order", json={
        "amount": 0.001,  # Small amount for testing
        "recipient": "YOUR_RECIPIENT_ADDRESS_HERE",
        "label": "Test Coffee ☕",
        "memo": "Stateful payment test"
    })
    
    if response.status_code != 200:
        print(f"❌ Failed to create order: {response.text}")
        return
    
    order = response.json()
    print(f"✅ Order created successfully!")
    print(f"   Order ID: {order['order_id']}")
    print(f"   Amount: {order['amount']} SOL")
    print(f"   Payment URL: {order['payment_url']}")
    print(f"   Expires in: {order['expires_in']} seconds")
    
    # Generate QR code
    print("\n📱 Generating QR code...")
    qr = qrcode.QRCode(version=1, box_size=10, border=5)
    qr.add_data(order['payment_url'])
    qr.make(fit=True)
    
    print("\n" + "="*50)
    print("📱 SCAN THIS QR CODE WITH YOUR SOLANA WALLET:")
    print("="*50)
    qr.print_ascii()
    print("="*50)
    
    print(f"\n🔗 Or manually enter this URL in your wallet:")
    print(f"   {order['payment_url']}")
    
    # Monitor order status
    print(f"\n👀 Monitoring order status...")
    order_id = order['order_id']
    
    for i in range(30):  # Monitor for 30 seconds
        try:
            status_response = requests.get(f"http://localhost:8000/orders/{order_id}/status")
            if status_response.status_code == 200:
                status = status_response.json()
                print(f"   Status: {status['status']} (check #{i+1})")
                
                if status['status'] in ['completed', 'expired']:
                    break
                    
            time.sleep(1)
        except KeyboardInterrupt:
            print("\n⏹️  Monitoring stopped by user")
            break
        except Exception as e:
            print(f"   Error checking status: {e}")
    
    # Final status
    try:
        final_response = requests.get(f"http://localhost:8000/orders/{order_id}/status")
        if final_response.status_code == 200:
            final_status = final_response.json()
            print(f"\n📊 Final order status:")
            print(json.dumps(final_status, indent=2))
    except Exception as e:
        print(f"❌ Could not get final status: {e}")

def list_orders():
    """List all orders"""
    try:
        response = requests.get("http://localhost:8000/orders")
        if response.status_code == 200:
            data = response.json()
            print(f"📋 Found {data['total']} orders:")
            for order in data['orders']:
                print(f"   {order['id']}: {order['status']} - {order['amount']} SOL")
        else:
            print(f"❌ Failed to get orders: {response.text}")
    except Exception as e:
        print(f"❌ Error: {e}")

if __name__ == "__main__":
    print("🧪 Solana Pay Stateful Merchant Test")
    print("="*40)
    
    # Check if server is running
    try:
        response = requests.get("http://localhost:8000/")
        if response.status_code == 200:
            print("✅ Server is running")
        else:
            print("❌ Server responded with error")
            exit(1)
    except Exception as e:
        print("❌ Server is not running. Start it with:")
        print("   uv run python examples/stateful_merchant.py")
        exit(1)
    
    print("\nChoose an option:")
    print("1. Create order and generate QR code")
    print("2. List all orders")
    
    choice = input("\nEnter choice (1 or 2): ").strip()
    
    if choice == "1":
        create_order_and_qr()
    elif choice == "2":
        list_orders()
    else:
        print("Invalid choice")