"""
Simple test for Logistics Check Tool

Tests basic functionality without requiring full database setup.
"""

import sys
from pathlib import Path
from datetime import timedelta

# Add project root to path
project_root = Path(__file__).parent.parent.parent.parent.parent
sys.path.insert(0, str(project_root))

from event_planning_agent_v2.agents.task_management.models.data_models import Resource
from event_planning_agent_v2.agents.task_management.models.consolidated_models import (
    ConsolidatedTask, ConsolidatedTaskData
)


def test_logistics_check_tool_structure():
    """Test that LogisticsCheckTool can be imported and instantiated"""
    print("=" * 80)
    print("TEST: Logistics Check Tool Structure")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.agents.task_management.tools.logistics_check_tool import (
            LogisticsCheckTool
        )
        print("✓ LogisticsCheckTool imported successfully")
        
        # Test instantiation (without database connection)
        tool = LogisticsCheckTool(db_connection=None)
        print("✓ LogisticsCheckTool instantiated successfully")
        
        # Check methods exist
        assert hasattr(tool, 'verify_logistics'), "Missing verify_logistics method"
        print("✓ verify_logistics method exists")
        
        assert hasattr(tool, '_check_transportation'), "Missing _check_transportation method"
        print("✓ _check_transportation method exists")
        
        assert hasattr(tool, '_check_equipment'), "Missing _check_equipment method"
        print("✓ _check_equipment method exists")
        
        assert hasattr(tool, '_check_setup_requirements'), "Missing _check_setup_requirements method"
        print("✓ _check_setup_requirements method exists")
        
        assert hasattr(tool, '_calculate_feasibility_score'), "Missing _calculate_feasibility_score method"
        print("✓ _calculate_feasibility_score method exists")
        
        assert hasattr(tool, '_flag_logistics_issues'), "Missing _flag_logistics_issues method"
        print("✓ _flag_logistics_issues method exists")
        
        print("\n✅ All structure tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Structure test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_transportation_check():
    """Test transportation checking logic"""
    print("\n" + "=" * 80)
    print("TEST: Transportation Check Logic")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.agents.task_management.tools.logistics_check_tool import (
            LogisticsCheckTool
        )
        
        tool = LogisticsCheckTool(db_connection=None)
        
        # Create test task with transportation needs
        task = ConsolidatedTask(
            task_id="task_001",
            task_name="Transport Equipment",
            priority_level="High",
            priority_score=0.8,
            priority_rationale="Critical for event",
            parent_task_id=None,
            task_description="Transport large sound system and lighting equipment to venue",
            granularity_level=1,
            estimated_duration=timedelta(hours=3),
            sub_tasks=[],
            dependencies=[],
            resources_required=[
                Resource(
                    resource_type="equipment",
                    resource_id="eq_001",
                    resource_name="Large Sound System",
                    quantity_required=1
                )
            ],
            resource_conflicts=[]
        )
        
        # Test with venue info
        venue_info = {
            'vendor_id': 'venue_001',
            'name': 'Grand Hall',
            'location_city': 'Mumbai',
            'location_full': 'Andheri West, Mumbai',
            'max_seating_capacity': 500
        }
        
        result = tool._check_transportation(task, venue_info)
        
        print(f"Status: {result['status']}")
        print(f"Notes: {result['notes']}")
        print(f"Issues: {result['issues']}")
        
        assert 'status' in result, "Missing status in result"
        assert 'notes' in result, "Missing notes in result"
        assert 'issues' in result, "Missing issues in result"
        
        print("\n✓ Transportation check returned valid structure")
        
        # Test without venue info
        result_no_venue = tool._check_transportation(task, None)
        assert result_no_venue['status'] == 'missing_data', "Should return missing_data without venue"
        print("✓ Correctly handles missing venue information")
        
        print("\n✅ Transportation check tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Transportation check test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_equipment_check():
    """Test equipment checking logic"""
    print("\n" + "=" * 80)
    print("TEST: Equipment Check Logic")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.agents.task_management.tools.logistics_check_tool import (
            LogisticsCheckTool
        )
        
        tool = LogisticsCheckTool(db_connection=None)
        
        # Create test task with equipment needs
        task = ConsolidatedTask(
            task_id="task_002",
            task_name="Setup Audio Visual",
            priority_level="High",
            priority_score=0.8,
            priority_rationale="Required for presentations",
            parent_task_id=None,
            task_description="Setup projector, screen, and microphones",
            granularity_level=1,
            estimated_duration=timedelta(hours=2),
            sub_tasks=[],
            dependencies=[],
            resources_required=[
                Resource(
                    resource_type="equipment",
                    resource_id="eq_002",
                    resource_name="Projector",
                    quantity_required=1
                ),
                Resource(
                    resource_type="equipment",
                    resource_id="eq_003",
                    resource_name="Microphones",
                    quantity_required=4
                )
            ],
            resource_conflicts=[]
        )
        
        venue_info = {
            'vendor_id': 'venue_001',
            'name': 'Grand Hall',
            'decor_options': {'projector': True, 'screen': True},
            'attributes': {'sound_system': True}
        }
        
        vendor_info = {}
        
        result = tool._check_equipment(task, venue_info, vendor_info)
        
        print(f"Status: {result['status']}")
        print(f"Notes: {result['notes']}")
        print(f"Issues: {result['issues']}")
        
        assert 'status' in result, "Missing status in result"
        assert 'notes' in result, "Missing notes in result"
        assert 'issues' in result, "Missing issues in result"
        
        print("\n✓ Equipment check returned valid structure")
        
        # Test task without equipment requirements
        task_no_equipment = ConsolidatedTask(
            task_id="task_003",
            task_name="Guest Registration",
            priority_level="Medium",
            priority_score=0.6,
            priority_rationale="Standard task",
            parent_task_id=None,
            task_description="Register guests at entrance",
            granularity_level=1,
            estimated_duration=timedelta(hours=1),
            sub_tasks=[],
            dependencies=[],
            resources_required=[],
            resource_conflicts=[]
        )
        
        result_no_equipment = tool._check_equipment(task_no_equipment, venue_info, vendor_info)
        assert result_no_equipment['status'] == 'verified', "Should verify when no equipment needed"
        print("✓ Correctly handles tasks without equipment requirements")
        
        print("\n✅ Equipment check tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Equipment check test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_setup_requirements_check():
    """Test setup requirements checking logic"""
    print("\n" + "=" * 80)
    print("TEST: Setup Requirements Check Logic")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.agents.task_management.tools.logistics_check_tool import (
            LogisticsCheckTool
        )
        
        tool = LogisticsCheckTool(db_connection=None)
        
        # Create test task with setup requirements
        task = ConsolidatedTask(
            task_id="task_004",
            task_name="Setup Stage Decoration",
            priority_level="High",
            priority_score=0.85,
            priority_rationale="Important for event aesthetics",
            parent_task_id=None,
            task_description="Setup and arrange stage decoration with lighting and backdrop",
            granularity_level=1,
            estimated_duration=timedelta(hours=4),
            sub_tasks=[],
            dependencies=[],
            resources_required=[],
            resource_conflicts=[]
        )
        
        venue_info = {
            'vendor_id': 'venue_001',
            'name': 'Grand Hall',
            'location_city': 'Mumbai',
            'max_seating_capacity': 500,
            'ideal_capacity': 400,
            'room_count': 2,
            'policies': {
                'no_outside_decorators': False,
                'limited_setup_time': False
            }
        }
        
        result = tool._check_setup_requirements(task, venue_info)
        
        print(f"Status: {result['status']}")
        print(f"Notes: {result['notes']}")
        print(f"Issues: {result['issues']}")
        
        assert 'status' in result, "Missing status in result"
        assert 'notes' in result, "Missing notes in result"
        assert 'issues' in result, "Missing issues in result"
        
        print("\n✓ Setup requirements check returned valid structure")
        
        # Test without venue info
        result_no_venue = tool._check_setup_requirements(task, None)
        assert result_no_venue['status'] == 'missing_data', "Should return missing_data without venue"
        print("✓ Correctly handles missing venue information")
        
        print("\n✅ Setup requirements check tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Setup requirements check test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def test_feasibility_score_calculation():
    """Test feasibility score calculation"""
    print("\n" + "=" * 80)
    print("TEST: Feasibility Score Calculation")
    print("=" * 80)
    
    try:
        from event_planning_agent_v2.agents.task_management.tools.logistics_check_tool import (
            LogisticsCheckTool
        )
        
        tool = LogisticsCheckTool(db_connection=None)
        
        # Test case 1: All verified
        result1 = {
            'status': 'verified',
            'notes': 'All good',
            'issues': []
        }
        score1 = tool._calculate_feasibility_score(result1, result1, result1)
        print(f"All verified score: {score1:.2f}")
        assert score1 >= 0.8, "All verified should have high score"
        print("✓ All verified case works correctly")
        
        # Test case 2: Some issues
        result2 = {
            'status': 'issue',
            'notes': 'Some problems',
            'issues': ['Issue 1']
        }
        score2 = tool._calculate_feasibility_score(result2, result1, result1)
        print(f"Some issues score: {score2:.2f}")
        assert 0.4 <= score2 <= 0.8, "Some issues should have medium score"
        print("✓ Some issues case works correctly")
        
        # Test case 3: Missing data
        result3 = {
            'status': 'missing_data',
            'notes': 'Data missing',
            'issues': []
        }
        score3 = tool._calculate_feasibility_score(result3, result3, result3)
        print(f"Missing data score: {score3:.2f}")
        assert score3 <= 0.5, "Missing data should have low score"
        print("✓ Missing data case works correctly")
        
        # Test case 4: Multiple issues
        result4 = {
            'status': 'issue',
            'notes': 'Multiple problems',
            'issues': ['Issue 1', 'Issue 2', 'Issue 3']
        }
        score4 = tool._calculate_feasibility_score(result4, result4, result4)
        print(f"Multiple issues score: {score4:.2f}")
        assert score4 <= 0.5, "Multiple issues should have low score"
        print("✓ Multiple issues case works correctly")
        
        print("\n✅ Feasibility score calculation tests passed!")
        return True
        
    except Exception as e:
        print(f"\n❌ Feasibility score calculation test failed: {e}")
        import traceback
        traceback.print_exc()
        return False


def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("LOGISTICS CHECK TOOL - SIMPLE TESTS")
    print("=" * 80)
    
    results = []
    
    # Run tests
    results.append(("Structure Test", test_logistics_check_tool_structure()))
    results.append(("Transportation Check", test_transportation_check()))
    results.append(("Equipment Check", test_equipment_check()))
    results.append(("Setup Requirements Check", test_setup_requirements_check()))
    results.append(("Feasibility Score Calculation", test_feasibility_score_calculation()))
    
    # Print summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for test_name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    all_passed = all(result[1] for result in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 80)
    
    return 0 if all_passed else 1


if __name__ == "__main__":
    exit(main())
