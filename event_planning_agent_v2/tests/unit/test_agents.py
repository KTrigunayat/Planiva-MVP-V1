"""
Unit tests for CrewAI agents
"""

import json
import pytest
from unittest.mock import Mock, patch, MagicMock
from datetime import datetime

from agents.orchestrator import (
    create_orchestrator_agent, 
    BeamSearchTool, 
    StateManagementTool, 
    ClientCommunicationTool,
    create_orchestrator_tasks
)
from agents.budgeting import (
    create_budgeting_agent,
    create_budget_allocation_task,
    create_fitness_calculation_task,
    BudgetingAgentCoordinator
)
from agents.sourcing import create_sourcing_agent
from agents.timeline import create_timeline_agent
from agents.blueprint import create_blueprint_agent


class TestOrchestratorAgent:
    """Test Orchestrator Agent functionality"""
    
    def test_orchestrator_agent_creation(self):
        """Test that orchestrator agent can be created with proper configuration"""
        agent = create_orchestrator_agent()
        
        assert agent.role == "Event Planning Coordinator"
        assert "optimal event combinations" in agent.goal
        assert agent.verbose is True
        assert agent.allow_delegation is True
        assert len(agent.tools) == 3
        assert agent.max_iter == 10
        assert agent.memory is True
    
    def test_beam_search_tool_initialization(self):
        """Test BeamSearchTool initialization and configuration"""
        tool = BeamSearchTool()
        
        assert tool.name == "Beam Search Optimization Tool"
        assert "beam search algorithm" in tool.description
        assert hasattr(tool, 'args_schema')
    
    def test_beam_search_combination_scoring(self):
        """Test beam search combination scoring logic"""
        tool = BeamSearchTool()
        
        # Test combination with good budget compliance
        combination = {
            'vendors': {
                'venue': {
                    'rental_cost': 300000,
                    'location_city': 'Bangalore',
                    'venue_type': 'Hotel',
                    'max_seating_capacity': 300
                },
                'caterer': {
                    'min_veg_price': 800,
                    'location_city': 'Bangalore',
                    'attributes': {'cuisines': ['Indian', 'Continental']}
                }
            },
            'budget_allocation': {
                'venue': 350000,
                'caterer': 200000
            }
        }
        
        client_requirements = {
            'guestCount': {'Reception': 250},
            'clientVision': 'Modern wedding in Bangalore',
            'venuePreferences': ['Hotel'],
            'foodAndCatering': {'cuisinePreferences': ['Indian']}
        }
        
        score = tool._calculate_combination_score(combination, client_requirements)
        
        assert 0 <= score <= 1
        assert score > 0.5  # Should be a decent score given good matches
    
    def test_beam_search_execution(self):
        """Test beam search tool execution with multiple combinations"""
        tool = BeamSearchTool()
        
        combinations = [
            {
                'vendors': {
                    'venue': {'rental_cost': 300000, 'location_city': 'Bangalore'},
                    'caterer': {'min_veg_price': 800, 'location_city': 'Bangalore'}
                },
                'budget_allocation': {'venue': 350000, 'caterer': 200000}
            },
            {
                'vendors': {
                    'venue': {'rental_cost': 500000, 'location_city': 'Mumbai'},
                    'caterer': {'min_veg_price': 1200, 'location_city': 'Mumbai'}
                },
                'budget_allocation': {'venue': 350000, 'caterer': 200000}
            }
        ]
        
        client_requirements = {
            'guestCount': {'Reception': 250},
            'clientVision': 'Wedding in Bangalore'
        }
        
        result = tool._run(combinations, client_requirements, beam_width=2)
        result_data = json.loads(result)
        
        assert result_data['beam_width'] == 2
        assert result_data['total_evaluated'] == 2
        assert len(result_data['top_combinations']) <= 2
        assert 'score_range' in result_data
        assert 'recommendations' in result_data
    
    def test_state_management_tool_operations(self):
        """Test state management tool operations"""
        tool = StateManagementTool()
        
        test_state = {
            'workflow_id': 'test_123',
            'current_step': 'vendor_sourcing',
            'beam_candidates': []
        }
        
        # Test save operation
        save_result = tool._run(test_state, 'save', 'test_workflow')
        save_data = json.loads(save_result)
        assert save_data['success'] is True
        assert save_data['action'] == 'save'
        
        # Test load operation
        load_result = tool._run({}, 'load', 'test_workflow')
        load_data = json.loads(load_result)
        assert load_data['success'] is True
        assert load_data['workflow_state'] == test_state
        
        # Test update operation
        update_state = {'current_step': 'budget_allocation'}
        update_result = tool._run(update_state, 'update', 'test_workflow')
        update_data = json.loads(update_result)
        assert update_data['success'] is True
        
        # Test reset operation
        reset_result = tool._run({}, 'reset', 'test_workflow')
        reset_data = json.loads(reset_result)
        assert reset_data['success'] is True
    
    def test_client_communication_tool_status_update(self):
        """Test client communication tool status update formatting"""
        tool = ClientCommunicationTool()
        
        content = {
            'current_status': 'Processing vendor options',
            'completed_steps': ['Budget allocation', 'Vendor sourcing'],
            'current_step': 'Combination optimization',
            'next_steps': ['Client presentation']
        }
        
        client_context = {
            'clientName': 'John Doe',
            'clientId': 'client_123'
        }
        
        result = tool._run('status_update', content, client_context)
        result_data = json.loads(result)
        
        assert result_data['message_type'] == 'status_update'
        assert result_data['delivery_status'] == 'ready_for_delivery'
        assert 'John Doe' in result_data['formatted_message']['greeting']
        assert 'progress' in result_data['formatted_message']
    
    def test_client_communication_tool_options_presentation(self):
        """Test client communication tool options presentation formatting"""
        tool = ClientCommunicationTool()
        
        content = {
            'vendor_combinations': [
                {
                    'score': 0.85,
                    'combination': {
                        'vendors': {
                            'venue': {'name': 'Grand Hotel', 'rental_cost': 300000, 'location_city': 'Bangalore'},
                            'caterer': {'name': 'Delicious Catering', 'min_veg_price': 800, 'location_city': 'Bangalore'}
                        },
                        'budget_allocation': {'venue': 350000, 'caterer': 200000}
                    }
                }
            ]
        }
        
        client_context = {
            'clientName': 'Jane Smith',
            'guestCount': {'Reception': 250}
        }
        
        result = tool._run('options_presentation', content, client_context)
        result_data = json.loads(result)
        
        assert result_data['message_type'] == 'options_presentation'
        assert 'Jane Smith' in result_data['formatted_message']['greeting']
        assert len(result_data['formatted_message']['options']) > 0
        assert 'selection_instructions' in result_data['formatted_message']
    
    def test_orchestrator_tasks_creation(self):
        """Test orchestrator tasks creation"""
        client_data = {
            'clientName': 'Test Client',
            'guestCount': {'Reception': 200},
            'clientVision': 'Modern elegant wedding',
            'budget': 1000000
        }
        
        tasks = create_orchestrator_tasks(client_data)
        
        assert len(tasks) == 3
        assert 'Initialize the event planning workflow' in tasks[0].description
        assert 'beam search optimization' in tasks[1].description
        assert 'Present optimized vendor combinations' in tasks[2].description


class TestBudgetingAgent:
    """Test Budgeting Agent functionality"""
    
    def test_budgeting_agent_creation(self):
        """Test that budgeting agent can be created with proper configuration"""
        agent = create_budgeting_agent()
        
        assert agent.role == "Financial Optimization Specialist"
        assert "budget allocation" in agent.goal
        assert agent.verbose is True
        assert agent.allow_delegation is False
        assert len(agent.tools) == 2
        assert agent.max_iter == 5
        assert agent.memory is True
    
    def test_budget_allocation_task_creation(self):
        """Test budget allocation task creation"""
        client_requirements = {
            'clientName': 'Test Client',
            'guestCount': {'Reception': 300},
            'clientVision': 'Luxury wedding celebration'
        }
        
        task = create_budget_allocation_task(client_requirements, 1500000)
        
        assert '₹1,500,000' in task.description
        assert 'Guest Count: 300' in task.description
        assert 'luxury wedding' in task.description.lower()
        assert 'BudgetAllocationTool' in str(task.tools)
    
    def test_fitness_calculation_task_creation(self):
        """Test fitness calculation task creation"""
        vendor_combinations = [
            {'vendors': {'venue': {}, 'caterer': {}}},
            {'vendors': {'venue': {}, 'caterer': {}}}
        ]
        
        client_requirements = {
            'clientVision': 'Modern elegant wedding'
        }
        
        budget_allocation = {
            'strategy': 'balanced'
        }
        
        task = create_fitness_calculation_task(
            vendor_combinations, client_requirements, budget_allocation
        )
        
        assert 'Number of Combinations: 2' in task.description
        assert 'Modern elegant wedding' in task.description
        assert 'FitnessCalculationTool' in str(task.tools)
    
    def test_budgeting_agent_coordinator_initialization(self):
        """Test BudgetingAgentCoordinator initialization"""
        coordinator = BudgetingAgentCoordinator()
        
        assert coordinator.agent is not None
        assert coordinator.mcp_integration_enabled is False
        assert hasattr(coordinator, 'generate_budget_strategies')
        assert hasattr(coordinator, 'calculate_combination_fitness')
    
    def test_budgeting_agent_coordinator_budget_strategies(self):
        """Test budget strategy generation"""
        coordinator = BudgetingAgentCoordinator()
        
        client_requirements = {
            'guestCount': {'Reception': 250},
            'clientVision': 'Modern wedding in Bangalore'
        }
        
        result = coordinator.generate_budget_strategies(client_requirements, 1000000)
        
        assert result['total_budget'] == 1000000
        assert 'event_type' in result
        assert 'allocation_strategies' in result
        assert len(result['allocation_strategies']) > 0
        assert 'recommended_strategy' in result
    
    def test_budgeting_agent_coordinator_fitness_calculation(self):
        """Test fitness calculation for vendor combinations"""
        coordinator = BudgetingAgentCoordinator()
        
        vendor_combinations = [
            {
                'vendors': {
                    'venue': {'rental_cost': 300000, 'location_city': 'Bangalore'},
                    'caterer': {'min_veg_price': 800, 'location_city': 'Bangalore'}
                }
            }
        ]
        
        client_requirements = {
            'guestCount': {'Reception': 250},
            'clientVision': 'Wedding in Bangalore'
        }
        
        budget_allocation = {
            'allocation': {'venue': 350000, 'caterer': 200000}
        }
        
        result = coordinator.calculate_combination_fitness(
            vendor_combinations, client_requirements, budget_allocation
        )
        
        assert len(result) == 1
        assert 'fitness_analysis' in result[0]
        assert 'overall_fitness_score' in result[0]
        assert 0 <= result[0]['overall_fitness_score'] <= 1
    
    def test_budgeting_agent_coordinator_performance_metrics(self):
        """Test performance metrics retrieval"""
        coordinator = BudgetingAgentCoordinator()
        
        metrics = coordinator.get_agent_performance_metrics()
        
        assert metrics['agent_type'] == 'budgeting'
        assert metrics['llm_model'] == 'gemma:2b'
        assert 'BudgetAllocationTool' in metrics['tools_available']
        assert 'FitnessCalculationTool' in metrics['tools_available']
        assert 'calculateFitnessScore' in metrics['preserved_algorithms']


class TestSourcingAgent:
    """Test Sourcing Agent functionality"""
    
    @patch('agents.sourcing.OllamaLLM')
    def test_sourcing_agent_creation(self, mock_llm):
        """Test that sourcing agent can be created with proper configuration"""
        mock_llm.return_value = Mock()
        
        agent = create_sourcing_agent()
        
        assert agent.role == "Vendor Sourcing Specialist"
        assert "find and rank optimal vendors" in agent.goal.lower()
        assert agent.verbose is True
        assert agent.allow_delegation is False
        assert len(agent.tools) >= 2  # Should have vendor tools
        assert agent.max_iter == 8
        assert agent.memory is True
        
        # Verify TinyLLaMA model is used
        mock_llm.assert_called_with(model="tinyllama")


class TestTimelineAgent:
    """Test Timeline Agent functionality"""
    
    @patch('agents.timeline.OllamaLLM')
    def test_timeline_agent_creation(self, mock_llm):
        """Test that timeline agent can be created with proper configuration"""
        mock_llm.return_value = Mock()
        
        agent = create_timeline_agent()
        
        assert agent.role == "Event Logistics Coordinator"
        assert "logistical feasibility" in agent.goal.lower()
        assert agent.verbose is True
        assert agent.allow_delegation is False
        assert len(agent.tools) >= 1  # Should have timeline tools
        assert agent.max_iter == 6
        assert agent.memory is True


class TestBlueprintAgent:
    """Test Blueprint Agent functionality"""
    
    @patch('agents.blueprint.OllamaLLM')
    def test_blueprint_agent_creation(self, mock_llm):
        """Test that blueprint agent can be created with proper configuration"""
        mock_llm.return_value = Mock()
        
        agent = create_blueprint_agent()
        
        assert agent.role == "Event Documentation Specialist"
        assert "comprehensive event blueprints" in agent.goal.lower()
        assert agent.verbose is True
        assert agent.allow_delegation is False
        assert len(agent.tools) >= 1  # Should have blueprint tools
        assert agent.max_iter == 4
        assert agent.memory is True


class TestAgentIntegration:
    """Test agent integration and workflow compatibility"""
    
    def test_agent_tool_compatibility(self):
        """Test that agents have compatible tools for workflow integration"""
        orchestrator = create_orchestrator_agent()
        budgeting = create_budgeting_agent()
        
        # Check that orchestrator has coordination tools
        orchestrator_tool_names = [tool.name for tool in orchestrator.tools]
        assert "Beam Search Optimization Tool" in orchestrator_tool_names
        assert "Workflow State Management Tool" in orchestrator_tool_names
        assert "Client Communication Tool" in orchestrator_tool_names
        
        # Check that budgeting agent has financial tools
        budgeting_tool_names = [tool.name for tool in budgeting.tools]
        assert "Budget Allocation Tool" in budgeting_tool_names
        assert "Fitness Score Calculation Tool" in budgeting_tool_names
    
    def test_agent_llm_configuration(self):
        """Test that agents use appropriate LLM models"""
        orchestrator = create_orchestrator_agent()
        budgeting = create_budgeting_agent()
        
        # Both should use Gemma-2B for complex reasoning
        assert hasattr(orchestrator, 'llm')
        assert hasattr(budgeting, 'llm')
    
    @patch('agents.orchestrator.OllamaLLM')
    @patch('agents.budgeting.OllamaLLM')
    def test_agent_workflow_simulation(self, mock_budgeting_llm, mock_orchestrator_llm):
        """Test simulated workflow between agents"""
        # Mock LLM responses
        mock_orchestrator_llm.return_value = Mock()
        mock_budgeting_llm.return_value = Mock()
        
        # Create agents
        orchestrator = create_orchestrator_agent()
        budgeting = create_budgeting_agent()
        
        # Simulate workflow data
        client_data = {
            'clientName': 'Test Client',
            'guestCount': {'Reception': 200},
            'clientVision': 'Modern elegant wedding',
            'budget': 800000
        }
        
        # Test orchestrator task creation
        orchestrator_tasks = create_orchestrator_tasks(client_data)
        assert len(orchestrator_tasks) == 3
        
        # Test budgeting task creation
        budget_task = create_budget_allocation_task(client_data, 800000)
        assert '₹800,000' in budget_task.description
        
        # Verify task compatibility
        assert orchestrator_tasks[0].agent is None  # Will be assigned to orchestrator
        assert budget_task.agent is None  # Will be assigned to budgeting agent
    
    def test_error_handling_in_agents(self):
        """Test error handling capabilities in agent tools"""
        # Test BeamSearchTool with empty combinations
        beam_tool = BeamSearchTool()
        result = beam_tool._run([], {}, beam_width=3)
        result_data = json.loads(result)
        
        assert result_data['total_evaluated'] == 0
        assert 'No combinations provided' in result_data['message']
        
        # Test StateManagementTool with invalid action
        state_tool = StateManagementTool()
        result = state_tool._run({}, 'invalid_action', 'test')
        result_data = json.loads(result)
        
        assert result_data['success'] is False
        assert 'Unknown action' in result_data['message']
        
        # Test ClientCommunicationTool with invalid message type
        comm_tool = ClientCommunicationTool()
        result = comm_tool._run('invalid_type', {}, {})
        result_data = json.loads(result)
        
        assert 'error' in result_data
        assert 'Unknown message type' in result_data['error']


if __name__ == "__main__":
    # Run basic agent tests
    print("Running CrewAI Agent Tests...")
    
    # Test agent creation
    try:
        orchestrator = create_orchestrator_agent()
        budgeting = create_budgeting_agent()
        print("✅ Successfully created orchestrator and budgeting agents")
    except Exception as e:
        print(f"❌ Agent creation failed: {e}")
        exit(1)
    
    # Test tool functionality
    try:
        beam_tool = BeamSearchTool()
        state_tool = StateManagementTool()
        comm_tool = ClientCommunicationTool()
        
        # Test basic tool operations
        test_combinations = [
            {
                'vendors': {'venue': {'rental_cost': 300000}},
                'budget_allocation': {'venue': 350000}
            }
        ]
        
        beam_result = beam_tool._run(test_combinations, {'guestCount': {'Reception': 200}})
        assert '"top_combinations"' in beam_result
        
        state_result = state_tool._run({'test': 'data'}, 'save', 'test_key')
        assert '"success": true' in state_result
        
        comm_result = comm_tool._run('status_update', {'current_status': 'Testing'}, {'clientName': 'Test'})
        assert '"message_type": "status_update"' in comm_result
        
        print("✅ Agent tools working correctly")
        
    except Exception as e:
        print(f"❌ Tool testing failed: {e}")
        exit(1)
    
    print("🎉 All basic agent tests passed!")