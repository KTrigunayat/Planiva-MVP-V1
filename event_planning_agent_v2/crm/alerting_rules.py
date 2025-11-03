"""
Alerting rules and conditions for CRM Communication Engine.

Defines alert conditions, severity levels, and notification logic
for critical CRM events.
"""

import logging
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime, timezone
from enum import Enum
from dataclasses import dataclass, field

logger = logging.getLogger(__name__)


class AlertSeverity(str, Enum):
    """Alert severity levels."""
    CRITICAL = "critical"  # Immediate action required
    HIGH = "high"          # Action required soon
    MEDIUM = "medium"      # Should be investigated
    LOW = "low"            # Informational


class AlertChannel(str, Enum):
    """Alert notification channels."""
    PAGERDUTY = "pagerduty"
    SLACK = "slack"
    EMAIL = "email"
    WEBHOOK = "webhook"


@dataclass
class AlertCondition:
    """Definition of an alert condition."""
    name: str
    description: str
    severity: AlertSeverity
    condition_func: Callable[[Dict[str, Any]], bool]
    notification_channels: List[AlertChannel]
    cooldown_seconds: int = 300  # 5 minutes default
    last_triggered: Optional[datetime] = None
    
    def should_trigger(self, metrics: Dict[str, Any]) -> bool:
        """
        Check if alert should trigger.
        
        Args:
            metrics: Current metrics
            
        Returns:
            True if alert should trigger
        """
        # Check cooldown
        if self.last_triggered:
            elapsed = (datetime.now(timezone.utc) - self.last_triggered).total_seconds()
            if elapsed < self.cooldown_seconds:
                return False
        
        # Evaluate condition
        try:
            return self.condition_func(metrics)
        except Exception as e:
            logger.error(f"Error evaluating alert condition {self.name}: {e}")
            return False
    
    def trigger(self) -> None:
        """Mark alert as triggered."""
        self.last_triggered = datetime.now(timezone.utc)


@dataclass
class Alert:
    """Alert instance."""
    condition_name: str
    severity: AlertSeverity
    message: str
    timestamp: datetime
    metrics: Dict[str, Any] = field(default_factory=dict)
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "condition": self.condition_name,
            "severity": self.severity.value,
            "message": self.message,
            "timestamp": self.timestamp.isoformat(),
            "metrics": self.metrics,
            "metadata": self.metadata
        }


class AlertManager:
    """
    Manages alert conditions and notifications.
    
    Evaluates alert conditions based on metrics and triggers
    notifications through appropriate channels.
    """
    
    def __init__(self):
        """Initialize alert manager."""
        self.conditions: Dict[str, AlertCondition] = {}
        self.active_alerts: List[Alert] = []
        self._initialize_default_conditions()
        
        logger.info("Alert Manager initialized")
    
    def _initialize_default_conditions(self) -> None:
        """Initialize default alert conditions."""
        
        # CRITICAL: Authentication failure
        self.add_condition(AlertCondition(
            name="auth_failure",
            description="Authentication failure detected for external API",
            severity=AlertSeverity.CRITICAL,
            condition_func=lambda m: m.get("auth_failures", 0) > 0,
            notification_channels=[AlertChannel.PAGERDUTY, AlertChannel.SLACK],
            cooldown_seconds=60  # 1 minute
        ))
        
        # CRITICAL: All channels failed
        self.add_condition(AlertCondition(
            name="all_channels_failed",
            description="All communication channels failed for a message",
            severity=AlertSeverity.CRITICAL,
            condition_func=lambda m: m.get("all_channels_failed", False),
            notification_channels=[AlertChannel.PAGERDUTY, AlertChannel.SLACK],
            cooldown_seconds=300  # 5 minutes
        ))
        
        # HIGH: Delivery rate below 90%
        self.add_condition(AlertCondition(
            name="low_delivery_rate",
            description="Communication delivery rate below 90%",
            severity=AlertSeverity.HIGH,
            condition_func=lambda m: (
                m.get("total_sent", 0) > 10 and
                m.get("delivery_rate", 1.0) < 0.90
            ),
            notification_channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            cooldown_seconds=900  # 15 minutes
        ))
        
        # HIGH: API error rate above 5%
        self.add_condition(AlertCondition(
            name="high_api_error_rate",
            description="API error rate exceeds 5%",
            severity=AlertSeverity.HIGH,
            condition_func=lambda m: (
                m.get("total_api_calls", 0) > 20 and
                m.get("api_error_rate", 0.0) > 0.05
            ),
            notification_channels=[AlertChannel.SLACK, AlertChannel.EMAIL],
            cooldown_seconds=600  # 10 minutes
        ))
        
        # MEDIUM: Retry rate above 20%
        self.add_condition(AlertCondition(
            name="high_retry_rate",
            description="Communication retry rate exceeds 20%",
            severity=AlertSeverity.MEDIUM,
            condition_func=lambda m: (
                m.get("total_sent", 0) > 10 and
                m.get("retry_rate", 0.0) > 0.20
            ),
            notification_channels=[AlertChannel.SLACK],
            cooldown_seconds=1800  # 30 minutes
        ))
        
        # MEDIUM: Open rate below 40%
        self.add_condition(AlertCondition(
            name="low_open_rate",
            description="Email open rate below 40%",
            severity=AlertSeverity.MEDIUM,
            condition_func=lambda m: (
                m.get("total_emails_delivered", 0) > 20 and
                m.get("open_rate", 1.0) < 0.40
            ),
            notification_channels=[AlertChannel.EMAIL],
            cooldown_seconds=3600  # 1 hour
        ))
        
        # MEDIUM: Channel unavailable
        self.add_condition(AlertCondition(
            name="channel_unavailable",
            description="Communication channel is unavailable",
            severity=AlertSeverity.MEDIUM,
            condition_func=lambda m: any(
                not m.get(f"{ch}_available", True)
                for ch in ["email", "sms", "whatsapp"]
            ),
            notification_channels=[AlertChannel.SLACK],
            cooldown_seconds=600  # 10 minutes
        ))
        
        # LOW: Cache miss rate above 50%
        self.add_condition(AlertCondition(
            name="high_cache_miss_rate",
            description="Cache miss rate exceeds 50%",
            severity=AlertSeverity.LOW,
            condition_func=lambda m: (
                m.get("total_cache_requests", 0) > 50 and
                m.get("cache_miss_rate", 0.0) > 0.50
            ),
            notification_channels=[AlertChannel.EMAIL],
            cooldown_seconds=7200  # 2 hours
        ))
        
        logger.info(f"Initialized {len(self.conditions)} default alert conditions")
    
    def add_condition(self, condition: AlertCondition) -> None:
        """
        Add an alert condition.
        
        Args:
            condition: Alert condition to add
        """
        self.conditions[condition.name] = condition
        logger.debug(f"Added alert condition: {condition.name}")
    
    def remove_condition(self, name: str) -> None:
        """
        Remove an alert condition.
        
        Args:
            name: Name of condition to remove
        """
        if name in self.conditions:
            del self.conditions[name]
            logger.debug(f"Removed alert condition: {name}")
    
    def evaluate_conditions(self, metrics: Dict[str, Any]) -> List[Alert]:
        """
        Evaluate all alert conditions against current metrics.
        
        Args:
            metrics: Current metrics
            
        Returns:
            List of triggered alerts
        """
        triggered_alerts = []
        
        for condition in self.conditions.values():
            if condition.should_trigger(metrics):
                alert = Alert(
                    condition_name=condition.name,
                    severity=condition.severity,
                    message=condition.description,
                    timestamp=datetime.now(timezone.utc),
                    metrics=metrics.copy(),
                    metadata={
                        "notification_channels": [ch.value for ch in condition.notification_channels]
                    }
                )
                
                triggered_alerts.append(alert)
                condition.trigger()
                
                logger.warning(
                    f"Alert triggered: {condition.name} ({condition.severity.value})"
                )
        
        # Add to active alerts
        self.active_alerts.extend(triggered_alerts)
        
        # Keep only recent alerts (last 24 hours)
        cutoff = datetime.now(timezone.utc).timestamp() - 86400
        self.active_alerts = [
            alert for alert in self.active_alerts
            if alert.timestamp.timestamp() > cutoff
        ]
        
        return triggered_alerts
    
    async def send_alert(self, alert: Alert) -> None:
        """
        Send alert through configured channels.
        
        Args:
            alert: Alert to send
        """
        channels = alert.metadata.get("notification_channels", [])
        
        for channel_name in channels:
            try:
                channel = AlertChannel(channel_name)
                
                if channel == AlertChannel.PAGERDUTY:
                    await self._send_to_pagerduty(alert)
                elif channel == AlertChannel.SLACK:
                    await self._send_to_slack(alert)
                elif channel == AlertChannel.EMAIL:
                    await self._send_to_email(alert)
                elif channel == AlertChannel.WEBHOOK:
                    await self._send_to_webhook(alert)
                
            except Exception as e:
                logger.error(
                    f"Failed to send alert to {channel_name}: {e}",
                    exc_info=True
                )
    
    async def _send_to_pagerduty(self, alert: Alert) -> None:
        """Send alert to PagerDuty."""
        logger.info(f"[PAGERDUTY] {alert.severity.value.upper()}: {alert.message}")
        # In production, integrate with PagerDuty API
        # Example:
        # await pagerduty_client.trigger_incident(
        #     summary=alert.message,
        #     severity=alert.severity.value,
        #     details=alert.to_dict()
        # )
    
    async def _send_to_slack(self, alert: Alert) -> None:
        """Send alert to Slack."""
        logger.info(f"[SLACK] {alert.severity.value.upper()}: {alert.message}")
        # In production, integrate with Slack API
        # Example:
        # await slack_client.post_message(
        #     channel="#alerts",
        #     text=f"🚨 {alert.severity.value.upper()}: {alert.message}",
        #     attachments=[alert.to_dict()]
        # )
    
    async def _send_to_email(self, alert: Alert) -> None:
        """Send alert via email."""
        logger.info(f"[EMAIL] {alert.severity.value.upper()}: {alert.message}")
        # In production, send email to ops team
        # Example:
        # await email_client.send(
        #     to="ops@example.com",
        #     subject=f"CRM Alert: {alert.condition_name}",
        #     body=self._format_alert_email(alert)
        # )
    
    async def _send_to_webhook(self, alert: Alert) -> None:
        """Send alert to webhook."""
        logger.info(f"[WEBHOOK] {alert.severity.value.upper()}: {alert.message}")
        # In production, POST to webhook URL
        # Example:
        # await http_client.post(
        #     webhook_url,
        #     json=alert.to_dict()
        # )
    
    def _format_alert_email(self, alert: Alert) -> str:
        """Format alert as email body."""
        return f"""
CRM Communication Engine Alert

Condition: {alert.condition_name}
Severity: {alert.severity.value.upper()}
Time: {alert.timestamp.isoformat()}

Message:
{alert.message}

Metrics:
{self._format_metrics(alert.metrics)}

---
This is an automated alert from the CRM Communication Engine.
        """.strip()
    
    def _format_metrics(self, metrics: Dict[str, Any]) -> str:
        """Format metrics for display."""
        lines = []
        for key, value in sorted(metrics.items()):
            if isinstance(value, float):
                lines.append(f"  {key}: {value:.2f}")
            else:
                lines.append(f"  {key}: {value}")
        return "\n".join(lines)
    
    def get_active_alerts(
        self,
        severity: Optional[AlertSeverity] = None
    ) -> List[Alert]:
        """
        Get active alerts, optionally filtered by severity.
        
        Args:
            severity: Optional severity filter
            
        Returns:
            List of active alerts
        """
        if severity:
            return [
                alert for alert in self.active_alerts
                if alert.severity == severity
            ]
        return self.active_alerts.copy()


# Global alert manager instance
_alert_manager: Optional[AlertManager] = None


def get_alert_manager() -> AlertManager:
    """
    Get global alert manager instance.
    
    Returns:
        AlertManager instance
    """
    global _alert_manager
    if _alert_manager is None:
        _alert_manager = AlertManager()
    return _alert_manager
