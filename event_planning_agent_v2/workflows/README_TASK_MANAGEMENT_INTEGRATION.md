# Task Management Integration - Developer Guide

## Overview

The Task Management Agent has been successfully integrated into the LangGraph event planning workflow. This document provides guidance for developers working with the task management node.

## Quick Start

### Using the Task Management Node

The task management node is automatically executed as part of the workflow:

```python
from event_planning_agent_v2.workflows import EventPlanningWorkflow

# Create workflow instance
workflow = EventPlanningWorkflow()

# Execute workflow (task management runs automatically)
result = workflow.execute_workflow(
    client_request={
        'client_id': 'client-123',
        'event_type': 'wedding',
        'guest_count': 150,
        'budget': 50000,
        'date': '2025-06-15',
        'location': 'San Francisco, CA'
    }
)

# Access extended task list from result
extended_task_list = result.get('extended_task_list')
if extended_task_list:
    tasks = extended_task_list['tasks']
    summary = extended_task_list['processing_summary']
    print(f"Generated {summary['total_tasks']} tasks")
```

### Checking if Task Management Ran

```python
from event_planning_agent_v2.workflows import should_run_task_management

# Check if task management would run for a given state
state = {
    'timeline_data': {'tasks': []},
    'workflow_status': 'running'
}

if should_run_task_management(state):
    print("Task management will run")
else:
    print("Task management will be skipped")
```

## Architecture

### Node Position in Workflow

```
client_selection → task_management → blueprint_generation
```

The task management node:
1. Receives state from client_selection (after vendor combination selected)
2. Processes timeline data to generate extended task list
3. Passes state to blueprint_generation with extended_task_list populated

### State Requirements

**Required Fields:**
- `timeline_data`: Timeline information (if missing, node is skipped)
- `workflow_status`: Current workflow status

**Optional Fields:**
- `selected_combination`: Selected vendor combination (recommended)
- `client_request`: Original client requirements

**Output Fields:**
- `extended_task_list`: Generated task data structure
- `next_node`: Set to 'blueprint_generation'
- `error_count`: Incremented on errors
- `last_error`: Error message if processing failed

## Extended Task List Structure

```python
{
    'tasks': [
        {
            'task_id': 'task-001',
            'name': 'Book venue',
            'priority': 'high',
            'dependencies': [],
            'timeline': {
                'start_date': '2025-01-15',
                'end_date': '2025-01-20',
                'duration_days': 5
            },
            'vendor_assignment': {
                'vendor_id': 'venue-123',
                'vendor_name': 'Grand Ballroom'
            },
            'logistics': {
                'verified': True,
                'notes': 'Venue available'
            },
            'conflicts': [],
            'status': 'pending'
        },
        # ... more tasks
    ],
    'processing_summary': {
        'total_tasks': 15,
        'tasks_with_errors': 0,
        'tasks_with_warnings': 2,
        'processing_time': 2.5,
        'sub_agent_results': {
            'prioritization': 'success',
            'granularity': 'success',
            'resource_dependency': 'success'
        },
        'tool_execution_status': {
            'timeline_calculation': 'success',
            'api_llm': 'success',
            'vendor_task': 'success',
            'logistics_check': 'success',
            'conflict_check': 'success',
            'venue_lookup': 'success'
        }
    },
    'metadata': {
        'generated_at': '2025-01-01T12:00:00',
        'agent_version': '1.0.0',
        'processing_mode': 'full'
    }
}
```

## Error Handling

### Graceful Degradation

The task management node implements graceful error handling:

```python
try:
    # Process task management
    result = task_management_node(state)
except Exception as e:
    # Error is caught and logged
    # Workflow continues to blueprint generation
    # Error details stored in state['last_error']
    pass
```

### Error Scenarios

| Scenario | Behavior | Next Node |
|----------|----------|-----------|
| Timeline data missing | Skip processing, log warning | blueprint_generation |
| Agent instantiation fails | Log error, continue workflow | blueprint_generation |
| Processing fails | Log error, update error_count | blueprint_generation |
| Workflow in FAILED state | Skip processing | blueprint_generation |

### Checking for Errors

```python
# After workflow execution
if result.get('error_count', 0) > 0:
    print(f"Errors occurred: {result.get('last_error')}")
    
# Check if task management was skipped
state_transitions = result.get('state_transitions', [])
task_mgmt_transitions = [
    t for t in state_transitions 
    if t.get('node_name') == 'task_management'
]

if task_mgmt_transitions:
    last_transition = task_mgmt_transitions[-1]
    if last_transition.get('output_data', {}).get('status') == 'skipped':
        print("Task management was skipped")
```

## Configuration

### Agent Configuration

The task management node uses default configuration from settings:

```python
# Default configuration (from settings.py)
task_management_agent = TaskManagementAgent(
    state_manager=state_manager,  # Uses get_state_manager()
    llm_model=None,  # Uses settings.llm.gemma_model
    db_connection=None  # Uses default connection
)
```

### Custom Configuration

To customize task management behavior, modify the agent initialization in `task_management_node.py`:

```python
# Example: Use custom LLM model
task_management_agent = TaskManagementAgent(
    state_manager=state_manager,
    llm_model="custom-model-name",
    db_connection=custom_db_connection
)
```

## Monitoring and Debugging

### Logging

The task management node logs extensively:

```python
import logging

# Enable debug logging
logging.getLogger('event_planning_agent_v2.workflows.task_management_node').setLevel(logging.DEBUG)
logging.getLogger('event_planning_agent_v2.agents.task_management').setLevel(logging.DEBUG)

# Run workflow
result = workflow.execute_workflow(client_request)
```

### State Transitions

All state transitions are logged:

```python
# Access state transitions
transitions = result.get('state_transitions', [])

# Filter task management transitions
task_mgmt_transitions = [
    t for t in transitions 
    if t.get('node_name') == 'task_management'
]

for transition in task_mgmt_transitions:
    print(f"Timestamp: {transition['timestamp']}")
    print(f"Event: {transition['event']}")
    print(f"Success: {transition['success']}")
    print(f"Data: {transition.get('output_data', {})}")
```

### Performance Metrics

```python
# Get processing summary
extended_task_list = result.get('extended_task_list', {})
summary = extended_task_list.get('processing_summary', {})

print(f"Processing time: {summary.get('processing_time', 0):.2f}s")
print(f"Total tasks: {summary.get('total_tasks', 0)}")
print(f"Tasks with errors: {summary.get('tasks_with_errors', 0)}")
print(f"Tasks with warnings: {summary.get('tasks_with_warnings', 0)}")

# Check tool execution status
tool_status = summary.get('tool_execution_status', {})
for tool_name, status in tool_status.items():
    print(f"{tool_name}: {status}")
```

## Testing

### Unit Tests

```python
from event_planning_agent_v2.workflows.task_management_node import (
    task_management_node,
    should_run_task_management
)

def test_should_run_with_timeline():
    state = {
        'timeline_data': {'tasks': []},
        'workflow_status': 'running'
    }
    assert should_run_task_management(state) == True

def test_should_skip_without_timeline():
    state = {
        'timeline_data': None,
        'workflow_status': 'running'
    }
    assert should_run_task_management(state) == False
```

### Integration Tests

```python
from unittest.mock import Mock, patch

@patch('event_planning_agent_v2.workflows.task_management_node.TaskManagementAgent')
def test_node_processes_successfully(mock_agent_class):
    # Setup mock
    mock_agent = Mock()
    mock_agent_class.return_value = mock_agent
    
    # Create state
    state = {
        'plan_id': 'test-123',
        'timeline_data': {'tasks': []},
        'workflow_status': 'running'
    }
    
    # Execute node
    result = task_management_node(state)
    
    # Verify
    assert mock_agent_class.called
    assert result['next_node'] == 'blueprint_generation'
```

## Best Practices

### 1. Always Check for Extended Task List

```python
extended_task_list = state.get('extended_task_list')
if extended_task_list:
    # Use extended task list
    tasks = extended_task_list['tasks']
else:
    # Fallback behavior
    print("Extended task list not available")
```

### 2. Handle Missing Timeline Data

```python
# Before workflow execution, ensure timeline data is present
if not state.get('timeline_data'):
    print("Warning: Timeline data missing, task management will be skipped")
```

### 3. Monitor Processing Time

```python
# Check if processing is taking too long
summary = extended_task_list.get('processing_summary', {})
processing_time = summary.get('processing_time', 0)

if processing_time > 10:  # seconds
    print(f"Warning: Task management took {processing_time}s")
```

### 4. Validate Task Data

```python
# Validate extended task list structure
if extended_task_list:
    assert 'tasks' in extended_task_list
    assert 'processing_summary' in extended_task_list
    assert isinstance(extended_task_list['tasks'], list)
```

## Troubleshooting

### Issue: Task Management Not Running

**Symptoms:** `extended_task_list` is None after workflow execution

**Possible Causes:**
1. Timeline data is missing
2. Workflow is in FAILED state
3. Agent instantiation failed

**Solution:**
```python
# Check state transitions
transitions = result.get('state_transitions', [])
task_mgmt_transitions = [
    t for t in transitions 
    if t.get('node_name') == 'task_management'
]

if not task_mgmt_transitions:
    print("Task management node was not executed")
else:
    last_transition = task_mgmt_transitions[-1]
    print(f"Status: {last_transition.get('output_data', {}).get('status')}")
    print(f"Reason: {last_transition.get('output_data', {}).get('reason')}")
```

### Issue: Processing Errors

**Symptoms:** `error_count` > 0, `last_error` contains error message

**Solution:**
```python
# Check error details
if result.get('error_count', 0) > 0:
    error_msg = result.get('last_error', '')
    print(f"Error: {error_msg}")
    
    # Check processing summary for details
    summary = result.get('extended_task_list', {}).get('processing_summary', {})
    print(f"Tasks with errors: {summary.get('tasks_with_errors', 0)}")
    print(f"Tool status: {summary.get('tool_execution_status', {})}")
```

### Issue: Slow Processing

**Symptoms:** Task management takes > 10 seconds

**Solution:**
```python
# Enable performance logging
import logging
logging.getLogger('event_planning_agent_v2.agents.task_management').setLevel(logging.DEBUG)

# Check tool execution times in logs
# Consider optimizing:
# 1. Database queries
# 2. LLM calls
# 3. Tool execution
```

## API Reference

### Functions

#### `task_management_node(state: EventPlanningState) -> EventPlanningState`

Main workflow node function.

**Parameters:**
- `state`: Current EventPlanningState from workflow

**Returns:**
- Updated EventPlanningState with extended_task_list populated

**Raises:**
- No exceptions (all errors caught and logged)

#### `should_run_task_management(state: EventPlanningState) -> bool`

Determines whether task management should run.

**Parameters:**
- `state`: Current EventPlanningState

**Returns:**
- `True` if task management should run, `False` otherwise

**Conditions:**
- Returns `True` if timeline_data present and workflow not failed
- Returns `False` if timeline_data missing or workflow failed

## Related Documentation

- [Task Management Agent Documentation](../agents/task_management/README.md)
- [Workflow State Models](./state_models.py)
- [Planning Workflow](./planning_workflow.py)
- [Task 17 Implementation Summary](./TASK_17_IMPLEMENTATION_SUMMARY.md)
- [Workflow Diagram](./WORKFLOW_DIAGRAM.md)

## Support

For issues or questions:
1. Check the troubleshooting section above
2. Review the implementation summary
3. Check the workflow diagram
4. Review the agent documentation
5. Check state transitions in logs

## Version History

- **v1.0.0** (2025-01-21): Initial integration
  - Task management node created
  - Workflow integration complete
  - Error handling implemented
  - Documentation complete
