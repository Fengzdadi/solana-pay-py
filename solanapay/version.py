"""Version information for Solana Pay Python library."""

# Version components
VERSION_MAJOR = 0
VERSION_MINOR = 1
VERSION_PATCH = 0
VERSION_PRE_RELEASE = None  # e.g., "alpha", "beta", "rc1"

# Full version string
if VERSION_PRE_RELEASE:
    __version__ = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}-{VERSION_PRE_RELEASE}"
else:
    __version__ = f"{VERSION_MAJOR}.{VERSION_MINOR}.{VERSION_PATCH}"

# Legacy compatibility
VERSION = __version__

# Version info tuple (similar to sys.version_info)
version_info = (VERSION_MAJOR, VERSION_MINOR, VERSION_PATCH, VERSION_PRE_RELEASE)

# Library metadata
LIBRARY_NAME = "solana-pay-py"
LIBRARY_DESCRIPTION = "Python implementation of Solana Pay protocol"
LIBRARY_AUTHOR = "Solana Pay Python Contributors"
LIBRARY_URL = "https://github.com/solana-foundation/solana-pay-py"

def get_version() -> str:
    """Get the current version string.
    
    Returns:
        Version string (e.g., "0.1.0" or "0.1.0-alpha")
    """
    return __version__

def get_version_info() -> tuple:
    """Get version information as a tuple.
    
    Returns:
        Tuple of (major, minor, patch, pre_release)
    """
    return version_info

def is_stable_release() -> bool:
    """Check if this is a stable release (no pre-release suffix).
    
    Returns:
        True if this is a stable release
    """
    return VERSION_PRE_RELEASE is None