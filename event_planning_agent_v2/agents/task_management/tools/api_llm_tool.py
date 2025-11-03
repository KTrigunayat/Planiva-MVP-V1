"""
API/LLM Tool for Task Enhancement

Processes consolidated tasks through LLM to enhance descriptions and provide
intelligent suggestions. Uses existing Ollama LLM infrastructure with retry
logic and fallback mechanisms for resilience.

Key Features:
- Context-aware prompt generation including task details, event context, and vendor info
- Structured data extraction: enhanced descriptions, suggestions, issues, best practices
- Automatic flagging of tasks requiring manual review
- Retry logic with exponential backoff for LLM failures
- Fallback mechanism to continue with unenhanced data when LLM unavailable
"""

import logging
import asyncio
import time
from typing import List, Dict, Any, Optional
import json

try:
    # Try relative imports first (when used as part of package)
    from ..models.consolidated_models import ConsolidatedTaskData, ConsolidatedTask
    from ..models.data_models import EnhancedTask
    from ..exceptions import ToolExecutionError
    from ....llm.optimized_manager import get_llm_manager
    from ....config.settings import get_settings
except ImportError:
    # Fall back to absolute imports (when running tests directly)
    from agents.task_management.models.consolidated_models import ConsolidatedTaskData, ConsolidatedTask
    from agents.task_management.models.data_models import EnhancedTask
    from agents.task_management.exceptions import ToolExecutionError
    from llm.optimized_manager import get_llm_manager
    from config.settings import get_settings

logger = logging.getLogger(__name__)


class APILLMTool:
    """
    Tool for enhancing tasks using LLM.
    
    Processes consolidated tasks through Ollama LLM to generate enhanced
    descriptions, suggestions, potential issues, and best practices.
    Implements retry logic and fallback mechanisms for resilience.
    """
    
    # Retry configuration
    MAX_RETRIES = 3
    INITIAL_BACKOFF = 1.0  # seconds
    BACKOFF_MULTIPLIER = 2.0
    MAX_BACKOFF = 30.0  # seconds
    
    def __init__(self, llm_model: Optional[str] = None):
        """
        Initialize API/LLM Tool with Ollama LLM infrastructure.
        
        Args:
            llm_model: Optional LLM model name (gemma:2b or tinyllama).
                      Defaults to gemma:2b from settings.
        """
        self.settings = get_settings()
        self.llm_model = llm_model or self.settings.llm.gemma_model
        self.llm_manager = None
        
        logger.info(f"Initialized APILLMTool with model: {self.llm_model}")
    
    async def _ensure_llm_manager(self):
        """Ensure LLM manager is initialized"""
        if self.llm_manager is None:
            self.llm_manager = await get_llm_manager()
    
    async def enhance_tasks(
        self,
        consolidated_data: ConsolidatedTaskData,
        event_context: Optional[Dict[str, Any]] = None
    ) -> List[EnhancedTask]:
        """
        Process consolidated tasks through LLM for enhancement.
        
        Args:
            consolidated_data: Consolidated task data from sub-agents
            event_context: Optional additional event context
            
        Returns:
            List of EnhancedTask objects with LLM enhancements
            
        Raises:
            ToolExecutionError: If critical enhancement failures occur
        """
        logger.info(f"Starting task enhancement for {len(consolidated_data.tasks)} tasks...")
        
        try:
            # Ensure LLM manager is ready
            await self._ensure_llm_manager()
            
            # Merge event context
            full_context = {**consolidated_data.event_context}
            if event_context:
                full_context.update(event_context)
            
            # Enhance each task
            enhanced_tasks = []
            for task in consolidated_data.tasks:
                try:
                    enhanced_task = await self._enhance_single_task(task, full_context)
                    enhanced_tasks.append(enhanced_task)
                except Exception as e:
                    logger.error(f"Error enhancing task {task.task_id}: {e}")
                    # Create fallback enhanced task
                    fallback_task = self._create_fallback_enhanced_task(task, str(e))
                    enhanced_tasks.append(fallback_task)
            
            logger.info(f"Successfully enhanced {len(enhanced_tasks)} tasks")
            return enhanced_tasks
            
        except Exception as e:
            error_msg = f"Failed to enhance tasks: {str(e)}"
            logger.error(error_msg)
            raise ToolExecutionError(
                tool_name="APILLMTool",
                message=error_msg,
                details={"error": str(e), "task_count": len(consolidated_data.tasks)}
            )
    
    async def _enhance_single_task(
        self,
        task: ConsolidatedTask,
        event_context: Dict[str, Any]
    ) -> EnhancedTask:
        """
        Enhance a single task using LLM with retry logic.
        
        Args:
            task: Consolidated task to enhance
            event_context: Event context information
            
        Returns:
            EnhancedTask object with LLM enhancements
        """
        # Generate enhancement prompt
        prompt = self._generate_enhancement_prompt(task, event_context)
        
        # Try to get LLM enhancement with retries
        llm_response = None
        last_error = None
        
        for attempt in range(self.MAX_RETRIES):
            try:
                llm_response = await self._call_llm_with_timeout(prompt, attempt)
                break  # Success, exit retry loop
            except Exception as e:
                last_error = e
                logger.warning(
                    f"LLM enhancement attempt {attempt + 1}/{self.MAX_RETRIES} "
                    f"failed for task {task.task_id}: {e}"
                )
                
                if attempt < self.MAX_RETRIES - 1:
                    # Calculate backoff time
                    backoff_time = min(
                        self.INITIAL_BACKOFF * (self.BACKOFF_MULTIPLIER ** attempt),
                        self.MAX_BACKOFF
                    )
                    logger.info(f"Retrying in {backoff_time:.1f} seconds...")
                    await asyncio.sleep(backoff_time)
        
        # Parse LLM response or create fallback
        if llm_response:
            try:
                enhanced_task = self._parse_llm_response(task, llm_response, event_context)
                return enhanced_task
            except Exception as e:
                logger.error(f"Failed to parse LLM response for task {task.task_id}: {e}")
                return self._create_fallback_enhanced_task(task, f"Parse error: {e}")
        else:
            # All retries failed, use fallback
            logger.warning(
                f"All LLM enhancement attempts failed for task {task.task_id}, "
                f"using fallback. Last error: {last_error}"
            )
            return self._create_fallback_enhanced_task(task, str(last_error))
    
    async def _call_llm_with_timeout(
        self,
        prompt: str,
        attempt: int
    ) -> str:
        """
        Call LLM with timeout protection.
        
        Args:
            prompt: Enhancement prompt
            attempt: Current attempt number (for logging)
            
        Returns:
            LLM response string
            
        Raises:
            asyncio.TimeoutError: If LLM call times out
            Exception: If LLM call fails
        """
        timeout = self.settings.llm.model_timeout
        
        try:
            response = await asyncio.wait_for(
                self.llm_manager.generate_response(
                    prompt=prompt,
                    model=self.llm_model,
                    temperature=0.4,  # Lower temperature for more consistent enhancements
                    max_tokens=500,
                    use_batch=False  # Direct execution for task enhancement
                ),
                timeout=timeout
            )
            return response
        except asyncio.TimeoutError:
            logger.warning(f"LLM call timed out after {timeout} seconds (attempt {attempt + 1})")
            raise
        except Exception as e:
            logger.error(f"LLM call failed (attempt {attempt + 1}): {e}")
            raise
    
    def _generate_enhancement_prompt(
        self,
        task: ConsolidatedTask,
        event_context: Dict[str, Any]
    ) -> str:
        """
        Create context-aware prompt for task enhancement.
        
        Includes task details, event context, vendor information, dependencies,
        and resource requirements to generate comprehensive enhancements.
        
        Args:
            task: Consolidated task to enhance
            event_context: Event context information
            
        Returns:
            Formatted prompt string
        """
        # Extract key context information
        event_type = event_context.get('event_type', 'unknown')
        guest_count = event_context.get('guest_count', 0)
        budget = event_context.get('budget', 0)
        days_until_event = event_context.get('days_until_event', 'unknown')
        
        # Format dependencies
        dependencies_str = "None"
        if task.dependencies:
            dependencies_str = ", ".join(task.dependencies)
        
        # Format resources
        resources_str = "None specified"
        if task.resources_required:
            resource_list = [
                f"{r.resource_name} ({r.resource_type})"
                for r in task.resources_required
            ]
            resources_str = ", ".join(resource_list)
        
        # Format sub-tasks
        subtasks_str = "None"
        if task.sub_tasks:
            subtasks_str = ", ".join(task.sub_tasks)
        
        prompt = f"""You are an expert event planning assistant. Enhance this task with detailed insights, suggestions, and best practices.

Event Context:
- Event Type: {event_type}
- Guest Count: {guest_count}
- Budget: ${budget:,.2f}
- Days Until Event: {days_until_event}

Task Information:
- Task ID: {task.task_id}
- Task Name: {task.task_name}
- Description: {task.task_description}
- Priority: {task.priority_level} (Score: {task.priority_score:.2f})
- Estimated Duration: {task.estimated_duration}
- Dependencies: {dependencies_str}
- Required Resources: {resources_str}
- Sub-tasks: {subtasks_str}

Please provide:
1. Enhanced Description: A more detailed, actionable description of what needs to be done
2. Suggestions: 2-3 specific suggestions to improve task execution
3. Potential Issues: 2-3 potential problems or challenges to watch for
4. Best Practices: 2-3 industry best practices for this type of task

Respond in this exact JSON format:
{{
  "enhanced_description": "Detailed description here",
  "suggestions": ["Suggestion 1", "Suggestion 2", "Suggestion 3"],
  "potential_issues": ["Issue 1", "Issue 2", "Issue 3"],
  "best_practices": ["Practice 1", "Practice 2", "Practice 3"],
  "requires_manual_review": false
}}

Set "requires_manual_review" to true if critical information is missing or if the task requires special attention."""
        
        return prompt
    
    def _parse_llm_response(
        self,
        task: ConsolidatedTask,
        llm_response: str,
        event_context: Dict[str, Any]
    ) -> EnhancedTask:
        """
        Extract structured data from LLM response.
        
        Parses the LLM response to extract enhanced_description, suggestions,
        potential_issues, and best_practices. Handles malformed responses
        gracefully.
        
        Args:
            task: Original consolidated task
            llm_response: Raw LLM response
            event_context: Event context for validation
            
        Returns:
            EnhancedTask object with parsed data
        """
        try:
            # Try to extract JSON from response
            response_text = llm_response.strip()
            
            # Find JSON block (might be wrapped in markdown code blocks)
            if "```json" in response_text:
                start = response_text.find("```json") + 7
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            elif "```" in response_text:
                start = response_text.find("```") + 3
                end = response_text.find("```", start)
                response_text = response_text[start:end].strip()
            
            # Parse JSON
            parsed_data = json.loads(response_text)
            
            # Extract fields with defaults
            enhanced_description = parsed_data.get(
                'enhanced_description',
                task.task_description
            )
            suggestions = parsed_data.get('suggestions', [])
            potential_issues = parsed_data.get('potential_issues', [])
            best_practices = parsed_data.get('best_practices', [])
            requires_manual_review = parsed_data.get('requires_manual_review', False)
            
            # Validate and clean data
            if not isinstance(suggestions, list):
                suggestions = [str(suggestions)]
            if not isinstance(potential_issues, list):
                potential_issues = [str(potential_issues)]
            if not isinstance(best_practices, list):
                best_practices = [str(best_practices)]
            
            # Check if manual review is needed based on content
            if self._flag_for_manual_review(task, parsed_data, event_context):
                requires_manual_review = True
            
            return EnhancedTask(
                task_id=task.task_id,
                enhanced_description=enhanced_description,
                suggestions=suggestions[:5],  # Limit to 5 suggestions
                potential_issues=potential_issues[:5],  # Limit to 5 issues
                best_practices=best_practices[:5],  # Limit to 5 practices
                requires_manual_review=requires_manual_review
            )
            
        except json.JSONDecodeError as e:
            logger.warning(f"Failed to parse JSON from LLM response for task {task.task_id}: {e}")
            # Try to extract information from unstructured text
            return self._parse_unstructured_response(task, llm_response)
        except Exception as e:
            logger.error(f"Error parsing LLM response for task {task.task_id}: {e}")
            raise
    
    def _parse_unstructured_response(
        self,
        task: ConsolidatedTask,
        llm_response: str
    ) -> EnhancedTask:
        """
        Parse unstructured LLM response as fallback.
        
        Args:
            task: Original consolidated task
            llm_response: Raw LLM response
            
        Returns:
            EnhancedTask with best-effort parsing
        """
        logger.info(f"Attempting unstructured parsing for task {task.task_id}")
        
        # Use the response as enhanced description
        enhanced_description = llm_response.strip()[:500]  # Limit length
        
        # Try to extract sections
        suggestions = []
        potential_issues = []
        best_practices = []
        
        lines = llm_response.split('\n')
        current_section = None
        
        for line in lines:
            line = line.strip()
            if not line:
                continue
            
            # Detect sections
            if 'suggestion' in line.lower():
                current_section = 'suggestions'
            elif 'issue' in line.lower() or 'problem' in line.lower():
                current_section = 'issues'
            elif 'practice' in line.lower() or 'best' in line.lower():
                current_section = 'practices'
            elif line.startswith('-') or line.startswith('•') or line[0].isdigit():
                # This is a list item
                item = line.lstrip('-•0123456789. ').strip()
                if item and current_section == 'suggestions':
                    suggestions.append(item)
                elif item and current_section == 'issues':
                    potential_issues.append(item)
                elif item and current_section == 'practices':
                    best_practices.append(item)
        
        return EnhancedTask(
            task_id=task.task_id,
            enhanced_description=enhanced_description or task.task_description,
            suggestions=suggestions[:3],
            potential_issues=potential_issues[:3],
            best_practices=best_practices[:3],
            requires_manual_review=True  # Flag for review due to parsing issues
        )
    
    def _flag_for_manual_review(
        self,
        task: ConsolidatedTask,
        parsed_data: Dict[str, Any],
        event_context: Dict[str, Any]
    ) -> bool:
        """
        Identify tasks with missing information that require manual review.
        
        Checks for:
        - Missing or incomplete task descriptions
        - Missing resource assignments
        - Missing dependencies for high-priority tasks
        - Insufficient event context
        - Empty or generic LLM enhancements
        
        Args:
            task: Original consolidated task
            parsed_data: Parsed LLM response data
            event_context: Event context information
            
        Returns:
            True if task requires manual review, False otherwise
        """
        # Check for missing critical information
        if not task.task_description or len(task.task_description) < 10:
            logger.info(f"Task {task.task_id} flagged: insufficient description")
            return True
        
        # High priority tasks without dependencies might need review
        if task.priority_level in ['Critical', 'High'] and not task.dependencies:
            logger.debug(f"Task {task.task_id} flagged: high priority without dependencies")
            # This is just a warning, not necessarily requiring review
        
        # Check if resources are specified for tasks that likely need them
        if task.priority_level == 'Critical' and not task.resources_required:
            logger.info(f"Task {task.task_id} flagged: critical task without resources")
            return True
        
        # Check if LLM enhancement is too generic or empty
        enhanced_desc = parsed_data.get('enhanced_description', '')
        if len(enhanced_desc) < 20:
            logger.info(f"Task {task.task_id} flagged: insufficient enhancement")
            return True
        
        # Check if no suggestions or issues were identified
        suggestions = parsed_data.get('suggestions', [])
        issues = parsed_data.get('potential_issues', [])
        if not suggestions and not issues:
            logger.info(f"Task {task.task_id} flagged: no suggestions or issues identified")
            return True
        
        # Check for placeholder or generic content
        generic_phrases = ['to be determined', 'tbd', 'unknown', 'not specified', 'n/a']
        desc_lower = task.task_description.lower()
        if any(phrase in desc_lower for phrase in generic_phrases):
            logger.info(f"Task {task.task_id} flagged: contains generic placeholder text")
            return True
        
        return False
    
    def _create_fallback_enhanced_task(
        self,
        task: ConsolidatedTask,
        error_message: str
    ) -> EnhancedTask:
        """
        Create fallback enhanced task when LLM enhancement fails.
        
        Uses the original task description and generates basic suggestions
        based on task properties without LLM assistance.
        
        Args:
            task: Original consolidated task
            error_message: Error that caused fallback
            
        Returns:
            EnhancedTask with fallback data
        """
        logger.info(f"Creating fallback enhanced task for {task.task_id}")
        
        # Use original description
        enhanced_description = task.task_description
        
        # Generate basic suggestions based on task properties
        suggestions = []
        if task.dependencies:
            suggestions.append(
                f"Ensure all {len(task.dependencies)} dependent tasks are completed first"
            )
        if task.resources_required:
            suggestions.append(
                f"Confirm availability of {len(task.resources_required)} required resources"
            )
        if task.priority_level in ['Critical', 'High']:
            suggestions.append(
                "This is a high-priority task - allocate sufficient time and resources"
            )
        
        # Generate basic potential issues
        potential_issues = []
        if task.resource_conflicts:
            potential_issues.append(
                f"Resource conflicts detected: {', '.join(task.resource_conflicts[:2])}"
            )
        if not task.resources_required:
            potential_issues.append(
                "No resources specified - may need to identify required resources"
            )
        
        # Generate basic best practices
        best_practices = [
            "Communicate clearly with all stakeholders",
            "Document progress and any issues encountered",
            "Build in buffer time for unexpected delays"
        ]
        
        return EnhancedTask(
            task_id=task.task_id,
            enhanced_description=enhanced_description,
            suggestions=suggestions,
            potential_issues=potential_issues,
            best_practices=best_practices,
            requires_manual_review=True  # Always flag fallback tasks for review
        )
