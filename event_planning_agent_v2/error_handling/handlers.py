"""
Multi-layer error handlers for the Event Planning Agent system.

Provides specialized error handling for different system components with
recovery strategies and escalation paths.
"""

import logging
import traceback
from abc import ABC, abstractmethod
from typing import Dict, Any, Optional, List, Callable, Union, Type
from datetime import datetime, timedelta
from enum import Enum
import asyncio
import functools

from .exceptions import (
    EventPlanningError, AgentError, WorkflowError, MCPServerError,
    DatabaseError, ValidationError, RecoveryError, ErrorSeverity, ErrorCategory
)
from .recovery import RecoveryManager, RecoveryStrategy, RecoveryResult

logger = logging.getLogger(__name__)


class HandlerAction(str, Enum):
    """Actions that error handlers can take"""
    RETRY = "retry"
    ESCALATE = "escalate"
    RECOVER = "recover"
    IGNORE = "ignore"
    FAIL_FAST = "fail_fast"
    DEGRADE_GRACEFULLY = "degrade_gracefully"


class ErrorContext:
    """Context information for error handling"""
    
    def __init__(
        self,
        error: Exception,
        component: str,
        operation: str,
        metadata: Optional[Dict[str, Any]] = None,
        correlation_id: Optional[str] = None
    ):
        self.error = error
        self.component = component
        self.operation = operation
        self.metadata = metadata or {}
        self.correlation_id = correlation_id
        self.timestamp = datetime.utcnow()
        self.handled = False
        self.recovery_attempts = 0
        self.escalated = False


class ErrorHandler(ABC):
    """Base class for error handlers"""
    
    def __init__(
        self,
        name: str,
        max_retries: int = 3,
        retry_delay: float = 1.0,
        escalation_threshold: int = 5
    ):
        self.name = name
        self.max_retries = max_retries
        self.retry_delay = retry_delay
        self.escalation_threshold = escalation_threshold
        
        # Error tracking
        self.error_counts: Dict[str, int] = {}
        self.last_errors: Dict[str, datetime] = {}
        
        # Handler chain
        self.next_handler: Optional['ErrorHandler'] = None
        
        # Recovery manager
        self.recovery_manager = RecoveryManager()
    
    def set_next(self, handler: 'ErrorHandler') -> 'ErrorHandler':
        """Set the next handler in the chain"""
        self.next_handler = handler
        return handler
    
    @abstractmethod
    def can_handle(self, context: ErrorContext) -> bool:
        """Check if this handler can handle the error"""
        pass
    
    @abstractmethod
    def handle_error(self, context: ErrorContext) -> HandlerAction:
        """Handle the error and return the action to take"""
        pass
    
    def process_error(self, context: ErrorContext) -> HandlerAction:
        """Process error through the handler chain"""
        if self.can_handle(context):
            try:
                # Track error occurrence
                self._track_error(context)
                
                # Handle the error
                action = self.handle_error(context)
                context.handled = True
                
                logger.info(f"Error handled by {self.name}: {action.value}")
                return action
                
            except Exception as handler_error:
                logger.error(f"Error handler {self.name} failed: {handler_error}")
                context.escalated = True
                
                # Try next handler
                if self.next_handler:
                    return self.next_handler.process_error(context)
                else:
                    return HandlerAction.FAIL_FAST
        
        elif self.next_handler:
            return self.next_handler.process_error(context)
        else:
            logger.warning(f"No handler found for error: {context.error}")
            return HandlerAction.ESCALATE
    
    def _track_error(self, context: ErrorContext):
        """Track error occurrence for pattern analysis"""
        error_key = f"{context.component}:{type(context.error).__name__}"
        
        self.error_counts[error_key] = self.error_counts.get(error_key, 0) + 1
        self.last_errors[error_key] = context.timestamp
        
        # Check for escalation threshold
        if self.error_counts[error_key] >= self.escalation_threshold:
            logger.warning(f"Error escalation threshold reached for {error_key}")
            context.escalated = True
    
    def should_retry(self, context: ErrorContext) -> bool:
        """Determine if error should be retried"""
        if context.recovery_attempts >= self.max_retries:
            return False
        
        if isinstance(context.error, EventPlanningError):
            return context.error.recoverable
        
        return True
    
    def get_retry_delay(self, attempt: int) -> float:
        """Calculate retry delay with exponential backoff"""
        return self.retry_delay * (2 ** attempt)


class AgentErrorHandler(ErrorHandler):
    """Specialized error handler for agent-related errors"""
    
    def __init__(self, **kwargs):
        super().__init__("AgentErrorHandler", **kwargs)
        
        # Agent-specific configuration
        self.agent_timeouts: Dict[str, int] = {}
        self.agent_retry_limits: Dict[str, int] = {}
    
    def can_handle(self, context: ErrorContext) -> bool:
        """Check if this is an agent-related error"""
        return (
            isinstance(context.error, AgentError) or
            context.component.startswith("agent_") or
            "agent" in context.operation.lower()
        )
    
    def handle_error(self, context: ErrorContext) -> HandlerAction:
        """Handle agent-specific errors"""
        error = context.error
        
        if isinstance(error, AgentError):
            agent_name = error.agent_name or "unknown"
            
            # Handle different types of agent errors
            if error.severity == ErrorSeverity.CRITICAL:
                logger.critical(f"Critical agent error in {agent_name}: {error.message}")
                return HandlerAction.FAIL_FAST
            
            elif error.severity == ErrorSeverity.HIGH:
                if error.recoverable and self.should_retry(context):
                    logger.warning(f"High severity agent error, attempting recovery: {error.message}")
                    return self._attempt_agent_recovery(context, agent_name)
                else:
                    return HandlerAction.ESCALATE
            
            elif error.severity == ErrorSeverity.MEDIUM:
                if self.should_retry(context):
                    return self._retry_agent_operation(context, agent_name)
                else:
                    return HandlerAction.DEGRADE_GRACEFULLY
            
            else:  # LOW severity
                logger.info(f"Low severity agent error, continuing: {error.message}")
                return HandlerAction.IGNORE
        
        # Handle generic agent errors
        if self.should_retry(context):
            return HandlerAction.RETRY
        else:
            return HandlerAction.ESCALATE
    
    def _attempt_agent_recovery(self, context: ErrorContext, agent_name: str) -> HandlerAction:
        """Attempt agent-specific recovery"""
        try:
            # Determine recovery strategy based on error type
            if "timeout" in str(context.error).lower():
                strategy = RecoveryStrategy.INCREASE_TIMEOUT
            elif "initialization" in str(context.error).lower():
                strategy = RecoveryStrategy.RESTART_COMPONENT
            elif "communication" in str(context.error).lower():
                strategy = RecoveryStrategy.RETRY_WITH_BACKOFF
            else:
                strategy = RecoveryStrategy.RESET_STATE
            
            # Execute recovery
            recovery_result = self.recovery_manager.execute_recovery(
                strategy=strategy,
                context={
                    "agent_name": agent_name,
                    "error": context.error,
                    "operation": context.operation
                }
            )
            
            if recovery_result.success:
                logger.info(f"Agent recovery successful for {agent_name}")
                return HandlerAction.RETRY
            else:
                logger.error(f"Agent recovery failed for {agent_name}: {recovery_result.message}")
                return HandlerAction.ESCALATE
                
        except Exception as recovery_error:
            logger.error(f"Agent recovery attempt failed: {recovery_error}")
            return HandlerAction.ESCALATE
    
    def _retry_agent_operation(self, context: ErrorContext, agent_name: str) -> HandlerAction:
        """Retry agent operation with appropriate delay"""
        context.recovery_attempts += 1
        
        # Calculate delay based on agent type and error
        delay = self.get_retry_delay(context.recovery_attempts)
        
        # Add jitter for agent operations
        import random
        delay += random.uniform(0, 1)
        
        logger.info(f"Retrying agent operation for {agent_name} in {delay:.2f}s (attempt {context.recovery_attempts})")
        
        # Schedule retry (in practice, this would be handled by the calling code)
        context.metadata["retry_delay"] = delay
        
        return HandlerAction.RETRY


class WorkflowErrorHandler(ErrorHandler):
    """Specialized error handler for workflow-related errors"""
    
    def __init__(self, **kwargs):
        super().__init__("WorkflowErrorHandler", **kwargs)
        
        # Workflow-specific configuration
        self.checkpoint_enabled = True
        self.state_recovery_enabled = True
    
    def can_handle(self, context: ErrorContext) -> bool:
        """Check if this is a workflow-related error"""
        return (
            isinstance(context.error, WorkflowError) or
            context.component.startswith("workflow_") or
            "workflow" in context.operation.lower() or
            "langgraph" in context.operation.lower()
        )
    
    def handle_error(self, context: ErrorContext) -> HandlerAction:
        """Handle workflow-specific errors"""
        error = context.error
        
        if isinstance(error, WorkflowError):
            workflow_id = error.workflow_id or "unknown"
            
            # Handle different types of workflow errors
            if isinstance(error, WorkflowRecursionError):
                logger.error(f"Workflow recursion limit exceeded for {workflow_id}")
                return self._handle_recursion_error(context, workflow_id)
            
            elif isinstance(error, WorkflowTimeoutError):
                logger.warning(f"Workflow timeout for {workflow_id}")
                return self._handle_timeout_error(context, workflow_id)
            
            elif isinstance(error, WorkflowStateError):
                logger.error(f"Workflow state error for {workflow_id}")
                return self._handle_state_error(context, workflow_id)
            
            elif isinstance(error, WorkflowExecutionError):
                logger.warning(f"Workflow execution error for {workflow_id}")
                return self._handle_execution_error(context, workflow_id)
            
            else:
                # Generic workflow error
                if self.should_retry(context):
                    return HandlerAction.RETRY
                else:
                    return HandlerAction.ESCALATE
        
        # Handle generic workflow errors
        return self._handle_generic_workflow_error(context)
    
    def _handle_recursion_error(self, context: ErrorContext, workflow_id: str) -> HandlerAction:
        """Handle workflow recursion errors"""
        # Recursion errors are usually not recoverable
        logger.error(f"Workflow {workflow_id} hit recursion limit - terminating")
        
        # Save current state for analysis
        self._save_error_state(context, workflow_id)
        
        return HandlerAction.FAIL_FAST
    
    def _handle_timeout_error(self, context: ErrorContext, workflow_id: str) -> HandlerAction:
        """Handle workflow timeout errors"""
        if self.should_retry(context):
            # Try recovery with increased timeout
            recovery_result = self.recovery_manager.execute_recovery(
                strategy=RecoveryStrategy.INCREASE_TIMEOUT,
                context={
                    "workflow_id": workflow_id,
                    "current_timeout": context.metadata.get("timeout", 300),
                    "error": context.error
                }
            )
            
            if recovery_result.success:
                return HandlerAction.RETRY
            else:
                return HandlerAction.ESCALATE
        else:
            return HandlerAction.DEGRADE_GRACEFULLY
    
    def _handle_state_error(self, context: ErrorContext, workflow_id: str) -> HandlerAction:
        """Handle workflow state errors"""
        if self.state_recovery_enabled:
            # Try to recover from checkpoint
            recovery_result = self.recovery_manager.execute_recovery(
                strategy=RecoveryStrategy.RESTORE_CHECKPOINT,
                context={
                    "workflow_id": workflow_id,
                    "error": context.error
                }
            )
            
            if recovery_result.success:
                logger.info(f"Workflow state recovered from checkpoint for {workflow_id}")
                return HandlerAction.RETRY
            else:
                logger.error(f"Failed to recover workflow state for {workflow_id}")
                return HandlerAction.ESCALATE
        else:
            return HandlerAction.ESCALATE
    
    def _handle_execution_error(self, context: ErrorContext, workflow_id: str) -> HandlerAction:
        """Handle workflow execution errors"""
        if self.should_retry(context):
            # Try different recovery strategies based on error details
            error_msg = str(context.error).lower()
            
            if "node" in error_msg:
                strategy = RecoveryStrategy.SKIP_FAILED_NODE
            elif "state" in error_msg:
                strategy = RecoveryStrategy.RESET_STATE
            else:
                strategy = RecoveryStrategy.RETRY_WITH_BACKOFF
            
            recovery_result = self.recovery_manager.execute_recovery(
                strategy=strategy,
                context={
                    "workflow_id": workflow_id,
                    "node_name": getattr(context.error, 'node_name', None),
                    "error": context.error
                }
            )
            
            if recovery_result.success:
                return HandlerAction.RETRY
            else:
                return HandlerAction.DEGRADE_GRACEFULLY
        else:
            return HandlerAction.ESCALATE
    
    def _handle_generic_workflow_error(self, context: ErrorContext) -> HandlerAction:
        """Handle generic workflow errors"""
        if context.error.__class__.__name__ in ["GraphRecursionError", "GraphInterrupt"]:
            return HandlerAction.FAIL_FAST
        elif self.should_retry(context):
            return HandlerAction.RETRY
        else:
            return HandlerAction.ESCALATE
    
    def _save_error_state(self, context: ErrorContext, workflow_id: str):
        """Save workflow state for error analysis"""
        try:
            error_data = {
                "workflow_id": workflow_id,
                "error": context.error.to_dict() if hasattr(context.error, 'to_dict') else str(context.error),
                "timestamp": context.timestamp.isoformat(),
                "operation": context.operation,
                "metadata": context.metadata,
                "traceback": traceback.format_exc()
            }
            
            # In practice, save to database or file system
            logger.debug(f"Saved error state for workflow {workflow_id}")
            
        except Exception as save_error:
            logger.error(f"Failed to save error state: {save_error}")


class MCPErrorHandler(ErrorHandler):
    """Specialized error handler for MCP server errors"""
    
    def __init__(self, **kwargs):
        super().__init__("MCPErrorHandler", **kwargs)
        
        # MCP-specific configuration
        self.server_health: Dict[str, bool] = {}
        self.fallback_enabled = True
        self.circuit_breaker_threshold = 5
        self.circuit_breaker_timeout = 60  # seconds
        self.circuit_breakers: Dict[str, Dict[str, Any]] = {}
    
    def can_handle(self, context: ErrorContext) -> bool:
        """Check if this is an MCP server-related error"""
        return (
            isinstance(context.error, MCPServerError) or
            context.component.startswith("mcp_") or
            "mcp" in context.operation.lower()
        )
    
    def handle_error(self, context: ErrorContext) -> HandlerAction:
        """Handle MCP server-specific errors"""
        error = context.error
        
        if isinstance(error, MCPServerError):
            server_name = error.server_name or "unknown"
            
            # Check circuit breaker
            if self._is_circuit_breaker_open(server_name):
                logger.warning(f"Circuit breaker open for MCP server {server_name}")
                return HandlerAction.DEGRADE_GRACEFULLY
            
            # Handle different types of MCP errors
            if isinstance(error, MCPServerConnectionError):
                return self._handle_connection_error(context, server_name)
            
            elif isinstance(error, MCPServerTimeoutError):
                return self._handle_timeout_error(context, server_name)
            
            elif isinstance(error, MCPToolError):
                return self._handle_tool_error(context, server_name, error.tool_name)
            
            else:
                # Generic MCP server error
                return self._handle_generic_mcp_error(context, server_name)
        
        # Handle generic MCP-related errors
        return self._handle_generic_mcp_error(context, "unknown")
    
    def _handle_connection_error(self, context: ErrorContext, server_name: str) -> HandlerAction:
        """Handle MCP server connection errors"""
        # Update circuit breaker
        self._record_failure(server_name)
        
        if self.should_retry(context):
            # Try to reconnect with exponential backoff
            delay = self.get_retry_delay(context.recovery_attempts)
            context.metadata["retry_delay"] = delay
            
            logger.info(f"Retrying MCP server connection to {server_name} in {delay:.2f}s")
            return HandlerAction.RETRY
        else:
            # Fallback to graceful degradation
            logger.warning(f"MCP server {server_name} unavailable, degrading gracefully")
            return HandlerAction.DEGRADE_GRACEFULLY
    
    def _handle_timeout_error(self, context: ErrorContext, server_name: str) -> HandlerAction:
        """Handle MCP server timeout errors"""
        self._record_failure(server_name)
        
        if self.should_retry(context):
            # Increase timeout for retry
            recovery_result = self.recovery_manager.execute_recovery(
                strategy=RecoveryStrategy.INCREASE_TIMEOUT,
                context={
                    "server_name": server_name,
                    "current_timeout": context.metadata.get("timeout", 30),
                    "error": context.error
                }
            )
            
            if recovery_result.success:
                return HandlerAction.RETRY
            else:
                return HandlerAction.DEGRADE_GRACEFULLY
        else:
            return HandlerAction.DEGRADE_GRACEFULLY
    
    def _handle_tool_error(self, context: ErrorContext, server_name: str, tool_name: Optional[str]) -> HandlerAction:
        """Handle MCP tool execution errors"""
        tool_name = tool_name or "unknown"
        
        # Some tool errors might be retryable
        if self.should_retry(context):
            error_msg = str(context.error).lower()
            
            if any(keyword in error_msg for keyword in ["timeout", "temporary", "retry"]):
                logger.info(f"Retrying MCP tool {tool_name} on server {server_name}")
                return HandlerAction.RETRY
            else:
                # Tool error might not be retryable, try fallback
                return self._try_fallback_tool(context, server_name, tool_name)
        else:
            return self._try_fallback_tool(context, server_name, tool_name)
    
    def _handle_generic_mcp_error(self, context: ErrorContext, server_name: str) -> HandlerAction:
        """Handle generic MCP server errors"""
        self._record_failure(server_name)
        
        if self.should_retry(context):
            return HandlerAction.RETRY
        else:
            return HandlerAction.DEGRADE_GRACEFULLY
    
    def _try_fallback_tool(self, context: ErrorContext, server_name: str, tool_name: str) -> HandlerAction:
        """Try fallback tool or graceful degradation"""
        if self.fallback_enabled:
            # In practice, this would try alternative tools or local implementations
            logger.info(f"Attempting fallback for tool {tool_name} from server {server_name}")
            
            # Mark in metadata that fallback was used
            context.metadata["fallback_used"] = True
            context.metadata["original_server"] = server_name
            context.metadata["original_tool"] = tool_name
            
            return HandlerAction.DEGRADE_GRACEFULLY
        else:
            return HandlerAction.ESCALATE
    
    def _is_circuit_breaker_open(self, server_name: str) -> bool:
        """Check if circuit breaker is open for server"""
        breaker = self.circuit_breakers.get(server_name)
        if not breaker:
            return False
        
        if breaker["state"] == "open":
            # Check if timeout has passed
            if datetime.utcnow() > breaker["open_until"]:
                # Reset to half-open
                breaker["state"] = "half-open"
                breaker["failure_count"] = 0
                logger.info(f"Circuit breaker for {server_name} moved to half-open")
                return False
            else:
                return True
        
        return False
    
    def _record_failure(self, server_name: str):
        """Record failure for circuit breaker"""
        if server_name not in self.circuit_breakers:
            self.circuit_breakers[server_name] = {
                "state": "closed",
                "failure_count": 0,
                "open_until": None
            }
        
        breaker = self.circuit_breakers[server_name]
        breaker["failure_count"] += 1
        
        if breaker["failure_count"] >= self.circuit_breaker_threshold:
            # Open circuit breaker
            breaker["state"] = "open"
            breaker["open_until"] = datetime.utcnow() + timedelta(seconds=self.circuit_breaker_timeout)
            logger.warning(f"Circuit breaker opened for MCP server {server_name}")
    
    def _record_success(self, server_name: str):
        """Record success for circuit breaker"""
        if server_name in self.circuit_breakers:
            breaker = self.circuit_breakers[server_name]
            if breaker["state"] == "half-open":
                # Close circuit breaker
                breaker["state"] = "closed"
                breaker["failure_count"] = 0
                logger.info(f"Circuit breaker closed for MCP server {server_name}")


class SystemErrorHandler(ErrorHandler):
    """System-level error handler for critical errors"""
    
    def __init__(self, **kwargs):
        super().__init__("SystemErrorHandler", **kwargs)
        
        # System-level configuration
        self.alert_manager = None  # Would be injected
        self.health_check_enabled = True
    
    def can_handle(self, context: ErrorContext) -> bool:
        """Handle all errors as last resort"""
        return True
    
    def handle_error(self, context: ErrorContext) -> HandlerAction:
        """Handle system-level errors"""
        error = context.error
        
        # Handle critical system errors
        if isinstance(error, (DatabaseConnectionError, ResourceError)):
            logger.critical(f"Critical system error: {error}")
            self._trigger_alert(context, "critical")
            return HandlerAction.FAIL_FAST
        
        # Handle authentication/authorization errors
        elif isinstance(error, (AuthenticationError, AuthorizationError)):
            logger.warning(f"Security error: {error}")
            self._trigger_alert(context, "security")
            return HandlerAction.FAIL_FAST
        
        # Handle validation errors
        elif isinstance(error, ValidationError):
            logger.info(f"Validation error: {error}")
            return HandlerAction.IGNORE  # Client should handle validation errors
        
        # Handle unknown errors
        else:
            logger.error(f"Unhandled error: {error}")
            self._trigger_alert(context, "unknown")
            
            if context.escalated or context.recovery_attempts >= self.max_retries:
                return HandlerAction.FAIL_FAST
            else:
                return HandlerAction.ESCALATE
    
    def _trigger_alert(self, context: ErrorContext, alert_type: str):
        """Trigger system alert"""
        try:
            alert_data = {
                "type": alert_type,
                "error": str(context.error),
                "component": context.component,
                "operation": context.operation,
                "timestamp": context.timestamp.isoformat(),
                "correlation_id": context.correlation_id,
                "metadata": context.metadata
            }
            
            # In practice, send to alert manager
            logger.warning(f"System alert triggered: {alert_type}")
            
        except Exception as alert_error:
            logger.error(f"Failed to trigger alert: {alert_error}")


# Error handler factory
class ErrorHandlerFactory:
    """Factory for creating error handler chains"""
    
    @staticmethod
    def create_default_chain() -> ErrorHandler:
        """Create default error handler chain"""
        # Create handlers
        agent_handler = AgentErrorHandler()
        workflow_handler = WorkflowErrorHandler()
        mcp_handler = MCPErrorHandler()
        system_handler = SystemErrorHandler()
        
        # Chain handlers
        agent_handler.set_next(workflow_handler).set_next(mcp_handler).set_next(system_handler)
        
        return agent_handler
    
    @staticmethod
    def create_custom_chain(handlers: List[ErrorHandler]) -> ErrorHandler:
        """Create custom error handler chain"""
        if not handlers:
            raise ValueError("At least one handler is required")
        
        # Chain handlers
        for i in range(len(handlers) - 1):
            handlers[i].set_next(handlers[i + 1])
        
        return handlers[0]


# Decorator for automatic error handling
def handle_errors(
    handler: Optional[ErrorHandler] = None,
    component: str = "unknown",
    operation: str = "unknown"
):
    """Decorator for automatic error handling"""
    
    def decorator(func):
        @functools.wraps(func)
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except Exception as e:
                # Create error context
                context = ErrorContext(
                    error=e,
                    component=component,
                    operation=operation or func.__name__,
                    metadata={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
                )
                
                # Use provided handler or default
                error_handler = handler or ErrorHandlerFactory.create_default_chain()
                
                # Process error
                action = error_handler.process_error(context)
                
                # Handle action
                if action == HandlerAction.RETRY:
                    # In practice, implement retry logic
                    raise e
                elif action == HandlerAction.IGNORE:
                    return None
                elif action == HandlerAction.DEGRADE_GRACEFULLY:
                    # Return degraded result
                    return {"error": "Service temporarily unavailable", "degraded": True}
                else:
                    # Re-raise for ESCALATE, FAIL_FAST
                    raise e
        
        return wrapper
    return decorator


# Async version of error handling decorator
def handle_errors_async(
    handler: Optional[ErrorHandler] = None,
    component: str = "unknown",
    operation: str = "unknown"
):
    """Async decorator for automatic error handling"""
    
    def decorator(func):
        @functools.wraps(func)
        async def wrapper(*args, **kwargs):
            try:
                return await func(*args, **kwargs)
            except Exception as e:
                # Create error context
                context = ErrorContext(
                    error=e,
                    component=component,
                    operation=operation or func.__name__,
                    metadata={"args": str(args)[:100], "kwargs": str(kwargs)[:100]}
                )
                
                # Use provided handler or default
                error_handler = handler or ErrorHandlerFactory.create_default_chain()
                
                # Process error
                action = error_handler.process_error(context)
                
                # Handle action
                if action == HandlerAction.RETRY:
                    # In practice, implement async retry logic
                    raise e
                elif action == HandlerAction.IGNORE:
                    return None
                elif action == HandlerAction.DEGRADE_GRACEFULLY:
                    # Return degraded result
                    return {"error": "Service temporarily unavailable", "degraded": True}
                else:
                    # Re-raise for ESCALATE, FAIL_FAST
                    raise e
        
        return wrapper
    return decorator