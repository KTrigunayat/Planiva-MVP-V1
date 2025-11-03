# Timeline Calculation Tool

## Overview

The Timeline Calculation Tool is a specialized component of the Task Management Agent that calculates precise start and end times for all event tasks based on their dependencies, durations, priorities, and scheduling constraints.

## Features

### 1. Dependency-Based Scheduling
- Uses **Kahn's algorithm** (topological sort) to order tasks by dependencies
- Ensures prerequisite tasks are always scheduled before dependent tasks
- Handles complex dependency graphs with multiple levels

### 2. Intelligent Buffer Time Management
- Automatically adds buffer time between dependent tasks
- Adjusts buffer based on task priority:
  - **Critical tasks**: 30 minutes buffer
  - **High priority**: 20 minutes buffer
  - **Medium priority**: 15 minutes buffer (default)
  - **Low priority**: 10 minutes buffer
- Reduces buffer for highly granular tasks (detailed sub-tasks)

### 3. Circular Dependency Detection
- Detects circular dependencies in task graphs
- Gracefully handles circular dependencies by breaking the cycle
- Logs warnings when circular dependencies are detected
- Continues processing with remaining tasks

### 4. Integration with Existing Timeline Agent
- References `TimelineGenerationTool` for baseline timeline data
- Integrates with `ConflictDetectionTool` for schedule validation
- Uses event date and start time from EventPlanningState
- Validates calculated schedules against existing timeline constraints

### 5. Flexible Scheduling
- Respects working hours (8 AM - 11 PM by default)
- Handles tasks with no dependencies (scheduled at current time)
- Handles tasks with multiple dependencies (waits for all to complete)
- Supports parallel task execution when dependencies allow

## Architecture

```
TimelineCalculationTool
├── calculate_timelines()          # Main entry point
│   ├── _extract_event_date()      # Get event date from state
│   ├── _topological_sort()        # Sort tasks by dependencies
│   ├── _schedule_tasks()          # Schedule all tasks
│   └── _validate_schedules()      # Validate with ConflictDetectionTool
│
├── _topological_sort()            # Kahn's algorithm implementation
│   ├── Build adjacency list
│   ├── Calculate in-degrees
│   ├── Process tasks with no dependencies
│   └── Detect circular dependencies
│
├── _schedule_tasks()              # Schedule tasks in order
│   ├── _get_event_start_time()   # Determine event start
│   ├── _calculate_task_start_time() # Calculate start for each task
│   ├── _calculate_buffer_time()  # Calculate buffer time
│   └── _extract_constraints()    # Extract scheduling constraints
│
└── _validate_schedules()          # Validate with existing tools
    └── _convert_to_timeline_format() # Convert to ConflictDetectionTool format
```

## Usage

### Basic Usage

```python
from agents.task_management.tools import TimelineCalculationTool
from agents.task_management.models import ConsolidatedTaskData

# Initialize tool
tool = TimelineCalculationTool(
    timeline_generation_tool=timeline_gen_tool,  # Optional
    conflict_detection_tool=conflict_tool         # Optional
)

# Calculate timelines
timelines = tool.calculate_timelines(
    consolidated_data=consolidated_task_data,
    state=event_planning_state
)

# Access results
for timeline in timelines:
    print(f"Task: {timeline.task_id}")
    print(f"  Start: {timeline.start_time}")
    print(f"  End: {timeline.end_time}")
    print(f"  Duration: {timeline.duration}")
    print(f"  Buffer: {timeline.buffer_time}")
```

### Integration with Task Management Agent

```python
from agents.task_management.core import TaskManagementAgent

# The Timeline Calculation Tool is automatically used by the
# Task Management Agent during tool processing phase

agent = TaskManagementAgent(state_manager, llm)
result = agent.process(state)

# Extended task list will include timeline data
extended_tasks = result['extended_task_list']['tasks']
for task in extended_tasks:
    timeline = task['timeline']
    print(f"{task['task_name']}: {timeline['start_time']} - {timeline['end_time']}")
```

## Input Requirements

### ConsolidatedTaskData
The tool requires consolidated task data with the following fields:

```python
@dataclass
class ConsolidatedTask:
    task_id: str                    # Unique task identifier
    task_name: str                  # Human-readable task name
    priority_level: str             # Critical, High, Medium, Low
    estimated_duration: timedelta   # Task duration
    dependencies: List[str]         # List of prerequisite task IDs
    granularity_level: int          # 0=top-level, 1=sub-task, 2=detailed
    # ... other fields
```

### EventPlanningState
The tool requires state data with:

```python
{
    'client_request': {
        'eventDate': '2025-10-20'   # Event date (YYYY-MM-DD)
    },
    'timeline_data': {              # Optional baseline timeline
        'event_date': '2025-10-20',
        'timeline': [
            {
                'start_time': '10:00',
                'duration': 8.0
            }
        ]
    },
    'selected_combination': {...}   # Vendor combination (for validation)
}
```

## Output Format

### TaskTimeline Objects

```python
@dataclass
class TaskTimeline:
    task_id: str                    # Task identifier
    start_time: datetime            # Calculated start time
    end_time: datetime              # Calculated end time
    duration: timedelta             # Task duration
    buffer_time: timedelta          # Buffer after task
    scheduling_constraints: List[str]  # List of constraints
```

### Example Output

```python
[
    TaskTimeline(
        task_id='task_1',
        start_time=datetime(2025, 10, 20, 10, 0),
        end_time=datetime(2025, 10, 20, 12, 0),
        duration=timedelta(hours=2),
        buffer_time=timedelta(minutes=30),
        scheduling_constraints=['Priority: Critical']
    ),
    TaskTimeline(
        task_id='task_2',
        start_time=datetime(2025, 10, 20, 12, 30),
        end_time=datetime(2025, 10, 20, 14, 0),
        duration=timedelta(hours=1.5),
        buffer_time=timedelta(minutes=20),
        scheduling_constraints=[
            'Depends on 1 task(s): task_1',
            'Priority: High'
        ]
    )
]
```

## Algorithm Details

### Topological Sort (Kahn's Algorithm)

The tool uses Kahn's algorithm to sort tasks by dependencies:

1. **Build Graph**: Create adjacency list and calculate in-degrees
2. **Initialize Queue**: Add all tasks with no dependencies (in-degree = 0)
3. **Process Queue**: 
   - Remove task from queue
   - Add to sorted list
   - Reduce in-degree of dependent tasks
   - Add tasks with in-degree = 0 to queue
4. **Detect Cycles**: If sorted list length < task count, circular dependencies exist

**Time Complexity**: O(V + E) where V = tasks, E = dependencies

### Task Scheduling Algorithm

1. **Determine Start Time**: Use event start time from baseline timeline
2. **For Each Task** (in topological order):
   - If no dependencies: start at current time
   - If has dependencies: start after latest dependency ends (including buffer)
   - Calculate end time: start + duration
   - Calculate buffer time: based on priority and granularity
   - Update current time: end + buffer
3. **Create TaskTimeline**: Store all calculated times

## Error Handling

### Circular Dependencies
```python
# Detected and logged as warnings
logger.warning(
    f"Circular dependencies broken for {len(circular_tasks)} tasks. "
    "These tasks will be scheduled in arbitrary order."
)
```

### Missing Dependencies
```python
# Unknown dependencies are logged and ignored
logger.warning(
    f"Task {task.task_id} has unknown dependency: {dependency_id}"
)
```

### Tool Execution Errors
```python
# Wrapped in ToolExecutionError with details
raise ToolExecutionError(
    tool_name="TimelineCalculationTool",
    message=error_msg,
    details={'task_count': len(tasks), 'error_type': type(e).__name__}
)
```

## Configuration

### Default Settings

```python
DEFAULT_BUFFER_MINUTES = 15      # Default buffer between tasks
DEFAULT_START_TIME = "09:00"     # Default event start time
WORKING_HOURS_START = 8          # 8 AM
WORKING_HOURS_END = 23           # 11 PM
```

### Buffer Time Calculation

| Priority Level | Buffer Time | Granularity Adjustment |
|---------------|-------------|------------------------|
| Critical      | 30 minutes  | -5 min for level 2+    |
| High          | 20 minutes  | -5 min for level 2+    |
| Medium        | 15 minutes  | -5 min for level 2+    |
| Low           | 10 minutes  | -5 min for level 2+    |

## Testing

### Run Tests

```bash
# From event_planning_agent_v2 directory
python agents/task_management/tools/test_timeline_calculation.py
```

### Test Coverage

1. **Basic Timeline Calculation**: Simple dependency chain
2. **Topological Sort**: Complex dependency graph
3. **Circular Dependency Handling**: Circular dependency detection

### Example Test Output

```
Running Timeline Calculation Tool tests...

Test 1: Basic timeline calculation
Task 1: 2025-10-20 10:00:00 - 2025-10-20 12:00:00
Task 2: 2025-10-20 12:30:00 - 2025-10-20 14:00:00
Task 3: 2025-10-20 14:20:00 - 2025-10-20 15:20:00
✓ Basic timeline calculation test passed!

Test 2: Topological sort
Sorted order: ['A', 'B', 'C', 'D']
✓ Topological sort test passed!

Test 3: Circular dependency handling
Circular dependencies detected: ['X', 'Y']
✓ Circular dependency handling test passed!

All tests passed! ✓
```

## Requirements Satisfied

This implementation satisfies **Requirement 3: Timeline Calculation Integration**:

- ✅ **3.1**: Creates Timeline Calculation Tool extending timeline_tools.py functionality
- ✅ **3.2**: Uses data from ConflictDetectionTool and TimelineGenerationTool
- ✅ **3.3**: Ensures dependent tasks are scheduled after prerequisites (topological sort)
- ✅ **3.4**: Coordinates with Timeline Agent's conflict detection capabilities
- ✅ **3.5**: Attaches calculated start/end dates to each task via TaskTimeline objects

## Future Enhancements

1. **Parallel Task Optimization**: Optimize scheduling to maximize parallel task execution
2. **Resource-Aware Scheduling**: Consider resource availability when scheduling
3. **Time Window Constraints**: Support specific time windows for tasks
4. **Dynamic Rescheduling**: Support real-time schedule adjustments
5. **Critical Path Analysis**: Identify and highlight critical path tasks
6. **Schedule Optimization**: Use optimization algorithms to minimize total event duration

## Dependencies

- Python 3.8+
- `datetime` (standard library)
- `typing` (standard library)
- `collections` (standard library)
- `logging` (standard library)
- Task Management Agent models
- Task Management Agent exceptions

## Related Components

- **ConflictDetectionTool**: Validates calculated schedules
- **TimelineGenerationTool**: Provides baseline timeline data
- **Task Management Agent Core**: Orchestrates tool execution
- **Prioritization Agent**: Provides task priorities
- **Granularity Agent**: Provides task durations
- **Resource & Dependency Agent**: Provides task dependencies

## License

Part of the Event Planning Agent v2 system.
