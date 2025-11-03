# Task Management Agent Error Handling

## Overview

The Task Management Agent implements comprehensive error handling and recovery mechanisms to ensure robust operation even when sub-agents or tools fail. The error handling system integrates with the existing error handling infrastructure from `error_handling/handlers.py` and `error_handling/monitoring.py`.

## Architecture

### Components

1. **TaskManagementErrorHandler** (`error_handler.py`)
   - Main error handling class
   - Handles sub-agent errors, tool errors, and critical failures
   - Integrates with error monitoring and state transition logging
   - Tracks error statistics and provides summaries

2. **Error Handler Integration** (`task_management_agent.py`)
   - `process_with_error_handling()` - Main entry point with error handling
   - `process()` - Core processing method
   - Error handling in `_invoke_sub_agents()` and `_process_tools()`

3. **Error Monitoring Integration**
   - Uses `get_error_monitor()` from `error_handling/monitoring.py`
   - Records errors with correlation IDs for tracking
   - Provides health reports and error summaries

4. **State Transition Logging**
   - Uses `StateTransitionLogger` from `workflows/state_models.py`
   - Logs all error-related state transitions
   - Tracks error count and last_error in EventPlanningState

## Error Types

### 1. Sub-Agent Errors

**Handling Strategy**: Continue with partial data

Sub-agent errors occur when one of the three sub-agents (Prioritization, Granularity, or Resource & Dependency) fails to process tasks.

**Behavior**:
- Error is logged to monitoring system
- State error_count is incremented
- State last_error is updated
- Processing continues with empty data for that sub-agent
- Other sub-agents continue to execute

**Example**:
```python
try:
    prioritized_tasks = await self.prioritization_agent.prioritize_tasks(state)
except Exception as e:
    should_continue, partial_data = self.error_handler.handle_sub_agent_error(
        error=e,
        sub_agent_name="PrioritizationAgent",
        state=state,
        partial_data=None
    )
    # Continue with empty list
```

### 2. Tool Execution Errors

**Handling Strategy**: Mark affected tasks and continue

Tool errors occur when one of the six tools (Timeline, LLM, Vendor, Logistics, Conflict, Venue) fails during processing.

**Behavior**:
- Error is logged to monitoring system
- State error_count is incremented
- State last_error is updated
- Affected tasks are identified
- Processing continues with remaining tools
- Tasks are marked with error flags in final output

**Example**:
```python
try:
    timelines = self.timeline_tool.calculate_timelines(consolidated_data, state)
except Exception as e:
    should_continue, error_metadata = self.error_handler.handle_tool_error(
        error=e,
        tool_name="TimelineCalculationTool",
        state=state,
        affected_tasks=[task.task_id for task in consolidated_data.tasks]
    )
    # Continue without timeline data
```

### 3. Critical Errors

**Handling Strategy**: Terminate workflow with FAILED status

Critical errors are unrecoverable failures that require workflow termination.

**Examples**:
- Database connection failures
- State management failures
- All sub-agents returning empty data
- Consolidation failures

**Behavior**:
- Error is logged to monitoring system as critical
- State workflow_status is set to FAILED
- State error_count is incremented
- State last_error is updated with detailed message
- State transition is logged to FAILED status
- Workflow is terminated

**Example**:
```python
try:
    # Critical operation
    consolidated_data = self._consolidate_data(...)
except Exception as e:
    return self.error_handler.handle_critical_error(
        error=e,
        state=state,
        operation="data_consolidation"
    )
```

## Usage

### Primary Entry Point

Always use `process_with_error_handling()` as the main entry point:

```python
# In workflow node
async def task_management_node(state: EventPlanningState) -> EventPlanningState:
    agent = TaskManagementAgent()
    return await agent.process_with_error_handling(state)
```

### Error Summary

Get comprehensive error statistics after processing:

```python
agent = TaskManagementAgent()
result_state = await agent.process_with_error_handling(state)

# Get error summary
error_summary = agent.get_error_summary()
print(f"Total errors: {error_summary['total_errors']}")
print(f"Sub-agent errors: {error_summary['sub_agent_errors']['count']}")
print(f"Tool errors: {error_summary['tool_errors']['count']}")
print(f"Critical errors: {error_summary['critical_errors']['count']}")
```

### Convenience Functions

For standalone error handling:

```python
from .error_handler import (
    handle_sub_agent_failure,
    handle_tool_failure,
    handle_critical_failure
)

# Handle sub-agent failure
should_continue, partial_data = handle_sub_agent_failure(
    sub_agent_name="PrioritizationAgent",
    error=exception,
    state=state
)

# Handle tool failure
should_continue, error_metadata = handle_tool_failure(
    tool_name="TimelineCalculationTool",
    error=exception,
    state=state,
    affected_tasks=["task-1", "task-2"]
)

# Handle critical failure
updated_state = handle_critical_failure(
    error=exception,
    state=state,
    operation="critical_operation"
)
```

## State Updates

### Error Tracking Fields

The error handler updates the following fields in EventPlanningState:

- **error_count**: Incremented for each error
- **last_error**: Updated with latest error message
- **workflow_status**: Set to FAILED for critical errors
- **last_updated**: Updated timestamp
- **state_transitions**: Error transitions logged

### Example State After Error

```python
{
    'plan_id': 'plan-123',
    'workflow_status': 'running',  # or 'failed' for critical errors
    'error_count': 2,
    'last_error': 'Tool TimelineCalculationTool failed: Connection timeout',
    'last_updated': '2024-01-15T10:30:00Z',
    'state_transitions': [
        {
            'from_status': 'running',
            'to_status': 'running',
            'trigger': 'tool_error_TimelineCalculationTool',
            'timestamp': '2024-01-15T10:30:00Z',
            'data': {
                'tool': 'TimelineCalculationTool',
                'error_type': 'ConnectionTimeout',
                'affected_tasks': ['task-1', 'task-2']
            }
        }
    ]
}
```

## Integration with Existing Infrastructure

### Error Monitoring

The error handler integrates with the global error monitor:

```python
from ....error_handling.monitoring import get_error_monitor, record_error

# Automatic error recording
record_error(
    error=exception,
    component="task_management.sub_agent.PrioritizationAgent",
    operation="sub_agent_processing",
    correlation_id=state.get('plan_id'),
    metadata=error_details
)
```

### Error Handlers

Uses existing error handler chain:

```python
from ....error_handling.handlers import AgentErrorHandler

# Leverage existing agent error handling patterns
self.agent_error_handler = AgentErrorHandler()
```

### State Transition Logging

Logs all error-related state transitions:

```python
from ....workflows.state_models import StateTransitionLogger

# Log error transitions
self.transition_logger.log_transition(
    state=state,
    from_status=current_status,
    to_status=new_status,
    trigger=f"sub_agent_error_{sub_agent_name}",
    additional_data=error_details
)
```

## Testing

Run the error handler tests:

```bash
# Run all tests
pytest event_planning_agent_v2/agents/task_management/core/test_error_handler.py -v

# Run specific test class
pytest event_planning_agent_v2/agents/task_management/core/test_error_handler.py::TestTaskManagementErrorHandler -v

# Run specific test
pytest event_planning_agent_v2/agents/task_management/core/test_error_handler.py::TestTaskManagementErrorHandler::test_handle_sub_agent_error_with_partial_data -v
```

## Best Practices

1. **Always use process_with_error_handling()** as the main entry point
2. **Check error_count** in state after processing to determine if errors occurred
3. **Review error_summary** for detailed error statistics
4. **Monitor state_transitions** for error patterns
5. **Use correlation_id** (plan_id) for tracking related errors
6. **Mark tasks appropriately** when tool failures affect specific tasks
7. **Log errors at appropriate levels** (warning for sub-agent, error for tool, critical for fatal)

## Error Recovery

### Automatic Recovery

- **Sub-agent failures**: Automatically continue with partial data
- **Tool failures**: Automatically continue with remaining tools
- **State updates**: Automatically tracked and persisted

### Manual Recovery

For critical failures, the workflow can be recovered by:

1. Checking the error_count and last_error in state
2. Reviewing state_transitions for error history
3. Using the state manager to restore from checkpoint
4. Retrying with corrected configuration or data

```python
from ....database.state_manager import recover_workflow_state

# Recover from checkpoint
recovered_state = recover_workflow_state(plan_id)
if recovered_state:
    # Retry processing
    result = await agent.process_with_error_handling(recovered_state)
```

## Monitoring and Alerts

The error handler integrates with the monitoring system to provide:

- Real-time error tracking
- Error rate monitoring
- Component health metrics
- Alert generation for critical errors

Access monitoring data:

```python
from ....error_handling.monitoring import get_error_monitor

monitor = get_error_monitor()

# Get system health
health = monitor.get_health_report()

# Get error summary
error_summary = monitor.get_error_summary(
    component="task_management",
    time_window_hours=24
)

# Get correlation analysis
correlation = monitor.get_correlation_analysis(plan_id)
```

## Requirements Satisfied

This implementation satisfies the following requirements from task 15:

✅ Create `core/error_handler.py` with error handling utilities
✅ Implement `process_with_error_handling()` wrapper method in TaskManagementAgent
✅ Implement `_handle_sub_agent_error()` to log sub-agent errors and continue with partial data
✅ Implement `_handle_tool_error()` to log tool errors and mark affected tasks
✅ Implement `_handle_critical_error()` to handle critical failures and update WorkflowStatus.FAILED
✅ Integrate with existing error handlers from `error_handling/handlers.py`
✅ Integrate with existing error monitoring from `error_handling/monitoring.py`
✅ Implement StateTransitionLogger integration for error tracking
✅ Update error_count and last_error fields in EventPlanningState on failures

## Related Requirements

- **Requirement 1.5**: Error handling and resilience integration
- **Requirement 2.4**: Handling missing or incomplete sub-agent data
- **Requirement 4.5**: LLM API failure handling
- **Requirement 12.1-12.5**: Comprehensive error handling and resilience
