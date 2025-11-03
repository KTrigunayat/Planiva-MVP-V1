# Data Consolidator Implementation

## Overview

The `DataConsolidator` class consolidates outputs from three sub-agents (Prioritization, Granularity, and Resource & Dependency) into a unified `ConsolidatedTaskData` structure.

## Features

### 1. Data Consolidation
- Merges data from three sub-agents into `ConsolidatedTask` objects
- Handles tasks that appear in some but not all sub-agent outputs
- Creates unified task IDs across all sources

### 2. Missing Data Handling
- Uses default values when sub-agent data is missing
- Logs warnings for missing data
- Continues processing with partial data
- Tracks all errors and warnings in processing metadata

### 3. Data Validation
- Validates dependency references
- Validates sub-task references
- Validates parent task references
- Detects circular dependencies using DFS algorithm
- Logs all validation issues as warnings

### 4. Error Tracking
- Maintains list of consolidation errors
- Maintains list of warnings
- Includes error/warning counts in processing metadata
- Provides detailed context for each error

## Implementation Details

### Methods

#### `consolidate_sub_agent_data()`
Main entry point that:
1. Builds task ID mappings for efficient lookup
2. Gets all unique task IDs from all sources
3. Consolidates each task individually
4. Validates consolidated data
5. Returns `ConsolidatedTaskData` with metadata

#### `_merge_prioritization_data()`
Merges data from Prioritization Agent:
- task_name
- priority_level (Critical, High, Medium, Low)
- priority_score (0.0 - 1.0)
- priority_rationale

Defaults: Medium priority, 0.5 score if missing

#### `_merge_granularity_data()`
Merges data from Granularity Agent:
- parent_task_id
- task_description
- granularity_level (0, 1, 2)
- estimated_duration
- sub_tasks list

Defaults: Top-level task, 1 hour duration if missing

#### `_merge_dependency_data()`
Merges data from Resource & Dependency Agent:
- dependencies list
- resources_required list
- resource_conflicts list

Defaults: Empty lists if missing

#### `_validate_consolidated_data()`
Validates:
- Invalid dependency references
- Invalid sub-task references
- Invalid parent task references
- Circular dependencies

#### `_check_circular_dependencies()`
Uses depth-first search to detect cycles in dependency graph

#### `_handle_missing_data()`
Logs and tracks missing data for later processing

## Usage Example

```python
from event_planning_agent_v2.agents.task_management.core import DataConsolidator

# Create consolidator
consolidator = DataConsolidator()

# Consolidate data from sub-agents
consolidated_data = consolidator.consolidate_sub_agent_data(
    prioritized_tasks=prioritized_tasks,
    granular_tasks=granular_tasks,
    dependency_tasks=dependency_tasks,
    event_context={"event_type": "wedding", "guest_count": 150}
)

# Access consolidated tasks
for task in consolidated_data.tasks:
    print(f"Task: {task.task_name}")
    print(f"  Priority: {task.priority_level}")
    print(f"  Duration: {task.estimated_duration}")
    print(f"  Dependencies: {task.dependencies}")

# Check for errors/warnings
metadata = consolidated_data.processing_metadata
print(f"Errors: {len(metadata['errors'])}")
print(f"Warnings: {len(metadata['warnings'])}")
```

## Requirements Satisfied

- **Requirement 2.1**: Receives and stores prioritization information ✓
- **Requirement 2.2**: Receives and merges granularity data ✓
- **Requirement 2.3**: Receives and integrates resource/dependency information ✓
- **Requirement 2.4**: Logs errors and continues with available data ✓
- **Requirement 2.5**: Creates consolidated task data object ✓

## Testing

Run the test suite:
```bash
python event_planning_agent_v2/agents/task_management/core/test_data_consolidator.py
```

Tests cover:
1. Basic consolidation with complete data
2. Missing data handling with defaults
3. Partial data from different sub-agents
4. Invalid reference validation

All tests pass successfully.
