"""
Error monitoring and observability system for the Event Planning Agent.

Provides comprehensive error tracking, metrics collection, and alerting
capabilities across all system components.
"""

import logging
import asyncio
import threading
import time
import uuid
from typing import Dict, Any, Optional, List, Callable, Set
from datetime import datetime, timedelta
from enum import Enum
from dataclasses import dataclass, field
from collections import defaultdict, deque
import json
import psutil

from .exceptions import EventPlanningError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)


class AlertLevel(str, Enum):
    """Alert severity levels"""
    INFO = "info"
    WARNING = "warning"
    ERROR = "error"
    CRITICAL = "critical"


class MetricType(str, Enum):
    """Types of metrics to collect"""
    COUNTER = "counter"
    GAUGE = "gauge"
    HISTOGRAM = "histogram"
    TIMER = "timer"


@dataclass
class ErrorEvent:
    """Represents an error event for monitoring"""
    id: str
    timestamp: datetime
    error_type: str
    error_message: str
    component: str
    operation: str
    severity: ErrorSeverity
    category: ErrorCategory
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    resolved: bool = False
    resolution_time: Optional[datetime] = None


@dataclass
class Metric:
    """Represents a system metric"""
    name: str
    value: float
    metric_type: MetricType
    timestamp: datetime
    labels: Dict[str, str] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class Alert:
    """Represents a system alert"""
    id: str
    level: AlertLevel
    title: str
    message: str
    timestamp: datetime
    component: str
    threshold_value: Optional[float] = None
    current_value: Optional[float] = None
    correlation_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    acknowledged: bool = False
    resolved: bool = False


class ErrorMetrics:
    """Collects and manages error-related metrics"""
    
    def __init__(self):
        self.error_counts: Dict[str, int] = defaultdict(int)
        self.error_rates: Dict[str, deque] = defaultdict(lambda: deque(maxlen=100))
        self.component_errors: Dict[str, Dict[str, int]] = defaultdict(lambda: defaultdict(int))
        self.severity_counts: Dict[ErrorSeverity, int] = defaultdict(int)
        self.category_counts: Dict[ErrorCategory, int] = defaultdict(int)
        
        # Time-based metrics
        self.hourly_errors: Dict[str, int] = defaultdict(int)
        self.daily_errors: Dict[str, int] = defaultdict(int)
        
        # Performance metrics
        self.response_times: deque = deque(maxlen=1000)
        self.throughput_metrics: deque = deque(maxlen=100)
        
        # System metrics
        self.system_metrics: Dict[str, float] = {}
        
        self._lock = threading.Lock()
    
    def record_error(self, error_event: ErrorEvent):
        """Record an error event"""
        with self._lock:
            # Update error counts
            error_key = f"{error_event.component}:{error_event.error_type}"
            self.error_counts[error_key] += 1
            
            # Update component errors
            self.component_errors[error_event.component][error_event.error_type] += 1
            
            # Update severity and category counts
            self.severity_counts[error_event.severity] += 1
            self.category_counts[error_event.category] += 1
            
            # Update time-based metrics
            hour_key = error_event.timestamp.strftime("%Y-%m-%d-%H")
            day_key = error_event.timestamp.strftime("%Y-%m-%d")
            self.hourly_errors[hour_key] += 1
            self.daily_errors[day_key] += 1
            
            # Update error rate
            self.error_rates[error_key].append(error_event.timestamp)
    
    def record_response_time(self, response_time_ms: float):
        """Record response time metric"""
        with self._lock:
            self.response_times.append(response_time_ms)
    
    def record_throughput(self, requests_per_second: float):
        """Record throughput metric"""
        with self._lock:
            self.throughput_metrics.append(requests_per_second)
    
    def update_system_metrics(self, metrics: Dict[str, float]):
        """Update system-level metrics"""
        with self._lock:
            self.system_metrics.update(metrics)
    
    def get_error_rate(self, component: str, error_type: str, window_minutes: int = 5) -> float:
        """Calculate error rate for component/error type"""
        with self._lock:
            error_key = f"{component}:{error_type}"
            if error_key not in self.error_rates:
                return 0.0
            
            cutoff_time = datetime.utcnow() - timedelta(minutes=window_minutes)
            recent_errors = [
                ts for ts in self.error_rates[error_key]
                if ts >= cutoff_time
            ]
            
            return len(recent_errors) / (window_minutes * 60)  # errors per second
    
    def get_component_health(self, component: str) -> Dict[str, Any]:
        """Get health metrics for a component"""
        with self._lock:
            component_data = self.component_errors.get(component, {})
            total_errors = sum(component_data.values())
            
            # Calculate error rates
            error_rates = {}
            for error_type in component_data.keys():
                error_rates[error_type] = self.get_error_rate(component, error_type)
            
            return {
                "component": component,
                "total_errors": total_errors,
                "error_types": dict(component_data),
                "error_rates": error_rates,
                "health_score": max(0, 100 - (total_errors * 2))  # Simple health score
            }
    
    def get_system_overview(self) -> Dict[str, Any]:
        """Get system-wide error overview"""
        with self._lock:
            total_errors = sum(self.error_counts.values())
            
            # Calculate average response time
            avg_response_time = (
                sum(self.response_times) / len(self.response_times)
                if self.response_times else 0
            )
            
            # Calculate current throughput
            current_throughput = (
                sum(self.throughput_metrics) / len(self.throughput_metrics)
                if self.throughput_metrics else 0
            )
            
            return {
                "total_errors": total_errors,
                "severity_breakdown": dict(self.severity_counts),
                "category_breakdown": dict(self.category_counts),
                "average_response_time_ms": avg_response_time,
                "current_throughput_rps": current_throughput,
                "system_metrics": dict(self.system_metrics),
                "component_count": len(self.component_errors),
                "active_components": list(self.component_errors.keys())
            }


class AlertManager:
    """Manages system alerts and notifications"""
    
    def __init__(self):
        self.alerts: Dict[str, Alert] = {}
        self.alert_rules: List[Dict[str, Any]] = []
        self.notification_channels: List[Callable] = []
        self.alert_history: deque = deque(maxlen=1000)
        
        # Alert thresholds
        self.thresholds = {
            "error_rate": 5.0,  # errors per minute
            "response_time": 5000.0,  # milliseconds
            "cpu_usage": 80.0,  # percentage
            "memory_usage": 85.0,  # percentage
            "disk_usage": 90.0,  # percentage
        }
        
        self._lock = threading.Lock()
        
        # Initialize default alert rules
        self._initialize_default_rules()
    
    def _initialize_default_rules(self):
        """Initialize default alerting rules"""
        self.alert_rules = [
            {
                "name": "high_error_rate",
                "condition": lambda metrics: self._check_error_rate(metrics),
                "level": AlertLevel.ERROR,
                "message": "High error rate detected"
            },
            {
                "name": "critical_error",
                "condition": lambda metrics: self._check_critical_errors(metrics),
                "level": AlertLevel.CRITICAL,
                "message": "Critical error detected"
            },
            {
                "name": "high_response_time",
                "condition": lambda metrics: self._check_response_time(metrics),
                "level": AlertLevel.WARNING,
                "message": "High response time detected"
            },
            {
                "name": "resource_exhaustion",
                "condition": lambda metrics: self._check_resource_usage(metrics),
                "level": AlertLevel.ERROR,
                "message": "High resource usage detected"
            }
        ]
    
    def add_notification_channel(self, channel: Callable[[Alert], None]):
        """Add notification channel"""
        self.notification_channels.append(channel)
    
    def set_threshold(self, metric_name: str, threshold: float):
        """Set alert threshold for metric"""
        with self._lock:
            self.thresholds[metric_name] = threshold
    
    def create_alert(
        self,
        level: AlertLevel,
        title: str,
        message: str,
        component: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Alert:
        """Create and process new alert"""
        alert = Alert(
            id=str(uuid.uuid4()),
            level=level,
            title=title,
            message=message,
            timestamp=datetime.utcnow(),
            component=component,
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
        
        with self._lock:
            self.alerts[alert.id] = alert
            self.alert_history.append(alert)
        
        # Send notifications
        self._send_notifications(alert)
        
        logger.warning(f"Alert created: {alert.level.value} - {alert.title}")
        return alert
    
    def resolve_alert(self, alert_id: str, resolution_message: Optional[str] = None):
        """Resolve an alert"""
        with self._lock:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.resolved = True
                if resolution_message:
                    alert.metadata["resolution_message"] = resolution_message
                
                logger.info(f"Alert resolved: {alert.title}")
    
    def acknowledge_alert(self, alert_id: str, acknowledged_by: str):
        """Acknowledge an alert"""
        with self._lock:
            if alert_id in self.alerts:
                alert = self.alerts[alert_id]
                alert.acknowledged = True
                alert.metadata["acknowledged_by"] = acknowledged_by
                alert.metadata["acknowledged_at"] = datetime.utcnow().isoformat()
                
                logger.info(f"Alert acknowledged by {acknowledged_by}: {alert.title}")
    
    def evaluate_alerts(self, metrics: Dict[str, Any]):
        """Evaluate alert rules against current metrics"""
        for rule in self.alert_rules:
            try:
                if rule["condition"](metrics):
                    # Check if similar alert already exists
                    existing_alert = self._find_similar_alert(rule["name"])
                    if not existing_alert:
                        self.create_alert(
                            level=rule["level"],
                            title=rule["name"].replace("_", " ").title(),
                            message=rule["message"],
                            component="system",
                            metadata={"rule": rule["name"], "metrics": metrics}
                        )
            except Exception as e:
                logger.error(f"Error evaluating alert rule {rule['name']}: {e}")
    
    def _find_similar_alert(self, rule_name: str) -> Optional[Alert]:
        """Find similar unresolved alert"""
        with self._lock:
            for alert in self.alerts.values():
                if (not alert.resolved and 
                    alert.metadata.get("rule") == rule_name and
                    (datetime.utcnow() - alert.timestamp).total_seconds() < 300):  # 5 minutes
                    return alert
        return None
    
    def _send_notifications(self, alert: Alert):
        """Send alert notifications"""
        for channel in self.notification_channels:
            try:
                channel(alert)
            except Exception as e:
                logger.error(f"Failed to send alert notification: {e}")
    
    def _check_error_rate(self, metrics: Dict[str, Any]) -> bool:
        """Check if error rate exceeds threshold"""
        error_rate = metrics.get("error_rate_per_minute", 0)
        return error_rate > self.thresholds.get("error_rate", 5.0)
    
    def _check_critical_errors(self, metrics: Dict[str, Any]) -> bool:
        """Check for critical errors"""
        severity_breakdown = metrics.get("severity_breakdown", {})
        critical_count = severity_breakdown.get(ErrorSeverity.CRITICAL.value, 0)
        return critical_count > 0
    
    def _check_response_time(self, metrics: Dict[str, Any]) -> bool:
        """Check if response time exceeds threshold"""
        response_time = metrics.get("average_response_time_ms", 0)
        return response_time > self.thresholds.get("response_time", 5000.0)
    
    def _check_resource_usage(self, metrics: Dict[str, Any]) -> bool:
        """Check if resource usage exceeds thresholds"""
        system_metrics = metrics.get("system_metrics", {})
        
        cpu_usage = system_metrics.get("cpu_usage", 0)
        memory_usage = system_metrics.get("memory_usage", 0)
        
        return (cpu_usage > self.thresholds.get("cpu_usage", 80.0) or
                memory_usage > self.thresholds.get("memory_usage", 85.0))
    
    def get_active_alerts(self) -> List[Alert]:
        """Get all active (unresolved) alerts"""
        with self._lock:
            return [alert for alert in self.alerts.values() if not alert.resolved]
    
    def get_alert_summary(self) -> Dict[str, Any]:
        """Get alert summary statistics"""
        with self._lock:
            active_alerts = self.get_active_alerts()
            
            level_counts = defaultdict(int)
            for alert in active_alerts:
                level_counts[alert.level.value] += 1
            
            return {
                "total_active_alerts": len(active_alerts),
                "level_breakdown": dict(level_counts),
                "total_alerts_today": len([
                    alert for alert in self.alert_history
                    if alert.timestamp.date() == datetime.utcnow().date()
                ]),
                "acknowledged_alerts": len([
                    alert for alert in active_alerts if alert.acknowledged
                ])
            }


class ErrorMonitor:
    """Main error monitoring system"""
    
    def __init__(self):
        self.metrics = ErrorMetrics()
        self.alert_manager = AlertManager()
        self.error_events: deque = deque(maxlen=10000)
        
        # Monitoring configuration
        self.monitoring_enabled = True
        self.monitoring_interval = 30  # seconds
        self.correlation_tracking = True
        
        # Background monitoring
        self.monitoring_thread: Optional[threading.Thread] = None
        self.stop_monitoring = threading.Event()
        
        # Correlation tracking
        self.correlations: Dict[str, List[str]] = defaultdict(list)
        
        self._lock = threading.Lock()
    
    def start_monitoring(self):
        """Start background monitoring"""
        if self.monitoring_thread and self.monitoring_thread.is_alive():
            logger.warning("Monitoring already started")
            return
        
        self.stop_monitoring.clear()
        self.monitoring_thread = threading.Thread(target=self._monitoring_loop, daemon=True)
        self.monitoring_thread.start()
        
        logger.info("Error monitoring started")
    
    def stop_monitoring_service(self):
        """Stop background monitoring"""
        self.stop_monitoring.set()
        if self.monitoring_thread:
            self.monitoring_thread.join(timeout=5)
        
        logger.info("Error monitoring stopped")
    
    def record_error(
        self,
        error: Exception,
        component: str,
        operation: str,
        correlation_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Record an error event"""
        if not self.monitoring_enabled:
            return
        
        # Create error event
        error_event = ErrorEvent(
            id=str(uuid.uuid4()),
            timestamp=datetime.utcnow(),
            error_type=type(error).__name__,
            error_message=str(error),
            component=component,
            operation=operation,
            severity=getattr(error, 'severity', ErrorSeverity.MEDIUM),
            category=getattr(error, 'category', ErrorCategory.UNKNOWN),
            correlation_id=correlation_id,
            metadata=metadata or {}
        )
        
        # Store error event
        with self._lock:
            self.error_events.append(error_event)
        
        # Update metrics
        self.metrics.record_error(error_event)
        
        # Track correlations
        if correlation_id and self.correlation_tracking:
            self.correlations[correlation_id].append(error_event.id)
        
        # Check for immediate alerts
        if error_event.severity in [ErrorSeverity.HIGH, ErrorSeverity.CRITICAL]:
            self.alert_manager.create_alert(
                level=AlertLevel.CRITICAL if error_event.severity == ErrorSeverity.CRITICAL else AlertLevel.ERROR,
                title=f"{error_event.severity.value.title()} Error in {component}",
                message=f"{error_event.error_type}: {error_event.error_message}",
                component=component,
                correlation_id=correlation_id,
                metadata={"error_event_id": error_event.id}
            )
        
        logger.debug(f"Error recorded: {error_event.error_type} in {component}")
    
    def record_performance_metric(
        self,
        metric_name: str,
        value: float,
        labels: Optional[Dict[str, str]] = None
    ):
        """Record a performance metric"""
        if metric_name == "response_time_ms":
            self.metrics.record_response_time(value)
        elif metric_name == "throughput_rps":
            self.metrics.record_throughput(value)
    
    def get_error_summary(
        self,
        component: Optional[str] = None,
        time_window_hours: int = 24
    ) -> Dict[str, Any]:
        """Get error summary for component or system"""
        cutoff_time = datetime.utcnow() - timedelta(hours=time_window_hours)
        
        with self._lock:
            # Filter events by time and component
            filtered_events = [
                event for event in self.error_events
                if event.timestamp >= cutoff_time and
                (component is None or event.component == component)
            ]
        
        if not filtered_events:
            return {"total_errors": 0, "time_window_hours": time_window_hours}
        
        # Calculate summary statistics
        error_types = defaultdict(int)
        severity_counts = defaultdict(int)
        component_counts = defaultdict(int)
        
        for event in filtered_events:
            error_types[event.error_type] += 1
            severity_counts[event.severity.value] += 1
            component_counts[event.component] += 1
        
        return {
            "total_errors": len(filtered_events),
            "time_window_hours": time_window_hours,
            "error_types": dict(error_types),
            "severity_breakdown": dict(severity_counts),
            "component_breakdown": dict(component_counts),
            "error_rate_per_hour": len(filtered_events) / time_window_hours,
            "most_common_error": max(error_types.items(), key=lambda x: x[1])[0] if error_types else None,
            "most_affected_component": max(component_counts.items(), key=lambda x: x[1])[0] if component_counts else None
        }
    
    def get_correlation_analysis(self, correlation_id: str) -> Dict[str, Any]:
        """Get correlation analysis for a correlation ID"""
        if correlation_id not in self.correlations:
            return {"correlation_id": correlation_id, "events": []}
        
        event_ids = self.correlations[correlation_id]
        
        with self._lock:
            correlated_events = [
                event for event in self.error_events
                if event.id in event_ids
            ]
        
        if not correlated_events:
            return {"correlation_id": correlation_id, "events": []}
        
        # Analyze correlation patterns
        components = set(event.component for event in correlated_events)
        error_types = set(event.error_type for event in correlated_events)
        
        # Timeline analysis
        sorted_events = sorted(correlated_events, key=lambda x: x.timestamp)
        duration = (sorted_events[-1].timestamp - sorted_events[0].timestamp).total_seconds()
        
        return {
            "correlation_id": correlation_id,
            "total_events": len(correlated_events),
            "affected_components": list(components),
            "error_types": list(error_types),
            "duration_seconds": duration,
            "first_error": sorted_events[0].timestamp.isoformat(),
            "last_error": sorted_events[-1].timestamp.isoformat(),
            "events": [
                {
                    "id": event.id,
                    "timestamp": event.timestamp.isoformat(),
                    "component": event.component,
                    "error_type": event.error_type,
                    "severity": event.severity.value
                }
                for event in sorted_events
            ]
        }
    
    def _monitoring_loop(self):
        """Background monitoring loop"""
        while not self.stop_monitoring.wait(self.monitoring_interval):
            try:
                # Collect system metrics
                system_metrics = self._collect_system_metrics()
                self.metrics.update_system_metrics(system_metrics)
                
                # Get current metrics for alert evaluation
                current_metrics = self.metrics.get_system_overview()
                current_metrics.update(system_metrics)
                
                # Evaluate alerts
                self.alert_manager.evaluate_alerts(current_metrics)
                
                # Clean up old data
                self._cleanup_old_data()
                
            except Exception as e:
                logger.error(f"Error in monitoring loop: {e}")
    
    def _collect_system_metrics(self) -> Dict[str, float]:
        """Collect current system metrics"""
        try:
            # CPU and memory usage
            cpu_usage = psutil.cpu_percent(interval=1)
            memory = psutil.virtual_memory()
            disk = psutil.disk_usage('/')
            
            # Network stats (if available)
            try:
                network = psutil.net_io_counters()
                network_bytes_sent = network.bytes_sent
                network_bytes_recv = network.bytes_recv
            except:
                network_bytes_sent = 0
                network_bytes_recv = 0
            
            return {
                "cpu_usage": cpu_usage,
                "memory_usage": memory.percent,
                "memory_available_gb": memory.available / (1024**3),
                "disk_usage": disk.percent,
                "disk_free_gb": disk.free / (1024**3),
                "network_bytes_sent": network_bytes_sent,
                "network_bytes_recv": network_bytes_recv
            }
            
        except Exception as e:
            logger.error(f"Failed to collect system metrics: {e}")
            return {}
    
    def _cleanup_old_data(self):
        """Clean up old monitoring data"""
        cutoff_time = datetime.utcnow() - timedelta(hours=24)
        
        # Clean up correlations for old events
        with self._lock:
            old_event_ids = {
                event.id for event in self.error_events
                if event.timestamp < cutoff_time
            }
            
            for correlation_id, event_ids in list(self.correlations.items()):
                # Remove old event IDs
                self.correlations[correlation_id] = [
                    eid for eid in event_ids if eid not in old_event_ids
                ]
                
                # Remove empty correlations
                if not self.correlations[correlation_id]:
                    del self.correlations[correlation_id]
    
    def get_health_report(self) -> Dict[str, Any]:
        """Generate comprehensive health report"""
        system_overview = self.metrics.get_system_overview()
        alert_summary = self.alert_manager.get_alert_summary()
        
        # Calculate health score
        health_score = 100
        
        # Deduct points for errors
        total_errors = system_overview.get("total_errors", 0)
        health_score -= min(total_errors * 0.1, 30)  # Max 30 points for errors
        
        # Deduct points for active alerts
        active_alerts = alert_summary.get("total_active_alerts", 0)
        health_score -= min(active_alerts * 5, 25)  # Max 25 points for alerts
        
        # Deduct points for high resource usage
        system_metrics = system_overview.get("system_metrics", {})
        cpu_usage = system_metrics.get("cpu_usage", 0)
        memory_usage = system_metrics.get("memory_usage", 0)
        
        if cpu_usage > 80:
            health_score -= (cpu_usage - 80) * 0.5
        if memory_usage > 85:
            health_score -= (memory_usage - 85) * 0.5
        
        health_score = max(0, health_score)
        
        # Determine health status
        if health_score >= 90:
            health_status = "excellent"
        elif health_score >= 75:
            health_status = "good"
        elif health_score >= 50:
            health_status = "fair"
        elif health_score >= 25:
            health_status = "poor"
        else:
            health_status = "critical"
        
        return {
            "health_score": health_score,
            "health_status": health_status,
            "timestamp": datetime.utcnow().isoformat(),
            "system_overview": system_overview,
            "alert_summary": alert_summary,
            "monitoring_status": {
                "enabled": self.monitoring_enabled,
                "uptime_seconds": (
                    (datetime.utcnow() - datetime.utcnow()).total_seconds()
                    if self.monitoring_thread else 0
                )
            }
        }


# Global error monitor instance
_error_monitor: Optional[ErrorMonitor] = None


def get_error_monitor() -> ErrorMonitor:
    """Get global error monitor instance"""
    global _error_monitor
    if _error_monitor is None:
        _error_monitor = ErrorMonitor()
    return _error_monitor


# Convenience functions
def record_error(
    error: Exception,
    component: str,
    operation: str,
    correlation_id: Optional[str] = None,
    metadata: Optional[Dict[str, Any]] = None
):
    """Record error using global monitor"""
    monitor = get_error_monitor()
    monitor.record_error(error, component, operation, correlation_id, metadata)


def record_performance_metric(
    metric_name: str,
    value: float,
    labels: Optional[Dict[str, str]] = None
):
    """Record performance metric using global monitor"""
    monitor = get_error_monitor()
    monitor.record_performance_metric(metric_name, value, labels)


def get_system_health() -> Dict[str, Any]:
    """Get system health report"""
    monitor = get_error_monitor()
    return monitor.get_health_report()


# Notification channel implementations
def console_notification_channel(alert: Alert):
    """Console notification channel"""
    print(f"ALERT [{alert.level.value.upper()}] {alert.title}: {alert.message}")


def log_notification_channel(alert: Alert):
    """Log file notification channel"""
    logger.warning(f"Alert: {alert.level.value} - {alert.title} - {alert.message}")


# Initialize default notification channels
def setup_default_monitoring():
    """Setup default monitoring configuration"""
    monitor = get_error_monitor()
    
    # Add default notification channels
    monitor.alert_manager.add_notification_channel(console_notification_channel)
    monitor.alert_manager.add_notification_channel(log_notification_channel)
    
    # Start monitoring
    monitor.start_monitoring()
    
    logger.info("Default error monitoring setup completed")