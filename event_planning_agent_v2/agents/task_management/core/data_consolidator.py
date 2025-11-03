"""
Data Consolidator for Task Management Agent

Consolidates outputs from three sub-agents (Prioritization, Granularity, Resource & Dependency)
into a unified ConsolidatedTaskData structure. Handles missing or inconsistent data gracefully
by logging errors and continuing with partial data when possible.

The consolidation process:
1. Merge prioritization data (priority levels, scores, rationale)
2. Merge granularity data (task descriptions, decomposition, duration estimates)
3. Merge dependency data (dependencies, resources, conflicts)
4. Validate consolidated data for completeness and consistency
5. Handle missing data by logging and marking affected tasks
"""

import logging
from typing import List, Dict, Any, Optional, Set
from datetime import timedelta

from ..models.task_models import PrioritizedTask, GranularTask, TaskWithDependencies
from ..models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
from ..models.data_models import Resource
from ..exceptions import ConsolidationError, SubAgentDataError

logger = logging.getLogger(__name__)


class DataConsolidator:
    """
    Consolidates data from three sub-agents into unified ConsolidatedTaskData.
    
    Handles missing or inconsistent data gracefully by:
    - Logging errors with detailed context
    - Using default values for missing fields
    - Marking tasks with data quality issues
    - Continuing processing with partial data
    """
    
    def __init__(self):
        """Initialize DataConsolidator"""
        self.consolidation_errors: List[Dict[str, Any]] = []
        self.warnings: List[Dict[str, Any]] = []
    
    def consolidate_sub_agent_data(
        self,
        prioritized_tasks: List[PrioritizedTask],
        granular_tasks: List[GranularTask],
        dependency_tasks: List[TaskWithDependencies],
        event_context: Optional[Dict[str, Any]] = None
    ) -> ConsolidatedTaskData:
        """
        Consolidate outputs from all three sub-agents into unified data structure.
        
        Args:
            prioritized_tasks: Output from Prioritization Agent
            granular_tasks: Output from Granularity Agent
            dependency_tasks: Output from Resource & Dependency Agent
            event_context: Optional event context information
            
        Returns:
            ConsolidatedTaskData with merged task information
            
        Raises:
            ConsolidationError: If consolidation fails critically
        """
        logger.info("Starting data consolidation from sub-agents")
        logger.debug(f"Input counts - Prioritized: {len(prioritized_tasks)}, "
                    f"Granular: {len(granular_tasks)}, Dependencies: {len(dependency_tasks)}")
        
        # Reset error tracking
        self.consolidation_errors = []
        self.warnings = []
        
        try:
            # Build task ID mappings for efficient lookup
            priority_map = {task.task_id: task for task in prioritized_tasks}
            granular_map = {task.task_id: task for task in granular_tasks}
            dependency_map = {task.task_id: task for task in dependency_tasks}
            
            # Get all unique task IDs from all sources
            all_task_ids = self._get_all_task_ids(
                prioritized_tasks, granular_tasks, dependency_tasks
            )
            
            logger.info(f"Found {len(all_task_ids)} unique tasks across all sub-agents")
            
            # Consolidate each task
            consolidated_tasks: List[ConsolidatedTask] = []
            for task_id in all_task_ids:
                try:
                    consolidated_task = self._consolidate_single_task(
                        task_id,
                        priority_map.get(task_id),
                        granular_map.get(task_id),
                        dependency_map.get(task_id)
                    )
                    consolidated_tasks.append(consolidated_task)
                except Exception as e:
                    error_msg = f"Failed to consolidate task {task_id}: {str(e)}"
                    logger.error(error_msg)
                    self.consolidation_errors.append({
                        'task_id': task_id,
                        'error': str(e),
                        'error_type': type(e).__name__
                    })
                    # Continue with next task
            
            # Validate consolidated data
            self._validate_consolidated_data(consolidated_tasks)
            
            # Create consolidated data object
            consolidated_data = ConsolidatedTaskData(
                tasks=consolidated_tasks,
                event_context=event_context or {},
                processing_metadata={
                    'total_tasks': len(consolidated_tasks),
                    'prioritized_count': len(prioritized_tasks),
                    'granular_count': len(granular_tasks),
                    'dependency_count': len(dependency_tasks),
                    'errors': self.consolidation_errors,
                    'warnings': self.warnings,
                    'tasks_with_missing_data': len(self.consolidation_errors)
                }
            )
            
            logger.info(f"Consolidation complete: {len(consolidated_tasks)} tasks, "
                       f"{len(self.consolidation_errors)} errors, {len(self.warnings)} warnings")
            
            return consolidated_data
            
        except Exception as e:
            error_msg = f"Critical error during data consolidation: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ConsolidationError(
                error_msg,
                details={
                    'prioritized_count': len(prioritized_tasks),
                    'granular_count': len(granular_tasks),
                    'dependency_count': len(dependency_tasks),
                    'errors': self.consolidation_errors
                }
            )
    
    def _get_all_task_ids(
        self,
        prioritized_tasks: List[PrioritizedTask],
        granular_tasks: List[GranularTask],
        dependency_tasks: List[TaskWithDependencies]
    ) -> Set[str]:
        """
        Get all unique task IDs from all sub-agent outputs.
        
        Args:
            prioritized_tasks: Tasks from Prioritization Agent
            granular_tasks: Tasks from Granularity Agent
            dependency_tasks: Tasks from Resource & Dependency Agent
            
        Returns:
            Set of all unique task IDs
        """
        task_ids = set()
        
        for task in prioritized_tasks:
            task_ids.add(task.task_id)
        
        for task in granular_tasks:
            task_ids.add(task.task_id)
        
        for task in dependency_tasks:
            task_ids.add(task.task_id)
        
        return task_ids
    
    def _consolidate_single_task(
        self,
        task_id: str,
        priority_task: Optional[PrioritizedTask],
        granular_task: Optional[GranularTask],
        dependency_task: Optional[TaskWithDependencies]
    ) -> ConsolidatedTask:
        """
        Consolidate data for a single task from all three sub-agents.
        
        Args:
            task_id: Unique task identifier
            priority_task: Task data from Prioritization Agent (may be None)
            granular_task: Task data from Granularity Agent (may be None)
            dependency_task: Task data from Resource & Dependency Agent (may be None)
            
        Returns:
            ConsolidatedTask with merged data
        """
        # Merge prioritization data
        priority_data = self._merge_prioritization_data(task_id, priority_task)
        
        # Merge granularity data
        granularity_data = self._merge_granularity_data(task_id, granular_task)
        
        # Merge dependency data
        dependency_data = self._merge_dependency_data(task_id, dependency_task)
        
        # Create consolidated task
        consolidated_task = ConsolidatedTask(
            # From Prioritization Agent
            task_id=task_id,
            task_name=priority_data['task_name'],
            priority_level=priority_data['priority_level'],
            priority_score=priority_data['priority_score'],
            priority_rationale=priority_data['priority_rationale'],
            
            # From Granularity Agent
            parent_task_id=granularity_data['parent_task_id'],
            task_description=granularity_data['task_description'],
            granularity_level=granularity_data['granularity_level'],
            estimated_duration=granularity_data['estimated_duration'],
            sub_tasks=granularity_data['sub_tasks'],
            
            # From Resource & Dependency Agent
            dependencies=dependency_data['dependencies'],
            resources_required=dependency_data['resources_required'],
            resource_conflicts=dependency_data['resource_conflicts']
        )
        
        return consolidated_task

    
    def _merge_prioritization_data(
        self,
        task_id: str,
        priority_task: Optional[PrioritizedTask]
    ) -> Dict[str, Any]:
        """
        Merge prioritization data from Prioritization Agent.
        
        Args:
            task_id: Task identifier
            priority_task: Task data from Prioritization Agent (may be None)
            
        Returns:
            Dictionary with prioritization fields (uses defaults if data missing)
        """
        if priority_task is None:
            warning_msg = f"Missing prioritization data for task {task_id}, using defaults"
            logger.warning(warning_msg)
            self.warnings.append({
                'task_id': task_id,
                'warning': 'Missing prioritization data',
                'sub_agent': 'PrioritizationAgent'
            })
            
            return {
                'task_name': f"Task {task_id}",
                'priority_level': "Medium",  # Default priority
                'priority_score': 0.5,  # Default score
                'priority_rationale': "No prioritization data available"
            }
        
        # Validate priority data
        if not priority_task.task_name:
            logger.warning(f"Task {task_id} has empty task_name")
            self.warnings.append({
                'task_id': task_id,
                'warning': 'Empty task_name',
                'sub_agent': 'PrioritizationAgent'
            })
        
        return {
            'task_name': priority_task.task_name or f"Task {task_id}",
            'priority_level': priority_task.priority_level,
            'priority_score': priority_task.priority_score,
            'priority_rationale': priority_task.priority_rationale
        }
    
    def _merge_granularity_data(
        self,
        task_id: str,
        granular_task: Optional[GranularTask]
    ) -> Dict[str, Any]:
        """
        Merge granularity data from Granularity Agent.
        
        Args:
            task_id: Task identifier
            granular_task: Task data from Granularity Agent (may be None)
            
        Returns:
            Dictionary with granularity fields (uses defaults if data missing)
        """
        if granular_task is None:
            warning_msg = f"Missing granularity data for task {task_id}, using defaults"
            logger.warning(warning_msg)
            self.warnings.append({
                'task_id': task_id,
                'warning': 'Missing granularity data',
                'sub_agent': 'GranularityAgent'
            })
            
            return {
                'parent_task_id': None,
                'task_description': f"No description available for task {task_id}",
                'granularity_level': 0,  # Top-level task by default
                'estimated_duration': timedelta(hours=1),  # Default 1 hour
                'sub_tasks': []
            }
        
        # Validate granularity data
        if not granular_task.task_description:
            logger.warning(f"Task {task_id} has empty task_description")
            self.warnings.append({
                'task_id': task_id,
                'warning': 'Empty task_description',
                'sub_agent': 'GranularityAgent'
            })
        
        if granular_task.estimated_duration.total_seconds() <= 0:
            logger.warning(f"Task {task_id} has invalid estimated_duration, using default")
            self.warnings.append({
                'task_id': task_id,
                'warning': 'Invalid estimated_duration',
                'sub_agent': 'GranularityAgent'
            })
            estimated_duration = timedelta(hours=1)
        else:
            estimated_duration = granular_task.estimated_duration
        
        return {
            'parent_task_id': granular_task.parent_task_id,
            'task_description': granular_task.task_description or f"No description for {task_id}",
            'granularity_level': granular_task.granularity_level,
            'estimated_duration': estimated_duration,
            'sub_tasks': granular_task.sub_tasks or []
        }
    
    def _merge_dependency_data(
        self,
        task_id: str,
        dependency_task: Optional[TaskWithDependencies]
    ) -> Dict[str, Any]:
        """
        Merge dependency and resource data from Resource & Dependency Agent.
        
        Args:
            task_id: Task identifier
            dependency_task: Task data from Resource & Dependency Agent (may be None)
            
        Returns:
            Dictionary with dependency and resource fields (uses defaults if data missing)
        """
        if dependency_task is None:
            warning_msg = f"Missing dependency data for task {task_id}, using defaults"
            logger.warning(warning_msg)
            self.warnings.append({
                'task_id': task_id,
                'warning': 'Missing dependency data',
                'sub_agent': 'ResourceDependencyAgent'
            })
            
            return {
                'dependencies': [],
                'resources_required': [],
                'resource_conflicts': []
            }
        
        # Validate dependency data
        if dependency_task.dependencies is None:
            logger.warning(f"Task {task_id} has None dependencies, using empty list")
            dependencies = []
        else:
            dependencies = dependency_task.dependencies
        
        if dependency_task.resources_required is None:
            logger.warning(f"Task {task_id} has None resources_required, using empty list")
            resources_required = []
        else:
            resources_required = dependency_task.resources_required
        
        if dependency_task.resource_conflicts is None:
            logger.warning(f"Task {task_id} has None resource_conflicts, using empty list")
            resource_conflicts = []
        else:
            resource_conflicts = dependency_task.resource_conflicts
        
        return {
            'dependencies': dependencies,
            'resources_required': resources_required,
            'resource_conflicts': resource_conflicts
        }
    
    def _validate_consolidated_data(self, consolidated_tasks: List[ConsolidatedTask]) -> None:
        """
        Validate consolidated data for missing or inconsistent information.
        
        Checks for:
        - Tasks with missing critical fields
        - Invalid dependency references
        - Circular dependencies
        - Inconsistent parent-child relationships
        
        Args:
            consolidated_tasks: List of consolidated tasks to validate
        """
        logger.info(f"Validating {len(consolidated_tasks)} consolidated tasks")
        
        if not consolidated_tasks:
            logger.warning("No consolidated tasks to validate")
            return
        
        # Build task ID set for validation
        task_ids = {task.task_id for task in consolidated_tasks}
        
        # Validate each task
        for task in consolidated_tasks:
            # Check for invalid dependency references
            for dep_id in task.dependencies:
                if dep_id not in task_ids:
                    warning_msg = f"Task {task.task_id} has invalid dependency reference: {dep_id}"
                    logger.warning(warning_msg)
                    self.warnings.append({
                        'task_id': task.task_id,
                        'warning': f'Invalid dependency reference: {dep_id}',
                        'validation': 'dependency_reference'
                    })
            
            # Check for invalid sub-task references
            for sub_task_id in task.sub_tasks:
                if sub_task_id not in task_ids:
                    warning_msg = f"Task {task.task_id} has invalid sub-task reference: {sub_task_id}"
                    logger.warning(warning_msg)
                    self.warnings.append({
                        'task_id': task.task_id,
                        'warning': f'Invalid sub-task reference: {sub_task_id}',
                        'validation': 'sub_task_reference'
                    })
            
            # Check for invalid parent task reference
            if task.parent_task_id and task.parent_task_id not in task_ids:
                warning_msg = f"Task {task.task_id} has invalid parent_task_id: {task.parent_task_id}"
                logger.warning(warning_msg)
                self.warnings.append({
                    'task_id': task.task_id,
                    'warning': f'Invalid parent_task_id: {task.parent_task_id}',
                    'validation': 'parent_reference'
                })
        
        # Check for circular dependencies
        self._check_circular_dependencies(consolidated_tasks)
        
        logger.info(f"Validation complete: {len(self.warnings)} warnings found")
    
    def _check_circular_dependencies(self, consolidated_tasks: List[ConsolidatedTask]) -> None:
        """
        Check for circular dependencies in the task graph.
        
        Uses depth-first search to detect cycles in the dependency graph.
        
        Args:
            consolidated_tasks: List of consolidated tasks to check
        """
        # Build adjacency list for dependency graph
        dependency_graph: Dict[str, List[str]] = {}
        for task in consolidated_tasks:
            dependency_graph[task.task_id] = task.dependencies
        
        # Track visited nodes and recursion stack
        visited: Set[str] = set()
        rec_stack: Set[str] = set()
        
        def has_cycle(task_id: str) -> bool:
            """DFS helper to detect cycles"""
            visited.add(task_id)
            rec_stack.add(task_id)
            
            # Check all dependencies
            for dep_id in dependency_graph.get(task_id, []):
                if dep_id not in visited:
                    if has_cycle(dep_id):
                        return True
                elif dep_id in rec_stack:
                    # Found a cycle
                    return True
            
            rec_stack.remove(task_id)
            return False
        
        # Check each task for cycles
        for task in consolidated_tasks:
            if task.task_id not in visited:
                if has_cycle(task.task_id):
                    warning_msg = f"Circular dependency detected involving task {task.task_id}"
                    logger.warning(warning_msg)
                    self.warnings.append({
                        'task_id': task.task_id,
                        'warning': 'Circular dependency detected',
                        'validation': 'circular_dependency'
                    })
    
    def _handle_missing_data(
        self,
        task_id: str,
        missing_field: str,
        sub_agent: str
    ) -> None:
        """
        Handle missing data by logging error and recording for later processing.
        
        This method is called when critical data is missing from a sub-agent output.
        It logs the error and adds it to the consolidation errors list, but allows
        processing to continue with default values.
        
        Args:
            task_id: Task identifier with missing data
            missing_field: Name of the missing field
            sub_agent: Name of the sub-agent that should have provided the data
        """
        error_msg = f"Missing {missing_field} for task {task_id} from {sub_agent}"
        logger.error(error_msg)
        
        self.consolidation_errors.append({
            'task_id': task_id,
            'missing_field': missing_field,
            'sub_agent': sub_agent,
            'error': error_msg
        })
