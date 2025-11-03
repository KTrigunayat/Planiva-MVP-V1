# Database Migrations

This directory contains SQL migration scripts for the Event Planning Agent v2 database schema.

## Migration Files

### add_task_management_tables.sql (v1.2.0)

Creates the database schema for the Task Management Agent component.

**Tables Created:**

1. **task_management_runs**
   - Stores metadata about each Task Management Agent processing run
   - Links to event_plans via event_id foreign key
   - Contains processing summary, status, and error logs
   - Cascading delete when parent event is deleted

2. **extended_tasks**
   - Stores the extended task list with all enhancements from sub-agents and tools
   - Links to task_management_runs via task_management_run_id foreign key
   - Stores full task data as JSONB for flexibility
   - Unique constraint prevents duplicate tasks per run
   - Cascading delete when parent run is deleted

3. **task_conflicts**
   - Stores detected conflicts (timeline, resource, venue) for tasks
   - Links to task_management_runs via task_management_run_id foreign key
   - Stores full conflict data as JSONB
   - Tracks resolution status and timestamp
   - Unique constraint prevents duplicate conflicts per run
   - Cascading delete when parent run is deleted

**Indexes Created:**

Performance indexes for efficient querying:
- Standard B-tree indexes on foreign keys, status fields, and timestamps
- GIN indexes on JSONB columns for efficient JSON querying
- Partial indexes for tasks with errors and tasks requiring manual review
- Partial index for unresolved conflicts

**Triggers:**

- Automatic `updated_at` timestamp updates on all three tables

## Running Migrations

### Automatic Migration (Recommended)

Run all pending migrations using the migration manager:

```bash
cd event_planning_agent_v2
python -m database.migrations
```

### Check Current Version

```bash
python -m database.migrations --version
```

### View Migration History

```bash
python -m database.migrations --history
```

### Manual Migration

If you need to run the SQL migration manually:

```bash
psql -U eventuser -d eventdb -f database/migrations/add_task_management_tables.sql
```

## Migration Sequence

Migrations are applied in version order:
1. v1.0.0 - LangGraph state management tables
2. v1.1.0 - Vendor table performance indexes
3. v1.2.0 - Task Management Agent tables (this migration)

## Requirements Addressed

This migration addresses the following requirements from the Task Management Agent specification:

- **Requirement 11.1**: Database persistence for extended task list
- **Requirement 11.2**: Database schema for task management data

## Schema Details

### task_management_runs

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| event_id | UUID | Foreign key to event_plans |
| run_timestamp | TIMESTAMPTZ | When the processing run started |
| processing_summary | JSONB | Summary data (total_tasks, errors, etc.) |
| status | VARCHAR(50) | Processing status (initialized, processing, completed, failed) |
| error_log | TEXT | Error messages if processing failed |
| created_at | TIMESTAMPTZ | Record creation timestamp |
| updated_at | TIMESTAMPTZ | Record update timestamp |

### extended_tasks

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| task_management_run_id | INTEGER | Foreign key to task_management_runs |
| task_id | VARCHAR(100) | Unique task identifier |
| task_data | JSONB | Full ExtendedTask structure |
| created_at | TIMESTAMPTZ | Record creation timestamp |
| updated_at | TIMESTAMPTZ | Record update timestamp |

### task_conflicts

| Column | Type | Description |
|--------|------|-------------|
| id | SERIAL | Primary key |
| task_management_run_id | INTEGER | Foreign key to task_management_runs |
| conflict_id | VARCHAR(100) | Unique conflict identifier |
| conflict_data | JSONB | Full Conflict structure |
| resolution_status | VARCHAR(50) | Status (unresolved, resolved, ignored) |
| resolved_at | TIMESTAMPTZ | When conflict was resolved |
| created_at | TIMESTAMPTZ | Record creation timestamp |
| updated_at | TIMESTAMPTZ | Record update timestamp |

## Rollback

To rollback this migration, you would need to:

```sql
DROP TABLE IF EXISTS task_conflicts CASCADE;
DROP TABLE IF EXISTS extended_tasks CASCADE;
DROP TABLE IF EXISTS task_management_runs CASCADE;
```

**Note:** This will permanently delete all Task Management Agent data. Use with caution.

## Testing

After running the migration, verify the tables were created:

```sql
-- Check tables exist
SELECT table_name 
FROM information_schema.tables 
WHERE table_schema = 'public' 
  AND table_name IN ('task_management_runs', 'extended_tasks', 'task_conflicts');

-- Check indexes
SELECT indexname, tablename 
FROM pg_indexes 
WHERE tablename IN ('task_management_runs', 'extended_tasks', 'task_conflicts');

-- Check foreign key constraints
SELECT conname, conrelid::regclass, confrelid::regclass
FROM pg_constraint
WHERE contype = 'f' 
  AND conrelid::regclass::text IN ('task_management_runs', 'extended_tasks', 'task_conflicts');
```
