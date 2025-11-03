"""
Extended Models for Task Management Agent

Contains models for the final output of the Task Management Agent:
- ExtendedTask: Complete task with all enhancements from sub-agents and tools
- ExtendedTaskList: Collection of extended tasks with processing summary
- ProcessingSummary: Summary of task processing results
"""

from dataclasses import dataclass, field
from datetime import timedelta
from typing import List, Optional, Dict
from .data_models import (
    Resource,
    TaskTimeline,
    VendorAssignment,
    LogisticsStatus,
    Conflict,
    VenueInfo
)


@dataclass
class ExtendedTask:
    """
    Complete task with all data from sub-agents and tool enhancements.
    This is the final task structure stored in EventPlanningState.
    """
    # Original consolidated data
    task_id: str
    task_name: str
    task_description: str
    priority_level: str
    priority_score: float
    granularity_level: int
    parent_task_id: Optional[str]
    sub_tasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    resources_required: List[Resource] = field(default_factory=list)
    
    # Tool enhancements
    timeline: Optional[TaskTimeline] = None
    llm_enhancements: Dict = field(default_factory=dict)
    assigned_vendors: List[VendorAssignment] = field(default_factory=list)
    logistics_status: Optional[LogisticsStatus] = None
    conflicts: List[Conflict] = field(default_factory=list)
    venue_info: Optional[VenueInfo] = None
    
    # Status flags
    has_errors: bool = False
    has_warnings: bool = False
    requires_manual_review: bool = False
    error_messages: List[str] = field(default_factory=list)
    warning_messages: List[str] = field(default_factory=list)


@dataclass
class ProcessingSummary:
    """Summary of task processing results"""
    total_tasks: int
    tasks_with_errors: int
    tasks_with_warnings: int
    tasks_requiring_review: int
    processing_time: float
    tool_execution_status: Dict[str, str] = field(default_factory=dict)


@dataclass
class ExtendedTaskList:
    """
    Final output structure containing all processed tasks with summary.
    This is stored in EventPlanningState.extended_task_list field.
    """
    tasks: List[ExtendedTask] = field(default_factory=list)
    processing_summary: ProcessingSummary = field(default_factory=lambda: ProcessingSummary(
        total_tasks=0,
        tasks_with_errors=0,
        tasks_with_warnings=0,
        tasks_requiring_review=0,
        processing_time=0.0
    ))
    metadata: Dict = field(default_factory=dict)
