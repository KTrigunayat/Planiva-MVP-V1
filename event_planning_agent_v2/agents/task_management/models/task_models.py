"""
Task-Specific Models for Task Management Agent

Contains models for task analysis by sub-agents:
- PrioritizedTask: Task with priority information
- GranularTask: Task with granularity breakdown
- TaskWithDependencies: Task with dependencies and resource requirements
"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Optional
from .data_models import Resource


@dataclass
class PrioritizedTask:
    """Task with priority information from Prioritization Agent"""
    task_id: str
    task_name: str
    priority_level: str  # Critical, High, Medium, Low
    priority_score: float
    priority_rationale: str


@dataclass
class GranularTask:
    """Task with granularity breakdown from Granularity Agent"""
    task_id: str
    parent_task_id: Optional[str]
    task_name: str
    task_description: str
    granularity_level: int  # 0=top-level, 1=sub-task, 2=detailed sub-task
    estimated_duration: timedelta
    sub_tasks: List[str] = field(default_factory=list)  # IDs of child tasks


@dataclass
class TaskWithDependencies:
    """Task with dependencies and resources from Resource & Dependency Agent"""
    task_id: str
    task_name: str
    dependencies: List[str] = field(default_factory=list)  # IDs of prerequisite tasks
    resources_required: List[Resource] = field(default_factory=list)
    resource_conflicts: List[str] = field(default_factory=list)  # Potential resource conflicts
