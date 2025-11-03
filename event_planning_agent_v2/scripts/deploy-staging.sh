#!/bin/bash

# Staging Deployment Script for Event Planning Agent v2
set -e

echo "🚀 Starting Staging Deployment..."

# Configuration
PROJECT_NAME="event-planning-agent-v2"
COMPOSE_FILE="docker/docker-compose.yml"
ENV_FILE=".env.staging"

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
    log_info "Setting up staging environment..."
    
    # Create staging environment file if it doesn't exist
    if [ ! -f "$ENV_FILE" ]; then
        log_info "Creating staging environment file from production template..."
        cp .env.production "$ENV_FILE"
        
        # Modify for staging
        sed -i 's/ENVIRONMENT=production/ENVIRONMENT=staging/' "$ENV_FILE"
        sed -i 's/LOG_LEVEL=INFO/LOG_LEVEL=DEBUG/' "$ENV_FILE"
        sed -i 's/DEBUG=false/DEBUG=true/' "$ENV_FILE"
        sed -i 's/API_WORKERS=4/API_WORKERS=2/' "$ENV_FILE"
    fi
    
    # Copy staging environment file
    cp "$ENV_FILE" .env
    
    # Create necessary directories
    mkdir -p logs data monitoring/grafana/dashboards monitoring/grafana/datasources
    
    # Set permissions
    chmod 755 logs data
    
    log_success "Environment setup completed"
}

# Run tests before deployment
run_tests() {
    log_info "Running tests before deployment..."
    
    # Build test image
    docker build -f docker/Dockerfile --target development -t event-planning-test .
    
    # Run unit tests
    docker run --rm -v $(pwd):/app event-planning-test pytest event_planning_agent_v2/tests/unit/ -v
    
    # Run integration tests
    docker run --rm -v $(pwd):/app event-planning-test pytest event_planning_agent_v2/tests/integration/ -v
    
    log_success "Tests passed successfully"
}

# Deploy application
deploy_application() {
    log_info "Deploying application..."
    
    # Pull latest images
    docker-compose -f $COMPOSE_FILE pull
    
    # Build application
    docker-compose -f $COMPOSE_FILE build --no-cache
    
    # Start services
    docker-compose -f $COMPOSE_FILE up -d
    
    log_success "Application deployed successfully"
}

# Setup Ollama models
setup_ollama() {
    log_info "Setting up Ollama models..."
    
    # Wait for Ollama to be ready
    sleep 15
    
    # Pull required models
    docker-compose -f $COMPOSE_FILE exec ollama ollama pull gemma:2b || log_warning "Failed to pull gemma:2b model"
    docker-compose -f $COMPOSE_FILE exec ollama ollama pull tinyllama || log_warning "Failed to pull tinyllama model"
    
    log_success "Ollama models setup completed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    # Wait for API service to be ready
    sleep 20
    
    docker-compose -f $COMPOSE_FILE exec event-planning-api python -m event_planning_agent_v2.database.setup
    
    log_success "Database migrations completed"
}

# Run smoke tests
run_smoke_tests() {
    log_info "Running smoke tests..."
    
    # Test API health
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "API health check passed"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "API health check failed after 30 attempts"
            return 1
        fi
        
        sleep 2
    done
    
    # Test database connection
    if docker-compose -f $COMPOSE_FILE exec postgres pg_isready -U eventuser -d eventdb &> /dev/null; then
        log_success "Database connection test passed"
    else
        log_error "Database connection test failed"
        return 1
    fi
    
    # Test basic API endpoints
    if curl -f http://localhost:8000/docs &> /dev/null; then
        log_success "API documentation accessible"
    else
        log_warning "API documentation not accessible"
    fi
    
    log_success "Smoke tests completed"
}

# Performance tests
run_performance_tests() {
    log_info "Running performance tests..."
    
    # Simple load test using curl
    log_info "Running basic load test..."
    
    for i in {1..10}; do
        curl -s http://localhost:8000/health > /dev/null &
    done
    wait
    
    log_success "Basic load test completed"
    
    # Check resource usage
    log_info "Resource usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    docker-compose -f $COMPOSE_FILE ps
    
    echo ""
    log_info "Available Services:"
    echo "  🌐 API: http://localhost:8000"
    echo "  📊 API Docs: http://localhost:8000/docs"
    echo "  🗄️  Database: localhost:5432"
    echo "  🤖 Ollama: http://localhost:11434"
    echo "  📈 Prometheus: http://localhost:9090"
    echo "  📊 Grafana: http://localhost:3000"
    
    echo ""
    log_info "Test Commands:"
    echo "  Health Check: curl http://localhost:8000/health"
    echo "  API Docs: curl http://localhost:8000/docs"
    echo "  Logs: docker-compose -f $COMPOSE_FILE logs -f"
}

# Cleanup function
cleanup() {
    log_info "Cleaning up staging environment..."
    docker-compose -f $COMPOSE_FILE down -v --remove-orphans
    docker system prune -f
}

# Main deployment process
main() {
    echo "🎯 Event Planning Agent v2 - Staging Deployment"
    echo "==============================================="
    
    check_prerequisites
    setup_environment
    run_tests
    deploy_application
    setup_ollama
    run_migrations
    run_smoke_tests
    run_performance_tests
    show_status
    
    log_success "🎉 Staging deployment completed successfully!"
    echo ""
    echo "Environment: Staging"
    echo "To view logs: docker-compose -f $COMPOSE_FILE logs -f"
    echo "To cleanup: $0 cleanup"
}

# Handle command line arguments
case "${1:-}" in
    "cleanup")
        cleanup
        ;;
    "status")
        show_status
        ;;
    "test")
        run_smoke_tests
        ;;
    "performance")
        run_performance_tests
        ;;
    *)
        main
        ;;
esac