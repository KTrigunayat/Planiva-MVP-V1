"""
Simple test for Venue Lookup Tool

Tests basic functionality without requiring full database setup.
"""

import sys
from pathlib import Path
from datetime import timedelta
from typing import Dict, Any

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from event_planning_agent_v2.agents.task_management.tools.venue_lookup_tool import VenueLookupTool
from event_planning_agent_v2.agents.task_management.models.data_models import Resource
from event_planning_agent_v2.agents.task_management.models.consolidated_models import (
    ConsolidatedTask, ConsolidatedTaskData
)


def create_mock_state_with_venue() -> Dict[str, Any]:
    """Create mock EventPlanningState with venue in selected_combination"""
    return {
        'selected_combination': {
            'venue': {
                'vendor_id': 'test-venue-123',
                'id': 'test-venue-123',
                'name': 'Grand Ballroom',
                'area_type': 'Banquet Hall',
                'location_city': 'Mumbai'
            },
            'fitness_score': 0.85
        },
        'client_request': {
            'date': '2025-12-15',
            'guest_count': 200
        }
    }


def create_mock_state_without_venue() -> Dict[str, Any]:
    """Create mock EventPlanningState without venue"""
    return {
        'selected_combination': {
            'caterer': {
                'vendor_id': 'test-caterer-123',
                'name': 'Delicious Catering'
            }
        },
        'client_request': {
            'date': '2025-12-15',
            'guest_count': 200
        }
    }


def create_mock_tasks() -> ConsolidatedTaskData:
    """Create mock consolidated task data"""
    tasks = [
        ConsolidatedTask(
            task_id='task-1',
            task_name='Venue Setup',
            task_description='Setup venue with seating arrangements and decorations',
            priority_level='High',
            priority_score=0.8,
            priority_rationale='Critical for event success',
            parent_task_id=None,
            granularity_level=0,
            estimated_duration=timedelta(hours=4),
            sub_tasks=[],
            dependencies=[],
            resources_required=[
                Resource(
                    resource_type='venue',
                    resource_id='venue-1',
                    resource_name='Main Hall',
                    quantity_required=1
                ),
                Resource(
                    resource_type='equipment',
                    resource_id='eq-1',
                    resource_name='Chairs and Tables',
                    quantity_required=200
                )
            ],
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id='task-2',
            task_name='Catering Coordination',
            task_description='Coordinate with caterer for menu and service',
            priority_level='Medium',
            priority_score=0.6,
            priority_rationale='Important but not critical',
            parent_task_id=None,
            granularity_level=0,
            estimated_duration=timedelta(hours=2),
            sub_tasks=[],
            dependencies=[],
            resources_required=[
                Resource(
                    resource_type='vendor',
                    resource_id='caterer-1',
                    resource_name='Caterer',
                    quantity_required=1
                )
            ],
            resource_conflicts=[]
        ),
        ConsolidatedTask(
            task_id='task-3',
            task_name='Floor Plan Design',
            task_description='Design floor plan for optimal space utilization',
            priority_level='High',
            priority_score=0.75,
            priority_rationale='Needed before setup',
            parent_task_id=None,
            granularity_level=0,
            estimated_duration=timedelta(hours=3),
            sub_tasks=[],
            dependencies=[],
            resources_required=[],
            resource_conflicts=[]
        )
    ]
    
    return ConsolidatedTaskData(
        tasks=tasks,
        event_context={'guest_count': 200, 'event_type': 'wedding'},
        processing_metadata={'timestamp': '2025-10-19T12:00:00'}
    )


def test_venue_extraction():
    """Test extracting venue from selected_combination"""
    print("\n=== Test 1: Venue Extraction ===")
    
    tool = VenueLookupTool(db_connection=None, use_mcp=False)
    state = create_mock_state_with_venue()
    
    venue_data = tool._get_venue_from_combination(state)
    
    if venue_data:
        print(f"✓ Venue extracted successfully")
        print(f"  Venue ID: {venue_data['vendor_id']}")
        print(f"  Venue Name: {venue_data['name']}")
    else:
        print("✗ Failed to extract venue")
    
    return venue_data is not None


def test_venue_extraction_missing():
    """Test handling missing venue"""
    print("\n=== Test 2: Missing Venue Handling ===")
    
    tool = VenueLookupTool(db_connection=None, use_mcp=False)
    state = create_mock_state_without_venue()
    
    venue_data = tool._get_venue_from_combination(state)
    
    if venue_data is None:
        print("✓ Correctly handled missing venue")
    else:
        print("✗ Should have returned None for missing venue")
    
    return venue_data is None


def test_task_requires_venue():
    """Test identifying tasks that require venue information"""
    print("\n=== Test 3: Task Venue Requirement Detection ===")
    
    tool = VenueLookupTool(db_connection=None, use_mcp=False)
    tasks = create_mock_tasks().tasks
    
    results = []
    for task in tasks:
        requires_venue = tool._task_requires_venue(task)
        results.append((task.task_name, requires_venue))
        print(f"  {task.task_name}: {'Requires venue' if requires_venue else 'No venue needed'}")
    
    # Task 1 (Venue Setup) should require venue
    # Task 2 (Catering) should not require venue
    # Task 3 (Floor Plan) should require venue (has 'space' keyword)
    expected = [True, False, True]
    actual = [r[1] for r in results]
    
    if actual == expected:
        print("✓ Venue requirement detection working correctly")
        return True
    else:
        print(f"✗ Expected {expected}, got {actual}")
        return False


def test_flag_venue_selection():
    """Test flagging tasks for venue selection"""
    print("\n=== Test 4: Venue Selection Flagging ===")
    
    tool = VenueLookupTool(db_connection=None, use_mcp=False)
    tasks = create_mock_tasks().tasks
    
    venue_info = tool._flag_venue_selection_needed(tasks[0])
    
    if venue_info.requires_venue_selection:
        print("✓ Task correctly flagged for venue selection")
        print(f"  Task ID: {venue_info.task_id}")
        print(f"  Venue Name: {venue_info.venue_name}")
        print(f"  Requires Selection: {venue_info.requires_venue_selection}")
        return True
    else:
        print("✗ Task not flagged for venue selection")
        return False


def test_missing_venue_info_creation():
    """Test creating venue info when venue is missing"""
    print("\n=== Test 5: Missing Venue Info Creation ===")
    
    tool = VenueLookupTool(db_connection=None, use_mcp=False)
    tasks = create_mock_tasks().tasks
    
    venue_infos = tool._create_missing_venue_info(tasks)
    
    # Should create venue info for tasks 1 and 3 (which require venue)
    if len(venue_infos) == 2:
        print(f"✓ Created venue info for {len(venue_infos)} tasks requiring venue")
        for info in venue_infos:
            print(f"  Task {info.task_id}: {info.venue_name}")
            if not info.requires_venue_selection:
                print("  ✗ Should be flagged for venue selection")
                return False
        return True
    else:
        print(f"✗ Expected 2 venue infos, got {len(venue_infos)}")
        return False


def test_mcp_availability_check():
    """Test MCP availability checking"""
    print("\n=== Test 6: MCP Availability Check ===")
    
    # Test with MCP disabled
    tool_no_mcp = VenueLookupTool(db_connection=None, use_mcp=False)
    if not tool_no_mcp.mcp_available:
        print("✓ MCP correctly disabled when use_mcp=False")
    else:
        print("✗ MCP should be disabled")
        return False
    
    # Test with MCP enabled (will likely fail to connect, which is expected)
    tool_with_mcp = VenueLookupTool(db_connection=None, use_mcp=True)
    print(f"  MCP availability: {tool_with_mcp.mcp_available}")
    print("✓ MCP availability check completed")
    
    return True


def run_all_tests():
    """Run all tests"""
    print("=" * 60)
    print("VENUE LOOKUP TOOL - SIMPLE TESTS")
    print("=" * 60)
    
    tests = [
        ("Venue Extraction", test_venue_extraction),
        ("Missing Venue Handling", test_venue_extraction_missing),
        ("Task Venue Requirement Detection", test_task_requires_venue),
        ("Venue Selection Flagging", test_flag_venue_selection),
        ("Missing Venue Info Creation", test_missing_venue_info_creation),
        ("MCP Availability Check", test_mcp_availability_check),
    ]
    
    results = []
    for test_name, test_func in tests:
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"\n✗ Test '{test_name}' failed with exception: {e}")
            import traceback
            traceback.print_exc()
            results.append((test_name, False))
    
    # Summary
    print("\n" + "=" * 60)
    print("TEST SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for _, result in results if result)
    total = len(results)
    
    for test_name, result in results:
        status = "✓ PASS" if result else "✗ FAIL"
        print(f"{status}: {test_name}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed!")
        return True
    else:
        print(f"\n⚠️  {total - passed} test(s) failed")
        return False


if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)
