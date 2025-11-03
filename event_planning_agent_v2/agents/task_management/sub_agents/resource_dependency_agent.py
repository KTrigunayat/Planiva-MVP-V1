"""
Resource & Dependency Agent Core for Task Management Agent

Identifies task dependencies and resource requirements based on:
- Task relationships and logical prerequisites
- Resource requirements (vendors, equipment, personnel, venue)
- Event context and vendor capabilities
- Potential resource conflicts

Uses Ollama LLM (gemma:2b or tinyllama) for intelligent dependency analysis.
"""

import logging
from typing import List, Dict, Any, Optional, Set
import re

from ..models.task_models import GranularTask, TaskWithDependencies
from ..models.data_models import Resource
from ..exceptions import SubAgentDataError
from ....workflows.state_models import EventPlanningState
from ....llm.optimized_manager import get_llm_manager
from ....config.settings import get_settings

logger = logging.getLogger(__name__)


class ResourceDependencyAgentCore:
    """
    Core agent for dependency analysis and resource identification.
    
    Analyzes task relationships to identify dependencies and extracts
    required resources (vendors, equipment, personnel, venue) from task
    descriptions and EventPlanningState.
    """
    
    # Resource type constants
    RESOURCE_VENDOR = "vendor"
    RESOURCE_EQUIPMENT = "equipment"
    RESOURCE_PERSONNEL = "personnel"
    RESOURCE_VENUE = "venue"
    
    # Dependency keywords for rule-based detection
    DEPENDENCY_KEYWORDS = {
        'before': ['before', 'prior to', 'prerequisite', 'must precede'],
        'after': ['after', 'following', 'once', 'when', 'requires'],
        'blocking': ['blocks', 'prevents', 'must complete before']
    }
    
    def __init__(self, llm_model: Optional[str] = None):
        """
        Initialize Resource & Dependency Agent with Ollama LLM.
        
        Args:
            llm_model: Optional LLM model name (gemma:2b or tinyllama).
                      Defaults to gemma:2b from settings.
        """
        self.settings = get_settings()
        self.llm_model = llm_model or self.settings.llm.gemma_model
        self.llm_manager = None
        
        logger.info(f"Initialized ResourceDependencyAgentCore with model: {self.llm_model}")
    
    async def _ensure_llm_manager(self):
        """Ensure LLM manager is initialized"""
        if self.llm_manager is None:
            self.llm_manager = await get_llm_manager()
    
    async def analyze_dependencies(
        self,
        tasks: List[GranularTask],
        state: EventPlanningState
    ) -> List[TaskWithDependencies]:
        """
        Identify task dependencies and resource requirements.
        
        Args:
            tasks: List of granular tasks from Granularity Agent
            state: Current event planning workflow state
            
        Returns:
            List of TaskWithDependencies objects
            
        Raises:
            SubAgentDataError: If required data is missing or invalid
        """
        logger.info(f"Starting dependency analysis for {len(tasks)} tasks...")
        
        try:
            # Ensure LLM manager is ready
            await self._ensure_llm_manager()
            
            if not tasks:
                logger.warning("No tasks provided for dependency analysis")
                return []
            
            # Extract event context and available resources
            event_context = self._extract_event_context(state)
            
            # Analyze each task
            tasks_with_dependencies = []
            for task in tasks:
                try:
                    analyzed_task = await self._analyze_single_task(task, tasks, event_context, state)
                    tasks_with_dependencies.append(analyzed_task)
                except Exception as e:
                    logger.error(f"Error analyzing task {task.task_id}: {e}")
                    # Create a default task to continue processing
                    default_task = self._create_default_task_with_dependencies(task, str(e))
                    tasks_with_dependencies.append(default_task)
            
            logger.info(f"Successfully analyzed dependencies for {len(tasks_with_dependencies)} tasks")
            return tasks_with_dependencies
            
        except Exception as e:
            error_msg = f"Failed to analyze dependencies: {str(e)}"
            logger.error(error_msg)
            raise SubAgentDataError(
                sub_agent_name="ResourceDependencyAgent",
                message=error_msg,
                details={"error": str(e)}
            )
    
    def _extract_event_context(self, state: EventPlanningState) -> Dict[str, Any]:
        """
        Extract relevant event context for dependency analysis.
        
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
            'selected_combination': state.get('selected_combination', {}),
            'timeline_data': state.get('timeline_data', {})
        }
        
        return context
    
    async def _analyze_single_task(
        self,
        task: GranularTask,
        all_tasks: List[GranularTask],
        event_context: Dict[str, Any],
        state: EventPlanningState
    ) -> TaskWithDependencies:
        """
        Analyze a single task for dependencies and resources.
        
        Args:
            task: Task to analyze
            all_tasks: All tasks for dependency detection
            event_context: Event context information
            state: Event planning state
            
        Returns:
            TaskWithDependencies object
        """
        # Detect dependencies
        dependencies = self._detect_dependencies(task, all_tasks)
        
        # Identify required resources
        resources = await self._identify_resources(task, event_context, state)
        
        # Detect potential resource conflicts
        resource_conflicts = self._detect_resource_conflicts(task, resources, all_tasks)
        
        return TaskWithDependencies(
            task_id=task.task_id,
            task_name=task.task_name,
            dependencies=dependencies,
            resources_required=resources,
            resource_conflicts=resource_conflicts
        )
    
    def _detect_dependencies(
        self,
        task: GranularTask,
        all_tasks: List[GranularTask]
    ) -> List[str]:
        """
        Analyze task relationships and determine prerequisite tasks.
        
        Uses multiple strategies:
        1. Parent-child relationships (sub-tasks depend on parent)
        2. Logical dependencies (setup before execution)
        3. Keyword-based detection in task descriptions
        4. Temporal ordering (earlier tasks may be prerequisites)
        
        Args:
            task: Task to analyze
            all_tasks: All tasks for relationship analysis
            
        Returns:
            List of task IDs that are prerequisites
        """
        dependencies = []
        
        # Strategy 1: Parent-child relationships
        # Sub-tasks implicitly depend on their parent being started
        if task.parent_task_id:
            # Check if parent exists in task list
            parent_exists = any(t.task_id == task.parent_task_id for t in all_tasks)
            if parent_exists:
                dependencies.append(task.parent_task_id)
        
        # Strategy 2: Sibling dependencies (sub-tasks of same parent)
        # Some sub-tasks naturally come before others
        if task.parent_task_id:
            siblings = [t for t in all_tasks 
                       if t.parent_task_id == task.parent_task_id 
                       and t.task_id != task.task_id]
            
            # Detect logical ordering among siblings
            sibling_deps = self._detect_sibling_dependencies(task, siblings)
            dependencies.extend(sibling_deps)
        
        # Strategy 3: Keyword-based dependency detection
        keyword_deps = self._detect_keyword_dependencies(task, all_tasks)
        dependencies.extend(keyword_deps)
        
        # Strategy 4: Logical task ordering
        logical_deps = self._detect_logical_dependencies(task, all_tasks)
        dependencies.extend(logical_deps)
        
        # Remove duplicates and self-references
        dependencies = list(set(dependencies))
        if task.task_id in dependencies:
            dependencies.remove(task.task_id)
        
        return dependencies
    
    def _detect_sibling_dependencies(
        self,
        task: GranularTask,
        siblings: List[GranularTask]
    ) -> List[str]:
        """
        Detect dependencies among sibling tasks (same parent).
        
        Args:
            task: Current task
            siblings: Sibling tasks
            
        Returns:
            List of sibling task IDs that are prerequisites
        """
        dependencies = []
        task_name_lower = task.task_name.lower()
        task_desc_lower = task.task_description.lower()
        
        # Tasks that typically come later in a sequence
        later_stage_keywords = [
            'finalize', 'confirm', 'verify', 'review', 'complete',
            'execute', 'deliver', 'wrap up', 'close out'
        ]
        
        # Tasks that typically come earlier
        early_stage_keywords = [
            'plan', 'schedule', 'book', 'reserve', 'initiate',
            'setup', 'prepare', 'coordinate', 'arrange'
        ]
        
        # If current task is a later-stage task, it depends on earlier tasks
        is_later_stage = any(keyword in task_name_lower or keyword in task_desc_lower 
                            for keyword in later_stage_keywords)
        
        if is_later_stage:
            for sibling in siblings:
                sibling_name_lower = sibling.task_name.lower()
                sibling_desc_lower = sibling.task_description.lower()
                
                # Check if sibling is an early-stage task
                is_early_stage = any(keyword in sibling_name_lower or keyword in sibling_desc_lower
                                    for keyword in early_stage_keywords)
                
                if is_early_stage:
                    dependencies.append(sibling.task_id)
        
        return dependencies
    
    def _detect_keyword_dependencies(
        self,
        task: GranularTask,
        all_tasks: List[GranularTask]
    ) -> List[str]:
        """
        Detect dependencies using keyword analysis in task descriptions.
        
        Args:
            task: Current task
            all_tasks: All tasks
            
        Returns:
            List of task IDs that are prerequisites based on keywords
        """
        dependencies = []
        task_desc_lower = task.task_description.lower()
        
        # Look for explicit dependency keywords
        for other_task in all_tasks:
            if other_task.task_id == task.task_id:
                continue
            
            other_name_lower = other_task.task_name.lower()
            
            # Check if other task is mentioned in current task's description
            if other_name_lower in task_desc_lower:
                # Check for dependency keywords
                for keyword_type, keywords in self.DEPENDENCY_KEYWORDS.items():
                    for keyword in keywords:
                        if keyword in task_desc_lower:
                            # This suggests a dependency
                            dependencies.append(other_task.task_id)
                            break
        
        return dependencies
    
    def _detect_logical_dependencies(
        self,
        task: GranularTask,
        all_tasks: List[GranularTask]
    ) -> List[str]:
        """
        Detect logical dependencies based on task types and event flow.
        
        Common event planning dependencies:
        - Venue must be booked before catering/setup
        - Contracts must be signed before coordination
        - Planning must happen before execution
        
        Args:
            task: Current task
            all_tasks: All tasks
            
        Returns:
            List of task IDs that are logical prerequisites
        """
        dependencies = []
        task_name_lower = task.task_name.lower()
        task_desc_lower = task.task_description.lower()
        
        # Define logical dependency rules
        dependency_rules = {
            # Coordination tasks depend on booking/contract tasks
            'coordinate': ['book', 'contract', 'confirm', 'reserve'],
            'setup': ['book', 'contract', 'plan', 'coordinate'],
            'execute': ['plan', 'coordinate', 'setup', 'prepare'],
            'deliver': ['execute', 'setup', 'prepare'],
            'verify': ['execute', 'deliver', 'complete'],
            'finalize': ['coordinate', 'confirm', 'review']
        }
        
        # Check if current task matches any rule
        for task_keyword, prerequisite_keywords in dependency_rules.items():
            if task_keyword in task_name_lower or task_keyword in task_desc_lower:
                # Find tasks that match prerequisite keywords
                for other_task in all_tasks:
                    if other_task.task_id == task.task_id:
                        continue
                    
                    other_name_lower = other_task.task_name.lower()
                    other_desc_lower = other_task.task_description.lower()
                    
                    # Check if other task matches any prerequisite keyword
                    for prereq_keyword in prerequisite_keywords:
                        if prereq_keyword in other_name_lower or prereq_keyword in other_desc_lower:
                            dependencies.append(other_task.task_id)
                            break
        
        return dependencies
    
    async def _identify_resources(
        self,
        task: GranularTask,
        event_context: Dict[str, Any],
        state: EventPlanningState
    ) -> List[Resource]:
        """
        Extract required resources from task descriptions and EventPlanningState.
        
        Identifies:
        - Vendors from selected_combination
        - Equipment from task descriptions and vendor capabilities
        - Personnel requirements
        - Venue resources
        
        Args:
            task: Task to analyze
            event_context: Event context
            state: Event planning state
            
        Returns:
            List of Resource objects
        """
        resources = []
        
        # Extract vendor resources from selected combination
        vendor_resources = self._extract_vendor_resources(task, event_context)
        resources.extend(vendor_resources)
        
        # Extract equipment resources using LLM
        try:
            equipment_resources = await self._extract_equipment_resources_llm(task, event_context)
            resources.extend(equipment_resources)
        except Exception as e:
            logger.warning(f"LLM equipment extraction failed for task {task.task_id}: {e}")
            # Fallback to rule-based extraction
            equipment_resources = self._extract_equipment_resources_fallback(task)
            resources.extend(equipment_resources)
        
        # Extract personnel resources
        personnel_resources = self._extract_personnel_resources(task, event_context)
        resources.extend(personnel_resources)
        
        # Extract venue resources
        venue_resources = self._extract_venue_resources(task, event_context)
        resources.extend(venue_resources)
        
        # Handle missing resource data
        if not resources:
            logger.warning(f"No resources identified for task {task.task_id}")
            # Add a placeholder resource to indicate analysis was performed
            resources.append(Resource(
                resource_type="unknown",
                resource_id="unknown",
                resource_name="Resources to be determined",
                quantity_required=0,
                availability_constraint="Requires manual resource identification"
            ))
        
        return resources
    
    def _extract_vendor_resources(
        self,
        task: GranularTask,
        event_context: Dict[str, Any]
    ) -> List[Resource]:
        """
        Extract vendor resources from selected combination.
        
        Args:
            task: Task to analyze
            event_context: Event context with selected_combination
            
        Returns:
            List of vendor Resource objects
        """
        resources = []
        selected_combination = event_context.get('selected_combination', {})
        
        task_name_lower = task.task_name.lower()
        task_desc_lower = task.task_description.lower()
        
        # Map vendor types to keywords
        vendor_mappings = {
            'venue': ['venue', 'location', 'space', 'hall'],
            'caterer': ['cater', 'food', 'menu', 'dining', 'meal'],
            'photographer': ['photo', 'picture', 'camera', 'shoot'],
            'makeup_artist': ['makeup', 'styling', 'beauty', 'hair']
        }
        
        # Check each vendor type
        for vendor_key, keywords in vendor_mappings.items():
            # Check if task relates to this vendor type
            if any(keyword in task_name_lower or keyword in task_desc_lower 
                   for keyword in keywords):
                # Get vendor from selected combination
                vendor = selected_combination.get(vendor_key)
                if vendor:
                    resources.append(Resource(
                        resource_type=self.RESOURCE_VENDOR,
                        resource_id=str(vendor.get('id', 'unknown')),
                        resource_name=vendor.get('name', f'Unknown {vendor_key}'),
                        quantity_required=1,
                        availability_constraint=None
                    ))
        
        return resources
    
    async def _extract_equipment_resources_llm(
        self,
        task: GranularTask,
        event_context: Dict[str, Any]
    ) -> List[Resource]:
        """
        Use LLM to extract equipment requirements from task description.
        
        Args:
            task: Task to analyze
            event_context: Event context
            
        Returns:
            List of equipment Resource objects
        """
        # Generate prompt for equipment extraction
        prompt = self._create_dependency_analysis_prompt(task, event_context)
        
        # Get LLM response
        llm_response = await self.llm_manager.generate_response(
            prompt=prompt,
            model=self.llm_model,
            temperature=0.3,
            max_tokens=300
        )
        
        # Parse equipment from response
        equipment_resources = self._parse_equipment_from_llm_response(llm_response, task)
        
        return equipment_resources
    
    def _create_dependency_analysis_prompt(
        self,
        task: GranularTask,
        event_context: Dict[str, Any]
    ) -> str:
        """
        Generate LLM prompt for dependency detection and resource identification.
        
        Args:
            task: Task to analyze
            event_context: Event context
            
        Returns:
            Formatted prompt string
        """
        prompt = f"""You are an expert event planning assistant. Analyze this task and identify required equipment and resources.

Event Context:
- Event Type: {event_context.get('event_type')}
- Guest Count: {event_context.get('guest_count')}
- Location: {event_context.get('location')}

Task Details:
- Task Name: {task.task_name}
- Description: {task.task_description}
- Estimated Duration: {task.estimated_duration}

Identify all equipment and resources needed for this task. Consider:
- Physical equipment (tables, chairs, audio/visual, lighting, etc.)
- Supplies and materials
- Special tools or technology
- Transportation needs

Respond in this exact format:
Equipment 1: [Name] (Quantity: [number])
Equipment 2: [Name] (Quantity: [number])
Equipment 3: [Name] (Quantity: [number])

If no specific equipment is needed, respond with:
Equipment: None required"""
        
        return prompt
    
    def _parse_equipment_from_llm_response(
        self,
        llm_response: str,
        task: GranularTask
    ) -> List[Resource]:
        """
        Parse equipment resources from LLM response.
        
        Args:
            llm_response: Raw LLM response
            task: Task being analyzed
            
        Returns:
            List of equipment Resource objects
        """
        resources = []
        
        try:
            lines = llm_response.strip().split('\n')
            
            for line in lines:
                line = line.strip()
                
                # Skip empty lines and headers
                if not line or line.lower().startswith('equipment:'):
                    continue
                
                # Check for "None required" response
                if 'none required' in line.lower() or 'no equipment' in line.lower():
                    break
                
                # Parse equipment line: "Equipment N: Name (Quantity: X)"
                match = re.match(r'Equipment \d+:\s*(.+?)\s*\(Quantity:\s*(\d+)\)', line, re.IGNORECASE)
                if match:
                    equipment_name = match.group(1).strip()
                    quantity = int(match.group(2))
                    
                    resources.append(Resource(
                        resource_type=self.RESOURCE_EQUIPMENT,
                        resource_id=f"equipment_{len(resources)+1}",
                        resource_name=equipment_name,
                        quantity_required=quantity,
                        availability_constraint=None
                    ))
        
        except Exception as e:
            logger.warning(f"Failed to parse equipment from LLM response: {e}")
        
        return resources
    
    def _extract_equipment_resources_fallback(
        self,
        task: GranularTask
    ) -> List[Resource]:
        """
        Fallback rule-based equipment extraction.
        
        Args:
            task: Task to analyze
            
        Returns:
            List of equipment Resource objects
        """
        resources = []
        combined_text = f"{task.task_name} {task.task_description}".lower()
        
        # Common equipment keywords
        equipment_keywords = {
            'tables': 'Tables',
            'chairs': 'Chairs',
            'microphone': 'Microphone/Audio System',
            'projector': 'Projector',
            'screen': 'Projection Screen',
            'lighting': 'Lighting Equipment',
            'sound system': 'Sound System',
            'decorations': 'Decorations',
            'linens': 'Table Linens',
            'utensils': 'Utensils and Serving Ware'
        }
        
        for keyword, equipment_name in equipment_keywords.items():
            if keyword in combined_text:
                resources.append(Resource(
                    resource_type=self.RESOURCE_EQUIPMENT,
                    resource_id=f"equipment_{keyword.replace(' ', '_')}",
                    resource_name=equipment_name,
                    quantity_required=1,
                    availability_constraint=None
                ))
        
        return resources
    
    def _extract_personnel_resources(
        self,
        task: GranularTask,
        event_context: Dict[str, Any]
    ) -> List[Resource]:
        """
        Extract personnel requirements from task.
        
        Args:
            task: Task to analyze
            event_context: Event context
            
        Returns:
            List of personnel Resource objects
        """
        resources = []
        combined_text = f"{task.task_name} {task.task_description}".lower()
        
        # Personnel keywords
        personnel_keywords = {
            'coordinator': ('Event Coordinator', 1),
            'staff': ('Event Staff', 2),
            'server': ('Servers', 3),
            'bartender': ('Bartenders', 2),
            'security': ('Security Personnel', 2),
            'valet': ('Valet Attendants', 2),
            'assistant': ('Assistant', 1)
        }
        
        for keyword, (personnel_name, default_quantity) in personnel_keywords.items():
            if keyword in combined_text:
                resources.append(Resource(
                    resource_type=self.RESOURCE_PERSONNEL,
                    resource_id=f"personnel_{keyword}",
                    resource_name=personnel_name,
                    quantity_required=default_quantity,
                    availability_constraint=None
                ))
        
        return resources
    
    def _extract_venue_resources(
        self,
        task: GranularTask,
        event_context: Dict[str, Any]
    ) -> List[Resource]:
        """
        Extract venue resources from selected combination.
        
        Args:
            task: Task to analyze
            event_context: Event context
            
        Returns:
            List of venue Resource objects
        """
        resources = []
        selected_combination = event_context.get('selected_combination', {})
        
        task_name_lower = task.task_name.lower()
        task_desc_lower = task.task_description.lower()
        
        # Check if task requires venue
        venue_keywords = ['venue', 'location', 'space', 'setup', 'hall', 'room']
        
        if any(keyword in task_name_lower or keyword in task_desc_lower 
               for keyword in venue_keywords):
            venue = selected_combination.get('venue')
            if venue:
                resources.append(Resource(
                    resource_type=self.RESOURCE_VENUE,
                    resource_id=str(venue.get('id', 'unknown')),
                    resource_name=venue.get('name', 'Unknown Venue'),
                    quantity_required=1,
                    availability_constraint=None
                ))
        
        return resources
    
    def _detect_resource_conflicts(
        self,
        task: GranularTask,
        resources: List[Resource],
        all_tasks: List[GranularTask]
    ) -> List[str]:
        """
        Identify potential resource conflicts.
        
        Conflicts occur when:
        - Multiple tasks require the same limited resource
        - Resource availability constraints are violated
        - Vendor capacity is exceeded
        
        Args:
            task: Current task
            resources: Resources required by current task
            all_tasks: All tasks (for checking resource usage)
            
        Returns:
            List of conflict descriptions
        """
        conflicts = []
        
        # Check for vendor conflicts (same vendor used by multiple tasks)
        vendor_resources = [r for r in resources if r.resource_type == self.RESOURCE_VENDOR]
        
        for vendor_resource in vendor_resources:
            # Count how many tasks might use this vendor
            # (This is a simplified check; full implementation would need timing info)
            conflict_msg = f"Vendor '{vendor_resource.resource_name}' may be required by multiple tasks simultaneously"
            conflicts.append(conflict_msg)
        
        # Check for equipment conflicts
        equipment_resources = [r for r in resources if r.resource_type == self.RESOURCE_EQUIPMENT]
        
        if len(equipment_resources) > 5:
            conflicts.append(f"Task requires {len(equipment_resources)} pieces of equipment - verify availability")
        
        # Check for personnel conflicts
        personnel_resources = [r for r in resources if r.resource_type == self.RESOURCE_PERSONNEL]
        total_personnel = sum(r.quantity_required for r in personnel_resources)
        
        if total_personnel > 10:
            conflicts.append(f"Task requires {total_personnel} personnel - verify staffing capacity")
        
        return conflicts
    
    def _create_default_task_with_dependencies(
        self,
        task: GranularTask,
        error_message: str
    ) -> TaskWithDependencies:
        """
        Create a default TaskWithDependencies when analysis fails.
        
        Args:
            task: Original granular task
            error_message: Error that occurred
            
        Returns:
            TaskWithDependencies with default values
        """
        return TaskWithDependencies(
            task_id=task.task_id,
            task_name=task.task_name,
            dependencies=[],
            resources_required=[Resource(
                resource_type="unknown",
                resource_id="unknown",
                resource_name=f"Error during analysis: {error_message}",
                quantity_required=0,
                availability_constraint="Requires manual analysis"
            )],
            resource_conflicts=[f"Analysis failed: {error_message}"]
        )
