# Task Management Agent

## Overview

The Task Management Agent is an orchestration component that extends the event_planning_agent_v2 system. It processes event planning data through specialized sub-agents and tools to generate a comprehensive, extended task list with timeline calculations, vendor assignments, logistics verification, and conflict resolution.

### Purpose

The Task Management Agent bridges the gap between timeline generation and blueprint creation by:
- Analyzing and prioritizing tasks based on event requirements
- Breaking down high-level tasks into actionable sub-tasks
- Identifying resource requirements and dependencies
- Calculating precise timelines with conflict detection
- Assigning vendors to specific tasks
- Verifying logistics feasibility
- Detecting and reporting conflicts

### Position in Workflow

```
Timeline Agent → Task Management Agent → Blueprint Agent
```

The Task Management Agent:
1. **Receives**: EventPlanningState with timeline_data and selected_combination
2. **Processes**: Tasks through sub-agents and tools
3. **Outputs**: Extended task list in EventPlanningState.extended_task_list
4. **Passes to**: Blueprint Agent for final document generation

## Architecture

### High-Level Components

```
Task Management Agent Core
├── Sub-Agents (Data Collection)
│   ├── Prioritization Agent
│   ├── Granularity Agent
│   └── Resource & Dependency Agent
├── Data Consolidator
└── Tools (Data Enhancement)
    ├── Timeline Calculation Tool
    ├── API/LLM Tool
    ├── Vendor Task Tool
    ├── Logistics Check Tool
    ├── Conflict Check Tool
    └── Venue Lookup Tool
```

### Processing Flow

```mermaid
graph TB
    A[EventPlanningState Input] --> B[Prioritization Agent]
    A --> C[Granularity Agent]
    A --> D[Resource & Dependency Agent]
    
    B --> E[Data Consolidator]
    C --> E
    D --> E
    
    E --> F[Timeline Calculation Tool]
    F --> G[API/LLM Tool]
    G --> H[Vendor Task Tool]
    H --> I[Logistics Check Tool]
    I --> J[Conflict Check Tool]
    J --> K[Venue Lookup Tool]
    
    K --> L[Extended Task List Generator]
    L --> M[EventPlanningState Output]
```

## Components

### 1. Sub-Agents

#### Prioritization Agent Core
**Purpose**: Analyzes tasks and assigns priority levels

**Input**: EventPlanningState
**Output**: List[PrioritizedTask]

**Priority Levels**:
- Critical: Must be completed, blocks other tasks
- High: Important for event success
- Medium: Standard tasks
- Low: Nice-to-have tasks

**Example**:
```python
PrioritizedTask(
    task_id='task-001',
    task_name='Venue Setup',
    priority_level='Critical',
    priority_score=0.95,
    priority_rationale='Must be completed before event'
)
```

#### Granularity Agent Core
**Purpose**: Breaks down high-level tasks into actionable sub-tasks

**Input**: List[PrioritizedTask]
**Output**: List[GranularTask]

**Granularity Levels**:
- 0: Top-level task
- 1: Sub-task
- 2: Detailed sub-task

**Example**:
```python
GranularTask(
    task_id='task-001',
    parent_task_id=None,
    task_name='Venue Setup',
    task_description='Complete venue setup including decorations',
    granularity_level=0,
    estimated_duration=timedelta(hours=4),
    sub_tasks=['task-001-1', 'task-001-2']
)
```

#### Resource & Dependency Agent Core
**Purpose**: Identifies resource requirements and task dependencies

**Input**: List[GranularTask]
**Output**: List[TaskWithDependencies]

**Resource Types**:
- vendor: Service providers
- equipment: Physical equipment
- personnel: Staff members
- venue: Event location

**Example**:
```python
TaskWithDependencies(
    task_id='task-001',
    task_name='Venue Setup',
    dependencies=[],
    resources_required=[
        Resource(
            resource_type='venue',
            resource_id='1',
            resource_name='Garden Paradise Resort',
            quantity_required=1,
            availability_constraint='Must be available 6 hours before event'
        )
    ],
    resource_conflicts=[]
)
```

### 2. Data Consolidator

**Purpose**: Merges outputs from all three sub-agents into unified data structure

**Input**: 
- List[PrioritizedTask]
- List[GranularTask]
- List[TaskWithDependencies]

**Output**: ConsolidatedTaskData

**Process**:
1. Merge prioritization data
2. Merge granularity data
3. Merge dependency data
4. Validate consolidated data
5. Handle missing data gracefully

### 3. Tools

#### Timeline Calculation Tool
**Purpose**: Calculate start and end times for tasks

**Features**:
- Topological sort for dependency ordering
- Buffer time calculation
- Constraint handling
- Integration with Timeline Agent

**Output**: List[TaskTimeline]

#### API/LLM Tool
**Purpose**: Enhance task descriptions using LLM

**Features**:
- Uses Ollama (gemma:2b or tinyllama)
- Generates enhanced descriptions
- Provides suggestions and best practices
- Identifies potential issues
- Flags tasks for manual review

**Output**: List[EnhancedTask]

#### Vendor Task Tool
**Purpose**: Assign vendors to tasks

**Features**:
- Uses selected_combination from state
- Matches vendors based on capabilities
- Considers fitness scores from beam search
- Flags tasks requiring manual assignment

**Output**: List[VendorAssignment]

#### Logistics Check Tool
**Purpose**: Verify logistics feasibility

**Features**:
- Transportation verification
- Equipment availability check
- Setup requirements validation
- Feasibility scoring

**Output**: List[LogisticsStatus]

#### Conflict Check Tool
**Purpose**: Detect scheduling and resource conflicts

**Features**:
- Timeline conflict detection
- Resource double-booking detection
- Venue availability conflicts
- Integration with Timeline Agent's ConflictDetectionTool

**Output**: List[Conflict]

#### Venue Lookup Tool
**Purpose**: Retrieve venue information for tasks

**Features**:
- Queries database for venue details
- Extracts venue from selected_combination
- Uses MCP vendor server if available
- Flags tasks requiring venue selection

**Output**: List[VenueInfo]

## Data Models

### Input: EventPlanningState

```python
{
    'plan_id': str,
    'client_request': dict,
    'workflow_status': WorkflowStatus,
    'timeline_data': dict,  # From Timeline Agent
    'selected_combination': dict,  # From Sourcing Agent
    'budget_allocations': list,
    'vendor_combinations': list,
    'beam_candidates': list,
    # ... other fields
}
```

### Output: ExtendedTaskList

```python
{
    'tasks': [
        {
            'task_id': str,
            'task_name': str,
            'task_description': str,
            'priority_level': str,
            'priority_score': float,
            'granularity_level': int,
            'parent_task_id': Optional[str],
            'sub_tasks': List[str],
            'dependencies': List[str],
            'resources_required': List[Resource],
            'timeline': TaskTimeline,
            'llm_enhancements': dict,
            'assigned_vendors': List[VendorAssignment],
            'logistics_status': LogisticsStatus,
            'conflicts': List[Conflict],
            'venue_info': Optional[VenueInfo],
            'has_errors': bool,
            'has_warnings': bool,
            'requires_manual_review': bool
        }
    ],
    'processing_summary': {
        'total_tasks': int,
        'tasks_with_errors': int,
        'tasks_with_warnings': int,
        'tasks_requiring_review': int,
        'processing_time': float,
        'tool_execution_status': dict
    },
    'metadata': dict
}
```

### Data Model Relationships

```
PrioritizedTask ─┐
GranularTask ────┼─→ ConsolidatedTask ─→ ExtendedTask
TaskWithDependencies ─┘                      ↑
                                             │
Timeline Tool ──────────────────────────────┤
LLM Tool ───────────────────────────────────┤
Vendor Tool ────────────────────────────────┤
Logistics Tool ─────────────────────────────┤
Conflict Tool ──────────────────────────────┤
Venue Tool ─────────────────────────────────┘
```

## Usage

### Basic Usage

```python
from agents.task_management.core.task_management_agent import TaskManagementAgent
from workflows.state_models import EventPlanningState

# Initialize agent
agent = TaskManagementAgent()

# Process state
updated_state = await agent.process(event_planning_state)

# Access extended task list
extended_task_list = updated_state['extended_task_list']
```

### Integration in Workflow

```python
# In planning_workflow.py
from workflows.task_management_node import task_management_node

# Add node to workflow
workflow.add_node("task_management", task_management_node)

# Add edges
workflow.add_edge("timeline_generation", "task_management")
workflow.add_edge("task_management", "blueprint_generation")
```

### Error Handling

```python
try:
    updated_state = await agent.process(state)
except SubAgentDataError as e:
    # Handle missing sub-agent data
    logger.error(f"Sub-agent data error: {e}")
except ToolExecutionError as e:
    # Handle tool execution failure
    logger.error(f"Tool execution error: {e}")
except TaskManagementError as e:
    # Handle general task management error
    logger.error(f"Task management error: {e}")
```

## Configuration

### Configuration File

Location: `config/task_management_config.py`

```python
TASK_MANAGEMENT_CONFIG = {
    # LLM Configuration
    'enable_llm_enhancement': True,
    'llm_model': 'gemma:2b',  # or 'tinyllama'
    'llm_timeout': 30,
    'llm_max_retries': 3,
    
    # Tool Configuration
    'enable_conflict_detection': True,
    'enable_logistics_check': True,
    'enable_venue_lookup': True,
    'parallel_tool_execution': False,
    
    # Processing Configuration
    'max_task_depth': 3,
    'buffer_time_minutes': 15,
    'default_task_duration_hours': 2,
    
    # Logging Configuration
    'log_level': 'INFO',
    'log_sub_agent_outputs': True,
    'log_tool_results': True
}
```

### Environment Variables

```bash
# LLM Configuration
OLLAMA_BASE_URL=http://localhost:11434
OLLAMA_MODEL=gemma:2b

# Database Configuration
DATABASE_URL=postgresql://user:pass@localhost:5432/event_planning

# Logging
LOG_LEVEL=INFO
TASK_MANAGEMENT_LOG_LEVEL=DEBUG
```

## Tool Execution Order

The tools are executed sequentially in the following order:

1. **Timeline Calculation Tool**
   - Depends on: Consolidated task data
   - Provides: Task timelines with start/end times

2. **API/LLM Tool**
   - Depends on: Consolidated task data, timelines
   - Provides: Enhanced descriptions and suggestions

3. **Vendor Task Tool**
   - Depends on: Consolidated task data, selected_combination
   - Provides: Vendor assignments

4. **Logistics Check Tool**
   - Depends on: Task data, vendor assignments, venue info
   - Provides: Logistics feasibility status

5. **Conflict Check Tool**
   - Depends on: Timelines, resource assignments
   - Provides: Conflict detection and resolution suggestions

6. **Venue Lookup Tool**
   - Depends on: Task data, selected_combination
   - Provides: Venue information and constraints

### Tool Dependencies

```
Timeline Tool (no dependencies)
    ↓
LLM Tool (uses timelines)
    ↓
Vendor Tool (uses selected_combination)
    ↓
Logistics Tool (uses vendor assignments)
    ↓
Conflict Tool (uses timelines + resources)
    ↓
Venue Tool (uses selected_combination)
```

## Testing

### Running Tests

```bash
# Run all task management tests
pytest event_planning_agent_v2/tests/test_task_management_agent.py -v

# Run specific test class
pytest event_planning_agent_v2/tests/test_task_management_agent.py::TestTaskManagementAgentIntegration -v

# Run with coverage
pytest event_planning_agent_v2/tests/test_task_management_agent.py --cov=agents.task_management
```

### Test Categories

1. **Integration Tests**: Full workflow testing
2. **Performance Tests**: Large dataset handling
3. **Edge Case Tests**: Boundary conditions
4. **Error Scenario Tests**: Failure handling

### Test Data

Sample test data is available in:
- `tests/conftest.py`: Shared fixtures
- `tests/test_task_management_agent.py`: Test-specific fixtures

## Database Schema

### Tables

#### task_management_runs
```sql
CREATE TABLE task_management_runs (
    id SERIAL PRIMARY KEY,
    event_id INTEGER REFERENCES events(id),
    run_timestamp TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    processing_summary JSONB,
    status VARCHAR(50),
    error_log TEXT
);
```

#### extended_tasks
```sql
CREATE TABLE extended_tasks (
    id SERIAL PRIMARY KEY,
    task_management_run_id INTEGER REFERENCES task_management_runs(id),
    task_id VARCHAR(100) UNIQUE,
    task_data JSONB,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
```

#### task_conflicts
```sql
CREATE TABLE task_conflicts (
    id SERIAL PRIMARY KEY,
    task_management_run_id INTEGER REFERENCES task_management_runs(id),
    conflict_id VARCHAR(100),
    conflict_data JSONB,
    resolution_status VARCHAR(50),
    resolved_at TIMESTAMP
);
```

## Error Handling

### Error Types

1. **SubAgentDataError**: Missing or invalid sub-agent data
2. **ToolExecutionError**: Tool execution failure
3. **ConsolidationError**: Data consolidation failure
4. **TaskManagementError**: General task management error

### Error Recovery

The agent implements graceful degradation:
- Missing sub-agent data: Continue with available data
- Tool failures: Mark affected tasks, continue processing
- Database errors: Use retry logic with exponential backoff
- LLM failures: Continue with unenhanced data

### Logging

Errors are logged at appropriate levels:
- **ERROR**: Tool failures, sub-agent errors
- **WARNING**: Missing data, partial results
- **INFO**: Processing milestones
- **DEBUG**: Detailed execution information

## Performance Considerations

### Optimization Strategies

1. **Sequential Tool Execution**: Tools run sequentially to manage resources
2. **Lazy Loading**: Data loaded only when needed
3. **Caching**: Vendor and venue data cached during processing
4. **Batch Processing**: Tasks processed in batches where possible

### Performance Metrics

Typical processing times (on standard hardware):
- 10 tasks: < 5 seconds
- 50 tasks: < 15 seconds
- 100 tasks: < 30 seconds

### Scalability

The agent scales linearly with task count:
- Memory usage: ~1MB per 10 tasks
- CPU usage: Moderate (LLM calls are the bottleneck)
- Database queries: Optimized with connection pooling

## Troubleshooting

### Common Issues

#### Issue: LLM Enhancement Fails
**Symptoms**: Tool status shows "llm_enhancement: failed"
**Solution**: 
- Check Ollama service is running
- Verify OLLAMA_BASE_URL configuration
- Check model is downloaded: `ollama pull gemma:2b`

#### Issue: No Tasks Generated
**Symptoms**: extended_task_list has 0 tasks
**Solution**:
- Verify timeline_data exists in state
- Check sub-agent outputs in logs
- Ensure selected_combination is populated

#### Issue: Database Connection Errors
**Symptoms**: Vendor/Venue tools fail
**Solution**:
- Verify DATABASE_URL is correct
- Check database is running
- Verify database migrations are applied

#### Issue: Slow Processing
**Symptoms**: Processing takes > 30 seconds
**Solution**:
- Disable LLM enhancement if not needed
- Reduce task count through granularity settings
- Check database query performance

### Debug Mode

Enable debug logging:
```python
import logging
logging.getLogger('agents.task_management').setLevel(logging.DEBUG)
```

## Contributing

### Adding New Tools

1. Create tool class in `tools/` directory
2. Implement required interface methods
3. Add tool to TaskManagementAgent initialization
4. Update tool execution order in `_process_tools()`
5. Add tests in `tests/`
6. Update documentation

### Adding New Sub-Agents

1. Create sub-agent class in `sub_agents/` directory
2. Implement required interface methods
3. Add sub-agent to TaskManagementAgent initialization
4. Update data consolidation logic
5. Add tests
6. Update documentation

## References

### Related Documentation

- [Design Document](../../.kiro/specs/task-management-agent/design.md)
- [Requirements Document](../../.kiro/specs/task-management-agent/requirements.md)
- [Tasks Document](../../.kiro/specs/task-management-agent/tasks.md)
- [Workflow Integration](../../workflows/README_TASK_MANAGEMENT_INTEGRATION.md)
- [State Management](STATE_MANAGEMENT_INTEGRATION.md)
- [Configuration Guide](CONFIG_AND_LOGGING_GUIDE.md)

### External Dependencies

- **LangGraph**: Workflow orchestration
- **Ollama**: LLM inference
- **PostgreSQL**: Data persistence
- **CrewAI**: Agent framework

## License

Part of the event_planning_agent_v2 system.

## Support

For issues or questions:
1. Check troubleshooting section
2. Review related documentation
3. Check logs for error details
4. Consult design document for architecture details
