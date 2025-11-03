"""
Test suite for Task Management Agent error handling.

Tests error handling for:
- Sub-agent failures
- Tool execution failures
- Critical errors
- State updates and error tracking
"""

import pytest
from datetime import datetime
from unittest.mock import Mock, patch

from .error_handler import (
    TaskManagementErrorHandler,
    process_with_error_handling,
    handle_sub_agent_failure,
    handle_tool_failure,
    handle_critical_failure
)
from ..exceptions import SubAgentDataError, ToolExecutionError, TaskManagementError
from ....workflows.state_models import EventPlanningState, WorkflowStatus


def create_test_state() -> EventPlanningState:
    """Create a test EventPlanningState"""
    return EventPlanningState(
        plan_id="test-plan-123",
        client_request={
            'client_id': 'test-client',
            'event_type': 'wedding',
            'guest_count': 100,
            'budget': 50000
        },
        workflow_status=WorkflowStatus.RUNNING.value,
        iteration_count=0,
        budget_allocations=[],
        vendor_combinations=[],
        beam_candidates=[],
        timeline_data=None,
        extended_task_list=None,
        selected_combination=None,
        final_blueprint=None,
        started_at=datetime.utcnow().isoformat(),
        last_updated=datetime.utcnow().isoformat(),
        beam_width=3,
        max_iterations=20,
        error_count=0,
        last_error=None,
        retry_count=0,
        state_transitions=[],
        current_node=None,
        next_node=None
    )


class TestTaskManagementErrorHandler:
    """Test TaskManagementErrorHandler class"""
    
    def test_initialization(self):
        """Test error handler initialization"""
        handler = TaskManagementErrorHandler()
        
        assert handler.error_monitor is not None
        assert handler.transition_logger is not None
        assert handler.agent_error_handler is not None
        assert len(handler.sub_agent_errors) == 0
        assert len(handler.tool_errors) == 0
        assert len(handler.critical_errors) == 0
    
    def test_handle_sub_agent_error_with_partial_data(self):
        """Test handling sub-agent error with partial data"""
        handler = TaskManagementErrorHandler()
        state = create_test_state()
        error = SubAgentDataError("TestAgent", "Test error message")
        partial_data = [{"task_id": "task-1"}]
        
        should_continue, data = handler.handle_sub_agent_error(
            error=error,
            sub_agent_name="TestAgent",
            state=state,
            partial_data=partial_data
        )
        
        assert should_continue is True
        assert data == partial_data
        assert state['error_count'] == 1
        assert "TestAgent" in state['last_error']
        assert len(handler.sub_agent_errors) == 1
    
    def test_handle_sub_agent_error_without_partial_data(self):
        """Test handling sub-agent error without partial data"""
        handler = TaskManagementErrorHandler()
        state = create_test_state()
        error = SubAgentDataError("TestAgent", "Test error message")
        
        should_continue, data = handler.handle_sub_agent_error(
            error=error,
            sub_agent_name="TestAgent",
            state=state,
            partial_data=None
        )
        
        assert should_continue is True
        assert data is None
        assert state['error_count'] == 1
        assert len(handler.sub_agent_errors) == 1
    
    def test_handle_tool_error(self):
        """Test handling tool execution error"""
        handler = TaskManagementErrorHandler()
        state = create_test_state()
        error = ToolExecutionError("TestTool", "Test error message")
        affected_tasks = ["task-1", "task-2"]
        
        should_continue, error_metadata = handler.handle_tool_error(
            error=error,
            tool_name="TestTool",
            state=state,
            affected_tasks=affected_tasks
        )
        
        assert should_continue is True
        assert error_metadata['tool_name'] == "TestTool"
        assert 'error_message' in error_metadata
        assert state['error_count'] == 1
        assert "TestTool" in state['last_error']
        assert len(handler.tool_errors) == 1
    
    def test_handle_critical_error(self):
        """Test handling critical error"""
        handler = TaskManagementErrorHandler()
        state = create_test_state()
        error = TaskManagementError("Critical failure")
        
        updated_state = handler.handle_critical_error(
            error=error,
            state=state,
            operation="test_operation"
        )
        
        assert updated_state['workflow_status'] == WorkflowStatus.FAILED.value
        assert updated_state['error_count'] == 1
        assert "Critical error" in updated_state['last_error']
        assert len(handler.critical_errors) == 1
    
    def test_mark_tasks_with_errors(self):
        """Test marking tasks with error flags"""
        from ..models.extended_models import ExtendedTask
        
        handler = TaskManagementErrorHandler()
        
        # Create test tasks
        tasks = [
            ExtendedTask(
                task_id="task-1",
                task_name="Test Task 1",
                task_description="Description 1",
                priority_level="High",
                priority_score=0.9,
                granularity_level=1,
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
            ),
            ExtendedTask(
                task_id="task-2",
                task_name="Test Task 2",
                task_description="Description 2",
                priority_level="Medium",
                priority_score=0.7,
                granularity_level=1,
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
        ]
        
        error_metadata = {
            'tool_name': 'TestTool',
            'error_message': 'Test error',
            'error_type': 'TestError'
        }
        
        # Mark specific task
        updated_tasks = handler.mark_tasks_with_errors(
            tasks=tasks,
            error_metadata=error_metadata,
            affected_task_ids=["task-1"]
        )
        
        assert updated_tasks[0].has_errors is True
        assert len(updated_tasks[0].error_messages) == 1
        assert updated_tasks[0].requires_manual_review is True
        assert updated_tasks[1].has_errors is False
    
    def test_get_error_summary(self):
        """Test getting error summary"""
        handler = TaskManagementErrorHandler()
        state = create_test_state()
        
        # Add some errors
        handler.handle_sub_agent_error(
            SubAgentDataError("Agent1", "Error 1"),
            "Agent1",
            state
        )
        handler.handle_tool_error(
            ToolExecutionError("Tool1", "Error 2"),
            "Tool1",
            state
        )
        
        summary = handler.get_error_summary()
        
        assert summary['total_errors'] == 2
        assert summary['sub_agent_errors']['count'] == 1
        assert summary['tool_errors']['count'] == 1
        assert summary['critical_errors']['count'] == 0
    
    def test_reset_error_tracking(self):
        """Test resetting error tracking"""
        handler = TaskManagementErrorHandler()
        state = create_test_state()
        
        # Add some errors
        handler.handle_sub_agent_error(
            SubAgentDataError("Agent1", "Error 1"),
            "Agent1",
            state
        )
        
        assert len(handler.sub_agent_errors) == 1
        
        # Reset
        handler.reset_error_tracking()
        
        assert len(handler.sub_agent_errors) == 0
        assert len(handler.tool_errors) == 0
        assert len(handler.critical_errors) == 0


class TestConvenienceFunctions:
    """Test convenience functions"""
    
    def test_handle_sub_agent_failure(self):
        """Test handle_sub_agent_failure convenience function"""
        state = create_test_state()
        error = SubAgentDataError("TestAgent", "Test error")
        
        should_continue, partial_data = handle_sub_agent_failure(
            sub_agent_name="TestAgent",
            error=error,
            state=state
        )
        
        assert should_continue is True
        assert state['error_count'] == 1
    
    def test_handle_tool_failure(self):
        """Test handle_tool_failure convenience function"""
        state = create_test_state()
        error = ToolExecutionError("TestTool", "Test error")
        
        should_continue, error_metadata = handle_tool_failure(
            tool_name="TestTool",
            error=error,
            state=state
        )
        
        assert should_continue is True
        assert error_metadata['tool_name'] == "TestTool"
        assert state['error_count'] == 1
    
    def test_handle_critical_failure(self):
        """Test handle_critical_failure convenience function"""
        state = create_test_state()
        error = TaskManagementError("Critical error")
        
        updated_state = handle_critical_failure(
            error=error,
            state=state,
            operation="test_operation"
        )
        
        assert updated_state['workflow_status'] == WorkflowStatus.FAILED.value
        assert updated_state['error_count'] == 1


class TestProcessWithErrorHandlingDecorator:
    """Test process_with_error_handling decorator"""
    
    def test_decorator_success(self):
        """Test decorator with successful execution"""
        
        class TestAgent:
            def __init__(self):
                self.error_handler = TaskManagementErrorHandler()
            
            @process_with_error_handling
            def process(self, state: EventPlanningState) -> EventPlanningState:
                state['workflow_status'] = WorkflowStatus.COMPLETED.value
                return state
        
        agent = TestAgent()
        state = create_test_state()
        
        result = agent.process(state)
        
        assert result['workflow_status'] == WorkflowStatus.COMPLETED.value
    
    def test_decorator_sub_agent_error(self):
        """Test decorator with sub-agent error"""
        
        class TestAgent:
            def __init__(self):
                self.error_handler = TaskManagementErrorHandler()
            
            @process_with_error_handling
            def process(self, state: EventPlanningState) -> EventPlanningState:
                raise SubAgentDataError("TestAgent", "Test error")
        
        agent = TestAgent()
        state = create_test_state()
        
        result = agent.process(state)
        
        # Should continue with error logged
        assert result['error_count'] == 1
        assert "TestAgent" in result['last_error']
    
    def test_decorator_tool_error(self):
        """Test decorator with tool error"""
        
        class TestAgent:
            def __init__(self):
                self.error_handler = TaskManagementErrorHandler()
            
            @process_with_error_handling
            def process(self, state: EventPlanningState) -> EventPlanningState:
                raise ToolExecutionError("TestTool", "Test error")
        
        agent = TestAgent()
        state = create_test_state()
        
        result = agent.process(state)
        
        # Should continue with error logged
        assert result['error_count'] == 1
        assert "TestTool" in result['last_error']
    
    def test_decorator_critical_error(self):
        """Test decorator with critical error"""
        
        class TestAgent:
            def __init__(self):
                self.error_handler = TaskManagementErrorHandler()
            
            @process_with_error_handling
            def process(self, state: EventPlanningState) -> EventPlanningState:
                raise TaskManagementError("Critical error")
        
        agent = TestAgent()
        state = create_test_state()
        
        result = agent.process(state)
        
        # Should fail workflow
        assert result['workflow_status'] == WorkflowStatus.FAILED.value
        assert result['error_count'] == 1


if __name__ == "__main__":
    # Run tests
    pytest.main([__file__, "-v"])
