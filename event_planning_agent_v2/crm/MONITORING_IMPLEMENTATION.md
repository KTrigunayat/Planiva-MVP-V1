# CRM Communication Engine - Monitoring and Observability Implementation

## Overview

This document describes the monitoring and observability implementation for the CRM Communication Engine, including Prometheus metrics, structured logging, health checks, and alerting.

## Components

### 1. Prometheus Metrics (`metrics.py`)

#### Available Metrics

**Communication Metrics:**
- `crm_communications_total` - Counter tracking total communications sent by message type, channel, and status
- `crm_delivery_time_seconds` - Histogram tracking delivery time from send to delivery
- `crm_open_rate` - Gauge tracking email open rate by message type
- `crm_click_rate` - Gauge tracking email click-through rate by message type

**Error and Retry Metrics:**
- `crm_api_errors_total` - Counter tracking API errors by provider and error type
- `crm_retry_attempts_total` - Counter tracking retry attempts by channel and attempt number
- `crm_fallback_used_total` - Counter tracking fallback channel usage

**System Metrics:**
- `crm_channel_availability` - Gauge indicating channel availability (1=available, 0=unavailable)
- `crm_active_communications` - Gauge tracking number of communications currently being processed
- `crm_queue_size` - Gauge tracking queue size by priority level
- `crm_info` - Info metric with CRM version and environment

#### Usage Example

```python
from event_planning_agent_v2.crm import MetricsCollector, initialize_metrics

# Initialize metrics on startup
initialize_metrics()

# Record a communication sent
MetricsCollector.record_communication_sent(
    message_type="budget_summary",
    channel="email",
    status="delivered"
)

# Record delivery time
MetricsCollector.record_delivery_time(
    channel="email",
    delivery_time_seconds=5.2
)

# Record API error
MetricsCollector.record_api_error(
    api="twilio",
    error_type="rate_limit"
)
```

### 2. Structured Logging (`logging_config.py`)

#### Log Levels

- **DEBUG**: Template rendering, cache hits/misses, detailed flow
- **INFO**: Communication sent, delivery confirmed, normal operations
- **WARNING**: Retry attempts, fallback channel used, degraded performance
- **ERROR**: Communication failed, API errors, recoverable errors
- **CRITICAL**: All channels failed, authentication failures, system-wide issues

#### JSON Log Format

```json
{
  "timestamp": "2025-10-27T10:30:00Z",
  "level": "INFO",
  "logger": "event_planning_agent_v2.crm.orchestrator",
  "message": "Communication sent",
  "module": "orchestrator",
  "function": "process_communication_request",
  "line": 145,
  "component": "CRMAgentOrchestrator",
  "event": "communication_sent",
  "plan_id": "abc-123",
  "client_id": "xyz-789",
  "communication_id": "comm-456",
  "channel": "email",
  "message_type": "budget_summary",
  "status": "delivered"
}
```

#### Usage Example

```python
from event_planning_agent_v2.crm import configure_crm_logging, get_crm_logger

# Configure logging on startup
configure_crm_logging(
    log_level="INFO",
    enable_json=True,
    log_file="/var/log/crm/crm.log"
)

# Get a logger instance
logger = get_crm_logger(__name__, component="MyComponent")

# Log with context
logger.info(
    "Processing request",
    plan_id="plan-123",
    client_id="client-456"
)

# Log communication events
logger.communication_sent(
    plan_id="plan-123",
    client_id="client-456",
    communication_id="comm-789",
    channel="email",
    message_type="welcome",
    status="sent"
)
```

### 3. Health Checks (`health_check.py`)

#### Health Check Endpoints

**Comprehensive Health Check:**
```
GET /api/crm/health?include_details=true
```

Response:
```json
{
  "status": "healthy",
  "version": "2.0.0",
  "timestamp": "2025-10-27T10:30:00Z",
  "uptime_seconds": 3600.5,
  "components": {
    "email_agent": {
      "status": "healthy",
      "message": "Email agent operational",
      "last_check": "2025-10-27T10:30:00Z",
      "metadata": {}
    },
    "messaging_agent": {
      "status": "healthy",
      "message": "Messaging agent operational",
      "last_check": "2025-10-27T10:30:00Z",
      "metadata": {}
    },
    "database": {
      "status": "healthy",
      "message": "Database operational",
      "last_check": "2025-10-27T10:30:00Z",
      "metadata": {}
    },
    "cache": {
      "status": "healthy",
      "message": "Cache operational",
      "last_check": "2025-10-27T10:30:00Z",
      "metadata": {}
    }
  }
}
```

**Readiness Check (Kubernetes):**
```
GET /api/crm/health/readiness
```

**Liveness Check (Kubernetes):**
```
GET /api/crm/health/liveness
```

#### Usage Example

```python
from event_planning_agent_v2.crm import initialize_health_checker

# Initialize health checker on startup
health_checker = initialize_health_checker(
    version="2.0.0",
    email_agent=email_agent,
    messaging_agent=messaging_agent,
    repository=repository,
    cache_manager=cache_manager
)

# Perform health check
health_status = await health_checker.check_health(include_details=True)
print(health_status.to_dict())
```

### 4. Alerting (`alerting_rules.py`)

#### Alert Conditions

**CRITICAL Alerts:**
- Authentication failure detected
- All communication channels failed

**HIGH Priority Alerts:**
- Delivery rate below 90%
- API error rate above 5%
- Channel unavailable

**MEDIUM Priority Alerts:**
- Retry rate above 20%
- Email open rate below 40%
- High fallback channel usage

**LOW Priority Alerts:**
- Cache miss rate above 50%

#### Alert Channels

- **PagerDuty**: Critical and high-priority alerts
- **Slack**: High and medium-priority alerts
- **Email**: Medium and low-priority alerts
- **Webhook**: Custom integrations

#### Usage Example

```python
from event_planning_agent_v2.crm import get_alert_manager

# Get alert manager
alert_manager = get_alert_manager()

# Evaluate conditions with current metrics
metrics = {
    "total_sent": 100,
    "delivery_rate": 0.85,  # Below 90% threshold
    "auth_failures": 0,
    "all_channels_failed": False
}

triggered_alerts = alert_manager.evaluate_conditions(metrics)

# Send alerts
for alert in triggered_alerts:
    await alert_manager.send_alert(alert)

# Get active alerts
active_alerts = alert_manager.get_active_alerts(severity=AlertSeverity.CRITICAL)
```

### 5. Prometheus Alerting Rules (`monitoring/rules/crm_alerts.yml`)

Prometheus alerting rules are defined for automated monitoring:

- **CRMAuthenticationFailure**: Triggers on auth errors
- **CRMAllChannelsFailed**: Triggers when all channels fail
- **CRMDeliveryRateLow**: Triggers when delivery rate < 90%
- **CRMAPIErrorRateHigh**: Triggers when API error rate > 5%
- **CRMChannelUnavailable**: Triggers when a channel is down
- **CRMRetryRateHigh**: Triggers when retry rate > 20%
- **CRMEmailOpenRateLow**: Triggers when open rate < 40%
- **CRMDeliveryTimeSlow**: Triggers when 95th percentile > 300s
- **CRMQueueSizeHigh**: Triggers when queue size > 100

## Integration

### Application Startup

```python
from event_planning_agent_v2.crm import initialize_crm_monitoring

# Initialize all monitoring components on startup
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

### Metrics Endpoint

Add Prometheus metrics endpoint to your FastAPI app:

```python
from prometheus_client import generate_latest, CONTENT_TYPE_LATEST
from fastapi import Response

@app.get("/metrics")
async def metrics():
    """Prometheus metrics endpoint."""
    return Response(
        content=generate_latest(),
        media_type=CONTENT_TYPE_LATEST
    )
```

### Grafana Dashboard

Import the provided Grafana dashboard JSON to visualize:
- Communication volume and success rate
- Delivery time percentiles
- Channel performance comparison
- Error rates and retry patterns
- Active alerts

## Monitoring Best Practices

### 1. Metric Collection

- Record metrics at key points in the communication lifecycle
- Use appropriate metric types (Counter, Gauge, Histogram)
- Include relevant labels for filtering and aggregation
- Avoid high-cardinality labels (e.g., don't use communication_id as label)

### 2. Logging

- Use structured logging with consistent field names
- Include correlation IDs (plan_id, client_id, communication_id)
- Log at appropriate levels (don't log sensitive data)
- Use JSON format for production environments

### 3. Health Checks

- Implement health checks for all critical dependencies
- Return appropriate HTTP status codes (200, 503)
- Include component-level details for debugging
- Keep health checks lightweight (< 1 second)

### 4. Alerting

- Set appropriate thresholds based on SLOs
- Use cooldown periods to prevent alert fatigue
- Route alerts to appropriate channels based on severity
- Include actionable information in alert messages

## Troubleshooting

### High API Error Rate

1. Check `crm_api_errors_total` metric for error types
2. Review logs for detailed error messages
3. Verify API credentials and quotas
4. Check external API status pages

### Low Delivery Rate

1. Check `crm_communications_total` by status
2. Review `crm_retry_attempts_total` for retry patterns
3. Check `crm_channel_availability` for channel issues
4. Review logs for specific failure reasons

### Slow Delivery Times

1. Check `crm_delivery_time_seconds` histogram
2. Review `crm_active_communications` for processing bottlenecks
3. Check database and cache performance
4. Review external API response times

## Configuration

### Environment Variables

```bash
# Logging
CRM_LOG_LEVEL=INFO
CRM_LOG_FILE=/var/log/crm/crm.log
CRM_ENABLE_JSON_LOGGING=true

# Metrics
CRM_METRICS_PORT=8000
CRM_METRICS_PATH=/metrics

# Health Checks
CRM_HEALTH_CHECK_INTERVAL=30

# Alerting
CRM_ALERT_PAGERDUTY_KEY=<key>
CRM_ALERT_SLACK_WEBHOOK=<webhook>
CRM_ALERT_EMAIL_TO=ops@example.com
```

### Prometheus Configuration

Update `prometheus.yml` to scrape CRM metrics:

```yaml
scrape_configs:
  - job_name: 'crm-communication-engine'
    static_configs:
      - targets: ['crm-api:8000']
    metrics_path: '/metrics'
    scrape_interval: 15s
```

### Alertmanager Configuration

Configure alert routing in `alertmanager.yml`:

```yaml
route:
  group_by: ['alertname', 'severity']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 12h
  receiver: 'default'
  routes:
    - match:
        severity: critical
      receiver: 'pagerduty'
    - match:
        severity: high
      receiver: 'slack'
    - match:
        severity: medium
      receiver: 'email'

receivers:
  - name: 'pagerduty'
    pagerduty_configs:
      - service_key: '<key>'
  - name: 'slack'
    slack_configs:
      - api_url: '<webhook>'
        channel: '#alerts'
  - name: 'email'
    email_configs:
      - to: 'ops@example.com'
```

## Testing

### Unit Tests

```python
import pytest
from event_planning_agent_v2.crm import MetricsCollector, get_crm_logger

def test_metrics_collection():
    """Test metrics are recorded correctly."""
    MetricsCollector.record_communication_sent(
        message_type="welcome",
        channel="email",
        status="delivered"
    )
    # Assert metric value increased

def test_structured_logging():
    """Test structured logging format."""
    logger = get_crm_logger(__name__)
    logger.info("Test message", plan_id="test-123")
    # Assert log entry contains expected fields
```

### Integration Tests

```python
async def test_health_check_endpoint():
    """Test health check endpoint."""
    response = await client.get("/api/crm/health")
    assert response.status_code == 200
    data = response.json()
    assert data["status"] in ["healthy", "degraded", "unhealthy"]
    assert "components" in data

async def test_metrics_endpoint():
    """Test Prometheus metrics endpoint."""
    response = await client.get("/metrics")
    assert response.status_code == 200
    assert "crm_communications_total" in response.text
```

## Performance Impact

The monitoring implementation has minimal performance impact:

- **Metrics**: < 1ms per metric recording
- **Logging**: < 2ms per log entry (JSON format)
- **Health Checks**: < 100ms per check
- **Alerting**: Evaluated asynchronously, no impact on request path

## Future Enhancements

1. **Distributed Tracing**: Add OpenTelemetry for request tracing
2. **Custom Dashboards**: Create role-specific Grafana dashboards
3. **Anomaly Detection**: ML-based anomaly detection for metrics
4. **Log Aggregation**: Integration with ELK stack or Splunk
5. **SLO Tracking**: Automated SLO/SLA monitoring and reporting
