-- Migration: Add Task Management Agent Tables
-- Version: 1.2.0
-- Description: Creates tables for Task Management Agent to store task processing data,
--              extended tasks, and conflict information
-- Requirements: 11.1, 11.2

-- ============================================================================
-- Task Management Runs Table
-- ============================================================================
-- Stores metadata about each task management processing run
CREATE TABLE IF NOT EXISTS task_management_runs (
    id SERIAL PRIMARY KEY,
    event_id UUID NOT NULL,
    run_timestamp TIMESTAMPTZ DEFAULT NOW(),
    processing_summary JSONB,
    status VARCHAR(50) NOT NULL DEFAULT 'initialized',
    error_log TEXT,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key constraint to event_plans
    CONSTRAINT fk_task_management_event 
        FOREIGN KEY (event_id) 
        REFERENCES event_plans(plan_id) 
        ON DELETE CASCADE
);

-- ============================================================================
-- Extended Tasks Table
-- ============================================================================
-- Stores the extended task list with all enhancements from sub-agents and tools
CREATE TABLE IF NOT EXISTS extended_tasks (
    id SERIAL PRIMARY KEY,
    task_management_run_id INTEGER NOT NULL,
    task_id VARCHAR(100) NOT NULL,
    task_data JSONB NOT NULL,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key constraint to task_management_runs
    CONSTRAINT fk_extended_tasks_run 
        FOREIGN KEY (task_management_run_id) 
        REFERENCES task_management_runs(id) 
        ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate tasks per run
    CONSTRAINT uq_task_per_run 
        UNIQUE (task_management_run_id, task_id)
);

-- ============================================================================
-- Task Conflicts Table
-- ============================================================================
-- Stores detected conflicts (timeline, resource, venue) for tasks
CREATE TABLE IF NOT EXISTS task_conflicts (
    id SERIAL PRIMARY KEY,
    task_management_run_id INTEGER NOT NULL,
    conflict_id VARCHAR(100) NOT NULL,
    conflict_data JSONB NOT NULL,
    resolution_status VARCHAR(50) DEFAULT 'unresolved',
    resolved_at TIMESTAMPTZ,
    created_at TIMESTAMPTZ DEFAULT NOW(),
    updated_at TIMESTAMPTZ DEFAULT NOW(),
    
    -- Foreign key constraint to task_management_runs
    CONSTRAINT fk_task_conflicts_run 
        FOREIGN KEY (task_management_run_id) 
        REFERENCES task_management_runs(id) 
        ON DELETE CASCADE,
    
    -- Unique constraint to prevent duplicate conflicts per run
    CONSTRAINT uq_conflict_per_run 
        UNIQUE (task_management_run_id, conflict_id)
);

-- ============================================================================
-- Performance Indexes
-- ============================================================================

-- Indexes for task_management_runs table
CREATE INDEX IF NOT EXISTS idx_task_mgmt_runs_event_id 
    ON task_management_runs(event_id);

CREATE INDEX IF NOT EXISTS idx_task_mgmt_runs_status 
    ON task_management_runs(status);

CREATE INDEX IF NOT EXISTS idx_task_mgmt_runs_timestamp 
    ON task_management_runs(run_timestamp DESC);

CREATE INDEX IF NOT EXISTS idx_task_mgmt_runs_created 
    ON task_management_runs(created_at DESC);

-- GIN index for JSONB processing_summary for efficient querying
CREATE INDEX IF NOT EXISTS idx_task_mgmt_runs_summary_gin 
    ON task_management_runs USING GIN (processing_summary);

-- Indexes for extended_tasks table
CREATE INDEX IF NOT EXISTS idx_extended_tasks_run_id 
    ON extended_tasks(task_management_run_id);

CREATE INDEX IF NOT EXISTS idx_extended_tasks_task_id 
    ON extended_tasks(task_id);

CREATE INDEX IF NOT EXISTS idx_extended_tasks_created 
    ON extended_tasks(created_at DESC);

-- GIN index for JSONB task_data for efficient querying
CREATE INDEX IF NOT EXISTS idx_extended_tasks_data_gin 
    ON extended_tasks USING GIN (task_data);

-- Partial index for tasks with errors (for quick error lookup)
CREATE INDEX IF NOT EXISTS idx_extended_tasks_errors 
    ON extended_tasks((task_data->>'has_errors')) 
    WHERE (task_data->>'has_errors')::boolean = true;

-- Partial index for tasks requiring manual review
CREATE INDEX IF NOT EXISTS idx_extended_tasks_review 
    ON extended_tasks((task_data->>'requires_manual_review')) 
    WHERE (task_data->>'requires_manual_review')::boolean = true;

-- Indexes for task_conflicts table
CREATE INDEX IF NOT EXISTS idx_task_conflicts_run_id 
    ON task_conflicts(task_management_run_id);

CREATE INDEX IF NOT EXISTS idx_task_conflicts_conflict_id 
    ON task_conflicts(conflict_id);

CREATE INDEX IF NOT EXISTS idx_task_conflicts_status 
    ON task_conflicts(resolution_status);

CREATE INDEX IF NOT EXISTS idx_task_conflicts_created 
    ON task_conflicts(created_at DESC);

-- GIN index for JSONB conflict_data for efficient querying
CREATE INDEX IF NOT EXISTS idx_task_conflicts_data_gin 
    ON task_conflicts USING GIN (conflict_data);

-- Partial index for unresolved conflicts (for quick lookup)
CREATE INDEX IF NOT EXISTS idx_task_conflicts_unresolved 
    ON task_conflicts(resolution_status) 
    WHERE resolution_status = 'unresolved';

-- ============================================================================
-- Triggers for updated_at columns
-- ============================================================================

-- Trigger for task_management_runs
CREATE TRIGGER update_task_management_runs_updated_at
    BEFORE UPDATE ON task_management_runs
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for extended_tasks
CREATE TRIGGER update_extended_tasks_updated_at
    BEFORE UPDATE ON extended_tasks
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- Trigger for task_conflicts
CREATE TRIGGER update_task_conflicts_updated_at
    BEFORE UPDATE ON task_conflicts
    FOR EACH ROW
    EXECUTE FUNCTION update_updated_at_column();

-- ============================================================================
-- Comments for documentation
-- ============================================================================

COMMENT ON TABLE task_management_runs IS 
    'Stores metadata about Task Management Agent processing runs';

COMMENT ON COLUMN task_management_runs.event_id IS 
    'Reference to the event plan being processed';

COMMENT ON COLUMN task_management_runs.processing_summary IS 
    'JSONB containing ProcessingSummary data: total_tasks, tasks_with_errors, processing_time, etc.';

COMMENT ON COLUMN task_management_runs.status IS 
    'Processing status: initialized, processing, completed, failed';

COMMENT ON TABLE extended_tasks IS 
    'Stores extended task list with all enhancements from sub-agents and tools';

COMMENT ON COLUMN extended_tasks.task_data IS 
    'JSONB containing full ExtendedTask structure with all tool enhancements';

COMMENT ON TABLE task_conflicts IS 
    'Stores detected conflicts (timeline, resource, venue) for tasks';

COMMENT ON COLUMN task_conflicts.conflict_data IS 
    'JSONB containing full Conflict structure with affected tasks and resolutions';

COMMENT ON COLUMN task_conflicts.resolution_status IS 
    'Conflict resolution status: unresolved, resolved, ignored';
