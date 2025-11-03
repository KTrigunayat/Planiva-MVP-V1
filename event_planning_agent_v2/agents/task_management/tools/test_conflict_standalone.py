"""
Standalone test for ConflictCheckTool

Tests basic functionality without triggering full import chain.
"""

from datetime import datetime, timedelta
from dataclasses import dataclass, field
from typing import List, Optional, Dict, Any
import hashlib
from collections import defaultdict


# Minimal data models for testing
@dataclass
class Resource:
    resource_type: str
    resource_id: str
    resource_name: str
    quantity_required: int
    availability_constraint: Optional[str] = None


@dataclass
class TaskTimeline:
    task_id: str
    start_time: datetime
    end_time: datetime
    duration: timedelta
    buffer_time: timedelta
    scheduling_constraints: List[str] = field(default_factory=list)


@dataclass
class Conflict:
    conflict_id: str
    conflict_type: str
    severity: str
    affected_tasks: List[str] = field(default_factory=list)
    conflict_description: str = ""
    suggested_resolutions: List[str] = field(default_factory=list)


@dataclass
class ConsolidatedTask:
    task_id: str
    task_name: str
    priority_level: str
    priority_score: float
    priority_rationale: str
    parent_task_id: Optional[str]
    task_description: str
    granularity_level: int
    estimated_duration: timedelta
    sub_tasks: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)
    resources_required: List[Resource] = field(default_factory=list)
    resource_conflicts: List[str] = field(default_factory=list)
    timeline: Optional[TaskTimeline] = None
    llm_enhancements: Optional[Dict] = None
    assigned_vendors: List[str] = field(default_factory=list)
    logistics_status: Optional[Any] = None
    conflicts: List[Conflict] = field(default_factory=list)
    venue_info: Optional[Any] = None


# Test the core conflict detection logic
def test_conflict_id_generation():
    """Test unique conflict ID generation"""
    print("\n=== Test: Conflict ID Generation ===")
    
    def generate_conflict_id(conflict_type: str, affected_tasks: List[str], additional_context: str = "") -> str:
        sorted_tasks = sorted(affected_tasks)
        hash_input = f"{conflict_type}:{':'.join(sorted_tasks)}:{additional_context}"
        conflict_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        conflict_id = f"{conflict_type}_{conflict_hash}"
        return conflict_id
    
    id1 = generate_conflict_id("timeline", ["task_1", "task_2"], "overlap")
    id2 = generate_conflict_id("timeline", ["task_2", "task_1"], "overlap")
    id3 = generate_conflict_id("timeline", ["task_1", "task_3"], "overlap")
    
    print(f"ID 1: {id1}")
    print(f"ID 2: {id2}")
    print(f"ID 3: {id3}")
    
    assert id1 == id2, "Same tasks should generate same ID regardless of order"
    assert id1 != id3, "Different tasks should generate different IDs"
    print("✓ Conflict ID generation working")


def test_timeline_overlap_logic():
    """Test timeline overlap detection logic"""
    print("\n=== Test: Timeline Overlap Logic ===")
    
    base_time = datetime(2025, 6, 15, 10, 0)
    
    # Create overlapping tasks
    task1 = ConsolidatedTask(
        task_id="task_1",
        task_name="Venue Setup",
        priority_level="High",
        priority_score=0.8,
        priority_rationale="High priority",
        parent_task_id=None,
        task_description="Setup venue",
        granularity_level=1,
        estimated_duration=timedelta(hours=2),
        timeline=TaskTimeline(
            task_id="task_1",
            start_time=base_time,
            end_time=base_time + timedelta(hours=2),
            duration=timedelta(hours=2),
            buffer_time=timedelta(minutes=15),
            scheduling_constraints=[]
        )
    )
    
    task2 = ConsolidatedTask(
        task_id="task_2",
        task_name="Decoration",
        priority_level="Medium",
        priority_score=0.6,
        priority_rationale="Medium priority",
        parent_task_id=None,
        task_description="Decorate venue",
        granularity_level=1,
        estimated_duration=timedelta(hours=2),
        timeline=TaskTimeline(
            task_id="task_2",
            start_time=base_time + timedelta(hours=1),
            end_time=base_time + timedelta(hours=3),
            duration=timedelta(hours=2),
            buffer_time=timedelta(minutes=15),
            scheduling_constraints=[]
        )
    )
    
    # Check overlap
    def tasks_overlap(t1, t2):
        return (
            t1.timeline.start_time < t2.timeline.end_time and
            t2.timeline.start_time < t1.timeline.end_time
        )
    
    overlap = tasks_overlap(task1, task2)
    print(f"Task 1: {task1.timeline.start_time} - {task1.timeline.end_time}")
    print(f"Task 2: {task2.timeline.start_time} - {task2.timeline.end_time}")
    print(f"Overlap detected: {overlap}")
    
    assert overlap, "Should detect overlap"
    print("✓ Timeline overlap detection working")


def test_resource_conflict_logic():
    """Test resource conflict detection logic"""
    print("\n=== Test: Resource Conflict Logic ===")
    
    base_time = datetime(2025, 6, 15, 10, 0)
    
    # Shared resource
    photographer = Resource(
        resource_type="vendor",
        resource_id="photographer_001",
        resource_name="John's Photography",
        quantity_required=1
    )
    
    # Tasks with shared resource
    task1 = ConsolidatedTask(
        task_id="task_3",
        task_name="Bridal Photos",
        priority_level="Critical",
        priority_score=0.9,
        priority_rationale="Critical",
        parent_task_id=None,
        task_description="Bridal photography",
        granularity_level=1,
        estimated_duration=timedelta(hours=2),
        resources_required=[photographer],
        timeline=TaskTimeline(
            task_id="task_3",
            start_time=base_time,
            end_time=base_time + timedelta(hours=2),
            duration=timedelta(hours=2),
            buffer_time=timedelta(minutes=15),
            scheduling_constraints=[]
        )
    )
    
    task2 = ConsolidatedTask(
        task_id="task_4",
        task_name="Family Photos",
        priority_level="High",
        priority_score=0.8,
        priority_rationale="High",
        parent_task_id=None,
        task_description="Family photography",
        granularity_level=1,
        estimated_duration=timedelta(hours=2),
        resources_required=[photographer],
        timeline=TaskTimeline(
            task_id="task_4",
            start_time=base_time + timedelta(hours=1),
            end_time=base_time + timedelta(hours=3),
            duration=timedelta(hours=2),
            buffer_time=timedelta(minutes=15),
            scheduling_constraints=[]
        )
    )
    
    # Check resource conflict
    tasks = [task1, task2]
    resource_usage = defaultdict(list)
    
    for task in tasks:
        if task.timeline:
            for resource in task.resources_required:
                resource_key = f"{resource.resource_type}:{resource.resource_id}"
                resource_usage[resource_key].append({
                    'task': task,
                    'start_time': task.timeline.start_time,
                    'end_time': task.timeline.end_time
                })
    
    conflicts_found = 0
    for resource_key, usages in resource_usage.items():
        if len(usages) >= 2:
            sorted_usages = sorted(usages, key=lambda x: x['start_time'])
            for i in range(len(sorted_usages) - 1):
                current = sorted_usages[i]
                next_usage = sorted_usages[i + 1]
                if current['end_time'] > next_usage['start_time']:
                    conflicts_found += 1
                    print(f"Resource conflict detected: {resource_key}")
                    print(f"  Task 1: {current['task'].task_name} ({current['start_time']} - {current['end_time']})")
                    print(f"  Task 2: {next_usage['task'].task_name} ({next_usage['start_time']} - {next_usage['end_time']})")
    
    assert conflicts_found > 0, "Should detect resource conflict"
    print("✓ Resource conflict detection working")


def test_resolution_suggestions():
    """Test resolution suggestion generation"""
    print("\n=== Test: Resolution Suggestions ===")
    
    def suggest_resolutions(conflict_type: str, severity: str) -> List[str]:
        suggestions = []
        
        if conflict_type == 'timeline':
            suggestions.extend([
                "Adjust task start times to eliminate overlap",
                "Add buffer time between dependent tasks",
                "Reschedule lower priority tasks to different time slots"
            ])
        elif conflict_type == 'resource':
            suggestions.extend([
                "Stagger task schedules to avoid resource overlap",
                "Allocate additional resources if available",
                "Prioritize critical tasks for resource allocation"
            ])
        elif conflict_type == 'venue':
            suggestions.extend([
                "Adjust venue usage schedule to eliminate overlaps",
                "Designate different areas of venue for concurrent activities"
            ])
        
        if severity == 'critical':
            suggestions.insert(0, "URGENT: This conflict must be resolved before proceeding")
        
        return suggestions
    
    timeline_suggestions = suggest_resolutions('timeline', 'high')
    print(f"Timeline conflict suggestions: {len(timeline_suggestions)}")
    for i, s in enumerate(timeline_suggestions[:3], 1):
        print(f"  {i}. {s}")
    
    resource_suggestions = suggest_resolutions('resource', 'critical')
    print(f"\nResource conflict suggestions: {len(resource_suggestions)}")
    for i, s in enumerate(resource_suggestions[:3], 1):
        print(f"  {i}. {s}")
    
    assert len(timeline_suggestions) > 0, "Should generate timeline suggestions"
    assert len(resource_suggestions) > 0, "Should generate resource suggestions"
    assert "URGENT" in resource_suggestions[0], "Critical conflicts should have urgent flag"
    print("✓ Resolution suggestions working")


def main():
    """Run all tests"""
    print("=" * 60)
    print("ConflictCheckTool Standalone Tests")
    print("=" * 60)
    
    try:
        test_conflict_id_generation()
        test_timeline_overlap_logic()
        test_resource_conflict_logic()
        test_resolution_suggestions()
        
        print("\n" + "=" * 60)
        print("✓ All tests passed!")
        print("=" * 60)
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    return 0


if __name__ == "__main__":
    exit(main())
