#!/bin/bash

# Production Deployment Script for Event Planning Agent v2
set -e

echo "🚀 Starting Production Deployment..."

# Configuration
PROJECT_NAME="event-planning-agent-v2"
COMPOSE_FILE="docker/docker-compose.yml"
COMPOSE_PROD_FILE="docker/docker-compose.prod.yml"
ENV_FILE=".env.production"
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"

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
    
    # Check required environment variables
    required_vars=(
        "DATABASE_URL"
        "JWT_SECRET"
        "CORS_ORIGINS"
        "ALLOWED_HOSTS"
        "MCP_AUTH_TOKEN"
        "GRAFANA_PASSWORD"
        "GRAFANA_SECRET_KEY"
    )
    
    for var in "${required_vars[@]}"; do
        if [ -z "${!var}" ]; then
            log_error "Required environment variable $var is not set"
            exit 1
        fi
    done
    
    log_success "Prerequisites check passed"
}

# Validate configuration
validate_configuration() {
    log_info "Validating configuration..."
    
    # Check if production environment file exists
    if [ ! -f "$ENV_FILE" ]; then
        log_error "Production environment file $ENV_FILE not found"
        exit 1
    fi
    
    # Validate JWT secret strength
    if [ ${#JWT_SECRET} -lt 32 ]; then
        log_error "JWT_SECRET must be at least 32 characters long"
        exit 1
    fi
    
    # Check if SSL certificates exist (if TLS is enabled)
    if [ "${ENABLE_TLS:-false}" = "true" ]; then
        if [ ! -f "ssl/server.crt" ] || [ ! -f "ssl/server.key" ]; then
            log_error "SSL certificates not found. Please provide ssl/server.crt and ssl/server.key"
            exit 1
        fi
    fi
    
    log_success "Configuration validation passed"
}

# Create backup
create_backup() {
    log_info "Creating backup..."
    
    mkdir -p "$BACKUP_DIR"
    
    # Backup database
    if docker-compose -f $COMPOSE_FILE ps postgres | grep -q "Up"; then
        docker-compose -f $COMPOSE_FILE exec -T postgres pg_dump -U eventuser eventdb > "$BACKUP_DIR/database.sql"
        log_success "Database backup created"
    fi
    
    # Backup volumes
    docker run --rm -v event-planning-agent-v2_postgres_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar czf /backup/postgres_data.tar.gz -C /data .
    
    log_success "Backup created at $BACKUP_DIR"
}

# Setup environment
setup_environment() {
    log_info "Setting up production environment..."
    
    # Copy production environment file
    cp "$ENV_FILE" .env
    
    # Create necessary directories
    mkdir -p logs data ssl monitoring/grafana/dashboards monitoring/grafana/datasources nginx
    
    # Set secure permissions
    chmod 700 ssl
    chmod 755 logs data
    
    # Generate SSL certificates if they don't exist
    if [ "${ENABLE_TLS:-false}" = "true" ] && [ ! -f "ssl/server.crt" ]; then
        log_info "Generating self-signed SSL certificates..."
        openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
            -keyout ssl/server.key \
            -out ssl/server.crt \
            -subj "/C=US/ST=State/L=City/O=Organization/CN=localhost"
        chmod 600 ssl/server.key
        chmod 644 ssl/server.crt
    fi
    
    log_success "Environment setup completed"
}

# Pull and build images
build_application() {
    log_info "Building application for production..."
    
    # Pull base images
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE pull postgres ollama prometheus grafana
    
    # Build application with production target
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE build --no-cache --target production
    
    log_success "Application built successfully"
}

# Deploy with zero downtime
deploy_zero_downtime() {
    log_info "Performing zero-downtime deployment..."
    
    # Start new services alongside old ones
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE up -d --scale event-planning-api=2
    
    # Wait for new instances to be healthy
    sleep 30
    
    # Health check new instances
    for i in {1..30}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "New instances are healthy"
            break
        fi
        
        if [ $i -eq 30 ]; then
            log_error "New instances failed health check"
            return 1
        fi
        
        sleep 2
    done
    
    # Scale down to desired number of instances
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE up -d --scale event-planning-api=2
    
    log_success "Zero-downtime deployment completed"
}

# Setup monitoring
setup_monitoring() {
    log_info "Setting up monitoring..."
    
    # Wait for Prometheus to be ready
    for i in {1..30}; do
        if curl -f http://localhost:9090/-/ready &> /dev/null; then
            log_success "Prometheus is ready"
            break
        fi
        sleep 2
    done
    
    # Wait for Grafana to be ready
    for i in {1..30}; do
        if curl -f http://localhost:3000/api/health &> /dev/null; then
            log_success "Grafana is ready"
            break
        fi
        sleep 2
    done
    
    log_success "Monitoring setup completed"
}

# Run database migrations
run_migrations() {
    log_info "Running database migrations..."
    
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE exec event-planning-api python -m event_planning_agent_v2.database.setup
    
    log_success "Database migrations completed"
}

# Comprehensive health check
health_check() {
    log_info "Performing comprehensive health check..."
    
    # Check API health
    for i in {1..60}; do
        if curl -f http://localhost:8000/health &> /dev/null; then
            log_success "API is healthy"
            break
        fi
        
        if [ $i -eq 60 ]; then
            log_error "API health check failed after 60 attempts"
            return 1
        fi
        
        sleep 2
    done
    
    # Check database connection
    if docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE exec postgres pg_isready -U eventuser -d eventdb &> /dev/null; then
        log_success "Database is healthy"
    else
        log_error "Database health check failed"
        return 1
    fi
    
    # Check MCP servers
    if curl -f http://localhost:8001/health &> /dev/null; then
        log_success "MCP servers are healthy"
    else
        log_warning "MCP servers health check failed"
    fi
    
    # Check monitoring
    if curl -f http://localhost:9090/-/ready &> /dev/null; then
        log_success "Prometheus is healthy"
    else
        log_warning "Prometheus health check failed"
    fi
    
    log_success "Health check completed"
}

# Security hardening
security_hardening() {
    log_info "Applying security hardening..."
    
    # Remove default networks
    docker network prune -f
    
    # Update system packages in containers
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE exec event-planning-api apt-get update && apt-get upgrade -y
    
    # Set secure file permissions
    find . -name "*.sh" -exec chmod 755 {} \;
    find . -name "*.json" -exec chmod 644 {} \;
    find . -name "*.env*" -exec chmod 600 {} \;
    
    log_success "Security hardening completed"
}

# Show deployment status
show_status() {
    log_info "Deployment Status:"
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE ps
    
    echo ""
    log_info "Available Services:"
    echo "  🌐 API: https://localhost (or configured domain)"
    echo "  📊 API Docs: https://localhost/docs"
    echo "  📈 Prometheus: http://localhost:9090"
    echo "  📊 Grafana: http://localhost:3000"
    
    echo ""
    log_info "Resource Usage:"
    docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
}

# Rollback function
rollback() {
    log_warning "Rolling back deployment..."
    
    # Stop current services
    docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE down
    
    # Restore from backup if available
    if [ -d "$BACKUP_DIR" ]; then
        log_info "Restoring from backup..."
        
        # Restore database
        if [ -f "$BACKUP_DIR/database.sql" ]; then
            docker-compose -f $COMPOSE_FILE up -d postgres
            sleep 10
            docker-compose -f $COMPOSE_FILE exec -T postgres psql -U eventuser -d eventdb < "$BACKUP_DIR/database.sql"
        fi
        
        # Restore volumes
        if [ -f "$BACKUP_DIR/postgres_data.tar.gz" ]; then
            docker run --rm -v event-planning-agent-v2_postgres_data:/data -v $(pwd)/$BACKUP_DIR:/backup alpine tar xzf /backup/postgres_data.tar.gz -C /data
        fi
    fi
    
    log_success "Rollback completed"
}

# Main deployment process
main() {
    echo "🎯 Event Planning Agent v2 - Production Deployment"
    echo "=================================================="
    
    # Handle script interruption
    trap rollback ERR
    
    check_prerequisites
    validate_configuration
    create_backup
    setup_environment
    build_application
    deploy_zero_downtime
    setup_monitoring
    run_migrations
    security_hardening
    health_check
    show_status
    
    log_success "🎉 Production deployment completed successfully!"
    echo ""
    echo "Backup created at: $BACKUP_DIR"
    echo "To view logs: docker-compose -f $COMPOSE_FILE -f $COMPOSE_PROD_FILE logs -f"
    echo "To rollback: $0 rollback"
}

# Handle command line arguments
case "${1:-}" in
    "rollback")
        rollback
        ;;
    "status")
        show_status
        ;;
    "health")
        health_check
        ;;
    "backup")
        create_backup
        ;;
    *)
        main
        ;;
esac