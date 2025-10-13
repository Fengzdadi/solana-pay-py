"""Command-line interface for Solana Pay Python library."""

from __future__ import annotations

import argparse
import asyncio
import json
import sys
from decimal import Decimal
from typing import Optional

from . import (
    __version__,
    create_payment_url,
    parse_payment_url,
    create_payment_transaction,
    verify_payment,
    get_compatibility_report,
    get_system_info,
)
from .utils import setup_logging


def create_parser() -> argparse.ArgumentParser:
    """Create the command-line argument parser."""
    parser = argparse.ArgumentParser(
        prog="solana-pay",
        description="Solana Pay Python CLI utility",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Create a payment URL
  solana-pay create-url --recipient 9Wz... --amount 0.01 --label "Coffee"
  
  # Parse a payment URL
  solana-pay parse-url "solana:9Wz...?amount=0.01"
  
  # Check system compatibility
  solana-pay check-compat
  
  # Get system information
  solana-pay system-info
        """
    )
    
    parser.add_argument(
        "--version",
        action="version",
        version=f"Solana Pay Python {__version__}"
    )
    
    parser.add_argument(
        "--verbose", "-v",
        action="store_true",
        help="Enable verbose logging"
    )
    
    subparsers = parser.add_subparsers(dest="command", help="Available commands")
    
    # Create URL command
    create_url_parser = subparsers.add_parser(
        "create-url",
        help="Create a Solana Pay URL"
    )
    create_url_parser.add_argument(
        "--recipient", "-r",
        required=True,
        help="Recipient public key (base58)"
    )
    create_url_parser.add_argument(
        "--amount", "-a",
        help="Payment amount (e.g., 0.01)"
    )
    create_url_parser.add_argument(
        "--token", "-t",
        help="SPL token mint address (omit for SOL)"
    )
    create_url_parser.add_argument(
        "--label", "-l",
        help="Human-readable label"
    )
    create_url_parser.add_argument(
        "--message", "-m",
        help="Payment message"
    )
    create_url_parser.add_argument(
        "--memo",
        help="On-chain memo"
    )
    create_url_parser.add_argument(
        "--reference",
        action="append",
        help="Reference public key (can be used multiple times)"
    )
    
    # Parse URL command
    parse_url_parser = subparsers.add_parser(
        "parse-url",
        help="Parse a Solana Pay URL"
    )
    parse_url_parser.add_argument(
        "url",
        help="Solana Pay URL to parse"
    )
    parse_url_parser.add_argument(
        "--format", "-f",
        choices=["json", "pretty"],
        default="pretty",
        help="Output format"
    )
    
    # Create transaction command
    create_tx_parser = subparsers.add_parser(
        "create-tx",
        help="Create a payment transaction"
    )
    create_tx_parser.add_argument(
        "--payer", "-p",
        required=True,
        help="Payer public key (base58)"
    )
    create_tx_parser.add_argument(
        "--recipient", "-r",
        required=True,
        help="Recipient public key (base58)"
    )
    create_tx_parser.add_argument(
        "--amount", "-a",
        required=True,
        help="Payment amount"
    )
    create_tx_parser.add_argument(
        "--token", "-t",
        help="SPL token mint address (omit for SOL)"
    )
    create_tx_parser.add_argument(
        "--memo",
        help="On-chain memo"
    )
    create_tx_parser.add_argument(
        "--rpc",
        help="Custom RPC endpoint"
    )
    
    # Verify payment command
    verify_parser = subparsers.add_parser(
        "verify",
        help="Verify a payment transaction"
    )
    verify_parser.add_argument(
        "--signature", "-s",
        required=True,
        help="Transaction signature"
    )
    verify_parser.add_argument(
        "--recipient", "-r",
        required=True,
        help="Expected recipient public key"
    )
    verify_parser.add_argument(
        "--amount", "-a",
        required=True,
        help="Expected payment amount"
    )
    verify_parser.add_argument(
        "--token", "-t",
        help="Expected SPL token mint address"
    )
    verify_parser.add_argument(
        "--memo",
        help="Expected memo"
    )
    verify_parser.add_argument(
        "--timeout",
        type=int,
        default=60,
        help="Verification timeout in seconds"
    )
    verify_parser.add_argument(
        "--rpc",
        help="Custom RPC endpoint"
    )
    
    # System info command
    subparsers.add_parser(
        "system-info",
        help="Show system information"
    )
    
    # Compatibility check command
    subparsers.add_parser(
        "check-compat",
        help="Check system compatibility"
    )
    
    return parser


async def handle_create_url(args) -> int:
    """Handle create-url command."""
    try:
        url = create_payment_url(
            recipient=args.recipient,
            amount=args.amount,
            token=args.token,
            label=args.label,
            message=args.message,
            memo=args.memo,
            references=args.reference
        )
        print(url)
        return 0
    except Exception as e:
        print(f"Error creating URL: {e}", file=sys.stderr)
        return 1


async def handle_parse_url(args) -> int:
    """Handle parse-url command."""
    try:
        parsed = parse_payment_url(args.url)
        
        if args.format == "json":
            print(json.dumps(parsed, indent=2))
        else:
            print("Parsed Solana Pay URL:")
            print(f"  Recipient: {parsed['recipient']}")
            if parsed['amount']:
                print(f"  Amount: {parsed['amount']}")
            if parsed['token']:
                print(f"  Token: {parsed['token']}")
            if parsed['label']:
                print(f"  Label: {parsed['label']}")
            if parsed['message']:
                print(f"  Message: {parsed['message']}")
            if parsed['memo']:
                print(f"  Memo: {parsed['memo']}")
            if parsed['references']:
                print(f"  References: {', '.join(parsed['references'])}")
        
        return 0
    except Exception as e:
        print(f"Error parsing URL: {e}", file=sys.stderr)
        return 1


async def handle_create_tx(args) -> int:
    """Handle create-tx command."""
    try:
        transaction = await create_payment_transaction(
            payer=args.payer,
            recipient=args.recipient,
            amount=args.amount,
            token=args.token,
            memo=args.memo,
            rpc_endpoint=args.rpc
        )
        print(transaction)
        return 0
    except Exception as e:
        print(f"Error creating transaction: {e}", file=sys.stderr)
        return 1


async def handle_verify(args) -> int:
    """Handle verify command."""
    try:
        result = await verify_payment(
            signature=args.signature,
            expected_recipient=args.recipient,
            expected_amount=args.amount,
            expected_token=args.token,
            expected_memo=args.memo,
            timeout=args.timeout,
            rpc_endpoint=args.rpc
        )
        
        print("Payment Verification Result:")
        print(f"  Valid: {'✅ Yes' if result['is_valid'] else '❌ No'}")
        print(f"  Recipient Match: {'✅' if result['recipient_match'] else '❌'}")
        print(f"  Amount Match: {'✅' if result['amount_match'] else '❌'}")
        print(f"  Memo Match: {'✅' if result['memo_match'] else '❌'}")
        print(f"  References Match: {'✅' if result['references_match'] else '❌'}")
        print(f"  Confirmation Status: {result['confirmation_status']}")
        
        if result['errors']:
            print("  Errors:")
            for error in result['errors']:
                print(f"    • {error}")
        
        if result['warnings']:
            print("  Warnings:")
            for warning in result['warnings']:
                print(f"    • {warning}")
        
        return 0 if result['is_valid'] else 1
    except Exception as e:
        print(f"Error verifying payment: {e}", file=sys.stderr)
        return 1


async def handle_system_info(args) -> int:
    """Handle system-info command."""
    try:
        info = get_system_info()
        print(json.dumps(info, indent=2, default=str))
        return 0
    except Exception as e:
        print(f"Error getting system info: {e}", file=sys.stderr)
        return 1


async def handle_check_compat(args) -> int:
    """Handle check-compat command."""
    try:
        report = get_compatibility_report()
        print(report)
        return 0
    except Exception as e:
        print(f"Error checking compatibility: {e}", file=sys.stderr)
        return 1


async def main() -> int:
    """Main CLI entry point."""
    parser = create_parser()
    args = parser.parse_args()
    
    # Set up logging
    if args.verbose:
        setup_logging(level="DEBUG")
    
    # Handle commands
    if args.command == "create-url":
        return await handle_create_url(args)
    elif args.command == "parse-url":
        return await handle_parse_url(args)
    elif args.command == "create-tx":
        return await handle_create_tx(args)
    elif args.command == "verify":
        return await handle_verify(args)
    elif args.command == "system-info":
        return await handle_system_info(args)
    elif args.command == "check-compat":
        return await handle_check_compat(args)
    else:
        parser.print_help()
        return 1


def cli_main():
    """Synchronous CLI entry point."""
    try:
        return asyncio.run(main())
    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        return 130
    except Exception as e:
        print(f"Unexpected error: {e}", file=sys.stderr)
        return 1


if __name__ == "__main__":
    sys.exit(cli_main())