"""
Test script for results components
"""
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from components.results import ResultsDisplayManager, PlanManager
from utils.helpers import format_currency

def test_results_display_manager():
    """Test the ResultsDisplayManager class"""
    print("Testing ResultsDisplayManager...")
    
    # Create test data
    test_combinations = [
        {
            "combination_id": "combo_1",
            "fitness_score": 85.5,
            "total_cost": 15000,
            "venue": {
                "name": "Grand Ballroom",
                "location": "Downtown",
                "cost": 8000,
                "amenities": ["Parking", "AV Equipment", "Catering Kitchen"]
            },
            "caterer": {
                "name": "Gourmet Catering Co",
                "cost": 4000,
                "cuisine_types": ["Italian", "American"]
            },
            "photographer": {
                "name": "Perfect Moments Photography",
                "cost": 2000
            },
            "makeup_artist": {
                "name": "Beauty by Sarah",
                "cost": 1000
            }
        },
        {
            "combination_id": "combo_2", 
            "fitness_score": 78.2,
            "total_cost": 12500,
            "venue": {
                "name": "Garden Pavilion",
                "location": "Suburbs",
                "cost": 6000,
                "amenities": ["Garden Views", "Outdoor Space"]
            },
            "caterer": {
                "name": "Fresh & Local Catering",
                "cost": 3500,
                "cuisine_types": ["Farm-to-Table", "Vegetarian"]
            },
            "photographer": {
                "name": "Natural Light Studios",
                "cost": 1800
            },
            "makeup_artist": {
                "name": "Glamour Touch",
                "cost": 1200
            }
        }
    ]
    
    # Test sorting
    manager = ResultsDisplayManager()
    
    # Test sort by fitness score (descending)
    sorted_by_fitness = manager._sort_combinations(test_combinations, "fitness_score", True)
    assert sorted_by_fitness[0]["fitness_score"] == 85.5
    print("✓ Sort by fitness score works")
    
    # Test sort by cost (ascending)
    sorted_by_cost = manager._sort_combinations(test_combinations, "total_cost", False)
    assert sorted_by_cost[0]["total_cost"] == 12500
    print("✓ Sort by cost works")
    
    # Test sort by venue name
    sorted_by_venue = manager._sort_combinations(test_combinations, "venue_name", False)
    assert sorted_by_venue[0]["venue"]["name"] == "Garden Pavilion"
    print("✓ Sort by venue name works")
    
    print("ResultsDisplayManager tests passed!")
    return True

def test_plan_manager():
    """Test the PlanManager class"""
    print("\nTesting PlanManager...")
    
    # Create test plans data
    test_plans = [
        {
            "plan_id": "plan_001",
            "client_name": "John Smith",
            "event_type": "Wedding",
            "status": "completed",
            "created_at": "2024-01-15",
            "budget": 20000
        },
        {
            "plan_id": "plan_002", 
            "client_name": "Jane Doe",
            "event_type": "Corporate Event",
            "status": "in_progress",
            "created_at": "2024-01-20",
            "budget": 15000
        },
        {
            "plan_id": "plan_003",
            "client_name": "Bob Johnson", 
            "event_type": "Birthday Party",
            "status": "pending",
            "created_at": "2024-01-25",
            "budget": 5000,
            "archived": True
        }
    ]
    
    manager = PlanManager()
    
    # Test filtering by status
    filtered = manager._filter_plans(test_plans, "", ["completed", "in_progress"], False)
    assert len(filtered) == 2
    print("✓ Status filtering works")
    
    # Test archived filtering
    filtered_with_archived = manager._filter_plans(test_plans, "", ["pending"], True)
    assert len(filtered_with_archived) == 1
    
    filtered_without_archived = manager._filter_plans(test_plans, "", ["pending"], False)
    assert len(filtered_without_archived) == 0
    print("✓ Archived filtering works")
    
    # Test search filtering
    search_filtered = manager._filter_plans(test_plans, "john", [], False)
    # Should find John Smith and Bob Johnson (but Bob Johnson is archived and we're not showing archived)
    search_filtered_with_archived = manager._filter_plans(test_plans, "john", [], True)
    assert len(search_filtered) == 1  # Only John Smith (not archived)
    assert len(search_filtered_with_archived) == 2  # John Smith and Bob Johnson
    print("✓ Search filtering works")
    
    print("PlanManager tests passed!")
    return True

def test_helper_functions():
    """Test helper functions"""
    print("\nTesting helper functions...")
    
    # Test currency formatting
    assert format_currency(1234.56) == "$1,234.56"
    assert format_currency(1000000) == "$1,000,000.00"
    print("✓ Currency formatting works")
    
    print("Helper function tests passed!")
    return True

def main():
    """Run all tests"""
    print("Running Results Components Tests")
    print("=" * 40)
    
    try:
        test_results_display_manager()
        test_plan_manager()
        test_helper_functions()
        
        print("\n" + "=" * 40)
        print("🎉 All tests passed successfully!")
        return True
        
    except Exception as e:
        print(f"\n❌ Test failed: {str(e)}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)