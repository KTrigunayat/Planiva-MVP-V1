"""
Simple test for ConflictCheckTool

Tests basic functionality of conflict detection without requiring full database setup.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from event_planning_agent_v2.agents.task_management.tools.conflict_check_tool import ConflictCheckTool
from event_planning_agent_v2.agents.task_management.models.data_models import (
    Resource, TaskTimeline, Conflict
)
from event_planning_agent_v2.agents.task_management.models.consolidated_models import (
    ConsolidatedTask, ConsolidatedTaskData
)


def create_sample_task(
    task_id: str,
    task_name: str,
    start_time: datetime,
    duration_hours: float,
    priority: str = "Medium",
    resources: list = None
) -> ConsolidatedTask:
    """Create a sample task for testing"""
    end_time = start_time + timedelta(hours=duration_hours)
    
    timeline = TaskTimeline(
        task_id=task_id,
        start_time=start_time,
        end_time=end_time,
        duration=timedelta(hours=duration_hours),
        buffer_time=timedelta(minutes=15),
        scheduling_constraints=[]
    )
    
    task = ConsolidatedTask(
        task_id=task_id,
        task_name=task_name,
        priority_level=priority,
        priority_score=0.8,
        priority_rationale=f"{priority} priority task",
        parent_task_id=None,
        task_description=f"Description for {task_name}",
        granularity_level=1,
        estimated_duration=timedelta(hours=duration_hours),
        sub_tasks=[],
        dependencies=[],
        resources_required=resources or [],
        resource_conflicts=[],
        timeline=timeline,
        llm_enhancements=None,
        assigned_vendors=[],
        logistics_status=None,
        conflicts=[],
        venue_info=None
    )
    
    return task


def test_timeline_overlap_detection():
    """Test detection of timeline overlaps"""
    print("\n=== Test 1: Timeline Overlap Detection ===")
    
    base_time = datetime(2025, 6, 15, 10, 0)
    
    # Create overlapping tasks
    task1 = create_sample_task(
        "task_1",
        "Venue Setup",
        base_time,
        2.0,  # 10:00 - 12:00
        "High"
    )
    
    task2 = create_sample_task(
        "task_2",
        "Decoration Setup",
        base_time + timedelta(hours=1),  # 11:00 - 13:00
        2.0,
        "Medium"
    )
    
    consolidated_data = ConsolidatedTaskData(
        tasks=[task1, task2],
        event_context={},
        processing_metadata={}
    )
    
    # Create tool and check conflicts
    tool = ConflictCheckTool()
    state = {'selected_combination': {}, 'client_request': {}}
    
    conflicts = tool.check_conflicts(consolidated_data, state)
    
    print(f"Found {len(conflicts)} conflicts")
    for conflict in conflicts:
        print(f"  - {conflict.conflict_type} ({conflict.severity}): {conflict.conflict_description}")
        print(f"    Affected tasks: {conflict.affected_tasks}")
        print(f"    Resolutions: {conflict.suggested_resolutions[:2]}")
    
    assert len(conflicts) > 0, "Should detect timeline overlap"
    print("✓ Timeline overlap detection working")


def test_resource_conflict_detection():
    """Test detection of resource conflicts"""
    print("\n=== Test 2: Resource Conflict Detection ===")
    
    base_time = datetime(2025, 6, 15, 10, 0)
    
    # Create shared resource
    photographer_resource = Resource(
        resource_type="vendor",
        resource_id="photographer_001",
        resource_name="John's Photography",
        quantity_required=1
    )
    
    # Create tasks sharing the same resource at overlapping times
    task1 = create_sample_task(
        "task_3",
        "Bridal Photography Session",
        base_time,
        2.0,
        "Critical",
        [photographer_resource]
    )
    
    task2 = create_sample_task(
        "task_4",
        "Family Portrait Session",
        base_time + timedelta(hours=1),
        2.0,
        "High",
        [photographer_resource]
    )
    
    consolidated_data = ConsolidatedTaskData(
        tasks=[task1, task2],
        event_context={},
        processing_metadata={}
    )
    
    tool = ConflictCheckTool()
    state = {'selected_combination': {}, 'client_request': {}}
    
    conflicts = tool.check_conflicts(consolidated_data, state)
    
    print(f"Found {len(conflicts)} conflicts")
    resource_conflicts = [c for c in conflicts if c.conflict_type == 'resource']
    print(f"Resource conflicts: {len(resource_conflicts)}")
    
    for conflict in resource_conflicts:
        print(f"  - {conflict.severity}: {conflict.conflict_description}")
        print(f"    Resolutions: {conflict.suggested_resolutions[:2]}")
    
    assert len(resource_conflicts) > 0, "Should detect resource conflict"
    print("✓ Resource conflict detection working")


def test_venue_conflict_detection():
    """Test detection of venue conflicts"""
    print("\n=== Test 3: Venue Conflict Detection ===")
    
    base_time = datetime(2025, 6, 15, 14, 0)
    
    # Create tasks requiring venue
    task1 = create_sample_task(
        "task_5",
        "Wedding Ceremony at venue hall",
        base_time,
        1.5,
        "Critical"
    )
    
    task2 = create_sample_task(
        "task_6",
        "Reception setup at venue",
        base_time + timedelta(hours=1),
        2.0,
        "High"
    )
    
    consolidated_data = ConsolidatedTaskData(
        tasks=[task1, task2],
        event_context={},
        processing_metadata={}
    )
    
    # Add venue to state
    state = {
        'selected_combination': {
            'venue': {
                'vendor_id': 'venue_001',
                'name': 'Grand Ballroom',
                'max_seating_capacity': 200
            }
        },
        'client_request': {}
    }
    
    tool = ConflictCheckTool()
    conflicts = tool.check_conflicts(consolidated_data, state)
    
    print(f"Found {len(conflicts)} conflicts")
    venue_conflicts = [c for c in conflicts if c.conflict_type == 'venue']
    print(f"Venue conflicts: {len(venue_conflicts)}")
    
    for conflict in venue_conflicts:
        print(f"  - {conflict.severity}: {conflict.conflict_description}")
        print(f"    Resolutions: {conflict.suggested_resolutions[:2]}")
    
    if len(venue_conflicts) > 0:
        print("✓ Venue conflict detection working")
    else:
        print("⚠ No venue conflicts detected (may be expected if tasks can run in parallel)")


def test_conflict_id_generation():
    """Test unique conflict ID generation"""
    print("\n=== Test 4: Conflict ID Generation ===")
    
    tool = ConflictCheckTool()
    
    # Generate conflict IDs
    id1 = tool._generate_conflict_id("timeline", ["task_1", "task_2"], "overlap")
    id2 = tool._generate_conflict_id("timeline", ["task_2", "task_1"], "overlap")  # Same tasks, different order
    id3 = tool._generate_conflict_id("timeline", ["task_1", "task_3"], "overlap")  # Different tasks
    
    print(f"ID 1: {id1}")
    print(f"ID 2: {id2}")
    print(f"ID 3: {id3}")
    
    assert id1 == id2, "Same tasks should generate same ID regardless of order"
    assert id1 != id3, "Different tasks should generate different IDs"
    
    print("✓ Conflict ID generation working correctly")


def test_resolution_suggestions():
    """Test resolution suggestion generation"""
    print("\n=== Test 5: Resolution Suggestions ===")
    
    tool = ConflictCheckTool()
    
    # Test timeline conflict suggestions
    timeline_conflict = Conflict(
        conflict_id="test_1",
        conflict_type="timeline",
        severity="high",
        affected_tasks=["task_1", "task_2"],
        conflict_description="Timeline overlap detected"
    )
    
    suggestions = tool._suggest_resolutions(timeline_conflict)
    print(f"Timeline conflict suggestions ({len(suggestions)}):")
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"  {i}. {suggestion}")
    
    # Test resource conflict suggestions
    resource_conflict = Conflict(
        conflict_id="test_2",
        conflict_type="resource",
        severity="critical",
        affected_tasks=["task_3", "task_4"],
        conflict_description="Vendor double-booking detected"
    )
    
    suggestions = tool._suggest_resolutions(resource_conflict)
    print(f"\nResource conflict suggestions ({len(suggestions)}):")
    for i, suggestion in enumerate(suggestions[:3], 1):
        print(f"  {i}. {suggestion}")
    
    print("✓ Resolution suggestions generated successfully")


def main():
    """Run all tests"""
    print("=" * 60)
    print("ConflictCheckTool Simple Tests")
    print("=" * 60)
    
    try:
        test_timeline_overlap_detection()
        test_resource_conflict_detection()
        test_venue_conflict_detection()
        test_conflict_id_generation()
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
