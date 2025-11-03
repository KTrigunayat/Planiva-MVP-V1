"""
Error handling and recovery utilities for Task Management Agent.

Provides comprehensive error handling for:
- Sub-agent errors (Prioritization, Granularity, Resource & Dependency)
- Tool execution errors (Timeline, LLM, Vendor, Logistics, Conflict, Venue)
- Critical failures requiring workflow termination
- State management and error tracking

Integrates with:
- Existing error handlers from error_handling/handlers.py
- Existing error monitoring from error_handling/monitoring.py
- StateTransitionLogger for error tracking
- EventPlanningState for error count and last_error updates
"""

import logging
import traceback
from typing import Dict, Any, Optional, List, Callable
from datetime import datetime
from functools import wraps

from ..exceptions import TaskManagementError, SubAgentDataError, ToolExecutionError, ConsolidationError
from ..models.extended_models import ExtendedTask, ExtendedTaskList, ProcessingSummary
from ..models.consolidated_models import ConsolidatedTaskData
from ....workflows.state_models import EventPlanningState, WorkflowStatus, StateTransitionLogger
from ....error_handling.handlers import ErrorHandler, ErrorContext, HandlerAction, AgentErrorHandler
from ....error_handling.monitoring import get_error_monitor, record_error
from ....error_handling.exceptions import AgentError, ErrorSeverity, ErrorCategory

logger = logging.getLogger(__name__)


class TaskManagementErrorHandler:
    """
    Specialized error handler for Task Management Agent operations.
    
    Provides error handling and recovery strategies for:
    - Sub-agent failures with partial data continuation
    - Tool execution failures with task marking
    - Critical failures with workflow termination
    - State updates and error tracking
    """
    
    def __init__(self):
        """Initialize error handler with monitoring and logging"""
        self.error_monitor = get_error_monitor()
        self.transition_logger = StateTransitionLogger()
        self.agent_error_handler = AgentErrorHandler()
        
        # Error tracking
        self.sub_agent_errors: List[Dict[str, Any]] = []
        self.tool_errors: List[Dict[str, Any]] = []
        self.critical_errors: List[Dict[str, Any]] = []
    
    def handle_sub_agent_error(
        self,
        error: Exception,
        sub_agent_name: str,
        state: EventPlanningState,
        partial_data: Optional[Any] = None
    ) -> tuple[bool, Optional[Any]]:
        """
        Handle sub-agent errors and continue with partial data.
        
        Sub-agent errors are non-critical - the system should log the error
        and continue processing with whatever data is available.
        
        Args:
            error: The exception that occurred
            sub_agent_name: Name of the sub-agent that failed
            state: Current EventPlanningState
            partial_data: Any partial data that was successfully retrieved
        
        Returns:
            Tuple of (should_continue, data_to_use)
            - should_continue: True if processing should continue
            - data_to_use: Partial data if available, None otherwise
        """
        error_details = {
            'sub_agent': sub_agent_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'has_partial_data': partial_data is not None,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        # Log error to monitoring system
        record_error(
            error=error,
            component=f"task_management.sub_agent.{sub_agent_name}",
            operation="sub_agent_processing",
            correlation_id=state.get('plan_id'),
            metadata=error_details
        )
        
        # Track error internally
        self.sub_agent_errors.append(error_details)
        
        # Update state error tracking
        state['error_count'] = state.get('error_count', 0) + 1
        state['last_error'] = f"Sub-agent {sub_agent_name} failed: {str(error)}"
        state['last_updated'] = datetime.utcnow().isoformat()
        
        # Log state transition for error
        self.transition_logger.log_transition(
            state=state,
            from_status=state.get('workflow_status', 'unknown'),
            to_status=state.get('workflow_status', 'unknown'),  # Status unchanged
            trigger=f"sub_agent_error_{sub_agent_name}",
            additional_data=error_details
        )
        
        # Log warning and continue with partial data
        if partial_data is not None:
            logger.warning(
                f"Sub-agent {sub_agent_name} failed but partial data available. "
                f"Continuing with partial data. Error: {str(error)}"
            )
            return True, partial_data
        else:
            logger.warning(
                f"Sub-agent {sub_agent_name} failed with no partial data. "
                f"Continuing without {sub_agent_name} data. Error: {str(error)}"
            )
            return True, None
    
    def handle_tool_error(
        self,
        error: Exception,
        tool_name: str,
        state: EventPlanningState,
        affected_tasks: Optional[List[str]] = None
    ) -> tuple[bool, Dict[str, Any]]:
        """
        Handle tool execution errors and mark affected tasks.
        
        Tool errors are logged and affected tasks are marked with error flags.
        Processing continues with remaining tools.
        
        Args:
            error: The exception that occurred
            tool_name: Name of the tool that failed
            state: Current EventPlanningState
            affected_tasks: List of task IDs affected by the failure
        
        Returns:
            Tuple of (should_continue, error_metadata)
            - should_continue: True if processing should continue
            - error_metadata: Metadata about the error for task marking
        """
        error_details = {
            'tool': tool_name,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'affected_tasks': affected_tasks or [],
            'timestamp': datetime.utcnow().isoformat(),
            'traceback': traceback.format_exc()
        }
        
        # Log error to monitoring system
        record_error(
            error=error,
            component=f"task_management.tool.{tool_name}",
            operation="tool_execution",
            correlation_id=state.get('plan_id'),
            metadata=error_details
        )
        
        # Track error internally
        self.tool_errors.append(error_details)
        
        # Update state error tracking
        state['error_count'] = state.get('error_count', 0) + 1
        state['last_error'] = f"Tool {tool_name} failed: {str(error)}"
        state['last_updated'] = datetime.utcnow().isoformat()
        
        # Log state transition for error
        self.transition_logger.log_transition(
            state=state,
            from_status=state.get('workflow_status', 'unknown'),
            to_status=state.get('workflow_status', 'unknown'),  # Status unchanged
            trigger=f"tool_error_{tool_name}",
            additional_data=error_details
        )
        
        # Log error and continue
        logger.error(
            f"Tool {tool_name} execution failed. Marking affected tasks and continuing. "
            f"Error: {str(error)}"
        )
        
        # Return metadata for marking tasks
        error_metadata = {
            'tool_name': tool_name,
            'error_message': str(error),
            'error_type': type(error).__name__,
            'timestamp': datetime.utcnow().isoformat()
        }
        
        return True, error_metadata
    
    def handle_critical_error(
        self,
        error: Exception,
        state: EventPlanningState,
        operation: str
    ) -> EventPlanningState:
        """
        Handle critical errors that require workflow termination.
        
        Critical errors include:
        - Database connection failures
        - State management failures
        - Unrecoverable system errors
        
        Args:
            error: The critical exception that occurred
            state: Current EventPlanningState
            operation: Operation that was being performed
        
        Returns:
            Updated EventPlanningState with FAILED status
        """
        error_details = {
            'operation': operation,
            'error_type': type(error).__name__,
            'error_message': str(error),
            'timestamp': datetime.utcnow().isoformat(),
            'traceback': traceback.format_exc(),
            'plan_id': state.get('plan_id')
        }
        
        # Log critical error to monitoring system
        record_error(
            error=error,
            component="task_management.critical",
            operation=operation,
            correlation_id=state.get('plan_id'),
            metadata=error_details
        )
        
        # Track error internally
        self.critical_errors.append(error_details)
        
        # Update state to FAILED
        state['workflow_status'] = WorkflowStatus.FAILED.value
        state['error_count'] = state.get('error_count', 0) + 1
        state['last_error'] = f"Critical error in {operation}: {str(error)}"
        state['last_updated'] = datetime.utcnow().isoformat()
        
        # Log state transition to FAILED
        self.transition_logger.log_transition(
            state=state,
            from_status=state.get('workflow_status', WorkflowStatus.RUNNING.value),
            to_status=WorkflowStatus.FAILED.value,
            trigger=f"critical_error_{operation}",
            additional_data=error_details
        )
        
        # Log critical error
        logger.critical(
            f"Critical error in Task Management Agent during {operation}. "
            f"Workflow terminated. Error: {str(error)}\n"
            f"Traceback: {traceback.format_exc()}"
        )
        
        return state
    
    def mark_tasks_with_errors(
        self,
        tasks: List[ExtendedTask],
        error_metadata: Dict[str, Any],
        affected_task_ids: Optional[List[str]] = None
    ) -> List[ExtendedTask]:
        """
        Mark tasks with error flags and messages.
        
        Args:
            tasks: List of ExtendedTask objects
            error_metadata: Metadata about the error
            affected_task_ids: Optional list of specific task IDs to mark
                              (if None, marks all tasks)
        
        Returns:
            Updated list of ExtendedTask objects with error flags
        """
        for task in tasks:
            # Check if this task should be marked
            if affected_task_ids is None or task.task_id in affected_task_ids:
                task.has_errors = True
                
                # Add error message
                error_msg = (
                    f"Tool '{error_metadata.get('tool_name')}' failed: "
                    f"{error_metadata.get('error_message')}"
                )
                task.error_messages.append(error_msg)
                
                # Mark for manual review
                task.requires_manual_review = True
                
                logger.debug(f"Marked task {task.task_id} with error from {error_metadata.get('tool_name')}")
        
        return tasks
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get summary of all errors encountered during processing.
        
        Returns:
            Dictionary with error statistics and details
        """
        return {
            'total_errors': len(self.sub_agent_errors) + len(self.tool_errors) + len(self.critical_errors),
            'sub_agent_errors': {
                'count': len(self.sub_agent_errors),
                'errors': self.sub_agent_errors
            },
            'tool_errors': {
                'count': len(self.tool_errors),
                'errors': self.tool_errors
            },
            'critical_errors': {
                'count': len(self.critical_errors),
                'errors': self.critical_errors
            },
            'timestamp': datetime.utcnow().isoformat()
        }
    
    def reset_error_tracking(self):
        """Reset error tracking for new processing run"""
        self.sub_agent_errors = []
        self.tool_errors = []
        self.critical_errors = []


def process_with_error_handling(func: Callable) -> Callable:
    """
    Decorator for wrapping Task Management Agent methods with error handling.
    
    Provides automatic error handling, logging, and state updates for
    Task Management Agent operations.
    
    Usage:
        @process_with_error_handling
        def process(self, state: EventPlanningState) -> EventPlanningState:
            # Method implementation
            pass
    
    Args:
        func: Function to wrap with error handling
    
    Returns:
        Wrapped function with error handling
    """
    @wraps(func)
    def wrapper(self, state: EventPlanningState, *args, **kwargs) -> EventPlanningState:
        """Wrapper function with error handling"""
        error_handler = getattr(self, 'error_handler', TaskManagementErrorHandler())
        
        try:
            # Execute the wrapped function
            logger.info(f"Executing {func.__name__} with error handling")
            result = func(self, state, *args, **kwargs)
            
            # Log successful completion
            logger.info(f"Successfully completed {func.__name__}")
            return result
            
        except SubAgentDataError as e:
            # Handle sub-agent errors
            logger.warning(f"Sub-agent error in {func.__name__}: {str(e)}")
            
            # Use error handler to process
            should_continue, partial_data = error_handler.handle_sub_agent_error(
                error=e,
                sub_agent_name=e.sub_agent_name,
                state=state,
                partial_data=None
            )
            
            if should_continue:
                # Continue with partial data - return state with error logged
                return state
            else:
                # Cannot continue - mark as failed
                return error_handler.handle_critical_error(e, state, func.__name__)
        
        except ToolExecutionError as e:
            # Handle tool execution errors
            logger.error(f"Tool execution error in {func.__name__}: {str(e)}")
            
            # Use error handler to process
            should_continue, error_metadata = error_handler.handle_tool_error(
                error=e,
                tool_name=e.tool_name,
                state=state,
                affected_tasks=e.details.get('affected_tasks')
            )
            
            if should_continue:
                # Continue with remaining tools - return state with error logged
                return state
            else:
                # Cannot continue - mark as failed
                return error_handler.handle_critical_error(e, state, func.__name__)
        
        except ConsolidationError as e:
            # Handle consolidation errors
            logger.error(f"Consolidation error in {func.__name__}: {str(e)}")
            
            # Consolidation errors are critical - cannot continue
            return error_handler.handle_critical_error(e, state, func.__name__)
        
        except TaskManagementError as e:
            # Handle generic task management errors
            logger.error(f"Task management error in {func.__name__}: {str(e)}")
            
            # Generic errors are treated as critical
            return error_handler.handle_critical_error(e, state, func.__name__)
        
        except Exception as e:
            # Handle unexpected errors
            logger.critical(f"Unexpected error in {func.__name__}: {str(e)}")
            
            # Unexpected errors are critical
            return error_handler.handle_critical_error(e, state, func.__name__)
    
    return wrapper


# Convenience functions for error handling
def create_error_handler() -> TaskManagementErrorHandler:
    """Create a new TaskManagementErrorHandler instance"""
    return TaskManagementErrorHandler()


def handle_sub_agent_failure(
    sub_agent_name: str,
    error: Exception,
    state: EventPlanningState
) -> tuple[bool, Optional[Any]]:
    """
    Convenience function for handling sub-agent failures.
    
    Args:
        sub_agent_name: Name of the failed sub-agent
        error: The exception that occurred
        state: Current EventPlanningState
    
    Returns:
        Tuple of (should_continue, partial_data)
    """
    handler = TaskManagementErrorHandler()
    return handler.handle_sub_agent_error(error, sub_agent_name, state)


def handle_tool_failure(
    tool_name: str,
    error: Exception,
    state: EventPlanningState,
    affected_tasks: Optional[List[str]] = None
) -> tuple[bool, Dict[str, Any]]:
    """
    Convenience function for handling tool failures.
    
    Args:
        tool_name: Name of the failed tool
        error: The exception that occurred
        state: Current EventPlanningState
        affected_tasks: Optional list of affected task IDs
    
    Returns:
        Tuple of (should_continue, error_metadata)
    """
    handler = TaskManagementErrorHandler()
    return handler.handle_tool_error(error, tool_name, state, affected_tasks)


def handle_critical_failure(
    error: Exception,
    state: EventPlanningState,
    operation: str
) -> EventPlanningState:
    """
    Convenience function for handling critical failures.
    
    Args:
        error: The critical exception
        state: Current EventPlanningState
        operation: Operation that was being performed
    
    Returns:
        Updated EventPlanningState with FAILED status
    """
    handler = TaskManagementErrorHandler()
    return handler.handle_critical_error(error, state, operation)
