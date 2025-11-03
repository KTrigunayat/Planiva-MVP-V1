#!/usr/bin/env python3
"""
Comprehensive test runner for Event Planning Agent v2 Streamlit GUI
"""
import os
import sys
import subprocess
import argparse
from pathlib import Path

def run_command(command, description=""):
    """Run a command and return the result"""
    print(f"\n{'='*60}")
    print(f"Running: {description or command}")
    print(f"{'='*60}")
    
    try:
        result = subprocess.run(
            command,
            shell=True,
            capture_output=True,
            text=True,
            cwd=Path(__file__).parent
        )
        
        if result.stdout:
            print("STDOUT:")
            print(result.stdout)
        
        if result.stderr:
            print("STDERR:")
            print(result.stderr)
        
        if result.returncode == 0:
            print(f"✅ SUCCESS: {description or command}")
        else:
            print(f"❌ FAILED: {description or command} (exit code: {result.returncode})")
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        return False

def install_dependencies():
    """Install test dependencies"""
    print("📦 Installing dependencies...")
    return run_command("pip install -r requirements.txt", "Installing dependencies")

def run_unit_tests():
    """Run unit tests"""
    return run_command(
        "python -m pytest tests/ -v -m 'not integration and not slow'",
        "Running unit tests"
    )

def run_integration_tests():
    """Run integration tests"""
    return run_command(
        "python -m pytest tests/ -v -m 'integration'",
        "Running integration tests"
    )

def run_all_tests():
    """Run all tests"""
    return run_command(
        "python -m pytest tests/ -v",
        "Running all tests"
    )

def run_coverage_tests():
    """Run tests with coverage"""
    success = run_command(
        "python -m pytest tests/ --cov=components --cov=utils --cov=pages --cov-report=html --cov-report=term-missing",
        "Running tests with coverage"
    )
    
    if success:
        print("\n📊 Coverage report generated in htmlcov/index.html")
    
    return success

def run_linting():
    """Run code linting"""
    print("🔍 Running code linting...")
    
    # Check if flake8 is available
    try:
        subprocess.run(["flake8", "--version"], capture_output=True, check=True)
        return run_command(
            "flake8 components/ utils/ pages/ tests/ --max-line-length=100 --ignore=E203,W503",
            "Running flake8 linting"
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  flake8 not installed, skipping linting")
        return True

def run_formatting_check():
    """Check code formatting"""
    print("🎨 Checking code formatting...")
    
    # Check if black is available
    try:
        subprocess.run(["black", "--version"], capture_output=True, check=True)
        return run_command(
            "black --check components/ utils/ pages/ tests/ --line-length=100",
            "Checking code formatting with black"
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  black not installed, skipping formatting check")
        return True

def run_security_check():
    """Run security checks"""
    print("🔒 Running security checks...")
    
    # Check if bandit is available
    try:
        subprocess.run(["bandit", "--version"], capture_output=True, check=True)
        return run_command(
            "bandit -r components/ utils/ pages/ -f json -o security-report.json",
            "Running bandit security check"
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  bandit not installed, skipping security check")
        return True

def run_type_checking():
    """Run type checking"""
    print("🔍 Running type checking...")
    
    # Check if mypy is available
    try:
        subprocess.run(["mypy", "--version"], capture_output=True, check=True)
        return run_command(
            "mypy components/ utils/ pages/ --ignore-missing-imports",
            "Running mypy type checking"
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        print("⚠️  mypy not installed, skipping type checking")
        return True

def cleanup_test_artifacts():
    """Clean up test artifacts"""
    print("🧹 Cleaning up test artifacts...")
    
    artifacts = [
        ".pytest_cache",
        "htmlcov",
        ".coverage",
        "security-report.json",
        "__pycache__",
        "*.pyc"
    ]
    
    for artifact in artifacts:
        run_command(f"rm -rf {artifact}", f"Removing {artifact}")

def main():
    """Main test runner"""
    parser = argparse.ArgumentParser(description="Test runner for Event Planning Agent v2 GUI")
    parser.add_argument(
        "test_type",
        nargs="?",
        default="all",
        choices=["unit", "integration", "all", "coverage", "lint", "format", "security", "type", "quick", "ci"],
        help="Type of tests to run"
    )
    parser.add_argument("--install", action="store_true", help="Install dependencies first")
    parser.add_argument("--cleanup", action="store_true", help="Clean up artifacts after tests")
    parser.add_argument("--verbose", "-v", action="store_true", help="Verbose output")
    
    args = parser.parse_args()
    
    print("🧪 Event Planning Agent v2 GUI Test Runner")
    print("=" * 60)
    
    # Install dependencies if requested
    if args.install:
        if not install_dependencies():
            print("❌ Failed to install dependencies")
            sys.exit(1)
    
    # Track overall success
    all_success = True
    
    # Run tests based on type
    if args.test_type == "unit":
        all_success &= run_unit_tests()
    
    elif args.test_type == "integration":
        all_success &= run_integration_tests()
    
    elif args.test_type == "all":
        all_success &= run_all_tests()
    
    elif args.test_type == "coverage":
        all_success &= run_coverage_tests()
    
    elif args.test_type == "lint":
        all_success &= run_linting()
    
    elif args.test_type == "format":
        all_success &= run_formatting_check()
    
    elif args.test_type == "security":
        all_success &= run_security_check()
    
    elif args.test_type == "type":
        all_success &= run_type_checking()
    
    elif args.test_type == "quick":
        print("🚀 Running quick test suite...")
        all_success &= run_unit_tests()
        all_success &= run_linting()
    
    elif args.test_type == "ci":
        print("🤖 Running CI test suite...")
        all_success &= run_all_tests()
        all_success &= run_coverage_tests()
        all_success &= run_linting()
        all_success &= run_formatting_check()
        all_success &= run_security_check()
        all_success &= run_type_checking()
    
    # Cleanup if requested
    if args.cleanup:
        cleanup_test_artifacts()
    
    # Final result
    print("\n" + "=" * 60)
    if all_success:
        print("🎉 All tests passed successfully!")
        sys.exit(0)
    else:
        print("❌ Some tests failed. Please check the output above.")
        sys.exit(1)

if __name__ == "__main__":
    main()