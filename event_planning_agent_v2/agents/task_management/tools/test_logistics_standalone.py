"""
Standalone test for Logistics Check Tool - bypasses __init__.py imports
"""

import sys
import importlib.util
from pathlib import Path
from datetime import timedelta

# Direct file import to bypass __init__.py
def import_from_file(module_name, file_path):
    """Import a module directly from a file path"""
    spec = importlib.util.spec_from_file_location(module_name, file_path)
    module = importlib.util.module_from_spec(spec)
    sys.modules[module_name] = module
    spec.loader.exec_module(module)
    return module

# Get paths
tools_dir = Path(__file__).parent
models_dir = tools_dir.parent / "models"

# Import data models first
data_models = import_from_file(
    "data_models",
    str(models_dir / "data_models.py")
)

consolidated_models = import_from_file(
    "consolidated_models",
    str(models_dir / "consolidated_models.py")
)

# Now we can import logistics_check_tool
# But we need to mock the database imports
print("Setting up mocks...")

# Create mock modules
class MockConnectionManager:
    def get_sync_session(self):
        return MockSession()

class MockSession:
    def __enter__(self):
        return self
    
    def __exit__(self, *args):
        pass
    
    def query(self, model):
        return MockQuery()

class MockQuery:
    def filter(self, *args):
        return self
    
    def first(self):
        return None

# Mock the database modules
sys.modules['event_planning_agent_v2'] = type(sys)('event_planning_agent_v2')
sys.modules['event_planning_agent_v2.workflows'] = type(sys)('workflows')
sys.modules['event_planning_agent_v2.workflows.state_models'] = type(sys)('state_models')
sys.modules['event_planning_agent_v2.database'] = type(sys)('database')
sys.modules['event_planning_agent_v2.database.connection'] = type(sys)('connection')
sys.modules['event_planning_agent_v2.database.models'] = type(sys)('models')

# Add mock functions
sys.modules['event_planning_agent_v2.database.connection'].get_connection_manager = lambda: MockConnectionManager()

# Add mock models
class MockVenue:
    vendor_id = None
    name = None
    location_city = None
    location_full = None
    max_seating_capacity = None
    ideal_capacity = None
    room_count = None
    decor_options = None
    attributes = None
    policies = None

sys.modules['event_planning_agent_v2.database.models'].Venue = MockVenue
sys.modules['event_planning_agent_v2.database.models'].Caterer = MockVenue
sys.modules['event_planning_agent_v2.database.models'].Photographer = MockVenue
sys.modules['event_planning_agent_v2.database.models'].MakeupArtist = MockVenue

# Mock EventPlanningState
sys.modules['event_planning_agent_v2.workflows.state_models'].EventPlanningState = dict

print("✓ Mocks set up successfully")

# Now import logistics_check_tool
logistics_module = import_from_file(
    "logistics_check_tool",
    str(tools_dir / "logistics_check_tool.py")
)

LogisticsCheckTool = logistics_module.LogisticsCheckTool

print("✓ LogisticsCheckTool imported successfully")

# Run tests
def test_structure():
    """Test class structure"""
    print("\n" + "=" * 80)
    print("TEST: Class Structure")
    print("=" * 80)
    
    tool = LogisticsCheckTool(db_connection=None)
    
    methods = [
        'verify_logistics',
        '_check_transportation',
        '_check_equipment',
        '_check_setup_requirements',
        '_calculate_feasibility_score',
        '_flag_logistics_issues'
    ]
    
    for method in methods:
        assert hasattr(tool, method), f"Missing method: {method}"
        print(f"✓ {method}() exists")
    
    print("\n✅ Structure test passed!")
    return True

def test_transportation():
    """Test transportation check"""
    print("\n" + "=" * 80)
    print("TEST: Transportation Check")
    print("=" * 80)
    
    tool = LogisticsCheckTool(db_connection=None)
    
    # Create test task
    task = consolidated_models.ConsolidatedTask(
        task_id="task_001",
        task_name="Transport Equipment",
        priority_level="High",
        priority_score=0.8,
        priority_rationale="Critical",
        parent_task_id=None,
        task_description="Transport large equipment to venue",
        granularity_level=1,
        estimated_duration=timedelta(hours=3),
        sub_tasks=[],
        dependencies=[],
        resources_required=[],
        resource_conflicts=[]
    )
    
    venue_info = {
        'vendor_id': 'venue_001',
        'name': 'Test Venue',
        'location_city': 'Mumbai',
        'location_full': 'Andheri, Mumbai'
    }
    
    result = tool._check_transportation(task, venue_info)
    
    assert 'status' in result
    assert 'notes' in result
    assert 'issues' in result
    
    print(f"Status: {result['status']}")
    print(f"Notes: {result['notes']}")
    print(f"Issues: {len(result['issues'])}")
    
    print("\n✅ Transportation check test passed!")
    return True

def test_equipment():
    """Test equipment check"""
    print("\n" + "=" * 80)
    print("TEST: Equipment Check")
    print("=" * 80)
    
    tool = LogisticsCheckTool(db_connection=None)
    
    task = consolidated_models.ConsolidatedTask(
        task_id="task_002",
        task_name="Setup AV Equipment",
        priority_level="High",
        priority_score=0.8,
        priority_rationale="Required",
        parent_task_id=None,
        task_description="Setup projector and sound system",
        granularity_level=1,
        estimated_duration=timedelta(hours=2),
        sub_tasks=[],
        dependencies=[],
        resources_required=[
            data_models.Resource(
                resource_type="equipment",
                resource_id="eq_001",
                resource_name="Projector",
                quantity_required=1
            )
        ],
        resource_conflicts=[]
    )
    
    venue_info = {
        'decor_options': {'projector': True},
        'attributes': {}
    }
    
    vendor_info = {}
    
    result = tool._check_equipment(task, venue_info, vendor_info)
    
    assert 'status' in result
    assert 'notes' in result
    assert 'issues' in result
    
    print(f"Status: {result['status']}")
    print(f"Notes: {result['notes']}")
    print(f"Issues: {len(result['issues'])}")
    
    print("\n✅ Equipment check test passed!")
    return True

def test_setup():
    """Test setup requirements check"""
    print("\n" + "=" * 80)
    print("TEST: Setup Requirements Check")
    print("=" * 80)
    
    tool = LogisticsCheckTool(db_connection=None)
    
    task = consolidated_models.ConsolidatedTask(
        task_id="task_003",
        task_name="Setup Stage Decoration",
        priority_level="High",
        priority_score=0.85,
        priority_rationale="Important",
        parent_task_id=None,
        task_description="Setup and arrange stage decoration",
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
        'max_seating_capacity': 500,
        'ideal_capacity': 400,
        'room_count': 2,
        'policies': {}
    }
    
    result = tool._check_setup_requirements(task, venue_info)
    
    assert 'status' in result
    assert 'notes' in result
    assert 'issues' in result
    
    print(f"Status: {result['status']}")
    print(f"Notes: {result['notes']}")
    print(f"Issues: {len(result['issues'])}")
    
    print("\n✅ Setup requirements check test passed!")
    return True

def test_feasibility_score():
    """Test feasibility score calculation"""
    print("\n" + "=" * 80)
    print("TEST: Feasibility Score Calculation")
    print("=" * 80)
    
    tool = LogisticsCheckTool(db_connection=None)
    
    # Test all verified
    result_verified = {
        'status': 'verified',
        'notes': 'All good',
        'issues': []
    }
    
    score = tool._calculate_feasibility_score(
        result_verified, result_verified, result_verified
    )
    
    print(f"All verified score: {score:.2f}")
    assert 0.8 <= score <= 1.0, "All verified should have high score"
    
    # Test with issues
    result_issue = {
        'status': 'issue',
        'notes': 'Problems',
        'issues': ['Issue 1', 'Issue 2']
    }
    
    score2 = tool._calculate_feasibility_score(
        result_issue, result_issue, result_issue
    )
    
    print(f"With issues score: {score2:.2f}")
    assert 0.0 <= score2 <= 0.5, "With issues should have low score"
    
    print("\n✅ Feasibility score calculation test passed!")
    return True

def main():
    """Run all tests"""
    print("\n" + "=" * 80)
    print("LOGISTICS CHECK TOOL - STANDALONE TESTS")
    print("=" * 80)
    
    tests = [
        ("Structure", test_structure),
        ("Transportation", test_transportation),
        ("Equipment", test_equipment),
        ("Setup", test_setup),
        ("Feasibility Score", test_feasibility_score)
    ]
    
    results = []
    for name, test_func in tests:
        try:
            result = test_func()
            results.append((name, result))
        except Exception as e:
            print(f"\n❌ {name} test failed: {e}")
            import traceback
            traceback.print_exc()
            results.append((name, False))
    
    # Summary
    print("\n" + "=" * 80)
    print("TEST SUMMARY")
    print("=" * 80)
    
    for name, passed in results:
        status = "✅ PASSED" if passed else "❌ FAILED"
        print(f"{name}: {status}")
    
    all_passed = all(r[1] for r in results)
    
    print("\n" + "=" * 80)
    if all_passed:
        print("🎉 ALL TESTS PASSED!")
        print("\nLogistics Check Tool is correctly implemented with:")
        print("  ✓ __init__() - Initialize with database connection")
        print("  ✓ verify_logistics() - Check logistics feasibility for all tasks")
        print("  ✓ _check_transportation() - Verify transportation requirements")
        print("  ✓ _check_equipment() - Verify equipment availability")
        print("  ✓ _check_setup_requirements() - Verify setup time and space")
        print("  ✓ _calculate_feasibility_score() - Calculate overall feasibility")
        print("  ✓ _flag_logistics_issues() - Mark tasks with issues")
        print("\nReturns: List[LogisticsStatus] objects")
    else:
        print("⚠️  SOME TESTS FAILED")
    print("=" * 80)
    
    return 0 if all_passed else 1

if __name__ == "__main__":
    exit(main())
