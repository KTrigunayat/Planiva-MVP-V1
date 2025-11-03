"""
Custom exception classes for the Event Planning Agent system.

Provides a hierarchy of exceptions for different system components and error types.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorSeverity(str, Enum):
    """Error severity levels"""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    CRITICAL = "critical"


class ErrorCategory(str, Enum):
    """Error categories for classification"""
    VALIDATION = "validation"
    AUTHENTICATION = "authentication"
    AUTHORIZATION = "authorization"
    RESOURCE = "resource"
    NETWORK = "network"
    DATABASE = "database"
    EXTERNAL_SERVICE = "external_service"
    BUSINESS_LOGIC = "business_logic"
    SYSTEM = "system"
    UNKNOWN = "unknown"


class EventPlanningError(Exception):
    """Base exception for all Event Planning Agent errors"""
    
    def __init__(
        self,
        message: str,
        error_code: Optional[str] = None,
        severity: ErrorSeverity = ErrorSeverity.MEDIUM,
        category: ErrorCategory = ErrorCategory.UNKNOWN,
        context: Optional[Dict[str, Any]] = None,
        recoverable: bool = True,
        retry_after: Optional[int] = None
    ):
        super().__init__(message)
        self.message = message
        self.error_code = error_code or self.__class__.__name__
        self.severity = severity
        self.category = category
        self.context = context or {}
        self.recoverable = recoverable
        self.retry_after = retry_after
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for serialization"""
        return {
            "error_type": self.__class__.__name__,
            "message": self.message,
            "error_code": self.error_code,
            "severity": self.severity.value,
            "category": self.category.value,
            "context": self.context,
            "recoverable": self.recoverable,
            "retry_after": self.retry_after
        }


class AgentError(EventPlanningError):
    """Base exception for agent-related errors"""
    
    def __init__(
        self,
        message: str,
        agent_name: Optional[str] = None,
        task_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.agent_name = agent_name
        self.task_name = task_name
        if agent_name:
            self.context["agent_name"] = agent_name
        if task_name:
            self.context["task_name"] = task_name


class AgentInitializationError(AgentError):
    """Error during agent initialization"""
    
    def __init__(self, message: str, agent_name: str, **kwargs):
        super().__init__(
            message,
            agent_name=agent_name,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            recoverable=False,
            **kwargs
        )


class AgentExecutionError(AgentError):
    """Error during agent task execution"""
    
    def __init__(self, message: str, agent_name: str, task_name: str, **kwargs):
        super().__init__(
            message,
            agent_name=agent_name,
            task_name=task_name,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.BUSINESS_LOGIC,
            **kwargs
        )


class AgentTimeoutError(AgentError):
    """Agent execution timeout"""
    
    def __init__(self, message: str, agent_name: str, timeout_seconds: int, **kwargs):
        super().__init__(
            message,
            agent_name=agent_name,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.RESOURCE,
            retry_after=timeout_seconds * 2,
            **kwargs
        )
        self.context["timeout_seconds"] = timeout_seconds


class AgentCommunicationError(AgentError):
    """Error in inter-agent communication"""
    
    def __init__(self, message: str, source_agent: str, target_agent: str, **kwargs):
        super().__init__(
            message,
            agent_name=source_agent,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.NETWORK,
            **kwargs
        )
        self.context["source_agent"] = source_agent
        self.context["target_agent"] = target_agent


class WorkflowError(EventPlanningError):
    """Base exception for workflow-related errors"""
    
    def __init__(
        self,
        message: str,
        workflow_id: Optional[str] = None,
        node_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.workflow_id = workflow_id
        self.node_name = node_name
        if workflow_id:
            self.context["workflow_id"] = workflow_id
        if node_name:
            self.context["node_name"] = node_name


class WorkflowStateError(WorkflowError):
    """Error in workflow state management"""
    
    def __init__(self, message: str, workflow_id: str, **kwargs):
        super().__init__(
            message,
            workflow_id=workflow_id,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            **kwargs
        )


class WorkflowExecutionError(WorkflowError):
    """Error during workflow execution"""
    
    def __init__(self, message: str, workflow_id: str, node_name: str, **kwargs):
        super().__init__(
            message,
            workflow_id=workflow_id,
            node_name=node_name,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.BUSINESS_LOGIC,
            **kwargs
        )


class WorkflowRecursionError(WorkflowError):
    """Workflow recursion limit exceeded"""
    
    def __init__(self, message: str, workflow_id: str, recursion_limit: int, **kwargs):
        super().__init__(
            message,
            workflow_id=workflow_id,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            recoverable=False,
            **kwargs
        )
        self.context["recursion_limit"] = recursion_limit


class WorkflowTimeoutError(WorkflowError):
    """Workflow execution timeout"""
    
    def __init__(self, message: str, workflow_id: str, timeout_seconds: int, **kwargs):
        super().__init__(
            message,
            workflow_id=workflow_id,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.RESOURCE,
            retry_after=timeout_seconds * 2,
            **kwargs
        )
        self.context["timeout_seconds"] = timeout_seconds


class MCPServerError(EventPlanningError):
    """Base exception for MCP server errors"""
    
    def __init__(
        self,
        message: str,
        server_name: Optional[str] = None,
        tool_name: Optional[str] = None,
        **kwargs
    ):
        super().__init__(message, **kwargs)
        self.server_name = server_name
        self.tool_name = tool_name
        if server_name:
            self.context["server_name"] = server_name
        if tool_name:
            self.context["tool_name"] = tool_name


class MCPServerConnectionError(MCPServerError):
    """MCP server connection error"""
    
    def __init__(self, message: str, server_name: str, **kwargs):
        super().__init__(
            message,
            server_name=server_name,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.NETWORK,
            **kwargs
        )


class MCPServerTimeoutError(MCPServerError):
    """MCP server timeout error"""
    
    def __init__(self, message: str, server_name: str, timeout_seconds: int, **kwargs):
        super().__init__(
            message,
            server_name=server_name,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.RESOURCE,
            retry_after=timeout_seconds,
            **kwargs
        )
        self.context["timeout_seconds"] = timeout_seconds


class MCPToolError(MCPServerError):
    """MCP tool execution error"""
    
    def __init__(self, message: str, server_name: str, tool_name: str, **kwargs):
        super().__init__(
            message,
            server_name=server_name,
            tool_name=tool_name,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_SERVICE,
            **kwargs
        )


class DatabaseError(EventPlanningError):
    """Database-related errors"""
    
    def __init__(self, message: str, operation: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.DATABASE,
            **kwargs
        )
        self.operation = operation
        if operation:
            self.context["operation"] = operation


class DatabaseConnectionError(DatabaseError):
    """Database connection error"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.CRITICAL,
            retry_after=30,
            **kwargs
        )


class DatabaseQueryError(DatabaseError):
    """Database query execution error"""
    
    def __init__(self, message: str, query: Optional[str] = None, **kwargs):
        super().__init__(message, **kwargs)
        if query:
            self.context["query"] = query[:500]  # Truncate long queries


class ValidationError(EventPlanningError):
    """Data validation errors"""
    
    def __init__(
        self,
        message: str,
        field_name: Optional[str] = None,
        field_value: Optional[Any] = None,
        **kwargs
    ):
        super().__init__(
            message,
            severity=ErrorSeverity.LOW,
            category=ErrorCategory.VALIDATION,
            recoverable=False,
            **kwargs
        )
        if field_name:
            self.context["field_name"] = field_name
        if field_value is not None:
            self.context["field_value"] = str(field_value)[:100]  # Truncate long values


class AuthenticationError(EventPlanningError):
    """Authentication errors"""
    
    def __init__(self, message: str, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.AUTHENTICATION,
            recoverable=False,
            **kwargs
        )


class AuthorizationError(EventPlanningError):
    """Authorization errors"""
    
    def __init__(self, message: str, required_permission: Optional[str] = None, **kwargs):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.AUTHORIZATION,
            recoverable=False,
            **kwargs
        )
        if required_permission:
            self.context["required_permission"] = required_permission


class ResourceError(EventPlanningError):
    """Resource-related errors (memory, disk, etc.)"""
    
    def __init__(
        self,
        message: str,
        resource_type: Optional[str] = None,
        current_usage: Optional[float] = None,
        limit: Optional[float] = None,
        **kwargs
    ):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.RESOURCE,
            **kwargs
        )
        if resource_type:
            self.context["resource_type"] = resource_type
        if current_usage is not None:
            self.context["current_usage"] = current_usage
        if limit is not None:
            self.context["limit"] = limit


class ExternalServiceError(EventPlanningError):
    """External service integration errors"""
    
    def __init__(
        self,
        message: str,
        service_name: Optional[str] = None,
        status_code: Optional[int] = None,
        **kwargs
    ):
        super().__init__(
            message,
            severity=ErrorSeverity.MEDIUM,
            category=ErrorCategory.EXTERNAL_SERVICE,
            **kwargs
        )
        if service_name:
            self.context["service_name"] = service_name
        if status_code:
            self.context["status_code"] = status_code


class RecoveryError(EventPlanningError):
    """Error during recovery operations"""
    
    def __init__(
        self,
        message: str,
        recovery_strategy: Optional[str] = None,
        original_error: Optional[str] = None,
        **kwargs
    ):
        super().__init__(
            message,
            severity=ErrorSeverity.HIGH,
            category=ErrorCategory.SYSTEM,
            recoverable=False,
            **kwargs
        )
        if recovery_strategy:
            self.context["recovery_strategy"] = recovery_strategy
        if original_error:
            self.context["original_error"] = original_error


# Convenience functions for creating common errors
def create_agent_error(
    message: str,
    agent_name: str,
    task_name: Optional[str] = None,
    error_type: str = "execution"
) -> AgentError:
    """Create appropriate agent error based on type"""
    if error_type == "initialization":
        return AgentInitializationError(message, agent_name)
    elif error_type == "timeout":
        return AgentTimeoutError(message, agent_name, 30)
    elif error_type == "execution":
        return AgentExecutionError(message, agent_name, task_name or "unknown")
    else:
        return AgentError(message, agent_name, task_name)


def create_workflow_error(
    message: str,
    workflow_id: str,
    node_name: Optional[str] = None,
    error_type: str = "execution"
) -> WorkflowError:
    """Create appropriate workflow error based on type"""
    if error_type == "state":
        return WorkflowStateError(message, workflow_id)
    elif error_type == "recursion":
        return WorkflowRecursionError(message, workflow_id, 50)
    elif error_type == "timeout":
        return WorkflowTimeoutError(message, workflow_id, 300)
    elif error_type == "execution":
        return WorkflowExecutionError(message, workflow_id, node_name or "unknown")
    else:
        return WorkflowError(message, workflow_id, node_name)


def create_mcp_error(
    message: str,
    server_name: str,
    tool_name: Optional[str] = None,
    error_type: str = "tool"
) -> MCPServerError:
    """Create appropriate MCP server error based on type"""
    if error_type == "connection":
        return MCPServerConnectionError(message, server_name)
    elif error_type == "timeout":
        return MCPServerTimeoutError(message, server_name, 30)
    elif error_type == "tool":
        return MCPToolError(message, server_name, tool_name or "unknown")
    else:
        return MCPServerError(message, server_name, tool_name)