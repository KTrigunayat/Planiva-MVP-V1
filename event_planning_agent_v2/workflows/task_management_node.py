"""
Task Management Node for LangGraph Workflow

This module provides the workflow node function for integrating the Task Management Agent
into the LangGraph event planning workflow. The node sits between timeline generation
and blueprint generation, processing selected vendor combinations to generate a
comprehensive extended task list.

The task management node:
1. Validates that timeline data is available (conditional execution)
2. Checks for existing checkpoints and restores state if needed
3. Instantiates the TaskManagementAgent with StateManager integration
4. Calls the agent's process_with_error_handling() method
5. Updates EventPlanningState with extended_task_list
6. Persists state after each processing step
7. Handles errors gracefully without blocking the workflow

State Management Integration:
- Uses StateManager from database/state_manager.py for persistence
- Creates checkpoints after sub-agent consolidation and tool processing
- Enables state restoration for resuming after interruptions
- Ensures Blueprint Agent can access extended_task_list from state

Integration:
- Receives state from timeline_generation node
- Passes state to blueprint_generation node
- Uses existing StateManager for persistence
- Follows existing error handling patterns
"""

import logging
import asyncio
from typing import Dict, Any, Optional

from .state_models import EventPlanningState, WorkflowStatus, transition_logger
from ..agents.task_management.core.task_management_agent import TaskManagementAgent
from ..agents.orchestrator import StateManagementTool
from ..database.state_manager import get_state_manager

logger = logging.getLogger(__name__)


def task_management_node(state: EventPlanningState) -> EventPlanningState:
    """
    LangGraph workflow node for Task Management Agent processing.
    
    This node function:
    1. Validates that required data (timeline_data, selected_combination) is available
    2. Checks for existing checkpoints and attempts state restoration if interrupted
    3. Instantiates TaskManagementAgent with StateManager integration
    4. Processes the state through the agent to generate extended_task_list
    5. Updates workflow state with task management results
    6. Persists state after each processing step for recovery
    7. Handles errors gracefully and logs all transitions
    
    State Management Integration:
    - Uses StateManager for persistence after each processing step
    - Creates checkpoints after sub-agent consolidation and tool processing
    - Enables state restoration for resuming after interruptions
    - Ensures Blueprint Agent can access extended_task_list from state
    
    The node can be skipped if timeline data is missing (handled by conditional edge).
    
    Args:
        state: Current EventPlanningState from workflow
        
    Returns:
        Updated EventPlanningState with extended_task_list field populated,
        or original state with error information if processing failed
        
    Workflow Integration:
        - Previous node: timeline_generation
        - Next node: blueprint_generation
        - Conditional: Skipped if timeline_data is missing
    """
    logger.info(f"Starting task management processing for plan {state.get('plan_id')}")
    
    # Log node entry
    state = transition_logger.log_node_entry(
        state=state,
        node_name="task_management",
        input_data={
            "has_timeline_data": state.get('timeline_data') is not None,
            "has_selected_combination": state.get('selected_combination') is not None,
            "has_checkpoints": 'task_management_checkpoints' in state,
            "iteration_count": state.get('iteration_count', 0)
        }
    )
    
    try:
        # Validate required data
        timeline_data = state.get('timeline_data')
        selected_combination = state.get('selected_combination')
        
        if not timeline_data:
            logger.warning("Timeline data not available, skipping task management processing")
            
            # Log skip with warning
            state = transition_logger.log_node_exit(
                state=state,
                node_name="task_management",
                output_data={
                    "status": "skipped",
                    "reason": "timeline_data_missing"
                },
                success=True
            )
            
            # Set next node to blueprint generation
            state['next_node'] = 'blueprint_generation'
            return state
        
        if not selected_combination:
            logger.warning("Selected combination not available, task management may have limited data")
            # Continue processing but log warning
        
        # Initialize state manager and StateManagementTool
        logger.info("Initializing state management infrastructure...")
        state_manager = get_state_manager()
        state_management_tool = StateManagementTool()
        
        # Check for existing checkpoints and attempt restoration
        checkpoints = state.get('task_management_checkpoints', {})
        if checkpoints:
            logger.info(f"Found existing checkpoints: {list(checkpoints.keys())}")
            logger.info("Attempting to restore from last checkpoint...")
            
            # Try to restore state from database
            try:
                restored_state = state_manager.recover_workflow_state(state.get('plan_id'))
                if restored_state:
                    logger.info("Successfully restored state from database")
                    state = restored_state
                else:
                    logger.warning("Could not restore state, continuing with current state")
            except Exception as restore_error:
                logger.warning(f"State restoration failed: {restore_error}, continuing with current state")
        
        # Initialize Task Management Agent with state manager
        logger.info("Initializing Task Management Agent...")
        task_management_agent = TaskManagementAgent(
            state_manager=state_manager,
            llm_model=None,  # Uses default from settings
            db_connection=None  # Uses default connection
        )
        
        # Check if we can resume from a checkpoint
        resume_from = task_management_agent.restore_from_checkpoint(state)
        if resume_from:
            logger.info(f"Resuming processing from checkpoint: {resume_from}")
        
        # Update workflow status
        state['workflow_status'] = WorkflowStatus.RUNNING.value
        state['current_node'] = 'task_management'
        
        # Save initial state before processing
        logger.info("Saving initial state before processing...")
        try:
            state_manager.save_workflow_state(state)
        except Exception as save_error:
            logger.warning(f"Failed to save initial state: {save_error}")
        
        # Process state through Task Management Agent
        logger.info("Processing state through Task Management Agent...")
        
        # Run async process method with error handling
        updated_state = asyncio.run(
            task_management_agent.process_with_error_handling(state)
        )
        
        # Check if processing was successful
        if updated_state.get('extended_task_list'):
            logger.info(
                f"Task management processing completed successfully for plan {state.get('plan_id')}"
            )
            
            # Extract processing summary for logging
            extended_task_list = updated_state.get('extended_task_list', {})
            processing_summary = extended_task_list.get('processing_summary', {})
            
            # Update workflow status to indicate completion
            updated_state['workflow_status'] = WorkflowStatus.RUNNING.value
            
            # Log successful processing
            state = transition_logger.log_node_exit(
                state=updated_state,
                node_name="task_management",
                output_data={
                    "status": "completed",
                    "total_tasks": processing_summary.get('total_tasks', 0),
                    "tasks_with_errors": processing_summary.get('tasks_with_errors', 0),
                    "tasks_with_warnings": processing_summary.get('tasks_with_warnings', 0),
                    "processing_time": processing_summary.get('processing_time', 0),
                    "extended_task_list_available": True
                },
                success=True
            )
            
            # Set next node to blueprint generation
            state['next_node'] = 'blueprint_generation'
            
            # Final state save with extended task list
            logger.info("Saving final state with extended task list...")
            try:
                state_manager.save_workflow_state(state)
                logger.info("Final state saved successfully - Blueprint Agent can now access extended_task_list")
            except Exception as save_error:
                logger.error(f"Failed to save final state: {save_error}")
                # Don't fail the workflow, just log the error
                state['error_count'] = state.get('error_count', 0) + 1
                state['last_error'] = f"State persistence error: {str(save_error)}"
            
            # Clean up checkpoints after successful completion
            if 'task_management_checkpoints' in state:
                del state['task_management_checkpoints']
                logger.info("Cleaned up task management checkpoints")
            
            return state
        else:
            # Processing completed but no extended task list generated
            logger.warning(
                f"Task management processing completed but no extended_task_list generated "
                f"for plan {state.get('plan_id')}"
            )
            
            # Log partial success
            state = transition_logger.log_node_exit(
                state=updated_state,
                node_name="task_management",
                output_data={
                    "status": "partial_success",
                    "reason": "no_extended_task_list_generated",
                    "extended_task_list_available": False
                },
                success=True
            )
            
            # Continue to blueprint generation anyway
            state['next_node'] = 'blueprint_generation'
            
            # Save state even with partial success
            try:
                state_manager.save_workflow_state(state)
            except Exception as save_error:
                logger.warning(f"Failed to save partial success state: {save_error}")
            
            return state
    
    except Exception as e:
        logger.error(f"Failed task management processing: {e}", exc_info=True)
        
        # Log failed processing
        state = transition_logger.log_node_exit(
            state=state,
            node_name="task_management",
            output_data={
                "status": "failed",
                "error": str(e),
                "extended_task_list_available": False
            },
            success=False
        )
        
        # Update error tracking in state
        state['error_count'] = state.get('error_count', 0) + 1
        state['last_error'] = f"Task management processing failed: {str(e)}"
        
        # Save error state for recovery
        try:
            state_manager = get_state_manager()
            state_manager.save_workflow_state(state)
            logger.info("Error state saved for potential recovery")
        except Exception as save_error:
            logger.error(f"Failed to save error state: {save_error}")
        
        # Don't fail the entire workflow - continue to blueprint generation
        # Blueprint agent can work without extended task list
        state['next_node'] = 'blueprint_generation'
        
        logger.info(
            f"Continuing workflow despite task management error for plan {state.get('plan_id')}"
        )
        
        return state


def should_run_task_management(state: EventPlanningState) -> bool:
    """
    Determine whether task management processing should run.
    
    This function is used by conditional edges to decide whether to execute
    the task management node or skip it.
    
    Args:
        state: Current EventPlanningState
        
    Returns:
        True if task management should run, False to skip
        
    Conditions for running:
        - timeline_data must be present
        - selected_combination should be present (warning if not)
        - workflow_status should not be FAILED
    """
    # Check if timeline data is available
    has_timeline = state.get('timeline_data') is not None
    
    # Check if workflow is in failed state
    is_failed = state.get('workflow_status') == WorkflowStatus.FAILED.value
    
    # Run task management if timeline data exists and workflow not failed
    should_run = has_timeline and not is_failed
    
    if not should_run:
        logger.info(
            f"Task management will be skipped for plan {state.get('plan_id')}: "
            f"has_timeline={has_timeline}, is_failed={is_failed}"
        )
    
    return should_run
