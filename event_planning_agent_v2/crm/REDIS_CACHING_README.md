# Redis Caching Layer - Implementation Guide

## Overview

The Redis caching layer provides high-performance caching for the CRM Communication Engine, reducing database load and improving response times for frequently accessed data.

## Features

### 1. Connection Pooling
- **Max Connections**: Configurable pool size (default: 10)
- **Timeout Configuration**: Socket timeout and connect timeout settings
- **Automatic Reconnection**: Handles transient connection failures
- **Resource Cleanup**: Proper connection pool cleanup on shutdown

### 2. Client Preferences Caching
- **TTL**: 1 hour (3600 seconds)
- **Cache Key Format**: `crm:prefs:{client_id}`
- **Automatic Invalidation**: Cache invalidated on preference updates
- **Fallback**: Gracefully falls back to database on cache miss

### 3. Email Template Caching
- **TTL**: Indefinite (manual invalidation only)
- **Cache Key Format**: `crm:template:{channel}:{template_name}`
- **Manual Invalidation**: Templates invalidated when updated
- **Performance**: Eliminates filesystem reads for frequently used templates

### 4. Rate Limit Tracking
- **Purpose**: Track API quota usage to prevent exhaustion
- **TTL**: Configurable per API (default: 60 seconds)
- **Cache Key Format**: `crm:ratelimit:{api}:{window}`
- **Atomic Operations**: Uses Redis INCR for thread-safe counting

### 5. Cache Statistics
- **Local Metrics**: Tracks cache hits/misses at application level
- **Redis Metrics**: Exposes Redis server statistics
- **Hit Rate Calculation**: Provides cache effectiveness metrics
- **Connection Pool Stats**: Monitors pool utilization

## Configuration

### Environment Variables

```bash
# Redis connection URL
REDIS_URL=redis://localhost:6379/0

# Cache TTL settings (optional, uses defaults if not set)
CACHE_TTL=3600

# Enable/disable caching
ENABLE_CACHING=true
```

### Initialization

```python
from event_planning_agent_v2.crm.cache_manager import CRMCacheManager

# Initialize with connection pooling
cache_manager = CRMCacheManager(
    redis_url="redis://localhost:6379/0",
    enabled=True,
    max_connections=10,
    socket_timeout=5,
    socket_connect_timeout=5
)

# Use as context manager for automatic cleanup
with CRMCacheManager(redis_url="redis://localhost:6379/0") as cache:
    preferences = cache.get_client_preferences("client-123")
```

## Usage Examples

### Client Preferences

```python
from event_planning_agent_v2.crm.models import ClientPreferences, MessageChannel

# Get preferences (checks cache first)
preferences = cache_manager.get_client_preferences("client-123")

if preferences is None:
    # Cache miss - fetch from database
    preferences = repository.get_client_preferences("client-123")
    
    # Cache the result
    if preferences:
        cache_manager.set_client_preferences(preferences)

# Update preferences (invalidates cache)
preferences.timezone = "America/Los_Angeles"
repository.save_client_preferences(preferences)
cache_manager.invalidate_client_preferences("client-123")
```

### Email Templates

```python
# Get template (checks cache first)
template_content = cache_manager.get_template("welcome", "email")

if template_content is None:
    # Cache miss - load from filesystem
    with open("templates/email/welcome.html") as f:
        template_content = f.read()
    
    # Cache the template (indefinite TTL)
    cache_manager.set_template("welcome", "email", template_content)

# Invalidate template after update
cache_manager.invalidate_template("welcome", "email")
```

### Rate Limiting

```python
# Check if API call is allowed
allowed, current_count = cache_manager.check_rate_limit(
    api="whatsapp",
    limit=1000,
    window=86400  # 24 hours
)

if allowed:
    # Make API call
    send_whatsapp_message(...)
else:
    # Rate limit exceeded
    logger.warning(f"Rate limit exceeded: {current_count}/1000")
    # Queue for later or use fallback channel
```

### Cache Statistics

```python
# Get cache statistics
stats = cache_manager.get_cache_stats()

print(f"Cache enabled: {stats['enabled']}")
print(f"Total keys: {stats['total_keys']}")
print(f"Hit rate: {stats['local_hit_rate']}%")
print(f"Connection pool max: {stats['connection_pool']['max_connections']}")
```

## Integration with Repository

The `CommunicationRepository` automatically uses the cache manager when provided:

```python
from event_planning_agent_v2.crm.repository import CommunicationRepository
from event_planning_agent_v2.crm.cache_manager import get_cache_manager

# Initialize cache manager
cache_manager = get_cache_manager(redis_url="redis://localhost:6379/0")

# Initialize repository with cache support
repository = CommunicationRepository(
    db_manager=db_manager,
    cache_manager=cache_manager
)

# Repository methods automatically use cache
preferences = repository.get_client_preferences("client-123")  # Checks cache first
repository.save_client_preferences(preferences)  # Invalidates cache
```

## Monitoring

### Cache Hit Rate

Monitor cache effectiveness:

```python
stats = cache_manager.get_cache_stats()
hit_rate = stats['local_hit_rate']

if hit_rate < 50:
    logger.warning(f"Low cache hit rate: {hit_rate}%")
```

### Health Checks

Include cache health in system health checks:

```python
def health_check():
    cache_healthy = cache_manager.health_check()
    
    return {
        "cache": {
            "status": "healthy" if cache_healthy else "unhealthy",
            "enabled": cache_manager.enabled
        }
    }
```

### Logging

Cache operations are logged at appropriate levels:

- **DEBUG**: Cache hits/misses, key operations
- **INFO**: Initialization, statistics
- **WARNING**: Connection failures, low hit rates
- **ERROR**: Critical failures

## Performance Considerations

### Connection Pool Sizing

- **Default**: 10 connections
- **High Load**: Increase to 20-50 connections
- **Low Load**: Reduce to 5 connections to save resources

### TTL Tuning

- **Client Preferences**: 1 hour (good balance between freshness and performance)
- **Templates**: Indefinite (templates rarely change)
- **Rate Limits**: Match API window (e.g., 60s for per-minute limits)

### Memory Usage

Monitor Redis memory usage:

```bash
redis-cli INFO memory
```

Estimate memory per cached item:
- Client Preferences: ~500 bytes
- Email Template: ~5-50 KB
- Rate Limit Counter: ~100 bytes

## Troubleshooting

### Cache Not Working

1. Check Redis connection:
   ```bash
   redis-cli ping
   ```

2. Verify environment variables:
   ```python
   import os
   print(os.getenv('REDIS_URL'))
   print(os.getenv('ENABLE_CACHING'))
   ```

3. Check logs for connection errors:
   ```
   grep "Redis" logs/event_planning.log
   ```

### Low Hit Rate

1. Verify TTL settings aren't too short
2. Check if cache is being invalidated too frequently
3. Monitor cache statistics over time

### Connection Pool Exhausted

1. Increase `max_connections` setting
2. Check for connection leaks (connections not being released)
3. Monitor connection pool usage in stats

## Best Practices

1. **Always Use Context Manager**: Ensures proper cleanup
   ```python
   with CRMCacheManager(redis_url=url) as cache:
       # Use cache
       pass
   ```

2. **Graceful Degradation**: Cache failures shouldn't break functionality
   ```python
   cached = cache_manager.get_client_preferences(client_id)
   if cached is None:
       # Fall back to database
       return repository.get_client_preferences(client_id)
   ```

3. **Invalidate on Updates**: Always invalidate cache when data changes
   ```python
   repository.save_client_preferences(preferences)
   cache_manager.invalidate_client_preferences(client_id)
   ```

4. **Monitor Performance**: Track cache hit rates and adjust TTLs accordingly

5. **Test Without Cache**: Ensure system works when caching is disabled

## Security Considerations

1. **Redis Authentication**: Use password-protected Redis in production
   ```bash
   REDIS_URL=redis://:password@localhost:6379/0
   ```

2. **Network Security**: Use TLS for Redis connections in production
   ```bash
   REDIS_URL=rediss://localhost:6379/0
   ```

3. **Data Sensitivity**: Don't cache highly sensitive data without encryption

4. **Access Control**: Restrict Redis access to application servers only

## Deployment

### Development

```bash
# Start Redis locally
docker run -d -p 6379:6379 redis:7-alpine

# Or use docker-compose
docker-compose up -d redis
```

### Production

1. Use managed Redis service (AWS ElastiCache, Azure Cache for Redis, etc.)
2. Enable persistence (RDB or AOF)
3. Set up replication for high availability
4. Configure monitoring and alerting
5. Use TLS encryption
6. Enable authentication

## Testing

Run cache manager tests:

```bash
# Run all cache tests
pytest event_planning_agent_v2/tests/unit/test_cache_manager.py -v

# Run with coverage
pytest event_planning_agent_v2/tests/unit/test_cache_manager.py --cov=event_planning_agent_v2.crm.cache_manager

# Run specific test
pytest event_planning_agent_v2/tests/unit/test_cache_manager.py::TestCRMCacheManager::test_get_client_preferences_cache_hit -v
```

## References

- [Redis Documentation](https://redis.io/documentation)
- [redis-py Documentation](https://redis-py.readthedocs.io/)
- [Connection Pooling Best Practices](https://redis.io/docs/manual/patterns/connection-pooling/)
- [Redis Memory Optimization](https://redis.io/docs/manual/optimization/memory-optimization/)
