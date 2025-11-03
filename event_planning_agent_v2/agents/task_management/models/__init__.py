"""
Task Management Data Models Module

Contains all data models used by the Task Management Agent:
- Base data models (Resource, TaskTimeline, etc.)
- Task-specific models (PrioritizedTask, GranularTask, etc.)
- Consolidated models (ConsolidatedTask, ConsolidatedTaskData)
- Extended models (ExtendedTask, ExtendedTaskList, ProcessingSummary)
"""

from .data_models import (
    Resource,
    TaskTimeline,
    EnhancedTask,
    VendorAssignment,
    LogisticsStatus,
    Conflict,
    VenueInfo
)

from .task_models import (
    PrioritizedTask,
    GranularTask,
    TaskWithDependencies
)

from .consolidated_models import (
    ConsolidatedTask,
    ConsolidatedTaskData
)

from .extended_models import (
    ExtendedTask,
    ExtendedTaskList,
    ProcessingSummary
)

__all__ = [
    # Base data models
    'Resource',
    'TaskTimeline',
    'EnhancedTask',
    'VendorAssignment',
    'LogisticsStatus',
    'Conflict',
    'VenueInfo',
    # Task-specific models
    'PrioritizedTask',
    'GranularTask',
    'TaskWithDependencies',
    # Consolidated models
    'ConsolidatedTask',
    'ConsolidatedTaskData',
    # Extended models
    'ExtendedTask',
    'ExtendedTaskList',
    'ProcessingSummary'
]
