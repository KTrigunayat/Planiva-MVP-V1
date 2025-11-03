#!/bin/bash

# Development Deployment Script for Event Planning Agent v2
set -e

echo "🚀 Starting Development Deployment..."

# Configuration
PROJECT_NAME="event-planning-agent-v2"
COMPOSE_FILE="docker/docker-compose.yml"
COMPOSE_DEV_FILE="docker/docker-compose.dev.yml"
ENV_FILE=".env.development"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Check prerequisites
check_prerequisites() {
    log_info "Checking prerequisites..."
    
    # Check Docker
    if ! command -v docker &> /dev/null; then
        log_error "Docker is not installed. Please install Docker first."
        exit 1
    fi
    
    # Check Docker Compose
    if ! command -v docker-compose &> /dev/null; then
        log_error "Docker Compose is not installed. Please install Docker Compose first."
        exit 1
    fi
    
    # Check if Docker daemon is running
    if ! docker info &> /dev/null; then
        log_error "Docker daemon is not running. Please start Docker first."
        exit 1
    fi
    
    log_success "Prerequisites check passed"
}

# Setup environment
setup_environment() {
    log_info "Setting up development environment..."
    
    # Copy development environment file
    if [ -f "$ENV_FILE" ]; then
        cp "$ENV_FILE" .env
        log_success "Development environment file copied"
    else
        log_warning "Development environment file not found, using default .env"
    fi
    
    # Create necessary directories
    mkdir -p logs data monitoring/grafana/dashboards monitoring/grafana/datasources
    
    # Set permissions
    chmod 755 logs data
    
    log_success "Environment setup completed"
}

# Pull latest images
pull_images() {
    log_info "Pulling latest Docker images..."
    
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE pull
    
    log_success "Images pulled successfully"
}

# Build application
build_application() {
    log_info "Building application..."
    
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE build --no-cache
    
    log_success "Application built successfully"
}

# Start services
start_services() {
    log_info "Starting services..."
    
    # Start infrastructure services first
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE up -d postgres ollama
    
    # Wait for database to be ready
    log_info "Waiting for database to be ready..."
    sleep 10
    
    # Start remaining services
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE up -d
    
    log_success "Services started successfully"
}

# Setup Ollama models
setup_ollama() {
    log_info "Setting up Ollama models..."
    
    # Wait for Ollama to be ready
    sleep 15
    
    # Pull required models
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE exec ollama ollama pull gemma:2b || log_warning "Failed to pull gemma:2b model"
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE exec ollama ollama pull tinyllama || log_warning "Failed to pull tinyllama model"
    
    log_success "Ollama models setup completed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for API service to be ready
    sleep 20
    
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE exec event-planning-api python -m event_planning_agent_v2.database.setup
    
    log_success "Database migrations completed"
}

# Health check
health_check() {
    log_info "Performing health check..."
    
    # Check API health
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "API is healthy"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "API health check failed after 30 attempts"
            return 1
        fi
        
        sleep 2
    done
    
    # Check database connection
    if docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE exec postgres pg_isready -U eventuser -d eventdb_dev &> /dev/null; then
        log_success "Database is healthy"
    else
        log_error "Database health check failed"
        return 1
    fi
    
    log_success "Health check passed"
}

# Show service status
show_status() {
    log_info "Service Status:"
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE ps
    
    echo ""
    log_info "Available Services:"
    echo "  🌐 API: http://localhost:8000"
    echo "  📊 API Docs: http://localhost:8000/docs"
    echo "  🗄️  Database: localhost:5432"
    echo "  🤖 Ollama: http://localhost:11434"
    echo "  📈 Prometheus: http://localhost:9090"
    echo "  📊 Grafana: http://localhost:3000 (admin/admin)"
    echo "  🔧 PgAdmin: http://localhost:5050 (admin@eventplanning.dev/admin)"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up..."
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE down -v --remove-orphans
}

# Main deployment process
main() {
    echo "🎯 Event Planning Agent v2 - Development Deployment"
    echo "=================================================="
    
    # Handle script interruption
    trap cleanup EXIT
    
    check_prerequisites
    setup_environment
    pull_images
    build_application
    start_services
    setup_ollama
    run_migrations
    health_check
    show_status
    
    log_success "🎉 Development deployment completed successfully!"
    echo ""
    echo "To view logs: docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE logs -f"
    echo "To stop services: docker-compose -f $COMPOSE_FILE -f $COMPOSE_DEV_FILE down"
}

# Handle command line arguments
case "${1:-}" in
    "cleanup")
        cleanup
        ;;
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    *)
        main
        ;;
esac