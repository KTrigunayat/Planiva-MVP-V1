# Task Management Agent - State Management Integration

## Overview

This document describes the state management integration implemented for the Task Management Agent, fulfilling the requirements of Task 18 from the implementation plan.

## Integration Components

### 1. StateManager Integration

The Task Management Agent integrates with the existing `WorkflowStateManager` from `database/state_manager.py`:

```python
from event_planning_agent_v2.database.state_manager import WorkflowStateManager

agent = TaskManagementAgent(
    state_manager=state_manager,  # Uses existing StateManager
    llm_model='gemma:2b',
    db_connection=None
)
```

**Key Features:**
- Uses existing state persistence infrastructure
- Leverages database connection from `database/connection.py`
- Follows existing transaction patterns from `database/models.py`
- Integrates with error recovery patterns from `error_handling/recovery.py`

### 2. StateManagementTool Integration

The workflow node integrates with `StateManagementTool` from `orchestrator.py`:

```python
from event_planning_agent_v2.agents.orchestrator import StateManagementTool

state_management_tool = StateManagementTool()
```

This tool provides workflow state management capabilities including:
- State save/load operations
- State updates
- State reset functionality

### 3. State Updates After Each Processing Step

The agent updates and persists state after each major processing step:

#### Step 1: After Sub-Agent Consolidation

```python
def _update_state_after_consolidation(
    self,
    state: EventPlanningState,
    consolidated_data: ConsolidatedTaskData
) -> EventPlanningState:
    """
    Creates checkpoint after sub-agent consolidation.
    Enables recovery if tool processing fails.
    """
```

**Checkpoint Data:**
- Completion status
- Timestamp
- Task count
- Consolidation errors/warnings

#### Step 2: After Tool Processing

```python
def _update_state_after_tools(
    self,
    state: EventPlanningState,
    tool_outputs: Dict[str, Any]
) -> EventPlanningState:
    """
    Creates checkpoint after tool processing.
    Enables recovery if extended task list generation fails.
    """
```

**Checkpoint Data:**
- Completion status
- Timestamp
- Tool execution status for all 6 tools
- Output counts for each tool

#### Step 3: After Extended Task List Generation

```python
def _update_state(
    self,
    state: EventPlanningState,
    extended_task_list: ExtendedTaskList
) -> EventPlanningState:
    """
    Final state update with extended_task_list.
    Persists complete results to database.
    """
```

**Final State Updates:**
- `extended_task_list` field populated
- `workflow_status` updated to RUNNING
- `last_updated` timestamp
- Full state persistence to database

### 4. State Persistence

State is persisted to the database using `StateManager.save_workflow_state()`:

```python
# Persist state to database
persistence_success = self.state_manager.save_workflow_state(state)

if persistence_success:
    logger.info("State persisted successfully to database")
else:
    logger.warning("State persistence returned False")
    # Log warning but don't fail processing
```

**Persistence Points:**
- After sub-agent consolidation (checkpoint)
- After tool processing (checkpoint)
- After extended task list generation (final save)
- On error (for recovery)

**Error Handling:**
- Persistence failures are logged but don't stop processing
- Error count is incremented in state
- Last error message is recorded
- Processing continues to ensure workflow completion

### 5. Workflow Status Updates

The agent updates `workflow_status` in `EventPlanningState`:

```python
# On successful completion
state['workflow_status'] = WorkflowStatus.RUNNING.value

# On critical error
state['workflow_status'] = WorkflowStatus.FAILED.value
```

**Status Transitions:**
- `RUNNING` → Task management processing in progress
- `RUNNING` → Successful completion (ready for Blueprint Agent)
- `FAILED` → Critical error occurred

### 6. State Restoration for Resuming After Interruptions

The agent supports resuming from checkpoints after interruptions:

```python
def restore_from_checkpoint(self, state: EventPlanningState) -> Optional[str]:
    """
    Restore processing from last checkpoint.
    
    Returns:
        - 'consolidation': Resume from tool processing
        - 'tool_processing': Resume from extended task list generation
        - None: Start from beginning
    """
```

**Checkpoint Structure:**

```python
state['task_management_checkpoints'] = {
    'consolidation': {
        'completed': True,
        'timestamp': '2024-01-01T00:00:00Z',
        'task_count': 10,
        'consolidation_errors': 0,
        'consolidation_warnings': 2
    },
    'tool_processing': {
        'completed': True,
        'timestamp': '2024-01-01T00:05:00Z',
        'tool_execution_status': {
            'timeline_calculation': 'success',
            'llm_enhancement': 'success',
            'vendor_assignment': 'success',
            'logistics_check': 'success',
            'conflict_check': 'success',
            'venue_lookup': 'success'
        },
        'timelines_count': 10,
        'enhancements_count': 10,
        'vendor_assignments_count': 8,
        'logistics_count': 10,
        'conflicts_count': 2,
        'venue_info_count': 10
    }
}
```

**Recovery Process:**

1. Check for existing checkpoints in state
2. Attempt to restore state from database using `recover_workflow_state()`
3. Determine which step to resume from
4. Continue processing from that step
5. Clean up checkpoints after successful completion

### 7. Blueprint Agent Access to Extended Task List

The Blueprint Agent can access `extended_task_list` from `EventPlanningState`:

```python
# In Blueprint Agent
extended_task_list = state.get('extended_task_list')

if extended_task_list:
    tasks = extended_task_list['tasks']
    processing_summary = extended_task_list['processing_summary']
    
    # Use task data for blueprint generation
    for task in tasks:
        task_id = task['task_id']
        task_name = task['task_name']
        priority = task['priority_level']
        # ... generate blueprint content
```

**Extended Task List Structure:**

```python
{
    'tasks': [
        {
            'task_id': 'task_1',
            'task_name': 'Venue Setup',
            'task_description': 'Set up venue for ceremony',
            'priority_level': 'High',
            'priority_score': 0.85,
            'granularity_level': 0,
            'parent_task_id': None,
            'sub_tasks': ['task_1_1', 'task_1_2'],
            'dependencies': [],
            'resources_required': [...],
            'timeline': {...},
            'llm_enhancements': {...},
            'assigned_vendors': [...],
            'logistics_status': {...},
            'conflicts': [...],
            'venue_info': {...},
            'has_errors': False,
            'has_warnings': True,
            'requires_manual_review': False,
            'error_messages': [],
            'warning_messages': ['Minor logistics concern']
        },
        # ... more tasks
    ],
    'processing_summary': {
        'total_tasks': 10,
        'tasks_with_errors': 0,
        'tasks_with_warnings': 3,
        'tasks_requiring_review': 1,
        'processing_time': 15.5,
        'tool_execution_status': {...}
    },
    'metadata': {
        'generated_at': '2024-01-01T00:10:00Z',
        'agent_version': '1.0.0',
        'llm_model': 'gemma:2b'
    }
}
```

## Workflow Integration

### Task Management Node

The `task_management_node` in `workflows/task_management_node.py` handles state management:

```python
def task_management_node(state: EventPlanningState) -> EventPlanningState:
    """
    LangGraph workflow node with state management integration.
    """
    # 1. Initialize state manager
    state_manager = get_state_manager()
    
    # 2. Check for checkpoints and restore if needed
    checkpoints = state.get('task_management_checkpoints', {})
    if checkpoints:
        restored_state = state_manager.recover_workflow_state(state.get('plan_id'))
        if restored_state:
            state = restored_state
    
    # 3. Initialize agent with state manager
    agent = TaskManagementAgent(state_manager=state_manager)
    
    # 4. Process with error handling
    updated_state = asyncio.run(agent.process_with_error_handling(state))
    
    # 5. Save final state
    state_manager.save_workflow_state(updated_state)
    
    # 6. Clean up checkpoints
    if 'task_management_checkpoints' in updated_state:
        del updated_state['task_management_checkpoints']
    
    return updated_state
```

### State Transitions

```
timeline_generation → task_management → blueprint_generation
                           ↓
                    [State Updates]
                           ↓
                    1. After consolidation (checkpoint)
                    2. After tools (checkpoint)
                    3. After extended task list (final save)
```

## Error Handling

### Persistence Errors

```python
try:
    self.state_manager.save_workflow_state(state)
    logger.info("State persisted successfully")
except Exception as e:
    logger.error(f"Failed to persist state: {e}")
    # Don't fail processing - log error and continue
    state['error_count'] = state.get('error_count', 0) + 1
    state['last_error'] = f"State persistence error: {str(e)}"
```

### Checkpoint Errors

```python
try:
    self.state_manager.checkpoint_workflow(state)
    logger.info("Checkpoint saved")
except Exception as e:
    logger.warning(f"Failed to save checkpoint: {e}")
    # Continue processing - checkpoint is optional
```

### Recovery Errors

```python
try:
    restored_state = state_manager.recover_workflow_state(plan_id)
    if restored_state:
        state = restored_state
except Exception as e:
    logger.warning(f"State restoration failed: {e}")
    # Continue with current state
```

## Testing

Comprehensive tests are provided in `tests/unit/test_task_management_state_integration.py`:

### Test Coverage

1. **StateManager Integration**
   - Initialization with StateManager
   - State persistence calls
   - Checkpoint creation

2. **State Updates**
   - After sub-agent consolidation
   - After tool processing
   - After extended task list generation

3. **Workflow Status**
   - Status updates on completion
   - Status updates on error

4. **State Restoration**
   - Restore from checkpoints
   - Resume from different steps
   - Handle missing checkpoints

5. **Blueprint Agent Access**
   - Access extended_task_list from state
   - Verify data structure
   - Verify data completeness

6. **Error Handling**
   - Persistence failures
   - Checkpoint failures
   - Recovery failures

### Running Tests

```bash
# Run all state integration tests
pytest event_planning_agent_v2/tests/unit/test_task_management_state_integration.py -v

# Run specific test class
pytest event_planning_agent_v2/tests/unit/test_task_management_state_integration.py::TestStateManagementIntegration -v

# Run with coverage
pytest event_planning_agent_v2/tests/unit/test_task_management_state_integration.py --cov=event_planning_agent_v2.agents.task_management.core --cov-report=html
```

## Requirements Fulfilled

This implementation fulfills all requirements from Task 18:

✅ **Requirement 10.1**: Integrate with existing StateManagementTool from orchestrator.py  
✅ **Requirement 10.2**: Update state after each processing step  
✅ **Requirement 10.3**: Use existing StateTransitionLogger for error tracking  
✅ **Requirement 10.4**: Restore state using existing state_manager  
✅ **Requirement 10.5**: Update workflow_status and persist using existing infrastructure  

✅ **Requirement 13.1**: Store Extended Task List in extended_task_list field  
✅ **Requirement 13.2**: Provide format compatible with Blueprint Agent  
✅ **Requirement 13.3**: Don't transition to blueprint_generation until ready  
✅ **Requirement 13.4**: Include metadata about processing status  
✅ **Requirement 13.5**: Blueprint Agent can incorporate Extended Task List data  

## Best Practices

1. **Always checkpoint after major steps** - Enables recovery
2. **Handle persistence failures gracefully** - Don't block workflow
3. **Clean up checkpoints after success** - Prevent state bloat
4. **Log all state transitions** - Aids debugging
5. **Verify Blueprint Agent compatibility** - Ensure data accessibility

## Future Enhancements

1. **Partial resumption** - Resume from specific tool instead of all tools
2. **Checkpoint compression** - Reduce checkpoint size for large task lists
3. **Async persistence** - Non-blocking state saves
4. **State versioning** - Handle schema changes gracefully
5. **Checkpoint expiration** - Auto-cleanup old checkpoints
