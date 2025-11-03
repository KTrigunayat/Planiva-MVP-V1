"""
Structured logging configuration for CRM Communication Engine.

This module provides JSON-formatted structured logging with appropriate
log levels and context enrichment for all CRM components.
"""

import logging
import json
import sys
from datetime import datetime
from typing import Dict, Any, Optional
from enum import Enum


class LogLevel(str, Enum):
    """Log levels for CRM components."""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


class StructuredFormatter(logging.Formatter):
    """
    Custom formatter that outputs logs in JSON format.
    
    Provides structured logging with consistent fields for easy parsing
    and analysis in log aggregation systems.
    """
    
    def format(self, record: logging.LogRecord) -> str:
        """
        Format log record as JSON.
        
        Args:
            record: Log record to format
            
        Returns:
            JSON-formatted log string
        """
        # Base log structure
        log_data = {
            "timestamp": datetime.utcnow().isoformat() + "Z",
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno
        }
        
        # Add exception info if present
        if record.exc_info:
            log_data["exception"] = self.formatException(record.exc_info)
        
        # Add extra fields from record
        if hasattr(record, 'plan_id'):
            log_data["plan_id"] = record.plan_id
        if hasattr(record, 'client_id'):
            log_data["client_id"] = record.client_id
        if hasattr(record, 'communication_id'):
            log_data["communication_id"] = record.communication_id
        if hasattr(record, 'channel'):
            log_data["channel"] = record.channel
        if hasattr(record, 'message_type'):
            log_data["message_type"] = record.message_type
        if hasattr(record, 'component'):
            log_data["component"] = record.component
        if hasattr(record, 'event'):
            log_data["event"] = record.event
        
        # Add any other custom fields
        for key, value in record.__dict__.items():
            if key not in ['name', 'msg', 'args', 'created', 'filename', 'funcName',
                          'levelname', 'lineno', 'module', 'msecs', 'message',
                          'pathname', 'process', 'processName', 'relativeCreated',
                          'thread', 'threadName', 'exc_info', 'exc_text', 'stack_info',
                          'plan_id', 'client_id', 'communication_id', 'channel',
                          'message_type', 'component', 'event']:
                if not key.startswith('_'):
                    log_data[key] = value
        
        return json.dumps(log_data)


class CRMLogger:
    """
    Enhanced logger for CRM components with structured logging support.
    
    Provides convenient methods for logging with context enrichment.
    """
    
    def __init__(self, name: str, component: Optional[str] = None):
        """
        Initialize CRM logger.
        
        Args:
            name: Logger name (typically __name__)
            component: Component name for context
        """
        self.logger = logging.getLogger(name)
        self.component = component or name.split('.')[-1]
    
    def _log_with_context(
        self,
        level: int,
        message: str,
        **context
    ) -> None:
        """
        Log message with context.
        
        Args:
            level: Log level
            message: Log message
            **context: Additional context fields
        """
        extra = {'component': self.component}
        extra.update(context)
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **context) -> None:
        """Log debug message."""
        self._log_with_context(logging.DEBUG, message, **context)
    
    def info(self, message: str, **context) -> None:
        """Log info message."""
        self._log_with_context(logging.INFO, message, **context)
    
    def warning(self, message: str, **context) -> None:
        """Log warning message."""
        self._log_with_context(logging.WARNING, message, **context)
    
    def error(self, message: str, **context) -> None:
        """Log error message."""
        self._log_with_context(logging.ERROR, message, **context)
    
    def critical(self, message: str, **context) -> None:
        """Log critical message."""
        self._log_with_context(logging.CRITICAL, message, **context)
    
    def communication_sent(
        self,
        plan_id: str,
        client_id: str,
        communication_id: str,
        channel: str,
        message_type: str,
        status: str
    ) -> None:
        """
        Log communication sent event.
        
        Args:
            plan_id: Event plan ID
            client_id: Client ID
            communication_id: Communication ID
            channel: Channel used
            message_type: Type of message
            status: Communication status
        """
        self.info(
            "Communication sent",
            event="communication_sent",
            plan_id=plan_id,
            client_id=client_id,
            communication_id=communication_id,
            channel=channel,
            message_type=message_type,
            status=status
        )
    
    def communication_delivered(
        self,
        communication_id: str,
        channel: str,
        delivery_time_seconds: float
    ) -> None:
        """
        Log communication delivered event.
        
        Args:
            communication_id: Communication ID
            channel: Channel used
            delivery_time_seconds: Time to delivery
        """
        self.info(
            "Communication delivered",
            event="communication_delivered",
            communication_id=communication_id,
            channel=channel,
            delivery_time_seconds=delivery_time_seconds
        )
    
    def communication_failed(
        self,
        communication_id: str,
        channel: str,
        error_message: str,
        error_category: Optional[str] = None
    ) -> None:
        """
        Log communication failure.
        
        Args:
            communication_id: Communication ID
            channel: Channel used
            error_message: Error message
            error_category: Category of error
        """
        self.error(
            "Communication failed",
            event="communication_failed",
            communication_id=communication_id,
            channel=channel,
            error_message=error_message,
            error_category=error_category
        )
    
    def retry_attempt(
        self,
        communication_id: str,
        channel: str,
        attempt_number: int,
        max_retries: int,
        delay_seconds: float
    ) -> None:
        """
        Log retry attempt.
        
        Args:
            communication_id: Communication ID
            channel: Channel being retried
            attempt_number: Current attempt number
            max_retries: Maximum retry attempts
            delay_seconds: Delay before retry
        """
        self.warning(
            f"Retrying communication (attempt {attempt_number}/{max_retries})",
            event="retry_attempt",
            communication_id=communication_id,
            channel=channel,
            attempt_number=attempt_number,
            max_retries=max_retries,
            delay_seconds=delay_seconds
        )
    
    def fallback_used(
        self,
        communication_id: str,
        primary_channel: str,
        fallback_channel: str,
        primary_error: str
    ) -> None:
        """
        Log fallback channel usage.
        
        Args:
            communication_id: Communication ID
            primary_channel: Primary channel that failed
            fallback_channel: Fallback channel used
            primary_error: Error from primary channel
        """
        self.warning(
            f"Using fallback channel: {primary_channel} -> {fallback_channel}",
            event="fallback_used",
            communication_id=communication_id,
            primary_channel=primary_channel,
            fallback_channel=fallback_channel,
            primary_error=primary_error
        )
    
    def api_error(
        self,
        api: str,
        error_type: str,
        error_message: str,
        status_code: Optional[int] = None
    ) -> None:
        """
        Log API error.
        
        Args:
            api: API provider
            error_type: Type of error
            error_message: Error message
            status_code: HTTP status code if applicable
        """
        self.error(
            f"API error: {api}",
            event="api_error",
            api=api,
            error_type=error_type,
            error_message=error_message,
            status_code=status_code
        )
    
    def cache_hit(self, cache_key: str, cache_type: str) -> None:
        """Log cache hit."""
        self.debug(
            "Cache hit",
            event="cache_hit",
            cache_key=cache_key,
            cache_type=cache_type
        )
    
    def cache_miss(self, cache_key: str, cache_type: str) -> None:
        """Log cache miss."""
        self.debug(
            "Cache miss",
            event="cache_miss",
            cache_key=cache_key,
            cache_type=cache_type
        )


def configure_crm_logging(
    log_level: str = "INFO",
    enable_json: bool = True,
    log_file: Optional[str] = None
) -> None:
    """
    Configure logging for CRM components.
    
    Args:
        log_level: Minimum log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        enable_json: Enable JSON-formatted structured logging
        log_file: Optional log file path
    """
    # Get root logger for CRM
    crm_logger = logging.getLogger('event_planning_agent_v2.crm')
    crm_logger.setLevel(getattr(logging, log_level.upper()))
    
    # Remove existing handlers
    crm_logger.handlers.clear()
    
    # Console handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setLevel(getattr(logging, log_level.upper()))
    
    if enable_json:
        console_handler.setFormatter(StructuredFormatter())
    else:
        console_handler.setFormatter(
            logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
        )
    
    crm_logger.addHandler(console_handler)
    
    # File handler if specified
    if log_file:
        file_handler = logging.FileHandler(log_file)
        file_handler.setLevel(getattr(logging, log_level.upper()))
        
        if enable_json:
            file_handler.setFormatter(StructuredFormatter())
        else:
            file_handler.setFormatter(
                logging.Formatter(
                    '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
                )
            )
        
        crm_logger.addHandler(file_handler)
    
    # Prevent propagation to root logger
    crm_logger.propagate = False
    
    logging.info(
        f"CRM logging configured: level={log_level}, json={enable_json}, "
        f"file={log_file or 'none'}"
    )


def get_crm_logger(name: str, component: Optional[str] = None) -> CRMLogger:
    """
    Get a CRM logger instance.
    
    Args:
        name: Logger name (typically __name__)
        component: Component name for context
        
    Returns:
        CRMLogger instance
    """
    return CRMLogger(name, component)
