"""
Test script for DataConsolidator

Tests the data consolidation logic with sample data from all three sub-agents.
"""

import sys
from pathlib import Path
from datetime import timedelta

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent.parent.parent.parent))

from event_planning_agent_v2.agents.task_management.core.data_consolidator import DataConsolidator
from event_planning_agent_v2.agents.task_management.models.task_models import (
    PrioritizedTask,
    GranularTask,
    TaskWithDependencies
)
from event_planning_agent_v2.agents.task_management.models.data_models import Resource


def test_basic_consolidation():
    """Test basic consolidation with complete data from all sub-agents"""
    print("\n=== Test 1: Basic Consolidation ===")
    
    # Create sample data from Prioritization Agent
    prioritized_tasks = [
        PrioritizedTask(
            task_id="task_001",
            task_name="Book Venue",
            priority_level="Critical",
            priority_score=0.95,
            priority_rationale="Must be done first to secure location"
        ),
        PrioritizedTask(
            task_id="task_002",
            task_name="Hire Caterer",
            priority_level="High",
            priority_score=0.75,
            priority_rationale="Important for guest satisfaction"
        )
    ]
    
    # Create sample data from Granularity Agent
    granular_tasks = [
        GranularTask(
            task_id="task_001",
            parent_task_id=None,
            task_name="Book Venue",
            task_description="Research and book appropriate venue for the event",
            granularity_level=0,
            estimated_duration=timedelta(hours=4),
            sub_tasks=["task_001_1", "task_001_2"]
        ),
        GranularTask(
            task_id="task_002",
            parent_task_id=None,
            task_name="Hire Caterer",
            task_description="Select and contract catering service",
            granularity_level=0,
            estimated_duration=timedelta(hours=3),
            sub_tasks=[]
        )
    ]
    
    # Create sample data from Resource & Dependency Agent
    dependency_tasks = [
        TaskWithDependencies(
            task_id="task_001",
            task_name="Book Venue",
            dependencies=[],
            resources_required=[
                Resource(
                    resource_type="venue",
                    resource_id="venue_001",
                    resource_name="Grand Ballroom",
                    quantity_required=1
                )
            ],
            resource_conflicts=[]
        ),
        TaskWithDependencies(
            task_id="task_002",
            task_name="Hire Caterer",
            dependencies=["task_001"],  # Depends on venue being booked
            resources_required=[
                Resource(
                    resource_type="vendor",
                    resource_id="caterer_001",
                    resource_name="Gourmet Catering Co",
                    quantity_required=1
                )
            ],
            resource_conflicts=[]
        )
    ]
    
    # Create consolidator and consolidate data
    consolidator = DataConsolidator()
    consolidated_data = consolidator.consolidate_sub_agent_data(
        prioritized_tasks=prioritized_tasks,
        granular_tasks=granular_tasks,
        dependency_tasks=dependency_tasks,
        event_context={"event_type": "wedding", "guest_count": 150}
    )
    
    # Verify results
    print(f"✓ Consolidated {len(consolidated_data.tasks)} tasks")
    print(f"✓ Errors: {len(consolidated_data.processing_metadata['errors'])}")
    print(f"✓ Warnings: {len(consolidated_data.processing_metadata['warnings'])}")
    
    # Check first task
    task1 = consolidated_data.tasks[0]
    print(f"\nTask 1: {task1.task_name}")
    print(f"  Priority: {task1.priority_level} (score: {task1.priority_score})")
    print(f"  Duration: {task1.estimated_duration}")
    print(f"  Dependencies: {task1.dependencies}")
    print(f"  Resources: {len(task1.resources_required)}")
    
    assert len(consolidated_data.tasks) == 2, "Should have 2 consolidated tasks"
    assert task1.task_id in ["task_001", "task_002"], "Task ID should match"
    print("\n✓ Test 1 PASSED")


def test_missing_data_handling():
    """Test consolidation with missing data from some sub-agents"""
    print("\n=== Test 2: Missing Data Handling ===")
    
    # Only provide prioritization data, missing granularity and dependency data
    prioritized_tasks = [
        PrioritizedTask(
            task_id="task_003",
            task_name="Send Invitations",
            priority_level="Medium",
            priority_score=0.60,
            priority_rationale="Important but not urgent"
        )
    ]
    
    # Empty lists for other sub-agents
    granular_tasks = []
    dependency_tasks = []
    
    # Create consolidator and consolidate data
    consolidator = DataConsolidator()
    consolidated_data = consolidator.consolidate_sub_agent_data(
        prioritized_tasks=prioritized_tasks,
        granular_tasks=granular_tasks,
        dependency_tasks=dependency_tasks
    )
    
    # Verify results
    print(f"✓ Consolidated {len(consolidated_data.tasks)} tasks")
    print(f"✓ Warnings: {len(consolidated_data.processing_metadata['warnings'])}")
    
    # Check that defaults were used
    task = consolidated_data.tasks[0]
    print(f"\nTask: {task.task_name}")
    print(f"  Description: {task.task_description}")
    print(f"  Duration: {task.estimated_duration}")
    print(f"  Dependencies: {task.dependencies}")
    
    assert len(consolidated_data.tasks) == 1, "Should have 1 consolidated task"
    assert task.task_description != "", "Should have default description"
    assert task.estimated_duration.total_seconds() > 0, "Should have default duration"
    assert len(consolidated_data.processing_metadata['warnings']) >= 2, "Should have warnings for missing data"
    print("\n✓ Test 2 PASSED")


def test_partial_data():
    """Test consolidation with partial data from different sub-agents"""
    print("\n=== Test 3: Partial Data ===")
    
    # Task appears in prioritization and granularity, but not dependency
    prioritized_tasks = [
        PrioritizedTask(
            task_id="task_004",
            task_name="Setup Decorations",
            priority_level="Low",
            priority_score=0.30,
            priority_rationale="Can be done closer to event"
        )
    ]
    
    granular_tasks = [
        GranularTask(
            task_id="task_004",
            parent_task_id=None,
            task_name="Setup Decorations",
            task_description="Arrange flowers and decorations at venue",
            granularity_level=0,
            estimated_duration=timedelta(hours=2),
            sub_tasks=[]
        )
    ]
    
    # Missing from dependency agent
    dependency_tasks = []
    
    # Create consolidator and consolidate data
    consolidator = DataConsolidator()
    consolidated_data = consolidator.consolidate_sub_agent_data(
        prioritized_tasks=prioritized_tasks,
        granular_tasks=granular_tasks,
        dependency_tasks=dependency_tasks
    )
    
    # Verify results
    print(f"✓ Consolidated {len(consolidated_data.tasks)} tasks")
    print(f"✓ Warnings: {len(consolidated_data.processing_metadata['warnings'])}")
    
    task = consolidated_data.tasks[0]
    print(f"\nTask: {task.task_name}")
    print(f"  Has priority data: ✓")
    print(f"  Has granularity data: ✓")
    print(f"  Has dependency data: Using defaults")
    
    assert len(consolidated_data.tasks) == 1, "Should have 1 consolidated task"
    assert task.priority_level == "Low", "Should have priority data"
    assert task.task_description == "Arrange flowers and decorations at venue", "Should have granularity data"
    assert task.dependencies == [], "Should have default empty dependencies"
    print("\n✓ Test 3 PASSED")


def test_invalid_references():
    """Test validation of invalid dependency and sub-task references"""
    print("\n=== Test 4: Invalid References ===")
    
    prioritized_tasks = [
        PrioritizedTask(
            task_id="task_005",
            task_name="Final Walkthrough",
            priority_level="High",
            priority_score=0.80,
            priority_rationale="Ensure everything is ready"
        )
    ]
    
    granular_tasks = [
        GranularTask(
            task_id="task_005",
            parent_task_id="task_999",  # Invalid parent reference
            task_name="Final Walkthrough",
            task_description="Check all arrangements before event",
            granularity_level=1,
            estimated_duration=timedelta(hours=1),
            sub_tasks=["task_888"]  # Invalid sub-task reference
        )
    ]
    
    dependency_tasks = [
        TaskWithDependencies(
            task_id="task_005",
            task_name="Final Walkthrough",
            dependencies=["task_777"],  # Invalid dependency reference
            resources_required=[],
            resource_conflicts=[]
        )
    ]
    
    # Create consolidator and consolidate data
    consolidator = DataConsolidator()
    consolidated_data = consolidator.consolidate_sub_agent_data(
        prioritized_tasks=prioritized_tasks,
        granular_tasks=granular_tasks,
        dependency_tasks=dependency_tasks
    )
    
    # Verify results
    print(f"✓ Consolidated {len(consolidated_data.tasks)} tasks")
    print(f"✓ Warnings: {len(consolidated_data.processing_metadata['warnings'])}")
    
    # Should have warnings for invalid references
    warnings = consolidated_data.processing_metadata['warnings']
    validation_warnings = [w for w in warnings if 'validation' in w]
    print(f"✓ Validation warnings: {len(validation_warnings)}")
    
    assert len(validation_warnings) >= 3, "Should have warnings for invalid references"
    print("\n✓ Test 4 PASSED")


if __name__ == "__main__":
    print("Testing DataConsolidator")
    print("=" * 50)
    
    try:
        test_basic_consolidation()
        test_missing_data_handling()
        test_partial_data()
        test_invalid_references()
        
        print("\n" + "=" * 50)
        print("✓ ALL TESTS PASSED")
        print("=" * 50)
    except AssertionError as e:
        print(f"\n✗ TEST FAILED: {e}")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ ERROR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
