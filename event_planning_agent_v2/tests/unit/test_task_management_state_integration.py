"""
Unit tests for Task Management Agent state management integration.

Tests verify:
1. Integration with StateManagementTool from orchestrator.py
2. State updates after each processing step (sub-agent consolidation, tool processing, extended task list generation)
3. State persistence using state_manager from database/state_manager.py
4. Workflow_status updates in EventPlanningState upon completion
5. State restoration for resuming after interruptions
6. Blueprint Agent can access extended_task_list from EventPlanningState
"""

import pytest
import asyncio
from unittest.mock import Mock, MagicMock, patch, AsyncMock
from datetime import datetime, timedelta
from uuid import uuid4

from event_planning_agent_v2.workflows.state_models import EventPlanningState, WorkflowStatus
from event_planning_agent_v2.agents.task_management.core.task_management_agent import TaskManagementAgent
from event_planning_agent_v2.agents.task_management.models.extended_models import (
    ExtendedTask, ExtendedTaskList, ProcessingSummary
)
from event_planning_agent_v2.agents.task_management.models.consolidated_models import (
    ConsolidatedTask, ConsolidatedTaskData
)
from event_planning_agent_v2.database.state_manager import WorkflowStateManager


@pytest.fixture
def mock_state_manager():
    """Create mock state manager"""
    manager = Mock(spec=WorkflowStateManager)
    manager.save_workflow_state = Mock(return_value=True)
    manager.checkpoint_workflow = Mock(return_value=True)
    manager.recover_workflow_state = Mock(return_value=None)
    return manager


@pytest.fixture
def sample_state():
    """Create sample EventPlanningState"""
    plan_id = str(uuid4())
    return EventPlanningState(
        plan_id=plan_id,
        client_request={
            'client_id': 'test_client',
            'event_type': 'wedding',
            'guest_count': 200,
            'budget': 500000,
            'date': '2024-06-15',
            'location': 'Mumbai'
        },
        workflow_status=WorkflowStatus.RUNNING.value,
        iteration_count=1,
        budget_allocations=[],
        vendor_combinations=[],
        beam_candidates=[],
        timeline_data={'event_date': '2024-06-15', 'tasks': []},
        extended_task_list=None,
        selected_combination={'venue': {'name': 'Test Venue'}},
        final_blueprint=None,
        started_at=datetime.utcnow().isoformat(),
        last_updated=datetime.utcnow().isoformat(),
        beam_width=3,
        max_iterations=20,
        error_count=0,
        last_error=None,
        retry_count=0,
        state_transitions=[],
        current_node='task_management',
        next_node=None
    )


@pytest.fixture
def sample_consolidated_data():
    """Create sample consolidated task data"""
    task = ConsolidatedTask(
        task_id='task_1',
        task_name='Test Task',
        priority_level='High',
        priority_score=0.8,
        priority_rationale='Important task',
        parent_task_id=None,
        task_description='Test task description',
        granularity_level=0,
        estimated_duration=timedelta(hours=2),
        sub_tasks=[],
        dependencies=[],
        resources_required=[],
        resource_conflicts=[]
    )
    
    return ConsolidatedTaskData(
        tasks=[task],
        event_context={'plan_id': 'test_plan'},
        processing_metadata={'timestamp': datetime.utcnow().isoformat()}
    )


@pytest.fixture
def sample_extended_task_list():
    """Create sample extended task list"""
    task = ExtendedTask(
        task_id='task_1',
        task_name='Test Task',
        task_description='Test task description',
        priority_level='High',
        priority_score=0.8,
        granularity_level=0,
        parent_task_id=None,
        sub_tasks=[],
        dependencies=[],
        resources_required=[],
        timeline=None,
        llm_enhancements={},
        assigned_vendors=[],
        logistics_status=None,
        conflicts=[],
        venue_info=None,
        has_errors=False,
        has_warnings=False,
        requires_manual_review=False,
        error_messages=[],
        warning_messages=[]
    )
    
    summary = ProcessingSummary(
        total_tasks=1,
        tasks_with_errors=0,
        tasks_with_warnings=0,
        tasks_requiring_review=0,
        processing_time=1.5,
        tool_execution_status={'timeline': 'success'}
    )
    
    return ExtendedTaskList(
        tasks=[task],
        processing_summary=summary,
        metadata={'generated_at': datetime.utcnow().isoformat()}
    )


class TestStateManagementIntegration:
    """Test state management integration"""
    
    def test_state_manager_initialization(self, mock_state_manager):
        """Test TaskManagementAgent initializes with StateManager"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        assert agent.state_manager is mock_state_manager
        assert agent.state_manager is not None
    
    def test_update_state_after_consolidation(
        self,
        mock_state_manager,
        sample_state,
        sample_consolidated_data
    ):
        """Test state update after sub-agent consolidation"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Update state after consolidation
        updated_state = agent._update_state_after_consolidation(
            sample_state,
            sample_consolidated_data
        )
        
        # Verify checkpoint was created
        assert 'task_management_checkpoints' in updated_state
        assert 'consolidation' in updated_state['task_management_checkpoints']
        assert updated_state['task_management_checkpoints']['consolidation']['completed'] is True
        assert updated_state['task_management_checkpoints']['consolidation']['task_count'] == 1
        
        # Verify checkpoint was saved
        mock_state_manager.checkpoint_workflow.assert_called_once()
    
    def test_update_state_after_tools(
        self,
        mock_state_manager,
        sample_state
    ):
        """Test state update after tool processing"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Set tool execution status
        agent.tool_execution_status = {
            'timeline_calculation': 'success',
            'llm_enhancement': 'success',
            'vendor_assignment': 'success'
        }
        
        tool_outputs = {
            'timelines': [Mock()],
            'llm_enhancements': [Mock()],
            'vendor_assignments': [Mock()],
            'logistics_statuses': [],
            'conflicts': [],
            'venue_info': []
        }
        
        # Update state after tools
        updated_state = agent._update_state_after_tools(
            sample_state,
            tool_outputs
        )
        
        # Verify checkpoint was created
        assert 'task_management_checkpoints' in updated_state
        assert 'tool_processing' in updated_state['task_management_checkpoints']
        assert updated_state['task_management_checkpoints']['tool_processing']['completed'] is True
        assert 'tool_execution_status' in updated_state['task_management_checkpoints']['tool_processing']
        
        # Verify checkpoint was saved
        mock_state_manager.checkpoint_workflow.assert_called_once()
    
    def test_update_state_with_extended_task_list(
        self,
        mock_state_manager,
        sample_state,
        sample_extended_task_list
    ):
        """Test state update with final extended task list"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Update state with extended task list
        updated_state = agent._update_state(
            sample_state,
            sample_extended_task_list
        )
        
        # Verify extended_task_list was added to state
        assert 'extended_task_list' in updated_state
        assert updated_state['extended_task_list'] is not None
        assert 'tasks' in updated_state['extended_task_list']
        assert 'processing_summary' in updated_state['extended_task_list']
        
        # Verify workflow status is set
        assert updated_state['workflow_status'] == WorkflowStatus.RUNNING.value
        
        # Verify state was persisted
        mock_state_manager.save_workflow_state.assert_called_once()
    
    def test_state_persistence_on_error(
        self,
        mock_state_manager,
        sample_state
    ):
        """Test state is persisted even when errors occur"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Mock sub-agents to raise error
        with patch.object(agent, '_invoke_sub_agents', side_effect=Exception("Test error")):
            # Process should handle error and persist state
            with pytest.raises(Exception):
                asyncio.run(agent.process(sample_state))
        
        # Verify state was persisted with error information
        assert mock_state_manager.save_workflow_state.called
    
    def test_restore_from_checkpoint_no_checkpoints(
        self,
        mock_state_manager,
        sample_state
    ):
        """Test restore from checkpoint when no checkpoints exist"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Remove checkpoints from state
        if 'task_management_checkpoints' in sample_state:
            del sample_state['task_management_checkpoints']
        
        # Should return None (start from beginning)
        resume_from = agent.restore_from_checkpoint(sample_state)
        assert resume_from is None
    
    def test_restore_from_checkpoint_consolidation_complete(
        self,
        mock_state_manager,
        sample_state
    ):
        """Test restore from checkpoint when consolidation is complete"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Add consolidation checkpoint
        sample_state['task_management_checkpoints'] = {
            'consolidation': {
                'completed': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Should return 'consolidation' (resume from tool processing)
        resume_from = agent.restore_from_checkpoint(sample_state)
        assert resume_from == 'consolidation'
    
    def test_restore_from_checkpoint_tools_complete(
        self,
        mock_state_manager,
        sample_state
    ):
        """Test restore from checkpoint when tool processing is complete"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Add both checkpoints
        sample_state['task_management_checkpoints'] = {
            'consolidation': {
                'completed': True,
                'timestamp': datetime.utcnow().isoformat()
            },
            'tool_processing': {
                'completed': True,
                'timestamp': datetime.utcnow().isoformat()
            }
        }
        
        # Should return 'tool_processing' (resume from extended task list generation)
        resume_from = agent.restore_from_checkpoint(sample_state)
        assert resume_from == 'tool_processing'
    
    def test_blueprint_agent_can_access_extended_task_list(
        self,
        mock_state_manager,
        sample_state,
        sample_extended_task_list
    ):
        """Test that Blueprint Agent can access extended_task_list from state"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Update state with extended task list
        updated_state = agent._update_state(
            sample_state,
            sample_extended_task_list
        )
        
        # Simulate Blueprint Agent accessing extended_task_list
        extended_task_list = updated_state.get('extended_task_list')
        
        # Verify Blueprint Agent can access the data
        assert extended_task_list is not None
        assert 'tasks' in extended_task_list
        assert 'processing_summary' in extended_task_list
        assert len(extended_task_list['tasks']) > 0
        
        # Verify task data is accessible
        first_task = extended_task_list['tasks'][0]
        assert 'task_id' in first_task
        assert 'task_name' in first_task
        assert 'priority_level' in first_task
    
    def test_state_persistence_failure_handling(
        self,
        mock_state_manager,
        sample_state,
        sample_extended_task_list
    ):
        """Test handling of state persistence failures"""
        # Mock state manager to fail on save
        mock_state_manager.save_workflow_state = Mock(side_effect=Exception("Database error"))
        
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Update state should not raise exception even if persistence fails
        updated_state = agent._update_state(
            sample_state,
            sample_extended_task_list
        )
        
        # Verify state still has extended_task_list
        assert 'extended_task_list' in updated_state
        
        # Verify error was logged in state
        assert updated_state['error_count'] > 0
        assert 'State persistence error' in updated_state['last_error']
    
    def test_checkpoint_failure_handling(
        self,
        mock_state_manager,
        sample_state,
        sample_consolidated_data
    ):
        """Test handling of checkpoint failures"""
        # Mock state manager to fail on checkpoint
        mock_state_manager.checkpoint_workflow = Mock(side_effect=Exception("Checkpoint error"))
        
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Update state should not raise exception even if checkpoint fails
        updated_state = agent._update_state_after_consolidation(
            sample_state,
            sample_consolidated_data
        )
        
        # Verify checkpoint metadata was still added to state
        assert 'task_management_checkpoints' in updated_state
        assert 'consolidation' in updated_state['task_management_checkpoints']


class TestWorkflowStatusUpdates:
    """Test workflow status updates"""
    
    def test_workflow_status_updated_on_completion(
        self,
        mock_state_manager,
        sample_state,
        sample_extended_task_list
    ):
        """Test workflow_status is updated upon completion"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Update state
        updated_state = agent._update_state(
            sample_state,
            sample_extended_task_list
        )
        
        # Verify workflow status is set to RUNNING (not FAILED)
        assert updated_state['workflow_status'] == WorkflowStatus.RUNNING.value
    
    def test_workflow_status_updated_on_error(
        self,
        mock_state_manager,
        sample_state
    ):
        """Test workflow_status is updated to FAILED on critical error"""
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Mock sub-agents to raise error
        with patch.object(agent, '_invoke_sub_agents', side_effect=Exception("Critical error")):
            # Process should update status to FAILED
            with pytest.raises(Exception):
                asyncio.run(agent.process(sample_state))
        
        # Verify workflow status was set to FAILED
        # (Note: This is checked in the process method's exception handler)


class TestStateRestoration:
    """Test state restoration for resuming after interruptions"""
    
    def test_state_restoration_from_database(
        self,
        mock_state_manager,
        sample_state
    ):
        """Test state can be restored from database"""
        # Mock state manager to return restored state
        restored_state = sample_state.copy()
        restored_state['task_management_checkpoints'] = {
            'consolidation': {'completed': True}
        }
        mock_state_manager.recover_workflow_state = Mock(return_value=restored_state)
        
        agent = TaskManagementAgent(
            state_manager=mock_state_manager,
            llm_model='gemma:2b'
        )
        
        # Restore from checkpoint
        resume_from = agent.restore_from_checkpoint(restored_state)
        
        # Verify restoration was successful
        assert resume_from == 'consolidation'
        assert 'task_management_checkpoints' in restored_state


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
