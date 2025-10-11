"""Global settings management for Solana Pay Python library."""

from __future__ import annotations

import os
import logging
from dataclasses import dataclass, field
from typing import Optional, Dict, Any

from .clusters import get_default_cluster, get_cluster_config
from ..utils.errors import ConfigurationError


@dataclass
class SolanaPaySettings:
    """Global settings for the Solana Pay library.
    
    These settings control the default behavior of the library and can be
    configured via environment variables or programmatically.
    
    Attributes:
        default_cluster: Default Solana cluster to use
        default_commitment: Default commitment level for transactions
        default_timeout: Default timeout for RPC operations (seconds)
        max_retries: Default maximum retry attempts for RPC operations
        enable_logging: Whether to enable library logging
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR)
        rpc_pool_size: Default RPC connection pool size
        custom_endpoints: Custom RPC endpoints by cluster name
    """
    
    default_cluster: str = field(default_factory=get_default_cluster)
    default_commitment: str = "confirmed"
    default_timeout: int = 30
    max_retries: int = 3
    enable_logging: bool = False
    log_level: str = "INFO"
    rpc_pool_size: int = 10
    custom_endpoints: Dict[str, str] = field(default_factory=dict)

    def __post_init__(self):
        """Validate settings after initialization."""
        # Validate commitment level
        valid_commitments = {"processed", "confirmed", "finalized"}
        if self.default_commitment not in valid_commitments:
            raise ConfigurationError(
                f"Invalid default commitment: {self.default_commitment}. "
                f"Must be one of {valid_commitments}"
            )
        
        # Validate timeout
        if self.default_timeout <= 0:
            raise ConfigurationError("Default timeout must be positive")
        
        # Validate max_retries
        if self.max_retries < 0:
            raise ConfigurationError("Max retries must be non-negative")
        
        # Validate log level
        valid_log_levels = {"DEBUG", "INFO", "WARNING", "ERROR", "CRITICAL"}
        if self.log_level.upper() not in valid_log_levels:
            raise ConfigurationError(
                f"Invalid log level: {self.log_level}. "
                f"Must be one of {valid_log_levels}"
            )
        
        # Validate RPC pool size
        if self.rpc_pool_size <= 0:
            raise ConfigurationError("RPC pool size must be positive")
        
        # Configure logging if enabled
        if self.enable_logging:
            self._configure_logging()

    def _configure_logging(self):
        """Configure logging for the library."""
        logger = logging.getLogger("solanapay")
        
        # Set log level
        log_level = getattr(logging, self.log_level.upper())
        logger.setLevel(log_level)
        
        # Add handler if none exists
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)

    def get_cluster_endpoint(self, cluster_name: Optional[str] = None) -> str:
        """Get RPC endpoint for a cluster.
        
        Args:
            cluster_name: Cluster name (uses default if None)
            
        Returns:
            RPC endpoint URL
            
        Raises:
            ConfigurationError: If cluster is not found
        """
        if cluster_name is None:
            cluster_name = self.default_cluster
        
        # Check custom endpoints first
        if cluster_name in self.custom_endpoints:
            return self.custom_endpoints[cluster_name]
        
        # Get from cluster configuration
        config = get_cluster_config(cluster_name)
        return config.rpc_endpoint

    def set_custom_endpoint(self, cluster_name: str, endpoint: str):
        """Set a custom RPC endpoint for a cluster.
        
        Args:
            cluster_name: Name of the cluster
            endpoint: RPC endpoint URL
        """
        if not endpoint.startswith(("http://", "https://")):
            raise ConfigurationError(f"Invalid RPC endpoint URL: {endpoint}")
        
        self.custom_endpoints[cluster_name] = endpoint

    def to_dict(self) -> Dict[str, Any]:
        """Convert settings to dictionary.
        
        Returns:
            Dictionary representation of settings
        """
        return {
            "default_cluster": self.default_cluster,
            "default_commitment": self.default_commitment,
            "default_timeout": self.default_timeout,
            "max_retries": self.max_retries,
            "enable_logging": self.enable_logging,
            "log_level": self.log_level,
            "rpc_pool_size": self.rpc_pool_size,
            "custom_endpoints": self.custom_endpoints.copy()
        }

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> SolanaPaySettings:
        """Create settings from dictionary.
        
        Args:
            data: Dictionary containing settings
            
        Returns:
            SolanaPaySettings instance
        """
        return cls(**data)

    @classmethod
    def from_env(cls) -> SolanaPaySettings:
        """Create settings from environment variables.
        
        Environment variables:
        - SOLANA_PAY_CLUSTER: Default cluster
        - SOLANA_PAY_COMMITMENT: Default commitment level
        - SOLANA_PAY_TIMEOUT: Default timeout (seconds)
        - SOLANA_PAY_MAX_RETRIES: Maximum retry attempts
        - SOLANA_PAY_ENABLE_LOGGING: Enable logging (true/false)
        - SOLANA_PAY_LOG_LEVEL: Logging level
        - SOLANA_PAY_RPC_POOL_SIZE: RPC connection pool size
        
        Returns:
            SolanaPaySettings configured from environment
        """
        def get_bool_env(key: str, default: bool) -> bool:
            value = os.getenv(key, "").lower()
            if value in ("true", "1", "yes", "on"):
                return True
            elif value in ("false", "0", "no", "off"):
                return False
            return default

        def get_int_env(key: str, default: int) -> int:
            try:
                return int(os.getenv(key, str(default)))
            except ValueError:
                return default

        return cls(
            default_cluster=os.getenv("SOLANA_PAY_CLUSTER", get_default_cluster()),
            default_commitment=os.getenv("SOLANA_PAY_COMMITMENT", "confirmed"),
            default_timeout=get_int_env("SOLANA_PAY_TIMEOUT", 30),
            max_retries=get_int_env("SOLANA_PAY_MAX_RETRIES", 3),
            enable_logging=get_bool_env("SOLANA_PAY_ENABLE_LOGGING", False),
            log_level=os.getenv("SOLANA_PAY_LOG_LEVEL", "INFO"),
            rpc_pool_size=get_int_env("SOLANA_PAY_RPC_POOL_SIZE", 10)
        )


# Global settings instance
_global_settings: Optional[SolanaPaySettings] = None


def get_settings() -> SolanaPaySettings:
    """Get the global settings instance.
    
    Returns:
        Global SolanaPaySettings instance
    """
    global _global_settings
    
    if _global_settings is None:
        _global_settings = SolanaPaySettings.from_env()
    
    return _global_settings


def set_settings(settings: SolanaPaySettings):
    """Set the global settings instance.
    
    Args:
        settings: SolanaPaySettings to use globally
    """
    global _global_settings
    _global_settings = settings


def reset_settings():
    """Reset settings to defaults from environment."""
    global _global_settings
    _global_settings = None


def configure_logging(
    enable: bool = True,
    level: str = "INFO"
):
    """Configure library logging.
    
    Args:
        enable: Whether to enable logging
        level: Log level (DEBUG, INFO, WARNING, ERROR)
    """
    settings = get_settings()
    settings.enable_logging = enable
    settings.log_level = level
    settings._configure_logging()


def get_default_rpc_endpoint() -> str:
    """Get the default RPC endpoint.
    
    Returns:
        Default RPC endpoint URL
    """
    settings = get_settings()
    return settings.get_cluster_endpoint()


def set_default_cluster(cluster_name: str):
    """Set the default cluster.
    
    Args:
        cluster_name: Name of the cluster to use as default
        
    Raises:
        ConfigurationError: If cluster is not found
    """
    # Validate cluster exists
    get_cluster_config(cluster_name)
    
    settings = get_settings()
    settings.default_cluster = cluster_name