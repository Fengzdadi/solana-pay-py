"""Solana cluster configurations and management."""

from __future__ import annotations

import os
from dataclasses import dataclass
from typing import Dict, Optional

from ..utils.errors import ConfigurationError


@dataclass
class ClusterConfig:
    """Configuration for a Solana cluster.
    
    Attributes:
        name: Human-readable cluster name
        rpc_endpoint: HTTP RPC endpoint URL
        ws_endpoint: WebSocket endpoint URL (optional)
        commitment: Default commitment level for this cluster
        description: Human-readable description
    """
    
    name: str
    rpc_endpoint: str
    ws_endpoint: Optional[str] = None
    commitment: str = "confirmed"
    description: str = ""

    def __post_init__(self):
        """Validate cluster configuration after initialization."""
        if not self.name:
            raise ConfigurationError("Cluster name cannot be empty")
        
        if not self.rpc_endpoint:
            raise ConfigurationError("RPC endpoint cannot be empty")
        
        if not self.rpc_endpoint.startswith(("http://", "https://")):
            raise ConfigurationError(f"Invalid RPC endpoint URL: {self.rpc_endpoint}")
        
        if self.ws_endpoint and not self.ws_endpoint.startswith(("ws://", "wss://")):
            raise ConfigurationError(f"Invalid WebSocket endpoint URL: {self.ws_endpoint}")
        
        valid_commitments = {"processed", "confirmed", "finalized"}
        if self.commitment not in valid_commitments:
            raise ConfigurationError(
                f"Invalid commitment level: {self.commitment}. "
                f"Must be one of {valid_commitments}"
            )


# Predefined cluster configurations
PREDEFINED_CLUSTERS: Dict[str, ClusterConfig] = {
    "devnet": ClusterConfig(
        name="devnet",
        rpc_endpoint="https://api.devnet.solana.com",
        ws_endpoint="wss://api.devnet.solana.com",
        commitment="confirmed",
        description="Solana Devnet - Development and testing environment"
    ),
    
    "testnet": ClusterConfig(
        name="testnet", 
        rpc_endpoint="https://api.testnet.solana.com",
        ws_endpoint="wss://api.testnet.solana.com",
        commitment="confirmed",
        description="Solana Testnet - Pre-production testing environment"
    ),
    
    "mainnet": ClusterConfig(
        name="mainnet-beta",
        rpc_endpoint="https://api.mainnet-beta.solana.com",
        ws_endpoint="wss://api.mainnet-beta.solana.com", 
        commitment="confirmed",
        description="Solana Mainnet Beta - Production environment"
    ),
    
    "mainnet-beta": ClusterConfig(
        name="mainnet-beta",
        rpc_endpoint="https://api.mainnet-beta.solana.com",
        ws_endpoint="wss://api.mainnet-beta.solana.com",
        commitment="confirmed", 
        description="Solana Mainnet Beta - Production environment"
    ),
    
    "localhost": ClusterConfig(
        name="localhost",
        rpc_endpoint="http://127.0.0.1:8899",
        ws_endpoint="ws://127.0.0.1:8900",
        commitment="processed",
        description="Local Solana validator for development"
    )
}

# Custom clusters registry
_custom_clusters: Dict[str, ClusterConfig] = {}


def get_cluster_config(cluster_name: str) -> ClusterConfig:
    """Get cluster configuration by name.
    
    Args:
        cluster_name: Name of the cluster
        
    Returns:
        ClusterConfig for the specified cluster
        
    Raises:
        ConfigurationError: If cluster is not found
        
    Example:
        >>> config = get_cluster_config("devnet")
        >>> print(config.rpc_endpoint)
        https://api.devnet.solana.com
    """
    # Check environment variable override first
    env_endpoint = os.getenv(f"SOLANA_PAY_{cluster_name.upper()}_RPC")
    if env_endpoint:
        return ClusterConfig(
            name=cluster_name,
            rpc_endpoint=env_endpoint,
            commitment="confirmed",
            description=f"Environment configured {cluster_name}"
        )
    
    # Check custom clusters
    if cluster_name in _custom_clusters:
        return _custom_clusters[cluster_name]
    
    # Check predefined clusters
    if cluster_name in PREDEFINED_CLUSTERS:
        return PREDEFINED_CLUSTERS[cluster_name]
    
    raise ConfigurationError(f"Unknown cluster: {cluster_name}")


def register_cluster(config: ClusterConfig) -> None:
    """Register a custom cluster configuration.
    
    Args:
        config: ClusterConfig to register
        
    Example:
        >>> custom_config = ClusterConfig(
        ...     name="my-rpc",
        ...     rpc_endpoint="https://my-rpc-provider.com",
        ...     description="My custom RPC provider"
        ... )
        >>> register_cluster(custom_config)
    """
    config.__post_init__()  # Validate configuration
    _custom_clusters[config.name] = config


def unregister_cluster(cluster_name: str) -> bool:
    """Unregister a custom cluster configuration.
    
    Args:
        cluster_name: Name of the cluster to unregister
        
    Returns:
        True if cluster was unregistered, False if not found
    """
    if cluster_name in _custom_clusters:
        del _custom_clusters[cluster_name]
        return True
    return False


def list_clusters() -> Dict[str, ClusterConfig]:
    """List all available cluster configurations.
    
    Returns:
        Dictionary mapping cluster names to configurations
    """
    all_clusters = {}
    all_clusters.update(PREDEFINED_CLUSTERS)
    all_clusters.update(_custom_clusters)
    return all_clusters


def get_default_cluster() -> str:
    """Get the default cluster name from environment or fallback.
    
    Returns:
        Default cluster name
    """
    return os.getenv("SOLANA_PAY_CLUSTER", "devnet")


def create_cluster_from_env(cluster_name: str) -> Optional[ClusterConfig]:
    """Create cluster configuration from environment variables.
    
    Looks for environment variables in the format:
    - SOLANA_PAY_{CLUSTER}_RPC: RPC endpoint
    - SOLANA_PAY_{CLUSTER}_WS: WebSocket endpoint (optional)
    - SOLANA_PAY_{CLUSTER}_COMMITMENT: Commitment level (optional)
    
    Args:
        cluster_name: Name of the cluster
        
    Returns:
        ClusterConfig if environment variables are found, None otherwise
    """
    env_prefix = f"SOLANA_PAY_{cluster_name.upper()}"
    
    rpc_endpoint = os.getenv(f"{env_prefix}_RPC")
    if not rpc_endpoint:
        return None
    
    ws_endpoint = os.getenv(f"{env_prefix}_WS")
    commitment = os.getenv(f"{env_prefix}_COMMITMENT", "confirmed")
    
    try:
        return ClusterConfig(
            name=cluster_name,
            rpc_endpoint=rpc_endpoint,
            ws_endpoint=ws_endpoint,
            commitment=commitment,
            description=f"Environment configured {cluster_name}"
        )
    except ConfigurationError:
        return None


def validate_cluster_connection(config: ClusterConfig) -> bool:
    """Validate that a cluster configuration can establish a connection.
    
    This performs a basic connectivity test without making actual RPC calls.
    
    Args:
        config: ClusterConfig to validate
        
    Returns:
        True if the configuration appears valid
    """
    try:
        # Basic URL validation
        import urllib.parse
        
        parsed = urllib.parse.urlparse(config.rpc_endpoint)
        if not parsed.scheme or not parsed.netloc:
            return False
        
        if config.ws_endpoint:
            ws_parsed = urllib.parse.urlparse(config.ws_endpoint)
            if not ws_parsed.scheme or not ws_parsed.netloc:
                return False
        
        return True
        
    except Exception:
        return False


def get_cluster_by_endpoint(endpoint: str) -> Optional[str]:
    """Find cluster name by RPC endpoint.
    
    Args:
        endpoint: RPC endpoint URL
        
    Returns:
        Cluster name if found, None otherwise
    """
    for name, config in list_clusters().items():
        if config.rpc_endpoint == endpoint:
            return name
    return None