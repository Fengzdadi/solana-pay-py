"""Debugging utilities for Solana Pay operations."""

from __future__ import annotations

import json
import pprint
from typing import Any, Dict, Optional, List
from decimal import Decimal

from solana.rpc.async_api import AsyncClient
from solders.pubkey import Pubkey
from solders.signature import Signature

from .logging import get_logger
from .errors import SolanaPayError

logger = get_logger(__name__)


class TransactionDebugger:
    """Utility for debugging Solana transactions."""
    
    def __init__(self, rpc_client: AsyncClient):
        self.rpc = rpc_client
    
    async def debug_transaction(self, signature: str) -> Dict[str, Any]:
        """Get comprehensive debug information for a transaction.
        
        Args:
            signature: Transaction signature to debug
            
        Returns:
            Dictionary containing debug information
        """
        debug_info = {
            "signature": signature,
            "transaction_data": None,
            "account_info": {},
            "balance_changes": {},
            "instruction_analysis": [],
            "errors": []
        }
        
        try:
            # Get transaction data
            sig_obj = Signature.from_string(signature)
            tx_response = await self.rpc.get_transaction(
                sig_obj,
                max_supported_transaction_version=0
            )
            
            if tx_response.value is None:
                debug_info["errors"].append("Transaction not found")
                return debug_info
            
            tx_data = tx_response.value
            debug_info["transaction_data"] = self._serialize_transaction_data(tx_data)
            
            # Analyze instructions
            debug_info["instruction_analysis"] = self._analyze_instructions(tx_data)
            
            # Calculate balance changes
            debug_info["balance_changes"] = self._calculate_balance_changes(tx_data)
            
            # Get account information
            accounts = self._extract_accounts(tx_data)
            for account in accounts:
                try:
                    account_info = await self.rpc.get_account_info(Pubkey.from_string(account))
                    debug_info["account_info"][account] = self._serialize_account_info(account_info.value)
                except Exception as e:
                    debug_info["account_info"][account] = f"Error: {str(e)}"
            
        except Exception as e:
            debug_info["errors"].append(f"Debug error: {str(e)}")
        
        return debug_info
    
    def _serialize_transaction_data(self, tx_data: Any) -> Dict[str, Any]:
        """Serialize transaction data for debugging."""
        try:
            # Convert to dict and handle special types
            serialized = {}
            
            if hasattr(tx_data, '__dict__'):
                for key, value in tx_data.__dict__.items():
                    serialized[key] = self._serialize_value(value)
            else:
                serialized = self._serialize_value(tx_data)
            
            return serialized
        except Exception as e:
            return {"error": f"Serialization failed: {str(e)}"}
    
    def _serialize_account_info(self, account_info: Any) -> Dict[str, Any]:
        """Serialize account info for debugging."""
        if account_info is None:
            return {"exists": False}
        
        try:
            return {
                "exists": True,
                "lamports": account_info.lamports,
                "owner": str(account_info.owner),
                "executable": account_info.executable,
                "rent_epoch": account_info.rent_epoch,
                "data_length": len(account_info.data) if account_info.data else 0
            }
        except Exception as e:
            return {"error": f"Account info serialization failed: {str(e)}"}
    
    def _serialize_value(self, value: Any) -> Any:
        """Serialize a value for JSON compatibility."""
        if value is None:
            return None
        elif isinstance(value, (str, int, float, bool)):
            return value
        elif isinstance(value, Decimal):
            return str(value)
        elif hasattr(value, '__str__'):
            return str(value)
        elif isinstance(value, (list, tuple)):
            return [self._serialize_value(item) for item in value]
        elif isinstance(value, dict):
            return {k: self._serialize_value(v) for k, v in value.items()}
        else:
            return str(value)
    
    def _analyze_instructions(self, tx_data: Any) -> List[Dict[str, Any]]:
        """Analyze transaction instructions."""
        instructions = []
        
        try:
            transaction = getattr(tx_data, 'transaction', {})
            message = getattr(transaction, 'message', {})
            tx_instructions = getattr(message, 'instructions', [])
            account_keys = getattr(message, 'accountKeys', [])
            
            for i, instruction in enumerate(tx_instructions):
                analysis = {
                    "index": i,
                    "program_id_index": getattr(instruction, 'programIdIndex', None),
                    "program_id": None,
                    "accounts": getattr(instruction, 'accounts', []),
                    "data": getattr(instruction, 'data', ''),
                    "analysis": "Unknown instruction"
                }
                
                # Get program ID
                if analysis["program_id_index"] is not None and analysis["program_id_index"] < len(account_keys):
                    analysis["program_id"] = str(account_keys[analysis["program_id_index"]])
                    analysis["analysis"] = self._analyze_instruction_type(analysis["program_id"])
                
                instructions.append(analysis)
        
        except Exception as e:
            instructions.append({"error": f"Instruction analysis failed: {str(e)}"})
        
        return instructions
    
    def _analyze_instruction_type(self, program_id: str) -> str:
        """Analyze instruction type based on program ID."""
        known_programs = {
            "11111111111111111111111111111112": "System Program",
            "TokenkegQfeZyiNwAJbNbGKPFXCWuBvf9Ss623VQ5DA": "SPL Token Program",
            "ATokenGPvbdGVxr1b2hvZbsiqW5xWH25efTNsLJA8knL": "Associated Token Program",
            "MemoSq4gqABAXKb96qnH8TysNcWxMyWCqXgDLGmfcHr": "Memo Program",
        }
        
        return known_programs.get(program_id, f"Unknown Program ({program_id})")
    
    def _calculate_balance_changes(self, tx_data: Any) -> Dict[str, Any]:
        """Calculate balance changes from transaction."""
        changes = {}
        
        try:
            meta = getattr(tx_data, 'meta', {})
            pre_balances = getattr(meta, 'preBalances', [])
            post_balances = getattr(meta, 'postBalances', [])
            
            transaction = getattr(tx_data, 'transaction', {})
            message = getattr(transaction, 'message', {})
            account_keys = getattr(message, 'accountKeys', [])
            
            for i, (pre, post) in enumerate(zip(pre_balances, post_balances)):
                if i < len(account_keys):
                    account = str(account_keys[i])
                    change = post - pre
                    changes[account] = {
                        "pre_balance": pre,
                        "post_balance": post,
                        "change": change,
                        "change_sol": change / 1_000_000_000  # Convert to SOL
                    }
        
        except Exception as e:
            changes["error"] = f"Balance calculation failed: {str(e)}"
        
        return changes
    
    def _extract_accounts(self, tx_data: Any) -> List[str]:
        """Extract all accounts from transaction."""
        accounts = []
        
        try:
            transaction = getattr(tx_data, 'transaction', {})
            message = getattr(transaction, 'message', {})
            account_keys = getattr(message, 'accountKeys', [])
            
            accounts = [str(key) for key in account_keys]
        
        except Exception as e:
            logger.error(f"Failed to extract accounts: {e}")
        
        return accounts


class PaymentDebugger:
    """Utility for debugging Solana Pay payment flows."""
    
    def __init__(self, rpc_client: AsyncClient):
        self.rpc = rpc_client
        self.tx_debugger = TransactionDebugger(rpc_client)
    
    async def debug_payment_flow(
        self,
        signature: str,
        expected_recipient: str,
        expected_amount: Optional[Decimal] = None,
        expected_token: Optional[str] = None
    ) -> Dict[str, Any]:
        """Debug a complete payment flow.
        
        Args:
            signature: Transaction signature
            expected_recipient: Expected payment recipient
            expected_amount: Expected payment amount
            expected_token: Expected token mint (None for SOL)
            
        Returns:
            Comprehensive debug information
        """
        debug_info = {
            "payment_analysis": {
                "expected_recipient": expected_recipient,
                "expected_amount": str(expected_amount) if expected_amount else None,
                "expected_token": expected_token,
                "payment_found": False,
                "amount_match": False,
                "recipient_match": False,
                "issues": []
            }
        }
        
        # Get transaction debug info
        tx_debug = await self.tx_debugger.debug_transaction(signature)
        debug_info["transaction_debug"] = tx_debug
        
        # Analyze payment
        if tx_debug.get("balance_changes"):
            self._analyze_payment(debug_info, tx_debug, expected_recipient, expected_amount)
        
        return debug_info
    
    def _analyze_payment(
        self,
        debug_info: Dict[str, Any],
        tx_debug: Dict[str, Any],
        expected_recipient: str,
        expected_amount: Optional[Decimal]
    ):
        """Analyze payment details."""
        payment_analysis = debug_info["payment_analysis"]
        balance_changes = tx_debug.get("balance_changes", {})
        
        # Check if recipient received payment
        if expected_recipient in balance_changes:
            recipient_change = balance_changes[expected_recipient]
            if recipient_change["change"] > 0:
                payment_analysis["payment_found"] = True
                payment_analysis["recipient_match"] = True
                payment_analysis["actual_amount_sol"] = recipient_change["change_sol"]
                
                # Check amount if expected
                if expected_amount is not None:
                    expected_sol = float(expected_amount)
                    actual_sol = recipient_change["change_sol"]
                    tolerance = 0.000001  # 1 microSOL
                    
                    if abs(actual_sol - expected_sol) <= tolerance:
                        payment_analysis["amount_match"] = True
                    else:
                        payment_analysis["issues"].append(
                            f"Amount mismatch: expected {expected_sol} SOL, got {actual_sol} SOL"
                        )
            else:
                payment_analysis["issues"].append("Recipient balance decreased or unchanged")
        else:
            payment_analysis["issues"].append("Recipient not found in transaction")


def format_debug_output(debug_data: Dict[str, Any], format_type: str = "pretty") -> str:
    """Format debug data for output.
    
    Args:
        debug_data: Debug data to format
        format_type: Format type ("pretty", "json", "compact")
        
    Returns:
        Formatted debug output
    """
    if format_type == "json":
        return json.dumps(debug_data, indent=2, default=str)
    elif format_type == "compact":
        return json.dumps(debug_data, separators=(',', ':'), default=str)
    else:  # pretty
        return pprint.pformat(debug_data, width=100, depth=10)


def create_debug_report(
    operation: str,
    inputs: Dict[str, Any],
    outputs: Optional[Dict[str, Any]] = None,
    error: Optional[Exception] = None,
    context: Optional[Dict[str, Any]] = None
) -> Dict[str, Any]:
    """Create a comprehensive debug report.
    
    Args:
        operation: Name of the operation
        inputs: Input parameters
        outputs: Output results (if successful)
        error: Exception that occurred (if failed)
        context: Additional context information
        
    Returns:
        Debug report
    """
    import time
    
    report = {
        "timestamp": time.time(),
        "operation": operation,
        "inputs": inputs,
        "success": error is None,
    }
    
    if outputs is not None:
        report["outputs"] = outputs
    
    if error is not None:
        report["error"] = {
            "type": type(error).__name__,
            "message": str(error),
        }
        
        if isinstance(error, SolanaPayError):
            report["error"]["code"] = error.error_code
            report["error"]["context"] = error.context
    
    if context:
        report["context"] = context
    
    return report


class DebugSession:
    """Debug session for tracking multiple operations."""
    
    def __init__(self, session_name: str):
        self.session_name = session_name
        self.operations: List[Dict[str, Any]] = []
        self.start_time = None
    
    def start(self):
        """Start the debug session."""
        import time
        self.start_time = time.time()
        logger.info(f"Started debug session: {self.session_name}")
    
    def add_operation(
        self,
        operation: str,
        inputs: Dict[str, Any],
        outputs: Optional[Dict[str, Any]] = None,
        error: Optional[Exception] = None,
        **context
    ):
        """Add an operation to the debug session."""
        report = create_debug_report(operation, inputs, outputs, error, context)
        self.operations.append(report)
    
    def get_summary(self) -> Dict[str, Any]:
        """Get session summary."""
        import time
        
        successful_ops = sum(1 for op in self.operations if op["success"])
        failed_ops = len(self.operations) - successful_ops
        
        return {
            "session_name": self.session_name,
            "start_time": self.start_time,
            "duration": time.time() - (self.start_time or time.time()),
            "total_operations": len(self.operations),
            "successful_operations": successful_ops,
            "failed_operations": failed_ops,
            "operations": self.operations
        }
    
    def save_to_file(self, filename: str):
        """Save debug session to file."""
        import json
        from pathlib import Path
        
        summary = self.get_summary()
        
        Path(filename).parent.mkdir(parents=True, exist_ok=True)
        with open(filename, 'w') as f:
            json.dump(summary, f, indent=2, default=str)
        
        logger.info(f"Debug session saved to: {filename}")