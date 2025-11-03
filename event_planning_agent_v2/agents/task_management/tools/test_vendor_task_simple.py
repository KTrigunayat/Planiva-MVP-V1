"""
Simple standalone test for VendorTaskTool

Tests core functionality without requiring full system imports
"""

import sys
from datetime import timedelta
from unittest.mock import Mock, MagicMock, patch


def test_vendor_task_tool_basic():
    """Test basic VendorTaskTool functionality"""
    
    # Mock the imports to avoid dependency issues
    sys.modules['event_planning_agent_v2.database.connection'] = Mock()
    sys.modules['event_planning_agent_v2.database.models'] = Mock()
    sys.modules['event_planning_agent_v2.workflows.state_models'] = Mock()
    sys.modules['event_planning_agent_v2.mcp_servers.vendor_server'] = Mock()
    
    # Now import after mocking
    from vendor_task_tool import VendorTaskTool
    from ..models.data_models import Resource, VendorAssignment
    from ..models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
    
    # Create mock database manager
    mock_db_manager = Mock()
    mock_session = MagicMock()
    mock_db_manager.get_sync_session.return_value.__enter__ = Mock(return_value=mock_session)
    mock_db_manager.get_sync_session.return_value.__exit__ = Mock(return_value=None)
    
    # Create tool instance
    tool = VendorTaskTool(db_connection=mock_db_manager, use_mcp=False)
    
    print("✓ VendorTaskTool initialized successfully")
    
    # Test vendor extraction
    selected_combination = {
        'venue': {
            'vendor_id': 'venue-1',
            'name': 'Grand Palace Hotel',
            'location_city': 'Mumbai'
        },
        'caterer': {
            'vendor_id': 'caterer-1',
            'name': 'Royal Caterers',
            'location_city': 'Mumbai'
        },
        'fitness_score': 0.85
    }
    
    vendors = tool._extract_vendors_from_combination(selected_combination)
    assert len(vendors) == 2
    assert 'venue' in vendors
    assert 'caterer' in vendors
    assert vendors['venue']['name'] == 'Grand Palace Hotel'
    
    print("✓ Vendor extraction works correctly")
    
    # Test vendor type identification
    task = ConsolidatedTask(
        task_id='task-1',
        task_name='Venue Setup and Decoration',
        priority_level='Critical',
        priority_score=0.95,
        priority_rationale='Essential',
        parent_task_id=None,
        task_description='Set up venue with decorations',
        granularity_level=0,
        estimated_duration=timedelta(hours=6),
        sub_tasks=[],
        dependencies=[],
        resources_required=[],
        resource_conflicts=[]
    )
    
    required_types = tool._identify_required_vendor_types(task)
    assert 'venue' in required_types
    
    print("✓ Vendor type identification works correctly")
    
    # Test manual assignment flagging
    assignment = tool._flag_manual_assignment(task, 'venue')
    assert isinstance(assignment, VendorAssignment)
    assert assignment.requires_manual_assignment is True
    assert assignment.vendor_id == ""
    
    print("✓ Manual assignment flagging works correctly")
    
    # Test match score calculation
    vendor = {
        'name': 'Grand Palace Hotel',
        'vendor_type': 'venue',
        'fitness_score': 0.85
    }
    vendor_details = {
        'max_seating_capacity': 300,
        'location_city': 'Mumbai'
    }
    
    match_score = tool._match_vendor_to_task(task, vendor, vendor_details)
    assert 0.0 <= match_score <= 1.0
    
    print("✓ Match score calculation works correctly")
    
    # Test rationale generation
    rationale = tool._generate_assignment_rationale(
        task, vendor, vendor_details, match_score
    )
    assert isinstance(rationale, str)
    assert len(rationale) > 0
    assert 'Grand Palace Hotel' in rationale
    
    print("✓ Rationale generation works correctly")
    
    print("\n✅ All basic tests passed!")
    return True


if __name__ == '__main__':
    try:
        test_vendor_task_tool_basic()
        print("\n🎉 VendorTaskTool implementation verified successfully!")
    except Exception as e:
        print(f"\n❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)
