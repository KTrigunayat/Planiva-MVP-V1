"""
Task Management Repository

Database persistence layer for Task Management Agent.
Handles saving and retrieving task management runs, extended tasks, and conflicts.
"""

import logging
import json
import time
from typing import Dict, Any, Optional, List
from datetime import datetime
from contextlib import contextmanager
from sqlalchemy import text, Table, Column, Integer, String, DateTime, ForeignKey, Text
from sqlalchemy.dialects.postgresql import JSONB, UUID
from sqlalchemy.exc import SQLAlchemyError, IntegrityError, OperationalError
from sqlalchemy.orm import Session

from .connection import get_sync_session, DatabaseConnectionManager
from .models import Base
from ..error_handling.recovery import RecoveryManager, RecoveryStrategy, RecoveryContext
from ..agents.task_management.models.extended_models import (
    ExtendedTaskList,
    ExtendedTask,
    ProcessingSummary
)
from ..agents.task_management.models.data_models import Conflict

logger = logging.getLogger(__name__)


class TaskManagementRepository:
    """
    Repository for persisting Task Management Agent data.
    
    Handles database operations for:
    - Task management run metadata
    - Extended task lists
    - Conflict data
    
    Implements retry logic with exponential backoff for transient database errors.
    """
    
    def __init__(self, db_manager: Optional[DatabaseConnectionManager] = None):
        """
        Initialize repository with database connection manager.
        
        Args:
            db_manager: Optional database connection manager. If None, uses global instance.
        """
        self.db_manager = db_manager
        self.recovery_manager = RecoveryManager()
        self.max_retries = 3
        self.base_retry_delay = 1.0
        self.max_retry_delay = 30.0
        
        logger.info("TaskManagementRepository initialized")
    
    @contextmanager
    def _get_session(self):
        """Get database session with proper error handling"""
        if self.db_manager:
            with self.db_manager.get_sync_session() as session:
                yield session
        else:
            with get_sync_session() as session:
                yield session
    
    def _execute_with_retry(
        self,
        operation: callable,
        operation_name: str,
        **kwargs
    ) -> Any:
        """
        Execute database operation with retry logic and exponential backoff.
        
        Args:
            operation: Callable to execute
            operation_name: Name of operation for logging
            **kwargs: Arguments to pass to operation
            
        Returns:
            Result of operation
            
        Raises:
            Exception: If operation fails after all retries
        """
        last_exception = None
        
        for attempt in range(self.max_retries):
            try:
                return operation(**kwargs)
            
            except (OperationalError, IntegrityError) as e:
                last_exception = e
                
                # Check if this is a transient error that can be retried
                is_transient = self._is_transient_error(e)
                
                if not is_transient or attempt == self.max_retries - 1:
                    logger.error(
                        f"{operation_name} failed after {attempt + 1} attempts: {e}"
                    )
                    raise
                
                # Calculate delay with exponential backoff
                delay = min(
                    self.base_retry_delay * (2 ** attempt),
                    self.max_retry_delay
                )
                
                logger.warning(
                    f"{operation_name} failed (attempt {attempt + 1}/{self.max_retries}), "
                    f"retrying in {delay:.2f}s: {e}"
                )
                
                # Use recovery manager for retry
                recovery_context = RecoveryContext(
                    strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                    error=e,
                    component="task_management_repository",
                    operation=operation_name,
                    attempt_count=attempt,
                    max_attempts=self.max_retries
                )
                
                recovery_result = self.recovery_manager.execute_recovery(
                    strategy=RecoveryStrategy.RETRY_WITH_BACKOFF,
                    context={'attempt': attempt, 'max_attempts': self.max_retries},
                    error=e,
                    component="task_management_repository",
                    operation=operation_name
                )
                
                if recovery_result.retry_after:
                    time.sleep(recovery_result.retry_after)
                else:
                    time.sleep(delay)
            
            except Exception as e:
                logger.error(f"{operation_name} failed with non-retryable error: {e}")
                raise
        
        # Should not reach here, but just in case
        if last_exception:
            raise last_exception
    
    def _is_transient_error(self, error: Exception) -> bool:
        """
        Check if database error is transient and can be retried.
        
        Args:
            error: Exception to check
            
        Returns:
            True if error is transient, False otherwise
        """
        error_str = str(error).lower()
        
        transient_indicators = [
            'connection',
            'timeout',
            'deadlock',
            'lock',
            'temporary',
            'transient',
            'unavailable'
        ]
        
        return any(indicator in error_str for indicator in transient_indicators)

    
    def save_task_management_run(
        self,
        event_id: str,
        processing_summary: ProcessingSummary,
        status: str = "completed",
        error_log: Optional[str] = None
    ) -> int:
        """
        Persist task management run metadata to database.
        
        Args:
            event_id: Event/plan ID this run is associated with
            processing_summary: Summary of task processing results
            status: Run status (completed, failed, partial)
            error_log: Optional error log if run failed
            
        Returns:
            ID of created task_management_run record
            
        Raises:
            Exception: If save operation fails after retries
        """
        def _save_operation(
            event_id: str,
            processing_summary: ProcessingSummary,
            status: str,
            error_log: Optional[str]
        ) -> int:
            with self._get_session() as session:
                # Convert ProcessingSummary to dict for JSONB storage
                summary_dict = {
                    'total_tasks': processing_summary.total_tasks,
                    'tasks_with_errors': processing_summary.tasks_with_errors,
                    'tasks_with_warnings': processing_summary.tasks_with_warnings,
                    'tasks_requiring_review': processing_summary.tasks_requiring_review,
                    'processing_time': processing_summary.processing_time,
                    'tool_execution_status': processing_summary.tool_execution_status
                }
                
                # Insert task management run
                query = text("""
                    INSERT INTO task_management_runs 
                    (event_id, run_timestamp, processing_summary, status, error_log)
                    VALUES (:event_id, :run_timestamp, :processing_summary, :status, :error_log)
                    RETURNING id
                """)
                
                result = session.execute(
                    query,
                    {
                        'event_id': event_id,
                        'run_timestamp': datetime.utcnow(),
                        'processing_summary': json.dumps(summary_dict),
                        'status': status,
                        'error_log': error_log
                    }
                )
                
                run_id = result.scalar()
                session.commit()
                
                logger.info(
                    f"Saved task management run {run_id} for event {event_id} "
                    f"with status {status}"
                )
                
                return run_id
        
        return self._execute_with_retry(
            operation=_save_operation,
            operation_name="save_task_management_run",
            event_id=event_id,
            processing_summary=processing_summary,
            status=status,
            error_log=error_log
        )
    
    def save_extended_tasks(
        self,
        task_management_run_id: int,
        extended_task_list: ExtendedTaskList
    ) -> int:
        """
        Persist extended task list to database using JSONB.
        
        Args:
            task_management_run_id: ID of task management run
            extended_task_list: Complete extended task list to persist
            
        Returns:
            Number of tasks saved
            
        Raises:
            Exception: If save operation fails after retries
        """
        def _save_operation(
            task_management_run_id: int,
            extended_task_list: ExtendedTaskList
        ) -> int:
            with self._get_session() as session:
                saved_count = 0
                
                for task in extended_task_list.tasks:
                    # Convert ExtendedTask to dict for JSONB storage
                    task_dict = self._serialize_extended_task(task)
                    
                    # Insert extended task
                    query = text("""
                        INSERT INTO extended_tasks 
                        (task_management_run_id, task_id, task_data, created_at, updated_at)
                        VALUES (:run_id, :task_id, :task_data, :created_at, :updated_at)
                        ON CONFLICT (task_management_run_id, task_id) 
                        DO UPDATE SET 
                            task_data = EXCLUDED.task_data,
                            updated_at = EXCLUDED.updated_at
                    """)
                    
                    session.execute(
                        query,
                        {
                            'run_id': task_management_run_id,
                            'task_id': task.task_id,
                            'task_data': json.dumps(task_dict),
                            'created_at': datetime.utcnow(),
                            'updated_at': datetime.utcnow()
                        }
                    )
                    
                    saved_count += 1
                
                session.commit()
                
                logger.info(
                    f"Saved {saved_count} extended tasks for run {task_management_run_id}"
                )
                
                return saved_count
        
        return self._execute_with_retry(
            operation=_save_operation,
            operation_name="save_extended_tasks",
            task_management_run_id=task_management_run_id,
            extended_task_list=extended_task_list
        )
    
    def save_conflicts(
        self,
        task_management_run_id: int,
        conflicts: List[Conflict]
    ) -> int:
        """
        Persist conflicts to database.
        
        Args:
            task_management_run_id: ID of task management run
            conflicts: List of conflicts to persist
            
        Returns:
            Number of conflicts saved
            
        Raises:
            Exception: If save operation fails after retries
        """
        def _save_operation(
            task_management_run_id: int,
            conflicts: List[Conflict]
        ) -> int:
            with self._get_session() as session:
                saved_count = 0
                
                for conflict in conflicts:
                    # Convert Conflict to dict for JSONB storage
                    conflict_dict = {
                        'conflict_id': conflict.conflict_id,
                        'conflict_type': conflict.conflict_type,
                        'severity': conflict.severity,
                        'affected_tasks': conflict.affected_tasks,
                        'conflict_description': conflict.conflict_description,
                        'suggested_resolutions': conflict.suggested_resolutions
                    }
                    
                    # Insert conflict
                    query = text("""
                        INSERT INTO task_conflicts 
                        (task_management_run_id, conflict_id, conflict_data, resolution_status)
                        VALUES (:run_id, :conflict_id, :conflict_data, :resolution_status)
                    """)
                    
                    session.execute(
                        query,
                        {
                            'run_id': task_management_run_id,
                            'conflict_id': conflict.conflict_id,
                            'conflict_data': json.dumps(conflict_dict),
                            'resolution_status': 'unresolved'
                        }
                    )
                    
                    saved_count += 1
                
                session.commit()
                
                logger.info(
                    f"Saved {saved_count} conflicts for run {task_management_run_id}"
                )
                
                return saved_count
        
        return self._execute_with_retry(
            operation=_save_operation,
            operation_name="save_conflicts",
            task_management_run_id=task_management_run_id,
            conflicts=conflicts
        )
    
    def get_task_management_run(
        self,
        event_id: str,
        run_id: Optional[int] = None
    ) -> Optional[Dict[str, Any]]:
        """
        Retrieve task management run data by event_id or run_id.
        
        Args:
            event_id: Event/plan ID to retrieve run for
            run_id: Optional specific run ID. If None, retrieves latest run.
            
        Returns:
            Dictionary containing run data, or None if not found
            
        Raises:
            Exception: If retrieval operation fails after retries
        """
        def _get_operation(
            event_id: str,
            run_id: Optional[int]
        ) -> Optional[Dict[str, Any]]:
            with self._get_session() as session:
                if run_id:
                    # Get specific run
                    query = text("""
                        SELECT id, event_id, run_timestamp, processing_summary, 
                               status, error_log
                        FROM task_management_runs
                        WHERE id = :run_id AND event_id = :event_id
                    """)
                    
                    result = session.execute(
                        query,
                        {'run_id': run_id, 'event_id': event_id}
                    ).fetchone()
                else:
                    # Get latest run for event
                    query = text("""
                        SELECT id, event_id, run_timestamp, processing_summary, 
                               status, error_log
                        FROM task_management_runs
                        WHERE event_id = :event_id
                        ORDER BY run_timestamp DESC
                        LIMIT 1
                    """)
                    
                    result = session.execute(
                        query,
                        {'event_id': event_id}
                    ).fetchone()
                
                if not result:
                    logger.info(
                        f"No task management run found for event {event_id}"
                        + (f" and run_id {run_id}" if run_id else "")
                    )
                    return None
                
                # Convert result to dict
                run_data = {
                    'id': result[0],
                    'event_id': result[1],
                    'run_timestamp': result[2].isoformat() if result[2] else None,
                    'processing_summary': json.loads(result[3]) if result[3] else {},
                    'status': result[4],
                    'error_log': result[5]
                }
                
                # Get associated tasks
                tasks_query = text("""
                    SELECT task_id, task_data, created_at, updated_at
                    FROM extended_tasks
                    WHERE task_management_run_id = :run_id
                    ORDER BY task_id
                """)
                
                tasks_result = session.execute(
                    tasks_query,
                    {'run_id': run_data['id']}
                ).fetchall()
                
                run_data['tasks'] = [
                    {
                        'task_id': row[0],
                        'task_data': json.loads(row[1]) if row[1] else {},
                        'created_at': row[2].isoformat() if row[2] else None,
                        'updated_at': row[3].isoformat() if row[3] else None
                    }
                    for row in tasks_result
                ]
                
                # Get associated conflicts
                conflicts_query = text("""
                    SELECT conflict_id, conflict_data, resolution_status, resolved_at
                    FROM task_conflicts
                    WHERE task_management_run_id = :run_id
                    ORDER BY conflict_id
                """)
                
                conflicts_result = session.execute(
                    conflicts_query,
                    {'run_id': run_data['id']}
                ).fetchall()
                
                run_data['conflicts'] = [
                    {
                        'conflict_id': row[0],
                        'conflict_data': json.loads(row[1]) if row[1] else {},
                        'resolution_status': row[2],
                        'resolved_at': row[3].isoformat() if row[3] else None
                    }
                    for row in conflicts_result
                ]
                
                logger.info(
                    f"Retrieved task management run {run_data['id']} for event {event_id} "
                    f"with {len(run_data['tasks'])} tasks and {len(run_data['conflicts'])} conflicts"
                )
                
                return run_data
        
        return self._execute_with_retry(
            operation=_get_operation,
            operation_name="get_task_management_run",
            event_id=event_id,
            run_id=run_id
        )

    
    def _serialize_extended_task(self, task: ExtendedTask) -> Dict[str, Any]:
        """
        Serialize ExtendedTask to dictionary for JSONB storage.
        
        Args:
            task: ExtendedTask to serialize
            
        Returns:
            Dictionary representation of task
        """
        task_dict = {
            'task_id': task.task_id,
            'task_name': task.task_name,
            'task_description': task.task_description,
            'priority_level': task.priority_level,
            'priority_score': task.priority_score,
            'granularity_level': task.granularity_level,
            'parent_task_id': task.parent_task_id,
            'sub_tasks': task.sub_tasks,
            'dependencies': task.dependencies,
            'resources_required': [
                {
                    'resource_type': r.resource_type,
                    'resource_id': r.resource_id,
                    'resource_name': r.resource_name,
                    'quantity_required': r.quantity_required,
                    'availability_constraint': r.availability_constraint
                }
                for r in task.resources_required
            ],
            'timeline': None,
            'llm_enhancements': task.llm_enhancements,
            'assigned_vendors': [
                {
                    'task_id': v.task_id,
                    'vendor_id': v.vendor_id,
                    'vendor_name': v.vendor_name,
                    'vendor_type': v.vendor_type,
                    'fitness_score': v.fitness_score,
                    'assignment_rationale': v.assignment_rationale,
                    'requires_manual_assignment': v.requires_manual_assignment
                }
                for v in task.assigned_vendors
            ],
            'logistics_status': None,
            'conflicts': [
                {
                    'conflict_id': c.conflict_id,
                    'conflict_type': c.conflict_type,
                    'severity': c.severity,
                    'affected_tasks': c.affected_tasks,
                    'conflict_description': c.conflict_description,
                    'suggested_resolutions': c.suggested_resolutions
                }
                for c in task.conflicts
            ],
            'venue_info': None,
            'has_errors': task.has_errors,
            'has_warnings': task.has_warnings,
            'requires_manual_review': task.requires_manual_review,
            'error_messages': task.error_messages,
            'warning_messages': task.warning_messages
        }
        
        # Serialize timeline if present
        if task.timeline:
            task_dict['timeline'] = {
                'task_id': task.timeline.task_id,
                'start_time': task.timeline.start_time.isoformat(),
                'end_time': task.timeline.end_time.isoformat(),
                'duration': task.timeline.duration.total_seconds(),
                'buffer_time': task.timeline.buffer_time.total_seconds(),
                'scheduling_constraints': task.timeline.scheduling_constraints
            }
        
        # Serialize logistics status if present
        if task.logistics_status:
            task_dict['logistics_status'] = {
                'task_id': task.logistics_status.task_id,
                'transportation_status': task.logistics_status.transportation_status,
                'transportation_notes': task.logistics_status.transportation_notes,
                'equipment_status': task.logistics_status.equipment_status,
                'equipment_notes': task.logistics_status.equipment_notes,
                'setup_status': task.logistics_status.setup_status,
                'setup_notes': task.logistics_status.setup_notes,
                'overall_feasibility': task.logistics_status.overall_feasibility,
                'issues': task.logistics_status.issues
            }
        
        # Serialize venue info if present
        if task.venue_info:
            task_dict['venue_info'] = {
                'task_id': task.venue_info.task_id,
                'venue_id': task.venue_info.venue_id,
                'venue_name': task.venue_info.venue_name,
                'venue_type': task.venue_info.venue_type,
                'capacity': task.venue_info.capacity,
                'available_equipment': task.venue_info.available_equipment,
                'setup_time_required': task.venue_info.setup_time_required.total_seconds(),
                'teardown_time_required': task.venue_info.teardown_time_required.total_seconds(),
                'access_restrictions': task.venue_info.access_restrictions,
                'requires_venue_selection': task.venue_info.requires_venue_selection
            }
        
        return task_dict
    
    def save_complete_task_management_data(
        self,
        event_id: str,
        extended_task_list: ExtendedTaskList,
        status: str = "completed",
        error_log: Optional[str] = None
    ) -> Dict[str, Any]:
        """
        Save complete task management data in a single transaction.
        
        This is a convenience method that saves the run metadata, tasks, and conflicts
        in a single database transaction for atomicity.
        
        Args:
            event_id: Event/plan ID
            extended_task_list: Complete extended task list
            status: Run status
            error_log: Optional error log
            
        Returns:
            Dictionary with run_id and counts of saved items
            
        Raises:
            Exception: If save operation fails after retries
        """
        def _save_complete_operation(
            event_id: str,
            extended_task_list: ExtendedTaskList,
            status: str,
            error_log: Optional[str]
        ) -> Dict[str, Any]:
            with self._get_session() as session:
                try:
                    # Save run metadata
                    summary_dict = {
                        'total_tasks': extended_task_list.processing_summary.total_tasks,
                        'tasks_with_errors': extended_task_list.processing_summary.tasks_with_errors,
                        'tasks_with_warnings': extended_task_list.processing_summary.tasks_with_warnings,
                        'tasks_requiring_review': extended_task_list.processing_summary.tasks_requiring_review,
                        'processing_time': extended_task_list.processing_summary.processing_time,
                        'tool_execution_status': extended_task_list.processing_summary.tool_execution_status
                    }
                    
                    run_query = text("""
                        INSERT INTO task_management_runs 
                        (event_id, run_timestamp, processing_summary, status, error_log)
                        VALUES (:event_id, :run_timestamp, :processing_summary, :status, :error_log)
                        RETURNING id
                    """)
                    
                    result = session.execute(
                        run_query,
                        {
                            'event_id': event_id,
                            'run_timestamp': datetime.utcnow(),
                            'processing_summary': json.dumps(summary_dict),
                            'status': status,
                            'error_log': error_log
                        }
                    )
                    
                    run_id = result.scalar()
                    
                    # Save tasks
                    tasks_saved = 0
                    for task in extended_task_list.tasks:
                        task_dict = self._serialize_extended_task(task)
                        
                        task_query = text("""
                            INSERT INTO extended_tasks 
                            (task_management_run_id, task_id, task_data, created_at, updated_at)
                            VALUES (:run_id, :task_id, :task_data, :created_at, :updated_at)
                            ON CONFLICT (task_management_run_id, task_id) 
                            DO UPDATE SET 
                                task_data = EXCLUDED.task_data,
                                updated_at = EXCLUDED.updated_at
                        """)
                        
                        session.execute(
                            task_query,
                            {
                                'run_id': run_id,
                                'task_id': task.task_id,
                                'task_data': json.dumps(task_dict),
                                'created_at': datetime.utcnow(),
                                'updated_at': datetime.utcnow()
                            }
                        )
                        
                        tasks_saved += 1
                    
                    # Save conflicts
                    conflicts_saved = 0
                    all_conflicts = []
                    
                    # Collect all conflicts from tasks
                    for task in extended_task_list.tasks:
                        all_conflicts.extend(task.conflicts)
                    
                    # Remove duplicates based on conflict_id
                    unique_conflicts = {c.conflict_id: c for c in all_conflicts}.values()
                    
                    for conflict in unique_conflicts:
                        conflict_dict = {
                            'conflict_id': conflict.conflict_id,
                            'conflict_type': conflict.conflict_type,
                            'severity': conflict.severity,
                            'affected_tasks': conflict.affected_tasks,
                            'conflict_description': conflict.conflict_description,
                            'suggested_resolutions': conflict.suggested_resolutions
                        }
                        
                        conflict_query = text("""
                            INSERT INTO task_conflicts 
                            (task_management_run_id, conflict_id, conflict_data, resolution_status)
                            VALUES (:run_id, :conflict_id, :conflict_data, :resolution_status)
                        """)
                        
                        session.execute(
                            conflict_query,
                            {
                                'run_id': run_id,
                                'conflict_id': conflict.conflict_id,
                                'conflict_data': json.dumps(conflict_dict),
                                'resolution_status': 'unresolved'
                            }
                        )
                        
                        conflicts_saved += 1
                    
                    # Commit transaction
                    session.commit()
                    
                    result_data = {
                        'run_id': run_id,
                        'tasks_saved': tasks_saved,
                        'conflicts_saved': conflicts_saved,
                        'status': status
                    }
                    
                    logger.info(
                        f"Saved complete task management data for event {event_id}: "
                        f"run_id={run_id}, tasks={tasks_saved}, conflicts={conflicts_saved}"
                    )
                    
                    return result_data
                    
                except Exception as e:
                    session.rollback()
                    logger.error(f"Failed to save complete task management data: {e}")
                    raise
        
        return self._execute_with_retry(
            operation=_save_complete_operation,
            operation_name="save_complete_task_management_data",
            event_id=event_id,
            extended_task_list=extended_task_list,
            status=status,
            error_log=error_log
        )
    
    def update_conflict_resolution(
        self,
        conflict_id: str,
        resolution_status: str,
        resolved_at: Optional[datetime] = None
    ) -> bool:
        """
        Update conflict resolution status.
        
        Args:
            conflict_id: ID of conflict to update
            resolution_status: New resolution status (resolved, in_progress, unresolved)
            resolved_at: Optional timestamp when conflict was resolved
            
        Returns:
            True if update successful, False otherwise
            
        Raises:
            Exception: If update operation fails after retries
        """
        def _update_operation(
            conflict_id: str,
            resolution_status: str,
            resolved_at: Optional[datetime]
        ) -> bool:
            with self._get_session() as session:
                query = text("""
                    UPDATE task_conflicts
                    SET resolution_status = :resolution_status,
                        resolved_at = :resolved_at
                    WHERE conflict_id = :conflict_id
                """)
                
                result = session.execute(
                    query,
                    {
                        'conflict_id': conflict_id,
                        'resolution_status': resolution_status,
                        'resolved_at': resolved_at or datetime.utcnow()
                    }
                )
                
                session.commit()
                
                updated = result.rowcount > 0
                
                if updated:
                    logger.info(
                        f"Updated conflict {conflict_id} resolution status to {resolution_status}"
                    )
                else:
                    logger.warning(f"No conflict found with ID {conflict_id}")
                
                return updated
        
        return self._execute_with_retry(
            operation=_update_operation,
            operation_name="update_conflict_resolution",
            conflict_id=conflict_id,
            resolution_status=resolution_status,
            resolved_at=resolved_at
        )
