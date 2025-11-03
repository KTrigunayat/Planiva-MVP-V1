#!/bin/bash

# Test script for Event Planning Agent v2 Streamlit GUI
# Usage: ./scripts/test.sh [test_type]

set -e

TEST_TYPE=${1:-all}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🧪 Running tests for Event Planning Agent v2 GUI..."

cd "$PROJECT_DIR"

# Install test dependencies if not already installed
echo "📦 Installing test dependencies..."
pip install -r requirements.txt

# Run different types of tests based on argument
case $TEST_TYPE in
    "unit")
        echo "🔬 Running unit tests..."
        pytest tests/ -m "unit" -v
        ;;
    "integration")
        echo "🔗 Running integration tests..."
        pytest tests/ -m "integration" -v
        ;;
    "coverage")
        echo "📊 Running tests with coverage..."
        pytest tests/ --cov=components --cov=utils --cov=pages --cov-report=html --cov-report=term
        echo "📋 Coverage report generated in htmlcov/"
        ;;
    "fast")
        echo "⚡ Running fast tests only..."
        pytest tests/ -m "not slow" -v
        ;;
    "api")
        echo "🌐 Running API tests..."
        pytest tests/ -m "api" -v
        ;;
    "all")
        echo "🎯 Running all tests..."
        pytest tests/ -v
        ;;
    *)
        echo "❌ Unknown test type: $TEST_TYPE"
        echo "Available options: unit, integration, coverage, fast, api, all"
        exit 1
        ;;
esac

echo "✅ Tests completed successfully!"