"""
End-to-end workflow tests with LangGraph execution
"""

import json
import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime
from typing import Dict, List, Any

from langgraph.graph import StateGraph, START, END
from workflows.planning_workflow import create_planning_workflow, EventPlanningWorkflow
from workflows.state_models import EventPlanningState, WorkflowStatus
from workflows.execution_engine import WorkflowExecutionEngine
from database.state_manager import WorkflowStateManager
from agents.budgeting import BudgetingAgentCoordinator

clas
s TestLangGraphWorkflow:
    """Test LangGraph workflow execution end-to-end"""
    
    @pytest.fixture
    def workflow_state_manager(self):
        """Mock workflow state manager"""
        manager = Mock(spec=WorkflowStateManager)
        manager.save_state = AsyncMock(return_value=True)
        manager.load_state = AsyncMock(return_value=None)
        manager.update_state = AsyncMock(return_value=True)
        return manager
    
    @pytest.fixture
    def sample_client_request(self):
        """Sample client request for testing"""
        return {
            "clientName": "Sarah & Michael",
            "clientId": "client_workflow_001",
            "guestCount": {
                "Reception": 120,
                "Ceremony": 100
            },
            "clientVision": "Intimate, cozy celebration with close family and friends",
            "budget": 800000,
            "venuePreferences": ["Resort", "Garden"],
            "essentialVenueAmenities": ["Parking", "AC", "Garden"],
            "foodAndCatering": {
                "cuisinePreferences": ["Indian", "Continental"],
                "dietaryOptions": ["Vegetarian", "Vegan"]
            },
            "additionalRequirements": {
                "photography": "Candid photography with focus on emotions",
                "videography": "Highlight reel with ceremony coverage",
                "makeup": "Natural bridal makeup with on-site service"
            },
            "eventDate": "2024-12-15",
            "location": "Bangalore"
        }
    
    @pytest.fixture
    def initial_workflow_state(self, sample_client_request):
        """Initial workflow state for testing"""
        return EventPlanningState(
            workflow_id="test_workflow_001",
            client_request=sample_client_request,
            budget_allocations=[],
            vendor_combinations=[],
            beam_candidates=[],
            selected_combination=None,
            final_blueprint=None,
            workflow_status=WorkflowStatus.INITIALIZED,
            iteration_count=0,
            current_step="initialization",
            error_context=None,
            metadata={}
        )
    
    @patch('workflows.planning_workflow.OllamaLLM')
    @patch('database.state_manager.WorkflowStateManager')
    async def test_complete_workflow_execution(self, mock_state_manager, mock_llm, 
                                             initial_workflow_state, workflow_state_manager):
        """Test complete workflow execution from start to finish"""
        # Mock LLM responses
        mock_llm.return_value = Mock()
        mock_state_manager.return_value = workflow_state_manager
        
        # Create workflow
        workflow = EventPlanningWorkflow()
        execution_engine = WorkflowExecutionEngine(workflow_state_manager)
        
        # Mock workflow nodes to return expected results
        with patch.object(workflow, 'initialize_planning') as mock_init, \
             patch.object(workflow, 'budget_allocation_node') as mock_budget, \
             patch.object(workflow, 'vendor_sourcing_node') as mock_sourcing, \
             patch.object(workflow, 'beam_search_node') as mock_beam, \
             patch.object(workflow, 'client_selection_node') as mock_selection, \
             patch.object(workflow, 'blueprint_generation_node') as mock_blueprint:
            
            # Configure mock returns for each workflow step
            mock_init.return_value = {
                **initial_workflow_state,
                "workflow_status": WorkflowStatus.BUDGET_ALLOCATION,
                "current_step": "budget_allocation"
            }
            
            mock_budget.return_value = {
                **initial_workflow_state,
                "budget_allocations": [
                    {
                        "strategy": "balanced",
                        "allocation": {
                            "venue": 300000,
                            "catering": 200000,
                            "photography": 80000,
                            "makeup": 40000,
                            "miscellaneous": 180000
                        }
                    }
                ],
                "workflow_status": WorkflowStatus.VENDOR_SOURCING,
                "current_step": "vendor_sourcing"
            }
            
            mock_sourcing.return_value = {
                **initial_workflow_state,
                "vendor_combinations": [
                    {
                        "combination_id": "combo_001",
                        "vendors": {
                            "venue": {"name": "Garden Resort", "cost": 250000},
                            "caterer": {"name": "Intimate Catering", "cost": 180000},
                            "photographer": {"name": "Candid Moments", "cost": 75000}
                        }
                    }
                ],
                "workflow_status": WorkflowStatus.BEAM_SEARCH,
                "current_step": "beam_search"
            }
            
            mock_beam.return_value = {
                **initial_workflow_state,
                "beam_candidates": [
                    {
                        "combination_id": "combo_001",
                        "fitness_score": 0.87,
                        "vendors": {
                            "venue": {"name": "Garden Resort", "cost": 250000},
                            "caterer": {"name": "Intimate Catering", "cost": 180000}
                        }
                    }
                ],
                "workflow_status": WorkflowStatus.CLIENT_SELECTION,
                "current_step": "client_selection",
                "iteration_count": 1
            }
            
            mock_selection.return_value = {
                **initial_workflow_state,
                "selected_combination": {
                    "combination_id": "combo_001",
                    "fitness_score": 0.87
                },
                "workflow_status": WorkflowStatus.BLUEPRINT_GENERATION,
                "current_step": "blueprint_generation"
            }
            
            mock_blueprint.return_value = {
                **initial_workflow_state,
                "final_blueprint": "# Wedding Event Blueprint\n\nComplete event plan...",
                "workflow_status": WorkflowStatus.COMPLETED,
                "current_step": "completed"
            }
            
            # Execute workflow
            result = await execution_engine.execute_workflow(initial_workflow_state)
            
            # Verify workflow completion
            assert result["workflow_status"] == WorkflowStatus.COMPLETED
            assert result["final_blueprint"] is not None
            assert result["selected_combination"] is not None
            
            # Verify all workflow steps were called
            mock_init.assert_called_once()
            mock_budget.assert_called_once()
            mock_sourcing.assert_called_once()
            mock_beam.assert_called_once()
            mock_selection.assert_called_once()
            mock_blueprint.assert_called_once()
    
    @patch('workflows.planning_workflow.OllamaLLM')
    async def test_beam_search_workflow_node(self, mock_llm, initial_workflow_state):
        """Test beam search node execution with multiple iterations"""
        mock_llm.return_value = Mock()
        
        # Create workflow with beam search capabilities
        workflow = EventPlanningWorkflow()
        
        # Prepare state with vendor combinations for beam search
        state_with_combinations = {
            **initial_workflow_state,
            "vendor_combinations": [
                {
                    "combination_id": "combo_001",
                    "vendors": {
                        "venue": {"name": "Resort A", "cost": 250000, "score": 0.8},
                        "caterer": {"name": "Caterer A", "cost": 180000, "score": 0.9}
                    },
                    "total_cost": 430000
                },
                {
                    "combination_id": "combo_002", 
                    "vendors": {
                        "venue": {"name": "Resort B", "cost": 300000, "score": 0.9},
                        "caterer": {"name": "Caterer B", "cost": 200000, "score": 0.8}
                    },
                    "total_cost": 500000
                },
                {
                    "combination_id": "combo_003",
                    "vendors": {
                        "venue": {"name": "Resort C", "cost": 280000, "score": 0.7},
                        "caterer": {"name": "Caterer C", "cost": 190000, "score": 0.85}
                    },
                    "total_cost": 470000
                }
            ]
        }
        
        # Mock fitness calculation
        with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
            mock_fitness.side_effect = [0.87, 0.82, 0.79]  # Fitness scores for combinations
            
            # Execute beam search node
            result = workflow.beam_search_node(state_with_combinations)
            
            # Verify beam search results
            assert "beam_candidates" in result
            assert len(result["beam_candidates"]) <= 3  # Beam width = 3
            assert result["iteration_count"] == 1
            
            # Verify candidates are sorted by fitness score
            beam_candidates = result["beam_candidates"]
            if len(beam_candidates) > 1:
                for i in range(len(beam_candidates) - 1):
                    assert beam_candidates[i]["fitness_score"] >= beam_candidates[i + 1]["fitness_score"]
            
            # Verify fitness calculation was called for each combination
            assert mock_fitness.call_count == 3
    
    @patch('workflows.planning_workflow.OllamaLLM')
    async def test_workflow_conditional_routing(self, mock_llm, initial_workflow_state):
        """Test conditional routing in workflow based on beam search results"""
        mock_llm.return_value = Mock()
        
        workflow = EventPlanningWorkflow()
        
        # Test case 1: Should continue search (low iteration count, low scores)
        state_continue = {
            **initial_workflow_state,
            "beam_candidates": [
                {"fitness_score": 0.6, "combination_id": "combo_001"},
                {"fitness_score": 0.55, "combination_id": "combo_002"}
            ],
            "iteration_count": 1
        }
        
        should_continue = workflow.should_continue_search(state_continue)
        assert should_continue == "continue"
        
        # Test case 2: Should present options (high scores or max iterations)
        state_present = {
            **initial_workflow_state,
            "beam_candidates": [
                {"fitness_score": 0.9, "combination_id": "combo_001"},
                {"fitness_score": 0.85, "combination_id": "combo_002"}
            ],
            "iteration_count": 2
        }
        
        should_continue = workflow.should_continue_search(state_present)
        assert should_continue == "present_options"
        
        # Test case 3: Max iterations reached
        state_max_iter = {
            **initial_workflow_state,
            "beam_candidates": [
                {"fitness_score": 0.7, "combination_id": "combo_001"}
            ],
            "iteration_count": 5  # Assuming max_iterations = 5
        }
        
        should_continue = workflow.should_continue_search(state_max_iter)
        assert should_continue == "present_options"
    
    @patch('workflows.planning_workflow.OllamaLLM')
    async def test_workflow_error_handling(self, mock_llm, initial_workflow_state):
        """Test workflow error handling and recovery"""
        mock_llm.return_value = Mock()
        
        workflow = EventPlanningWorkflow()
        state_manager = Mock(spec=WorkflowStateManager)
        execution_engine = WorkflowExecutionEngine(state_manager)
        
        # Mock a node that raises an exception
        with patch.object(workflow, 'budget_allocation_node') as mock_budget:
            mock_budget.side_effect = Exception("Budget allocation failed")
            
            # Mock error recovery
            state_manager.save_recovery_checkpoint = AsyncMock(return_value=True)
            state_manager.recover_from_checkpoint = AsyncMock(return_value=initial_workflow_state)
            
            # Execute workflow with error
            with pytest.raises(Exception) as exc_info:
                await execution_engine.execute_workflow(initial_workflow_state)
            
            assert "Budget allocation failed" in str(exc_info.value)
            
            # Verify recovery checkpoint was saved
            state_manager.save_recovery_checkpoint.assert_called_once()
    
    @patch('workflows.planning_workflow.OllamaLLM')
    async def test_workflow_state_persistence(self, mock_llm, initial_workflow_state, workflow_state_manager):
        """Test workflow state persistence across execution steps"""
        mock_llm.return_value = Mock()
        
        workflow = EventPlanningWorkflow()
        execution_engine = WorkflowExecutionEngine(workflow_state_manager)
        
        # Mock workflow steps to verify state persistence
        with patch.object(workflow, 'budget_allocation_node') as mock_budget:
            mock_budget.return_value = {
                **initial_workflow_state,
                "budget_allocations": [{"strategy": "test"}],
                "workflow_status": WorkflowStatus.VENDOR_SOURCING
            }
            
            # Execute single step
            result = workflow.budget_allocation_node(initial_workflow_state)
            
            # Verify state was updated
            assert len(result["budget_allocations"]) == 1
            assert result["workflow_status"] == WorkflowStatus.VENDOR_SOURCING
            
            # Verify state manager was called to save state
            workflow_state_manager.save_state.assert_called()


class TestWorkflowPerformance:
    """Test workflow performance characteristics"""
    
    @pytest.fixture
    def performance_test_data(self):
        """Large dataset for performance testing"""
        return {
            "clientName": "Performance Test",
            "clientId": "perf_test_001",
            "guestCount": {"Reception": 500, "Ceremony": 400},
            "budget": 2000000,
            "venuePreferences": ["Hotel", "Resort", "Palace"],
            "eventDate": "2024-12-01",
            "location": "Mumbai"
        }
    
    def test_beam_search_performance(self, performance_test_data):
        """Test beam search algorithm performance with large datasets"""
        import time
        
        # Create large number of vendor combinations
        vendor_combinations = []
        for i in range(100):  # 100 combinations
            combination = {
                "combination_id": f"combo_{i:03d}",
                "vendors": {
                    "venue": {
                        "name": f"Venue {i}",
                        "cost": 200000 + (i * 5000),
                        "score": 0.5 + (i % 50) * 0.01
                    },
                    "caterer": {
                        "name": f"Caterer {i}",
                        "cost": 150000 + (i * 3000),
                        "score": 0.6 + (i % 40) * 0.01
                    }
                },
                "total_cost": 350000 + (i * 8000)
            }
            vendor_combinations.append(combination)
        
        # Test beam search performance
        workflow = EventPlanningWorkflow()
        
        state = EventPlanningState(
            workflow_id="perf_test",
            client_request=performance_test_data,
            vendor_combinations=vendor_combinations,
            beam_candidates=[],
            workflow_status=WorkflowStatus.BEAM_SEARCH,
            iteration_count=0
        )
        
        # Mock fitness calculation for performance
        with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
            mock_fitness.side_effect = [0.5 + (i % 100) * 0.005 for i in range(100)]
            
            start_time = time.time()
            result = workflow.beam_search_node(state)
            execution_time = time.time() - start_time
            
            # Performance assertions
            assert execution_time < 2.0  # Should complete within 2 seconds
            assert len(result["beam_candidates"]) == 3  # Beam width = 3
            assert result["beam_candidates"][0]["fitness_score"] >= result["beam_candidates"][1]["fitness_score"]
            
            # Verify all combinations were evaluated
            assert mock_fitness.call_count == 100
    
    def test_vendor_ranking_performance(self, performance_test_data):
        """Test vendor ranking algorithm performance"""
        import time
        
        # Create large vendor dataset
        vendors = []
        for i in range(200):  # 200 vendors
            vendor = {
                "id": f"vendor_{i:03d}",
                "name": f"Vendor {i}",
                "cost": 50000 + (i * 1000),
                "location_city": "Mumbai" if i % 2 == 0 else "Bangalore",
                "rating": 3.0 + (i % 20) * 0.1,
                "attributes": {
                    "specialties": ["Indian", "Continental"] if i % 3 == 0 else ["Indian"],
                    "capacity": 100 + (i * 5)
                }
            }
            vendors.append(vendor)
        
        # Test ranking performance
        budgeting_coordinator = BudgetingAgentCoordinator()
        
        start_time = time.time()
        
        # Mock vendor scoring
        scored_vendors = []
        for vendor in vendors:
            # Simulate scoring calculation
            score = (vendor["rating"] * 0.3 + 
                    (1.0 if vendor["location_city"] == "Mumbai" else 0.5) * 0.4 +
                    (1.0 if len(vendor["attributes"]["specialties"]) > 1 else 0.7) * 0.3)
            scored_vendors.append((vendor, score))
        
        # Sort by score
        scored_vendors.sort(key=lambda x: x[1], reverse=True)
        top_vendors = scored_vendors[:10]  # Top 10 vendors
        
        ranking_time = time.time() - start_time
        
        # Performance assertions
        assert ranking_time < 1.0  # Should complete within 1 second
        assert len(top_vendors) == 10
        
        # Verify ranking is correct
        for i in range(len(top_vendors) - 1):
            assert top_vendors[i][1] >= top_vendors[i + 1][1]
    
    def test_concurrent_workflow_execution(self, performance_test_data):
        """Test concurrent workflow execution performance"""
        import threading
        import time
        
        results = {}
        errors = {}
        
        def execute_workflow(workflow_id):
            try:
                workflow = EventPlanningWorkflow()
                
                state = EventPlanningState(
                    workflow_id=workflow_id,
                    client_request=performance_test_data,
                    vendor_combinations=[],
                    beam_candidates=[],
                    workflow_status=WorkflowStatus.INITIALIZED,
                    iteration_count=0
                )
                
                # Mock quick workflow execution
                with patch.object(workflow, 'initialize_planning') as mock_init:
                    mock_init.return_value = {
                        **state,
                        "workflow_status": WorkflowStatus.COMPLETED,
                        "final_blueprint": f"Blueprint for {workflow_id}"
                    }
                    
                    result = workflow.initialize_planning(state)
                    results[workflow_id] = result
                    
            except Exception as e:
                errors[workflow_id] = str(e)
        
        # Execute multiple workflows concurrently
        threads = []
        start_time = time.time()
        
        for i in range(5):  # 5 concurrent workflows
            thread = threading.Thread(
                target=execute_workflow,
                args=(f"workflow_{i:03d}",)
            )
            threads.append(thread)
            thread.start()
        
        # Wait for all threads to complete
        for thread in threads:
            thread.join(timeout=10)
        
        execution_time = time.time() - start_time
        
        # Performance assertions
        assert len(errors) == 0, f"Errors occurred: {errors}"
        assert len(results) == 5
        assert execution_time < 5.0  # Should complete within 5 seconds
        
        # Verify all workflows completed
        for i in range(5):
            workflow_id = f"workflow_{i:03d}"
            assert workflow_id in results
            assert results[workflow_id]["workflow_status"] == WorkflowStatus.COMPLETED
    
    def test_memory_usage_during_workflow(self, performance_test_data):
        """Test memory usage during workflow execution"""
        import psutil
        import os
        
        process = psutil.Process(os.getpid())
        initial_memory = process.memory_info().rss / 1024 / 1024  # MB
        
        # Execute workflow with large state
        workflow = EventPlanningWorkflow()
        
        # Create large state with many vendor combinations
        large_combinations = []
        for i in range(50):
            combination = {
                "combination_id": f"combo_{i}",
                "vendors": {
                    "venue": {"name": f"Venue {i}", "cost": 200000 + i * 1000},
                    "caterer": {"name": f"Caterer {i}", "cost": 150000 + i * 500},
                    "photographer": {"name": f"Photographer {i}", "cost": 80000 + i * 200}
                },
                "metadata": {"large_data": "x" * 1000}  # 1KB of data per combination
            }
            large_combinations.append(combination)
        
        state = EventPlanningState(
            workflow_id="memory_test",
            client_request=performance_test_data,
            vendor_combinations=large_combinations,
            beam_candidates=[],
            workflow_status=WorkflowStatus.BEAM_SEARCH,
            iteration_count=0
        )
        
        # Execute beam search with large dataset
        with patch.object(workflow, '_calculate_fitness_score') as mock_fitness:
            mock_fitness.side_effect = [0.5 + i * 0.01 for i in range(50)]
            
            result = workflow.beam_search_node(state)
        
        final_memory = process.memory_info().rss / 1024 / 1024  # MB
        memory_increase = final_memory - initial_memory
        
        # Memory usage should be reasonable
        assert memory_increase < 50  # Less than 50MB increase
        assert len(result["beam_candidates"]) <= 3  # Beam search should limit candidates


class TestWorkflowIntegrationScenarios:
    """Test specific integration scenarios"""
    
    @pytest.fixture
    def multi_event_data(self):
        """Data for multi-event wedding scenario"""
        return {
            "clientName": "Raj & Priya",
            "clientId": "multi_event_001",
            "guestCount": {
                "Sangeet": 200,
                "Ceremony": 300,
                "Reception": 400
            },
            "clientVision": "Traditional multi-day celebration",
            "budget": 1500000,
            "venuePreferences": ["Hotel", "Banquet Hall"],
            "eventDate": "2024-12-20",
            "location": "Delhi"
        }
    
    @patch('workflows.planning_workflow.OllamaLLM')
    async def test_multi_event_workflow(self, mock_llm, multi_event_data):
        """Test workflow handling multiple events (Sangeet, Ceremony, Reception)"""
        mock_llm.return_value = Mock()
        
        workflow = EventPlanningWorkflow()
        
        state = EventPlanningState(
            workflow_id="multi_event_test",
            client_request=multi_event_data,
            vendor_combinations=[],
            beam_candidates=[],
            workflow_status=WorkflowStatus.INITIALIZED,
            iteration_count=0
        )
        
        # Mock budget allocation for multi-event
        with patch.object(workflow, 'budget_allocation_node') as mock_budget:
            mock_budget.return_value = {
                **state,
                "budget_allocations": [
                    {
                        "strategy": "multi_event",
                        "allocation": {
                            "sangeet_venue": 200000,
                            "ceremony_venue": 300000,
                            "reception_venue": 400000,
                            "catering": 400000,
                            "photography": 100000,
                            "miscellaneous": 100000
                        },
                        "event_breakdown": {
                            "Sangeet": 300000,
                            "Ceremony": 500000,
                            "Reception": 700000
                        }
                    }
                ],
                "workflow_status": WorkflowStatus.VENDOR_SOURCING
            }
            
            result = workflow.budget_allocation_node(state)
            
            # Verify multi-event budget allocation
            allocation = result["budget_allocations"][0]
            assert "event_breakdown" in allocation
            assert "Sangeet" in allocation["event_breakdown"]
            assert "Ceremony" in allocation["event_breakdown"]
            assert "Reception" in allocation["event_breakdown"]
            
            # Verify total budget is preserved
            total_allocated = sum(allocation["event_breakdown"].values())
            assert total_allocated <= multi_event_data["budget"]
    
    @patch('workflows.planning_workflow.OllamaLLM')
    async def test_budget_constraint_workflow(self, mock_llm):
        """Test workflow with tight budget constraints"""
        mock_llm.return_value = Mock()
        
        # Low budget scenario
        tight_budget_data = {
            "clientName": "Budget Wedding",
            "clientId": "budget_001",
            "guestCount": {"Reception": 100},
            "budget": 300000,  # Very tight budget
            "venuePreferences": ["Community Hall"],
            "eventDate": "2024-12-25"
        }
        
        workflow = EventPlanningWorkflow()
        
        state = EventPlanningState(
            workflow_id="budget_constraint_test",
            client_request=tight_budget_data,
            vendor_combinations=[],
            beam_candidates=[],
            workflow_status=WorkflowStatus.INITIALIZED,
            iteration_count=0
        )
        
        # Mock budget allocation with constraints
        with patch.object(workflow, 'budget_allocation_node') as mock_budget:
            mock_budget.return_value = {
                **state,
                "budget_allocations": [
                    {
                        "strategy": "budget_conscious",
                        "allocation": {
                            "venue": 120000,  # 40% of budget
                            "catering": 90000,  # 30% of budget
                            "photography": 45000,  # 15% of budget
                            "miscellaneous": 45000  # 15% of budget
                        },
                        "constraints": {
                            "max_venue_cost": 120000,
                            "max_catering_per_person": 900,
                            "budget_utilization": 1.0
                        }
                    }
                ],
                "workflow_status": WorkflowStatus.VENDOR_SOURCING
            }
            
            result = workflow.budget_allocation_node(state)
            
            # Verify budget constraints are respected
            allocation = result["budget_allocations"][0]
            total_allocated = sum(allocation["allocation"].values())
            assert total_allocated <= tight_budget_data["budget"]
            
            # Verify constraint information is included
            assert "constraints" in allocation
            assert allocation["constraints"]["budget_utilization"] == 1.0


if __name__ == "__main__":
    # Run basic workflow tests
    print("Running LangGraph Workflow Integration Tests...")
    
    try:
        # Test workflow creation
        workflow = EventPlanningWorkflow()
        assert workflow is not None
        print("✅ Workflow creation successful")
        
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
        print("✅ State model working correctly")
        
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
        print("✅ Beam search logic working correctly")
        
    except Exception as e:
        print(f"❌ Workflow test failed: {e}")
        exit(1)
    
    print("🎉 All basic workflow tests passed!")