#!/usr/bin/env python3
"""
Stateful Solana Pay Merchant Server
Demonstrates proper order management and QR code generation
"""

from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import JSONResponse
from pydantic import BaseModel
import uvicorn
import uuid
from datetime import datetime, timedelta
from typing import Dict, Any, Optional
import asyncio

# Order state management (in production, use a database)
orders: Dict[str, Dict[str, Any]] = {}

app = FastAPI(title="Solana Pay Merchant with State Management")

class CreateOrderRequest(BaseModel):
    amount: float
    recipient: str
    label: Optional[str] = "Payment"
    memo: Optional[str] = None

class TransactionRequest(BaseModel):
    account: str

@app.get("/")
async def root():
    """API information"""
    return {
        "name": "Solana Pay Merchant Server",
        "version": "1.0.0",
        "endpoints": {
            "create_order": "POST /create-order",
            "payment_info": "GET /pay/{order_id}",
            "create_transaction": "POST /pay/{order_id}",
            "order_status": "GET /orders/{order_id}/status"
        },
        "active_orders": len(orders)
    }

@app.post("/create-order")
async def create_order(request: CreateOrderRequest):
    """Create a new payment order"""
    order_id = str(uuid.uuid4())[:8]
    
    orders[order_id] = {
        "id": order_id,
        "amount": request.amount,
        "recipient": request.recipient,
        "label": request.label,
        "memo": request.memo,
        "status": "created",
        "created_at": datetime.now(),
        "expires_at": datetime.now() + timedelta(minutes=5),
        "payer": None,
        "transaction_signature": None
    }
    
    # Return the payment URL (this would be your actual domain in production)
    base_url = "http://localhost:8000"  # In production: https://yourdomain.com
    payment_url = f"{base_url}/pay/{order_id}"
    
    return {
        "order_id": order_id,
        "payment_url": payment_url,
        "qr_data": payment_url,
        "amount": request.amount,
        "recipient": request.recipient,
        "expires_in": 300,  # 5 minutes
        "expires_at": orders[order_id]["expires_at"].isoformat()
    }

@app.get("/pay/{order_id}")
async def get_payment_info(order_id: str):
    """Transaction request endpoint - what wallets call first"""
    
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders[order_id]
    
    # Check if order expired
    if datetime.now() > order["expires_at"]:
        order["status"] = "expired"
        raise HTTPException(status_code=410, detail="Order expired")
    
    # Return transaction metadata (required by Solana Pay spec)
    return {
        "label": order["label"] or f"Order #{order_id}",
        "icon": "https://solana.com/favicon.ico"  # Optional merchant icon
    }

@app.post("/pay/{order_id}")
async def create_transaction(order_id: str, request: TransactionRequest):
    """Create transaction for the order - what wallets call to get the transaction"""
    
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders[order_id]
    
    # Check if order expired
    if datetime.now() > order["expires_at"]:
        order["status"] = "expired"
        raise HTTPException(status_code=410, detail="Order expired")
    
    # Check if already processed
    if order["status"] == "completed":
        raise HTTPException(status_code=409, detail="Order already completed")
    
    # Build fresh transaction
    try:
        from solanapay.tx_builders.transfer import build_transfer_tx
        from solana.rpc.async_api import AsyncClient
        from decimal import Decimal
        
        rpc = AsyncClient("https://api.devnet.solana.com")
        
        tx_b64 = await build_transfer_tx(
            rpc,
            payer=request.account,  # Wallet's public key
            recipient=order["recipient"],
            amount=Decimal(str(order["amount"])),
            memo=order["memo"] or f"Order {order_id}"
        )
        
        # Update order status
        order["status"] = "pending"
        order["payer"] = request.account
        
        await rpc.close()
        
        print(f"✅ Transaction created for order {order_id}")
        print(f"   Payer: {request.account}")
        print(f"   Amount: {order['amount']} SOL")
        
        return {
            "transaction": tx_b64,
            "message": order["label"] or f"Payment for Order #{order_id}"
        }
        
    except Exception as e:
        if 'rpc' in locals():
            await rpc.close()
        print(f"❌ Failed to create transaction for order {order_id}: {str(e)}")
        raise HTTPException(status_code=400, detail=f"Failed to create transaction: {str(e)}")

@app.get("/orders/{order_id}/status")
async def get_order_status(order_id: str):
    """Check order status"""
    if order_id not in orders:
        raise HTTPException(status_code=404, detail="Order not found")
    
    order = orders[order_id].copy()
    
    # Check if expired
    if datetime.now() > order["expires_at"] and order["status"] not in ["completed", "expired"]:
        order["status"] = "expired"
        orders[order_id]["status"] = "expired"
    
    # Convert datetime to string for JSON serialization
    order["created_at"] = order["created_at"].isoformat()
    order["expires_at"] = order["expires_at"].isoformat()
    
    return order

@app.get("/orders")
async def list_orders():
    """List all orders (for debugging)"""
    result = []
    for order_id, order in orders.items():
        order_copy = order.copy()
        order_copy["created_at"] = order_copy["created_at"].isoformat()
        order_copy["expires_at"] = order_copy["expires_at"].isoformat()
        result.append(order_copy)
    
    return {"orders": result, "total": len(result)}

if __name__ == "__main__":
    print("🚀 Starting Stateful Solana Pay Merchant Server...")
    print("📱 API docs at: http://localhost:8000/docs")
    print("📦 Create orders at: http://localhost:8000/create-order")
    print("📊 View orders at: http://localhost:8000/orders")
    uvicorn.run(app, host="0.0.0.0", port=8000)