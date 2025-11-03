# Task Management Repository

## Overview

The `TaskManagementRepository` provides database persistence for the Task Management Agent. It handles saving and retrieving task management runs, extended tasks, and conflict data with built-in retry logic and error recovery.

## Features

- **Atomic Transactions**: All database operations use transactions for data consistency
- **Retry Logic**: Automatic retry with exponential backoff for transient database errors
- **Error Recovery**: Integration with the error recovery system for robust failure handling
- **JSONB Storage**: Efficient storage of complex task data structures using PostgreSQL JSONB
- **Batch Operations**: Support for saving complete task management data in a single transaction

## Database Schema

### Tables

#### `task_management_runs`
Stores metadata about each task management processing run.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| event_id | UUID | Reference to event plan |
| run_timestamp | TIMESTAMPTZ | When the run occurred |
| processing_summary | JSONB | Summary of processing results |
| status | VARCHAR(50) | Run status (completed, failed, partial) |
| error_log | TEXT | Error log if run failed |
| created_at | TIMESTAMPTZ | Record creation time |
| updated_at | TIMESTAMPTZ | Record update time |

#### `extended_tasks`
Stores extended task list with all enhancements from sub-agents and tools.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| task_management_run_id | INTEGER | Foreign key to task_management_runs |
| task_id | VARCHAR(100) | Unique task identifier |
| task_data | JSONB | Complete ExtendedTask structure |
| created_at | TIMESTAMPTZ | Record creation time |
| updated_at | TIMESTAMPTZ | Record update time |

#### `task_conflicts`
Stores detected conflicts (timeline, resource, venue) for tasks.

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| task_management_run_id | INTEGER | Foreign key to task_management_runs |
| conflict_id | VARCHAR(100) | Unique conflict identifier |
| conflict_data | JSONB | Complete Conflict structure |
| resolution_status | VARCHAR(50) | Resolution status (unresolved, resolved, ignored) |
| resolved_at | TIMESTAMPTZ | When conflict was resolved |
| created_at | TIMESTAMPTZ | Record creation time |
| updated_at | TIMESTAMPTZ | Record update time |

## Usage

### Basic Usage

```python
from event_planning_agent_v2.database.task_management_repository import TaskManagementRepository
from event_planning_agent_v2.agents.task_management.models.extended_models import (
    ExtendedTaskList,
    ProcessingSummary
)

# Initialize repository
repo = TaskManagementRepository()

# Save complete task management data
result = repo.save_complete_task_management_data(
    event_id='event_123',
    extended_task_list=extended_task_list,
    status='completed'
)

print(f"Saved run {result['run_id']} with {result['tasks_saved']} tasks")
```

### Individual Operations

```python
# Save run metadata
run_id = repo.save_task_management_run(
    event_id='event_123',
    processing_summary=processing_summary,
    status='completed'
)

# Save extended tasks
tasks_saved = repo.save_extended_tasks(
    task_management_run_id=run_id,
    extended_task_list=extended_task_list
)

# Save conflicts
conflicts_saved = repo.save_conflicts(
    task_management_run_id=run_id,
    conflicts=conflicts
)

# Retrieve run data
run_data = repo.get_task_management_run(
    event_id='event_123'
)

# Update conflict resolution
repo.update_conflict_resolution(
    conflict_id='conflict_001',
    resolution_status='resolved'
)
```

### With Custom Database Manager

```python
from event_planning_agent_v2.database.connection import DatabaseConnectionManager

# Use custom database manager
db_manager = DatabaseConnectionManager(database_url='postgresql://...')
repo = TaskManagementRepository(db_manager=db_manager)
```

## API Reference

### `TaskManagementRepository`

#### `__init__(db_manager: Optional[DatabaseConnectionManager] = None)`
Initialize repository with optional database connection manager.

#### `save_task_management_run(event_id: str, processing_summary: ProcessingSummary, status: str = "completed", error_log: Optional[str] = None) -> int`
Persist task management run metadata to database.

**Returns**: ID of created task_management_run record

#### `save_extended_tasks(task_management_run_id: int, extended_task_list: ExtendedTaskList) -> int`
Persist extended task list to database using JSONB.

**Returns**: Number of tasks saved

#### `save_conflicts(task_management_run_id: int, conflicts: List[Conflict]) -> int`
Persist conflicts to database.

**Returns**: Number of conflicts saved

#### `get_task_management_run(event_id: str, run_id: Optional[int] = None) -> Optional[Dict[str, Any]]`
Retrieve task management run data by event_id or run_id.

**Returns**: Dictionary containing run data with tasks and conflicts, or None if not found

#### `save_complete_task_management_data(event_id: str, extended_task_list: ExtendedTaskList, status: str = "completed", error_log: Optional[str] = None) -> Dict[str, Any]`
Save complete task management data in a single transaction.

**Returns**: Dictionary with run_id and counts of saved items

#### `update_conflict_resolution(conflict_id: str, resolution_status: str, resolved_at: Optional[datetime] = None) -> bool`
Update conflict resolution status.

**Returns**: True if update successful, False otherwise

## Error Handling

The repository implements comprehensive error handling:

1. **Transient Error Detection**: Automatically detects transient database errors (connection timeouts, deadlocks, etc.)
2. **Exponential Backoff**: Retries failed operations with exponential backoff (1s, 2s, 4s, up to 30s max)
3. **Recovery Integration**: Uses the RecoveryManager for coordinated error recovery
4. **Transaction Rollback**: Automatically rolls back transactions on errors
5. **Detailed Logging**: Logs all operations, errors, and retries for debugging

### Retry Configuration

```python
repo = TaskManagementRepository()
repo.max_retries = 5  # Default: 3
repo.base_retry_delay = 2.0  # Default: 1.0
repo.max_retry_delay = 60.0  # Default: 30.0
```

## Data Serialization

The repository automatically serializes complex data structures to JSONB:

- **ExtendedTask**: Complete task with all enhancements
- **ProcessingSummary**: Summary of task processing results
- **Conflict**: Conflict data with affected tasks and resolutions
- **Timeline**: Task timeline with start/end times
- **VendorAssignment**: Vendor-to-task assignments
- **LogisticsStatus**: Logistics verification results
- **VenueInfo**: Venue information for tasks

All datetime objects are converted to ISO format strings, and timedelta objects are converted to seconds.

## Performance Considerations

1. **Indexes**: The migration script creates indexes on frequently queried columns
2. **GIN Indexes**: JSONB columns have GIN indexes for efficient querying
3. **Partial Indexes**: Special indexes for tasks with errors or requiring review
4. **Batch Operations**: Use `save_complete_task_management_data()` for atomic batch saves
5. **Connection Pooling**: Leverages the DatabaseConnectionManager's connection pooling

## Testing

Run the simple tests to verify functionality:

```bash
python event_planning_agent_v2/tests/unit/test_task_management_repository_simple.py
```

For full integration tests (requires database):

```bash
pytest event_planning_agent_v2/tests/unit/test_task_management_repository.py -v
```

## Migration

To create the required database tables, run the migration script:

```bash
psql -U your_user -d your_database -f event_planning_agent_v2/database/migrations/add_task_management_tables.sql
```

## Requirements

- PostgreSQL 12+
- SQLAlchemy 2.0+
- Python 3.9+

## Related Components

- `TaskManagementAgent`: Main agent that uses this repository
- `ExtendedTaskList`: Data model for extended tasks
- `ProcessingSummary`: Data model for processing summary
- `RecoveryManager`: Error recovery system
- `DatabaseConnectionManager`: Database connection management
