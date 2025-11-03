# Deployment Guide

This guide covers deployment of Event Planning Agent v2 across different environments.

## Table of Contents

- [Prerequisites](#prerequisites)
- [Environment Setup](#environment-setup)
- [Development Deployment](#development-deployment)
- [Staging Deployment](#staging-deployment)
- [Production Deployment](#production-deployment)
- [Configuration Management](#configuration-management)
- [Monitoring Setup](#monitoring-setup)
- [Troubleshooting](#troubleshooting)

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+), macOS (10.15+), or Windows 10+ with WSL2
- **Memory**: Minimum 8GB RAM (16GB recommended for production)
- **Storage**: Minimum 20GB free space (50GB recommended for production)
- **CPU**: 4+ cores recommended

### Software Dependencies

- **Docker**: 20.10+ with Docker Compose v2
- **Python**: 3.9+ (for local development)
- **Git**: Latest version
- **curl**: For health checks and API testing

### Installation Commands

#### Ubuntu/Debian
```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose-plugin

# Install Python and Git
sudo apt install python3.9 python3-pip git curl
```

#### macOS
```bash
# Install Docker Desktop
# Download from https://www.docker.com/products/docker-desktop

# Install Python and Git (using Homebrew)
brew install python@3.9 git curl
```

#### Windows
```powershell
# Install Docker Desktop
# Download from https://www.docker.com/products/docker-desktop

# Install Python and Git
# Download Python from https://www.python.org/downloads/
# Download Git from https://git-scm.com/download/win
```

## Environment Setup

### 1. Clone Repository

```bash
git clone <repository-url>
cd event_planning_agent_v2
```

### 2. Environment Configuration

Choose the appropriate environment configuration:

#### Development Environment
```bash
cp .env.development .env
```

#### Staging Environment
```bash
cp .env.production .env.staging
# Edit .env.staging with staging-specific values
cp .env.staging .env
```

#### Production Environment
```bash
cp .env.production .env
# Edit .env with production-specific values
```

### 3. Required Environment Variables

#### Development
```bash
# Minimal required variables for development
DATABASE_URL=postgresql://eventuser:eventpass@localhost:5432/eventdb_dev
OLLAMA_BASE_URL=http://localhost:11434
LOG_LEVEL=DEBUG
```

#### Production
```bash
# Required production variables
DATABASE_URL=postgresql://user:password@db-host:5432/eventdb
JWT_SECRET=your-super-secure-jwt-secret-32-chars-min
CORS_ORIGINS=https://yourdomain.com,https://api.yourdomain.com
ALLOWED_HOSTS=yourdomain.com,api.yourdomain.com
MCP_AUTH_TOKEN=your-mcp-auth-token
GRAFANA_PASSWORD=secure-grafana-password
GRAFANA_SECRET_KEY=grafana-secret-key
API_BASE_URL=https://api.yourdomain.com
API_SERVER_IP=10.0.0.100
```

## Development Deployment

### Quick Start (Recommended)

#### Using Bash Script (Linux/macOS)
```bash
chmod +x scripts/deploy-dev.sh
./scripts/deploy-dev.sh
```

#### Using PowerShell Script (Windows)
```powershell
Set-ExecutionPolicy -ExecutionPolicy RemoteSigned -Scope CurrentUser
.\scripts\deploy-dev.ps1
```

### Manual Deployment

#### 1. Setup Environment
```bash
# Copy development environment
cp .env.development .env

# Create necessary directories
mkdir -p logs data monitoring/grafana/dashboards monitoring/grafana/datasources
```

#### 2. Start Services
```bash
# Start infrastructure services first
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d postgres ollama

# Wait for services to be ready
sleep 10

# Start application services
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml up -d
```

#### 3. Setup Ollama Models
```bash
# Wait for Ollama to be ready
sleep 15

# Pull required models
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml exec ollama ollama pull gemma:2b
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml exec ollama ollama pull tinyllama
```

#### 4. Run Database Setup
```bash
# Wait for API to be ready
sleep 20

# Run database migrations
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.dev.yml exec event-planning-api python -m event_planning_agent_v2.database.setup
```

#### 5. Verify Deployment
```bash
# Check service health
curl http://localhost:8000/health

# Check API documentation
curl http://localhost:8000/docs
```

### Development Services

After successful deployment, the following services will be available:

- **API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Database**: localhost:5432 (eventuser/eventpass)
- **Ollama**: http://localhost:11434
- **Prometheus**: http://localhost:9090
- **Grafana**: http://localhost:3000 (admin/admin)
- **PgAdmin**: http://localhost:5050 (admin@eventplanning.dev/admin)

## Staging Deployment

### Using Deployment Script
```bash
chmod +x scripts/deploy-staging.sh
./scripts/deploy-staging.sh
```

### Manual Staging Deployment

#### 1. Setup Staging Environment
```bash
# Create staging environment file
cp .env.production .env.staging

# Modify for staging
sed -i 's/ENVIRONMENT=production/ENVIRONMENT=staging/' .env.staging
sed -i 's/LOG_LEVEL=INFO/LOG_LEVEL=DEBUG/' .env.staging
sed -i 's/API_WORKERS=4/API_WORKERS=2/' .env.staging

# Use staging environment
cp .env.staging .env
```

#### 2. Run Pre-deployment Tests
```bash
# Build test image
docker build -f docker/Dockerfile --target development -t event-planning-test .

# Run unit tests
docker run --rm -v $(pwd):/app event-planning-test pytest event_planning_agent_v2/tests/unit/ -v

# Run integration tests
docker run --rm -v $(pwd):/app event-planning-test pytest event_planning_agent_v2/tests/integration/ -v
```

#### 3. Deploy Application
```bash
# Pull and build
docker-compose -f docker/docker-compose.yml pull
docker-compose -f docker/docker-compose.yml build --no-cache

# Start services
docker-compose -f docker/docker-compose.yml up -d
```

#### 4. Run Smoke Tests
```bash
# Test API health
for i in {1..30}; do
    if curl -f http://localhost:8000/health; then
        echo "API is healthy"
        break
    fi
    sleep 2
done

# Test database connection
docker-compose -f docker/docker-compose.yml exec postgres pg_isready -U eventuser -d eventdb
```

## Production Deployment

### Prerequisites for Production

#### 1. Security Setup
```bash
# Generate strong JWT secret (32+ characters)
JWT_SECRET=$(openssl rand -base64 32)

# Generate MCP auth token
MCP_AUTH_TOKEN=$(openssl rand -base64 24)

# Generate Grafana credentials
GRAFANA_PASSWORD=$(openssl rand -base64 16)
GRAFANA_SECRET_KEY=$(openssl rand -base64 32)
```

#### 2. SSL Certificates
```bash
# Create SSL directory
mkdir -p ssl

# Generate self-signed certificates (for testing)
openssl req -x509 -nodes -days 365 -newkey rsa:2048 \
    -keyout ssl/server.key \
    -out ssl/server.crt \
    -subj "/C=US/ST=State/L=City/O=Organization/CN=yourdomain.com"

# Set secure permissions
chmod 600 ssl/server.key
chmod 644 ssl/server.crt
```

### Using Production Deployment Script
```bash
# Set required environment variables
export DATABASE_URL="postgresql://user:password@db-host:5432/eventdb"
export JWT_SECRET="your-super-secure-jwt-secret"
export CORS_ORIGINS="https://yourdomain.com"
export ALLOWED_HOSTS="yourdomain.com"
export MCP_AUTH_TOKEN="your-mcp-auth-token"
export GRAFANA_PASSWORD="secure-password"
export GRAFANA_SECRET_KEY="grafana-secret"

# Run deployment
chmod +x scripts/deploy-prod.sh
./scripts/deploy-prod.sh
```

### Manual Production Deployment

#### 1. Environment Setup
```bash
# Copy and configure production environment
cp .env.production .env

# Edit .env with your production values
nano .env
```

#### 2. Create Backup
```bash
# Create backup directory
BACKUP_DIR="backups/$(date +%Y%m%d_%H%M%S)"
mkdir -p "$BACKUP_DIR"

# Backup existing database (if upgrading)
if docker-compose ps postgres | grep -q "Up"; then
    docker-compose exec -T postgres pg_dump -U eventuser eventdb > "$BACKUP_DIR/database.sql"
fi
```

#### 3. Deploy with Zero Downtime
```bash
# Pull latest images
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml pull

# Build application
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml build --no-cache --target production

# Start new instances alongside old ones
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d --scale event-planning-api=2

# Wait for health check
sleep 30

# Verify new instances are healthy
for i in {1..30}; do
    if curl -f http://localhost:8000/health; then
        echo "New instances are healthy"
        break
    fi
    sleep 2
done

# Scale to desired number of instances
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d
```

#### 4. Security Hardening
```bash
# Remove default networks
docker network prune -f

# Set secure file permissions
find . -name "*.sh" -exec chmod 755 {} \;
find . -name "*.json" -exec chmod 644 {} \;
find . -name "*.env*" -exec chmod 600 {} \;

# Update system packages in containers
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml exec event-planning-api apt-get update && apt-get upgrade -y
```

### Production Services

After successful production deployment:

- **API**: https://yourdomain.com (behind reverse proxy)
- **Prometheus**: http://localhost:9090 (internal)
- **Grafana**: http://localhost:3000 (internal)
- **Database**: Internal network only

## Configuration Management

### Environment-Specific Configurations

#### MCP Server Configuration
```bash
# Development
config/mcp_config.dev.json

# Staging  
config/mcp_config.json

# Production
config/mcp_config.prod.json
```

#### Hot Reloading (Development Only)
The system supports hot reloading of configuration files in development mode:

```bash
# Enable hot reloading
CONFIG_WATCH_ENABLED=true
CONFIG_WATCH_INTERVAL=5

# Modify configuration files
nano config/mcp_config.dev.json
# Changes will be automatically detected and applied
```

### Configuration Validation
```bash
# Validate configuration
docker-compose exec event-planning-api python -c "
from event_planning_agent_v2.config.config_manager import validate_configuration
print('Valid:', validate_configuration())
"
```

## Monitoring Setup

### Prometheus Configuration

#### 1. Configure Targets
Edit `monitoring/prometheus.yml`:
```yaml
scrape_configs:
  - job_name: 'event-planning-api'
    static_configs:
      - targets: ['event-planning-api:8000']
    scrape_interval: 10s
```

#### 2. Access Prometheus
- URL: http://localhost:9090
- Query examples:
  - `http_requests_total`: Total HTTP requests
  - `agent_execution_time`: Agent execution times
  - `workflow_iterations`: Workflow iteration counts

### Grafana Setup

#### 1. Access Grafana
- URL: http://localhost:3000
- Default credentials: admin/admin (change in production)

#### 2. Import Dashboards
```bash
# Copy dashboard configurations
cp monitoring/grafana/dashboards/* /var/lib/grafana/dashboards/
```

#### 3. Key Metrics to Monitor
- API response times
- Agent execution times
- Database connection pool usage
- Memory and CPU usage
- Error rates and types

### Log Management

#### 1. Structured Logging
```bash
# View application logs
docker-compose logs -f event-planning-api

# View specific log levels
docker-compose logs event-planning-api | grep ERROR
```

#### 2. Log Rotation
Logs are automatically rotated based on configuration:
```bash
LOG_ROTATION=1 day
LOG_RETENTION=30 days
```

## Troubleshooting

### Common Issues

#### 1. Database Connection Issues
```bash
# Check database status
docker-compose exec postgres pg_isready -U eventuser -d eventdb

# Check connection string
echo $DATABASE_URL

# Test connection manually
docker-compose exec event-planning-api python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Connection successful')
"
```

#### 2. Ollama Model Issues
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Pull models manually
docker-compose exec ollama ollama pull gemma:2b
docker-compose exec ollama ollama pull tinyllama

# Check model loading
docker-compose exec ollama ollama list
```

#### 3. MCP Server Issues
```bash
# Check MCP server logs
docker-compose logs mcp-servers

# Test MCP server connectivity
curl http://localhost:8001/health
curl http://localhost:8002/health
curl http://localhost:8003/health

# Restart MCP servers
docker-compose restart mcp-servers
```

#### 4. API Health Check Failures
```bash
# Check API logs
docker-compose logs event-planning-api

# Test API endpoints
curl -v http://localhost:8000/health
curl -v http://localhost:8000/docs

# Check resource usage
docker stats
```

### Performance Tuning

#### 1. Database Optimization
```sql
-- Check slow queries
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Analyze table statistics
ANALYZE venues;
ANALYZE caterers;
ANALYZE photographers;
```

#### 2. Memory Optimization
```bash
# Adjust Docker memory limits
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml up -d \
  --memory="4g" --memory-swap="8g"

# Monitor memory usage
docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"
```

#### 3. API Performance
```bash
# Increase worker processes
API_WORKERS=4

# Enable caching
ENABLE_CACHING=true
CACHE_SIZE=5000
CACHE_TTL=600
```

### Recovery Procedures

#### 1. Rollback Deployment
```bash
# Using deployment script
./scripts/deploy-prod.sh rollback

# Manual rollback
docker-compose -f docker/docker-compose.yml -f docker/docker-compose.prod.yml down
# Restore from backup
# Restart with previous version
```

#### 2. Database Recovery
```bash
# Restore from backup
BACKUP_DIR="backups/20241207_143000"
docker-compose exec -T postgres psql -U eventuser -d eventdb < "$BACKUP_DIR/database.sql"
```

#### 3. Emergency Procedures
```bash
# Stop all services
docker-compose down

# Clear all data (CAUTION!)
docker-compose down -v

# Emergency contact
# Email: ops@eventplanning.ai
# Slack: #event-planning-ops
```

### Health Monitoring

#### 1. Automated Health Checks
```bash
# Create health check script
cat > health_check.sh << 'EOF'
#!/bin/bash
curl -f http://localhost:8000/health || exit 1
curl -f http://localhost:9090/-/ready || exit 1
docker-compose exec postgres pg_isready -U eventuser -d eventdb || exit 1
EOF

chmod +x health_check.sh

# Run health check
./health_check.sh
```

#### 2. Alerting Setup
```bash
# Configure Prometheus alerting rules
# Edit monitoring/prometheus.yml to add alertmanager configuration

# Setup Grafana alerts
# Configure notification channels in Grafana UI
```

This deployment guide provides comprehensive instructions for deploying Event Planning Agent v2 across all environments. Follow the appropriate section based on your deployment target and requirements.