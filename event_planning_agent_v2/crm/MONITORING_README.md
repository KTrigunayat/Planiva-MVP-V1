# CRM Communication Engine - Monitoring & Observability

## Quick Start

### 1. Initialize Monitoring on Application Startup

```python
from event_planning_agent_v2.crm import initialize_crm_monitoring

# Initialize all monitoring components
health_checker = initialize_crm_monitoring(
    version="2.0.0",
    environment="production",
    log_level="INFO",
    enable_json_logging=True,
    log_file="/var/log/crm/crm.log",
    email_agent=email_agent,
    messaging_agent=messaging_agent,
    repository=repository,
    cache_manager=cache_manager
)
```

### 2. Add Metrics Endpoint to FastAPI

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

@app.get("/metrics")
async def metrics():
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### 3. Configure Prometheus

Add to `prometheus.yml`:

```yaml
scrape_configs:
  - job_name: 'crm-communication-engine'
    static_configs:
      - targets: ['localhost:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### 4. Load Alert Rules

```yaml
rule_files:
  - "/etc/prometheus/rules/crm_alerts.yml"
```

## Available Endpoints

### Health Checks
- `GET /api/crm/health` - Comprehensive health status
- `GET /api/crm/health/readiness` - Kubernetes readiness probe
- `GET /api/crm/health/liveness` - Kubernetes liveness probe

### Metrics
- `GET /metrics` - Prometheus metrics endpoint
- `GET /api/crm/metrics/summary` - Human-readable metrics summary

### Alerts
- `GET /api/crm/alerts` - Active alerts
- `GET /api/crm/alerts?severity=critical` - Filter by severity

## Key Metrics

| Metric | Type | Description |
|--------|------|-------------|
| `crm_communications_total` | Counter | Total communications sent |
| `crm_delivery_time_seconds` | Histogram | Time from send to delivery |
| `crm_open_rate` | Gauge | Email open rate by message type |
| `crm_api_errors_total` | Counter | API errors by provider |
| `crm_retry_attempts_total` | Counter | Retry attempts by channel |
| `crm_channel_availability` | Gauge | Channel availability status |

## Alert Conditions

### Critical
- Authentication failure detected
- All communication channels failed

### High
- Delivery rate below 90%
- API error rate above 5%
- Channel unavailable

### Medium
- Retry rate above 20%
- Email open rate below 40%
- High fallback usage

## Log Levels

- **DEBUG**: Cache operations, template rendering
- **INFO**: Communications sent, normal operations
- **WARNING**: Retries, fallback usage
- **ERROR**: Communication failures, API errors
- **CRITICAL**: System-wide failures, auth issues

## Testing

Run the test suite:

```bash
cd event_planning_agent_v2/crm
python test_monitoring.py
```

## Documentation

- [MONITORING_IMPLEMENTATION.md](./MONITORING_IMPLEMENTATION.md) - Complete implementation guide
- [MONITORING_SUMMARY.md](./MONITORING_SUMMARY.md) - Implementation summary

## Support

For issues or questions about monitoring:
1. Check the logs: `/var/log/crm/crm.log`
2. Review active alerts: `GET /api/crm/alerts`
3. Check component health: `GET /api/crm/health?include_details=true`
4. Review metrics: `GET /metrics`
