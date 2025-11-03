"""
Simple test for Timeline Calculation Tool

This test verifies the basic functionality of the TimelineCalculationTool.
"""

import sys
from pathlib import Path
from datetime import datetime, timedelta

# Add parent directory to path
parent_dir = Path(__file__).parent.parent.parent.parent
sys.path.insert(0, str(parent_dir))

# Now import from the agents module
from agents.task_management.tools.timeline_calculation_tool import TimelineCalculationTool
from agents.task_management.models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
from agents.task_management.models.data_models import Resource


def test_timeline_calculation_basic():
    """Test basic timeline calculation with simple dependencies"""
    
    # Create test tasks
    task1 = ConsolidatedTask(
        task_id="task_1",
        task_name="Setup Venue",
        priority_level="Critical",
        priority_score=0.95,
        priority_rationale="Must be done first",
        parent_task_id=None,
        task_description="Set up the venue for the event",
        granularity_level=0,
        estimated_duration=timedelta(hours=2),
        sub_tasks=[],
        dependencies=[],  # No dependencies
        resources_required=[],
        resource_conflicts=[]
    )
    
    task2 = ConsolidatedTask(
        task_id="task_2",
        task_name="Catering Setup",
        priority_level="High",
        priority_score=0.85,
        priority_rationale="Depends on venue setup",
        parent_task_id=None,
        task_description="Set up catering equipment and food stations",
        granularity_level=0,
        estimated_duration=timedelta(hours=1.5),
        sub_tasks=[],
        dependencies=["task_1"],  # Depends on task_1
        resources_required=[],
        resource_conflicts=[]
    )
    
    task3 = ConsolidatedTask(
        task_id="task_3",
        task_name="Photography Setup",
        priority_level="Medium",
        priority_score=0.70,
        priority_rationale="Can be done in parallel",
        parent_task_id=None,
        task_description="Set up photography equipment",
        granularity_level=0,
        estimated_duration=timedelta(hours=1),
        sub_tasks=[],
        dependencies=["task_1"],  # Also depends on task_1
        resources_required=[],
        resource_conflicts=[]
    )
    
    # Create consolidated data
    consolidated_data = ConsolidatedTaskData(
        tasks=[task1, task2, task3],
        event_context={},
        processing_metadata={}
    )
    
    # Create mock state
    state = {
        'client_request': {
            'eventDate': '2025-10-20'
        },
        'timeline_data': {
            'event_date': '2025-10-20',
            'timeline': [
                {
                    'name': 'Event Start',
                    'start_time': '10:00',
                    'duration': 0.5
                }
            ]
        }
    }
    
    # Initialize tool
    tool = TimelineCalculationTool()
    
    # Calculate timelines
    timelines = tool.calculate_timelines(consolidated_data, state)
    
    # Verify results
    assert len(timelines) == 3, f"Expected 3 timelines, got {len(timelines)}"
    
    # Verify task_1 starts first
    task1_timeline = next(t for t in timelines if t.task_id == "task_1")
    print(f"Task 1: {task1_timeline.start_time} - {task1_timeline.end_time}")
    
    # Verify task_2 starts after task_1 ends
    task2_timeline = next(t for t in timelines if t.task_id == "task_2")
    print(f"Task 2: {task2_timeline.start_time} - {task2_timeline.end_time}")
    assert task2_timeline.start_time >= task1_timeline.end_time, \
        "Task 2 should start after Task 1 ends"
    
    # Verify task_3 starts after task_1 ends
    task3_timeline = next(t for t in timelines if t.task_id == "task_3")
    print(f"Task 3: {task3_timeline.start_time} - {task3_timeline.end_time}")
    assert task3_timeline.start_time >= task1_timeline.end_time, \
        "Task 3 should start after Task 1 ends"
    
    print("\n✓ Basic timeline calculation test passed!")


def test_topological_sort():
    """Test topological sort with complex dependencies"""
    
    # Create tasks with complex dependencies
    tasks = [
        ConsolidatedTask(
            task_id="A",
            task_name="Task A",
            priority_level="High",
            priority_score=0.9,
            priority_rationale="First task",
            parent_task_id=None,
            task_description="Task A",
            granularity_level=0,
            estimated_duration=timedelta(hours=1),
            dependencies=[],  # No dependencies
        ),
        ConsolidatedTask(
            task_id="B",
            task_name="Task B",
            priority_level="High",
            priority_score=0.85,
            priority_rationale="Depends on A",
            parent_task_id=None,
            task_description="Task B",
            granularity_level=0,
            estimated_duration=timedelta(hours=1),
            dependencies=["A"],
        ),
        ConsolidatedTask(
            task_id="C",
            task_name="Task C",
            priority_level="Medium",
            priority_score=0.75,
            priority_rationale="Depends on A",
            parent_task_id=None,
            task_description="Task C",
            granularity_level=0,
            estimated_duration=timedelta(hours=1),
            dependencies=["A"],
        ),
        ConsolidatedTask(
            task_id="D",
            task_name="Task D",
            priority_level="Medium",
            priority_score=0.70,
            priority_rationale="Depends on B and C",
            parent_task_id=None,
            task_description="Task D",
            granularity_level=0,
            estimated_duration=timedelta(hours=1),
            dependencies=["B", "C"],
        ),
    ]
    
    # Initialize tool
    tool = TimelineCalculationTool()
    
    # Perform topological sort
    sorted_tasks = tool._topological_sort(tasks)
    
    # Verify order
    task_ids = [t.task_id for t in sorted_tasks]
    print(f"Sorted order: {task_ids}")
    
    # A should come before B, C, and D
    assert task_ids.index("A") < task_ids.index("B"), "A should come before B"
    assert task_ids.index("A") < task_ids.index("C"), "A should come before C"
    assert task_ids.index("A") < task_ids.index("D"), "A should come before D"
    
    # B and C should come before D
    assert task_ids.index("B") < task_ids.index("D"), "B should come before D"
    assert task_ids.index("C") < task_ids.index("D"), "C should come before D"
    
    print("✓ Topological sort test passed!")


def test_circular_dependency_handling():
    """Test handling of circular dependencies"""
    
    # Create tasks with circular dependency
    tasks = [
        ConsolidatedTask(
            task_id="X",
            task_name="Task X",
            priority_level="High",
            priority_score=0.9,
            priority_rationale="Task X",
            parent_task_id=None,
            task_description="Task X",
            granularity_level=0,
            estimated_duration=timedelta(hours=1),
            dependencies=["Y"],  # Depends on Y
        ),
        ConsolidatedTask(
            task_id="Y",
            task_name="Task Y",
            priority_level="High",
            priority_score=0.85,
            priority_rationale="Task Y",
            parent_task_id=None,
            task_description="Task Y",
            granularity_level=0,
            estimated_duration=timedelta(hours=1),
            dependencies=["X"],  # Depends on X (circular!)
        ),
    ]
    
    # Initialize tool
    tool = TimelineCalculationTool()
    
    # Perform topological sort (should handle circular dependency gracefully)
    sorted_tasks = tool._topological_sort(tasks)
    
    # Should still return all tasks
    assert len(sorted_tasks) == 2, "Should return all tasks despite circular dependency"
    
    print("✓ Circular dependency handling test passed!")


if __name__ == "__main__":
    print("Running Timeline Calculation Tool tests...\n")
    
    print("Test 1: Basic timeline calculation")
    test_timeline_calculation_basic()
    
    print("\nTest 2: Topological sort")
    test_topological_sort()
    
    print("\nTest 3: Circular dependency handling")
    test_circular_dependency_handling()
    
    print("\n" + "="*50)
    print("All tests passed! ✓")
    print("="*50)
