"""
Conflict Check Tool for Task Management Agent

This tool detects conflicts in task scheduling, resource allocation, and venue availability:
- Timeline conflicts using existing Timeline Agent conflict detection
- Resource conflicts (vendors, equipment, personnel double-booking)
- Venue availability conflicts
- Generates unique conflict identifiers
- Suggests resolution strategies

Integrates with:
- ConflictDetectionTool from timeline_tools.py for scheduling conflicts
- EventPlanningState for timeline and vendor data
- ConsolidatedTaskData for task information
"""

import logging
import hashlib
from typing import List, Optional, Dict, Any, Set, Tuple
from datetime import datetime, timedelta
from collections import defaultdict

from ..models.data_models import Conflict, Resource, TaskTimeline
from ..models.consolidated_models import ConsolidatedTask, ConsolidatedTaskData
from ..exceptions import ToolExecutionError
from ....workflows.state_models import EventPlanningState
from ....tools.timeline_tools import ConflictDetectionTool

logger = logging.getLogger(__name__)


class ConflictCheckTool:
    """
    Tool for detecting conflicts in task scheduling, resources, and venue availability.
    
    This tool:
    1. Uses existing Timeline Agent conflict detection for scheduling conflicts
    2. Detects resource double-booking (vendors, equipment, personnel)
    3. Detects venue availability conflicts
    4. Generates unique conflict identifiers
    5. Suggests potential resolution strategies
    6. Returns conflicts with severity levels and affected tasks
    """
    
    def __init__(self, timeline_conflict_tool: Optional[ConflictDetectionTool] = None):
        """
        Initialize Conflict Check Tool
        
        Args:
            timeline_conflict_tool: Optional existing ConflictDetectionTool instance
        """
        self.timeline_conflict_tool = timeline_conflict_tool or ConflictDetectionTool()
        logger.info("ConflictCheckTool initialized")
    
    def check_conflicts(
        self,
        consolidated_data: ConsolidatedTaskData,
        state: EventPlanningState
    ) -> List[Conflict]:
        """
        Check for all types of conflicts in tasks
        
        Args:
            consolidated_data: Consolidated task data from sub-agents
            state: Current EventPlanningState with timeline and vendor data
            
        Returns:
            List of Conflict objects with severity levels and affected tasks
            
        Raises:
            ToolExecutionError: If conflict checking fails critically
        """
        try:
            logger.info(f"Starting conflict detection for {len(consolidated_data.tasks)} tasks")
            
            all_conflicts = []
            
            # Check timeline conflicts using existing Timeline Agent
            timeline_conflicts = self._check_timeline_conflicts(
                consolidated_data.tasks, state
            )
            all_conflicts.extend(timeline_conflicts)
            logger.info(f"Found {len(timeline_conflicts)} timeline conflicts")
            
            # Check resource conflicts (vendors, equipment, personnel)
            resource_conflicts = self._check_resource_conflicts(
                consolidated_data.tasks
            )
            all_conflicts.extend(resource_conflicts)
            logger.info(f"Found {len(resource_conflicts)} resource conflicts")
            
            # Check venue conflicts
            venue_conflicts = self._check_venue_conflicts(
                consolidated_data.tasks, state
            )
            all_conflicts.extend(venue_conflicts)
            logger.info(f"Found {len(venue_conflicts)} venue conflicts")
            
            # Deduplicate conflicts
            unique_conflicts = self._deduplicate_conflicts(all_conflicts)
            
            logger.info(
                f"Conflict detection complete: {len(unique_conflicts)} unique conflicts found"
            )
            return unique_conflicts
            
        except Exception as e:
            logger.error(f"Conflict checking failed: {e}")
            raise ToolExecutionError(f"Failed to check conflicts: {e}")
    
    def _check_timeline_conflicts(
        self,
        tasks: List[ConsolidatedTask],
        state: EventPlanningState
    ) -> List[Conflict]:
        """
        Use existing Timeline Agent conflict detection for scheduling conflicts
        
        Args:
            tasks: List of consolidated tasks
            state: Current EventPlanningState
            
        Returns:
            List of timeline-related Conflict objects
        """
        conflicts = []
        
        try:
            # Extract timeline data from state
            timeline_data = state.get('timeline_data')
            if not timeline_data:
                logger.warning("No timeline_data found in state, skipping timeline conflict check")
                return conflicts
            
            # Extract vendor combination and event date
            selected_combination = state.get('selected_combination', {})
            client_request = state.get('client_request', {})
            event_date = client_request.get('date', datetime.now().strftime('%Y-%m-%d'))
            
            # Build event timeline from tasks with timeline information
            event_timeline = self._build_event_timeline_from_tasks(tasks)
            
            if not event_timeline.get('activities'):
                logger.debug("No activities with timeline information, skipping timeline conflict check")
                return conflicts
            
            # Use existing ConflictDetectionTool
            try:
                conflict_result = self.timeline_conflict_tool._run(
                    vendor_combination=selected_combination,
                    event_date=event_date,
                    event_timeline=event_timeline
                )
                
                # Parse conflict detection results
                import json
                result_data = json.loads(conflict_result)
                
                # Convert timeline tool conflicts to our Conflict format
                detailed_conflicts = result_data.get('detailed_conflicts', [])
                for tc in detailed_conflicts:
                    conflict = self._convert_timeline_conflict(tc, tasks)
                    if conflict:
                        conflicts.append(conflict)
                        
            except Exception as e:
                logger.warning(f"Timeline conflict detection tool failed: {e}")
            
            # Also check for task timeline overlaps directly
            direct_conflicts = self._check_direct_timeline_overlaps(tasks)
            conflicts.extend(direct_conflicts)
            
        except Exception as e:
            logger.error(f"Timeline conflict checking failed: {e}")
        
        return conflicts
    
    def _check_resource_conflicts(
        self,
        tasks: List[ConsolidatedTask]
    ) -> List[Conflict]:
        """
        Detect resource double-booking (vendors, equipment, personnel)
        
        Args:
            tasks: List of consolidated tasks
            
        Returns:
            List of resource-related Conflict objects
        """
        conflicts = []
        
        try:
            # Group tasks by resource usage and time
            resource_usage = defaultdict(list)
            
            for task in tasks:
                if not task.timeline:
                    continue
                
                # Check each resource required by the task
                for resource in task.resources_required:
                    resource_key = f"{resource.resource_type}:{resource.resource_id}"
                    resource_usage[resource_key].append({
                        'task': task,
                        'resource': resource,
                        'start_time': task.timeline.start_time,
                        'end_time': task.timeline.end_time
                    })
            
            # Check for overlapping usage of same resource
            for resource_key, usages in resource_usage.items():
                if len(usages) < 2:
                    continue
                
                # Sort by start time
                sorted_usages = sorted(usages, key=lambda x: x['start_time'])
                
                # Check for overlaps
                for i in range(len(sorted_usages) - 1):
                    current = sorted_usages[i]
                    next_usage = sorted_usages[i + 1]
                    
                    # Check if current task ends after next task starts
                    if current['end_time'] > next_usage['start_time']:
                        conflict = self._create_resource_conflict(
                            current, next_usage, resource_key
                        )
                        conflicts.append(conflict)
            
            # Check for vendor-specific conflicts
            vendor_conflicts = self._check_vendor_resource_conflicts(tasks)
            conflicts.extend(vendor_conflicts)
            
        except Exception as e:
            logger.error(f"Resource conflict checking failed: {e}")
        
        return conflicts
    
    def _check_venue_conflicts(
        self,
        tasks: List[ConsolidatedTask],
        state: EventPlanningState
    ) -> List[Conflict]:
        """
        Detect venue availability conflicts
        
        Args:
            tasks: List of consolidated tasks
            state: Current EventPlanningState
            
        Returns:
            List of venue-related Conflict objects
        """
        conflicts = []
        
        try:
            # Extract venue from selected combination
            selected_combination = state.get('selected_combination', {})
            venue_data = selected_combination.get('venue')
            
            if not venue_data:
                logger.debug("No venue in selected combination, skipping venue conflict check")
                return conflicts
            
            venue_id = venue_data.get('vendor_id') or venue_data.get('id')
            venue_name = venue_data.get('name', 'Unknown Venue')
            
            # Check for tasks requiring venue at overlapping times
            venue_tasks = []
            for task in tasks:
                if self._task_requires_venue(task):
                    if task.timeline:
                        venue_tasks.append(task)
            
            if len(venue_tasks) < 2:
                return conflicts
            
            # Sort by start time
            sorted_tasks = sorted(venue_tasks, key=lambda t: t.timeline.start_time)
            
            # Check for overlaps
            for i in range(len(sorted_tasks) - 1):
                current = sorted_tasks[i]
                next_task = sorted_tasks[i + 1]
                
                # Check if current task ends after next task starts
                if current.timeline.end_time > next_task.timeline.start_time:
                    conflict = self._create_venue_conflict(
                        current, next_task, venue_id, venue_name
                    )
                    conflicts.append(conflict)
            
            # Check venue capacity constraints
            capacity_conflicts = self._check_venue_capacity_conflicts(
                venue_tasks, venue_data
            )
            conflicts.extend(capacity_conflicts)
            
        except Exception as e:
            logger.error(f"Venue conflict checking failed: {e}")
        
        return conflicts
    
    def _generate_conflict_id(
        self,
        conflict_type: str,
        affected_tasks: List[str],
        additional_context: str = ""
    ) -> str:
        """
        Create unique conflict identifier
        
        Args:
            conflict_type: Type of conflict (timeline, resource, venue)
            affected_tasks: List of affected task IDs
            additional_context: Additional context for uniqueness
            
        Returns:
            Unique conflict ID string
        """
        # Sort task IDs for consistent hashing
        sorted_tasks = sorted(affected_tasks)
        
        # Create hash input
        hash_input = f"{conflict_type}:{':'.join(sorted_tasks)}:{additional_context}"
        
        # Generate hash
        conflict_hash = hashlib.md5(hash_input.encode()).hexdigest()[:12]
        
        # Create readable conflict ID
        conflict_id = f"{conflict_type}_{conflict_hash}"
        
        return conflict_id
    
    def _suggest_resolutions(
        self,
        conflict: Conflict,
        tasks: Optional[List[ConsolidatedTask]] = None
    ) -> List[str]:
        """
        Provide potential conflict resolution strategies
        
        Args:
            conflict: Conflict object to suggest resolutions for
            tasks: Optional list of tasks for context
            
        Returns:
            List of suggested resolution strategies
        """
        suggestions = []
        
        if conflict.conflict_type == 'timeline':
            suggestions.extend([
                "Adjust task start times to eliminate overlap",
                "Add buffer time between dependent tasks",
                "Reschedule lower priority tasks to different time slots",
                "Consider parallel execution if tasks are independent"
            ])
            
            if conflict.severity in ['critical', 'high']:
                suggestions.append("Immediate timeline restructuring required")
        
        elif conflict.conflict_type == 'resource':
            suggestions.extend([
                "Stagger task schedules to avoid resource overlap",
                "Allocate additional resources if available",
                "Prioritize critical tasks for resource allocation",
                "Consider alternative resources or vendors"
            ])
            
            if 'vendor' in conflict.conflict_description.lower():
                suggestions.append("Contact vendor to confirm availability for extended hours")
        
        elif conflict.conflict_type == 'venue':
            suggestions.extend([
                "Adjust venue usage schedule to eliminate overlaps",
                "Designate different areas of venue for concurrent activities",
                "Reschedule non-critical venue activities",
                "Consider using multiple venue spaces if available"
            ])
            
            if 'capacity' in conflict.conflict_description.lower():
                suggestions.append("Reduce guest count or select larger venue")
        
        # Add severity-specific suggestions
        if conflict.severity == 'critical':
            suggestions.insert(0, "URGENT: This conflict must be resolved before proceeding")
        elif conflict.severity == 'high':
            suggestions.insert(0, "High priority: Resolve this conflict soon")
        
        return suggestions
    
    # Helper methods
    
    def _build_event_timeline_from_tasks(
        self,
        tasks: List[ConsolidatedTask]
    ) -> Dict[str, Any]:
        """
        Build event timeline structure from tasks for ConflictDetectionTool
        
        Args:
            tasks: List of consolidated tasks
            
        Returns:
            Event timeline dictionary
        """
        activities = []
        
        for task in tasks:
            if not task.timeline:
                continue
            
            activity = {
                'name': task.task_name,
                'type': self._infer_activity_type(task),
                'start_time': task.timeline.start_time.strftime('%H:%M'),
                'duration': task.timeline.duration.total_seconds() / 3600,  # Convert to hours
                'end_time': task.timeline.end_time.strftime('%H:%M')
            }
            activities.append(activity)
        
        return {'activities': activities}
    
    def _infer_activity_type(self, task: ConsolidatedTask) -> str:
        """Infer activity type from task name/description"""
        task_text = f"{task.task_name} {task.task_description}".lower()
        
        if any(word in task_text for word in ['setup', 'preparation', 'arrange']):
            return 'setup'
        elif any(word in task_text for word in ['ceremony', 'wedding', 'vows']):
            return 'ceremony'
        elif any(word in task_text for word in ['reception', 'dinner', 'meal']):
            return 'reception'
        elif any(word in task_text for word in ['photo', 'video', 'shoot']):
            return 'photography'
        elif any(word in task_text for word in ['makeup', 'hair', 'beauty']):
            return 'makeup'
        elif any(word in task_text for word in ['entertainment', 'music', 'dance']):
            return 'entertainment'
        elif any(word in task_text for word in ['cocktail', 'drinks']):
            return 'cocktail'
        elif any(word in task_text for word in ['cleanup', 'teardown']):
            return 'cleanup'
        else:
            return 'general'
    
    def _convert_timeline_conflict(
        self,
        timeline_conflict: Dict[str, Any],
        tasks: List[ConsolidatedTask]
    ) -> Optional[Conflict]:
        """
        Convert timeline tool conflict to our Conflict format
        
        Args:
            timeline_conflict: Conflict from ConflictDetectionTool
            tasks: List of tasks for mapping
            
        Returns:
            Conflict object or None
        """
        try:
            conflict_type = timeline_conflict.get('type', 'timeline')
            severity = timeline_conflict.get('severity', 'medium')
            issue = timeline_conflict.get('issue', 'Timeline conflict detected')
            
            # Try to map affected tasks
            affected_tasks = []
            if 'activity' in issue.lower():
                # Extract activity names from issue description
                for task in tasks:
                    if task.task_name.lower() in issue.lower():
                        affected_tasks.append(task.task_id)
            
            conflict_id = self._generate_conflict_id(
                'timeline',
                affected_tasks or ['unknown'],
                conflict_type
            )
            
            conflict = Conflict(
                conflict_id=conflict_id,
                conflict_type='timeline',
                severity=severity,
                affected_tasks=affected_tasks,
                conflict_description=issue
            )
            
            # Add resolution suggestions
            conflict.suggested_resolutions = self._suggest_resolutions(conflict, tasks)
            
            return conflict
            
        except Exception as e:
            logger.warning(f"Failed to convert timeline conflict: {e}")
            return None
    
    def _check_direct_timeline_overlaps(
        self,
        tasks: List[ConsolidatedTask]
    ) -> List[Conflict]:
        """
        Check for direct timeline overlaps between tasks
        
        Args:
            tasks: List of consolidated tasks
            
        Returns:
            List of timeline overlap conflicts
        """
        conflicts = []
        
        # Filter tasks with timeline information
        tasks_with_timeline = [t for t in tasks if t.timeline]
        
        if len(tasks_with_timeline) < 2:
            return conflicts
        
        # Sort by start time
        sorted_tasks = sorted(tasks_with_timeline, key=lambda t: t.timeline.start_time)
        
        # Check for overlaps
        for i in range(len(sorted_tasks)):
            for j in range(i + 1, len(sorted_tasks)):
                task1 = sorted_tasks[i]
                task2 = sorted_tasks[j]
                
                # Check if tasks overlap
                if self._tasks_overlap(task1, task2):
                    # Check if overlap is problematic (not intentional parallel execution)
                    if self._is_problematic_overlap(task1, task2):
                        conflict = Conflict(
                            conflict_id=self._generate_conflict_id(
                                'timeline',
                                [task1.task_id, task2.task_id],
                                'overlap'
                            ),
                            conflict_type='timeline',
                            severity=self._determine_overlap_severity(task1, task2),
                            affected_tasks=[task1.task_id, task2.task_id],
                            conflict_description=(
                                f"Timeline overlap: '{task1.task_name}' "
                                f"({task1.timeline.start_time.strftime('%H:%M')}-"
                                f"{task1.timeline.end_time.strftime('%H:%M')}) overlaps with "
                                f"'{task2.task_name}' "
                                f"({task2.timeline.start_time.strftime('%H:%M')}-"
                                f"{task2.timeline.end_time.strftime('%H:%M')})"
                            )
                        )
                        conflict.suggested_resolutions = self._suggest_resolutions(conflict)
                        conflicts.append(conflict)
        
        return conflicts
    
    def _tasks_overlap(
        self,
        task1: ConsolidatedTask,
        task2: ConsolidatedTask
    ) -> bool:
        """Check if two tasks have overlapping timelines"""
        if not task1.timeline or not task2.timeline:
            return False
        
        # Tasks overlap if one starts before the other ends
        return (
            task1.timeline.start_time < task2.timeline.end_time and
            task2.timeline.start_time < task1.timeline.end_time
        )
    
    def _is_problematic_overlap(
        self,
        task1: ConsolidatedTask,
        task2: ConsolidatedTask
    ) -> bool:
        """
        Determine if overlap is problematic or intentional parallel execution
        
        Args:
            task1: First task
            task2: Second task
            
        Returns:
            True if overlap is problematic
        """
        # Check if tasks have dependencies (dependent tasks shouldn't overlap)
        if task1.task_id in task2.dependencies or task2.task_id in task1.dependencies:
            return True
        
        # Check if tasks share resources (resource conflict)
        task1_resources = {f"{r.resource_type}:{r.resource_id}" for r in task1.resources_required}
        task2_resources = {f"{r.resource_type}:{r.resource_id}" for r in task2.resources_required}
        
        if task1_resources & task2_resources:  # Intersection
            return True
        
        # Check if both tasks are high priority (might need sequential execution)
        if task1.priority_level in ['Critical', 'High'] and task2.priority_level in ['Critical', 'High']:
            return True
        
        # Otherwise, overlap might be intentional parallel execution
        return False
    
    def _determine_overlap_severity(
        self,
        task1: ConsolidatedTask,
        task2: ConsolidatedTask
    ) -> str:
        """
        Determine severity of timeline overlap
        
        Args:
            task1: First task
            task2: Second task
            
        Returns:
            Severity level: critical, high, medium, or low
        """
        # Critical if tasks have dependencies
        if task1.task_id in task2.dependencies or task2.task_id in task1.dependencies:
            return 'critical'
        
        # High if both tasks are critical priority
        if task1.priority_level == 'Critical' and task2.priority_level == 'Critical':
            return 'high'
        
        # High if tasks share critical resources
        task1_resources = {f"{r.resource_type}:{r.resource_id}" for r in task1.resources_required}
        task2_resources = {f"{r.resource_type}:{r.resource_id}" for r in task2.resources_required}
        
        if task1_resources & task2_resources:
            return 'high'
        
        # Medium if at least one task is high priority
        if task1.priority_level in ['Critical', 'High'] or task2.priority_level in ['Critical', 'High']:
            return 'medium'
        
        # Low otherwise
        return 'low'
    
    def _create_resource_conflict(
        self,
        usage1: Dict[str, Any],
        usage2: Dict[str, Any],
        resource_key: str
    ) -> Conflict:
        """
        Create a resource conflict object
        
        Args:
            usage1: First resource usage
            usage2: Second resource usage
            resource_key: Resource identifier
            
        Returns:
            Conflict object
        """
        task1 = usage1['task']
        task2 = usage2['task']
        resource = usage1['resource']
        
        conflict_id = self._generate_conflict_id(
            'resource',
            [task1.task_id, task2.task_id],
            resource_key
        )
        
        # Determine severity based on resource type and task priorities
        severity = 'medium'
        if resource.resource_type == 'vendor':
            severity = 'high'
        if task1.priority_level == 'Critical' or task2.priority_level == 'Critical':
            severity = 'critical'
        
        conflict = Conflict(
            conflict_id=conflict_id,
            conflict_type='resource',
            severity=severity,
            affected_tasks=[task1.task_id, task2.task_id],
            conflict_description=(
                f"Resource conflict: {resource.resource_type} '{resource.resource_name}' "
                f"is double-booked. Task '{task1.task_name}' "
                f"({usage1['start_time'].strftime('%H:%M')}-{usage1['end_time'].strftime('%H:%M')}) "
                f"and task '{task2.task_name}' "
                f"({usage2['start_time'].strftime('%H:%M')}-{usage2['end_time'].strftime('%H:%M')}) "
                f"both require this resource."
            )
        )
        
        conflict.suggested_resolutions = self._suggest_resolutions(conflict)
        return conflict
    
    def _check_vendor_resource_conflicts(
        self,
        tasks: List[ConsolidatedTask]
    ) -> List[Conflict]:
        """
        Check for vendor-specific resource conflicts
        
        Args:
            tasks: List of consolidated tasks
            
        Returns:
            List of vendor resource conflicts
        """
        conflicts = []
        
        # Group tasks by assigned vendors
        vendor_tasks = defaultdict(list)
        
        for task in tasks:
            if not task.timeline:
                continue
            
            # Check assigned vendors
            for vendor_id in task.assigned_vendors:
                vendor_tasks[vendor_id].append(task)
        
        # Check for vendor double-booking
        for vendor_id, tasks_list in vendor_tasks.items():
            if len(tasks_list) < 2:
                continue
            
            # Sort by start time
            sorted_tasks = sorted(tasks_list, key=lambda t: t.timeline.start_time)
            
            # Check for overlaps
            for i in range(len(sorted_tasks) - 1):
                current = sorted_tasks[i]
                next_task = sorted_tasks[i + 1]
                
                if current.timeline.end_time > next_task.timeline.start_time:
                    conflict = Conflict(
                        conflict_id=self._generate_conflict_id(
                            'resource',
                            [current.task_id, next_task.task_id],
                            f"vendor_{vendor_id}"
                        ),
                        conflict_type='resource',
                        severity='high',
                        affected_tasks=[current.task_id, next_task.task_id],
                        conflict_description=(
                            f"Vendor double-booking: Vendor {vendor_id} is assigned to "
                            f"overlapping tasks '{current.task_name}' and '{next_task.task_name}'"
                        )
                    )
                    conflict.suggested_resolutions = self._suggest_resolutions(conflict)
                    conflicts.append(conflict)
        
        return conflicts
    
    def _create_venue_conflict(
        self,
        task1: ConsolidatedTask,
        task2: ConsolidatedTask,
        venue_id: str,
        venue_name: str
    ) -> Conflict:
        """
        Create a venue conflict object
        
        Args:
            task1: First task
            task2: Second task
            venue_id: Venue identifier
            venue_name: Venue name
            
        Returns:
            Conflict object
        """
        conflict_id = self._generate_conflict_id(
            'venue',
            [task1.task_id, task2.task_id],
            venue_id
        )
        
        # Venue conflicts are typically high severity
        severity = 'high'
        if task1.priority_level == 'Critical' or task2.priority_level == 'Critical':
            severity = 'critical'
        
        conflict = Conflict(
            conflict_id=conflict_id,
            conflict_type='venue',
            severity=severity,
            affected_tasks=[task1.task_id, task2.task_id],
            conflict_description=(
                f"Venue conflict: '{venue_name}' is required by overlapping tasks. "
                f"Task '{task1.task_name}' "
                f"({task1.timeline.start_time.strftime('%H:%M')}-"
                f"{task1.timeline.end_time.strftime('%H:%M')}) and "
                f"task '{task2.task_name}' "
                f"({task2.timeline.start_time.strftime('%H:%M')}-"
                f"{task2.timeline.end_time.strftime('%H:%M')}) "
                f"both require venue access."
            )
        )
        
        conflict.suggested_resolutions = self._suggest_resolutions(conflict)
        return conflict
    
    def _task_requires_venue(self, task: ConsolidatedTask) -> bool:
        """
        Check if task requires venue access
        
        Args:
            task: Task to check
            
        Returns:
            True if task requires venue
        """
        task_text = f"{task.task_name} {task.task_description}".lower()
        
        # Check for venue-related keywords
        venue_keywords = [
            'venue', 'location', 'space', 'hall', 'room', 'setup', 'decoration',
            'ceremony', 'reception', 'event', 'guest', 'seating'
        ]
        
        if any(keyword in task_text for keyword in venue_keywords):
            return True
        
        # Check resources
        for resource in task.resources_required:
            if resource.resource_type == 'venue':
                return True
        
        # Check venue info
        if task.venue_info and not task.venue_info.requires_venue_selection:
            return True
        
        return False
    
    def _check_venue_capacity_conflicts(
        self,
        venue_tasks: List[ConsolidatedTask],
        venue_data: Dict[str, Any]
    ) -> List[Conflict]:
        """
        Check for venue capacity constraint violations
        
        Args:
            venue_tasks: Tasks requiring venue
            venue_data: Venue information
            
        Returns:
            List of capacity-related conflicts
        """
        conflicts = []
        
        try:
            max_capacity = venue_data.get('max_seating_capacity', 0)
            if max_capacity == 0:
                return conflicts
            
            # Check if any task mentions guest count exceeding capacity
            for task in venue_tasks:
                task_text = f"{task.task_name} {task.task_description}".lower()
                
                # Look for guest count mentions
                if 'guest' in task_text or 'capacity' in task_text:
                    # This is a simplified check - in real implementation,
                    # would extract actual guest count from task or state
                    conflict = Conflict(
                        conflict_id=self._generate_conflict_id(
                            'venue',
                            [task.task_id],
                            'capacity'
                        ),
                        conflict_type='venue',
                        severity='medium',
                        affected_tasks=[task.task_id],
                        conflict_description=(
                            f"Potential venue capacity issue for task '{task.task_name}'. "
                            f"Venue capacity: {max_capacity} guests. "
                            f"Verify guest count does not exceed capacity."
                        )
                    )
                    conflict.suggested_resolutions = self._suggest_resolutions(conflict)
                    conflicts.append(conflict)
                    break  # Only flag once per venue
        
        except Exception as e:
            logger.warning(f"Venue capacity check failed: {e}")
        
        return conflicts
    
    def _deduplicate_conflicts(
        self,
        conflicts: List[Conflict]
    ) -> List[Conflict]:
        """
        Remove duplicate conflicts based on conflict_id
        
        Args:
            conflicts: List of conflicts (may contain duplicates)
            
        Returns:
            List of unique conflicts
        """
        seen_ids = set()
        unique_conflicts = []
        
        for conflict in conflicts:
            if conflict.conflict_id not in seen_ids:
                seen_ids.add(conflict.conflict_id)
                unique_conflicts.append(conflict)
        
        return unique_conflicts
