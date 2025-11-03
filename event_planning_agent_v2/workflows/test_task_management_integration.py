"""
Test Task Management Node Integration with LangGraph Workflow

This test verifies that the task management node is properly integrated
into the LangGraph workflow and can be executed correctly.
"""

import pytest
import asyncio
from typing import Dict, Any
from unittest.mock import Mock, patch, AsyncMock

from .task_management_node import (
    task_management_node,
    should_run_task_management
)
from .state_models import EventPlanningState, WorkflowStatus, create_initial_state
from .planning_workflow import create_event_planning_workflow


class TestTaskManagementNodeIntegration:
    """Test suite for task management node integration"""
    
    def test_should_run_task_management_with_timeline_data(self):
        """Test that task management runs when timeline data is present"""
        state: EventPlanningState = {
            'plan_id': 'test-plan-123',
            'timeline_data': {'tasks': []},
            'workflow_status': WorkflowStatus.RUNNING.value,
            'client_request': {},
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'extended_task_list': None,
            'selected_combination': None,
            'final_blueprint': None,
            'started_at': '2025-01-01T00:00:00',
            'last_updated': '2025-01-01T00:00:00',
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': None,
            'next_node': None
        }
        
        result = should_run_task_management(state)
        assert result is True
    
    def test_should_skip_task_management_without_timeline_data(self):
        """Test that task management is skipped when timeline data is missing"""
        state: EventPlanningState = {
            'plan_id': 'test-plan-123',
            'timeline_data': None,
            'workflow_status': WorkflowStatus.RUNNING.value,
            'client_request': {},
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'extended_task_list': None,
            'selected_combination': None,
            'final_blueprint': None,
            'started_at': '2025-01-01T00:00:00',
            'last_updated': '2025-01-01T00:00:00',
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': None,
            'next_node': None
        }
        
        result = should_run_task_management(state)
        assert result is False
    
    def test_should_skip_task_management_when_failed(self):
        """Test that task management is skipped when workflow is failed"""
        state: EventPlanningState = {
            'plan_id': 'test-plan-123',
            'timeline_data': {'tasks': []},
            'workflow_status': WorkflowStatus.FAILED.value,
            'client_request': {},
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'extended_task_list': None,
            'selected_combination': None,
            'final_blueprint': None,
            'started_at': '2025-01-01T00:00:00',
            'last_updated': '2025-01-01T00:00:00',
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': None,
            'next_node': None
        }
        
        result = should_run_task_management(state)
        assert result is False
    
    @patch('event_planning_agent_v2.workflows.task_management_node.TaskManagementAgent')
    @patch('event_planning_agent_v2.workflows.task_management_node.get_state_manager')
    def test_task_management_node_skips_without_timeline(
        self,
        mock_get_state_manager,
        mock_task_agent_class
    ):
        """Test that node skips processing when timeline data is missing"""
        # Create state without timeline data
        state: EventPlanningState = {
            'plan_id': 'test-plan-123',
            'timeline_data': None,
            'workflow_status': WorkflowStatus.RUNNING.value,
            'client_request': {},
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'extended_task_list': None,
            'selected_combination': None,
            'final_blueprint': None,
            'started_at': '2025-01-01T00:00:00',
            'last_updated': '2025-01-01T00:00:00',
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': None,
            'next_node': None
        }
        
        # Execute node
        result = task_management_node(state)
        
        # Verify node was skipped
        assert result['next_node'] == 'blueprint_generation'
        assert mock_task_agent_class.call_count == 0  # Agent not instantiated
    
    @patch('event_planning_agent_v2.workflows.task_management_node.TaskManagementAgent')
    @patch('event_planning_agent_v2.workflows.task_management_node.get_state_manager')
    @patch('event_planning_agent_v2.workflows.task_management_node.asyncio.run')
    def test_task_management_node_processes_with_timeline(
        self,
        mock_asyncio_run,
        mock_get_state_manager,
        mock_task_agent_class
    ):
        """Test that node processes when timeline data is present"""
        # Create state with timeline data
        state: EventPlanningState = {
            'plan_id': 'test-plan-123',
            'timeline_data': {'tasks': [{'id': 'task-1', 'name': 'Test Task'}]},
            'selected_combination': {'combination_id': 'combo-1'},
            'workflow_status': WorkflowStatus.RUNNING.value,
            'client_request': {},
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'extended_task_list': None,
            'final_blueprint': None,
            'started_at': '2025-01-01T00:00:00',
            'last_updated': '2025-01-01T00:00:00',
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': None,
            'next_node': None
        }
        
        # Mock the agent's process method to return state with extended_task_list
        mock_agent_instance = Mock()
        mock_task_agent_class.return_value = mock_agent_instance
        
        # Mock asyncio.run to return state with extended_task_list
        processed_state = state.copy()
        processed_state['extended_task_list'] = {
            'tasks': [],
            'processing_summary': {
                'total_tasks': 1,
                'tasks_with_errors': 0,
                'tasks_with_warnings': 0,
                'processing_time': 1.5
            },
            'metadata': {}
        }
        mock_asyncio_run.return_value = processed_state
        
        # Mock state manager
        mock_state_manager = Mock()
        mock_get_state_manager.return_value = mock_state_manager
        
        # Execute node
        result = task_management_node(state)
        
        # Verify agent was instantiated
        assert mock_task_agent_class.call_count == 1
        
        # Verify asyncio.run was called
        assert mock_asyncio_run.call_count == 1
        
        # Verify next node is set
        assert result['next_node'] == 'blueprint_generation'
    
    def test_workflow_includes_task_management_node(self):
        """Test that the workflow graph includes the task management node"""
        workflow = create_event_planning_workflow()
        
        # Get the workflow nodes
        nodes = workflow.nodes
        
        # Verify task_management node exists
        assert 'task_management' in nodes
        
        # Verify the node is callable
        assert callable(nodes['task_management'])
    
    @patch('event_planning_agent_v2.workflows.task_management_node.TaskManagementAgent')
    @patch('event_planning_agent_v2.workflows.task_management_node.get_state_manager')
    def test_task_management_node_handles_errors_gracefully(
        self,
        mock_get_state_manager,
        mock_task_agent_class
    ):
        """Test that node handles errors without failing the workflow"""
        # Create state with timeline data
        state: EventPlanningState = {
            'plan_id': 'test-plan-123',
            'timeline_data': {'tasks': []},
            'workflow_status': WorkflowStatus.RUNNING.value,
            'client_request': {},
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'extended_task_list': None,
            'selected_combination': None,
            'final_blueprint': None,
            'started_at': '2025-01-01T00:00:00',
            'last_updated': '2025-01-01T00:00:00',
            'beam_width': 3,
            'max_iterations': 20,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0,
            'state_transitions': [],
            'current_node': None,
            'next_node': None
        }
        
        # Mock agent to raise an exception
        mock_task_agent_class.side_effect = Exception("Test error")
        
        # Execute node
        result = task_management_node(state)
        
        # Verify error was tracked
        assert result['error_count'] == 1
        assert 'Test error' in result['last_error']
        
        # Verify workflow continues to blueprint generation
        assert result['next_node'] == 'blueprint_generation'


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
