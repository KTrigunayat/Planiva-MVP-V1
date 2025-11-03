"""
Test script for task progress tracking functionality
"""
import sys
import os
from datetime import datetime, date, timedelta

# Add the current directory to Python path for imports
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from utils.helpers import (
    calculate_task_progress,
    calculate_progress_by_priority,
    calculate_progress_by_vendor,
    get_overdue_tasks,
    get_dependent_tasks,
    check_prerequisites_complete
)

def create_sample_tasks():
    """Create sample task data for testing"""
    today = date.today()
    yesterday = today - timedelta(days=1)
    tomorrow = today + timedelta(days=1)
    
    return [
        {
            'id': '1',
            'name': 'Task 1',
            'status': 'completed',
            'priority': 'critical',
            'is_overdue': False,
            'end_date': tomorrow.isoformat(),
            'assigned_vendor': {'name': 'Vendor A', 'type': 'Venue'},
            'dependencies': []
        },
        {
            'id': '2',
            'name': 'Task 2',
            'status': 'in_progress',
            'priority': 'high',
            'is_overdue': False,
            'end_date': tomorrow.isoformat(),
            'assigned_vendor': {'name': 'Vendor A', 'type': 'Venue'},
            'dependencies': [{'task_id': '1'}]
        },
        {
            'id': '3',
            'name': 'Task 3',
            'status': 'pending',
            'priority': 'medium',
            'is_overdue': True,
            'end_date': yesterday.isoformat(),
            'assigned_vendor': {'name': 'Vendor B', 'type': 'Catering'},
            'dependencies': []
        },
        {
            'id': '4',
            'name': 'Task 4',
            'status': 'blocked',
            'priority': 'low',
            'is_overdue': False,
            'end_date': tomorrow.isoformat(),
            'assigned_vendor': {'name': 'Vendor B', 'type': 'Catering'},
            'dependencies': [{'task_id': '2'}]
        },
        {
            'id': '5',
            'name': 'Task 5',
            'status': 'completed',
            'priority': 'high',
            'is_overdue': False,
            'end_date': tomorrow.isoformat(),
            'assigned_vendor': {'name': 'Vendor C', 'type': 'Photography'},
            'dependencies': []
        }
    ]

def test_calculate_task_progress():
    """Test calculate_task_progress function"""
    print("Testing calculate_task_progress...")
    
    tasks = create_sample_tasks()
    progress = calculate_task_progress(tasks)
    
    assert progress['total_tasks'] == 5, f"Expected 5 total tasks, got {progress['total_tasks']}"
    assert progress['completed_tasks'] == 2, f"Expected 2 completed tasks, got {progress['completed_tasks']}"
    assert progress['in_progress_tasks'] == 1, f"Expected 1 in_progress task, got {progress['in_progress_tasks']}"
    assert progress['pending_tasks'] == 1, f"Expected 1 pending task, got {progress['pending_tasks']}"
    assert progress['blocked_tasks'] == 1, f"Expected 1 blocked task, got {progress['blocked_tasks']}"
    assert progress['overdue_tasks'] == 1, f"Expected 1 overdue task, got {progress['overdue_tasks']}"
    assert progress['completion_percentage'] == 40.0, f"Expected 40% completion, got {progress['completion_percentage']}"
    
    # Test with empty list
    empty_progress = calculate_task_progress([])
    assert empty_progress['total_tasks'] == 0
    assert empty_progress['completion_percentage'] == 0.0
    
    print("✅ calculate_task_progress tests passed")

def test_calculate_progress_by_priority():
    """Test calculate_progress_by_priority function"""
    print("Testing calculate_progress_by_priority...")
    
    tasks = create_sample_tasks()
    priority_progress = calculate_progress_by_priority(tasks)
    
    # Check Critical priority
    assert priority_progress['Critical']['total'] == 1
    assert priority_progress['Critical']['completed'] == 1
    assert priority_progress['Critical']['completion_percentage'] == 100.0
    
    # Check High priority
    assert priority_progress['High']['total'] == 2
    assert priority_progress['High']['completed'] == 1
    assert priority_progress['High']['completion_percentage'] == 50.0
    
    # Check Medium priority
    assert priority_progress['Medium']['total'] == 1
    assert priority_progress['Medium']['completed'] == 0
    assert priority_progress['Medium']['overdue'] == 1
    
    # Check Low priority
    assert priority_progress['Low']['total'] == 1
    assert priority_progress['Low']['completed'] == 0
    
    print("✅ calculate_progress_by_priority tests passed")

def test_calculate_progress_by_vendor():
    """Test calculate_progress_by_vendor function"""
    print("Testing calculate_progress_by_vendor...")
    
    tasks = create_sample_tasks()
    vendor_progress = calculate_progress_by_vendor(tasks)
    
    # Check Vendor A
    assert 'Vendor A' in vendor_progress
    assert vendor_progress['Vendor A']['total'] == 2
    assert vendor_progress['Vendor A']['completed'] == 1
    assert vendor_progress['Vendor A']['completion_percentage'] == 50.0
    assert vendor_progress['Vendor A']['vendor_type'] == 'Venue'
    
    # Check Vendor B
    assert 'Vendor B' in vendor_progress
    assert vendor_progress['Vendor B']['total'] == 2
    assert vendor_progress['Vendor B']['completed'] == 0
    assert vendor_progress['Vendor B']['overdue'] == 1
    
    # Check Vendor C
    assert 'Vendor C' in vendor_progress
    assert vendor_progress['Vendor C']['total'] == 1
    assert vendor_progress['Vendor C']['completed'] == 1
    assert vendor_progress['Vendor C']['completion_percentage'] == 100.0
    
    print("✅ calculate_progress_by_vendor tests passed")

def test_get_overdue_tasks():
    """Test get_overdue_tasks function"""
    print("Testing get_overdue_tasks...")
    
    tasks = create_sample_tasks()
    overdue_tasks = get_overdue_tasks(tasks)
    
    assert len(overdue_tasks) == 1, f"Expected 1 overdue task, got {len(overdue_tasks)}"
    assert overdue_tasks[0]['id'] == '3'
    assert 'days_overdue' in overdue_tasks[0]
    assert overdue_tasks[0]['days_overdue'] >= 1
    
    print("✅ get_overdue_tasks tests passed")

def test_get_dependent_tasks():
    """Test get_dependent_tasks function"""
    print("Testing get_dependent_tasks...")
    
    tasks = create_sample_tasks()
    
    # Task 1 has Task 2 depending on it
    dependent_on_1 = get_dependent_tasks(tasks, '1')
    assert len(dependent_on_1) == 1
    assert dependent_on_1[0]['id'] == '2'
    
    # Task 2 has Task 4 depending on it
    dependent_on_2 = get_dependent_tasks(tasks, '2')
    assert len(dependent_on_2) == 1
    assert dependent_on_2[0]['id'] == '4'
    
    # Task 3 has no dependent tasks
    dependent_on_3 = get_dependent_tasks(tasks, '3')
    assert len(dependent_on_3) == 0
    
    print("✅ get_dependent_tasks tests passed")

def test_check_prerequisites_complete():
    """Test check_prerequisites_complete function"""
    print("Testing check_prerequisites_complete...")
    
    tasks = create_sample_tasks()
    
    # Task 1 has no prerequisites
    task_1 = tasks[0]
    assert check_prerequisites_complete(task_1, tasks) == True
    
    # Task 2 depends on Task 1 (which is completed)
    task_2 = tasks[1]
    assert check_prerequisites_complete(task_2, tasks) == True
    
    # Task 4 depends on Task 2 (which is in_progress, not completed)
    task_4 = tasks[3]
    assert check_prerequisites_complete(task_4, tasks) == False
    
    print("✅ check_prerequisites_complete tests passed")

def main():
    """Run all tests"""
    print("Running task progress tracking tests...\n")
    
    try:
        test_calculate_task_progress()
        test_calculate_progress_by_priority()
        test_calculate_progress_by_vendor()
        test_get_overdue_tasks()
        test_get_dependent_tasks()
        test_check_prerequisites_complete()
        
        print("\n🎉 All task progress tracking tests passed successfully!")
        return True
        
    except AssertionError as e:
        print(f"\n❌ Test assertion failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False
    except Exception as e:
        print(f"\n❌ Test failed with error: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)
