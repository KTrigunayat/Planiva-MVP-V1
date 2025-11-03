"""
Custom exceptions for Task Management Agent

Defines exception hierarchy for task management operations:
- TaskManagementError: Base exception for all task management errors
- SubAgentDataError: Errors related to sub-agent data processing
- ToolExecutionError: Errors during tool execution
- ConsolidationError: Errors during data consolidation
"""


class TaskManagementError(Exception):
    """
    Base exception for Task Management Agent errors.
    
    All task management-specific exceptions inherit from this class
    to allow for centralized error handling and logging.
    """
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize TaskManagementError
        
        Args:
            message: Human-readable error message
            details: Optional dictionary with additional error context
        """
        super().__init__(message)
        self.message = message
        self.details = details or {}
    
    def __str__(self):
        if self.details:
            return f"{self.message} | Details: {self.details}"
        return self.message


class SubAgentDataError(TaskManagementError):
    """
    Exception raised when sub-agent data is missing, incomplete, or invalid.
    
    This error is raised when:
    - A sub-agent fails to return expected data
    - Sub-agent data is malformed or doesn't match expected schema
    - Required fields are missing from sub-agent output
    
    The Task Management Agent should handle this gracefully by logging
    the error and continuing with partial data when possible.
    """
    
    def __init__(self, sub_agent_name: str, message: str, details: dict = None):
        """
        Initialize SubAgentDataError
        
        Args:
            sub_agent_name: Name of the sub-agent that failed
            message: Error description
            details: Additional context about the error
        """
        self.sub_agent_name = sub_agent_name
        error_details = details or {}
        error_details['sub_agent'] = sub_agent_name
        super().__init__(f"Sub-agent '{sub_agent_name}' error: {message}", error_details)


class ToolExecutionError(TaskManagementError):
    """
    Exception raised when a tool fails to execute successfully.
    
    This error is raised when:
    - A tool encounters an unexpected error during execution
    - Tool dependencies (database, LLM, external services) are unavailable
    - Tool input validation fails
    - Tool processing times out
    
    The Task Management Agent should handle this by logging the error,
    marking affected tasks, and continuing with remaining tools when possible.
    """
    
    def __init__(self, tool_name: str, message: str, details: dict = None):
        """
        Initialize ToolExecutionError
        
        Args:
            tool_name: Name of the tool that failed
            message: Error description
            details: Additional context including affected tasks, error type, etc.
        """
        self.tool_name = tool_name
        error_details = details or {}
        error_details['tool'] = tool_name
        super().__init__(f"Tool '{tool_name}' execution failed: {message}", error_details)


class ConsolidationError(TaskManagementError):
    """
    Exception raised when data consolidation from sub-agents fails.
    
    This error is raised when:
    - Sub-agent outputs cannot be merged due to conflicting data
    - Required data for consolidation is missing
    - Data validation fails during consolidation
    - Consolidated data structure is invalid
    
    This is a critical error that may prevent the Task Management Agent
    from proceeding with tool processing.
    """
    
    def __init__(self, message: str, details: dict = None):
        """
        Initialize ConsolidationError
        
        Args:
            message: Error description
            details: Additional context including which sub-agents were involved,
                    what data failed to consolidate, etc.
        """
        super().__init__(f"Data consolidation failed: {message}", details)
