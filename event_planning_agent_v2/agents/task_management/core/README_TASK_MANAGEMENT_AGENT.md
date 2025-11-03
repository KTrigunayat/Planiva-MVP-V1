# Task Management Agent Core - Implementation Guide

## Overview

The Task Management Agent Core (`TaskManagementAgent`) is the main orchestrator that coordinates all sub-agents and tools to generate comprehensive extended task lists for event planning.

## Architecture

```
TaskManagementAgent
├── Sub-Agents (Data Collection)
│   ├── PrioritizationAgentCore
│   ├── GranularityAgentCore
│   └── ResourceDependencyAgentCore
├── Data Consolidator
│   └── DataConsolidator
└── Tools (Data Enhancement)
    ├── TimelineCalculationTool
    ├── APILLMTool
    ├── VendorTaskTool
    ├── LogisticsCheckTool
    ├── ConflictCheckTool
    └── VenueLookupTool
```

## Usage

### Basic Usage

```python
from agents.task_management.core import TaskManagementAgent
from workflows.state_models import EventPlanningState

# Initialize agent
agent = TaskManagementAgent()

# Process state
state: EventPlanningState = {
    'plan_id': 'event-123',
    'client_request': {...},
    'selected_combination': {...},
    'timeline_data': {...},
    # ... other state fields
}

# Run processing
updated_state = await agent.process(state)

# Access extended task list
extended_task_list = updated_state['extended_task_list']
```

### Custom Configuration

```python
from database.state_manager import WorkflowStateManager

# Initialize with custom configuration
state_manager = WorkflowStateManager()
agent = TaskManagementAgent(
    state_manager=state_manager,
    llm_model='tinyllama',  # or 'gemma:2b'
    db_connection=custom_db_connection
)
```

## Processing Flow

### Step 1: Sub-Agent Invocation
The agent invokes three sub-agents in sequence:

1. **Prioritization Agent**: Assigns priority levels (Critical, High, Medium, Low)
2. **Granularity Agent**: Breaks down tasks into actionable sub-tasks
3. **Resource & Dependency Agent**: Identifies dependencies and resource requirements

### Step 2: Data Consolidation
Merges outputs from all sub-agents into unified `ConsolidatedTaskData`:
- Combines priority, granularity, and dependency information
- Handles missing or incomplete data gracefully
- Logs consolidation errors and warnings

### Step 3: Tool Processing
Processes consolidated data through six tools sequentially:

1. **Timeline Calculation**: Calculates start/end times based on dependencies
2. **LLM Enhancement**: Enhances descriptions with AI suggestions
3. **Vendor Assignment**: Assigns vendors from selected combination
4. **Logistics Verification**: Checks transportation, equipment, setup feasibility
5. **Conflict Detection**: Detects scheduling and resource conflicts
6. **Venue Lookup**: Retrieves detailed venue information

### Step 4: Extended Task List Generation
Creates final `ExtendedTaskList` with:
- All consolidated task data
- All tool enhancements
- Status flags (errors, warnings, manual review)
- Processing summary statistics

### Step 5: State Update
Updates `EventPlanningState` with:
- `extended_task_list` field populated
- `last_updated` timestamp
- Error information (if any)

## Output Structure

### ExtendedTaskList

```python
{
    'tasks': [
        {
            'task_id': 'task-1',
            'task_name': 'Venue Setup',
            'task_description': 'Set up venue for ceremony',
            'priority_level': 'Critical',
            'priority_score': 0.95,
            'granularity_level': 0,
            'parent_task_id': None,
            'sub_tasks': ['task-1-1', 'task-1-2'],
            'dependencies': [],
            'resources_required': [...],
            'timeline': {
                'start_time': '2025-12-15T08:00:00',
                'end_time': '2025-12-15T10:00:00',
                'duration': 7200,  # seconds
                'buffer_time': 900  # seconds
            },
            'llm_enhancements': {
                'enhanced_description': '...',
                'suggestions': [...],
                'potential_issues': [...],
                'best_practices': [...]
            },
            'assigned_vendors': [...],
            'logistics_status': {...},
            'conflicts': [],
            'venue_info': {...},
            'has_errors': False,
            'has_warnings': False,
            'requires_manual_review': False,
            'error_messages': [],
            'warning_messages': []
        },
        # ... more tasks
    ],
    'processing_summary': {
        'total_tasks': 25,
        'tasks_with_errors': 2,
        'tasks_with_warnings': 5,
        'tasks_requiring_review': 3,
        'processing_time': 12.5,
        'tool_execution_status': {
            'timeline_calculation': 'success',
            'llm_enhancement': 'success',
            'vendor_assignment': 'success',
            'logistics_check': 'success',
            'conflict_check': 'success',
            'venue_lookup': 'success'
        }
    },
    'metadata': {
        'generated_at': '2025-10-19T10:30:00',
        'agent_version': '1.0.0',
        'llm_model': 'gemma:2b',
        'consolidation_errors': 0,
        'consolidation_warnings': 2
    }
}
```

## Error Handling

### Graceful Degradation
The agent continues processing even when individual components fail:

- **Sub-agent failures**: Continues with available data from other sub-agents
- **Tool failures**: Continues without that tool's enhancements
- **Partial data**: Processes what's available and flags missing data

### Error Tracking
All errors are tracked and reported:

```python
# Check processing summary for errors
summary = extended_task_list['processing_summary']
if summary['tasks_with_errors'] > 0:
    print(f"Warning: {summary['tasks_with_errors']} tasks have errors")

# Check tool execution status
for tool, status in summary['tool_execution_status'].items():
    if 'failed' in status:
        print(f"Tool {tool} failed: {status}")
```

### Error Types
- `TaskManagementError`: Critical processing failures
- `SubAgentDataError`: All sub-agents failed
- `ToolExecutionError`: Tool execution failed (handled gracefully)

## Logging

The agent provides comprehensive logging:

```
============================================================
Starting Task Management Agent processing
============================================================

[STEP 1] Invoking sub-agents...
  → Invoking Prioritization Agent...
    ✓ Prioritization Agent returned 25 tasks
  → Invoking Granularity Agent...
    ✓ Granularity Agent returned 45 tasks
  → Invoking Resource & Dependency Agent...
    ✓ Resource & Dependency Agent returned 45 tasks

[STEP 2] Consolidating sub-agent data...
  ✓ Consolidated 45 tasks

[STEP 3] Processing through tools...
  [1/6] Timeline Calculation Tool...
    ✓ Calculated timelines for 45 tasks
  [2/6] API/LLM Tool...
    ✓ Enhanced 45 tasks
  [3/6] Vendor Task Tool...
    ✓ Assigned vendors for 45 tasks
  [4/6] Logistics Check Tool...
    ✓ Verified logistics for 45 tasks
  [5/6] Conflict Check Tool...
    ✓ Detected 3 conflicts
  [6/6] Venue Lookup Tool...
    ✓ Retrieved venue info for 45 tasks

[STEP 4] Generating extended task list...
  ✓ Generated extended task list with 45 tasks

[STEP 5] Updating EventPlanningState...
  ✓ State updated successfully

============================================================
Task Management Agent processing completed in 12.50s
Total tasks: 45
Tasks with errors: 2
Tasks with warnings: 5
Tasks requiring review: 3
============================================================
```

## Integration with Workflow

### LangGraph Node (Future Implementation)

```python
from agents.task_management.core import TaskManagementAgent

async def task_management_node(state: EventPlanningState) -> EventPlanningState:
    """LangGraph node for task management"""
    agent = TaskManagementAgent()
    return await agent.process(state)

# Add to workflow
workflow.add_node("task_management", task_management_node)
workflow.add_edge("timeline_generation", "task_management")
workflow.add_edge("task_management", "blueprint_generation")
```

## Performance Considerations

### Processing Time
- Typical processing time: 10-20 seconds for 50 tasks
- LLM enhancement is the slowest step (async processing helps)
- Tool processing is sequential (can be parallelized in future)

### Memory Usage
- Minimal memory footprint
- All data structures use dataclasses
- State is serialized to dict for storage

### Scalability
- Handles 100+ tasks efficiently
- Sub-agent processing is async
- Tool processing can be parallelized (future enhancement)

## Testing

### Unit Tests
```bash
pytest agents/task_management/core/test_task_management_agent.py -v
```

### Verification Script
```bash
cd agents/task_management/core
python verify_task_management_agent.py
```

## Dependencies

### Required Packages
- `langchain`: LLM integration
- `pydantic`: Data validation
- `sqlalchemy`: Database operations
- `asyncio`: Async processing

### Internal Dependencies
- Sub-agents: Prioritization, Granularity, Resource & Dependency
- Tools: Timeline, LLM, Vendor, Logistics, Conflict, Venue
- Models: Extended, Consolidated, Task, Data models
- Infrastructure: State manager, LLM manager, database connection

## Configuration

### Environment Variables
```bash
# LLM Configuration
LLM_MODEL=gemma:2b  # or tinyllama
LLM_TEMPERATURE=0.7
LLM_MAX_TOKENS=2000

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost/eventdb

# Processing Configuration
MAX_RETRIES=3
TIMEOUT_SECONDS=30
```

### Settings
Configure in `config/settings.py`:
```python
TASK_MANAGEMENT_CONFIG = {
    'enable_llm_enhancement': True,
    'llm_model': 'gemma:2b',
    'max_retries': 3,
    'timeout_seconds': 30,
    'enable_conflict_detection': True,
    'enable_logistics_check': True,
    'enable_venue_lookup': True,
    'parallel_tool_execution': False,
    'log_level': 'INFO'
}
```

## Troubleshooting

### Common Issues

#### 1. Sub-agent returns empty data
**Symptom**: "All sub-agents returned empty data"
**Solution**: Check that state contains required fields (client_request, timeline_data, selected_combination)

#### 2. Tool execution fails
**Symptom**: Tool status shows "failed: ..."
**Solution**: Check tool-specific logs for details. Agent continues with other tools.

#### 3. LLM timeout
**Symptom**: "API/LLM Tool failed: timeout"
**Solution**: Increase timeout in settings or use faster model (tinyllama)

#### 4. Database connection error
**Symptom**: "Database connection failed"
**Solution**: Check DATABASE_URL and database availability

### Debug Mode
Enable debug logging:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

## Future Enhancements

### Planned Features
1. Parallel tool execution for better performance
2. Caching of LLM responses
3. Incremental processing for large task lists
4. Real-time progress updates
5. Task prioritization optimization
6. Advanced conflict resolution strategies

### Extension Points
- Custom sub-agents can be added
- Custom tools can be integrated
- Custom consolidation logic
- Custom serialization formats

## Support

For issues or questions:
1. Check logs for detailed error messages
2. Review processing summary for tool status
3. Verify state contains required fields
4. Check database connectivity
5. Verify LLM service availability

## Version History

### v1.0.0 (Current)
- Initial implementation
- Three sub-agents (Prioritization, Granularity, Resource & Dependency)
- Six tools (Timeline, LLM, Vendor, Logistics, Conflict, Venue)
- Data consolidation
- Extended task list generation
- State management integration
- Comprehensive error handling
- Detailed logging

## License

Part of the Event Planning Agent v2 system.
