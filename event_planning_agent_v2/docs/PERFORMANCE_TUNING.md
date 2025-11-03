# Performance Tuning Guide

This guide provides comprehensive performance optimization strategies for Event Planning Agent v2.

## Table of Contents

- [Performance Overview](#performance-overview)
- [System Requirements](#system-requirements)
- [Database Optimization](#database-optimization)
- [LLM and Model Optimization](#llm-and-model-optimization)
- [Workflow Optimization](#workflow-optimization)
- [API Performance](#api-performance)
- [Container Optimization](#container-optimization)
- [Monitoring and Profiling](#monitoring-and-profiling)
- [Caching Strategies](#caching-strategies)
- [Network Optimization](#network-optimization)
- [Production Tuning](#production-tuning)

## Performance Overview

### Key Performance Metrics

Monitor these critical metrics for optimal performance:

- **Response Time**: API endpoint response times (target: <2s for planning requests)
- **Throughput**: Requests per second (target: 100+ RPS)
- **Agent Execution Time**: Individual agent processing time (target: <30s per agent)
- **Workflow Completion Time**: End-to-end planning workflow (target: <2 minutes)
- **Resource Utilization**: CPU, memory, and I/O usage (target: <80% peak usage)

### Performance Benchmarks

| Metric | Development | Staging | Production |
|--------|-------------|---------|------------|
| API Response Time | <5s | <3s | <2s |
| Workflow Time | <5min | <3min | <2min |
| Concurrent Users | 10 | 50 | 200+ |
| Memory Usage | <2GB | <4GB | <8GB |
| CPU Usage | <50% | <70% | <80% |

## System Requirements

### Minimum Requirements

**Development:**
- CPU: 4 cores
- RAM: 8GB
- Storage: 20GB SSD
- Network: 10 Mbps

**Production:**
- CPU: 8+ cores
- RAM: 16GB+
- Storage: 100GB+ SSD
- Network: 100+ Mbps

### Recommended Hardware

**High-Performance Setup:**
```yaml
CPU: 16+ cores (Intel Xeon or AMD EPYC)
RAM: 32GB+ DDR4
Storage: NVMe SSD with 1000+ IOPS
Network: 1 Gbps+
GPU: NVIDIA RTX 4090 or Tesla V100 (for LLM acceleration)
```

## Database Optimization

### PostgreSQL Configuration

#### 1. Connection Pool Optimization

```bash
# In .env file
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40
DB_POOL_TIMEOUT=30
DB_POOL_RECYCLE=3600
```

#### 2. PostgreSQL Settings

```sql
-- In docker-compose.yml postgres command
command: >
  postgres
  -c max_connections=200
  -c shared_buffers=512MB
  -c effective_cache_size=2GB
  -c maintenance_work_mem=128MB
  -c checkpoint_completion_target=0.9
  -c wal_buffers=32MB
  -c default_statistics_target=100
  -c random_page_cost=1.1
  -c effective_io_concurrency=200
  -c work_mem=8MB
  -c min_wal_size=1GB
  -c max_wal_size=4GB
```

#### 3. Index Optimization

```sql
-- Create performance indexes
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_capacity_cost 
ON venues(capacity, cost_per_person);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_caterers_cost_cuisine 
ON caterers(cost_per_person, cuisine_type);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_photographers_rate_style 
ON photographers(hourly_rate, style);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_status_created 
ON event_plans(status, created_at);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_agent_performance_plan_agent 
ON agent_performance(plan_id, agent_name);

-- JSONB indexes for flexible queries
CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_venues_amenities_gin 
ON venues USING GIN (amenities);

CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_event_plans_data_gin 
ON event_plans USING GIN (plan_data);
```

#### 4. Query Optimization

```sql
-- Analyze tables regularly
ANALYZE venues;
ANALYZE caterers;
ANALYZE photographers;
ANALYZE event_plans;

-- Monitor slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements 
ORDER BY mean_time DESC 
LIMIT 10;

-- Vacuum regularly
VACUUM ANALYZE;
```

#### 5. Partitioning for Large Tables

```sql
-- Partition event_plans by date for better performance
CREATE TABLE event_plans_2024 PARTITION OF event_plans
FOR VALUES FROM ('2024-01-01') TO ('2025-01-01');

CREATE TABLE event_plans_2025 PARTITION OF event_plans
FOR VALUES FROM ('2025-01-01') TO ('2026-01-01');
```

### Database Monitoring

```bash
# Monitor database performance
docker-compose exec postgres psql -U eventuser -d eventdb -c "
SELECT 
    schemaname,
    tablename,
    attname,
    n_distinct,
    correlation
FROM pg_stats 
WHERE schemaname = 'public'
ORDER BY tablename, attname;
"

# Check index usage
docker-compose exec postgres psql -U eventuser -d eventdb -c "
SELECT 
    schemaname,
    tablename,
    indexname,
    idx_scan,
    idx_tup_read,
    idx_tup_fetch
FROM pg_stat_user_indexes
ORDER BY idx_scan DESC;
"
```

## LLM and Model Optimization

### 1. Ollama Configuration

```bash
# Optimize Ollama settings in .env
OLLAMA_BASE_URL=http://ollama:11434
MODEL_TIMEOUT=180
MODEL_RETRIES=3

# Use appropriate model sizes
GEMMA_MODEL=gemma:2b  # Faster than 7b version
TINYLLAMA_MODEL=tinyllama  # Lightweight for simple tasks
```

### 2. Model Loading Optimization

```bash
# Pre-load models at startup
docker-compose exec ollama ollama pull gemma:2b
docker-compose exec ollama ollama pull tinyllama

# Keep models in memory
docker-compose exec ollama ollama run gemma:2b "warmup"
docker-compose exec ollama ollama run tinyllama "warmup"
```

### 3. GPU Acceleration

```yaml
# In docker-compose.yml for Ollama service
ollama:
  image: ollama/ollama:latest
  deploy:
    resources:
      reservations:
        devices:
          - driver: nvidia
            count: 1
            capabilities: [gpu]
  environment:
    - NVIDIA_VISIBLE_DEVICES=all
```

### 4. Model Caching

```python
# Implement model response caching
from functools import lru_cache

@lru_cache(maxsize=1000)
def cached_llm_call(prompt_hash, model_name):
    # Cache LLM responses for identical prompts
    pass
```

### 5. Batch Processing

```python
# Process multiple requests in batches
async def batch_llm_requests(requests, batch_size=5):
    for i in range(0, len(requests), batch_size):
        batch = requests[i:i + batch_size]
        await asyncio.gather(*[process_request(req) for req in batch])
```

## Workflow Optimization

### 1. Beam Search Tuning

```bash
# Optimize beam search parameters in .env
BEAM_WIDTH=3  # Balance between quality and speed
MAX_WORKFLOW_ITERATIONS=15  # Prevent infinite loops
STATE_CHECKPOINT_INTERVAL=3  # Save state frequently
```

### 2. Agent Timeout Configuration

```bash
# Set appropriate timeouts
AGENT_TIMEOUT=300  # 5 minutes per agent
WORKFLOW_TIMEOUT=1800  # 30 minutes total workflow
```

### 3. Parallel Agent Execution

```python
# Execute independent agents in parallel
async def parallel_agent_execution():
    budget_task = asyncio.create_task(budget_agent.execute())
    sourcing_task = asyncio.create_task(sourcing_agent.execute())
    
    # Wait for both to complete
    budget_result, sourcing_result = await asyncio.gather(
        budget_task, sourcing_task
    )
```

### 4. Workflow State Optimization

```python
# Optimize state serialization
class OptimizedEventPlanningState(TypedDict):
    # Use efficient data structures
    beam_candidates: List[Dict[str, Any]]  # Limit size
    workflow_status: str
    iteration_count: int
    
    # Compress large data
    compressed_history: Optional[bytes]
```

### 5. Early Termination Strategies

```python
# Implement early termination for good solutions
def should_terminate_early(state: EventPlanningState) -> bool:
    if state["iteration_count"] >= 5:
        best_score = max(combo.get("score", 0) for combo in state["beam_candidates"])
        if best_score > 0.9:  # 90% fitness score
            return True
    return False
```

## API Performance

### 1. FastAPI Optimization

```python
# Optimize FastAPI settings
app = FastAPI(
    title="Event Planning Agent v2",
    docs_url="/docs" if settings.debug else None,  # Disable docs in production
    redoc_url=None,  # Disable redoc
    openapi_url="/openapi.json" if settings.debug else None
)

# Use async endpoints
@app.post("/v1/plans")
async def create_plan(request: PlanRequest):
    # Async implementation
    pass
```

### 2. Request Validation Optimization

```python
# Use efficient Pydantic models
class OptimizedPlanRequest(BaseModel):
    client_id: str = Field(..., max_length=100)
    event_type: str = Field(..., max_length=50)
    guest_count: int = Field(..., gt=0, le=10000)
    budget: float = Field(..., gt=0)
    
    class Config:
        # Optimize validation
        validate_assignment = False
        use_enum_values = True
        allow_population_by_field_name = True
```

### 3. Response Compression

```python
# Enable response compression
from fastapi.middleware.gzip import GZipMiddleware

app.add_middleware(GZipMiddleware, minimum_size=1000)
```

### 4. Connection Pooling

```python
# Use connection pooling for external services
import aiohttp

class OptimizedHTTPClient:
    def __init__(self):
        connector = aiohttp.TCPConnector(
            limit=100,  # Total connection pool size
            limit_per_host=30,  # Per-host connection limit
            ttl_dns_cache=300,  # DNS cache TTL
            use_dns_cache=True,
        )
        self.session = aiohttp.ClientSession(connector=connector)
```

### 5. Caching Middleware

```python
# Implement response caching
from fastapi_cache import FastAPICache
from fastapi_cache.backends.redis import RedisBackend

@app.on_event("startup")
async def startup():
    redis = aioredis.from_url("redis://localhost", encoding="utf8")
    FastAPICache.init(RedisBackend(redis), prefix="fastapi-cache")

@app.get("/v1/plans/{plan_id}")
@cache(expire=300)  # Cache for 5 minutes
async def get_plan(plan_id: str):
    pass
```

## Container Optimization

### 1. Docker Image Optimization

```dockerfile
# Multi-stage build for smaller images
FROM python:3.11-slim as builder
# Build dependencies
COPY requirements.txt .
RUN pip install --user -r requirements.txt

FROM python:3.11-slim as production
# Copy only necessary files
COPY --from=builder /root/.local /home/app/.local
COPY event_planning_agent_v2/ ./event_planning_agent_v2/

# Optimize Python
ENV PYTHONOPTIMIZE=1
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1
```

### 2. Resource Limits

```yaml
# In docker-compose.yml
services:
  event-planning-api:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
```

### 3. Health Check Optimization

```yaml
# Efficient health checks
healthcheck:
  test: ["CMD", "curl", "-f", "http://localhost:8000/health"]
  interval: 30s
  timeout: 5s
  retries: 3
  start_period: 40s
```

### 4. Volume Optimization

```yaml
# Use tmpfs for temporary data
volumes:
  - type: tmpfs
    target: /tmp
    tmpfs:
      size: 1G
  - type: bind
    source: ./logs
    target: /app/logs
```

## Monitoring and Profiling

### 1. Application Profiling

```python
# Add profiling middleware
import cProfile
import pstats
from fastapi import Request

@app.middleware("http")
async def profile_middleware(request: Request, call_next):
    if request.url.path.startswith("/profile"):
        profiler = cProfile.Profile()
        profiler.enable()
        
        response = await call_next(request)
        
        profiler.disable()
        stats = pstats.Stats(profiler)
        # Log or return profiling data
        
        return response
    return await call_next(request)
```

### 2. Custom Metrics

```python
# Implement custom metrics
from prometheus_client import Counter, Histogram, Gauge

# Request metrics
REQUEST_COUNT = Counter('http_requests_total', 'Total HTTP requests', ['method', 'endpoint'])
REQUEST_DURATION = Histogram('http_request_duration_seconds', 'HTTP request duration')
ACTIVE_WORKFLOWS = Gauge('active_workflows', 'Number of active workflows')

# Agent metrics
AGENT_EXECUTION_TIME = Histogram('agent_execution_seconds', 'Agent execution time', ['agent_name'])
WORKFLOW_ITERATIONS = Histogram('workflow_iterations', 'Number of workflow iterations')
```

### 3. Performance Monitoring

```bash
# Monitor key performance indicators
curl http://localhost:8000/metrics | grep -E "(http_request_duration|agent_execution|workflow_iterations)"

# Database performance
docker-compose exec postgres psql -U eventuser -d eventdb -c "
SELECT 
    query,
    calls,
    total_time,
    mean_time,
    stddev_time
FROM pg_stat_statements 
ORDER BY total_time DESC 
LIMIT 10;
"
```

### 4. Real-time Monitoring

```python
# Real-time performance dashboard
import asyncio
import websockets

async def performance_websocket(websocket, path):
    while True:
        metrics = {
            "cpu_usage": get_cpu_usage(),
            "memory_usage": get_memory_usage(),
            "active_requests": get_active_requests(),
            "response_time": get_avg_response_time()
        }
        await websocket.send(json.dumps(metrics))
        await asyncio.sleep(1)
```

## Caching Strategies

### 1. Application-Level Caching

```python
# Implement multi-level caching
from functools import lru_cache
import redis

class CacheManager:
    def __init__(self):
        self.redis_client = redis.Redis(host='redis', port=6379, db=0)
        self.local_cache = {}
    
    @lru_cache(maxsize=1000)
    def get_vendor_data(self, vendor_id: str):
        # Local cache first, then Redis, then database
        pass
    
    async def cache_workflow_state(self, plan_id: str, state: dict):
        # Cache workflow state for recovery
        await self.redis_client.setex(
            f"workflow:{plan_id}", 
            3600,  # 1 hour TTL
            json.dumps(state)
        )
```

### 2. Database Query Caching

```python
# Cache expensive database queries
@lru_cache(maxsize=500)
def get_vendor_combinations(filters_hash: str):
    # Cache vendor search results
    pass

# Implement query result caching
class CachedVendorService:
    def __init__(self):
        self.cache_ttl = 300  # 5 minutes
        
    async def search_vendors(self, filters: dict):
        cache_key = hashlib.md5(json.dumps(filters, sort_keys=True).encode()).hexdigest()
        
        # Check cache first
        cached_result = await self.redis_client.get(f"vendors:{cache_key}")
        if cached_result:
            return json.loads(cached_result)
        
        # Query database
        result = await self._query_database(filters)
        
        # Cache result
        await self.redis_client.setex(
            f"vendors:{cache_key}",
            self.cache_ttl,
            json.dumps(result)
        )
        
        return result
```

### 3. Response Caching

```python
# Cache API responses
from fastapi_cache.decorator import cache

@app.get("/v1/vendors")
@cache(expire=300)  # Cache for 5 minutes
async def get_vendors(filters: VendorFilters = Depends()):
    return await vendor_service.search_vendors(filters.dict())
```

## Network Optimization

### 1. Connection Optimization

```python
# Optimize HTTP connections
import httpx

async_client = httpx.AsyncClient(
    limits=httpx.Limits(
        max_keepalive_connections=20,
        max_connections=100,
        keepalive_expiry=30
    ),
    timeout=httpx.Timeout(30.0)
)
```

### 2. Request Batching

```python
# Batch multiple requests
async def batch_vendor_requests(vendor_ids: List[str]):
    # Process multiple vendor requests in a single batch
    async with httpx.AsyncClient() as client:
        tasks = [
            client.get(f"/vendors/{vendor_id}")
            for vendor_id in vendor_ids
        ]
        responses = await asyncio.gather(*tasks)
        return responses
```

### 3. Load Balancing

```yaml
# Nginx load balancer configuration
upstream event_planning_api {
    least_conn;
    server event-planning-api-1:8000 weight=1 max_fails=3 fail_timeout=30s;
    server event-planning-api-2:8000 weight=1 max_fails=3 fail_timeout=30s;
    server event-planning-api-3:8000 weight=1 max_fails=3 fail_timeout=30s;
}

server {
    listen 80;
    location / {
        proxy_pass http://event_planning_api;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
}
```

## Production Tuning

### 1. Environment Configuration

```bash
# Production environment variables
ENVIRONMENT=production
DEBUG=false
LOG_LEVEL=INFO

# Performance settings
API_WORKERS=4
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=40

# Caching
ENABLE_CACHING=true
CACHE_SIZE=5000
CACHE_TTL=600

# Timeouts
AGENT_TIMEOUT=300
WORKFLOW_TIMEOUT=1800
MODEL_TIMEOUT=180
```

### 2. Scaling Configuration

```yaml
# Auto-scaling with Docker Swarm
version: '3.8'
services:
  event-planning-api:
    deploy:
      replicas: 3
      update_config:
        parallelism: 1
        delay: 10s
        order: start-first
      restart_policy:
        condition: on-failure
        delay: 5s
        max_attempts: 3
        window: 120s
      resources:
        limits:
          cpus: '2.0'
          memory: 4G
        reservations:
          cpus: '1.0'
          memory: 2G
```

### 3. Monitoring and Alerting

```yaml
# Prometheus alerting rules
groups:
  - name: event_planning_alerts
    rules:
      - alert: HighResponseTime
        expr: http_request_duration_seconds{quantile="0.95"} > 2
        for: 5m
        labels:
          severity: warning
        annotations:
          summary: "High API response time"
          
      - alert: HighErrorRate
        expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
        for: 2m
        labels:
          severity: critical
        annotations:
          summary: "High error rate detected"
```

### 4. Performance Testing

```bash
# Load testing with Apache Bench
ab -n 1000 -c 10 http://localhost:8000/health

# Stress testing with wrk
wrk -t12 -c400 -d30s http://localhost:8000/health

# Custom load test
python -m pytest tests/performance/test_load.py -v
```

### 5. Continuous Optimization

```python
# Automated performance monitoring
class PerformanceMonitor:
    def __init__(self):
        self.metrics_collector = MetricsCollector()
        
    async def monitor_performance(self):
        while True:
            metrics = await self.collect_metrics()
            
            # Check for performance degradation
            if metrics['avg_response_time'] > 2.0:
                await self.alert_performance_issue(metrics)
            
            # Auto-scale if needed
            if metrics['cpu_usage'] > 80:
                await self.trigger_auto_scale()
            
            await asyncio.sleep(60)  # Check every minute
```

This performance tuning guide provides comprehensive optimization strategies for all components of the Event Planning Agent v2 system. Regular monitoring and iterative optimization based on real-world usage patterns will ensure optimal performance in production environments.