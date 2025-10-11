"""Compatibility utilities and version checking for Solana Pay Python library."""

from __future__ import annotations

import sys
import warnings
from typing import Dict, Any, Optional, Tuple

from .version import __version__, version_info, is_stable_release


# Minimum Python version required
MIN_PYTHON_VERSION = (3, 11)

# Dependency version requirements
DEPENDENCY_REQUIREMENTS = {
    "solana": "0.36.0",
    "solders": "0.26.0", 
    "fastapi": "0.118.0",
    "pydantic": "2.12.0",
    "httpx": "0.28.0",
}


def check_python_version() -> bool:
    """Check if the current Python version is supported.
    
    Returns:
        True if Python version is supported
        
    Raises:
        RuntimeError: If Python version is too old
    """
    current_version = sys.version_info[:2]
    
    if current_version < MIN_PYTHON_VERSION:
        raise RuntimeError(
            f"Solana Pay Python requires Python {MIN_PYTHON_VERSION[0]}.{MIN_PYTHON_VERSION[1]} "
            f"or higher. Current version: {current_version[0]}.{current_version[1]}"
        )
    
    return True


def check_dependencies() -> Dict[str, Any]:
    """Check if all required dependencies are available and compatible.
    
    Returns:
        Dictionary containing dependency check results
    """
    results = {
        "all_available": True,
        "all_compatible": True,
        "dependencies": {},
        "missing": [],
        "incompatible": []
    }
    
    for package, min_version in DEPENDENCY_REQUIREMENTS.items():
        try:
            module = __import__(package)
            installed_version = getattr(module, "__version__", "unknown")
            
            # Basic version comparison (simplified)
            is_compatible = _compare_versions(installed_version, min_version) >= 0
            
            results["dependencies"][package] = {
                "available": True,
                "installed_version": installed_version,
                "required_version": min_version,
                "compatible": is_compatible
            }
            
            if not is_compatible:
                results["all_compatible"] = False
                results["incompatible"].append(package)
                
        except ImportError:
            results["all_available"] = False
            results["missing"].append(package)
            results["dependencies"][package] = {
                "available": False,
                "installed_version": None,
                "required_version": min_version,
                "compatible": False
            }
    
    return results


def _compare_versions(version1: str, version2: str) -> int:
    """Compare two version strings.
    
    Args:
        version1: First version string
        version2: Second version string
        
    Returns:
        -1 if version1 < version2, 0 if equal, 1 if version1 > version2
    """
    try:
        # Simple version comparison - split by dots and compare numerically
        v1_parts = [int(x) for x in version1.split('.') if x.isdigit()]
        v2_parts = [int(x) for x in version2.split('.') if x.isdigit()]
        
        # Pad shorter version with zeros
        max_len = max(len(v1_parts), len(v2_parts))
        v1_parts.extend([0] * (max_len - len(v1_parts)))
        v2_parts.extend([0] * (max_len - len(v2_parts)))
        
        for v1, v2 in zip(v1_parts, v2_parts):
            if v1 < v2:
                return -1
            elif v1 > v2:
                return 1
        
        return 0
        
    except (ValueError, AttributeError):
        # If version parsing fails, assume compatible
        return 0


def get_system_info() -> Dict[str, Any]:
    """Get comprehensive system information for debugging.
    
    Returns:
        Dictionary containing system information
    """
    import platform
    
    info = {
        "python": {
            "version": sys.version,
            "version_info": sys.version_info,
            "executable": sys.executable,
            "platform": sys.platform
        },
        "system": {
            "platform": platform.platform(),
            "machine": platform.machine(),
            "processor": platform.processor(),
            "system": platform.system(),
            "release": platform.release()
        },
        "library": {
            "version": __version__,
            "version_info": version_info,
            "is_stable": is_stable_release()
        }
    }
    
    # Add dependency information
    dep_check = check_dependencies()
    info["dependencies"] = dep_check["dependencies"]
    
    return info


def warn_if_unstable():
    """Issue a warning if this is not a stable release."""
    if not is_stable_release():
        warnings.warn(
            f"You are using a pre-release version of Solana Pay Python ({__version__}). "
            "This version may contain bugs and is not recommended for production use.",
            UserWarning,
            stacklevel=2
        )


def deprecation_warning(
    feature: str,
    version: str,
    replacement: Optional[str] = None,
    removal_version: Optional[str] = None
):
    """Issue a deprecation warning for a feature.
    
    Args:
        feature: Name of the deprecated feature
        version: Version in which the feature was deprecated
        replacement: Recommended replacement (if any)
        removal_version: Version in which the feature will be removed
    """
    message = f"{feature} is deprecated as of version {version}"
    
    if replacement:
        message += f" and will be replaced by {replacement}"
    
    if removal_version:
        message += f". It will be removed in version {removal_version}"
    
    message += "."
    
    warnings.warn(message, DeprecationWarning, stacklevel=3)


class CompatibilityChecker:
    """Utility class for checking compatibility and system requirements."""
    
    def __init__(self):
        self._checks_performed = False
        self._check_results = {}
    
    def perform_checks(self, warn_on_issues: bool = True) -> Dict[str, Any]:
        """Perform all compatibility checks.
        
        Args:
            warn_on_issues: Whether to issue warnings for compatibility issues
            
        Returns:
            Dictionary containing all check results
        """
        if self._checks_performed:
            return self._check_results
        
        results = {
            "python_compatible": True,
            "dependencies_available": True,
            "dependencies_compatible": True,
            "system_info": get_system_info(),
            "issues": []
        }
        
        # Check Python version
        try:
            check_python_version()
        except RuntimeError as e:
            results["python_compatible"] = False
            results["issues"].append(str(e))
            if warn_on_issues:
                warnings.warn(str(e), RuntimeWarning)
        
        # Check dependencies
        dep_results = check_dependencies()
        results["dependencies_available"] = dep_results["all_available"]
        results["dependencies_compatible"] = dep_results["all_compatible"]
        results["dependency_details"] = dep_results
        
        if not dep_results["all_available"]:
            missing = ", ".join(dep_results["missing"])
            issue = f"Missing required dependencies: {missing}"
            results["issues"].append(issue)
            if warn_on_issues:
                warnings.warn(issue, RuntimeWarning)
        
        if not dep_results["all_compatible"]:
            incompatible = ", ".join(dep_results["incompatible"])
            issue = f"Incompatible dependency versions: {incompatible}"
            results["issues"].append(issue)
            if warn_on_issues:
                warnings.warn(issue, RuntimeWarning)
        
        # Check for unstable version
        if not is_stable_release() and warn_on_issues:
            warn_if_unstable()
        
        self._check_results = results
        self._checks_performed = True
        
        return results
    
    def is_compatible(self) -> bool:
        """Check if the current environment is fully compatible.
        
        Returns:
            True if all compatibility checks pass
        """
        results = self.perform_checks(warn_on_issues=False)
        return (
            results["python_compatible"] and
            results["dependencies_available"] and
            results["dependencies_compatible"]
        )
    
    def get_compatibility_report(self) -> str:
        """Get a human-readable compatibility report.
        
        Returns:
            Formatted compatibility report
        """
        results = self.perform_checks(warn_on_issues=False)
        
        lines = [
            "Solana Pay Python Compatibility Report",
            "=" * 40,
            f"Library Version: {__version__}",
            f"Python Version: {sys.version.split()[0]}",
            ""
        ]
        
        # Python compatibility
        if results["python_compatible"]:
            lines.append("✅ Python version compatible")
        else:
            lines.append("❌ Python version incompatible")
        
        # Dependencies
        if results["dependencies_available"]:
            lines.append("✅ All dependencies available")
        else:
            missing = results["dependency_details"]["missing"]
            lines.append(f"❌ Missing dependencies: {', '.join(missing)}")
        
        if results["dependencies_compatible"]:
            lines.append("✅ All dependencies compatible")
        else:
            incompatible = results["dependency_details"]["incompatible"]
            lines.append(f"❌ Incompatible dependencies: {', '.join(incompatible)}")
        
        # Issues
        if results["issues"]:
            lines.extend(["", "Issues:"])
            for issue in results["issues"]:
                lines.append(f"  • {issue}")
        
        return "\n".join(lines)


# Global compatibility checker instance
_compatibility_checker = CompatibilityChecker()

# Convenience functions
def check_compatibility(warn_on_issues: bool = True) -> bool:
    """Check if the current environment is compatible.
    
    Args:
        warn_on_issues: Whether to issue warnings for issues
        
    Returns:
        True if environment is compatible
    """
    return _compatibility_checker.perform_checks(warn_on_issues)["python_compatible"]


def get_compatibility_report() -> str:
    """Get a compatibility report for the current environment.
    
    Returns:
        Formatted compatibility report
    """
    return _compatibility_checker.get_compatibility_report()


# Perform basic checks on import (but don't warn by default)
try:
    check_python_version()
except RuntimeError:
    # Let the user handle this if they want to check compatibility
    pass