"""
Monitoring initialization for CRM Communication Engine.

This module initializes all monitoring components including metrics,
logging, health checks, and alerting.
"""

import logging
from typing import Optional
from .metrics import initialize_metrics, MetricsCollector
from .logging_config import configure_crm_logging
from .health_check import initialize_health_checker, CRMHealthChecker
from .alerting_rules import get_alert_manager

logger = logging.getLogger(__name__)


def initialize_crm_monitoring(
    version: str = "2.0.0",
    environment: str = "production",
    log_level: str = "INFO",
    enable_json_logging: bool = True,
    log_file: Optional[str] = None,
    email_agent=None,
    messaging_agent=None,
    repository=None,
    cache_manager=None
) -> CRMHealthChecker:
    """
    Initialize all CRM monitoring components.
    
    This function should be called during application startup to set up:
    - Prometheus metrics
    - Structured logging
    - Health checks
    - Alert manager
    
    Args:
        version: CRM engine version
        environment: Environment name (development, staging, production)
        log_level: Logging level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json_logging: Enable JSON-formatted structured logging
        log_file: Optional log file path
        email_agent: Email sub-agent instance
        messaging_agent: Messaging sub-agent instance
        repository: Communication repository instance
        cache_manager: Cache manager instance
        
    Returns:
        CRMHealthChecker instance
    """
    logger.info("Initializing CRM monitoring components...")
    
    # 1. Initialize Prometheus metrics
    try:
        initialize_metrics()
        MetricsCollector.set_system_info(version=version, environment=environment)
        logger.info("✓ Prometheus metrics initialized")
    except Exception as e:
        logger.error(f"Failed to initialize metrics: {e}")
    
    # 2. Configure structured logging
    try:
        configure_crm_logging(
            log_level=log_level,
            enable_json=enable_json_logging,
            log_file=log_file
        )
        logger.info("✓ Structured logging configured")
    except Exception as e:
        logger.error(f"Failed to configure logging: {e}")
    
    # 3. Initialize health checker
    try:
        health_checker = initialize_health_checker(
            version=version,
            email_agent=email_agent,
            messaging_agent=messaging_agent,
            repository=repository,
            cache_manager=cache_manager
        )
        logger.info("✓ Health checker initialized")
    except Exception as e:
        logger.error(f"Failed to initialize health checker: {e}")
        health_checker = None
    
    # 4. Initialize alert manager
    try:
        alert_manager = get_alert_manager()
        logger.info(f"✓ Alert manager initialized with {len(alert_manager.conditions)} conditions")
    except Exception as e:
        logger.error(f"Failed to initialize alert manager: {e}")
    
    logger.info("CRM monitoring initialization complete")
    
    return health_checker


def shutdown_crm_monitoring():
    """
    Shutdown CRM monitoring components.
    
    This function should be called during application shutdown to clean up
    monitoring resources.
    """
    logger.info("Shutting down CRM monitoring components...")
    
    # Add any cleanup logic here
    # For example, flushing metrics, closing log files, etc.
    
    logger.info("CRM monitoring shutdown complete")
