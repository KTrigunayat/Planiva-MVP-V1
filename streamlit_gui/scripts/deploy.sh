#!/bin/bash

# Deployment script for Event Planning Agent v2 Streamlit GUI
# Usage: ./scripts/deploy.sh [environment]

set -e

ENVIRONMENT=${1:-production}
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_DIR="$(dirname "$SCRIPT_DIR")"

echo "🚀 Deploying Event Planning Agent v2 GUI to $ENVIRONMENT environment..."

# Load environment-specific configuration
if [ -f "$PROJECT_DIR/.env.$ENVIRONMENT" ]; then
    echo "📋 Loading environment configuration from .env.$ENVIRONMENT"
    export $(cat "$PROJECT_DIR/.env.$ENVIRONMENT" | grep -v '^#' | xargs)
else
    echo "⚠️  No environment-specific configuration found, using defaults"
fi

# Validate required environment variables
required_vars=("API_BASE_URL")
for var in "${required_vars[@]}"; do
    if [ -z "${!var}" ]; then
        echo "❌ Error: Required environment variable $var is not set"
        exit 1
    fi
done

echo "✅ Environment validation passed"

# Build Docker image
echo "🔨 Building Docker image..."
docker build -t event-planning-gui:$ENVIRONMENT "$PROJECT_DIR"

# Stop existing container if running
if docker ps -q -f name=event-planning-gui-$ENVIRONMENT; then
    echo "🛑 Stopping existing container..."
    docker stop event-planning-gui-$ENVIRONMENT
    docker rm event-planning-gui-$ENVIRONMENT
fi

# Run new container
echo "🚀 Starting new container..."
docker run -d \
    --name event-planning-gui-$ENVIRONMENT \
    --restart unless-stopped \
    -p ${GUI_PORT:-8501}:8501 \
    --env-file "$PROJECT_DIR/.env.$ENVIRONMENT" \
    event-planning-gui:$ENVIRONMENT

# Wait for container to be ready
echo "⏳ Waiting for container to be ready..."
sleep 10

# Health check
if curl -f http://localhost:${GUI_PORT:-8501}/_stcore/health > /dev/null 2>&1; then
    echo "✅ Deployment successful! GUI is running at http://localhost:${GUI_PORT:-8501}"
else
    echo "❌ Health check failed. Check container logs:"
    docker logs event-planning-gui-$ENVIRONMENT
    exit 1
fi

echo "🎉 Deployment completed successfully!"