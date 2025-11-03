#!/bin/bash

# Development script for Event Planning Agent v2 Streamlit GUI
# Usage: ./scripts/dev.sh [command]

set -e

COMMAND=${1:-run}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

cd "$PROJECT_DIR"

case $COMMAND in
    "run")
        echo "🚀 Starting development server..."
        # Load development environment
        if [ -f ".env.development" ]; then
            export $(cat .env.development | grep -v '^#' | xargs)
        fi
        streamlit run app.py --server.port=8501 --server.address=0.0.0.0
        ;;
    "install")
        echo "📦 Installing dependencies..."
        pip install -r requirements.txt
        ;;
    "test")
        echo "🧪 Running tests in watch mode..."
        pytest tests/ -v --tb=short -x
        ;;
    "lint")
        echo "🔍 Running code linting..."
        if command -v flake8 &> /dev/null; then
            flake8 components/ utils/ pages/ tests/ --max-line-length=100 --ignore=E203,W503
        else
            echo "⚠️  flake8 not installed, skipping linting"
        fi
        ;;
    "format")
        echo "🎨 Formatting code..."
        if command -v black &> /dev/null; then
            black components/ utils/ pages/ tests/ --line-length=100
        else
            echo "⚠️  black not installed, skipping formatting"
        fi
        ;;
    "clean")
        echo "🧹 Cleaning up..."
        find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
        find . -type f -name "*.pyc" -delete 2>/dev/null || true
        rm -rf .pytest_cache/ htmlcov/ .coverage 2>/dev/null || true
        echo "✅ Cleanup completed"
        ;;
    "docker-dev")
        echo "🐳 Starting development with Docker..."
        docker-compose -f docker-compose.dev.yml up --build
        ;;
    "docker-stop")
        echo "🛑 Stopping Docker development environment..."
        docker-compose -f docker-compose.dev.yml down
        ;;
    *)
        echo "❌ Unknown command: $COMMAND"
        echo "Available commands:"
        echo "  run        - Start development server"
        echo "  install    - Install dependencies"
        echo "  test       - Run tests"
        echo "  lint       - Run code linting"
        echo "  format     - Format code"
        echo "  clean      - Clean up temporary files"
        echo "  docker-dev - Start with Docker"
        echo "  docker-stop- Stop Docker environment"
        exit 1
        ;;
esac