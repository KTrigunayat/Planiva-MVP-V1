"""
Integration tests for agent collaboration using existing test data
"""

import json
import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime
from typing import Dict, List, Any

from crewai import Crew, Task
from agents.orchestrator import create_orchestrator_agent, create_orchestrator_tasks
from agents.budgeting import create_budgeting_agent, create_budget_allocation_task, BudgetingAgentCoordinator
from agents.sourcing import create_sourcing_agent, create_sourcing_tasks
from agents.timeline import create_timeline_agent, create_timeline_tasks
from agents.blueprint import create_blueprint_agent, create_blueprint_tasks


class TestAgentCollaboration:
    """Test agent collaboration workflows"""
    
    @pytest.fixture
    def intimate_wedding_data(self):
        """Test data for intimate wedding scenario"""
        return {
            "clientName": "Sarah & Michael",
            "clientId": "client_intimate_001",
            "guestCount": {
                "Reception": 120,
                "Ceremony": 100
            },
            "clientVision": "We want an intimate, cozy celebration with close family and friends. Focus on quality over quantity with beautiful photography and personalized touches.",
            "budget": 800000,
            "venuePreferences": ["Resort", "Garden"],
            "essentialVenueAmenities": ["Parking", "AC", "Garden"],
            "foodAndCatering": {
                "cuisinePreferences": ["Indian", "Continental"],
                "dietaryOptions": ["Vegetarian", "Vegan"]
            },
            "additionalRequirements": {
                "photography": "Candid photography with focus on emotions and moments",
                "videography": "Highlight reel with ceremony coverage",
                "makeup": "Natural bridal makeup with on-site service"
            },
            "eventDate": "2024-12-15",
            "location": "Bangalore"
        }
    
    @pytest.fixture
    def luxury_wedding_data(self):
        """Test data for luxury wedding scenario"""
        return {
            "clientName": "Priya & Arjun",
            "clientId": "client_luxury_001",
            "guestCount": {
                "Reception": 500,
                "Ceremony": 400,
                "Sangeet": 300
            },
            "clientVision": "Grand luxury wedding with premium vendors, opulent decorations, and world-class service. No expense spared for the perfect celebration.",
            "budget": 2500000,
            "venuePreferences": ["Hotel", "Palace"],
            "essentialVenueAmenities": ["Parking", "AC", "Sound System", "Bridal Suite"],
            "foodAndCatering": {
                "cuisinePreferences": ["Indian", "Continental", "Chinese"],
                "dietaryOptions": ["Vegetarian", "Non-Vegetarian", "Jain"]
            },
            "additionalRequirements": {
                "photography": "Premium photography with multiple photographers and drone coverage",
                "videography": "Cinematic wedding film with same-day highlights",
                "makeup": "Celebrity makeup artist with full bridal party service"
            },
            "eventDate": "2024-11-25",
            "location": "Mumbai"
        }
    
    @patch('agents.orchestrator.OllamaLLM')
    @patch('agents.budgeting.OllamaLLM')
    @patch('agents.sourcing.OllamaLLM')
    def test_orchestrator_budgeting_collaboration(self, mock_sourcing_llm, mock_budgeting_llm, mock_orchestrator_llm, intimate_wedding_data):
        """Test collaboration between Orchestrator and Budgeting agents"""
        # Mock LLM responses
        mock_orchestrator_llm.return_value = Mock()
        mock_budgeting_llm.return_value = Mock()
        mock_sourcing_llm.return_value = Mock()
        
        # Create agents
        orchestrator = create_orchestrator_agent()
        budgeting = create_budgeting_agent()
        
        # Create tasks
        orchestrator_tasks = create_orchestrator_tasks(intimate_wedding_data)
        budget_task = create_budget_allocation_task(intimate_wedding_data, intimate_wedding_data['budget'])
        
        # Assign agents to tasks
        for task in orchestrator_tasks:
            task.agent = orchestrator
        budget_task.agent = budgeting
        
        # Test budget allocation coordination
        budgeting_coordinator = BudgetingAgentCoordinator()
        budget_strategies = budgeting_coordinator.generate_budget_strategies(
            intimate_wedding_data, intimate_wedding_data['budget']
        )
        
        # Verify budget allocation results
        assert budget_strategies['total_budget'] == 800000
        assert budget_strategies['event_type'] == 'intimate'  # Should detect intimate event
        assert len(budget_strategies['allocation_strategies']) == 3
        
        # Test orchestrator beam search with budget results
        beam_search_tool = orchestrator.tools[0]  # BeamSearchTool
        
        # Create mock vendor combinations with budget allocation
        test_combinations = [
            {
                'vendors': {
                    'venue': {'rental_cost': 200000, 'location_city': 'Bangalore'},
                    'caterer': {'min_veg_price': 700, 'location_city': 'Bangalore'}
                },
                'budget_allocation': budget_strategies['recommended_strategy']['allocation']
            }
        ]
        
        beam_result = beam_search_tool._run(
            test_combinations, 
            intimate_wedding_data, 
            beam_width=3
        )
        beam_data = json.loads(beam_result)
        
        assert beam_data['beam_width'] == 3
        assert len(beam_data['top_combinations']) > 0
        assert beam_data['top_combinations'][0]['score'] > 0
    
    @patch('agents.sourcing.OllamaLLM')
    @patch('agents.budgeting.OllamaLLM')
    def test_sourcing_budgeting_collaboration(self, mock_budgeting_llm, mock_sourcing_llm, luxury_wedding_data):
        """Test collaboration between Sourcing and Budgeting agents"""
        # Mock LLM responses
        mock_budgeting_llm.return_value = Mock()
        mock_sourcing_llm.return_value = Mock()
        
        # Create agents
        sourcing = create_sourcing_agent()
        budgeting = create_budgeting_agent()
        
        # Step 1: Generate budget allocation
        budgeting_coordinator = BudgetingAgentCoordinator()
        budget_strategies = budgeting_coordinator.generate_budget_strategies(
            luxury_wedding_data, luxury_wedding_data['budget']
        )
        
        # Verify luxury event detection and allocation
        assert budget_strategies['event_type'] == 'luxury'
        assert budget_strategies['total_budget'] == 2500000
        
        recommended_allocation = budget_strategies['recommended_strategy']['allocation']
        
        # Step 2: Mock vendor sourcing results
        mock_vendor_combinations = [
            {
                'vendors': {
                    'venue': {
                        'id': 'venue_luxury_1',
                        'name': 'Grand Palace Hotel',
                        'rental_cost': 1000000,
                        'max_seating_capacity': 600,
                        'location_city': 'Mumbai',
                        'venue_type': 'Hotel'
                    },
                    'caterer': {
                        'id': 'caterer_luxury_1',
                        'name': 'Royal Catering',
                        'min_veg_price': 1200,
                        'min_nonveg_price': 1500,
                        'location_city': 'Mumbai',
                        'attributes': {'cuisines': ['Indian', 'Continental', 'Chinese']}
                    },
                    'photographer': {
                        'id': 'photographer_luxury_1',
                        'name': 'Elite Photography',
                        'photo_package_price': 150000,
                        'location_city': 'Mumbai'
                    },
                    'makeup_artist': {
                        'id': 'makeup_luxury_1',
                        'name': 'Celebrity Makeup Studio',
                        'bridal_makeup_price': 50000,
                        'location_city': 'Mumbai'
                    }
                }
            }
        ]
        
        # Step 3: Calculate fitness scores for vendor combinations
        scored_combinations = budgeting_coordinator.calculate_combination_fitness(
            mock_vendor_combinations, luxury_wedding_data, budget_strategies['recommended_strategy']
        )
        
        # Verify fitness calculation results
        assert len(scored_combinations) == 1
        combination = scored_combinations[0]
        
        assert 'fitness_analysis' in combination
        assert 'overall_fitness_score' in combination
        assert 0 <= combination['overall_fitness_score'] <= 1
        
        # Check that luxury vendors score well for luxury event
        fitness_analysis = combination['fitness_analysis']
        assert 'component_scores' in fitness_analysis
        assert fitness_analysis['component_scores']['budget_fitness'] > 0.5
        assert fitness_analysis['component_scores']['preference_fitness'] > 0.5
    
    @patch('agents.timeline.OllamaLLM')
    @patch('agents.budgeting.OllamaLLM')
    def test_timeline_budgeting_integration(self, mock_budgeting_llm, mock_timeline_llm, intimate_wedding_data):
        """Test integration between Timeline and Budgeting agents"""
        # Mock LLM responses
        mock_budgeting_llm.return_value = Mock()
        mock_timeline_llm.return_value = Mock()
        
        # Create agents
        timeline = create_timeline_agent()
        budgeting = create_budgeting_agent()
        
        # Generate budget allocation
        budgeting_coordinator = BudgetingAgentCoordinator()
        budget_strategies = budgeting_coordinator.generate_budget_strategies(
            intimate_wedding_data, intimate_wedding_data['budget']
        )
        
        # Create mock vendor combination with timeline constraints
        vendor_combination = {
            'venue': {
                'name': 'Garden Resort',
                'location_city': 'Bangalore',
                'rental_cost': 250000,
                'setup_time_hours': 4,
                'max_event_duration': 8
            },
            'caterer': {
                'name': 'Intimate Catering',
                'location_city': 'Bangalore',
                'min_veg_price': 700,
                'setup_time_hours': 2,
                'service_duration': 4
            },
            'photographer': {
                'name': 'Candid Moments',
                'location_city': 'Bangalore',
                'photo_package_price': 60000,
                'coverage_hours': 6
            }
        }
        
        # Test timeline conflict detection
        conflict_tool = timeline.tools[0]  # ConflictDetectionTool
        
        test_timeline = {
            'activities': [
                {'name': 'Venue Setup', 'start_time': '10:00', 'duration': 4.0},
                {'name': 'Catering Setup', 'start_time': '12:00', 'duration': 2.0},
                {'name': 'Photography Start', 'start_time': '14:00', 'duration': 6.0},
                {'name': 'Ceremony', 'start_time': '16:00', 'duration': 1.5},
                {'name': 'Reception', 'start_time': '18:00', 'duration': 4.0}
            ]
        }
        
        conflict_result = conflict_tool._run(
            vendor_combination, 
            intimate_wedding_data['eventDate'], 
            test_timeline
        )
        conflict_data = json.loads(conflict_result)
        
        # Verify timeline feasibility
        assert 'feasibility_score' in conflict_data
        assert 'conflicts_detected' in conflict_data
        assert 'recommendations' in conflict_data
        
        # Should have high feasibility for well-planned timeline
        assert conflict_data['feasibility_score'] > 0.7
    
    @patch('agents.blueprint.OllamaLLM')
    @patch('agents.budgeting.OllamaLLM')
    def test_blueprint_final_integration(self, mock_budgeting_llm, mock_blueprint_llm, luxury_wedding_data):
        """Test Blueprint agent integration with final vendor selection"""
        # Mock LLM responses
        mock_budgeting_llm.return_value = Mock()
        mock_blueprint_llm.return_value = Mock()
        
        # Create agents
        blueprint = create_blueprint_agent()
        budgeting = create_budgeting_agent()
        
        # Create final vendor selection data
        final_selection = {
            'client_data': luxury_wedding_data,
            'selected_combination': {
                'vendors': {
                    'venue': {
                        'name': 'Grand Palace Hotel',
                        'rental_cost': 1000000,
                        'location_city': 'Mumbai',
                        'contact': '+91-9876543210'
                    },
                    'caterer': {
                        'name': 'Royal Catering',
                        'min_veg_price': 1200,
                        'location_city': 'Mumbai',
                        'contact': '+91-9876543211'
                    }
                },
                'total_cost': 2200000,
                'fitness_score': 0.89
            },
            'timeline': {
                'event_date': '2024-11-25',
                'activities': [
                    {'name': 'Ceremony', 'start_time': '16:00', 'duration': 2.0},
                    {'name': 'Reception', 'start_time': '19:00', 'duration': 5.0}
                ]
            }
        }
        
        # Test blueprint generation
        blueprint_tool = blueprint.tools[0]  # BlueprintGenerationTool
        
        # Mock LLM response for blueprint generation
        mock_blueprint_response = """
        # Wedding Event Blueprint
        
        ## Client Information
        - **Couple**: Priya & Arjun
        - **Event Date**: November 25, 2024
        - **Location**: Mumbai
        - **Guest Count**: 500 (Reception)
        
        ## Vendor Details
        ### Venue: Grand Palace Hotel
        - **Cost**: ₹10,00,000
        - **Contact**: +91-9876543210
        - **Capacity**: 600 guests
        
        ### Catering: Royal Catering
        - **Cost**: ₹12,00,000 (estimated for 500 guests)
        - **Contact**: +91-9876543211
        - **Cuisines**: Indian, Continental, Chinese
        
        ## Timeline
        - **4:00 PM**: Ceremony begins
        - **7:00 PM**: Reception starts
        
        ## Total Investment: ₹22,00,000
        ## Fitness Score: 89%
        """
        
        blueprint_tool.llm.invoke.return_value = mock_blueprint_response
        
        blueprint_result = blueprint_tool._run(final_selection)
        blueprint_data = json.loads(blueprint_result)
        
        # Verify blueprint generation
        assert 'blueprint_content' in blueprint_data
        assert 'generation_metadata' in blueprint_data
        assert 'client_name' in blueprint_data['generation_metadata']
        assert blueprint_data['generation_metadata']['client_name'] == 'Priya & Arjun'
        
        # Check that blueprint contains key information
        blueprint_content = blueprint_data['blueprint_content']
        assert 'Grand Palace Hotel' in blueprint_content
        assert 'Royal Catering' in blueprint_content
        assert '₹22,00,000' in blueprint_content


class TestWorkflowIntegration:
    """Test end-to-end workflow integration"""
    
    @pytest.fixture
    def mock_crew_execution(self):
        """Mock crew execution for testing"""
        def mock_kickoff(inputs):
            return Mock(
                success=True,
                result="Workflow completed successfully",
                tasks_output=[
                    Mock(description="Budget allocation completed", output="Budget strategies generated"),
                    Mock(description="Vendor sourcing completed", output="Vendors sourced and ranked"),
                    Mock(description="Timeline validation completed", output="Timeline validated"),
                    Mock(description="Blueprint generation completed", output="Final blueprint created")
                ]
            )
        return mock_kickoff
    
    @patch('crewai.Crew.kickoff')
    @patch('agents.orchestrator.OllamaLLM')
    @patch('agents.budgeting.OllamaLLM')
    @patch('agents.sourcing.OllamaLLM')
    @patch('agents.timeline.OllamaLLM')
    @patch('agents.blueprint.OllamaLLM')
    def test_complete_workflow_integration(self, mock_blueprint_llm, mock_timeline_llm, 
                                         mock_sourcing_llm, mock_budgeting_llm, 
                                         mock_orchestrator_llm, mock_crew_kickoff, 
                                         mock_crew_execution, intimate_wedding_data):
        """Test complete workflow integration from start to finish"""
        # Mock all LLMs
        mock_orchestrator_llm.return_value = Mock()
        mock_budgeting_llm.return_value = Mock()
        mock_sourcing_llm.return_value = Mock()
        mock_timeline_llm.return_value = Mock()
        mock_blueprint_llm.return_value = Mock()
        
        # Mock crew execution
        mock_crew_kickoff.side_effect = mock_crew_execution
        
        # Create all agents
        orchestrator = create_orchestrator_agent()
        budgeting = create_budgeting_agent()
        sourcing = create_sourcing_agent()
        timeline = create_timeline_agent()
        blueprint = create_blueprint_agent()
        
        # Create tasks for each agent
        orchestrator_tasks = create_orchestrator_tasks(intimate_wedding_data)
        budget_task = create_budget_allocation_task(intimate_wedding_data, intimate_wedding_data['budget'])
        sourcing_tasks = create_sourcing_tasks(intimate_wedding_data)
        timeline_tasks = create_timeline_tasks(intimate_wedding_data)
        blueprint_tasks = create_blueprint_tasks(intimate_wedding_data)
        
        # Assign agents to tasks
        for task in orchestrator_tasks:
            task.agent = orchestrator
        budget_task.agent = budgeting
        for task in sourcing_tasks:
            task.agent = sourcing
        for task in timeline_tasks:
            task.agent = timeline
        for task in blueprint_tasks:
            task.agent = blueprint
        
        # Create crew with all agents and tasks
        all_tasks = orchestrator_tasks + [budget_task] + sourcing_tasks + timeline_tasks + blueprint_tasks
        
        crew = Crew(
            agents=[orchestrator, budgeting, sourcing, timeline, blueprint],
            tasks=all_tasks,
            verbose=True,
            process="sequential"  # Sequential process for testing
        )
        
        # Execute workflow
        result = crew.kickoff(inputs=intimate_wedding_data)
        
        # Verify workflow execution
        assert result.success is True
        assert len(result.tasks_output) == 4  # Mocked task outputs
        
        # Verify that crew.kickoff was called with correct inputs
        mock_crew_kickoff.assert_called_once_with(inputs=intimate_wedding_data)
    
    def test_workflow_state_management(self, intimate_wedding_data):
        """Test workflow state management across agent interactions"""
        # Create orchestrator with state management
        orchestrator = create_orchestrator_agent()
        state_tool = orchestrator.tools[1]  # StateManagementTool
        
        # Test workflow state progression
        initial_state = {
            'workflow_id': 'test_workflow_001',
            'client_data': intimate_wedding_data,
            'current_step': 'initialization',
            'completed_steps': [],
            'beam_candidates': []
        }
        
        # Save initial state
        save_result = state_tool._run(initial_state, 'save', 'workflow_001')
        save_data = json.loads(save_result)
        assert save_data['success'] is True
        
        # Update state after budget allocation
        budget_update = {
            'current_step': 'vendor_sourcing',
            'completed_steps': ['initialization', 'budget_allocation'],
            'budget_strategies': [
                {'strategy': 'balanced', 'fitness_score': 0.85}
            ]
        }
        
        update_result = state_tool._run(budget_update, 'update', 'workflow_001')
        update_data = json.loads(update_result)
        assert update_data['success'] is True
        
        # Load final state
        load_result = state_tool._run({}, 'load', 'workflow_001')
        load_data = json.loads(load_result)
        
        assert load_data['success'] is True
        final_state = load_data['workflow_state']
        assert final_state['current_step'] == 'vendor_sourcing'
        assert 'budget_allocation' in final_state['completed_steps']
        assert 'budget_strategies' in final_state
    
    def test_error_recovery_workflow(self, luxury_wedding_data):
        """Test error recovery in agent workflows"""
        # Create budgeting coordinator
        budgeting_coordinator = BudgetingAgentCoordinator()
        
        # Test with invalid budget (should handle gracefully)
        try:
            invalid_data = luxury_wedding_data.copy()
            invalid_data['budget'] = -1000  # Invalid negative budget
            
            # Should handle error gracefully
            budget_strategies = budgeting_coordinator.generate_budget_strategies(
                invalid_data, invalid_data['budget']
            )
            
            # Should return some default strategy even with invalid input
            assert 'allocation_strategies' in budget_strategies
            
        except Exception as e:
            # If exception is raised, it should be a meaningful error
            assert "budget" in str(e).lower() or "invalid" in str(e).lower()
        
        # Test with missing required fields
        try:
            incomplete_data = {'clientName': 'Test'}  # Missing required fields
            
            budget_strategies = budgeting_coordinator.generate_budget_strategies(
                incomplete_data, 1000000
            )
            
            # Should handle missing fields gracefully
            assert 'event_type' in budget_strategies
            
        except Exception as e:
            # Should provide meaningful error message
            assert len(str(e)) > 0


class TestPerformanceIntegration:
    """Test performance aspects of agent integration"""
    
    def test_agent_response_times(self, intimate_wedding_data):
        """Test that agent operations complete within reasonable time"""
        import time
        
        # Test budget allocation performance
        start_time = time.time()
        budgeting_coordinator = BudgetingAgentCoordinator()
        budget_strategies = budgeting_coordinator.generate_budget_strategies(
            intimate_wedding_data, intimate_wedding_data['budget']
        )
        budget_time = time.time() - start_time
        
        # Should complete within 5 seconds
        assert budget_time < 5.0
        assert len(budget_strategies['allocation_strategies']) > 0
        
        # Test fitness calculation performance
        start_time = time.time()
        mock_combinations = [
            {
                'vendors': {
                    'venue': {'rental_cost': 200000, 'location_city': 'Bangalore'},
                    'caterer': {'min_veg_price': 700, 'location_city': 'Bangalore'}
                }
            }
        ]
        
        scored_combinations = budgeting_coordinator.calculate_combination_fitness(
            mock_combinations, intimate_wedding_data, budget_strategies['recommended_strategy']
        )
        fitness_time = time.time() - start_time
        
        # Should complete within 3 seconds
        assert fitness_time < 3.0
        assert len(scored_combinations) > 0
    
    def test_memory_usage_integration(self, luxury_wedding_data):
        """Test memory usage during agent operations"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Perform multiple agent operations
        budgeting_coordinator = BudgetingAgentCoordinator()
        
        for i in range(10):  # Simulate multiple workflow executions
            budget_strategies = budgeting_coordinator.generate_budget_strategies(
                luxury_wedding_data, luxury_wedding_data['budget']
            )
            
            mock_combinations = [
                {
                    'vendors': {
                        'venue': {'rental_cost': 1000000, 'location_city': 'Mumbai'},
                        'caterer': {'min_veg_price': 1200, 'location_city': 'Mumbai'}
                    }
                }
            ]
            
            scored_combinations = budgeting_coordinator.calculate_combination_fitness(
                mock_combinations, luxury_wedding_data, budget_strategies['recommended_strategy']
            )
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory increase should be reasonable (less than 100MB for 10 operations)
        assert memory_increase < 100
    
    def test_concurrent_agent_operations(self, intimate_wedding_data, luxury_wedding_data):
        """Test concurrent agent operations"""
        import threading
        import time
        
        results = {}
        errors = {}
        
        def run_budget_allocation(client_data, result_key):
            try:
                coordinator = BudgetingAgentCoordinator()
                result = coordinator.generate_budget_strategies(
                    client_data, client_data['budget']
                )
                results[result_key] = result
            except Exception as e:
                errors[result_key] = str(e)
        
        # Run concurrent budget allocations
        thread1 = threading.Thread(
            target=run_budget_allocation, 
            args=(intimate_wedding_data, 'intimate')
        )
        thread2 = threading.Thread(
            target=run_budget_allocation, 
            args=(luxury_wedding_data, 'luxury')
        )
        
        start_time = time.time()
        thread1.start()
        thread2.start()
        
        thread1.join(timeout=10)  # 10 second timeout
        thread2.join(timeout=10)
        
        execution_time = time.time() - start_time
        
        # Both operations should complete successfully
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 2
        assert 'intimate' in results
        assert 'luxury' in results
        
        # Should complete within reasonable time (concurrent execution)
        assert execution_time < 8.0  # Should be faster than sequential
        
        # Verify results are correct
        assert results['intimate']['event_type'] == 'intimate'
        assert results['luxury']['event_type'] == 'luxury'


if __name__ == "__main__":
    # Run basic integration tests
    print("Running Agent Collaboration Integration Tests...")
    
    # Test data
    test_intimate_data = {
        "clientName": "Test Intimate",
        "guestCount": {"Reception": 120},
        "clientVision": "Intimate cozy celebration",
        "budget": 800000,
        "venuePreferences": ["Resort"],
        "eventDate": "2024-12-15"
    }
    
    test_luxury_data = {
        "clientName": "Test Luxury",
        "guestCount": {"Reception": 500},
        "clientVision": "Grand luxury wedding",
        "budget": 2500000,
        "venuePreferences": ["Hotel"],
        "eventDate": "2024-11-25"
    }
    
    try:
        # Test budget allocation for different event types
        coordinator = BudgetingAgentCoordinator()
        
        intimate_budget = coordinator.generate_budget_strategies(test_intimate_data, 800000)
        luxury_budget = coordinator.generate_budget_strategies(test_luxury_data, 2500000)
        
        assert intimate_budget['event_type'] == 'intimate'
        assert luxury_budget['event_type'] == 'luxury'
        
        print("✅ Event type detection working correctly")
        
        # Test fitness calculation integration
        mock_combination = [{
            'vendors': {
                'venue': {'rental_cost': 200000, 'location_city': 'Bangalore'},
                'caterer': {'min_veg_price': 700, 'location_city': 'Bangalore'}
            }
        }]
        
        scored = coordinator.calculate_combination_fitness(
            mock_combination, test_intimate_data, intimate_budget['recommended_strategy']
        )
        
        assert len(scored) == 1
        assert 'overall_fitness_score' in scored[0]
        
        print("✅ Agent collaboration working correctly")
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        exit(1)
    
    print("🎉 All basic integration tests passed!")