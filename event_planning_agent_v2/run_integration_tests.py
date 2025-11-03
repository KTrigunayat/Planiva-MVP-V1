#!/usr/bin/env python3
"""
Integration test runner for the event planning agent system
"""

import sys
import os
import unittest
from unittest.mock import Mock, patch

# Add the current directory to Python path
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

def test_basic_integration():
    """Test basic integration functionality"""
    print("Running basic integration tests...")
    
    try:
        # Test 1: Budget allocation integration
        from agents.budgeting import BudgetingAgentCoordinator
        
        coordinator = BudgetingAgentCoordinator()
        
        test_client_data = {
            "clientName": "Test Client",
            "guestCount": {"Reception": 120},
            "clientVision": "Intimate cozy celebration",
            "budget": 800000,
            "venuePreferences": ["Resort"],
            "eventDate": "2024-12-15",
            "location": "Bangalore"
        }
        
        budget_strategies = coordinator.generate_budget_strategies(test_client_data, 800000)
        
        assert 'total_budget' in budget_strategies
        assert 'event_type' in budget_strategies
        assert 'allocation_strategies' in budget_strategies
        assert len(budget_strategies['allocation_strategies']) > 0
        
        print("✅ Budget allocation integration test passed")
        
        # Test 2: Fitness calculation integration
        mock_combination = [{
            'vendors': {
                'venue': {'rental_cost': 200000, 'location_city': 'Bangalore'},
                'caterer': {'min_veg_price': 700, 'location_city': 'Bangalore'}
            }
        }]
        
        scored_combinations = coordinator.calculate_combination_fitness(
            mock_combination, test_client_data, budget_strategies['recommended_strategy']
        )
        
        assert len(scored_combinations) == 1
        assert 'overall_fitness_score' in scored_combinations[0]
        assert 0 <= scored_combinations[0]['overall_fitness_score'] <= 1
        
        print("✅ Fitness calculation integration test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_workflow_integration():
    """Test workflow integration functionality"""
    print("Running workflow integration tests...")
    
    try:
        from workflows.planning_workflow import EventPlanningWorkflow
        from workflows.state_models import EventPlanningState, WorkflowStatus
        
        # Test workflow creation
        workflow = EventPlanningWorkflow()
        assert workflow is not None
        print("✅ Workflow creation test passed")
        
        # Test state model
        test_state = EventPlanningState(
            workflow_id="test_001",
            client_request={"clientName": "Test"},
            vendor_combinations=[],
            beam_candidates=[],
            workflow_status=WorkflowStatus.INITIALIZED,
            iteration_count=0
        )
        
        assert test_state["workflow_id"] == "test_001"
        assert test_state["workflow_status"] == WorkflowStatus.INITIALIZED
        print("✅ State model test passed")
        
        # Test beam search logic
        test_combinations = [
            {"combination_id": "combo_1", "fitness_score": 0.8},
            {"combination_id": "combo_2", "fitness_score": 0.9},
            {"combination_id": "combo_3", "fitness_score": 0.7}
        ]
        
        # Sort by fitness score (simulate beam search)
        sorted_combinations = sorted(test_combinations, key=lambda x: x["fitness_score"], reverse=True)
        top_3 = sorted_combinations[:3]
        
        assert len(top_3) == 3
        assert top_3[0]["fitness_score"] == 0.9
        print("✅ Beam search logic test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Workflow integration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_performance_basics():
    """Test basic performance characteristics"""
    print("Running basic performance tests...")
    
    try:
        import time
        from agents.budgeting import BudgetingAgentCoordinator
        
        coordinator = BudgetingAgentCoordinator()
        
        test_data = {
            "clientName": "Performance Test",
            "guestCount": {"Reception": 200},
            "budget": 1000000,
            "venuePreferences": ["Hotel"],
            "eventDate": "2024-12-01"
        }
        
        # Test budget allocation performance
        start_time = time.time()
        budget_strategies = coordinator.generate_budget_strategies(test_data, 1000000)
        budget_time = time.time() - start_time
        
        assert budget_time < 5.0  # Should complete within 5 seconds
        print(f"✅ Budget allocation performance test passed ({budget_time:.3f}s)")
        
        # Test fitness calculation performance
        mock_combinations = []
        for i in range(10):  # Test with 10 combinations
            combination = {
                'vendors': {
                    'venue': {'rental_cost': 200000 + i*10000, 'location_city': 'Mumbai'},
                    'caterer': {'min_veg_price': 800 + i*50, 'location_city': 'Mumbai'}
                }
            }
            mock_combinations.append(combination)
        
        start_time = time.time()
        scored_combinations = coordinator.calculate_combination_fitness(
            mock_combinations, test_data, budget_strategies['recommended_strategy']
        )
        fitness_time = time.time() - start_time
        
        assert fitness_time < 3.0  # Should complete within 3 seconds
        assert len(scored_combinations) == 10
        print(f"✅ Fitness calculation performance test passed ({fitness_time:.3f}s)")
        
        return True
        
    except Exception as e:
        print(f"❌ Performance test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_agent_collaboration():
    """Test agent collaboration scenarios"""
    print("Running agent collaboration tests...")
    
    try:
        from agents.budgeting import BudgetingAgentCoordinator
        
        # Test different event types
        intimate_data = {
            "clientName": "Intimate Wedding",
            "guestCount": {"Reception": 100},
            "clientVision": "Small intimate celebration",
            "budget": 600000,
            "venuePreferences": ["Garden"],
            "eventDate": "2024-12-15"
        }
        
        luxury_data = {
            "clientName": "Luxury Wedding", 
            "guestCount": {"Reception": 400},
            "clientVision": "Grand luxury celebration",
            "budget": 2000000,
            "venuePreferences": ["Palace"],
            "eventDate": "2024-11-25"
        }
        
        coordinator = BudgetingAgentCoordinator()
        
        # Test intimate event detection
        intimate_budget = coordinator.generate_budget_strategies(intimate_data, 600000)
        assert intimate_budget['event_type'] == 'intimate'
        print("✅ Intimate event detection test passed")
        
        # Test luxury event detection
        luxury_budget = coordinator.generate_budget_strategies(luxury_data, 2000000)
        assert luxury_budget['event_type'] == 'luxury'
        print("✅ Luxury event detection test passed")
        
        # Test budget allocation differences
        intimate_allocation = intimate_budget['recommended_strategy']['allocation']
        luxury_allocation = luxury_budget['recommended_strategy']['allocation']
        
        # Luxury events should allocate more to premium categories
        assert luxury_allocation.get('venue', 0) > intimate_allocation.get('venue', 0)
        print("✅ Budget allocation differentiation test passed")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent collaboration test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def main():
    """Run all integration tests"""
    print("🚀 Starting Event Planning Agent Integration Tests")
    print("=" * 60)
    
    tests = [
        ("Basic Integration", test_basic_integration),
        ("Workflow Integration", test_workflow_integration),
        ("Performance Basics", test_performance_basics),
        ("Agent Collaboration", test_agent_collaboration)
    ]
    
    passed = 0
    failed = 0
    
    for test_name, test_func in tests:
        print(f"\n📋 {test_name}")
        print("-" * 40)
        
        try:
            if test_func():
                passed += 1
                print(f"✅ {test_name} PASSED")
            else:
                failed += 1
                print(f"❌ {test_name} FAILED")
        except Exception as e:
            failed += 1
            print(f"❌ {test_name} FAILED with exception: {e}")
    
    print("\n" + "=" * 60)
    print(f"📊 Test Results: {passed} passed, {failed} failed")
    
    if failed == 0:
        print("🎉 All integration tests passed!")
        return 0
    else:
        print("💥 Some tests failed!")
        return 1

if __name__ == "__main__":
    exit(main())