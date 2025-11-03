"""
Granularity Agent Core for Task Management Agent

Breaks down high-level tasks into detailed, actionable sub-tasks based on:
- Task complexity and scope
- Priority level from Prioritization Agent
- Event context and requirements
- Vendor-specific requirements

Uses Ollama LLM (gemma:2b or tinyllama) for intelligent task decomposition.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import timedelta
import re

from ..models.task_models import PrioritizedTask, GranularTask
from ..exceptions import SubAgentDataError
from ....workflows.state_models import EventPlanningState
from ....llm.optimized_manager import get_llm_manager
from ....config.settings import get_settings

logger = logging.getLogger(__name__)


class GranularityAgentCore:
    """
    Core agent for task decomposition and granularity analysis.
    
    Breaks down high-level tasks into detailed, actionable sub-tasks with
    appropriate granularity levels (0=top-level, 1=sub-task, 2=detailed sub-task).
    Estimates duration for each task based on complexity and event context.
    """
    
    # Granularity level constants
    LEVEL_TOP = 0  # Top-level task
    LEVEL_SUB = 1  # Sub-task
    LEVEL_DETAILED = 2  # Detailed sub-task
    
    # Default durations by vendor type (in hours)
    DEFAULT_DURATIONS = {
        'venue': 4.0,
        'caterer': 6.0,
        'photographer': 8.0,
        'makeup_artist': 3.0,
        'default': 2.0
    }
    
    def __init__(self, llm_model: Optional[str] = None):
        """
        Initialize Granularity Agent with Ollama LLM.
        
        Args:
            llm_model: Optional LLM model name (gemma:2b or tinyllama).
                      Defaults to gemma:2b from settings.
        """
        self.settings = get_settings()
        self.llm_model = llm_model or self.settings.llm.gemma_model
        self.llm_manager = None
        
        logger.info(f"Initialized GranularityAgentCore with model: {self.llm_model}")
    
    async def _ensure_llm_manager(self):
        """Ensure LLM manager is initialized"""
        if self.llm_manager is None:
            self.llm_manager = await get_llm_manager()
    
    async def decompose_tasks(
        self,
        tasks: List[PrioritizedTask],
        state: EventPlanningState
    ) -> List[GranularTask]:
        """
        Break down prioritized tasks into granular sub-tasks.
        
        Args:
            tasks: List of prioritized tasks from Prioritization Agent
            state: Current event planning workflow state
            
        Returns:
            List of GranularTask objects with parent-child relationships
            
        Raises:
            SubAgentDataError: If required task data is missing or invalid
        """
        logger.info(f"Starting task decomposition for {len(tasks)} tasks...")
        
        try:
            # Ensure LLM manager is ready
            await self._ensure_llm_manager()
            
            if not tasks:
                logger.warning("No tasks provided for decomposition")
                return []
            
            # Extract event context
            event_context = self._extract_event_context(state)
            
            # Decompose each task
            granular_tasks = []
            for task in tasks:
                try:
                    decomposed = await self._decompose_single_task(task, event_context, state)
                    granular_tasks.extend(decomposed)
                except Exception as e:
                    logger.error(f"Error decomposing task {task.task_id}: {e}")
                    # Create a default granular task to continue processing
                    default_task = self._create_default_granular_task(task, str(e))
                    granular_tasks.append(default_task)
            
            logger.info(f"Successfully decomposed into {len(granular_tasks)} granular tasks")
            return granular_tasks
            
        except Exception as e:
            error_msg = f"Failed to decompose tasks: {str(e)}"
            logger.error(error_msg)
            raise SubAgentDataError(
                sub_agent_name="GranularityAgent",
                message=error_msg,
                details={"error": str(e)}
            )
    
    def _extract_event_context(self, state: EventPlanningState) -> Dict[str, Any]:
        """
        Extract relevant event context for task decomposition.
        
        Args:
            state: Event planning state
            
        Returns:
            Dictionary with event context information
        """
        client_request = state.get('client_request', {})
        
        context = {
            'event_type': client_request.get('event_type', 'unknown'),
            'guest_count': client_request.get('guest_count', 0),
            'budget': client_request.get('budget', 0),
            'location': client_request.get('location', 'unknown'),
            'preferences': client_request.get('preferences', {}),
            'requirements': client_request.get('requirements', {}),
            'selected_combination': state.get('selected_combination', {})
        }
        
        return context
    
    async def _decompose_single_task(
        self,
        task: PrioritizedTask,
        event_context: Dict[str, Any],
        state: EventPlanningState
    ) -> List[GranularTask]:
        """
        Decompose a single prioritized task into granular sub-tasks.
        
        Args:
            task: Prioritized task to decompose
            event_context: Event context information
            state: Event planning state
            
        Returns:
            List of GranularTask objects (parent + children)
        """
        # Determine appropriate granularity level
        granularity_level = self._determine_granularity_level(task)
        
        # If task doesn't need decomposition, return as-is
        if granularity_level == 0:
            duration = self._estimate_duration(task, event_context, self.LEVEL_TOP)
            return [GranularTask(
                task_id=task.task_id,
                parent_task_id=None,
                task_name=task.task_name,
                task_description=f"Priority: {task.priority_level}. {task.priority_rationale}",
                granularity_level=self.LEVEL_TOP,
                estimated_duration=duration,
                sub_tasks=[]
            )]
        
        # Generate decomposition using LLM
        prompt = self._create_decomposition_prompt(task, event_context, granularity_level)
        
        try:
            llm_response = await self.llm_manager.generate_response(
                prompt=prompt,
                model=self.llm_model,
                temperature=0.4,  # Moderate temperature for creative but consistent decomposition
                max_tokens=500
            )
            
            # Parse LLM response to extract sub-tasks
            sub_tasks_data = self._parse_decomposition_response(llm_response, task)
            
        except Exception as e:
            logger.warning(f"LLM decomposition failed for task {task.task_id}: {e}")
            # Fallback to rule-based decomposition
            sub_tasks_data = self._fallback_decomposition(task, event_context)
        
        # Create GranularTask objects
        granular_tasks = []
        
        # Create parent task
        parent_duration = timedelta(hours=0)
        sub_task_ids = []
        
        for i, sub_task_info in enumerate(sub_tasks_data):
            sub_task_id = f"{task.task_id}_sub_{i+1}"
            sub_task_ids.append(sub_task_id)
            
            # Estimate duration for sub-task
            duration = self._estimate_duration_from_description(
                sub_task_info['name'],
                sub_task_info.get('description', ''),
                event_context
            )
            parent_duration += duration
            
            granular_task = GranularTask(
                task_id=sub_task_id,
                parent_task_id=task.task_id,
                task_name=sub_task_info['name'],
                task_description=sub_task_info.get('description', ''),
                granularity_level=self.LEVEL_SUB,
                estimated_duration=duration,
                sub_tasks=[]
            )
            granular_tasks.append(granular_task)
        
        # Create parent task with references to sub-tasks
        parent_task = GranularTask(
            task_id=task.task_id,
            parent_task_id=None,
            task_name=task.task_name,
            task_description=f"Priority: {task.priority_level}. {task.priority_rationale}",
            granularity_level=self.LEVEL_TOP,
            estimated_duration=parent_duration,
            sub_tasks=sub_task_ids
        )
        
        # Return parent first, then children
        return [parent_task] + granular_tasks
    
    def _determine_granularity_level(self, task: PrioritizedTask) -> int:
        """
        Determine appropriate level of task breakdown.
        
        Decision factors:
        - Priority level: Higher priority tasks get more detailed breakdown
        - Task complexity: Complex tasks need more granularity
        - Task name: Some tasks are already granular
        
        Args:
            task: Prioritized task
            
        Returns:
            Granularity level (0=no breakdown, 1=sub-tasks, 2=detailed)
        """
        # High priority tasks should be broken down for better tracking
        if task.priority_level in ["Critical", "High"]:
            return 1  # Break into sub-tasks
        
        # Check if task name suggests it's already granular
        task_name_lower = task.task_name.lower()
        granular_keywords = ['setup', 'coordinate', 'confirm', 'finalize', 'review']
        
        if any(keyword in task_name_lower for keyword in granular_keywords):
            return 0  # Already granular enough
        
        # Medium priority tasks get moderate breakdown
        if task.priority_level == "Medium":
            return 1  # Break into sub-tasks
        
        # Low priority tasks can remain high-level
        return 0
    
    def _create_decomposition_prompt(
        self,
        task: PrioritizedTask,
        event_context: Dict[str, Any],
        granularity_level: int
    ) -> str:
        """
        Generate LLM prompt for task decomposition.
        
        Args:
            task: Task to decompose
            event_context: Event context
            granularity_level: Target granularity level
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert event planning assistant. Break down this task into actionable sub-tasks.

Event Context:
- Event Type: {event_context.get('event_type')}
- Guest Count: {event_context.get('guest_count')}
- Budget: ${event_context.get('budget', 0):,.2f}

Task to Decompose:
- Task Name: {task.task_name}
- Priority: {task.priority_level}
- Rationale: {task.priority_rationale}

Break this task into 3-5 specific, actionable sub-tasks. Each sub-task should:
- Be concrete and measurable
- Have a clear deliverable
- Be completable independently
- Take between 30 minutes to 4 hours

Respond in this exact format:
Sub-task 1: [Name]
Description: [Brief description]

Sub-task 2: [Name]
Description: [Brief description]

Sub-task 3: [Name]
Description: [Brief description]

(Continue for 3-5 sub-tasks)"""
        
        return prompt
    
    def _parse_decomposition_response(
        self,
        llm_response: str,
        task: PrioritizedTask
    ) -> List[Dict[str, str]]:
        """
        Parse LLM response to extract sub-tasks.
        
        Args:
            llm_response: Raw LLM response
            task: Original task being decomposed
            
        Returns:
            List of dictionaries with 'name' and 'description' keys
        """
        sub_tasks = []
        
        try:
            # Split response into lines
            lines = llm_response.strip().split('\n')
            
            current_sub_task = None
            
            for line in lines:
                line = line.strip()
                
                # Match "Sub-task N:" pattern
                if re.match(r'^Sub-task \d+:', line, re.IGNORECASE):
                    # Save previous sub-task if exists
                    if current_sub_task and current_sub_task.get('name'):
                        sub_tasks.append(current_sub_task)
                    
                    # Start new sub-task
                    name = re.sub(r'^Sub-task \d+:\s*', '', line, flags=re.IGNORECASE)
                    current_sub_task = {'name': name, 'description': ''}
                
                # Match "Description:" pattern
                elif line.startswith('Description:') and current_sub_task:
                    description = line.replace('Description:', '').strip()
                    current_sub_task['description'] = description
            
            # Add last sub-task
            if current_sub_task and current_sub_task.get('name'):
                sub_tasks.append(current_sub_task)
            
            # Validate we got at least some sub-tasks
            if not sub_tasks:
                logger.warning(f"No sub-tasks parsed from LLM response for task {task.task_id}")
                return self._fallback_decomposition(task, {})
            
            return sub_tasks
            
        except Exception as e:
            logger.error(f"Failed to parse decomposition response: {e}")
            return self._fallback_decomposition(task, {})
    
    def _fallback_decomposition(
        self,
        task: PrioritizedTask,
        event_context: Dict[str, Any]
    ) -> List[Dict[str, str]]:
        """
        Provide rule-based fallback decomposition when LLM fails.
        
        Args:
            task: Task to decompose
            event_context: Event context
            
        Returns:
            List of sub-task dictionaries
        """
        task_name_lower = task.task_name.lower()
        
        # Venue-related tasks
        if 'venue' in task_name_lower:
            return [
                {'name': 'Confirm venue booking and contract', 'description': 'Finalize venue contract and payment'},
                {'name': 'Coordinate venue setup requirements', 'description': 'Discuss layout, equipment, and timing'},
                {'name': 'Schedule venue walkthrough', 'description': 'Visit venue to confirm arrangements'},
                {'name': 'Confirm venue access times', 'description': 'Verify setup and teardown windows'}
            ]
        
        # Catering-related tasks
        elif 'cater' in task_name_lower:
            return [
                {'name': 'Finalize menu selection', 'description': 'Confirm dishes and dietary accommodations'},
                {'name': 'Confirm guest count and timing', 'description': 'Provide final headcount and service schedule'},
                {'name': 'Coordinate delivery and setup', 'description': 'Arrange catering arrival and setup time'},
                {'name': 'Review service requirements', 'description': 'Confirm staffing and equipment needs'}
            ]
        
        # Photography-related tasks
        elif 'photo' in task_name_lower:
            return [
                {'name': 'Confirm photography package', 'description': 'Finalize hours, deliverables, and pricing'},
                {'name': 'Create shot list', 'description': 'List must-have photos and special requests'},
                {'name': 'Schedule pre-event consultation', 'description': 'Discuss timeline and locations'},
                {'name': 'Confirm equipment and backup plans', 'description': 'Verify gear and contingency arrangements'}
            ]
        
        # Makeup-related tasks
        elif 'makeup' in task_name_lower or 'styling' in task_name_lower:
            return [
                {'name': 'Schedule makeup trial', 'description': 'Test looks and finalize style'},
                {'name': 'Confirm timing and location', 'description': 'Set appointment time and place'},
                {'name': 'Discuss products and preferences', 'description': 'Review product choices and allergies'},
                {'name': 'Coordinate with other vendors', 'description': 'Align timing with photography and event'}
            ]
        
        # Generic fallback
        else:
            return [
                {'name': f'Plan {task.task_name}', 'description': 'Create detailed plan and timeline'},
                {'name': f'Coordinate {task.task_name}', 'description': 'Communicate with relevant parties'},
                {'name': f'Execute {task.task_name}', 'description': 'Complete the task activities'},
                {'name': f'Verify {task.task_name}', 'description': 'Confirm completion and quality'}
            ]
    
    def _estimate_duration(
        self,
        task: PrioritizedTask,
        event_context: Dict[str, Any],
        granularity_level: int
    ) -> timedelta:
        """
        Estimate duration for a task based on type and context.
        
        Args:
            task: Task to estimate
            event_context: Event context
            granularity_level: Granularity level of the task
            
        Returns:
            Estimated duration as timedelta
        """
        # Extract vendor type from task name
        task_name_lower = task.task_name.lower()
        
        # Determine base duration by vendor type
        base_hours = self.DEFAULT_DURATIONS['default']
        
        for vendor_type, hours in self.DEFAULT_DURATIONS.items():
            if vendor_type in task_name_lower:
                base_hours = hours
                break
        
        # Adjust based on priority (higher priority might need more time)
        if task.priority_level == "Critical":
            base_hours *= 1.2
        elif task.priority_level == "Low":
            base_hours *= 0.8
        
        # Adjust based on guest count (larger events need more time)
        guest_count = event_context.get('guest_count', 0)
        if guest_count > 200:
            base_hours *= 1.3
        elif guest_count > 100:
            base_hours *= 1.15
        
        return timedelta(hours=base_hours)
    
    def _estimate_duration_from_description(
        self,
        task_name: str,
        task_description: str,
        event_context: Dict[str, Any]
    ) -> timedelta:
        """
        Estimate duration for a sub-task based on its name and description.
        
        Args:
            task_name: Name of the sub-task
            task_description: Description of the sub-task
            event_context: Event context
            
        Returns:
            Estimated duration as timedelta
        """
        combined_text = f"{task_name} {task_description}".lower()
        
        # Quick tasks (30 min - 1 hour)
        quick_keywords = ['confirm', 'review', 'finalize', 'schedule', 'call', 'email']
        if any(keyword in combined_text for keyword in quick_keywords):
            return timedelta(minutes=45)
        
        # Medium tasks (1-2 hours)
        medium_keywords = ['coordinate', 'discuss', 'plan', 'create', 'prepare']
        if any(keyword in combined_text for keyword in medium_keywords):
            return timedelta(hours=1.5)
        
        # Long tasks (2-4 hours)
        long_keywords = ['setup', 'execute', 'deliver', 'install', 'arrange']
        if any(keyword in combined_text for keyword in long_keywords):
            return timedelta(hours=3)
        
        # Default to 1 hour
        return timedelta(hours=1)
    
    def _create_default_granular_task(
        self,
        task: PrioritizedTask,
        error_message: str
    ) -> GranularTask:
        """
        Create a default granular task when decomposition fails.
        
        Args:
            task: Original prioritized task
            error_message: Error that occurred
            
        Returns:
            GranularTask with default values
        """
        return GranularTask(
            task_id=task.task_id,
            parent_task_id=None,
            task_name=task.task_name,
            task_description=f"Priority: {task.priority_level}. Error during decomposition: {error_message}",
            granularity_level=self.LEVEL_TOP,
            estimated_duration=timedelta(hours=2),
            sub_tasks=[]
        )
