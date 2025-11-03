# Troubleshooting Guide

This guide helps diagnose and resolve common issues with Event Planning Agent v2.

## Table of Contents

- [Quick Diagnostics](#quick-diagnostics)
- [Common Issues](#common-issues)
- [Performance Issues](#performance-issues)
- [Configuration Problems](#configuration-problems)
- [Database Issues](#database-issues)
- [LLM and Model Issues](#llm-and-model-issues)
- [MCP Server Issues](#mcp-server-issues)
- [API and Network Issues](#api-and-network-issues)
- [Docker and Container Issues](#docker-and-container-issues)
- [Monitoring and Logging](#monitoring-and-logging)
- [Recovery Procedures](#recovery-procedures)

## Quick Diagnostics

### System Health Check

Run this comprehensive health check to identify issues:

```bash
#!/bin/bash
echo "🔍 Event Planning Agent v2 - Health Check"
echo "========================================"

# Check Docker
echo "📦 Docker Status:"
docker --version && echo "✅ Docker installed" || echo "❌ Docker not found"
docker info > /dev/null 2>&1 && echo "✅ Docker daemon running" || echo "❌ Docker daemon not running"

# Check services
echo -e "\n🚀 Service Status:"
docker-compose ps

# Check API health
echo -e "\n🌐 API Health:"
curl -s http://localhost:8000/health | jq . && echo "✅ API healthy" || echo "❌ API unhealthy"

# Check database
echo -e "\n🗄️ Database Status:"
docker-compose exec postgres pg_isready -U eventuser -d eventdb && echo "✅ Database ready" || echo "❌ Database not ready"

# Check Ollama
echo -e "\n🤖 Ollama Status:"
curl -s http://localhost:11434/api/tags | jq . && echo "✅ Ollama ready" || echo "❌ Ollama not ready"

# Check MCP servers
echo -e "\n🔌 MCP Servers:"
for port in 8001 8002 8003; do
    curl -s http://localhost:$port/health > /dev/null && echo "✅ MCP server on port $port" || echo "❌ MCP server on port $port not responding"
done

# Check resource usage
echo -e "\n📊 Resource Usage:"
docker stats --no-stream --format "table {{.Container}}\t{{.CPUPerc}}\t{{.MemUsage}}"
```

### Log Analysis

Quick log analysis to identify errors:

```bash
# Check for errors in the last 100 lines
docker-compose logs --tail=100 event-planning-api | grep -i error

# Check for warnings
docker-compose logs --tail=100 event-planning-api | grep -i warning

# Check database logs
docker-compose logs --tail=50 postgres | grep -i error

# Check MCP server logs
docker-compose logs --tail=50 mcp-servers | grep -i error
```

## Common Issues

### 1. Service Won't Start

**Symptoms:**
- Docker containers exit immediately
- Services show "Exited (1)" status
- API not responding

**Diagnosis:**
```bash
# Check container logs
docker-compose logs event-planning-api

# Check exit codes
docker-compose ps

# Check resource usage
docker system df
```

**Solutions:**

#### Insufficient Resources
```bash
# Check available memory
free -h

# Check disk space
df -h

# Increase Docker memory limits
# Edit docker-compose.yml:
deploy:
  resources:
    limits:
      memory: 4G
    reservations:
      memory: 2G
```

#### Port Conflicts
```bash
# Check port usage
netstat -tulpn | grep :8000
lsof -i :8000

# Change ports in docker-compose.yml
ports:
  - "8001:8000"  # Use different external port
```

#### Environment Variables
```bash
# Validate environment file
cat .env | grep -v '^#' | grep -v '^$'

# Check required variables
docker-compose config
```

### 2. Database Connection Issues

**Symptoms:**
- "Connection refused" errors
- "Database does not exist" errors
- Slow query performance

**Diagnosis:**
```bash
# Test database connection
docker-compose exec postgres psql -U eventuser -d eventdb -c "SELECT 1;"

# Check database logs
docker-compose logs postgres | tail -20

# Check connection pool
docker-compose exec event-planning-api python -c "
from event_planning_agent_v2.database.connection import get_db_pool
pool = get_db_pool()
print(f'Pool size: {pool.size}, Checked out: {pool.checkedout()}')
"
```

**Solutions:**

#### Database Not Ready
```bash
# Wait for database to be ready
docker-compose exec postgres pg_isready -U eventuser -d eventdb

# Add health check dependency in docker-compose.yml
depends_on:
  postgres:
    condition: service_healthy
```

#### Connection String Issues
```bash
# Verify connection string format
echo $DATABASE_URL
# Should be: postgresql://user:password@host:port/database

# Test connection manually
docker-compose exec event-planning-api python -c "
import psycopg2
conn = psycopg2.connect('$DATABASE_URL')
print('Connection successful')
conn.close()
"
```

#### Database Initialization
```bash
# Run database setup
docker-compose exec event-planning-api python -m event_planning_agent_v2.database.setup

# Check tables exist
docker-compose exec postgres psql -U eventuser -d eventdb -c "\dt"
```

### 3. API Response Issues

**Symptoms:**
- 500 Internal Server Error
- Timeout errors
- Slow response times

**Diagnosis:**
```bash
# Check API logs
docker-compose logs event-planning-api | grep -E "(ERROR|Exception|Traceback)"

# Test API endpoints
curl -v http://localhost:8000/health
curl -v http://localhost:8000/docs

# Check response times
time curl http://localhost:8000/health
```

**Solutions:**

#### Application Errors
```bash
# Check detailed error logs
docker-compose logs event-planning-api --tail=100

# Enable debug mode
# In .env:
DEBUG=true
LOG_LEVEL=DEBUG

# Restart services
docker-compose restart event-planning-api
```

#### Performance Issues
```bash
# Increase worker processes
# In .env:
API_WORKERS=4

# Increase timeout settings
# In .env:
AGENT_TIMEOUT=600
WORKFLOW_TIMEOUT=1800
```

## Performance Issues

### 1. Slow Agent Execution

**Symptoms:**
- Long response times for event planning requests
- Timeout errors during workflow execution
- High CPU usage

**Diagnosis:**
```bash
# Check agent performance metrics
curl http://localhost:8000/metrics | grep agent_execution_time

# Monitor resource usage
docker stats event-planning-agent-v2_event-planning-api_1

# Check workflow iterations
docker-compose logs event-planning-api | grep "workflow_iterations"
```

**Solutions:**

#### Optimize Beam Search
```bash
# Reduce beam width for faster execution
# In .env:
BEAM_WIDTH=2
MAX_WORKFLOW_ITERATIONS=15

# Reduce agent iterations
MAX_ITERATIONS=5
```

#### LLM Optimization
```bash
# Use smaller models for development
# In .env:
GEMMA_MODEL=gemma:2b  # Instead of larger models
TINYLLAMA_MODEL=tinyllama

# Reduce model timeout
MODEL_TIMEOUT=180
```

### 2. High Memory Usage

**Symptoms:**
- Out of memory errors
- Container restarts
- System slowdown

**Diagnosis:**
```bash
# Check memory usage
docker stats --format "table {{.Container}}\t{{.MemUsage}}\t{{.MemPerc}}"

# Check system memory
free -h

# Monitor memory over time
watch -n 5 'docker stats --no-stream'
```

**Solutions:**

#### Memory Limits
```bash
# Set memory limits in docker-compose.yml
deploy:
  resources:
    limits:
      memory: 2G
    reservations:
      memory: 1G
```

#### Optimize Caching
```bash
# Reduce cache size
# In .env:
CACHE_SIZE=1000
MAX_BEAM_HISTORY_SIZE=50

# Enable garbage collection
PYTHONOPTIMIZE=1
```

## Configuration Problems

### 1. Environment Variable Issues

**Symptoms:**
- Configuration validation errors
- Services using default values
- Authentication failures

**Diagnosis:**
```bash
# Validate configuration
docker-compose exec event-planning-api python -c "
from event_planning_agent_v2.config.config_manager import validate_configuration
print('Configuration valid:', validate_configuration())
"

# Check loaded configuration
docker-compose exec event-planning-api python -c "
from event_planning_agent_v2.config.settings import get_settings
settings = get_settings()
print('Environment:', settings.environment)
print('Database URL:', settings.get_database_url())
"
```

**Solutions:**

#### Missing Variables
```bash
# Check required variables
grep -E "Field.*env=" event_planning_agent_v2/config/settings.py

# Set missing variables in .env
echo "MISSING_VAR=value" >> .env

# Restart services
docker-compose restart
```

#### Variable Substitution
```bash
# Check MCP config variable substitution
docker-compose exec event-planning-api python -c "
from event_planning_agent_v2.config.config_manager import get_mcp_config
config = get_mcp_config()
print(config)
"
```

### 2. MCP Configuration Issues

**Symptoms:**
- MCP servers not starting
- Tool approval failures
- Connection timeouts

**Diagnosis:**
```bash
# Validate MCP configuration
cat config/mcp_config.json | jq .

# Check MCP server status
docker-compose logs mcp-servers

# Test MCP server endpoints
curl http://localhost:8001/health
```

**Solutions:**

#### Configuration Syntax
```bash
# Validate JSON syntax
jq . config/mcp_config.json

# Check environment variable substitution
envsubst < config/mcp_config.json | jq .
```

#### Server Connectivity
```bash
# Check MCP server ports
netstat -tulpn | grep -E ":(8001|8002|8003)"

# Restart MCP servers
docker-compose restart mcp-servers
```

## Database Issues

### 1. Migration Failures

**Symptoms:**
- Database schema errors
- Missing tables or columns
- Migration script failures

**Diagnosis:**
```bash
# Check migration status
docker-compose exec event-planning-api python -c "
from event_planning_agent_v2.database.migrations import get_migration_status
print(get_migration_status())
"

# Check database schema
docker-compose exec postgres psql -U eventuser -d eventdb -c "\d"
```

**Solutions:**

#### Manual Migration
```bash
# Run migrations manually
docker-compose exec event-planning-api python -m event_planning_agent_v2.database.setup

# Reset database (CAUTION: Data loss)
docker-compose down -v
docker-compose up -d postgres
sleep 10
docker-compose exec event-planning-api python -m event_planning_agent_v2.database.setup
```

### 2. Performance Issues

**Symptoms:**
- Slow query execution
- High database CPU usage
- Connection pool exhaustion

**Diagnosis:**
```bash
# Check slow queries
docker-compose exec postgres psql -U eventuser -d eventdb -c "
SELECT query, mean_time, calls 
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;
"

# Check connection pool
docker-compose exec postgres psql -U eventuser -d eventdb -c "
SELECT count(*) as active_connections 
FROM pg_stat_activity 
WHERE state = 'active';
"
```

**Solutions:**

#### Query Optimization
```sql
-- Add indexes for common queries
CREATE INDEX IF NOT EXISTS idx_venues_capacity ON venues(capacity);
CREATE INDEX IF NOT EXISTS idx_caterers_cost ON caterers(cost_per_person);

-- Analyze tables
ANALYZE venues;
ANALYZE caterers;
ANALYZE photographers;
```

#### Connection Pool Tuning
```bash
# Increase pool size in .env
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Optimize PostgreSQL settings
# In docker-compose.yml postgres command:
command: >
  postgres
  -c max_connections=200
  -c shared_buffers=256MB
  -c effective_cache_size=1GB
```

## LLM and Model Issues

### 1. Ollama Connection Issues

**Symptoms:**
- "Connection refused" to Ollama
- Model loading failures
- Slow model responses

**Diagnosis:**
```bash
# Check Ollama status
curl http://localhost:11434/api/tags

# Check Ollama logs
docker-compose logs ollama

# Test model availability
curl http://localhost:11434/api/show -d '{"name": "gemma:2b"}'
```

**Solutions:**

#### Service Issues
```bash
# Restart Ollama
docker-compose restart ollama

# Check Ollama health
docker-compose exec ollama ollama list

# Pull models manually
docker-compose exec ollama ollama pull gemma:2b
docker-compose exec ollama ollama pull tinyllama
```

#### Performance Optimization
```bash
# Increase model timeout
# In .env:
MODEL_TIMEOUT=300

# Use GPU acceleration (if available)
# In docker-compose.yml:
deploy:
  resources:
    reservations:
      devices:
        - driver: nvidia
          count: 1
          capabilities: [gpu]
```

### 2. Model Loading Issues

**Symptoms:**
- Models not found errors
- Long model loading times
- Memory errors during model loading

**Diagnosis:**
```bash
# Check available models
docker-compose exec ollama ollama list

# Check model sizes
docker-compose exec ollama du -sh ~/.ollama/models/*

# Monitor memory during model loading
watch -n 1 'docker stats --no-stream ollama'
```

**Solutions:**

#### Model Management
```bash
# Remove unused models
docker-compose exec ollama ollama rm unused-model

# Use smaller models
# In .env:
GEMMA_MODEL=gemma:2b  # Use 2B instead of 7B
TINYLLAMA_MODEL=tinyllama
```

## MCP Server Issues

### 1. Server Startup Failures

**Symptoms:**
- MCP servers not responding
- Connection refused errors
- Server process exits

**Diagnosis:**
```bash
# Check MCP server logs
docker-compose logs mcp-servers

# Check server processes
docker-compose exec mcp-servers ps aux

# Test server connectivity
for port in 8001 8002 8003; do
    curl -v http://localhost:$port/health
done
```

**Solutions:**

#### Process Management
```bash
# Restart MCP servers
docker-compose restart mcp-servers

# Check server startup script
docker-compose exec mcp-servers cat /app/start-mcp-servers.sh

# Manual server start for debugging
docker-compose exec mcp-servers python -m event_planning_agent_v2.mcp_servers.vendor_server
```

### 2. Tool Execution Issues

**Symptoms:**
- Tool approval failures
- Timeout errors
- Authentication errors

**Diagnosis:**
```bash
# Check tool approval configuration
cat config/mcp_config.json | jq '.mcpServers[].autoApprove'

# Test tool execution
curl -X POST http://localhost:8001/tools/enhanced_vendor_search \
  -H "Content-Type: application/json" \
  -d '{"filters": {}, "preferences": {}}'
```

**Solutions:**

#### Configuration Updates
```bash
# Update auto-approve list
# In config/mcp_config.json:
"autoApprove": [
  "enhanced_vendor_search",
  "vendor_compatibility_check",
  "fitness_score_calculation"
]

# Restart services
docker-compose restart
```

## API and Network Issues

### 1. Network Connectivity

**Symptoms:**
- Services can't communicate
- DNS resolution failures
- Port binding errors

**Diagnosis:**
```bash
# Check Docker networks
docker network ls
docker network inspect event-planning-agent-v2_event-planning-network

# Test inter-service connectivity
docker-compose exec event-planning-api ping postgres
docker-compose exec event-planning-api ping ollama
```

**Solutions:**

#### Network Configuration
```bash
# Recreate networks
docker-compose down
docker network prune
docker-compose up -d

# Check port conflicts
netstat -tulpn | grep -E ":(8000|5432|11434)"
```

### 2. Load Balancing Issues

**Symptoms:**
- Uneven load distribution
- Some instances not receiving requests
- Health check failures

**Diagnosis:**
```bash
# Check service replicas
docker-compose ps event-planning-api

# Test load distribution
for i in {1..10}; do
    curl -s http://localhost:8000/health | jq .instance_id
done
```

**Solutions:**

#### Scaling Configuration
```bash
# Scale services
docker-compose up -d --scale event-planning-api=3

# Configure health checks
# In docker-compose.yml:
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 10s
  retries: 3
```

## Docker and Container Issues

### 1. Container Resource Issues

**Symptoms:**
- Containers being killed (OOMKilled)
- High resource usage
- Performance degradation

**Diagnosis:**
```bash
# Check container resource usage
docker stats

# Check system resources
free -h
df -h

# Check Docker system usage
docker system df
```

**Solutions:**

#### Resource Management
```bash
# Set resource limits
# In docker-compose.yml:
deploy:
  resources:
    limits:
      cpus: '2.0'
      memory: 4G
    reservations:
      cpus: '1.0'
      memory: 2G

# Clean up unused resources
docker system prune -f
docker volume prune -f
```

### 2. Image Build Issues

**Symptoms:**
- Build failures
- Large image sizes
- Slow build times

**Diagnosis:**
```bash
# Check build logs
docker-compose build --no-cache 2>&1 | tee build.log

# Check image sizes
docker images | grep event-planning

# Analyze image layers
docker history event-planning-agent-v2_event-planning-api
```

**Solutions:**

#### Build Optimization
```bash
# Use multi-stage builds
# Already implemented in Dockerfile

# Clean build cache
docker builder prune -f

# Optimize layer caching
# Copy requirements first, then code
```

## Monitoring and Logging

### 1. Log Analysis

**Symptoms:**
- Missing logs
- Log rotation issues
- Performance impact from logging

**Diagnosis:**
```bash
# Check log files
ls -la logs/

# Check log rotation
docker-compose exec event-planning-api ls -la /app/logs/

# Check logging configuration
docker-compose exec event-planning-api python -c "
from event_planning_agent_v2.config.settings import get_settings
settings = get_settings()
print('Log level:', settings.observability.log_level)
print('Log format:', settings.observability.log_format)
"
```

**Solutions:**

#### Log Configuration
```bash
# Adjust log level
# In .env:
LOG_LEVEL=INFO  # Reduce from DEBUG

# Configure log rotation
LOG_ROTATION=1 day
LOG_RETENTION=7 days

# Use structured logging
LOG_FORMAT=json
```

### 2. Metrics Collection

**Symptoms:**
- Missing metrics
- Prometheus scraping failures
- Grafana dashboard issues

**Diagnosis:**
```bash
# Check Prometheus targets
curl http://localhost:9090/api/v1/targets

# Check metrics endpoint
curl http://localhost:8000/metrics

# Check Grafana datasource
curl http://localhost:3000/api/datasources
```

**Solutions:**

#### Metrics Configuration
```bash
# Enable metrics collection
# In .env:
ENABLE_METRICS=true

# Check Prometheus configuration
cat monitoring/prometheus.yml

# Restart monitoring services
docker-compose restart prometheus grafana
```

## Recovery Procedures

### 1. Service Recovery

**Complete System Recovery:**
```bash
# Stop all services
docker-compose down

# Clean up resources
docker system prune -f
docker volume prune -f

# Restart from clean state
docker-compose up -d

# Wait for services to be ready
sleep 30

# Run health check
curl http://localhost:8000/health
```

### 2. Data Recovery

**Database Recovery:**
```bash
# Stop application services
docker-compose stop event-planning-api mcp-servers

# Backup current database
docker-compose exec postgres pg_dump -U eventuser eventdb > backup_$(date +%Y%m%d_%H%M%S).sql

# Restore from backup
docker-compose exec -T postgres psql -U eventuser -d eventdb < backup_file.sql

# Restart services
docker-compose start event-planning-api mcp-servers
```

### 3. Emergency Procedures

**Critical System Failure:**
```bash
# Emergency shutdown
docker-compose down --remove-orphans

# Contact support
echo "System down at $(date)" | mail -s "Emergency: Event Planning System Down" ops@eventplanning.ai

# Activate backup system (if available)
# Follow disaster recovery plan
```

### 4. Rollback Procedures

**Application Rollback:**
```bash
# Using deployment script
./scripts/deploy-prod.sh rollback

# Manual rollback
git checkout previous-stable-tag
docker-compose build
docker-compose up -d
```

## Getting Help

### Support Channels

1. **Documentation**: Check this troubleshooting guide and deployment documentation
2. **Logs**: Always include relevant logs when reporting issues
3. **GitHub Issues**: Create detailed issue reports with reproduction steps
4. **Email Support**: ops@eventplanning.ai for critical issues

### Issue Reporting Template

When reporting issues, include:

```
**Environment:**
- OS: [Ubuntu 20.04, macOS 12, Windows 11]
- Docker version: [20.10.x]
- Deployment type: [development, staging, production]

**Issue Description:**
[Clear description of the problem]

**Steps to Reproduce:**
1. [Step 1]
2. [Step 2]
3. [Step 3]

**Expected Behavior:**
[What should happen]

**Actual Behavior:**
[What actually happens]

**Logs:**
```
[Include relevant logs]
```

**Configuration:**
[Include relevant configuration (redact sensitive data)]
```

This troubleshooting guide covers the most common issues and their solutions. For complex issues not covered here, please contact support with detailed information about your environment and the specific problem you're experiencing.