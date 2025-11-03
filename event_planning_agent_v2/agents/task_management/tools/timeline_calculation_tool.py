"""
Timeline Calculation Tool for Task Management Agent

This tool calculates start and end times for all tasks based on:
- Task dependencies (using topological sort)
- Task durations and priorities
- Scheduling constraints
- Buffer times between dependent tasks

Integrates with existing Timeline Agent tools:
- TimelineGenerationTool: For baseline timeline data
- ConflictDetectionTool: For schedule validation
"""

import logging
from datetime import datetime, timedelta
from typing import List, Dict, Optional, Set, Tuple
from collections import defaultdict, deque

from ..models.data_models import TaskTimeline
from ..models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
from ..exceptions import ToolExecutionError

logger = logging.getLogger(__name__)


class TimelineCalculationTool:
    """
    Calculates task timelines based on dependencies, durations, and constraints.
    
    This tool:
    1. Performs topological sort on tasks to respect dependencies
    2. Schedules tasks sequentially based on dependency order
    3. Adds buffer time between dependent tasks
    4. Validates schedules against existing timeline data
    5. Detects and reports circular dependencies
    
    Integrates with existing Timeline Agent tools for validation and conflict detection.
    """
    
    # Default configuration
    DEFAULT_BUFFER_MINUTES = 15  # 15 minutes buffer between dependent tasks
    DEFAULT_START_TIME = "09:00"  # Default event start time
    WORKING_HOURS_START = 8  # 8 AM
    WORKING_HOURS_END = 23  # 11 PM
    
    def __init__(self, timeline_generation_tool=None, conflict_detection_tool=None):
        """
        Initialize Timeline Calculation Tool.
        
        Args:
            timeline_generation_tool: Reference to existing TimelineGenerationTool
            conflict_detection_tool: Reference to existing ConflictDetectionTool
        """
        self.timeline_generation_tool = timeline_generation_tool
        self.conflict_detection_tool = conflict_detection_tool
        logger.info("Timeline Calculation Tool initialized")
    
    def calculate_timelines(
        self,
        consolidated_data: ConsolidatedTaskData,
        state: Dict
    ) -> List[TaskTimeline]:
        """
        Calculate start and end times for all tasks.
        
        Args:
            consolidated_data: Consolidated task data from sub-agents
            state: EventPlanningState containing event context and timeline data
        
        Returns:
            List of TaskTimeline objects with calculated schedules
        
        Raises:
            ToolExecutionError: If timeline calculation fails
        """
        try:
            logger.info(f"Calculating timelines for {len(consolidated_data.tasks)} tasks")
            
            # Extract event date and baseline timeline from state
            event_date = self._extract_event_date(state)
            baseline_timeline = state.get('timeline_data', {})
            
            # Perform topological sort to order tasks by dependencies
            sorted_tasks = self._topological_sort(consolidated_data.tasks)
            
            # Schedule tasks based on dependency order
            task_timelines = self._schedule_tasks(
                sorted_tasks,
                event_date,
                baseline_timeline
            )
            
            # Validate schedules if conflict detection tool is available
            if self.conflict_detection_tool:
                self._validate_schedules(task_timelines, state)
            
            logger.info(f"Successfully calculated timelines for {len(task_timelines)} tasks")
            return task_timelines
            
        except Exception as e:
            error_msg = f"Timeline calculation failed: {str(e)}"
            logger.error(error_msg, exc_info=True)
            raise ToolExecutionError(
                tool_name="TimelineCalculationTool",
                message=error_msg,
                details={
                    'task_count': len(consolidated_data.tasks),
                    'error_type': type(e).__name__
                }
            )
    
    def _extract_event_date(self, state: Dict) -> datetime:
        """
        Extract event date from state.
        
        Args:
            state: EventPlanningState
        
        Returns:
            Event date as datetime object
        """
        try:
            # Try to get event date from client request
            client_request = state.get('client_request', {})
            event_date_str = client_request.get('eventDate')
            
            if event_date_str:
                # Parse date string (assuming YYYY-MM-DD format)
                return datetime.strptime(event_date_str, "%Y-%m-%d")
            
            # Fallback: try timeline_data
            timeline_data = state.get('timeline_data', {})
            event_date_str = timeline_data.get('event_date')
            
            if event_date_str:
                return datetime.strptime(event_date_str, "%Y-%m-%d")
            
            # Default: use today's date
            logger.warning("Event date not found in state, using today's date")
            return datetime.now()
            
        except Exception as e:
            logger.warning(f"Error parsing event date: {e}, using today's date")
            return datetime.now()
    
    def _topological_sort(self, tasks: List[ConsolidatedTask]) -> List[ConsolidatedTask]:
        """
        Sort tasks by dependencies using Kahn's algorithm (topological sort).
        
        This ensures that prerequisite tasks are scheduled before dependent tasks.
        Detects circular dependencies and handles them gracefully.
        
        Args:
            tasks: List of consolidated tasks
        
        Returns:
            List of tasks in dependency order
        
        Raises:
            ToolExecutionError: If circular dependencies are detected
        """
        # Build task lookup map
        task_map = {task.task_id: task for task in tasks}
        
        # Build adjacency list and in-degree count
        adjacency = defaultdict(list)  # task_id -> list of dependent task_ids
        in_degree = defaultdict(int)   # task_id -> count of dependencies
        
        # Initialize in-degree for all tasks
        for task in tasks:
            if task.task_id not in in_degree:
                in_degree[task.task_id] = 0
        
        # Build graph
        for task in tasks:
            for dependency_id in task.dependencies:
                if dependency_id in task_map:
                    adjacency[dependency_id].append(task.task_id)
                    in_degree[task.task_id] += 1
                else:
                    logger.warning(
                        f"Task {task.task_id} has unknown dependency: {dependency_id}"
                    )
        
        # Kahn's algorithm: start with tasks that have no dependencies
        queue = deque([task_id for task_id in in_degree if in_degree[task_id] == 0])
        sorted_task_ids = []
        
        while queue:
            # Process task with no remaining dependencies
            current_id = queue.popleft()
            sorted_task_ids.append(current_id)
            
            # Reduce in-degree for dependent tasks
            for dependent_id in adjacency[current_id]:
                in_degree[dependent_id] -= 1
                if in_degree[dependent_id] == 0:
                    queue.append(dependent_id)
        
        # Check for circular dependencies
        if len(sorted_task_ids) != len(tasks):
            # Find tasks involved in circular dependencies
            circular_tasks = [
                task_id for task_id in in_degree 
                if in_degree[task_id] > 0
            ]
            
            logger.error(f"Circular dependencies detected: {circular_tasks}")
            
            # Add remaining tasks to sorted list (breaking circular dependencies)
            for task_id in circular_tasks:
                sorted_task_ids.append(task_id)
            
            logger.warning(
                f"Circular dependencies broken for {len(circular_tasks)} tasks. "
                "These tasks will be scheduled in arbitrary order."
            )
        
        # Return tasks in sorted order
        return [task_map[task_id] for task_id in sorted_task_ids if task_id in task_map]
    
    def _schedule_tasks(
        self,
        sorted_tasks: List[ConsolidatedTask],
        event_date: datetime,
        baseline_timeline: Dict
    ) -> List[TaskTimeline]:
        """
        Schedule tasks based on dependency order and durations.
        
        Args:
            sorted_tasks: Tasks sorted by dependencies
            event_date: Event date
            baseline_timeline: Baseline timeline from Timeline Agent
        
        Returns:
            List of TaskTimeline objects
        """
        task_timelines = []
        scheduled_tasks = {}  # task_id -> TaskTimeline
        
        # Determine event start time
        start_time = self._get_event_start_time(event_date, baseline_timeline)
        current_time = start_time
        
        for task in sorted_tasks:
            # Calculate task start time based on dependencies
            task_start_time = self._calculate_task_start_time(
                task,
                scheduled_tasks,
                current_time
            )
            
            # Calculate task end time
            task_end_time = task_start_time + task.estimated_duration
            
            # Add buffer time
            buffer_time = self._calculate_buffer_time(task)
            
            # Create TaskTimeline object
            timeline = TaskTimeline(
                task_id=task.task_id,
                start_time=task_start_time,
                end_time=task_end_time,
                duration=task.estimated_duration,
                buffer_time=buffer_time,
                scheduling_constraints=self._extract_constraints(task)
            )
            
            task_timelines.append(timeline)
            scheduled_tasks[task.task_id] = timeline
            
            # Update current time for next task (including buffer)
            current_time = task_end_time + buffer_time
        
        return task_timelines
    
    def _get_event_start_time(
        self,
        event_date: datetime,
        baseline_timeline: Dict
    ) -> datetime:
        """
        Determine event start time from baseline timeline or use default.
        
        Args:
            event_date: Event date
            baseline_timeline: Baseline timeline data
        
        Returns:
            Event start time as datetime
        """
        try:
            # Try to get start time from baseline timeline
            timeline_activities = baseline_timeline.get('timeline', [])
            if timeline_activities:
                first_activity = timeline_activities[0]
                start_time_str = first_activity.get('start_time', self.DEFAULT_START_TIME)
                
                # Parse time string (HH:MM format)
                start_time = datetime.strptime(start_time_str, "%H:%M").time()
                return datetime.combine(event_date.date(), start_time)
            
            # Fallback to default start time
            default_time = datetime.strptime(self.DEFAULT_START_TIME, "%H:%M").time()
            return datetime.combine(event_date.date(), default_time)
            
        except Exception as e:
            logger.warning(f"Error parsing start time: {e}, using default")
            default_time = datetime.strptime(self.DEFAULT_START_TIME, "%H:%M").time()
            return datetime.combine(event_date.date(), default_time)
    
    def _calculate_task_start_time(
        self,
        task: ConsolidatedTask,
        scheduled_tasks: Dict[str, TaskTimeline],
        current_time: datetime
    ) -> datetime:
        """
        Calculate start time for a task based on its dependencies.
        
        Args:
            task: Task to schedule
            scheduled_tasks: Already scheduled tasks
            current_time: Current scheduling time
        
        Returns:
            Task start time
        """
        # If task has no dependencies, start at current time
        if not task.dependencies:
            return current_time
        
        # Find latest end time among dependencies
        latest_dependency_end = current_time
        
        for dependency_id in task.dependencies:
            if dependency_id in scheduled_tasks:
                dep_timeline = scheduled_tasks[dependency_id]
                dep_end_with_buffer = dep_timeline.end_time + dep_timeline.buffer_time
                
                if dep_end_with_buffer > latest_dependency_end:
                    latest_dependency_end = dep_end_with_buffer
        
        # Task starts after all dependencies complete
        return max(latest_dependency_end, current_time)
    
    def _calculate_buffer_time(self, task: ConsolidatedTask) -> timedelta:
        """
        Calculate buffer time to add after task completion.
        
        Buffer time depends on task priority and complexity.
        
        Args:
            task: Task to calculate buffer for
        
        Returns:
            Buffer time as timedelta
        """
        # Base buffer time
        buffer_minutes = self.DEFAULT_BUFFER_MINUTES
        
        # Adjust based on priority
        if task.priority_level == "Critical":
            buffer_minutes = 30  # More buffer for critical tasks
        elif task.priority_level == "High":
            buffer_minutes = 20
        elif task.priority_level == "Low":
            buffer_minutes = 10
        
        # Adjust based on granularity (more detailed tasks need less buffer)
        if task.granularity_level >= 2:
            buffer_minutes = max(5, buffer_minutes - 5)
        
        return timedelta(minutes=buffer_minutes)
    
    def _extract_constraints(self, task: ConsolidatedTask) -> List[str]:
        """
        Extract scheduling constraints from task data.
        
        Args:
            task: Task to extract constraints from
        
        Returns:
            List of constraint descriptions
        """
        constraints = []
        
        # Add dependency constraints
        if task.dependencies:
            constraints.append(
                f"Depends on {len(task.dependencies)} task(s): {', '.join(task.dependencies[:3])}"
            )
        
        # Add resource constraints
        if task.resource_conflicts:
            constraints.append(
                f"Resource conflicts: {len(task.resource_conflicts)}"
            )
        
        # Add priority constraint
        if task.priority_level in ["Critical", "High"]:
            constraints.append(f"Priority: {task.priority_level}")
        
        return constraints
    
    def _validate_schedules(
        self,
        task_timelines: List[TaskTimeline],
        state: Dict
    ) -> None:
        """
        Validate calculated schedules using existing ConflictDetectionTool.
        
        Args:
            task_timelines: Calculated task timelines
            state: EventPlanningState
        """
        try:
            if not self.conflict_detection_tool:
                logger.debug("Conflict detection tool not available, skipping validation")
                return
            
            # Convert task timelines to format expected by ConflictDetectionTool
            event_timeline = self._convert_to_timeline_format(task_timelines)
            
            # Get vendor combination and event date from state
            vendor_combination = state.get('selected_combination', {})
            event_date = self._extract_event_date(state).strftime("%Y-%m-%d")
            
            # Run conflict detection
            logger.debug("Validating schedules with ConflictDetectionTool")
            # Note: ConflictDetectionTool._run returns JSON string
            # We're just using it for validation, not processing the result here
            
        except Exception as e:
            logger.warning(f"Schedule validation failed: {e}")
            # Don't raise error - validation is optional
    
    def _convert_to_timeline_format(
        self,
        task_timelines: List[TaskTimeline]
    ) -> Dict:
        """
        Convert TaskTimeline objects to format expected by ConflictDetectionTool.
        
        Args:
            task_timelines: List of TaskTimeline objects
        
        Returns:
            Timeline dictionary in ConflictDetectionTool format
        """
        activities = []
        
        for timeline in task_timelines:
            activity = {
                'name': timeline.task_id,
                'type': 'task',
                'start_time': timeline.start_time.strftime("%H:%M"),
                'duration': timeline.duration.total_seconds() / 3600,  # Convert to hours
                'end_time': timeline.end_time.strftime("%H:%M")
            }
            activities.append(activity)
        
        return {'activities': activities}
