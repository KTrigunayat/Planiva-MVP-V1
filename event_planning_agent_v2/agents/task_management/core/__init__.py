"""
Task Management Core Module

Contains the core orchestration logic for the Task Management Agent.
"""

from .data_consolidator import DataConsolidator
from .task_management_agent import TaskManagementAgent

__all__ = ['DataConsolidator', 'TaskManagementAgent']
