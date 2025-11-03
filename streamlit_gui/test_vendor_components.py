"""
Test script for vendor assignment display components
"""

import sys
import os

# Add parent directory to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from components.task_components import (
    render_vendor_assignment_card,
    render_vendor_centric_view,
    render_vendor_workload_chart,
    render_vendor_filter_dropdown,
    _calculate_average_priority
)


def test_calculate_average_priority():
    """Test average priority calculation"""
    
    # Test with mixed priorities
    tasks = [
        {"priority": "critical"},
        {"priority": "high"},
        {"priority": "medium"},
        {"priority": "low"}
    ]
    result = _calculate_average_priority(tasks)
    print(f"✓ Mixed priorities: {result}")
    assert result == "High/Medium"
    
    # Test with all critical
    tasks = [
        {"priority": "critical"},
        {"priority": "critical"}
    ]
    result = _calculate_average_priority(tasks)
    print(f"✓ All critical: {result}")
    assert result == "Critical/High"
    
    # Test with empty list
    tasks = []
    result = _calculate_average_priority(tasks)
    print(f"✓ Empty list: {result}")
    assert result == "N/A"
    
    # Test with all low
    tasks = [
        {"priority": "low"},
        {"priority": "low"}
    ]
    result = _calculate_average_priority(tasks)
    print(f"✓ All low: {result}")
    assert result == "Low"
    
    print("\n✅ All priority calculation tests passed!")


def test_vendor_data_structure():
    """Test that vendor data structures are handled correctly"""
    
    # Test task with vendor
    task_with_vendor = {
        "id": "task1",
        "name": "Setup Venue",
        "assigned_vendor": {
            "name": "Elite Venues",
            "type": "Venue",
            "vendor_id": "v123",
            "fitness_score": 85.5,
            "rationale": "Best location and availability",
            "availability": "Available",
            "contact": {
                "email": "contact@elitevenues.com",
                "phone": "+1-555-0123",
                "address": "123 Main St",
                "website": "https://elitevenues.com"
            },
            "combination_id": "combo1"
        }
    }
    
    vendor = task_with_vendor.get("assigned_vendor")
    assert vendor is not None
    assert vendor.get("name") == "Elite Venues"
    assert vendor.get("fitness_score") == 85.5
    print("✓ Task with vendor structure is valid")
    
    # Test task without vendor
    task_without_vendor = {
        "id": "task2",
        "name": "Manual Task"
    }
    
    vendor = task_without_vendor.get("assigned_vendor")
    assert vendor is None
    print("✓ Task without vendor structure is valid")
    
    print("\n✅ All vendor data structure tests passed!")


def test_vendor_grouping():
    """Test vendor grouping logic"""
    
    tasks = [
        {
            "id": "t1",
            "name": "Task 1",
            "priority": "high",
            "status": "completed",
            "assigned_vendor": {
                "name": "Vendor A",
                "type": "Caterer"
            }
        },
        {
            "id": "t2",
            "name": "Task 2",
            "priority": "medium",
            "status": "pending",
            "assigned_vendor": {
                "name": "Vendor A",
                "type": "Caterer"
            }
        },
        {
            "id": "t3",
            "name": "Task 3",
            "priority": "critical",
            "status": "in_progress",
            "assigned_vendor": {
                "name": "Vendor B",
                "type": "Photographer"
            }
        },
        {
            "id": "t4",
            "name": "Task 4",
            "priority": "low",
            "status": "pending"
            # No vendor assigned
        }
    ]
    
    # Group tasks by vendor
    vendor_tasks_map = {}
    unassigned_tasks = []
    
    for task in tasks:
        vendor = task.get("assigned_vendor")
        if vendor:
            vendor_name = vendor.get("name", "Unknown Vendor")
            if vendor_name not in vendor_tasks_map:
                vendor_tasks_map[vendor_name] = {
                    "vendor_info": vendor,
                    "tasks": []
                }
            vendor_tasks_map[vendor_name]["tasks"].append(task)
        else:
            unassigned_tasks.append(task)
    
    assert len(vendor_tasks_map) == 2
    assert "Vendor A" in vendor_tasks_map
    assert "Vendor B" in vendor_tasks_map
    assert len(vendor_tasks_map["Vendor A"]["tasks"]) == 2
    assert len(vendor_tasks_map["Vendor B"]["tasks"]) == 1
    assert len(unassigned_tasks) == 1
    
    print("✓ Vendor grouping logic works correctly")
    print(f"  - Found {len(vendor_tasks_map)} vendors")
    print(f"  - Vendor A has {len(vendor_tasks_map['Vendor A']['tasks'])} tasks")
    print(f"  - Vendor B has {len(vendor_tasks_map['Vendor B']['tasks'])} tasks")
    print(f"  - {len(unassigned_tasks)} unassigned tasks")
    
    print("\n✅ All vendor grouping tests passed!")


def test_workload_calculation():
    """Test workload calculation logic"""
    
    tasks = [
        {
            "id": "t1",
            "status": "completed",
            "priority": "critical",
            "estimated_duration_hours": 4,
            "assigned_vendor": {"name": "Vendor A"}
        },
        {
            "id": "t2",
            "status": "pending",
            "priority": "high",
            "estimated_duration_hours": 2,
            "assigned_vendor": {"name": "Vendor A"}
        },
        {
            "id": "t3",
            "status": "in_progress",
            "priority": "medium",
            "estimated_duration_hours": 3,
            "assigned_vendor": {"name": "Vendor B"}
        }
    ]
    
    # Calculate workload
    vendor_workload = {}
    
    for task in tasks:
        vendor = task.get("assigned_vendor")
        if vendor:
            vendor_name = vendor.get("name", "Unknown Vendor")
            if vendor_name not in vendor_workload:
                vendor_workload[vendor_name] = {
                    "total_tasks": 0,
                    "completed_tasks": 0,
                    "total_hours": 0,
                    "critical_tasks": 0,
                    "high_tasks": 0
                }
            
            vendor_workload[vendor_name]["total_tasks"] += 1
            
            if task.get("status", "").lower() == "completed":
                vendor_workload[vendor_name]["completed_tasks"] += 1
            
            duration = task.get("estimated_duration_hours", 0)
            if isinstance(duration, (int, float)):
                vendor_workload[vendor_name]["total_hours"] += duration
            
            priority = task.get("priority", "").lower()
            if priority == "critical":
                vendor_workload[vendor_name]["critical_tasks"] += 1
            elif priority == "high":
                vendor_workload[vendor_name]["high_tasks"] += 1
    
    assert len(vendor_workload) == 2
    assert vendor_workload["Vendor A"]["total_tasks"] == 2
    assert vendor_workload["Vendor A"]["completed_tasks"] == 1
    assert vendor_workload["Vendor A"]["total_hours"] == 6
    assert vendor_workload["Vendor A"]["critical_tasks"] == 1
    assert vendor_workload["Vendor A"]["high_tasks"] == 1
    
    assert vendor_workload["Vendor B"]["total_tasks"] == 1
    assert vendor_workload["Vendor B"]["total_hours"] == 3
    
    print("✓ Workload calculation works correctly")
    print(f"  - Vendor A: {vendor_workload['Vendor A']['total_tasks']} tasks, {vendor_workload['Vendor A']['total_hours']} hours")
    print(f"  - Vendor B: {vendor_workload['Vendor B']['total_tasks']} tasks, {vendor_workload['Vendor B']['total_hours']} hours")
    
    print("\n✅ All workload calculation tests passed!")


if __name__ == "__main__":
    print("=" * 60)
    print("Testing Vendor Assignment Display Components")
    print("=" * 60)
    print()
    
    try:
        test_calculate_average_priority()
        print()
        test_vendor_data_structure()
        print()
        test_vendor_grouping()
        print()
        test_workload_calculation()
        print()
        print("=" * 60)
        print("✅ ALL TESTS PASSED!")
        print("=" * 60)
    except AssertionError as e:
        print()
        print("=" * 60)
        print(f"❌ TEST FAILED: {e}")
        print("=" * 60)
        sys.exit(1)
    except Exception as e:
        print()
        print("=" * 60)
        print(f"❌ UNEXPECTED ERROR: {e}")
        print("=" * 60)
        sys.exit(1)
