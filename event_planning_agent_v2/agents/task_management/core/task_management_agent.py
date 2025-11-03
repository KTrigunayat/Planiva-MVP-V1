"""
Task Management Agent Core Orchestrator

Main orchestration component that coordinates sub-agents and tools to generate
a comprehensive extended task list. This agent:

1. Invokes three sub-agents (Prioritization, Granularity, Resource & Dependency)
2. Consolidates sub-agent outputs using DataConsolidator
3. Processes consolidated data through six tools sequentially:
   - Timeline Calculation Tool
   - API/LLM Tool
   - Vendor Task Tool
   - Logistics Check Tool
   - Conflict Check Tool
   - Venue Lookup Tool
4. Generates final ExtendedTaskList from all outputs
5. Updates EventPlanningState with extended_task_list

Integrates with:
- StateManager for state persistence
- Ollama LLM infrastructure
- Existing database connections
- Error handling infrastructure
"""

import logging
import time
from typing import Dict, Any, Optional, List
from datetime import datetime

# Import structured logging
from ....observability.logging import get_logger, correlation_context

from ..sub_agents.prioritization_agent import PrioritizationAgentCore
from ..sub_agents.granularity_agent import GranularityAgentCore
from ..sub_agents.resource_dependency_agent import ResourceDependencyAgentCore
from ..tools.timeline_calculation_tool import TimelineCalculationTool
from ..tools.api_llm_tool import APILLMTool
from ..tools.vendor_task_tool import VendorTaskTool
from ..tools.logistics_check_tool import LogisticsCheckTool
from ..tools.conflict_check_tool import ConflictCheckTool
from ..tools.venue_lookup_tool import VenueLookupTool
from .data_consolidator import DataConsolidator
from ..models.extended_models import ExtendedTask, ExtendedTaskList, ProcessingSummary
from ..models.consolidated_models import ConsolidatedTaskData
from ..exceptions import TaskManagementError, SubAgentDataError, ToolExecutionError
from ....workflows.state_models import EventPlanningState, WorkflowStatus
from ....database.state_manager import WorkflowStateManager
from ....llm.optimized_manager import get_llm_manager
from ....config.settings import get_settings
from .error_handler import (
    TaskManagementErrorHandler,
    process_with_error_handling
)
from ....config.task_management_config import (
    TASK_MANAGEMENT_CONFIG,
    get_config,
    load_config_from_env
)

# Initialize structured logger for task management
logger = get_logger(__name__, component="task_management")


class TaskManagementAgent:
    """
    Main orchestrator for Task Management Agent.
    
    Coordinates sub-agents and tools to generate comprehensive extended task list
    with priorities, granularity, dependencies, timelines, vendor assignments,
    logistics verification, and conflict detection.
    """
    
    def __init__(
        self,
        state_manager: Optional[WorkflowStateManager] = None,
        llm_model: Optional[str] = None,
        db_connection=None,
        config: Optional[Dict[str, Any]] = None
    ):
        """
        Initialize Task Management Agent with all sub-agents and tools.
        
        Args:
            state_manager: Optional StateManager instance (creates new if None)
            llm_model: Optional LLM model name (uses settings default if None)
            db_connection: Optional database connection (uses default if None)
            config: Optional configuration dictionary (uses default if None)
        """
        # Load configuration
        if config:
            from ....config.task_management_config import TaskManagementConfig
            self.config = TaskManagementConfig.from_dict(config)
        else:
            self.config = load_config_from_env()
        
        # Configure logging level based on config
        if self.config.enable_debug_logging:
            logger.logger.setLevel(logging.DEBUG)
        else:
            logger.logger.setLevel(getattr(logging, self.config.log_level))
        
        logger.info(
            "Initializing Task Management Agent",
            operation="init",
            metadata={
                "llm_model": llm_model,
                "config": self.config.to_dict()
            }
        )
        
        self.settings = get_settings()
        self.state_manager = state_manager or WorkflowStateManager()
        self.llm_model = llm_model or self.config.llm_model or self.settings.llm.gemma_model
        self.db_connection = db_connection
        
        # Initialize sub-agents
        logger.info(
            "Initializing Task Management Agent sub-agents",
            operation="init_sub_agents",
            metadata={
                "enable_prioritization": self.config.enable_prioritization_agent,
                "enable_granularity": self.config.enable_granularity_agent,
                "enable_resource_dependency": self.config.enable_resource_dependency_agent
            }
        )
        
        self.prioritization_agent = PrioritizationAgentCore(llm_model=self.llm_model)
        self.granularity_agent = GranularityAgentCore(llm_model=self.llm_model)
        self.resource_dependency_agent = ResourceDependencyAgentCore(llm_model=self.llm_model)
        
        # Initialize data consolidator
        self.data_consolidator = DataConsolidator()
        
        # Initialize tools
        logger.info(
            "Initializing Task Management Agent tools",
            operation="init_tools",
            metadata={
                "enable_timeline": self.config.enable_timeline_calculation,
                "enable_llm": self.config.enable_llm_enhancement,
                "enable_vendor": self.config.enable_vendor_assignment,
                "enable_logistics": self.config.enable_logistics_check,
                "enable_conflict": self.config.enable_conflict_detection,
                "enable_venue": self.config.enable_venue_lookup
            }
        )
        
        self.timeline_tool = TimelineCalculationTool()
        self.llm_tool = APILLMTool(llm_model=self.llm_model)
        self.vendor_tool = VendorTaskTool(db_connection=self.db_connection)
        self.logistics_tool = LogisticsCheckTool(db_connection=self.db_connection)
        self.conflict_tool = ConflictCheckTool()
        self.venue_tool = VenueLookupTool(db_connection=self.db_connection)
        
        # Processing metrics
        self.tool_execution_status: Dict[str, str] = {}
        
        # Initialize error handler
        self.error_handler = TaskManagementErrorHandler()
        
        logger.info(
            "Task Management Agent initialized successfully",
            operation="init_complete",
            metadata={
                "llm_model": self.llm_model,
                "parallel_execution": self.config.parallel_tool_execution
            }
        )
    
    async def process_with_error_handling(self, state: EventPlanningState) -> EventPlanningState:
        """
        Main orchestration entry point with comprehensive error handling.
        
        This is the primary method that should be called by the workflow.
        It wraps the core process() method with error handling, recovery,
        and state management.
        
        Args:
            state: Current EventPlanningState from workflow
            
        Returns:
            Updated EventPlanningState with extended_task_list field populated
            or error information if processing failed
        """
        # Reset error tracking for new processing run
        self.error_handler.reset_error_tracking()
        
        try:
            # Call core process method
            return await self.process(state)
            
        except SubAgentDataError as e:
            # Handle sub-agent errors - continue with partial data
            logger.warning(f"Sub-agent error: {str(e)}")
            should_continue, partial_data = self.error_handler.handle_sub_agent_error(
                error=e,
                sub_agent_name=e.sub_agent_name,
                state=state,
                partial_data=None
            )
            
            if should_continue:
                # Return state with error logged but not failed
                return state
            else:
                # Critical failure
                return self.error_handler.handle_critical_error(e, state, "sub_agent_processing")
        
        except ToolExecutionError as e:
            # Handle tool execution errors - mark affected tasks
            logger.error(f"Tool execution error: {str(e)}")
            should_continue, error_metadata = self.error_handler.handle_tool_error(
                error=e,
                tool_name=e.tool_name,
                state=state,
                affected_tasks=e.details.get('affected_tasks')
            )
            
            if should_continue:
                # Return state with error logged but not failed
                return state
            else:
                # Critical failure
                return self.error_handler.handle_critical_error(e, state, "tool_execution")
        
        except TaskManagementError as e:
            # Handle generic task management errors as critical
            logger.error(f"Task management error: {str(e)}")
            return self.error_handler.handle_critical_error(e, state, "task_management")
        
        except Exception as e:
            # Handle unexpected errors as critical
            logger.critical(f"Unexpected error: {str(e)}")
            return self.error_handler.handle_critical_error(e, state, "unexpected_error")
    
    async def process(self, state: EventPlanningState) -> EventPlanningState:
        """
        Core orchestration method for task management processing.
        
        This method:
        1. Invokes all three sub-agents to collect task data
        2. Consolidates sub-agent outputs
        3. Processes consolidated data through all six tools sequentially
        4. Generates final ExtendedTaskList
        5. Updates EventPlanningState with extended_task_list
        
        State is updated and persisted after each major processing step:
        - After sub-agent consolidation
        - After tool processing
        - After extended task list generation
        
        This enables state restoration for resuming after interruptions.
        
        Note: This method should typically be called via process_with_error_handling()
        which provides comprehensive error handling and recovery.
        
        Args:
            state: Current EventPlanningState from workflow
            
        Returns:
            Updated EventPlanningState with extended_task_list field populated
            
        Raises:
            TaskManagementError: If critical processing failures occur
        """
        start_time = time.time()
        
        logger.info(
            "=" * 80 + "\nStarting Task Management Agent processing\n" + "=" * 80,
            operation="process_start",
            metadata={
                "plan_id": state.get('plan_id', 'unknown'),
                "workflow_status": state.get('workflow_status'),
                "config": self.config.to_dict()
            }
        )
        
        try:
            # Step 1: Invoke sub-agents and collect outputs
            logger.info("\n[STEP 1] Invoking sub-agents...")
            sub_agent_outputs = await self._invoke_sub_agents(state)
            
            # Step 2: Consolidate sub-agent data
            logger.info("\n[STEP 2] Consolidating sub-agent data...")
            consolidated_data = self._consolidate_data(
                sub_agent_outputs['prioritized_tasks'],
                sub_agent_outputs['granular_tasks'],
                sub_agent_outputs['dependency_tasks'],
                state
            )
            
            # Update state after sub-agent consolidation
            state = self._update_state_after_consolidation(state, consolidated_data)
            
            # Step 3: Process through tools sequentially
            logger.info("\n[STEP 3] Processing through tools...")
            tool_outputs = await self._process_tools(consolidated_data, state)
            
            # Update state after tool processing
            state = self._update_state_after_tools(state, tool_outputs)
            
            # Step 4: Generate extended task list
            logger.info("\n[STEP 4] Generating extended task list...")
            extended_task_list = self._generate_extended_task_list(
                consolidated_data,
                tool_outputs,
                start_time
            )
            
            # Step 5: Update state with final extended task list
            logger.info("\n[STEP 5] Updating EventPlanningState...")
            updated_state = self._update_state(state, extended_task_list)
            
            processing_time = time.time() - start_time
            
            # Log performance metrics
            logger.log_performance(
                operation="task_management_processing",
                duration_ms=processing_time * 1000,
                success=True,
                metadata={
                    "total_tasks": extended_task_list.processing_summary.total_tasks,
                    "tasks_with_errors": extended_task_list.processing_summary.tasks_with_errors,
                    "tasks_with_warnings": extended_task_list.processing_summary.tasks_with_warnings,
                    "tasks_requiring_review": extended_task_list.processing_summary.tasks_requiring_review,
                    "tool_execution_status": self.tool_execution_status
                }
            )
            
            logger.info(
                "=" * 80 + f"\nTask Management Agent processing completed in {processing_time:.2f}s\n" +
                f"Total tasks: {extended_task_list.processing_summary.total_tasks}\n" +
                f"Tasks with errors: {extended_task_list.processing_summary.tasks_with_errors}\n" +
                f"Tasks with warnings: {extended_task_list.processing_summary.tasks_with_warnings}\n" +
                f"Tasks requiring review: {extended_task_list.processing_summary.tasks_requiring_review}\n" +
                "=" * 80,
                operation="process_complete",
                metadata={
                    "processing_time_seconds": processing_time,
                    "summary": extended_task_list.processing_summary.__dict__
                }
            )
            
            return updated_state
            
        except Exception as e:
            processing_time = time.time() - start_time
            
            logger.error(
                f"Critical error in Task Management Agent: {e}",
                operation="process_error",
                exception=e,
                metadata={
                    "processing_time_seconds": processing_time,
                    "plan_id": state.get('plan_id', 'unknown'),
                    "tool_execution_status": self.tool_execution_status
                }
            )
            
            # Update state with error information
            state['error_count'] = state.get('error_count', 0) + 1
            state['last_error'] = f"Task Management Agent error: {str(e)}"
            state['workflow_status'] = WorkflowStatus.FAILED.value
            
            # Persist error state for recovery
            try:
                self.state_manager.save_workflow_state(state)
            except Exception as persist_error:
                logger.error(
                    f"Failed to persist error state: {persist_error}",
                    operation="persist_error_state",
                    exception=persist_error
                )
            
            raise TaskManagementError(f"Task Management Agent processing failed: {e}") from e
    
    async def _invoke_sub_agents(self, state: EventPlanningState) -> Dict[str, List]:
        """
        Invoke all three sub-agents and collect their outputs.
        
        Uses error handler to gracefully handle sub-agent failures and
        continue with partial data when possible.
        
        Args:
            state: Current EventPlanningState
            
        Returns:
            Dictionary with keys: prioritized_tasks, granular_tasks, dependency_tasks
            
        Raises:
            SubAgentDataError: If all sub-agents fail and no data is available
        """
        logger.info(
            "Invoking sub-agents",
            operation="invoke_sub_agents",
            metadata={
                "enabled_agents": {
                    "prioritization": self.config.enable_prioritization_agent,
                    "granularity": self.config.enable_granularity_agent,
                    "resource_dependency": self.config.enable_resource_dependency_agent
                }
            }
        )
        
        sub_agent_outputs = {
            'prioritized_tasks': [],
            'granular_tasks': [],
            'dependency_tasks': []
        }
        
        # Invoke Prioritization Agent
        if self.config.enable_prioritization_agent:
            logger.debug("Invoking Prioritization Agent", operation="invoke_prioritization_agent")
            start_time = time.time()
            try:
                prioritized_tasks = await self.prioritization_agent.prioritize_tasks(state)
                sub_agent_outputs['prioritized_tasks'] = prioritized_tasks
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_agent_interaction(
                    agent_name="PrioritizationAgent",
                    action="prioritize_tasks",
                    duration_ms=duration_ms,
                    success=True,
                    output_data={"task_count": len(prioritized_tasks)},
                    metadata={"plan_id": state.get('plan_id', 'unknown')}
                )
                
                if self.config.log_sub_agent_outputs:
                    logger.debug(
                        f"Prioritization Agent output: {len(prioritized_tasks)} tasks",
                        operation="prioritization_output",
                        metadata={"tasks": [t.__dict__ if hasattr(t, '__dict__') else str(t) for t in prioritized_tasks[:5]]}
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_agent_interaction(
                    agent_name="PrioritizationAgent",
                    action="prioritize_tasks",
                    duration_ms=duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                # Use error handler to log and continue
                should_continue, partial_data = self.error_handler.handle_sub_agent_error(
                    error=e,
                    sub_agent_name="PrioritizationAgent",
                    state=state,
                    partial_data=None
                )
                if partial_data:
                    sub_agent_outputs['prioritized_tasks'] = partial_data
        
        # Invoke Granularity Agent
        if self.config.enable_granularity_agent:
            logger.debug("Invoking Granularity Agent", operation="invoke_granularity_agent")
            start_time = time.time()
            try:
                granular_tasks = await self.granularity_agent.decompose_tasks(
                    sub_agent_outputs['prioritized_tasks'],
                    state
                )
                sub_agent_outputs['granular_tasks'] = granular_tasks
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_agent_interaction(
                    agent_name="GranularityAgent",
                    action="decompose_tasks",
                    duration_ms=duration_ms,
                    success=True,
                    output_data={"task_count": len(granular_tasks)},
                    metadata={"plan_id": state.get('plan_id', 'unknown')}
                )
                
                if self.config.log_sub_agent_outputs:
                    logger.debug(
                        f"Granularity Agent output: {len(granular_tasks)} tasks",
                        operation="granularity_output",
                        metadata={"tasks": [t.__dict__ if hasattr(t, '__dict__') else str(t) for t in granular_tasks[:5]]}
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_agent_interaction(
                    agent_name="GranularityAgent",
                    action="decompose_tasks",
                    duration_ms=duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                # Use error handler to log and continue
                should_continue, partial_data = self.error_handler.handle_sub_agent_error(
                    error=e,
                    sub_agent_name="GranularityAgent",
                    state=state,
                    partial_data=None
                )
                if partial_data:
                    sub_agent_outputs['granular_tasks'] = partial_data
        
        # Invoke Resource & Dependency Agent
        if self.config.enable_resource_dependency_agent:
            logger.debug("Invoking Resource & Dependency Agent", operation="invoke_resource_dependency_agent")
            start_time = time.time()
            try:
                dependency_tasks = await self.resource_dependency_agent.analyze_dependencies(
                    sub_agent_outputs['granular_tasks'],
                    state
                )
                sub_agent_outputs['dependency_tasks'] = dependency_tasks
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_agent_interaction(
                    agent_name="ResourceDependencyAgent",
                    action="analyze_dependencies",
                    duration_ms=duration_ms,
                    success=True,
                    output_data={"task_count": len(dependency_tasks)},
                    metadata={"plan_id": state.get('plan_id', 'unknown')}
                )
                
                if self.config.log_sub_agent_outputs:
                    logger.debug(
                        f"Resource & Dependency Agent output: {len(dependency_tasks)} tasks",
                        operation="resource_dependency_output",
                        metadata={"tasks": [t.__dict__ if hasattr(t, '__dict__') else str(t) for t in dependency_tasks[:5]]}
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_agent_interaction(
                    agent_name="ResourceDependencyAgent",
                    action="analyze_dependencies",
                    duration_ms=duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                # Use error handler to log and continue
                should_continue, partial_data = self.error_handler.handle_sub_agent_error(
                    error=e,
                    sub_agent_name="ResourceDependencyAgent",
                    state=state,
                    partial_data=None
                )
                if partial_data:
                    sub_agent_outputs['dependency_tasks'] = partial_data
        
        # Check if we have any data at all
        total_tasks = sum(len(tasks) for tasks in sub_agent_outputs.values())
        if total_tasks == 0:
            error = SubAgentDataError(
                sub_agent_name="all",
                message="All sub-agents returned empty data",
                details={'sub_agent_outputs': sub_agent_outputs}
            )
            raise error
        
        return sub_agent_outputs
    
    def _consolidate_data(
        self,
        prioritized_tasks: List,
        granular_tasks: List,
        dependency_tasks: List,
        state: EventPlanningState
    ) -> ConsolidatedTaskData:
        """
        Consolidate sub-agent outputs using DataConsolidator.
        
        Args:
            prioritized_tasks: Output from Prioritization Agent
            granular_tasks: Output from Granularity Agent
            dependency_tasks: Output from Resource & Dependency Agent
            state: Current EventPlanningState for event context
            
        Returns:
            ConsolidatedTaskData with merged task information
            
        Raises:
            TaskManagementError: If consolidation fails critically
        """
        logger.info(
            "Consolidating data from sub-agents",
            operation="consolidate_data",
            metadata={
                "prioritized_count": len(prioritized_tasks),
                "granular_count": len(granular_tasks),
                "dependency_count": len(dependency_tasks)
            }
        )
        
        start_time = time.time()
        
        try:
            # Extract event context from state
            event_context = {
                'client_request': state.get('client_request', {}),
                'timeline_data': state.get('timeline_data', {}),
                'selected_combination': state.get('selected_combination', {}),
                'plan_id': state.get('plan_id', 'unknown')
            }
            
            # Consolidate using DataConsolidator
            consolidated_data = self.data_consolidator.consolidate_sub_agent_data(
                prioritized_tasks=prioritized_tasks,
                granular_tasks=granular_tasks,
                dependency_tasks=dependency_tasks,
                event_context=event_context
            )
            
            duration_ms = (time.time() - start_time) * 1000
            
            logger.log_performance(
                operation="data_consolidation",
                duration_ms=duration_ms,
                success=True,
                metadata={
                    "consolidated_task_count": len(consolidated_data.tasks),
                    "error_count": len(self.data_consolidator.consolidation_errors),
                    "warning_count": len(self.data_consolidator.warnings)
                }
            )
            
            # Log any consolidation errors or warnings
            if self.data_consolidator.consolidation_errors:
                logger.warning(
                    f"Data consolidation completed with {len(self.data_consolidator.consolidation_errors)} errors",
                    operation="consolidation_errors",
                    metadata={"errors": self.data_consolidator.consolidation_errors[:10]}
                )
            if self.data_consolidator.warnings:
                logger.warning(
                    f"Data consolidation completed with {len(self.data_consolidator.warnings)} warnings",
                    operation="consolidation_warnings",
                    metadata={"warnings": self.data_consolidator.warnings[:10]}
                )
            
            return consolidated_data
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            
            logger.error(
                f"Data consolidation failed: {e}",
                operation="consolidate_data_error",
                exception=e,
                metadata={"duration_ms": duration_ms}
            )
            
            raise TaskManagementError(f"Failed to consolidate sub-agent data: {e}") from e
    
    async def _process_tools(
        self,
        consolidated_data: ConsolidatedTaskData,
        state: EventPlanningState
    ) -> Dict[str, Any]:
        """
        Process consolidated data through all six tools sequentially.
        
        Tools are invoked in order:
        1. Timeline Calculation Tool
        2. API/LLM Tool
        3. Vendor Task Tool
        4. Logistics Check Tool
        5. Conflict Check Tool
        6. Venue Lookup Tool
        
        Args:
            consolidated_data: Consolidated task data from sub-agents
            state: Current EventPlanningState
            
        Returns:
            Dictionary with tool outputs keyed by tool name
        """
        logger.info("Processing through tools sequentially...")
        
        tool_outputs = {
            'timelines': [],
            'llm_enhancements': [],
            'vendor_assignments': [],
            'logistics_statuses': [],
            'conflicts': [],
            'venue_info': []
        }
        
        # Reset tool execution status
        self.tool_execution_status = {}
        
        # Tool 1: Timeline Calculation
        if self.config.enable_timeline_calculation:
            logger.debug("Executing Timeline Calculation Tool", operation="tool_timeline_calculation")
            start_time = time.time()
            try:
                timelines = self.timeline_tool.calculate_timelines(consolidated_data, state)
                tool_outputs['timelines'] = timelines
                self.tool_execution_status['timeline_calculation'] = 'success'
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_performance(
                    operation="timeline_calculation_tool",
                    duration_ms=duration_ms,
                    success=True,
                    metadata={"timeline_count": len(timelines)}
                )
                
                if self.config.log_tool_results:
                    logger.debug(
                        f"Timeline Calculation Tool results: {len(timelines)} timelines",
                        operation="timeline_results",
                        metadata={"timelines": [t.__dict__ if hasattr(t, '__dict__') else str(t) for t in timelines[:5]]}
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.tool_execution_status['timeline_calculation'] = f'failed: {str(e)}'
                
                logger.log_performance(
                    operation="timeline_calculation_tool",
                    duration_ms=duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                # Use error handler to log and continue
                should_continue, error_metadata = self.error_handler.handle_tool_error(
                    error=e,
                    tool_name="TimelineCalculationTool",
                    state=state,
                    affected_tasks=[task.task_id for task in consolidated_data.tasks]
                )
        
        # Tool 2: API/LLM Enhancement
        if self.config.enable_llm_enhancement:
            logger.debug("Executing API/LLM Tool", operation="tool_llm_enhancement")
            start_time = time.time()
            try:
                llm_enhancements = await self.llm_tool.enhance_tasks(
                    consolidated_data,
                    event_context=state.get('client_request', {})
                )
                tool_outputs['llm_enhancements'] = llm_enhancements
                self.tool_execution_status['llm_enhancement'] = 'success'
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_performance(
                    operation="llm_enhancement_tool",
                    duration_ms=duration_ms,
                    success=True,
                    metadata={"enhancement_count": len(llm_enhancements)}
                )
                
                if self.config.log_tool_results:
                    logger.debug(
                        f"API/LLM Tool results: {len(llm_enhancements)} enhancements",
                        operation="llm_results",
                        metadata={"enhancements": [e.__dict__ if hasattr(e, '__dict__') else str(e) for e in llm_enhancements[:5]]}
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.tool_execution_status['llm_enhancement'] = f'failed: {str(e)}'
                
                logger.log_performance(
                    operation="llm_enhancement_tool",
                    duration_ms=duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                # Use error handler to log and continue
                should_continue, error_metadata = self.error_handler.handle_tool_error(
                    error=e,
                    tool_name="APILLMTool",
                    state=state,
                    affected_tasks=[task.task_id for task in consolidated_data.tasks]
                )
        
        # Tool 3: Vendor Task Assignment
        if self.config.enable_vendor_assignment:
            logger.debug("Executing Vendor Task Tool", operation="tool_vendor_assignment")
            start_time = time.time()
            try:
                vendor_assignments = self.vendor_tool.assign_vendors(consolidated_data, state)
                tool_outputs['vendor_assignments'] = vendor_assignments
                self.tool_execution_status['vendor_assignment'] = 'success'
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_performance(
                    operation="vendor_assignment_tool",
                    duration_ms=duration_ms,
                    success=True,
                    metadata={"assignment_count": len(vendor_assignments)}
                )
                
                if self.config.log_tool_results:
                    logger.debug(
                        f"Vendor Task Tool results: {len(vendor_assignments)} assignments",
                        operation="vendor_results"
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.tool_execution_status['vendor_assignment'] = f'failed: {str(e)}'
                
                logger.log_performance(
                    operation="vendor_assignment_tool",
                    duration_ms=duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                should_continue, error_metadata = self.error_handler.handle_tool_error(
                    error=e,
                    tool_name="VendorTaskTool",
                    state=state,
                    affected_tasks=[task.task_id for task in consolidated_data.tasks]
                )
        
        # Tool 4: Logistics Check
        if self.config.enable_logistics_check:
            logger.debug("Executing Logistics Check Tool", operation="tool_logistics_check")
            start_time = time.time()
            try:
                logistics_statuses = self.logistics_tool.verify_logistics(consolidated_data, state)
                tool_outputs['logistics_statuses'] = logistics_statuses
                self.tool_execution_status['logistics_check'] = 'success'
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_performance(
                    operation="logistics_check_tool",
                    duration_ms=duration_ms,
                    success=True,
                    metadata={"status_count": len(logistics_statuses)}
                )
                
                if self.config.log_tool_results:
                    logger.debug(
                        f"Logistics Check Tool results: {len(logistics_statuses)} statuses",
                        operation="logistics_results"
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.tool_execution_status['logistics_check'] = f'failed: {str(e)}'
                
                logger.log_performance(
                    operation="logistics_check_tool",
                    duration_ms=duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                should_continue, error_metadata = self.error_handler.handle_tool_error(
                    error=e,
                    tool_name="LogisticsCheckTool",
                    state=state,
                    affected_tasks=[task.task_id for task in consolidated_data.tasks]
                )
        
        # Tool 5: Conflict Check
        if self.config.enable_conflict_detection:
            logger.debug("Executing Conflict Check Tool", operation="tool_conflict_check")
            start_time = time.time()
            try:
                conflicts = self.conflict_tool.check_conflicts(consolidated_data, state)
                tool_outputs['conflicts'] = conflicts
                self.tool_execution_status['conflict_check'] = 'success'
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_performance(
                    operation="conflict_check_tool",
                    duration_ms=duration_ms,
                    success=True,
                    metadata={"conflict_count": len(conflicts)}
                )
                
                if self.config.log_tool_results:
                    logger.debug(
                        f"Conflict Check Tool results: {len(conflicts)} conflicts",
                        operation="conflict_results"
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.tool_execution_status['conflict_check'] = f'failed: {str(e)}'
                
                logger.log_performance(
                    operation="conflict_check_tool",
                    duration_ms=duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                should_continue, error_metadata = self.error_handler.handle_tool_error(
                    error=e,
                    tool_name="ConflictCheckTool",
                    state=state,
                    affected_tasks=[task.task_id for task in consolidated_data.tasks]
                )
        
        # Tool 6: Venue Lookup
        if self.config.enable_venue_lookup:
            logger.debug("Executing Venue Lookup Tool", operation="tool_venue_lookup")
            start_time = time.time()
            try:
                venue_info = self.venue_tool.lookup_venues(consolidated_data, state)
                tool_outputs['venue_info'] = venue_info
                self.tool_execution_status['venue_lookup'] = 'success'
                duration_ms = (time.time() - start_time) * 1000
                
                logger.log_performance(
                    operation="venue_lookup_tool",
                    duration_ms=duration_ms,
                    success=True,
                    metadata={"venue_count": len(venue_info)}
                )
                
                if self.config.log_tool_results:
                    logger.debug(
                        f"Venue Lookup Tool results: {len(venue_info)} venues",
                        operation="venue_results"
                    )
            except Exception as e:
                duration_ms = (time.time() - start_time) * 1000
                self.tool_execution_status['venue_lookup'] = f'failed: {str(e)}'
                
                logger.log_performance(
                    operation="venue_lookup_tool",
                    duration_ms=duration_ms,
                    success=False,
                    metadata={"error": str(e)}
                )
                
                should_continue, error_metadata = self.error_handler.handle_tool_error(
                    error=e,
                    tool_name="VenueLookupTool",
                    state=state,
                    affected_tasks=[task.task_id for task in consolidated_data.tasks]
                )
        
        logger.info("  Tool processing completed")
        return tool_outputs
    
    def _generate_extended_task_list(
        self,
        consolidated_data: ConsolidatedTaskData,
        tool_outputs: Dict[str, Any],
        start_time: float
    ) -> ExtendedTaskList:
        """
        Generate final ExtendedTaskList from consolidated data and tool outputs.
        
        Args:
            consolidated_data: Consolidated task data from sub-agents
            tool_outputs: Outputs from all tools
            start_time: Processing start time for duration calculation
            
        Returns:
            ExtendedTaskList with all task data and processing summary
        """
        logger.info("Generating extended task list...")
        
        # Create lookup maps for tool outputs by task_id
        timeline_map = {t.task_id: t for t in tool_outputs.get('timelines', [])}
        llm_map = {e.task_id: e for e in tool_outputs.get('llm_enhancements', [])}
        vendor_map = {}
        for va in tool_outputs.get('vendor_assignments', []):
            if va.task_id not in vendor_map:
                vendor_map[va.task_id] = []
            vendor_map[va.task_id].append(va)
        logistics_map = {ls.task_id: ls for ls in tool_outputs.get('logistics_statuses', [])}
        venue_map = {vi.task_id: vi for vi in tool_outputs.get('venue_info', [])}
        
        # Group conflicts by affected tasks
        conflict_map = {}
        for conflict in tool_outputs.get('conflicts', []):
            for task_id in conflict.affected_tasks:
                if task_id not in conflict_map:
                    conflict_map[task_id] = []
                conflict_map[task_id].append(conflict)
        
        # Generate ExtendedTask for each consolidated task
        extended_tasks = []
        tasks_with_errors = 0
        tasks_with_warnings = 0
        tasks_requiring_review = 0
        
        for task in consolidated_data.tasks:
            # Get tool enhancements for this task
            timeline = timeline_map.get(task.task_id)
            llm_enhancement = llm_map.get(task.task_id)
            vendor_assignments = vendor_map.get(task.task_id, [])
            logistics_status = logistics_map.get(task.task_id)
            task_conflicts = conflict_map.get(task.task_id, [])
            venue_info = venue_map.get(task.task_id)
            
            # Build LLM enhancements dict
            llm_enhancements = {}
            if llm_enhancement:
                llm_enhancements = {
                    'enhanced_description': llm_enhancement.enhanced_description,
                    'suggestions': llm_enhancement.suggestions,
                    'potential_issues': llm_enhancement.potential_issues,
                    'best_practices': llm_enhancement.best_practices
                }
            
            # Determine status flags
            has_errors = False
            has_warnings = False
            requires_manual_review = False
            error_messages = []
            warning_messages = []
            
            # Check for missing critical data
            if not timeline:
                has_warnings = True
                warning_messages.append("Timeline not calculated")
            
            if not vendor_assignments:
                has_warnings = True
                warning_messages.append("No vendors assigned")
            
            if llm_enhancement and llm_enhancement.requires_manual_review:
                requires_manual_review = True
                warning_messages.append("Flagged for manual review by LLM")
            
            if logistics_status and logistics_status.overall_feasibility == 'not_feasible':
                has_errors = True
                error_messages.append("Logistics not feasible")
            
            if task_conflicts:
                critical_conflicts = [c for c in task_conflicts if c.severity in ['critical', 'high']]
                if critical_conflicts:
                    has_errors = True
                    error_messages.append(f"{len(critical_conflicts)} critical/high conflicts detected")
                else:
                    has_warnings = True
                    warning_messages.append(f"{len(task_conflicts)} conflicts detected")
            
            # Create ExtendedTask
            extended_task = ExtendedTask(
                task_id=task.task_id,
                task_name=task.task_name,
                task_description=task.task_description,
                priority_level=task.priority_level,
                priority_score=task.priority_score,
                granularity_level=task.granularity_level,
                parent_task_id=task.parent_task_id,
                sub_tasks=task.sub_tasks,
                dependencies=task.dependencies,
                resources_required=task.resources_required,
                timeline=timeline,
                llm_enhancements=llm_enhancements,
                assigned_vendors=vendor_assignments,
                logistics_status=logistics_status,
                conflicts=task_conflicts,
                venue_info=venue_info,
                has_errors=has_errors,
                has_warnings=has_warnings,
                requires_manual_review=requires_manual_review,
                error_messages=error_messages,
                warning_messages=warning_messages
            )
            
            extended_tasks.append(extended_task)
            
            # Update counters
            if has_errors:
                tasks_with_errors += 1
            if has_warnings:
                tasks_with_warnings += 1
            if requires_manual_review:
                tasks_requiring_review += 1
        
        # Create processing summary
        processing_time = time.time() - start_time
        processing_summary = ProcessingSummary(
            total_tasks=len(extended_tasks),
            tasks_with_errors=tasks_with_errors,
            tasks_with_warnings=tasks_with_warnings,
            tasks_requiring_review=tasks_requiring_review,
            processing_time=processing_time,
            tool_execution_status=self.tool_execution_status.copy()
        )
        
        # Create ExtendedTaskList
        extended_task_list = ExtendedTaskList(
            tasks=extended_tasks,
            processing_summary=processing_summary,
            metadata={
                'generated_at': datetime.utcnow().isoformat(),
                'agent_version': '1.0.0',
                'llm_model': self.llm_model,
                'consolidation_errors': len(self.data_consolidator.consolidation_errors),
                'consolidation_warnings': len(self.data_consolidator.warnings)
            }
        )
        
        logger.info(f"  ✓ Generated extended task list with {len(extended_tasks)} tasks")
        
        return extended_task_list
    
    def _update_state(
        self,
        state: EventPlanningState,
        extended_task_list: ExtendedTaskList
    ) -> EventPlanningState:
        """
        Update EventPlanningState with extended_task_list and persist to database.
        
        This method:
        1. Converts ExtendedTaskList to dict for state storage
        2. Updates the extended_task_list field in EventPlanningState
        3. Updates workflow_status to indicate task management completion
        4. Updates last_updated timestamp
        5. Persists state to database using StateManager
        6. Ensures Blueprint Agent can access extended_task_list
        
        Args:
            state: Current EventPlanningState
            extended_task_list: Generated ExtendedTaskList
            
        Returns:
            Updated EventPlanningState with extended_task_list and persisted to database
        """
        logger.info("Updating EventPlanningState with extended_task_list...")
        
        # Convert ExtendedTaskList to dict for state storage
        extended_task_list_dict = self._serialize_extended_task_list(extended_task_list)
        
        # Update state with extended task list
        state['extended_task_list'] = extended_task_list_dict
        state['last_updated'] = datetime.utcnow().isoformat()
        
        # Update workflow status to indicate task management completion
        # This allows Blueprint Agent to know task management has completed
        state['workflow_status'] = WorkflowStatus.RUNNING.value
        
        # Persist state to database using StateManager
        try:
            logger.info("  → Persisting state to database...")
            persistence_success = self.state_manager.save_workflow_state(state)
            
            if persistence_success:
                logger.info("  ✓ State persisted successfully to database")
            else:
                logger.warning("  ⚠ State persistence returned False - state may not be saved")
                # Don't fail processing, just log warning
                state['error_count'] = state.get('error_count', 0) + 1
                state['last_error'] = "State persistence warning: save_workflow_state returned False"
        
        except Exception as e:
            logger.error(f"  ✗ Failed to persist state to database: {e}")
            # Don't fail processing, just log error
            state['error_count'] = state.get('error_count', 0) + 1
            state['last_error'] = f"State persistence error: {str(e)}"
        
        logger.info("  ✓ State updated successfully")
        
        return state
    
    def _update_state_after_consolidation(
        self,
        state: EventPlanningState,
        consolidated_data: ConsolidatedTaskData
    ) -> EventPlanningState:
        """
        Update state after sub-agent consolidation step.
        
        This checkpoint allows recovery if tool processing fails.
        Stores intermediate processing state for resumption.
        
        Args:
            state: Current EventPlanningState
            consolidated_data: Consolidated data from sub-agents
            
        Returns:
            Updated EventPlanningState with consolidation checkpoint
        """
        logger.info("  → Creating checkpoint after sub-agent consolidation...")
        
        # Store consolidation metadata in state for recovery
        if 'task_management_checkpoints' not in state:
            state['task_management_checkpoints'] = {}
        
        state['task_management_checkpoints']['consolidation'] = {
            'completed': True,
            'timestamp': datetime.utcnow().isoformat(),
            'task_count': len(consolidated_data.tasks),
            'consolidation_errors': len(self.data_consolidator.consolidation_errors),
            'consolidation_warnings': len(self.data_consolidator.warnings)
        }
        
        state['last_updated'] = datetime.utcnow().isoformat()
        
        # Checkpoint state to database
        try:
            self.state_manager.checkpoint_workflow(state)
            logger.info("  ✓ Consolidation checkpoint saved")
        except Exception as e:
            logger.warning(f"  ⚠ Failed to save consolidation checkpoint: {e}")
        
        return state
    
    def _update_state_after_tools(
        self,
        state: EventPlanningState,
        tool_outputs: Dict[str, Any]
    ) -> EventPlanningState:
        """
        Update state after tool processing step.
        
        This checkpoint allows recovery if extended task list generation fails.
        Stores tool execution status for resumption.
        
        Args:
            state: Current EventPlanningState
            tool_outputs: Outputs from all tools
            
        Returns:
            Updated EventPlanningState with tool processing checkpoint
        """
        logger.info("  → Creating checkpoint after tool processing...")
        
        # Store tool processing metadata in state for recovery
        if 'task_management_checkpoints' not in state:
            state['task_management_checkpoints'] = {}
        
        state['task_management_checkpoints']['tool_processing'] = {
            'completed': True,
            'timestamp': datetime.utcnow().isoformat(),
            'tool_execution_status': self.tool_execution_status.copy(),
            'timelines_count': len(tool_outputs.get('timelines', [])),
            'enhancements_count': len(tool_outputs.get('llm_enhancements', [])),
            'vendor_assignments_count': len(tool_outputs.get('vendor_assignments', [])),
            'logistics_count': len(tool_outputs.get('logistics_statuses', [])),
            'conflicts_count': len(tool_outputs.get('conflicts', [])),
            'venue_info_count': len(tool_outputs.get('venue_info', []))
        }
        
        state['last_updated'] = datetime.utcnow().isoformat()
        
        # Checkpoint state to database
        try:
            self.state_manager.checkpoint_workflow(state)
            logger.info("  ✓ Tool processing checkpoint saved")
        except Exception as e:
            logger.warning(f"  ⚠ Failed to save tool processing checkpoint: {e}")
        
        return state
    
    def restore_from_checkpoint(self, state: EventPlanningState) -> Optional[str]:
        """
        Restore processing from last checkpoint after interruption.
        
        Checks task_management_checkpoints in state to determine where
        processing was interrupted and what step to resume from.
        
        Args:
            state: EventPlanningState to restore from
            
        Returns:
            String indicating which step to resume from:
            - 'consolidation': Resume from tool processing
            - 'tool_processing': Resume from extended task list generation
            - None: Start from beginning
        """
        checkpoints = state.get('task_management_checkpoints', {})
        
        if not checkpoints:
            logger.info("No checkpoints found, starting from beginning")
            return None
        
        # Check if tool processing was completed
        if checkpoints.get('tool_processing', {}).get('completed'):
            logger.info("Tool processing checkpoint found, can resume from extended task list generation")
            return 'tool_processing'
        
        # Check if consolidation was completed
        if checkpoints.get('consolidation', {}).get('completed'):
            logger.info("Consolidation checkpoint found, can resume from tool processing")
            return 'consolidation'
        
        logger.info("No valid checkpoints found, starting from beginning")
        return None
    
    def _serialize_extended_task_list(self, extended_task_list: ExtendedTaskList) -> Dict[str, Any]:
        """
        Serialize ExtendedTaskList to dictionary for state storage.
        
        Args:
            extended_task_list: ExtendedTaskList to serialize
            
        Returns:
            Dictionary representation
        """
        from dataclasses import asdict
        
        # Convert to dict (handles nested dataclasses)
        result = asdict(extended_task_list)
        
        # Convert timedelta objects to strings for JSON serialization
        for task in result['tasks']:
            if task.get('timeline') and task['timeline'].get('duration'):
                duration = task['timeline']['duration']
                if hasattr(duration, 'total_seconds'):
                    task['timeline']['duration'] = duration.total_seconds()
            if task.get('timeline') and task['timeline'].get('buffer_time'):
                buffer = task['timeline']['buffer_time']
                if hasattr(buffer, 'total_seconds'):
                    task['timeline']['buffer_time'] = buffer.total_seconds()
        
        return result
    
    def get_error_summary(self) -> Dict[str, Any]:
        """
        Get comprehensive error summary from error handler.
        
        Returns:
            Dictionary with error statistics and details including:
            - Total error count
            - Sub-agent errors
            - Tool errors
            - Critical errors
        """
        return self.error_handler.get_error_summary()
