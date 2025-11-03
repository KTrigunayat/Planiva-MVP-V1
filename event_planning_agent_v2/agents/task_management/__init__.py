"""
Task Management Agent Module

This module contains the Task Management Agent and its sub-components for
processing event planning tasks with prioritization, granularity analysis,
dependency tracking, and comprehensive tool-based enhancements.
"""

# Import exceptions
from .exceptions import (
    TaskManagementError,
    SubAgentDataError,
    ToolExecutionError,
    ConsolidationError
)

# Core agent will be imported once implemented
# from .core.task_management_agent import TaskManagementAgent

__all__ = [
    'TaskManagementError',
    'SubAgentDataError',
    'ToolExecutionError',
    'ConsolidationError',
    # 'TaskManagementAgent',  # Will be uncommented when implemented
]
