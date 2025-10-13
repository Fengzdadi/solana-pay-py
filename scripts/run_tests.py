#!/usr/bin/env python3
"""
Test runner script for Solana Pay Python library.

This script provides various test running options and generates reports.

Usage:
    python scripts/run_tests.py [options]
"""

import argparse
import subprocess
import sys
from pathlib import Path


def run_command(cmd, description=""):
    """Run a command and return the result."""
    if description:
        print(f"🔄 {description}")
    
    print(f"   Running: {' '.join(cmd)}")
    
    try:
        result = subprocess.run(cmd, capture_output=True, text=True, check=True)
        print(f"   ✅ Success")
        if result.stdout:
            print(f"   Output: {result.stdout.strip()}")
        return True
    except subprocess.CalledProcessError as e:
        print(f"   ❌ Failed (exit code {e.returncode})")
        if e.stdout:
            print(f"   Stdout: {e.stdout.strip()}")
        if e.stderr:
            print(f"   Stderr: {e.stderr.strip()}")
        return False


def run_unit_tests(verbose=False, coverage=False):
    """Run unit tests."""
    cmd = ["uv", "run", "pytest", "tests/", "-m", "unit or not integration"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=solanapay", "--cov-report=html", "--cov-report=term"])
    
    return run_command(cmd, "Running unit tests")


def run_integration_tests(verbose=False):
    """Run integration tests."""
    cmd = ["uv", "run", "pytest", "tests/", "-m", "integration"]
    
    if verbose:
        cmd.append("-v")
    
    return run_command(cmd, "Running integration tests")


def run_all_tests(verbose=False, coverage=False):
    """Run all tests."""
    cmd = ["uv", "run", "pytest", "tests/"]
    
    if verbose:
        cmd.append("-v")
    
    if coverage:
        cmd.extend(["--cov=solanapay", "--cov-report=html", "--cov-report=term"])
    
    return run_command(cmd, "Running all tests")


def run_linting():
    """Run code linting."""
    success = True
    
    # Ruff check
    if not run_command(["uv", "run", "ruff", "check", "."], "Running ruff linting"):
        success = False
    
    # Ruff format check
    if not run_command(["uv", "run", "ruff", "format", "--check", "."], "Checking code formatting"):
        success = False
    
    return success


def run_type_checking():
    """Run type checking."""
    return run_command(["uv", "run", "mypy", "solanapay"], "Running type checking")


def run_security_check():
    """Run security checks."""
    # This would run security tools like bandit if configured
    print("🔒 Security checks not configured yet")
    return True


def generate_test_report():
    """Generate comprehensive test report."""
    print("📊 Generating test report...")
    
    # Run tests with coverage and XML output
    cmd = [
        "uv", "run", "pytest", "tests/",
        "--cov=solanapay",
        "--cov-report=html",
        "--cov-report=xml",
        "--cov-report=term",
        "--junit-xml=test-results.xml"
    ]
    
    success = run_command(cmd, "Generating test report")
    
    if success:
        print("📋 Test report generated:")
        print("   • HTML coverage: htmlcov/index.html")
        print("   • XML coverage: coverage.xml")
        print("   • JUnit results: test-results.xml")
    
    return success


def run_performance_tests():
    """Run performance benchmarks."""
    print("⚡ Performance tests not implemented yet")
    return True


def main():
    """Main test runner."""
    parser = argparse.ArgumentParser(
        description="Test runner for Solana Pay Python",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Run all tests with coverage
  python scripts/run_tests.py --all --coverage
  
  # Run only unit tests
  python scripts/run_tests.py --unit
  
  # Run linting and type checking
  python scripts/run_tests.py --lint --types
  
  # Generate comprehensive report
  python scripts/run_tests.py --report
        """
    )
    
    parser.add_argument("--unit", action="store_true", help="Run unit tests")
    parser.add_argument("--integration", action="store_true", help="Run integration tests")
    parser.add_argument("--all", action="store_true", help="Run all tests")
    parser.add_argument("--lint", action="store_true", help="Run linting")
    parser.add_argument("--types", action="store_true", help="Run type checking")
    parser.add_argument("--security", action="store_true", help="Run security checks")
    parser.add_argument("--performance", action="store_true", help="Run performance tests")
    parser.add_argument("--report", action="store_true", help="Generate test report")
    parser.add_argument("--coverage", action="store_true", help="Include coverage analysis")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    parser.add_argument("--fast", action="store_true", help="Skip slow tests")
    
    args = parser.parse_args()
    
    # If no specific tests requested, run all
    if not any([args.unit, args.integration, args.all, args.lint, args.types, 
                args.security, args.performance, args.report]):
        args.all = True
        args.lint = True
        args.types = True
    
    print("🧪 Solana Pay Python - Test Runner")
    print("=" * 40)
    
    success = True
    
    # Run linting
    if args.lint:
        if not run_linting():
            success = False
        print()
    
    # Run type checking
    if args.types:
        if not run_type_checking():
            success = False
        print()
    
    # Run unit tests
    if args.unit:
        if not run_unit_tests(args.verbose, args.coverage):
            success = False
        print()
    
    # Run integration tests
    if args.integration:
        if not run_integration_tests(args.verbose):
            success = False
        print()
    
    # Run all tests
    if args.all:
        if not run_all_tests(args.verbose, args.coverage):
            success = False
        print()
    
    # Run security checks
    if args.security:
        if not run_security_check():
            success = False
        print()
    
    # Run performance tests
    if args.performance:
        if not run_performance_tests():
            success = False
        print()
    
    # Generate report
    if args.report:
        if not generate_test_report():
            success = False
        print()
    
    # Summary
    if success:
        print("🎉 All checks passed!")
        return 0
    else:
        print("❌ Some checks failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())