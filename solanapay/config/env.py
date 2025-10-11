"""Environment variable configuration utilities."""

from __future__ import annotations

import os
from typing import Optional, Dict, Any, Union


def get_env_bool(key: str, default: bool = False) -> bool:
    """Get a boolean value from environment variable.
    
    Args:
        key: Environment variable name
        default: Default value if not set
        
    Returns:
        Boolean value
    """
    value = os.getenv(key, "").lower().strip()
    
    if value in ("true", "1", "yes", "on", "enabled"):
        return True
    elif value in ("false", "0", "no", "off", "disabled"):
        return False
    else:
        return default


def get_env_int(key: str, default: int = 0) -> int:
    """Get an integer value from environment variable.
    
    Args:
        key: Environment variable name
        default: Default value if not set or invalid
        
    Returns:
        Integer value
    """
    try:
        value = os.getenv(key)
        return int(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def get_env_float(key: str, default: float = 0.0) -> float:
    """Get a float value from environment variable.
    
    Args:
        key: Environment variable name
        default: Default value if not set or invalid
        
    Returns:
        Float value
    """
    try:
        value = os.getenv(key)
        return float(value) if value is not None else default
    except (ValueError, TypeError):
        return default


def get_env_list(
    key: str, 
    separator: str = ",", 
    default: Optional[list] = None
) -> list:
    """Get a list value from environment variable.
    
    Args:
        key: Environment variable name
        separator: Separator character for list items
        default: Default value if not set
        
    Returns:
        List of strings
    """
    value = os.getenv(key)
    if value is None:
        return default or []
    
    return [item.strip() for item in value.split(separator) if item.strip()]


def get_env_dict(
    key: str,
    item_separator: str = ",",
    kv_separator: str = "=",
    default: Optional[dict] = None
) -> dict:
    """Get a dictionary value from environment variable.
    
    Format: key1=value1,key2=value2
    
    Args:
        key: Environment variable name
        item_separator: Separator between key-value pairs
        kv_separator: Separator between key and value
        default: Default value if not set
        
    Returns:
        Dictionary
    """
    value = os.getenv(key)
    if value is None:
        return default or {}
    
    result = {}
    for item in value.split(item_separator):
        item = item.strip()
        if kv_separator in item:
            k, v = item.split(kv_separator, 1)
            result[k.strip()] = v.strip()
    
    return result


def set_env_defaults(defaults: Dict[str, Union[str, int, float, bool]]):
    """Set default environment variables if not already set.
    
    Args:
        defaults: Dictionary of environment variable defaults
    """
    for key, value in defaults.items():
        if key not in os.environ:
            os.environ[key] = str(value)


def load_env_file(file_path: str) -> Dict[str, str]:
    """Load environment variables from a file.
    
    Simple .env file loader that supports:
    - KEY=value format
    - Comments starting with #
    - Empty lines
    
    Args:
        file_path: Path to the .env file
        
    Returns:
        Dictionary of loaded variables
    """
    env_vars = {}
    
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            for line_num, line in enumerate(f, 1):
                line = line.strip()
                
                # Skip empty lines and comments
                if not line or line.startswith('#'):
                    continue
                
                # Parse KEY=value format
                if '=' in line:
                    key, value = line.split('=', 1)
                    key = key.strip()
                    value = value.strip()
                    
                    # Remove quotes if present
                    if value.startswith('"') and value.endswith('"'):
                        value = value[1:-1]
                    elif value.startswith("'") and value.endswith("'"):
                        value = value[1:-1]
                    
                    env_vars[key] = value
                    
                    # Set in os.environ if not already set
                    if key not in os.environ:
                        os.environ[key] = value
    
    except FileNotFoundError:
        pass  # File doesn't exist, that's okay
    except Exception as e:
        # Log error but don't fail
        import logging
        logger = logging.getLogger(__name__)
        logger.warning(f"Failed to load env file {file_path}: {e}")
    
    return env_vars


def get_solana_pay_env_vars() -> Dict[str, str]:
    """Get all Solana Pay related environment variables.
    
    Returns:
        Dictionary of SOLANA_PAY_* environment variables
    """
    prefix = "SOLANA_PAY_"
    return {
        key: value
        for key, value in os.environ.items()
        if key.startswith(prefix)
    }


def validate_required_env_vars(required_vars: list[str]) -> list[str]:
    """Validate that required environment variables are set.
    
    Args:
        required_vars: List of required environment variable names
        
    Returns:
        List of missing environment variables
    """
    missing = []
    for var in required_vars:
        if not os.getenv(var):
            missing.append(var)
    return missing


# Common Solana Pay environment variable defaults
SOLANA_PAY_ENV_DEFAULTS = {
    "SOLANA_PAY_CLUSTER": "devnet",
    "SOLANA_PAY_COMMITMENT": "confirmed",
    "SOLANA_PAY_TIMEOUT": "30",
    "SOLANA_PAY_MAX_RETRIES": "3",
    "SOLANA_PAY_ENABLE_LOGGING": "false",
    "SOLANA_PAY_LOG_LEVEL": "INFO",
    "SOLANA_PAY_RPC_POOL_SIZE": "10"
}


def setup_default_env():
    """Set up default Solana Pay environment variables."""
    set_env_defaults(SOLANA_PAY_ENV_DEFAULTS)


def print_env_config():
    """Print current Solana Pay environment configuration."""
    print("Solana Pay Environment Configuration:")
    print("=" * 40)
    
    env_vars = get_solana_pay_env_vars()
    if not env_vars:
        print("No SOLANA_PAY_* environment variables set")
        return
    
    for key, value in sorted(env_vars.items()):
        # Mask sensitive values
        if "key" in key.lower() or "secret" in key.lower():
            display_value = "*" * len(value) if value else ""
        else:
            display_value = value
        
        print(f"{key}: {display_value}")


# Auto-setup defaults when module is imported
setup_default_env()