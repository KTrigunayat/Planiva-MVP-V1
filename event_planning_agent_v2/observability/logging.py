"""
Structured logging system with correlation ID support.

Provides comprehensive logging capabilities with structured output,
correlation tracking, and integration with monitoring systems.
"""

import logging
import json
import threading
import uuid
from typing import Dict, Any, Optional, Union
from datetime import datetime
from enum import Enum
from contextvars import ContextVar
from dataclasses import dataclass, field, asdict
import traceback
import sys
import os

# Context variable for correlation ID tracking
correlation_id_context: ContextVar[Optional[str]] = ContextVar('correlation_id', default=None)


class LogLevel(str, Enum):
    """Log levels"""
    DEBUG = "DEBUG"
    INFO = "INFO"
    WARNING = "WARNING"
    ERROR = "ERROR"
    CRITICAL = "CRITICAL"


@dataclass
class LogContext:
    """Context information for structured logging"""
    correlation_id: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class StructuredLogRecord:
    """Structured log record"""
    timestamp: str
    level: str
    message: str
    logger_name: str
    correlation_id: Optional[str] = None
    component: Optional[str] = None
    operation: Optional[str] = None
    user_id: Optional[str] = None
    session_id: Optional[str] = None
    request_id: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    exception: Optional[Dict[str, Any]] = None
    performance: Optional[Dict[str, Any]] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for JSON serialization"""
        return {k: v for k, v in asdict(self).items() if v is not None}
    
    def to_json(self) -> str:
        """Convert to JSON string"""
        return json.dumps(self.to_dict(), default=str)


class CorrelationContext:
    """Manages correlation ID context"""
    
    @staticmethod
    def set_correlation_id(correlation_id: str):
        """Set correlation ID for current context"""
        correlation_id_context.set(correlation_id)
    
    @staticmethod
    def get_correlation_id() -> Optional[str]:
        """Get correlation ID from current context"""
        return correlation_id_context.get()
    
    @staticmethod
    def generate_correlation_id() -> str:
        """Generate new correlation ID"""
        return str(uuid.uuid4())
    
    @staticmethod
    def ensure_correlation_id() -> str:
        """Ensure correlation ID exists, generate if needed"""
        correlation_id = CorrelationContext.get_correlation_id()
        if not correlation_id:
            correlation_id = CorrelationContext.generate_correlation_id()
            CorrelationContext.set_correlation_id(correlation_id)
        return correlation_id


class StructuredFormatter(logging.Formatter):
    """Custom formatter for structured logging"""
    
    def __init__(self, include_metadata: bool = True):
        super().__init__()
        self.include_metadata = include_metadata
    
    def format(self, record: logging.LogRecord) -> str:
        """Format log record as structured JSON"""
        
        # Extract structured data from record
        structured_record = StructuredLogRecord(
            timestamp=datetime.utcnow().isoformat() + "Z",
            level=record.levelname,
            message=record.getMessage(),
            logger_name=record.name,
            correlation_id=CorrelationContext.get_correlation_id()
        )
        
        # Add context information if available
        if hasattr(record, 'component'):
            structured_record.component = record.component
        if hasattr(record, 'operation'):
            structured_record.operation = record.operation
        if hasattr(record, 'user_id'):
            structured_record.user_id = record.user_id
        if hasattr(record, 'session_id'):
            structured_record.session_id = record.session_id
        if hasattr(record, 'request_id'):
            structured_record.request_id = record.request_id
        
        # Add metadata
        if self.include_metadata and hasattr(record, 'metadata'):
            structured_record.metadata = record.metadata
        
        # Add exception information
        if record.exc_info:
            structured_record.exception = {
                "type": record.exc_info[0].__name__ if record.exc_info[0] else None,
                "message": str(record.exc_info[1]) if record.exc_info[1] else None,
                "traceback": traceback.format_exception(*record.exc_info)
            }
        
        # Add performance information
        if hasattr(record, 'performance'):
            structured_record.performance = record.performance
        
        return structured_record.to_json()


class StructuredLogger:
    """Enhanced logger with structured output and correlation tracking"""
    
    def __init__(
        self,
        name: str,
        level: LogLevel = LogLevel.INFO,
        component: Optional[str] = None,
        include_console: bool = True,
        include_file: bool = True,
        log_file_path: Optional[str] = None
    ):
        self.name = name
        self.component = component
        self.logger = logging.getLogger(name)
        self.logger.setLevel(getattr(logging, level.value))
        
        # Clear existing handlers
        self.logger.handlers.clear()
        
        # Add structured formatter
        formatter = StructuredFormatter()
        
        # Console handler
        if include_console:
            console_handler = logging.StreamHandler(sys.stdout)
            console_handler.setFormatter(formatter)
            self.logger.addHandler(console_handler)
        
        # File handler
        if include_file:
            log_file = log_file_path or f"logs/{name}.log"
            os.makedirs(os.path.dirname(log_file), exist_ok=True)
            
            file_handler = logging.FileHandler(log_file)
            file_handler.setFormatter(formatter)
            self.logger.addHandler(file_handler)
        
        # Prevent propagation to avoid duplicate logs
        self.logger.propagate = False
    
    def _log(
        self,
        level: LogLevel,
        message: str,
        operation: Optional[str] = None,
        user_id: Optional[str] = None,
        session_id: Optional[str] = None,
        request_id: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        exception: Optional[Exception] = None,
        performance: Optional[Dict[str, Any]] = None
    ):
        """Internal logging method"""
        
        # Create log record
        extra = {
            'component': self.component,
            'operation': operation,
            'user_id': user_id,
            'session_id': session_id,
            'request_id': request_id,
            'metadata': metadata or {},
            'performance': performance
        }
        
        # Log with appropriate level
        log_method = getattr(self.logger, level.value.lower())
        
        if exception:
            log_method(message, exc_info=True, extra=extra)
        else:
            log_method(message, extra=extra)
    
    def debug(
        self,
        message: str,
        operation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log debug message"""
        self._log(LogLevel.DEBUG, message, operation, metadata=metadata, **kwargs)
    
    def info(
        self,
        message: str,
        operation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log info message"""
        self._log(LogLevel.INFO, message, operation, metadata=metadata, **kwargs)
    
    def warning(
        self,
        message: str,
        operation: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log warning message"""
        self._log(LogLevel.WARNING, message, operation, metadata=metadata, **kwargs)
    
    def error(
        self,
        message: str,
        operation: Optional[str] = None,
        exception: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log error message"""
        self._log(LogLevel.ERROR, message, operation, exception=exception, metadata=metadata, **kwargs)
    
    def critical(
        self,
        message: str,
        operation: Optional[str] = None,
        exception: Optional[Exception] = None,
        metadata: Optional[Dict[str, Any]] = None,
        **kwargs
    ):
        """Log critical message"""
        self._log(LogLevel.CRITICAL, message, operation, exception=exception, metadata=metadata, **kwargs)
    
    def log_performance(
        self,
        operation: str,
        duration_ms: float,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log performance metrics"""
        performance_data = {
            "duration_ms": duration_ms,
            "success": success,
            "operation": operation
        }
        
        message = f"Performance: {operation} completed in {duration_ms:.2f}ms"
        if not success:
            message += " (failed)"
        
        self._log(
            LogLevel.INFO,
            message,
            operation=operation,
            metadata=metadata,
            performance=performance_data
        )
    
    def log_agent_interaction(
        self,
        agent_name: str,
        action: str,
        duration_ms: Optional[float] = None,
        success: bool = True,
        input_data: Optional[Dict[str, Any]] = None,
        output_data: Optional[Dict[str, Any]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log agent interaction"""
        interaction_metadata = {
            "agent_name": agent_name,
            "action": action,
            "success": success
        }
        
        if input_data:
            interaction_metadata["input_size"] = len(str(input_data))
        if output_data:
            interaction_metadata["output_size"] = len(str(output_data))
        
        if metadata:
            interaction_metadata.update(metadata)
        
        performance_data = None
        if duration_ms is not None:
            performance_data = {
                "duration_ms": duration_ms,
                "success": success,
                "operation": f"agent_{action}"
            }
        
        message = f"Agent {agent_name} {action}"
        if duration_ms:
            message += f" in {duration_ms:.2f}ms"
        if not success:
            message += " (failed)"
        
        self._log(
            LogLevel.INFO,
            message,
            operation=f"agent_{action}",
            metadata=interaction_metadata,
            performance=performance_data
        )
    
    def log_workflow_event(
        self,
        workflow_id: str,
        event_type: str,
        node_name: Optional[str] = None,
        duration_ms: Optional[float] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log workflow event"""
        workflow_metadata = {
            "workflow_id": workflow_id,
            "event_type": event_type,
            "success": success
        }
        
        if node_name:
            workflow_metadata["node_name"] = node_name
        
        if metadata:
            workflow_metadata.update(metadata)
        
        performance_data = None
        if duration_ms is not None:
            performance_data = {
                "duration_ms": duration_ms,
                "success": success,
                "operation": f"workflow_{event_type}"
            }
        
        message = f"Workflow {workflow_id} {event_type}"
        if node_name:
            message += f" (node: {node_name})"
        if duration_ms:
            message += f" in {duration_ms:.2f}ms"
        if not success:
            message += " (failed)"
        
        self._log(
            LogLevel.INFO,
            message,
            operation=f"workflow_{event_type}",
            metadata=workflow_metadata,
            performance=performance_data
        )
    
    def log_mcp_operation(
        self,
        server_name: str,
        tool_name: str,
        operation: str,
        duration_ms: Optional[float] = None,
        success: bool = True,
        metadata: Optional[Dict[str, Any]] = None
    ):
        """Log MCP server operation"""
        mcp_metadata = {
            "server_name": server_name,
            "tool_name": tool_name,
            "operation": operation,
            "success": success
        }
        
        if metadata:
            mcp_metadata.update(metadata)
        
        performance_data = None
        if duration_ms is not None:
            performance_data = {
                "duration_ms": duration_ms,
                "success": success,
                "operation": f"mcp_{operation}"
            }
        
        message = f"MCP {server_name}.{tool_name} {operation}"
        if duration_ms:
            message += f" in {duration_ms:.2f}ms"
        if not success:
            message += " (failed)"
        
        self._log(
            LogLevel.INFO,
            message,
            operation=f"mcp_{operation}",
            metadata=mcp_metadata,
            performance=performance_data
        )


class LoggerManager:
    """Manages structured loggers across the application"""
    
    def __init__(self):
        self.loggers: Dict[str, StructuredLogger] = {}
        self.default_config = {
            "level": LogLevel.INFO,
            "include_console": True,
            "include_file": True
        }
        self._lock = threading.Lock()
    
    def get_logger(
        self,
        name: str,
        component: Optional[str] = None,
        **config_overrides
    ) -> StructuredLogger:
        """Get or create structured logger"""
        
        with self._lock:
            if name not in self.loggers:
                # Merge default config with overrides
                config = {**self.default_config, **config_overrides}
                
                self.loggers[name] = StructuredLogger(
                    name=name,
                    component=component,
                    **config
                )
            
            return self.loggers[name]
    
    def configure_logging(
        self,
        level: LogLevel = LogLevel.INFO,
        include_console: bool = True,
        include_file: bool = True,
        log_directory: str = "logs"
    ):
        """Configure global logging settings"""
        self.default_config.update({
            "level": level,
            "include_console": include_console,
            "include_file": include_file,
            "log_file_path": f"{log_directory}/{{name}}.log"
        })
        
        # Ensure log directory exists
        os.makedirs(log_directory, exist_ok=True)
    
    def set_correlation_id(self, correlation_id: str):
        """Set correlation ID for current context"""
        CorrelationContext.set_correlation_id(correlation_id)
    
    def get_correlation_id(self) -> Optional[str]:
        """Get correlation ID from current context"""
        return CorrelationContext.get_correlation_id()
    
    def ensure_correlation_id(self) -> str:
        """Ensure correlation ID exists"""
        return CorrelationContext.ensure_correlation_id()


# Global logger manager
_logger_manager: Optional[LoggerManager] = None


def get_logger_manager() -> LoggerManager:
    """Get global logger manager"""
    global _logger_manager
    if _logger_manager is None:
        _logger_manager = LoggerManager()
    return _logger_manager


def get_logger(name: str, component: Optional[str] = None, **kwargs) -> StructuredLogger:
    """Get structured logger"""
    manager = get_logger_manager()
    return manager.get_logger(name, component, **kwargs)


def set_correlation_id(correlation_id: str):
    """Set correlation ID for current context"""
    CorrelationContext.set_correlation_id(correlation_id)


def get_correlation_id() -> Optional[str]:
    """Get correlation ID from current context"""
    return CorrelationContext.get_correlation_id()


def ensure_correlation_id() -> str:
    """Ensure correlation ID exists"""
    return CorrelationContext.ensure_correlation_id()


# Decorator for automatic correlation ID management
def with_correlation_id(correlation_id: Optional[str] = None):
    """Decorator to ensure correlation ID is set for function execution"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            # Set correlation ID if provided, or ensure one exists
            if correlation_id:
                CorrelationContext.set_correlation_id(correlation_id)
            else:
                CorrelationContext.ensure_correlation_id()
            
            return func(*args, **kwargs)
        
        return wrapper
    return decorator


# Context manager for correlation ID
class correlation_context:
    """Context manager for correlation ID"""
    
    def __init__(self, correlation_id: Optional[str] = None):
        self.correlation_id = correlation_id or CorrelationContext.generate_correlation_id()
        self.previous_correlation_id = None
    
    def __enter__(self):
        self.previous_correlation_id = CorrelationContext.get_correlation_id()
        CorrelationContext.set_correlation_id(self.correlation_id)
        return self.correlation_id
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        if self.previous_correlation_id:
            CorrelationContext.set_correlation_id(self.previous_correlation_id)
        else:
            # Clear correlation ID if there wasn't one before
            correlation_id_context.set(None)


# Initialize default logging configuration
def setup_default_logging(
    level: LogLevel = LogLevel.INFO,
    log_directory: str = "logs"
):
    """Setup default logging configuration"""
    manager = get_logger_manager()
    manager.configure_logging(
        level=level,
        include_console=True,
        include_file=True,
        log_directory=log_directory
    )
    
    # Create logs directory
    os.makedirs(log_directory, exist_ok=True)
    
    # Get root logger to test configuration
    root_logger = get_logger("event_planning_agent", component="system")
    root_logger.info("Structured logging initialized", operation="setup_logging")


# Performance logging decorator
def log_performance(
    logger_name: str = "performance",
    operation: Optional[str] = None,
    include_args: bool = False
):
    """Decorator to automatically log function performance"""
    
    def decorator(func):
        def wrapper(*args, **kwargs):
            import time
            
            logger = get_logger(logger_name)
            op_name = operation or func.__name__
            
            metadata = {}
            if include_args:
                metadata["args_count"] = len(args)
                metadata["kwargs_count"] = len(kwargs)
            
            start_time = time.time()
            success = True
            
            try:
                result = func(*args, **kwargs)
                return result
            except Exception as e:
                success = False
                logger.error(
                    f"Function {op_name} failed",
                    operation=op_name,
                    exception=e,
                    metadata=metadata
                )
                raise
            finally:
                duration_ms = (time.time() - start_time) * 1000
                logger.log_performance(
                    operation=op_name,
                    duration_ms=duration_ms,
                    success=success,
                    metadata=metadata
                )
        
        return wrapper
    return decorator