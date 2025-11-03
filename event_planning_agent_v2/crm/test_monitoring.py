"""
Test script for CRM monitoring and observability components.

This script demonstrates the usage of metrics, logging, health checks,
and alerting in the CRM Communication Engine.
"""

import asyncio
import logging
from datetime import datetime

# Import monitoring components
from .metrics import MetricsCollector, initialize_metrics
from .logging_config import configure_crm_logging, get_crm_logger
from .health_check import initialize_health_checker
from .alerting_rules import get_alert_manager, AlertSeverity
from .monitoring_init import initialize_crm_monitoring

# Configure basic logging for test output
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


async def test_metrics():
    """Test Prometheus metrics collection."""
    print("\n=== Testing Metrics ===")
    
    # Initialize metrics
    initialize_metrics()
    print("✓ Metrics initialized")
    
    # Record some sample metrics
    MetricsCollector.record_communication_sent(
        message_type="welcome",
        channel="email",
        status="delivered"
    )
    print("✓ Recorded communication sent metric")
    
    MetricsCollector.record_delivery_time(
        channel="email",
        delivery_time_seconds=5.2
    )
    print("✓ Recorded delivery time metric")
    
    MetricsCollector.record_api_error(
        api="twilio",
        error_type="rate_limit"
    )
    print("✓ Recorded API error metric")
    
    MetricsCollector.record_retry_attempt(
        channel="sms",
        attempt_number=2
    )
    print("✓ Recorded retry attempt metric")
    
    MetricsCollector.record_fallback_used(
        primary_channel="whatsapp",
        fallback_channel="sms"
    )
    print("✓ Recorded fallback usage metric")
    
    MetricsCollector.set_channel_availability("email", True)
    MetricsCollector.set_channel_availability("sms", True)
    MetricsCollector.set_channel_availability("whatsapp", False)
    print("✓ Set channel availability metrics")
    
    MetricsCollector.update_open_rate("budget_summary", 0.65)
    MetricsCollector.update_click_rate("budget_summary", 0.25)
    print("✓ Updated engagement rate metrics")
    
    print("\nMetrics collection test completed successfully!")


def test_structured_logging():
    """Test structured logging."""
    print("\n=== Testing Structured Logging ===")
    
    # Configure logging
    configure_crm_logging(
        log_level="INFO",
        enable_json=True,
        log_file=None  # Output to console only
    )
    print("✓ Structured logging configured")
    
    # Get a logger
    crm_logger = get_crm_logger(__name__, component="TestComponent")
    
    # Test different log levels
    crm_logger.debug("Debug message", test_field="debug_value")
    crm_logger.info("Info message", test_field="info_value")
    crm_logger.warning("Warning message", test_field="warning_value")
    crm_logger.error("Error message", test_field="error_value")
    
    # Test specialized logging methods
    crm_logger.communication_sent(
        plan_id="test-plan-123",
        client_id="test-client-456",
        communication_id="test-comm-789",
        channel="email",
        message_type="welcome",
        status="sent"
    )
    print("✓ Logged communication sent event")
    
    crm_logger.retry_attempt(
        communication_id="test-comm-789",
        channel="email",
        attempt_number=2,
        max_retries=3,
        delay_seconds=60.0
    )
    print("✓ Logged retry attempt event")
    
    crm_logger.fallback_used(
        communication_id="test-comm-789",
        primary_channel="whatsapp",
        fallback_channel="sms",
        primary_error="WhatsApp API unavailable"
    )
    print("✓ Logged fallback usage event")
    
    crm_logger.api_error(
        api="twilio",
        error_type="rate_limit",
        error_message="Rate limit exceeded",
        status_code=429
    )
    print("✓ Logged API error event")
    
    print("\nStructured logging test completed successfully!")


async def test_health_checks():
    """Test health check functionality."""
    print("\n=== Testing Health Checks ===")
    
    # Initialize health checker (without actual agents for testing)
    health_checker = initialize_health_checker(
        version="2.0.0",
        email_agent=None,
        messaging_agent=None,
        repository=None,
        cache_manager=None
    )
    print("✓ Health checker initialized")
    
    # Perform health check
    health_status = await health_checker.check_health(include_details=True)
    print(f"✓ Health check completed: status={health_status.status.value}")
    
    # Display component health
    print("\nComponent Health:")
    for name, component in health_status.components.items():
        print(f"  - {name}: {component.status.value} - {component.message}")
    
    # Test readiness and liveness
    readiness = health_checker.get_readiness()
    liveness = health_checker.get_liveness()
    print(f"\n✓ Readiness: {readiness}")
    print(f"✓ Liveness: {liveness}")
    
    print("\nHealth check test completed successfully!")


async def test_alerting():
    """Test alerting functionality."""
    print("\n=== Testing Alerting ===")
    
    # Get alert manager
    alert_manager = get_alert_manager()
    print(f"✓ Alert manager initialized with {len(alert_manager.conditions)} conditions")
    
    # Test with metrics that should trigger alerts
    print("\nTesting alert conditions...")
    
    # Test 1: Low delivery rate (should trigger HIGH alert)
    metrics_low_delivery = {
        "total_sent": 100,
        "delivery_rate": 0.85,  # Below 90% threshold
        "auth_failures": 0,
        "all_channels_failed": False,
        "total_api_calls": 0,
        "api_error_rate": 0.0
    }
    
    alerts = alert_manager.evaluate_conditions(metrics_low_delivery)
    if alerts:
        print(f"✓ Triggered {len(alerts)} alert(s) for low delivery rate:")
        for alert in alerts:
            print(f"  - {alert.condition_name} ({alert.severity.value}): {alert.message}")
    
    # Test 2: Authentication failure (should trigger CRITICAL alert)
    metrics_auth_failure = {
        "total_sent": 50,
        "delivery_rate": 0.95,
        "auth_failures": 1,  # Auth failure detected
        "all_channels_failed": False,
        "total_api_calls": 50,
        "api_error_rate": 0.02
    }
    
    alerts = alert_manager.evaluate_conditions(metrics_auth_failure)
    if alerts:
        print(f"✓ Triggered {len(alerts)} alert(s) for auth failure:")
        for alert in alerts:
            print(f"  - {alert.condition_name} ({alert.severity.value}): {alert.message}")
    
    # Test 3: All channels failed (should trigger CRITICAL alert)
    metrics_all_failed = {
        "total_sent": 20,
        "delivery_rate": 0.0,
        "auth_failures": 0,
        "all_channels_failed": True,  # All channels failed
        "total_api_calls": 20,
        "api_error_rate": 0.0
    }
    
    alerts = alert_manager.evaluate_conditions(metrics_all_failed)
    if alerts:
        print(f"✓ Triggered {len(alerts)} alert(s) for all channels failed:")
        for alert in alerts:
            print(f"  - {alert.condition_name} ({alert.severity.value}): {alert.message}")
    
    # Get active alerts
    active_alerts = alert_manager.get_active_alerts()
    print(f"\n✓ Total active alerts: {len(active_alerts)}")
    
    # Get critical alerts only
    critical_alerts = alert_manager.get_active_alerts(severity=AlertSeverity.CRITICAL)
    print(f"✓ Critical alerts: {len(critical_alerts)}")
    
    print("\nAlerting test completed successfully!")


async def test_full_monitoring_initialization():
    """Test full monitoring initialization."""
    print("\n=== Testing Full Monitoring Initialization ===")
    
    # Initialize all monitoring components
    health_checker = initialize_crm_monitoring(
        version="2.0.0",
        environment="test",
        log_level="INFO",
        enable_json_logging=False,  # Use simple format for test output
        log_file=None,
        email_agent=None,
        messaging_agent=None,
        repository=None,
        cache_manager=None
    )
    
    print("✓ All monitoring components initialized")
    
    # Verify components are working
    if health_checker:
        health_status = await health_checker.check_health(include_details=False)
        print(f"✓ Health status: {health_status.status.value}")
    
    print("\nFull monitoring initialization test completed successfully!")


async def main():
    """Run all tests."""
    print("=" * 60)
    print("CRM Monitoring and Observability Test Suite")
    print("=" * 60)
    
    try:
        # Run tests
        await test_metrics()
        test_structured_logging()
        await test_health_checks()
        await test_alerting()
        await test_full_monitoring_initialization()
        
        print("\n" + "=" * 60)
        print("All tests completed successfully! ✓")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n❌ Test failed with error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    asyncio.run(main())
