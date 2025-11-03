"""
Consolidated Models for Task Management Agent

Contains models for consolidated data from sub-agents:
- ConsolidatedTask: Unified task data from all three sub-agents
- ConsolidatedTaskData: Collection of consolidated tasks with metadata
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
class ConsolidatedTask:
    """
    Unified task data combining outputs from all three sub-agents.
    This structure is populated by sub-agents and then enhanced by tools.
    """
    # From Prioritization Agent
    task_id: str
    task_name: str
    priority_level: str
    priority_score: float
    priority_rationale: str
    
    # From Granularity Agent
    parent_task_id: Optional[str]
    task_description: str
    granularity_level: int
    estimated_duration: timedelta
    sub_tasks: List[str] = field(default_factory=list)
    
    # From Resource & Dependency Agent
    dependencies: List[str] = field(default_factory=list)
    resources_required: List[Resource] = field(default_factory=list)
    resource_conflicts: List[str] = field(default_factory=list)
    
    # To be populated by tools (initialized as None)
    timeline: Optional[TaskTimeline] = None
    llm_enhancements: Optional[Dict] = None
    assigned_vendors: List[str] = field(default_factory=list)
    logistics_status: Optional[LogisticsStatus] = None
    conflicts: List[Conflict] = field(default_factory=list)
    venue_info: Optional[VenueInfo] = None


@dataclass
class ConsolidatedTaskData:
    """
    Collection of consolidated tasks with event context and processing metadata.
    This is the main data structure passed between sub-agents and tools.
    """
    tasks: List[ConsolidatedTask] = field(default_factory=list)
    event_context: Dict = field(default_factory=dict)
    processing_metadata: Dict = field(default_factory=dict)
