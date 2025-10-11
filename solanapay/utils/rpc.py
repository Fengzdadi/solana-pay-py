"""RPC client management with connection pooling and retry logic."""

from __future__ import annotations

import asyncio
import logging
from typing import Optional, Dict, Any
from contextlib import asynccontextmanager

from solana.rpc.async_api import AsyncClient
from solana.rpc.commitment import Commitment
from httpx import AsyncClient as HttpxAsyncClient, Limits, Timeout

from .errors import RPCError, NetworkError, TimeoutError as SolanaPayTimeoutError

logger = logging.getLogger(__name__)


class RPCClientManager:
    """Manages RPC connections with pooling, retry logic, and error handling.
    
    This class provides a high-level interface for managing Solana RPC connections
    with automatic retry, connection pooling, and comprehensive error handling.
    
    Attributes:
        endpoint: RPC endpoint URL
        commitment: Default commitment level for transactions
        max_retries: Maximum number of retry attempts
        timeout: Request timeout in seconds
        max_connections: Maximum number of concurrent connections
    """
    
    def __init__(
        self,
        endpoint: str,
        commitment: str = "confirmed",
        max_retries: int = 3,
        timeout: int = 30,
        max_connections: int = 10,
        **kwargs
    ):
        """Initialize RPC client manager.
        
        Args:
            endpoint: Solana RPC endpoint URL
            commitment: Default commitment level ("processed", "confirmed", "finalized")
            max_retries: Maximum retry attempts for failed requests
            timeout: Request timeout in seconds
            max_connections: Maximum concurrent connections
            **kwargs: Additional arguments passed to AsyncClient
        """
        self.endpoint = endpoint
        self.commitment = Commitment(commitment)
        self.max_retries = max_retries
        self.timeout = timeout
        self.max_connections = max_connections
        self.extra_kwargs = kwargs
        
        # Connection pool configuration
        self._limits = Limits(
            max_keepalive_connections=max_connections,
            max_connections=max_connections * 2,
            keepalive_expiry=30.0
        )
        
        self._timeout = Timeout(timeout)
        self._client: Optional[AsyncClient] = None
        self._http_client: Optional[HttpxAsyncClient] = None
        self._closed = False

    async def __aenter__(self) -> AsyncClient:
        """Async context manager entry."""
        return await self.get_client()

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()

    async def get_client(self) -> AsyncClient:
        """Get or create an RPC client with connection pooling.
        
        Returns:
            Configured AsyncClient instance
            
        Raises:
            RPCError: If client creation fails
        """
        if self._closed:
            raise RPCError("RPC client manager has been closed")
        
        if self._client is None:
            try:
                # Create HTTP client with connection pooling
                self._http_client = HttpxAsyncClient(
                    limits=self._limits,
                    timeout=self._timeout
                )
                
                # Create Solana RPC client
                self._client = AsyncClient(
                    endpoint=self.endpoint,
                    commitment=self.commitment,
                    timeout=self.timeout,
                    **self.extra_kwargs
                )
                
                logger.debug(f"Created RPC client for endpoint: {self.endpoint}")
                
            except Exception as e:
                raise RPCError(
                    f"Failed to create RPC client: {str(e)}",
                    rpc_endpoint=self.endpoint
                ) from e
        
        return self._client

    async def close(self):
        """Close the RPC client and cleanup resources."""
        if not self._closed:
            self._closed = True
            
            if self._http_client:
                await self._http_client.aclose()
                self._http_client = None
            
            if self._client:
                await self._client.close()
                self._client = None
            
            logger.debug(f"Closed RPC client for endpoint: {self.endpoint}")

    async def execute_with_retry(
        self,
        operation,
        *args,
        max_retries: Optional[int] = None,
        **kwargs
    ):
        """Execute an RPC operation with retry logic.
        
        Args:
            operation: Async function to execute
            *args: Arguments for the operation
            max_retries: Override default max_retries for this operation
            **kwargs: Keyword arguments for the operation
            
        Returns:
            Result of the operation
            
        Raises:
            RPCError: If operation fails after all retries
            NetworkError: If network-level errors occur
            TimeoutError: If operation times out
        """
        retries = max_retries if max_retries is not None else self.max_retries
        last_exception = None
        
        for attempt in range(retries + 1):
            try:
                client = await self.get_client()
                result = await operation(client, *args, **kwargs)
                
                if attempt > 0:
                    logger.info(f"RPC operation succeeded on attempt {attempt + 1}")
                
                return result
                
            except asyncio.TimeoutError as e:
                last_exception = SolanaPayTimeoutError(
                    f"RPC operation timed out after {self.timeout}s",
                    timeout_seconds=self.timeout,
                    operation=operation.__name__ if hasattr(operation, '__name__') else str(operation)
                )
                
            except Exception as e:
                last_exception = e
                
                # Check if this is a retryable error
                if not self._is_retryable_error(e):
                    break
                
                if attempt < retries:
                    wait_time = min(2 ** attempt, 10)  # Exponential backoff, max 10s
                    logger.warning(
                        f"RPC operation failed (attempt {attempt + 1}/{retries + 1}), "
                        f"retrying in {wait_time}s: {str(e)}"
                    )
                    await asyncio.sleep(wait_time)
                else:
                    logger.error(f"RPC operation failed after {retries + 1} attempts: {str(e)}")
        
        # All retries exhausted, raise the last exception
        if isinstance(last_exception, (RPCError, NetworkError, SolanaPayTimeoutError)):
            raise last_exception
        else:
            raise RPCError(
                f"RPC operation failed after {retries + 1} attempts: {str(last_exception)}",
                rpc_endpoint=self.endpoint
            ) from last_exception

    def _is_retryable_error(self, error: Exception) -> bool:
        """Check if an error is retryable.
        
        Args:
            error: Exception to check
            
        Returns:
            True if the error should be retried
        """
        # Network-level errors are usually retryable
        if isinstance(error, (ConnectionError, TimeoutError, asyncio.TimeoutError)):
            return True
        
        # HTTP errors that might be temporary
        error_str = str(error).lower()
        retryable_patterns = [
            "connection",
            "timeout",
            "network",
            "temporary",
            "rate limit",
            "too many requests",
            "service unavailable",
            "internal server error"
        ]
        
        return any(pattern in error_str for pattern in retryable_patterns)

    async def health_check(self) -> bool:
        """Perform a health check on the RPC endpoint.
        
        Returns:
            True if the endpoint is healthy
        """
        try:
            async def check_health(client):
                # Simple health check - get slot
                response = await client.get_slot()
                return response.value is not None
            
            return await self.execute_with_retry(check_health, max_retries=1)
            
        except Exception as e:
            logger.warning(f"RPC health check failed: {str(e)}")
            return False

    def get_endpoint_info(self) -> Dict[str, Any]:
        """Get information about the RPC endpoint configuration.
        
        Returns:
            Dictionary containing endpoint configuration
        """
        return {
            "endpoint": self.endpoint,
            "commitment": str(self.commitment),
            "max_retries": self.max_retries,
            "timeout": self.timeout,
            "max_connections": self.max_connections,
            "is_closed": self._closed
        }


@asynccontextmanager
async def create_rpc_client(
    endpoint: str,
    commitment: str = "confirmed",
    **kwargs
):
    """Create an RPC client with automatic cleanup.
    
    This is a convenience function for creating RPC clients with proper
    resource management.
    
    Args:
        endpoint: Solana RPC endpoint URL
        commitment: Default commitment level
        **kwargs: Additional arguments for RPCClientManager
        
    Yields:
        AsyncClient instance
        
    Example:
        >>> async with create_rpc_client("https://api.devnet.solana.com") as client:
        ...     balance = await client.get_balance(pubkey)
    """
    manager = RPCClientManager(endpoint, commitment, **kwargs)
    try:
        client = await manager.get_client()
        yield client
    finally:
        await manager.close()


class RPCConnectionPool:
    """Pool of RPC connections for load balancing and failover.
    
    This class manages multiple RPC endpoints and provides automatic
    failover and load balancing capabilities.
    """
    
    def __init__(self, endpoints: list[str], **kwargs):
        """Initialize connection pool.
        
        Args:
            endpoints: List of RPC endpoint URLs
            **kwargs: Arguments passed to each RPCClientManager
        """
        if not endpoints:
            raise ValueError("At least one endpoint is required")
        
        self.endpoints = endpoints
        self.managers = [
            RPCClientManager(endpoint, **kwargs)
            for endpoint in endpoints
        ]
        self.current_index = 0
        self._closed = False

    async def get_client(self) -> AsyncClient:
        """Get a client from the pool with automatic failover.
        
        Returns:
            AsyncClient from a healthy endpoint
            
        Raises:
            RPCError: If no healthy endpoints are available
        """
        if self._closed:
            raise RPCError("Connection pool has been closed")
        
        # Try each endpoint starting from current index
        for i in range(len(self.managers)):
            manager_index = (self.current_index + i) % len(self.managers)
            manager = self.managers[manager_index]
            
            try:
                client = await manager.get_client()
                
                # Health check if this is not the primary endpoint
                if i > 0:
                    if await manager.health_check():
                        self.current_index = manager_index
                        logger.info(f"Switched to endpoint: {manager.endpoint}")
                    else:
                        continue
                
                return client
                
            except Exception as e:
                logger.warning(f"Failed to get client from {manager.endpoint}: {str(e)}")
                continue
        
        raise RPCError("No healthy RPC endpoints available")

    async def close(self):
        """Close all connections in the pool."""
        if not self._closed:
            self._closed = True
            
            for manager in self.managers:
                await manager.close()
            
            logger.debug("Closed RPC connection pool")

    async def __aenter__(self):
        """Async context manager entry."""
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()