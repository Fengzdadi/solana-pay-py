#!/usr/bin/env python3
"""
One-click devnet setup script for Solana Pay Python.

This script helps you get started with Solana Pay on devnet by:
1. Checking system compatibility
2. Testing RPC connectivity
3. Providing setup instructions
4. Creating example configurations

Usage:
    python scripts/setup_devnet.py
"""

import asyncio
import json
import os
import sys
from pathlib import Path

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from solanapay import (
    check_compatibility,
    get_system_info,
    create_payment_url,
    SolanaPayClient
)
from solanapay.utils.rpc import create_rpc_client


async def check_rpc_connectivity():
    """Test RPC connectivity to devnet."""
    print("🌐 Testing RPC connectivity...")
    
    endpoints = [
        "https://api.devnet.solana.com",
        "https://devnet.helius-rpc.com",
    ]
    
    working_endpoints = []
    
    for endpoint in endpoints:
        try:
            async with create_rpc_client(endpoint, timeout=10) as rpc:
                slot = await rpc.get_slot()
                print(f"   ✅ {endpoint} - Current slot: {slot}")
                working_endpoints.append(endpoint)
        except Exception as e:
            print(f"   ❌ {endpoint} - Error: {str(e)[:50]}...")
    
    return working_endpoints


def create_env_file():
    """Create a .env file with devnet configuration."""
    env_content = """# Solana Pay Python - Devnet Configuration

# Solana Configuration
SOLANA_PAY_CLUSTER=devnet
SOLANA_PAY_COMMITMENT=confirmed
SOLANA_PAY_TIMEOUT=30
SOLANA_PAY_MAX_RETRIES=3

# Logging
SOLANA_PAY_ENABLE_LOGGING=true
SOLANA_PAY_LOG_LEVEL=INFO

# Server Configuration (for merchant examples)
HOST=0.0.0.0
PORT=8000

# Merchant Configuration (replace with your wallet address)
MERCHANT_RECIPIENT=9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM
MERCHANT_LABEL="Devnet Test Store"
MERCHANT_AMOUNT=0.01

# Custom RPC (optional - uncomment to use)
# SOLANA_PAY_DEVNET_RPC=https://api.devnet.solana.com
"""
    
    env_file = Path(".env")
    if env_file.exists():
        print(f"⚠️  .env file already exists at {env_file.absolute()}")
        response = input("   Overwrite? (y/N): ").strip().lower()
        if response != 'y':
            print("   Skipping .env file creation")
            return False
    
    with open(env_file, 'w') as f:
        f.write(env_content)
    
    print(f"✅ Created .env file at {env_file.absolute()}")
    return True


def create_example_config():
    """Create example configuration files."""
    config_dir = Path("config")
    config_dir.mkdir(exist_ok=True)
    
    # Merchant config
    merchant_config = {
        "label": "Devnet Test Store",
        "recipient": "9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
        "amount": "0.01",
        "memo": "Devnet test purchase",
        "cluster": "devnet"
    }
    
    with open(config_dir / "merchant.json", 'w') as f:
        json.dump(merchant_config, f, indent=2)
    
    # Test URLs config
    test_urls = {
        "sol_payment": create_payment_url(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount="0.01",
            label="SOL Test Payment"
        ),
        "usdc_payment": create_payment_url(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount="1.00",
            token="4zMMC9srt5Ri5X14GAgXhaHii3GnPAEERYPJgZJDncDU",  # Devnet USDC
            label="USDC Test Payment"
        )
    }
    
    with open(config_dir / "test_urls.json", 'w') as f:
        json.dump(test_urls, f, indent=2)
    
    print(f"✅ Created example configs in {config_dir.absolute()}/")


async def test_basic_functionality():
    """Test basic Solana Pay functionality."""
    print("🧪 Testing basic functionality...")
    
    try:
        # Test URL creation
        url = create_payment_url(
            recipient="9WzDXwBbmkg8ZTbNMqUxvQRAyrZzDsGYdLVL9zYtAWWM",
            amount="0.01",
            label="Test Payment"
        )
        print(f"   ✅ URL creation: {url[:50]}...")
        
        # Test client creation
        client = SolanaPayClient(rpc_endpoint="https://api.devnet.solana.com")
        print("   ✅ Client creation successful")
        
        # Test RPC connection
        status = await client.get_transaction_status("11111111111111111111111111111111111111111111111111111111111111111111111111111111111111111")
        print(f"   ✅ RPC connection: {status['exists']} (expected False)")
        
        return True
        
    except Exception as e:
        print(f"   ❌ Functionality test failed: {e}")
        return False


def print_next_steps():
    """Print next steps for the user."""
    print("\n" + "=" * 60)
    print("🎉 Devnet Setup Complete!")
    print("=" * 60)
    
    print("\n📋 Next Steps:")
    print("   1. Get a Solana wallet (Phantom, Solflare, etc.)")
    print("   2. Switch your wallet to Devnet")
    print("   3. Get devnet SOL from: https://faucet.solana.com/")
    print("   4. Update MERCHANT_RECIPIENT in .env with your wallet address")
    
    print("\n🚀 Try These Examples:")
    print("   # Simple payment")
    print("   python examples/simple_payment.py")
    print()
    print("   # SPL token payment")
    print("   python examples/spl_token_payment.py")
    print()
    print("   # Merchant server")
    print("   python examples/fastapi_merchant.py")
    
    print("\n🔧 CLI Tools:")
    print("   # Create payment URL")
    print("   solana-pay create-url --recipient YOUR_WALLET --amount 0.01")
    print()
    print("   # Check system compatibility")
    print("   solana-pay check-compat")
    print()
    print("   # Get system info")
    print("   solana-pay system-info")
    
    print("\n📚 Documentation:")
    print("   • API Docs: docs/api.md")
    print("   • Tutorial: docs/tutorial.md")
    print("   • Troubleshooting: docs/troubleshooting.md")
    
    print("\n💡 Tips:")
    print("   • Always test on devnet before mainnet")
    print("   • Use the CLI tools for quick testing")
    print("   • Check logs if something doesn't work")
    print("   • Join the Solana Discord for help")


async def main():
    """Main setup function."""
    print("🚀 Solana Pay Python - Devnet Setup")
    print("=" * 40)
    print()
    
    # Step 1: Check compatibility
    print("🔍 Step 1: Checking system compatibility...")
    is_compatible = check_compatibility(warn_on_issues=False)
    
    if is_compatible:
        print("   ✅ System is compatible!")
    else:
        print("   ⚠️  Compatibility issues detected")
        print("   Run 'solana-pay check-compat' for details")
    print()
    
    # Step 2: Test RPC connectivity
    print("🔍 Step 2: Testing RPC connectivity...")
    working_endpoints = await check_rpc_connectivity()
    
    if working_endpoints:
        print(f"   ✅ Found {len(working_endpoints)} working RPC endpoints")
    else:
        print("   ❌ No working RPC endpoints found")
        print("   Check your internet connection and try again")
        return
    print()
    
    # Step 3: Test basic functionality
    print("🔍 Step 3: Testing basic functionality...")
    functionality_ok = await test_basic_functionality()
    
    if not functionality_ok:
        print("   ❌ Basic functionality test failed")
        print("   Check the error messages above")
        return
    print()
    
    # Step 4: Create configuration files
    print("📝 Step 4: Creating configuration files...")
    create_env_file()
    create_example_config()
    print()
    
    # Step 5: Show system info
    print("📊 Step 5: System Information:")
    try:
        info = get_system_info()
        print(f"   Python: {info['python']['version'].split()[0]}")
        print(f"   Platform: {info['system']['platform']}")
        print(f"   Library: {info['library']['version']}")
        
        # Check dependencies
        deps = info.get('dependencies', {})
        working_deps = sum(1 for dep in deps.values() if dep.get('available', False))
        total_deps = len(deps)
        print(f"   Dependencies: {working_deps}/{total_deps} available")
        
    except Exception as e:
        print(f"   ⚠️  Could not get system info: {e}")
    
    print()
    
    # Final steps
    print_next_steps()


if __name__ == "__main__":
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n👋 Setup cancelled by user")
    except Exception as e:
        print(f"\n💥 Setup failed: {str(e)}")
        sys.exit(1)