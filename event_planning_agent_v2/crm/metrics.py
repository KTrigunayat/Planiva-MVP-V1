"""
Prometheus metrics for CRM Communication Engine.

This module defines and exports Prometheus metrics for monitoring
communication effectiveness, delivery performance, and API health.
"""

from prometheus_client import Counter, Histogram, Gauge, Info
from typing import Optional
import logging

logger = logging.getLogger(__name__)

# Communication metrics
crm_communications_total = Counter(
    'crm_communications_total',
    'Total number of communications sent',
    ['message_type', 'channel', 'status']
)

crm_delivery_time_seconds = Histogram(
    'crm_delivery_time_seconds',
    'Time from send to delivery in seconds',
    ['channel'],
    buckets=[1, 5, 10, 30, 60, 120, 300, 600, 1800, 3600]  # 1s to 1h
)

crm_open_rate = Gauge(
    'crm_open_rate',
    'Email open rate by message type',
    ['message_type']
)

crm_click_rate = Gauge(
    'crm_click_rate',
    'Email click-through rate by message type',
    ['message_type']
)

crm_api_errors_total = Counter(
    'crm_api_errors_total',
    'Total API errors by provider and error type',
    ['api', 'error_type']
)

crm_retry_attempts_total = Counter(
    'crm_retry_attempts_total',
    'Total retry attempts by channel',
    ['channel', 'attempt_number']
)

crm_fallback_used_total = Counter(
    'crm_fallback_used_total',
    'Total fallback channel usage',
    ['primary_channel', 'fallback_channel']
)

crm_channel_availability = Gauge(
    'crm_channel_availability',
    'Channel availability status (1=available, 0=unavailable)',
    ['channel']
)

crm_active_communications = Gauge(
    'crm_active_communications',
    'Number of communications currently being processed'
)

crm_queue_size = Gauge(
    'crm_queue_size',
    'Number of communications in queue',
    ['priority']
)

# System info
crm_info = Info(
    'crm_info',
    'CRM Communication Engine information'
)


class MetricsCollector:
    """
    Helper class for collecting and recording CRM metrics.
    
    Provides convenient methods for recording metrics throughout
    the CRM communication lifecycle.
    """
    
    @staticmethod
    def record_communication_sent(
        message_type: str,
        channel: str,
        status: str
    ) -> None:
        """
        Record a communication sent event.
        
        Args:
            message_type: Type of message (welcome, budget_summary, etc.)
            channel: Channel used (email, sms, whatsapp)
            status: Final status (sent, delivered, failed, etc.)
        """
        try:
            crm_communications_total.labels(
                message_type=message_type,
                channel=channel,
                status=status
            ).inc()
            logger.debug(
                f"Recorded communication metric: "
                f"type={message_type}, channel={channel}, status={status}"
            )
        except Exception as e:
            logger.error(f"Failed to record communication metric: {e}")
    
    @staticmethod
    def record_delivery_time(
        channel: str,
        delivery_time_seconds: float
    ) -> None:
        """
        Record delivery time for a communication.
        
        Args:
            channel: Channel used
            delivery_time_seconds: Time from send to delivery in seconds
        """
        try:
            crm_delivery_time_seconds.labels(channel=channel).observe(
                delivery_time_seconds
            )
            logger.debug(
                f"Recorded delivery time: channel={channel}, "
                f"time={delivery_time_seconds:.2f}s"
            )
        except Exception as e:
            logger.error(f"Failed to record delivery time metric: {e}")
    
    @staticmethod
    def update_open_rate(
        message_type: str,
        open_rate: float
    ) -> None:
        """
        Update email open rate gauge.
        
        Args:
            message_type: Type of message
            open_rate: Open rate as decimal (0.0 to 1.0)
        """
        try:
            crm_open_rate.labels(message_type=message_type).set(open_rate)
            logger.debug(
                f"Updated open rate: type={message_type}, rate={open_rate:.2%}"
            )
        except Exception as e:
            logger.error(f"Failed to update open rate metric: {e}")
    
    @staticmethod
    def update_click_rate(
        message_type: str,
        click_rate: float
    ) -> None:
        """
        Update email click-through rate gauge.
        
        Args:
            message_type: Type of message
            click_rate: Click rate as decimal (0.0 to 1.0)
        """
        try:
            crm_click_rate.labels(message_type=message_type).set(click_rate)
            logger.debug(
                f"Updated click rate: type={message_type}, rate={click_rate:.2%}"
            )
        except Exception as e:
            logger.error(f"Failed to update click rate metric: {e}")
    
    @staticmethod
    def record_api_error(
        api: str,
        error_type: str
    ) -> None:
        """
        Record an API error.
        
        Args:
            api: API provider (whatsapp, twilio, smtp)
            error_type: Type of error (auth, rate_limit, timeout, etc.)
        """
        try:
            crm_api_errors_total.labels(
                api=api,
                error_type=error_type
            ).inc()
            logger.debug(f"Recorded API error: api={api}, type={error_type}")
        except Exception as e:
            logger.error(f"Failed to record API error metric: {e}")
    
    @staticmethod
    def record_retry_attempt(
        channel: str,
        attempt_number: int
    ) -> None:
        """
        Record a retry attempt.
        
        Args:
            channel: Channel being retried
            attempt_number: Attempt number (1, 2, 3, etc.)
        """
        try:
            crm_retry_attempts_total.labels(
                channel=channel,
                attempt_number=str(attempt_number)
            ).inc()
            logger.debug(
                f"Recorded retry attempt: channel={channel}, "
                f"attempt={attempt_number}"
            )
        except Exception as e:
            logger.error(f"Failed to record retry attempt metric: {e}")
    
    @staticmethod
    def record_fallback_used(
        primary_channel: str,
        fallback_channel: str
    ) -> None:
        """
        Record fallback channel usage.
        
        Args:
            primary_channel: Primary channel that failed
            fallback_channel: Fallback channel used
        """
        try:
            crm_fallback_used_total.labels(
                primary_channel=primary_channel,
                fallback_channel=fallback_channel
            ).inc()
            logger.debug(
                f"Recorded fallback usage: {primary_channel} -> {fallback_channel}"
            )
        except Exception as e:
            logger.error(f"Failed to record fallback metric: {e}")
    
    @staticmethod
    def set_channel_availability(
        channel: str,
        available: bool
    ) -> None:
        """
        Set channel availability status.
        
        Args:
            channel: Channel name
            available: True if available, False if unavailable
        """
        try:
            crm_channel_availability.labels(channel=channel).set(
                1.0 if available else 0.0
            )
            logger.debug(
                f"Set channel availability: channel={channel}, "
                f"available={available}"
            )
        except Exception as e:
            logger.error(f"Failed to set channel availability metric: {e}")
    
    @staticmethod
    def set_active_communications(count: int) -> None:
        """
        Set number of active communications.
        
        Args:
            count: Number of active communications
        """
        try:
            crm_active_communications.set(count)
        except Exception as e:
            logger.error(f"Failed to set active communications metric: {e}")
    
    @staticmethod
    def set_queue_size(priority: str, size: int) -> None:
        """
        Set queue size for a priority level.
        
        Args:
            priority: Priority level (critical, high, normal, low)
            size: Queue size
        """
        try:
            crm_queue_size.labels(priority=priority).set(size)
        except Exception as e:
            logger.error(f"Failed to set queue size metric: {e}")
    
    @staticmethod
    def set_system_info(version: str, environment: str) -> None:
        """
        Set CRM system information.
        
        Args:
            version: CRM engine version
            environment: Environment (development, staging, production)
        """
        try:
            crm_info.info({
                'version': version,
                'environment': environment
            })
            logger.info(
                f"Set CRM system info: version={version}, env={environment}"
            )
        except Exception as e:
            logger.error(f"Failed to set system info metric: {e}")


# Initialize channel availability metrics
def initialize_metrics():
    """Initialize default metric values."""
    try:
        # Set all channels as available by default
        MetricsCollector.set_channel_availability('email', True)
        MetricsCollector.set_channel_availability('sms', True)
        MetricsCollector.set_channel_availability('whatsapp', True)
        
        # Initialize queue sizes
        MetricsCollector.set_queue_size('critical', 0)
        MetricsCollector.set_queue_size('high', 0)
        MetricsCollector.set_queue_size('normal', 0)
        MetricsCollector.set_queue_size('low', 0)
        
        # Set active communications to 0
        MetricsCollector.set_active_communications(0)
        
        logger.info("CRM metrics initialized")
    except Exception as e:
        logger.error(f"Failed to initialize metrics: {e}")
