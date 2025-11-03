"""
Prioritization Agent Core for Task Management Agent

Analyzes tasks from EventPlanningState and assigns priority levels based on:
- Event context (date, guest count, budget)
- Task deadlines and time sensitivity
- Dependencies and critical path analysis
- Client requirements and preferences

Uses Ollama LLM (gemma:2b or tinyllama) for intelligent prioritization.
"""

import logging
from typing import List, Dict, Any, Optional
from datetime import datetime, timedelta
import json

from ..models.task_models import PrioritizedTask
from ..exceptions import SubAgentDataError
from ....workflows.state_models import EventPlanningState
from ....llm.optimized_manager import get_llm_manager
from ....config.settings import get_settings

logger = logging.getLogger(__name__)


class PrioritizationAgentCore:
    """
    Core agent for task prioritization.
    
    Analyzes tasks from the event planning workflow and assigns priority levels
    (Critical, High, Medium, Low) based on multiple factors including event context,
    deadlines, dependencies, and client requirements.
    """
    
    # Priority level constants
    PRIORITY_CRITICAL = "Critical"
    PRIORITY_HIGH = "High"
    PRIORITY_MEDIUM = "Medium"
    PRIORITY_LOW = "Low"
    
    # Priority score ranges
    SCORE_CRITICAL_MIN = 0.85
    SCORE_HIGH_MIN = 0.65
    SCORE_MEDIUM_MIN = 0.40
    
    def __init__(self, llm_model: Optional[str] = None):
        """
        Initialize Prioritization Agent with Ollama LLM.
        
        Args:
            llm_model: Optional LLM model name (gemma:2b or tinyllama).
                      Defaults to gemma:2b from settings.
        """
        self.settings = get_settings()
        self.llm_model = llm_model or self.settings.llm.gemma_model
        self.llm_manager = None
        
        logger.info(f"Initialized PrioritizationAgentCore with model: {self.llm_model}")
    
    async def _ensure_llm_manager(self):
        """Ensure LLM manager is initialized"""
        if self.llm_manager is None:
            self.llm_manager = await get_llm_manager()
    
    async def prioritize_tasks(self, state: EventPlanningState) -> List[PrioritizedTask]:
        """
        Analyze tasks from EventPlanningState and assign priority levels.
        
        Args:
            state: Current event planning workflow state
            
        Returns:
            List of PrioritizedTask objects with priority information
            
        Raises:
            SubAgentDataError: If required task data is missing or invalid
        """
        logger.info("Starting task prioritization...")
        
        try:
            # Ensure LLM manager is ready
            await self._ensure_llm_manager()
            
            # Extract tasks from state
            tasks = self._extract_tasks_from_state(state)
            
            if not tasks:
                logger.warning("No tasks found in state for prioritization")
                return []
            
            # Extract event context
            event_context = self._extract_event_context(state)
            
            # Prioritize each task
            prioritized_tasks = []
            for task in tasks:
                try:
                    prioritized_task = await self._prioritize_single_task(task, event_context, state)
                    prioritized_tasks.append(prioritized_task)
                except Exception as e:
                    logger.error(f"Error prioritizing task {task.get('task_id', 'unknown')}: {e}")
                    # Create a default priority task to continue processing
                    prioritized_tasks.append(self._create_default_priority_task(task, str(e)))
            
            logger.info(f"Successfully prioritized {len(prioritized_tasks)} tasks")
            return prioritized_tasks
            
        except Exception as e:
            error_msg = f"Failed to prioritize tasks: {str(e)}"
            logger.error(error_msg)
            raise SubAgentDataError(
                sub_agent_name="PrioritizationAgent",
                message=error_msg,
                details={"error": str(e)}
            )
    
    def _extract_tasks_from_state(self, state: EventPlanningState) -> List[Dict[str, Any]]:
        """
        Extract tasks from EventPlanningState.
        
        Tasks can come from:
        - timeline_data (if Timeline Agent has run)
        - selected_combination (vendor-specific tasks)
        - client_request (high-level requirements)
        
        Args:
            state: Event planning state
            
        Returns:
            List of task dictionaries
        """
        tasks = []
        
        # Extract from timeline_data if available
        timeline_data = state.get('timeline_data')
        if timeline_data and isinstance(timeline_data, dict):
            timeline_tasks = timeline_data.get('tasks', [])
            if timeline_tasks:
                tasks.extend(timeline_tasks)
                logger.debug(f"Extracted {len(timeline_tasks)} tasks from timeline_data")
        
        # If no tasks from timeline, create high-level tasks from selected combination
        if not tasks:
            selected_combination = state.get('selected_combination')
            if selected_combination:
                tasks = self._create_tasks_from_combination(selected_combination, state)
                logger.debug(f"Created {len(tasks)} high-level tasks from selected_combination")
        
        # Ensure each task has a unique ID
        for i, task in enumerate(tasks):
            if 'task_id' not in task:
                task['task_id'] = f"task_{i+1}"
            if 'task_name' not in task:
                task['task_name'] = task.get('name', f"Task {i+1}")
        
        return tasks
    
    def _create_tasks_from_combination(
        self, 
        combination: Dict[str, Any], 
        state: EventPlanningState
    ) -> List[Dict[str, Any]]:
        """
        Create high-level tasks from selected vendor combination.
        
        Args:
            combination: Selected vendor combination
            state: Event planning state
            
        Returns:
            List of task dictionaries
        """
        tasks = []
        task_id = 1
        
        # Venue tasks
        if combination.get('venue'):
            venue = combination['venue']
            tasks.append({
                'task_id': f"task_{task_id}",
                'task_name': f"Venue Setup - {venue.get('name', 'Unknown')}",
                'description': f"Coordinate venue setup and preparation",
                'vendor_type': 'venue',
                'vendor_id': venue.get('id'),
                'estimated_duration': '4 hours'
            })
            task_id += 1
        
        # Catering tasks
        if combination.get('caterer'):
            caterer = combination['caterer']
            tasks.append({
                'task_id': f"task_{task_id}",
                'task_name': f"Catering Coordination - {caterer.get('name', 'Unknown')}",
                'description': f"Coordinate catering services and menu",
                'vendor_type': 'caterer',
                'vendor_id': caterer.get('id'),
                'estimated_duration': '6 hours'
            })
            task_id += 1
        
        # Photography tasks
        if combination.get('photographer'):
            photographer = combination['photographer']
            tasks.append({
                'task_id': f"task_{task_id}",
                'task_name': f"Photography Session - {photographer.get('name', 'Unknown')}",
                'description': f"Coordinate photography coverage",
                'vendor_type': 'photographer',
                'vendor_id': photographer.get('id'),
                'estimated_duration': '8 hours'
            })
            task_id += 1
        
        # Makeup tasks
        if combination.get('makeup_artist'):
            makeup = combination['makeup_artist']
            tasks.append({
                'task_id': f"task_{task_id}",
                'task_name': f"Makeup Services - {makeup.get('name', 'Unknown')}",
                'description': f"Coordinate makeup and styling services",
                'vendor_type': 'makeup_artist',
                'vendor_id': makeup.get('id'),
                'estimated_duration': '3 hours'
            })
            task_id += 1
        
        return tasks
    
    def _extract_event_context(self, state: EventPlanningState) -> Dict[str, Any]:
        """
        Extract relevant event context for prioritization.
        
        Args:
            state: Event planning state
            
        Returns:
            Dictionary with event context information
        """
        client_request = state.get('client_request', {})
        
        context = {
            'event_type': client_request.get('event_type', 'unknown'),
            'event_date': client_request.get('date'),
            'guest_count': client_request.get('guest_count', 0),
            'budget': client_request.get('budget', 0),
            'location': client_request.get('location', 'unknown'),
            'preferences': client_request.get('preferences', {}),
            'requirements': client_request.get('requirements', {}),
            'current_date': datetime.now().isoformat()
        }
        
        # Calculate days until event
        if context['event_date']:
            try:
                event_date = datetime.fromisoformat(context['event_date'].replace('Z', '+00:00'))
                current_date = datetime.now()
                days_until_event = (event_date - current_date).days
                context['days_until_event'] = days_until_event
            except Exception as e:
                logger.warning(f"Could not parse event date: {e}")
                context['days_until_event'] = None
        
        return context
    
    async def _prioritize_single_task(
        self,
        task: Dict[str, Any],
        event_context: Dict[str, Any],
        state: EventPlanningState
    ) -> PrioritizedTask:
        """
        Prioritize a single task using LLM and scoring algorithm.
        
        Args:
            task: Task dictionary
            event_context: Event context information
            state: Event planning state
            
        Returns:
            PrioritizedTask object
        """
        # Calculate base priority score
        priority_score = self._calculate_priority_score(task, event_context)
        
        # Generate LLM prompt for intelligent prioritization
        prompt = self._create_prioritization_prompt(task, event_context, priority_score)
        
        # Get LLM enhancement
        try:
            llm_response = await self.llm_manager.generate_response(
                prompt=prompt,
                model=self.llm_model,
                temperature=0.3,  # Lower temperature for more consistent prioritization
                max_tokens=200
            )
            
            # Parse LLM response
            priority_level, rationale = self._parse_llm_response(llm_response, priority_score)
            
        except Exception as e:
            logger.warning(f"LLM prioritization failed for task {task.get('task_id')}: {e}")
            # Fallback to score-based prioritization
            priority_level = self._score_to_priority_level(priority_score)
            rationale = f"Automated prioritization based on score: {priority_score:.2f}"
        
        return PrioritizedTask(
            task_id=task['task_id'],
            task_name=task['task_name'],
            priority_level=priority_level,
            priority_score=priority_score,
            priority_rationale=rationale
        )
    
    def _calculate_priority_score(
        self,
        task: Dict[str, Any],
        event_context: Dict[str, Any]
    ) -> float:
        """
        Calculate numerical priority score based on multiple factors.
        
        Scoring factors:
        - Time sensitivity (40%): Days until event, task deadline
        - Dependency impact (25%): Tasks that block other tasks
        - Resource criticality (20%): Availability of required resources
        - Client importance (15%): Client preferences and requirements
        
        Args:
            task: Task dictionary
            event_context: Event context information
            
        Returns:
            Priority score between 0.0 and 1.0
        """
        score = 0.0
        
        # Time sensitivity score (40%)
        time_score = self._calculate_time_sensitivity_score(task, event_context)
        score += time_score * 0.40
        
        # Dependency impact score (25%)
        dependency_score = self._calculate_dependency_score(task)
        score += dependency_score * 0.25
        
        # Resource criticality score (20%)
        resource_score = self._calculate_resource_score(task, event_context)
        score += resource_score * 0.20
        
        # Client importance score (15%)
        client_score = self._calculate_client_importance_score(task, event_context)
        score += client_score * 0.15
        
        # Ensure score is between 0 and 1
        return max(0.0, min(1.0, score))
    
    def _calculate_time_sensitivity_score(
        self,
        task: Dict[str, Any],
        event_context: Dict[str, Any]
    ) -> float:
        """Calculate time sensitivity score based on deadlines"""
        days_until_event = event_context.get('days_until_event')
        
        if days_until_event is None:
            return 0.5  # Default medium priority if date unknown
        
        # Critical if event is within 7 days
        if days_until_event <= 7:
            return 1.0
        # High if within 14 days
        elif days_until_event <= 14:
            return 0.8
        # Medium if within 30 days
        elif days_until_event <= 30:
            return 0.6
        # Lower priority for events further out
        elif days_until_event <= 60:
            return 0.4
        else:
            return 0.2
    
    def _calculate_dependency_score(self, task: Dict[str, Any]) -> float:
        """Calculate score based on task dependencies"""
        # Check if task has dependencies or blocks other tasks
        dependencies = task.get('dependencies', [])
        blocks_tasks = task.get('blocks_tasks', [])
        
        # Tasks with no dependencies can start immediately (higher priority)
        if not dependencies:
            base_score = 0.7
        else:
            # More dependencies = potentially lower priority
            base_score = max(0.3, 0.7 - (len(dependencies) * 0.1))
        
        # Tasks that block others are higher priority
        if blocks_tasks:
            base_score += min(0.3, len(blocks_tasks) * 0.1)
        
        return min(1.0, base_score)
    
    def _calculate_resource_score(
        self,
        task: Dict[str, Any],
        event_context: Dict[str, Any]
    ) -> float:
        """Calculate score based on resource criticality"""
        vendor_type = task.get('vendor_type', '')
        
        # Venue and catering are typically most critical
        critical_vendors = ['venue', 'caterer']
        high_priority_vendors = ['photographer', 'makeup_artist']
        
        if vendor_type in critical_vendors:
            return 0.9
        elif vendor_type in high_priority_vendors:
            return 0.7
        else:
            return 0.5
    
    def _calculate_client_importance_score(
        self,
        task: Dict[str, Any],
        event_context: Dict[str, Any]
    ) -> float:
        """Calculate score based on client preferences and requirements"""
        preferences = event_context.get('preferences', {})
        requirements = event_context.get('requirements', {})
        
        task_name = task.get('task_name', '').lower()
        vendor_type = task.get('vendor_type', '').lower()
        
        # Check if task relates to client preferences
        for pref_key, pref_value in preferences.items():
            if pref_key.lower() in task_name or pref_key.lower() in vendor_type:
                return 0.9
        
        # Check if task relates to requirements
        for req_key, req_value in requirements.items():
            if req_key.lower() in task_name or req_key.lower() in vendor_type:
                return 0.8
        
        return 0.5  # Default medium importance
    
    def _create_prioritization_prompt(
        self,
        task: Dict[str, Any],
        event_context: Dict[str, Any],
        calculated_score: float
    ) -> str:
        """
        Generate LLM prompt for intelligent task prioritization.
        
        Args:
            task: Task dictionary
            event_context: Event context
            calculated_score: Pre-calculated priority score
            
        Returns:
            Formatted prompt string
        """
        days_until_event = event_context.get('days_until_event', 'unknown')
        
        prompt = f"""You are an expert event planning assistant. Analyze this task and provide a priority level and brief rationale.

Event Context:
- Event Type: {event_context.get('event_type')}
- Days Until Event: {days_until_event}
- Guest Count: {event_context.get('guest_count')}
- Budget: ${event_context.get('budget', 0):,.2f}

Task Details:
- Task Name: {task.get('task_name')}
- Description: {task.get('description', 'N/A')}
- Vendor Type: {task.get('vendor_type', 'N/A')}
- Estimated Duration: {task.get('estimated_duration', 'N/A')}
- Calculated Score: {calculated_score:.2f}

Based on the calculated score and event context, assign a priority level:
- Critical (0.85-1.0): Must be done immediately, blocks other tasks
- High (0.65-0.84): Important, should be done soon
- Medium (0.40-0.64): Normal priority, can be scheduled flexibly
- Low (0.0-0.39): Can be deferred if needed

Respond in this exact format:
Priority: [Critical/High/Medium/Low]
Rationale: [One sentence explaining why]"""
        
        return prompt
    
    def _parse_llm_response(
        self,
        llm_response: str,
        fallback_score: float
    ) -> tuple[str, str]:
        """
        Parse LLM response to extract priority level and rationale.
        
        Args:
            llm_response: Raw LLM response
            fallback_score: Score to use if parsing fails
            
        Returns:
            Tuple of (priority_level, rationale)
        """
        try:
            lines = llm_response.strip().split('\n')
            priority_level = None
            rationale = None
            
            for line in lines:
                line = line.strip()
                if line.startswith('Priority:'):
                    priority_text = line.replace('Priority:', '').strip()
                    # Extract priority level
                    for level in [self.PRIORITY_CRITICAL, self.PRIORITY_HIGH, 
                                 self.PRIORITY_MEDIUM, self.PRIORITY_LOW]:
                        if level.lower() in priority_text.lower():
                            priority_level = level
                            break
                elif line.startswith('Rationale:'):
                    rationale = line.replace('Rationale:', '').strip()
            
            # Validate parsed values
            if not priority_level:
                priority_level = self._score_to_priority_level(fallback_score)
            
            if not rationale:
                rationale = f"Priority determined by analysis (score: {fallback_score:.2f})"
            
            return priority_level, rationale
            
        except Exception as e:
            logger.warning(f"Failed to parse LLM response: {e}")
            return (
                self._score_to_priority_level(fallback_score),
                f"Automated prioritization (score: {fallback_score:.2f})"
            )
    
    def _score_to_priority_level(self, score: float) -> str:
        """
        Convert numerical score to priority level.
        
        Args:
            score: Priority score between 0.0 and 1.0
            
        Returns:
            Priority level string
        """
        if score >= self.SCORE_CRITICAL_MIN:
            return self.PRIORITY_CRITICAL
        elif score >= self.SCORE_HIGH_MIN:
            return self.PRIORITY_HIGH
        elif score >= self.SCORE_MEDIUM_MIN:
            return self.PRIORITY_MEDIUM
        else:
            return self.PRIORITY_LOW
    
    def _create_default_priority_task(
        self,
        task: Dict[str, Any],
        error_message: str
    ) -> PrioritizedTask:
        """
        Create a default priority task when prioritization fails.
        
        Args:
            task: Original task dictionary
            error_message: Error that occurred
            
        Returns:
            PrioritizedTask with default medium priority
        """
        return PrioritizedTask(
            task_id=task.get('task_id', 'unknown'),
            task_name=task.get('task_name', 'Unknown Task'),
            priority_level=self.PRIORITY_MEDIUM,
            priority_score=0.5,
            priority_rationale=f"Default priority assigned due to error: {error_message}"
        )
