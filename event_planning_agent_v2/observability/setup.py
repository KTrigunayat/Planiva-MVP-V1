"""
Setup and initialization for the observability system.

Provides centralized configuration and initialization for all observability
components including logging, metrics, tracing, and health checks.
"""

import os
import logging
from typing import Dict, Any, Optional
from pathlib import Path

from .logging import setup_default_logging, LogLevel, get_logger_manager
from .metrics import setup_default_metrics, get_metrics_collector
from .tracing import setup_default_tracing, get_tracer
from .health import setup_default_health_checks, get_health_checker
from ..error_handling.monitoring import setup_default_monitoring, get_error_monitor

logger = None  # Will be initialized after logging setup


class ObservabilityConfig:
    """Configuration for observability system"""
    
    def __init__(
        self,
        # Logging configuration
        log_level: LogLevel = LogLevel.INFO,
        log_directory: str = "logs",
        enable_console_logging: bool = True,
        enable_file_logging: bool = True,
        
        # Metrics configuration
        enable_metrics: bool = True,
        metrics_collection_interval: int = 30,
        
        # Tracing configuration
        enable_tracing: bool = True,
        trace_retention_hours: int = 24,
        max_spans_per_trace: int = 1000,
        
        # Health checks configuration
        enable_health_checks: bool = True,
        health_check_interval: int = 30,
        
        # Error monitoring configuration
        enable_error_monitoring: bool = True,
        error_monitoring_interval: int = 30,
        
        # Integration configuration
        correlation_id_header: str = "X-Correlation-Id",
        trace_id_header: str = "X-Trace-Id"
    ):
        self.log_level = log_level
        self.log_directory = log_directory
        self.enable_console_logging = enable_console_logging
        self.enable_file_logging = enable_file_logging
        
        self.enable_metrics = enable_metrics
        self.metrics_collection_interval = metrics_collection_interval
        
        self.enable_tracing = enable_tracing
        self.trace_retention_hours = trace_retention_hours
        self.max_spans_per_trace = max_spans_per_trace
        
        self.enable_health_checks = enable_health_checks
        self.health_check_interval = health_check_interval
        
        self.enable_error_monitoring = enable_error_monitoring
        self.error_monitoring_interval = error_monitoring_interval
        
        self.correlation_id_header = correlation_id_header
        self.trace_id_header = trace_id_header
    
    @classmethod
    def from_environment(cls) -> 'ObservabilityConfig':
        """Create configuration from environment variables"""
        return cls(
            log_level=LogLevel(os.getenv("LOG_LEVEL", "INFO")),
            log_directory=os.getenv("LOG_DIRECTORY", "logs"),
            enable_console_logging=os.getenv("ENABLE_CONSOLE_LOGGING", "true").lower() == "true",
            enable_file_logging=os.getenv("ENABLE_FILE_LOGGING", "true").lower() == "true",
            
            enable_metrics=os.getenv("ENABLE_METRICS", "true").lower() == "true",
            metrics_collection_interval=int(os.getenv("METRICS_COLLECTION_INTERVAL", "30")),
            
            enable_tracing=os.getenv("ENABLE_TRACING", "true").lower() == "true",
            trace_retention_hours=int(os.getenv("TRACE_RETENTION_HOURS", "24")),
            max_spans_per_trace=int(os.getenv("MAX_SPANS_PER_TRACE", "1000")),
            
            enable_health_checks=os.getenv("ENABLE_HEALTH_CHECKS", "true").lower() == "true",
            health_check_interval=int(os.getenv("HEALTH_CHECK_INTERVAL", "30")),
            
            enable_error_monitoring=os.getenv("ENABLE_ERROR_MONITORING", "true").lower() == "true",
            error_monitoring_interval=int(os.getenv("ERROR_MONITORING_INTERVAL", "30")),
            
            correlation_id_header=os.getenv("CORRELATION_ID_HEADER", "X-Correlation-Id"),
            trace_id_header=os.getenv("TRACE_ID_HEADER", "X-Trace-Id")
        )


def setup_observability(config: Optional[ObservabilityConfig] = None) -> Dict[str, Any]:
    """
    Setup comprehensive observability system.
    
    Args:
        config: Optional configuration. If None, uses environment-based config.
        
    Returns:
        Dictionary with setup results and component references
    """
    if config is None:
        config = ObservabilityConfig.from_environment()
    
    setup_results = {}
    
    # 1. Setup logging first (needed by other components)
    if config.enable_console_logging or config.enable_file_logging:
        try:
            setup_default_logging(
                level=config.log_level,
                log_directory=config.log_directory
            )
            
            # Configure logger manager
            logger_manager = get_logger_manager()
            logger_manager.configure_logging(
                level=config.log_level,
                include_console=config.enable_console_logging,
                include_file=config.enable_file_logging,
                log_directory=config.log_directory
            )
            
            setup_results["logging"] = {
                "status": "success",
                "log_directory": config.log_directory,
                "log_level": config.log_level.value
            }
            
            # Now we can use logger
            global logger
            logger = get_logger_manager().get_logger(__name__, component="observability_setup")
            logger.info("Logging system initialized")
            
        except Exception as e:
            setup_results["logging"] = {"status": "failed", "error": str(e)}
            print(f"Failed to setup logging: {e}")  # Fallback to print
    
    # 2. Setup metrics collection
    if config.enable_metrics:
        try:
            setup_default_metrics()
            
            metrics_collector = get_metrics_collector()
            metrics_collector.collection_interval = config.metrics_collection_interval
            
            setup_results["metrics"] = {
                "status": "success",
                "collection_interval": config.metrics_collection_interval
            }
            
            if logger:
                logger.info("Metrics collection initialized")
                
        except Exception as e:
            setup_results["metrics"] = {"status": "failed", "error": str(e)}
            if logger:
                logger.error(f"Failed to setup metrics: {e}")
    
    # 3. Setup distributed tracing
    if config.enable_tracing:
        try:
            setup_default_tracing()
            
            tracer = get_tracer()
            tracer.span_retention_hours = config.trace_retention_hours
            tracer.max_spans_per_trace = config.max_spans_per_trace
            
            setup_results["tracing"] = {
                "status": "success",
                "retention_hours": config.trace_retention_hours,
                "max_spans_per_trace": config.max_spans_per_trace
            }
            
            if logger:
                logger.info("Distributed tracing initialized")
                
        except Exception as e:
            setup_results["tracing"] = {"status": "failed", "error": str(e)}
            if logger:
                logger.error(f"Failed to setup tracing: {e}")
    
    # 4. Setup health checks
    if config.enable_health_checks:
        try:
            setup_default_health_checks()
            
            health_checker = get_health_checker()
            health_checker.check_interval = config.health_check_interval
            
            setup_results["health_checks"] = {
                "status": "success",
                "check_interval": config.health_check_interval
            }
            
            if logger:
                logger.info("Health checking initialized")
                
        except Exception as e:
            setup_results["health_checks"] = {"status": "failed", "error": str(e)}
            if logger:
                logger.error(f"Failed to setup health checks: {e}")
    
    # 5. Setup error monitoring
    if config.enable_error_monitoring:
        try:
            setup_default_monitoring()
            
            error_monitor = get_error_monitor()
            error_monitor.monitoring_interval = config.error_monitoring_interval
            
            setup_results["error_monitoring"] = {
                "status": "success",
                "monitoring_interval": config.error_monitoring_interval
            }
            
            if logger:
                logger.info("Error monitoring initialized")
                
        except Exception as e:
            setup_results["error_monitoring"] = {"status": "failed", "error": str(e)}
            if logger:
                logger.error(f"Failed to setup error monitoring: {e}")
    
    # 6. Setup integration points
    try:
        # Configure header names for correlation and tracing
        setup_results["integration"] = {
            "status": "success",
            "correlation_id_header": config.correlation_id_header,
            "trace_id_header": config.trace_id_header
        }
        
        if logger:
            logger.info("Observability integration configured")
            
    except Exception as e:
        setup_results["integration"] = {"status": "failed", "error": str(e)}
        if logger:
            logger.error(f"Failed to setup integration: {e}")
    
    # Log overall setup results
    if logger:
        successful_components = [k for k, v in setup_results.items() if v.get("status") == "success"]
        failed_components = [k for k, v in setup_results.items() if v.get("status") == "failed"]
        
        logger.info(
            f"Observability setup completed",
            operation="observability_setup",
            metadata={
                "successful_components": successful_components,
                "failed_components": failed_components,
                "total_components": len(setup_results)
            }
        )
        
        if failed_components:
            logger.warning(f"Some observability components failed to initialize: {failed_components}")
    
    return setup_results


def shutdown_observability():
    """Shutdown observability system gracefully"""
    global logger
    
    if logger:
        logger.info("Shutting down observability system")
    
    shutdown_results = {}
    
    # Stop error monitoring
    try:
        error_monitor = get_error_monitor()
        error_monitor.stop_monitoring_service()
        shutdown_results["error_monitoring"] = "stopped"
    except Exception as e:
        shutdown_results["error_monitoring"] = f"error: {e}"
    
    # Stop health checks
    try:
        health_checker = get_health_checker()
        health_checker.stop_health_checking()
        shutdown_results["health_checks"] = "stopped"
    except Exception as e:
        shutdown_results["health_checks"] = f"error: {e}"
    
    # Stop tracing
    try:
        tracer = get_tracer()
        tracer.stop_tracing()
        shutdown_results["tracing"] = "stopped"
    except Exception as e:
        shutdown_results["tracing"] = f"error: {e}"
    
    # Stop metrics collection
    try:
        metrics_collector = get_metrics_collector()
        metrics_collector.stop_collection()
        shutdown_results["metrics"] = "stopped"
    except Exception as e:
        shutdown_results["metrics"] = f"error: {e}"
    
    if logger:
        logger.info("Observability system shutdown completed", metadata=shutdown_results)
    
    return shutdown_results


def get_observability_status() -> Dict[str, Any]:
    """Get current status of observability components"""
    status = {}
    
    # Logging status
    try:
        logger_manager = get_logger_manager()
        status["logging"] = {
            "active_loggers": len(logger_manager.loggers),
            "default_level": logger_manager.default_config.get("level", "unknown")
        }
    except Exception as e:
        status["logging"] = {"error": str(e)}
    
    # Metrics status
    try:
        metrics_collector = get_metrics_collector()
        status["metrics"] = {
            "collection_enabled": metrics_collector.collection_enabled,
            "total_metrics": len(metrics_collector.metrics),
            "agent_metrics": len(metrics_collector.agent_metrics),
            "workflow_metrics": len(metrics_collector.workflow_metrics)
        }
    except Exception as e:
        status["metrics"] = {"error": str(e)}
    
    # Tracing status
    try:
        tracer = get_tracer()
        status["tracing"] = {
            "enabled": tracer.enabled,
            "total_spans": len(tracer.spans),
            "total_traces": len(tracer.traces),
            "cleanup_enabled": tracer.cleanup_enabled
        }
    except Exception as e:
        status["tracing"] = {"error": str(e)}
    
    # Health checks status
    try:
        health_checker = get_health_checker()
        status["health_checks"] = {
            "check_enabled": health_checker.check_enabled,
            "registered_checks": len(health_checker.health_checks),
            "component_health": len(health_checker.component_health)
        }
    except Exception as e:
        status["health_checks"] = {"error": str(e)}
    
    # Error monitoring status
    try:
        error_monitor = get_error_monitor()
        status["error_monitoring"] = {
            "monitoring_enabled": error_monitor.monitoring_enabled,
            "total_errors": len(error_monitor.error_events),
            "active_alerts": len(error_monitor.alert_manager.get_active_alerts())
        }
    except Exception as e:
        status["error_monitoring"] = {"error": str(e)}
    
    return status


def create_observability_dashboard_data() -> Dict[str, Any]:
    """Create data for observability dashboard"""
    try:
        # Get system health
        health_checker = get_health_checker()
        system_health = health_checker.get_system_health()
        
        # Get metrics summary
        metrics_collector = get_metrics_collector()
        metrics_summary = metrics_collector.get_metrics_summary(window_minutes=60)
        
        # Get error monitoring data
        error_monitor = get_error_monitor()
        health_report = error_monitor.get_health_report()
        
        # Get tracing data
        tracer = get_tracer()
        
        return {
            "timestamp": system_health.timestamp.isoformat(),
            "system_health": system_health.to_dict(),
            "metrics_summary": metrics_summary,
            "error_report": health_report,
            "tracing_stats": {
                "total_spans": len(tracer.spans),
                "total_traces": len(tracer.traces),
                "enabled": tracer.enabled
            },
            "observability_status": get_observability_status()
        }
        
    except Exception as e:
        return {
            "error": str(e),
            "timestamp": "unknown"
        }


# Environment-based initialization
def init_from_environment():
    """Initialize observability from environment variables"""
    config = ObservabilityConfig.from_environment()
    return setup_observability(config)


# Quick setup functions for different environments
def setup_development_observability():
    """Setup observability for development environment"""
    config = ObservabilityConfig(
        log_level=LogLevel.DEBUG,
        enable_console_logging=True,
        enable_file_logging=True,
        enable_metrics=True,
        enable_tracing=True,
        enable_health_checks=True,
        enable_error_monitoring=True
    )
    return setup_observability(config)


def setup_production_observability():
    """Setup observability for production environment"""
    config = ObservabilityConfig(
        log_level=LogLevel.INFO,
        enable_console_logging=False,  # Use structured logging to files/external systems
        enable_file_logging=True,
        enable_metrics=True,
        enable_tracing=True,
        enable_health_checks=True,
        enable_error_monitoring=True,
        trace_retention_hours=12,  # Shorter retention in production
        metrics_collection_interval=60  # Less frequent collection
    )
    return setup_observability(config)


def setup_testing_observability():
    """Setup observability for testing environment"""
    config = ObservabilityConfig(
        log_level=LogLevel.WARNING,
        enable_console_logging=False,
        enable_file_logging=False,
        enable_metrics=False,
        enable_tracing=False,
        enable_health_checks=False,
        enable_error_monitoring=False
    )
    return setup_observability(config)