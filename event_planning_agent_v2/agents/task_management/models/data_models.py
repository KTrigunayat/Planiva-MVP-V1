"""
Base Data Models for Task Management Agent

Contains fundamental data structures used across the Task Management Agent:
- Resource: Represents required resources (vendors, equipment, personnel, venue)
- TaskTimeline: Timeline information for tasks
- EnhancedTask: LLM-enhanced task information
- VendorAssignment: Vendor-to-task assignments
- LogisticsStatus: Logistics verification results
- Conflict: Detected conflicts
- VenueInfo: Venue information for tasks
"""

from dataclasses import dataclass, field
from datetime import datetime, timedelta
from typing import List, Optional, Dict


@dataclass
class Resource:
    """Represents a resource required for a task"""
    resource_type: str  # vendor, equipment, personnel, venue
    resource_id: str
    resource_name: str
    quantity_required: int
    availability_constraint: Optional[str] = None


@dataclass
class TaskTimeline:
    """Timeline information for a task"""
    task_id: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    buffer_time: timedelta
    scheduling_constraints: List[str] = field(default_factory=list)


@dataclass
class EnhancedTask:
    """LLM-enhanced task information"""
    task_id: str
    enhanced_description: str
    suggestions: List[str] = field(default_factory=list)
    potential_issues: List[str] = field(default_factory=list)
    best_practices: List[str] = field(default_factory=list)
    requires_manual_review: bool = False


@dataclass
class VendorAssignment:
    """Vendor assignment to a task"""
    task_id: str
    vendor_id: str
    vendor_name: str
    vendor_type: str
    fitness_score: float
    assignment_rationale: str
    requires_manual_assignment: bool = False


@dataclass
class LogisticsStatus:
    """Logistics verification status for a task"""
    task_id: str
    transportation_status: str  # verified, issue, missing_data
    transportation_notes: str
    equipment_status: str  # verified, issue, missing_data
    equipment_notes: str
    setup_status: str  # verified, issue, missing_data
    setup_notes: str
    overall_feasibility: str  # feasible, needs_attention, not_feasible
    issues: List[str] = field(default_factory=list)


@dataclass
class Conflict:
    """Represents a detected conflict"""
    conflict_id: str
    conflict_type: str  # timeline, resource, venue
    severity: str  # critical, high, medium, low
    affected_tasks: List[str] = field(default_factory=list)
    conflict_description: str = ""
    suggested_resolutions: List[str] = field(default_factory=list)


@dataclass
class VenueInfo:
    """Venue information for a task"""
    task_id: str
    venue_id: str
    venue_name: str
    venue_type: str
    capacity: int
    available_equipment: List[str] = field(default_factory=list)
    setup_time_required: timedelta = timedelta(hours=1)
    teardown_time_required: timedelta = timedelta(hours=1)
    access_restrictions: List[str] = field(default_factory=list)
    requires_venue_selection: bool = False
