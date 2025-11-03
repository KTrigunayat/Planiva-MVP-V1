"""
FastAPI routes for Event Planning Agent v2
"""

import logging
from fastapi import APIRouter, HTTPException, Depends, BackgroundTasks, Query
from fastapi.responses import JSONResponse
from typing import Dict, Any, Optional, List
from datetime import datetime
from uuid import uuid4
import asyncio

from .schemas import (
    EventPlanRequest, EventPlanResponse, CombinationSelection,
    ErrorResponse, HealthResponse, PlanListResponse, AsyncTaskResponse,
    PlanStatus, WorkflowStatus, EventCombination
)
from ..workflows.execution_engine import (
    get_execution_engine, ExecutionConfig, ExecutionMode,
    execute_event_planning_workflow, get_workflow_status,
    resume_event_planning_workflow, cancel_workflow
)
from ..database.state_manager import get_state_manager
from ..config.settings import get_settings
from .crew_integration import (
    execute_event_planning, generate_event_blueprint,
    get_planning_workflow_status, cancel_planning_workflow,
    resume_planning_workflow
)

logger = logging.getLogger(__name__)
router = APIRouter()

# Dependency to get settings
def get_app_settings():
    return get_settings()

# Dependency to get state manager
def get_db_state_manager():
    return get_state_manager()

# Dependency to get execution engine
def get_workflow_engine():
    return get_execution_engine()


@router.get("/", response_model=Dict[str, str])
async def root():
    """Root endpoint"""
    return {
        "message": "Event Planning Agent v2 API",
        "version": "2.0.0",
        "status": "active"
    }


@router.get("/health", response_model=HealthResponse)
async def health_check(
    settings = Depends(get_app_settings),
    state_manager = Depends(get_db_state_manager)
):
    """Health check endpoint"""
    try:
        # Check database connectivity
        db_status = "healthy"
        try:
            state_manager.health_check()
        except Exception as e:
            db_status = f"unhealthy: {str(e)}"
        
        # Check workflow engine
        engine_status = "healthy"
        try:
            engine = get_workflow_engine()
            metrics = engine.get_performance_metrics()
            if metrics["total_executions"] > 0 and metrics["success_rate"] < 0.5:
                engine_status = "degraded"
        except Exception as e:
            engine_status = f"unhealthy: {str(e)}"
        
        overall_status = "healthy"
        if "unhealthy" in [db_status, engine_status]:
            overall_status = "unhealthy"
        elif "degraded" in [db_status, engine_status]:
            overall_status = "degraded"
        
        return HealthResponse(
            status=overall_status,
            version="2.0.0",
            components={
                "database": db_status,
                "workflow_engine": engine_status,
                "api": "healthy"
            }
        )
    except Exception as e:
        logger.error(f"Health check failed: {e}")
        return HealthResponse(
            status="unhealthy",
            version="2.0.0",
            components={"error": str(e)}
        )


@router.post("/v1/plans", response_model=EventPlanResponse)
async def create_plan(
    request: EventPlanRequest,
    background_tasks: BackgroundTasks,
    async_execution: bool = Query(False, description="Execute workflow asynchronously"),
    settings = Depends(get_app_settings),
    state_manager = Depends(get_db_state_manager)
):
    """
    Create a new event plan
    
    Maintains compatibility with existing request/response format while
    integrating with CrewAI and LangGraph workflow execution.
    """
    try:
        # Generate plan ID
        plan_id = str(uuid4())
        
        logger.info(f"Creating event plan {plan_id} for client {request.clientName}")
        
        # Convert request to internal format
        client_request = request.dict()
        
        # Create initial plan record
        initial_plan = {
            "plan_id": plan_id,
            "status": PlanStatus.PENDING.value,
            "client_name": request.clientName,
            "client_request": client_request,
            "combinations": [],
            "selected_combination": None,
            "final_blueprint": None,
            "workflow_status": {
                "current_step": "initialization",
                "progress_percentage": 0.0,
                "steps_completed": [],
                "estimated_completion": None,
                "error_message": None
            },
            "created_at": datetime.utcnow(),
            "updated_at": datetime.utcnow()
        }
        
        # Save initial state
        state_manager.save_plan(initial_plan)
        
        if async_execution:
            # Execute workflow asynchronously
            execution_config = ExecutionConfig(
                mode=ExecutionMode.ASYNCHRONOUS,
                enable_monitoring=True,
                enable_checkpointing=True
            )
            
            # Start background task
            background_tasks.add_task(
                _execute_workflow_background,
                client_request,
                plan_id,
                execution_config,
                state_manager
            )
            
            # Return immediate response
            return EventPlanResponse(
                plan_id=plan_id,
                status=PlanStatus.PROCESSING,
                client_name=request.clientName,
                combinations=[],
                workflow_status=WorkflowStatus(
                    current_step="initialization",
                    progress_percentage=5.0,
                    steps_completed=["plan_created"]
                ),
                created_at=initial_plan["created_at"],
                updated_at=initial_plan["updated_at"]
            )
        else:
            # Execute workflow synchronously
            execution_config = ExecutionConfig(
                mode=ExecutionMode.SYNCHRONOUS,
                timeout=300.0,  # 5 minutes
                enable_monitoring=True,
                enable_checkpointing=True
            )
            
            # Execute workflow using CrewAI integration
            result = execute_event_planning(
                client_request=client_request,
                plan_id=plan_id,
                async_execution=False
            )
            
            # Convert result to response format
            return _convert_execution_result_to_response(result, state_manager)
            
    except Exception as e:
        logger.error(f"Failed to create plan: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="plan_creation_failed",
                message=f"Failed to create event plan: {str(e)}",
                details={"client_name": request.clientName}
            ).dict()
        )


@router.get("/v1/plans/{plan_id}", response_model=EventPlanResponse)
async def get_plan(
    plan_id: str,
    include_workflow_details: bool = Query(False, description="Include detailed workflow status"),
    state_manager = Depends(get_db_state_manager)
):
    """
    Get event plan by ID with enhanced status reporting
    
    Provides comprehensive plan status including workflow execution details,
    agent performance metrics, and real-time progress updates.
    """
    try:
        logger.info(f"Retrieving plan {plan_id}")
        
        # Load plan from database
        plan_data = state_manager.load_plan(plan_id)
        if not plan_data:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="plan_not_found",
                    message=f"Event plan {plan_id} not found"
                ).dict()
            )
        
        # Get workflow status if available
        workflow_status = None
        if include_workflow_details:
            execution_status = get_planning_workflow_status(plan_id)
            if execution_status:
                workflow_status = WorkflowStatus(
                    current_step=execution_status.get("status", "unknown"),
                    progress_percentage=_calculate_progress_percentage(execution_status),
                    steps_completed=execution_status.get("nodes_executed", []),
                    error_message=execution_status.get("error")
                )
        
        # Convert combinations to proper format
        combinations = []
        for combo_data in plan_data.get("combinations", []):
            combinations.append(EventCombination(**combo_data))
        
        selected_combination = None
        if plan_data.get("selected_combination"):
            selected_combination = EventCombination(**plan_data["selected_combination"])
        
        return EventPlanResponse(
            plan_id=plan_id,
            status=PlanStatus(plan_data.get("status", "pending")),
            client_name=plan_data.get("client_name", "Unknown"),
            combinations=combinations,
            selected_combination=selected_combination,
            final_blueprint=plan_data.get("final_blueprint"),
            workflow_status=workflow_status,
            created_at=plan_data.get("created_at", datetime.utcnow()),
            updated_at=plan_data.get("updated_at", datetime.utcnow())
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="plan_retrieval_failed",
                message=f"Failed to retrieve plan: {str(e)}",
                details={"plan_id": plan_id}
            ).dict()
        )


@router.post("/v1/plans/{plan_id}/select-combination", response_model=EventPlanResponse)
async def select_combination(
    plan_id: str,
    selection: CombinationSelection,
    background_tasks: BackgroundTasks,
    generate_blueprint: bool = Query(True, description="Generate final blueprint"),
    state_manager = Depends(get_db_state_manager)
):
    """
    Select a combination for the event plan
    
    Allows clients to select from available combinations and optionally
    trigger blueprint generation through the Blueprint Agent.
    """
    try:
        logger.info(f"Selecting combination {selection.combination_id} for plan {plan_id}")
        
        # Load existing plan
        plan_data = state_manager.load_plan(plan_id)
        if not plan_data:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="plan_not_found",
                    message=f"Event plan {plan_id} not found"
                ).dict()
            )
        
        # Find the selected combination
        selected_combo = None
        for combo in plan_data.get("combinations", []):
            if combo.get("combination_id") == selection.combination_id:
                selected_combo = combo
                break
        
        if not selected_combo:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="combination_not_found",
                    message=f"Combination {selection.combination_id} not found in plan"
                ).dict()
            )
        
        # Update plan with selection
        plan_data["selected_combination"] = selected_combo
        plan_data["status"] = PlanStatus.PROCESSING.value if generate_blueprint else PlanStatus.COMPLETED.value
        plan_data["updated_at"] = datetime.utcnow()
        
        # Add selection metadata
        if selection.notes:
            plan_data["selection_notes"] = selection.notes
        if selection.client_feedback:
            plan_data["client_feedback"] = selection.client_feedback
        
        # Save updated plan
        state_manager.save_plan(plan_data)
        
        if generate_blueprint:
            # Trigger blueprint generation in background
            background_tasks.add_task(
                _generate_blueprint_background,
                plan_id,
                selected_combo,
                state_manager
            )
            
            workflow_status = WorkflowStatus(
                current_step="blueprint_generation",
                progress_percentage=90.0,
                steps_completed=["combination_selected"],
                estimated_completion=datetime.utcnow().replace(microsecond=0)
            )
        else:
            workflow_status = WorkflowStatus(
                current_step="completed",
                progress_percentage=100.0,
                steps_completed=["combination_selected", "plan_finalized"]
            )
        
        return EventPlanResponse(
            plan_id=plan_id,
            status=PlanStatus(plan_data["status"]),
            client_name=plan_data.get("client_name", "Unknown"),
            combinations=[EventCombination(**c) for c in plan_data.get("combinations", [])],
            selected_combination=EventCombination(**selected_combo),
            final_blueprint=plan_data.get("final_blueprint"),
            workflow_status=workflow_status,
            created_at=plan_data.get("created_at", datetime.utcnow()),
            updated_at=plan_data["updated_at"]
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to select combination for plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="combination_selection_failed",
                message=f"Failed to select combination: {str(e)}",
                details={"plan_id": plan_id, "combination_id": selection.combination_id}
            ).dict()
        )


@router.get("/v1/plans", response_model=PlanListResponse)
async def list_plans(
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(10, ge=1, le=100, description="Page size"),
    status: Optional[PlanStatus] = Query(None, description="Filter by status"),
    client_name: Optional[str] = Query(None, description="Filter by client name"),
    state_manager = Depends(get_db_state_manager)
):
    """List event plans with pagination and filtering"""
    try:
        # Build filters
        filters = {}
        if status:
            filters["status"] = status.value
        if client_name:
            filters["client_name"] = client_name
        
        # Get plans from database
        plans_data, total_count = state_manager.list_plans(
            page=page,
            page_size=page_size,
            filters=filters
        )
        
        # Convert to response format
        plans = []
        for plan_data in plans_data:
            combinations = [EventCombination(**c) for c in plan_data.get("combinations", [])]
            selected_combination = None
            if plan_data.get("selected_combination"):
                selected_combination = EventCombination(**plan_data["selected_combination"])
            
            plans.append(EventPlanResponse(
                plan_id=plan_data["plan_id"],
                status=PlanStatus(plan_data.get("status", "pending")),
                client_name=plan_data.get("client_name", "Unknown"),
                combinations=combinations,
                selected_combination=selected_combination,
                final_blueprint=plan_data.get("final_blueprint"),
                created_at=plan_data.get("created_at", datetime.utcnow()),
                updated_at=plan_data.get("updated_at", datetime.utcnow())
            ))
        
        return PlanListResponse(
            plans=plans,
            total_count=total_count,
            page=page,
            page_size=page_size
        )
        
    except Exception as e:
        logger.error(f"Failed to list plans: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="plan_listing_failed",
                message=f"Failed to list plans: {str(e)}"
            ).dict()
        )


@router.post("/v1/plans/{plan_id}/resume", response_model=EventPlanResponse)
async def resume_plan(
    plan_id: str,
    background_tasks: BackgroundTasks,
    async_execution: bool = Query(True, description="Resume asynchronously"),
    state_manager = Depends(get_db_state_manager)
):
    """Resume a paused or failed workflow"""
    try:
        logger.info(f"Resuming workflow for plan {plan_id}")
        
        # Check if plan exists
        plan_data = state_manager.load_plan(plan_id)
        if not plan_data:
            raise HTTPException(
                status_code=404,
                detail=ErrorResponse(
                    error="plan_not_found",
                    message=f"Event plan {plan_id} not found"
                ).dict()
            )
        
        if async_execution:
            # Resume asynchronously
            execution_config = ExecutionConfig(
                mode=ExecutionMode.ASYNCHRONOUS,
                enable_monitoring=True,
                enable_checkpointing=True
            )
            
            background_tasks.add_task(
                _resume_workflow_background,
                plan_id,
                execution_config,
                state_manager
            )
            
            # Update status
            plan_data["status"] = PlanStatus.PROCESSING.value
            plan_data["updated_at"] = datetime.utcnow()
            state_manager.save_plan(plan_data)
            
            return EventPlanResponse(
                plan_id=plan_id,
                status=PlanStatus.PROCESSING,
                client_name=plan_data.get("client_name", "Unknown"),
                combinations=[EventCombination(**c) for c in plan_data.get("combinations", [])],
                workflow_status=WorkflowStatus(
                    current_step="resuming",
                    progress_percentage=10.0,
                    steps_completed=["resume_initiated"]
                ),
                created_at=plan_data.get("created_at", datetime.utcnow()),
                updated_at=plan_data["updated_at"]
            )
        else:
            # Resume synchronously
            execution_config = ExecutionConfig(
                mode=ExecutionMode.SYNCHRONOUS,
                timeout=300.0,
                enable_monitoring=True
            )
            
            result = resume_planning_workflow(plan_id, async_execution=False)
            return _convert_execution_result_to_response(result, state_manager)
            
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to resume plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="plan_resume_failed",
                message=f"Failed to resume plan: {str(e)}",
                details={"plan_id": plan_id}
            ).dict()
        )


@router.delete("/v1/plans/{plan_id}")
async def cancel_plan(
    plan_id: str,
    state_manager = Depends(get_db_state_manager)
):
    """Cancel an active workflow execution"""
    try:
        logger.info(f"Cancelling plan {plan_id}")
        
        # Cancel workflow execution
        cancelled = cancel_planning_workflow(plan_id)
        
        if cancelled:
            # Update plan status
            plan_data = state_manager.load_plan(plan_id)
            if plan_data:
                plan_data["status"] = PlanStatus.CANCELLED.value
                plan_data["updated_at"] = datetime.utcnow()
                state_manager.save_plan(plan_data)
            
            return {"message": f"Plan {plan_id} cancelled successfully"}
        else:
            return {"message": f"Plan {plan_id} was not actively running"}
            
    except Exception as e:
        logger.error(f"Failed to cancel plan {plan_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="plan_cancellation_failed",
                message=f"Failed to cancel plan: {str(e)}",
                details={"plan_id": plan_id}
            ).dict()
        )


# Background task functions
async def _execute_workflow_background(
    client_request: Dict[str, Any],
    plan_id: str,
    config: ExecutionConfig,
    state_manager
):
    """Execute workflow in background"""
    try:
        result = execute_event_planning(client_request, plan_id, async_execution=True)
        
        # Update plan with results
        plan_data = state_manager.load_plan(plan_id)
        if plan_data:
            if result.success and result.final_state:
                plan_data["status"] = PlanStatus.COMPLETED.value
                plan_data["combinations"] = result.final_state.get("beam_candidates", [])
            else:
                plan_data["status"] = PlanStatus.FAILED.value
                plan_data["error_message"] = result.error
            
            plan_data["updated_at"] = datetime.utcnow()
            state_manager.save_plan(plan_data)
            
    except Exception as e:
        logger.error(f"Background workflow execution failed for plan {plan_id}: {e}")
        # Update plan with error
        plan_data = state_manager.load_plan(plan_id)
        if plan_data:
            plan_data["status"] = PlanStatus.FAILED.value
            plan_data["error_message"] = str(e)
            plan_data["updated_at"] = datetime.utcnow()
            state_manager.save_plan(plan_data)


async def _resume_workflow_background(
    plan_id: str,
    config: ExecutionConfig,
    state_manager
):
    """Resume workflow in background"""
    try:
        result = resume_planning_workflow(plan_id, async_execution=True)
        
        # Update plan with results
        plan_data = state_manager.load_plan(plan_id)
        if plan_data:
            if result.success and result.final_state:
                plan_data["status"] = PlanStatus.COMPLETED.value
                plan_data["combinations"] = result.final_state.get("beam_candidates", [])
            else:
                plan_data["status"] = PlanStatus.FAILED.value
                plan_data["error_message"] = result.error
            
            plan_data["updated_at"] = datetime.utcnow()
            state_manager.save_plan(plan_data)
            
    except Exception as e:
        logger.error(f"Background workflow resume failed for plan {plan_id}: {e}")


async def _generate_blueprint_background(
    plan_id: str,
    selected_combination: Dict[str, Any],
    state_manager
):
    """Generate blueprint in background"""
    try:
        # Use CrewAI Blueprint Agent to generate blueprint
        blueprint = generate_event_blueprint(plan_id, selected_combination)
        
        # Fallback to simple blueprint if agent fails
        if not blueprint:
            blueprint = f"""
Event Blueprint for Plan {plan_id}

Selected Vendors:
- Venue: {selected_combination.get('venue', {}).get('name', 'TBD')}
- Caterer: {selected_combination.get('caterer', {}).get('name', 'TBD')}
- Photographer: {selected_combination.get('photographer', {}).get('name', 'TBD')}
- Makeup Artist: {selected_combination.get('makeup_artist', {}).get('name', 'TBD')}

Total Estimated Cost: ₹{selected_combination.get('estimated_cost', 0):,.2f}
Feasibility Score: {selected_combination.get('feasibility_score', 0):.2f}

Generated on: {datetime.utcnow().isoformat()}
            """.strip()
        
        # Update plan with blueprint
        plan_data = state_manager.load_plan(plan_id)
        if plan_data:
            plan_data["final_blueprint"] = blueprint
            plan_data["status"] = PlanStatus.COMPLETED.value
            plan_data["updated_at"] = datetime.utcnow()
            state_manager.save_plan(plan_data)
            
    except Exception as e:
        logger.error(f"Blueprint generation failed for plan {plan_id}: {e}")


def _convert_execution_result_to_response(result, state_manager) -> EventPlanResponse:
    """Convert execution result to API response"""
    plan_data = state_manager.load_plan(result.plan_id)
    
    if not plan_data:
        # Create minimal response from result
        return EventPlanResponse(
            plan_id=result.plan_id,
            status=PlanStatus.COMPLETED if result.success else PlanStatus.FAILED,
            client_name="Unknown",
            combinations=[],
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
    
    # Convert combinations
    combinations = []
    if result.final_state and result.final_state.get("beam_candidates"):
        for combo in result.final_state["beam_candidates"]:
            combinations.append(EventCombination(**combo))
    
    return EventPlanResponse(
        plan_id=result.plan_id,
        status=PlanStatus.COMPLETED if result.success else PlanStatus.FAILED,
        client_name=plan_data.get("client_name", "Unknown"),
        combinations=combinations,
        workflow_status=WorkflowStatus(
            current_step="completed" if result.success else "failed",
            progress_percentage=100.0 if result.success else 0.0,
            steps_completed=result.nodes_executed,
            error_message=result.error
        ),
        created_at=plan_data.get("created_at", datetime.utcnow()),
        updated_at=datetime.utcnow()
    )


def _calculate_progress_percentage(execution_status: Dict[str, Any]) -> float:
    """Calculate progress percentage from execution status"""
    status = execution_status.get("status", "unknown")
    nodes_executed = len(execution_status.get("nodes_executed", []))
    
    # Rough progress calculation based on typical workflow steps
    total_expected_nodes = 8  # Approximate number of workflow nodes
    
    if status == "completed":
        return 100.0
    elif status == "failed":
        return max(10.0, (nodes_executed / total_expected_nodes) * 100)
    elif status == "running":
        return min(95.0, max(10.0, (nodes_executed / total_expected_nodes) * 100))
    else:
        return 5.0


# CRM Preference Management Endpoints

@router.post("/api/crm/preferences")
async def update_client_preferences(
    preferences_data: Dict[str, Any],
    state_manager = Depends(get_db_state_manager)
):
    """
    Update client communication preferences.
    
    Request body:
    {
        "client_id": "string",
        "preferred_channels": ["email", "sms", "whatsapp"],
        "timezone": "America/New_York",
        "quiet_hours_start": "22:00",
        "quiet_hours_end": "08:00",
        "opt_out_email": false,
        "opt_out_sms": false,
        "opt_out_whatsapp": false,
        "language_preference": "en"
    }
    """
    try:
        from ..crm.models import ClientPreferences, MessageChannel
        from ..crm.repository import CommunicationRepository
        from ..crm.cache_manager import get_cache_manager
        
        logger.info(f"Updating preferences for client {preferences_data.get('client_id')}")
        
        # Validate required fields
        if 'client_id' not in preferences_data:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="validation_error",
                    message="client_id is required"
                ).dict()
            )
        
        # Parse and validate preferred channels
        preferred_channels = []
        if 'preferred_channels' in preferences_data:
            try:
                for ch in preferences_data['preferred_channels']:
                    preferred_channels.append(MessageChannel(ch))
            except ValueError as e:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="validation_error",
                        message=f"Invalid channel: {e}"
                    ).dict()
                )
        else:
            preferred_channels = [MessageChannel.EMAIL]
        
        # Create ClientPreferences object with validation
        try:
            preferences = ClientPreferences(
                client_id=preferences_data['client_id'],
                preferred_channels=preferred_channels,
                timezone=preferences_data.get('timezone', 'UTC'),
                quiet_hours_start=preferences_data.get('quiet_hours_start', '22:00'),
                quiet_hours_end=preferences_data.get('quiet_hours_end', '08:00'),
                opt_out_email=preferences_data.get('opt_out_email', False),
                opt_out_sms=preferences_data.get('opt_out_sms', False),
                opt_out_whatsapp=preferences_data.get('opt_out_whatsapp', False),
                language_preference=preferences_data.get('language_preference', 'en')
            )
        except ValueError as e:
            raise HTTPException(
                status_code=400,
                detail=ErrorResponse(
                    error="validation_error",
                    message=f"Invalid preferences: {e}"
                ).dict()
            )
        
        # Save to database
        repository = CommunicationRepository()
        success = repository.save_client_preferences(preferences)
        
        if not success:
            raise HTTPException(
                status_code=500,
                detail=ErrorResponse(
                    error="save_failed",
                    message="Failed to save preferences"
                ).dict()
            )
        
        # Invalidate cache
        cache_manager = get_cache_manager()
        cache_manager.invalidate_client_preferences(preferences.client_id)
        
        # Cache new preferences
        cache_manager.set_client_preferences(preferences)
        
        logger.info(f"Successfully updated preferences for client {preferences.client_id}")
        
        return {
            "success": True,
            "message": "Preferences updated successfully",
            "preferences": {
                "client_id": preferences.client_id,
                "preferred_channels": [ch.value for ch in preferences.preferred_channels],
                "timezone": preferences.timezone,
                "quiet_hours_start": preferences.quiet_hours_start,
                "quiet_hours_end": preferences.quiet_hours_end,
                "opt_out_email": preferences.opt_out_email,
                "opt_out_sms": preferences.opt_out_sms,
                "opt_out_whatsapp": preferences.opt_out_whatsapp,
                "language_preference": preferences.language_preference
            }
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to update preferences: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="preference_update_failed",
                message=f"Failed to update preferences: {str(e)}"
            ).dict()
        )


@router.get("/api/crm/preferences/{client_id}")
async def get_client_preferences_endpoint(
    client_id: str,
    state_manager = Depends(get_db_state_manager)
):
    """
    Get client communication preferences.
    
    Returns preferences from cache if available, otherwise from database.
    If no preferences exist, returns default preferences.
    """
    try:
        from ..crm.models import ClientPreferences, MessageChannel
        from ..crm.repository import CommunicationRepository
        from ..crm.cache_manager import get_cache_manager
        
        logger.info(f"Retrieving preferences for client {client_id}")
        
        # Try cache first
        cache_manager = get_cache_manager()
        preferences = cache_manager.get_client_preferences(client_id)
        
        if preferences:
            logger.debug(f"Preferences retrieved from cache for client {client_id}")
        else:
            # Load from database
            repository = CommunicationRepository()
            preferences = repository.get_client_preferences(client_id)
            
            if preferences:
                # Cache for future requests
                cache_manager.set_client_preferences(preferences)
                logger.debug(f"Preferences retrieved from database for client {client_id}")
            else:
                # Return default preferences
                preferences = ClientPreferences(
                    client_id=client_id,
                    preferred_channels=[MessageChannel.EMAIL],
                    timezone="UTC",
                    quiet_hours_start="22:00",
                    quiet_hours_end="08:00",
                    opt_out_email=False,
                    opt_out_sms=False,
                    opt_out_whatsapp=False,
                    language_preference="en"
                )
                logger.debug(f"Returning default preferences for client {client_id}")
        
        return {
            "client_id": preferences.client_id,
            "preferred_channels": [ch.value for ch in preferences.preferred_channels],
            "timezone": preferences.timezone,
            "quiet_hours_start": preferences.quiet_hours_start,
            "quiet_hours_end": preferences.quiet_hours_end,
            "opt_out_email": preferences.opt_out_email,
            "opt_out_sms": preferences.opt_out_sms,
            "opt_out_whatsapp": preferences.opt_out_whatsapp,
            "language_preference": preferences.language_preference,
            "available_channels": [ch.value for ch in preferences.get_available_channels()]
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve preferences for client {client_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="preference_retrieval_failed",
                message=f"Failed to retrieve preferences: {str(e)}"
            ).dict()
        )


@router.delete("/api/crm/preferences/{client_id}")
async def delete_client_preferences_endpoint(
    client_id: str,
    state_manager = Depends(get_db_state_manager)
):
    """
    Delete client communication preferences (GDPR compliance).
    
    Removes preferences from both database and cache.
    """
    try:
        from ..crm.repository import CommunicationRepository
        from ..crm.cache_manager import get_cache_manager
        
        logger.info(f"Deleting preferences for client {client_id}")
        
        # Delete from database
        repository = CommunicationRepository()
        deleted = repository.delete_client_preferences(client_id)
        
        # Invalidate cache
        cache_manager = get_cache_manager()
        cache_manager.invalidate_client_preferences(client_id)
        
        if deleted:
            logger.info(f"Successfully deleted preferences for client {client_id}")
            return {
                "success": True,
                "message": f"Preferences deleted for client {client_id}"
            }
        else:
            return {
                "success": False,
                "message": f"No preferences found for client {client_id}"
            }
        
    except Exception as e:
        logger.error(f"Failed to delete preferences for client {client_id}: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="preference_deletion_failed",
                message=f"Failed to delete preferences: {str(e)}"
            ).dict()
        )


# CRM Health Check and Monitoring Endpoints

@router.get("/api/crm/health")
async def crm_health_check(
    include_details: bool = Query(True, description="Include detailed component checks")
):
    """
    CRM Communication Engine health check endpoint.
    
    Provides health status for load balancers and monitoring systems.
    Returns overall health and individual component statuses.
    """
    try:
        from ..crm.health_check import get_health_checker
        
        health_checker = get_health_checker()
        
        if health_checker is None:
            # Health checker not initialized - return basic status
            return {
                "status": "degraded",
                "version": "2.0.0",
                "timestamp": datetime.utcnow().isoformat(),
                "message": "Health checker not initialized",
                "components": {}
            }
        
        # Perform health check
        health_status = await health_checker.check_health(include_details=include_details)
        
        return health_status.to_dict()
        
    except Exception as e:
        logger.error(f"CRM health check failed: {e}")
        return {
            "status": "unhealthy",
            "version": "2.0.0",
            "timestamp": datetime.utcnow().isoformat(),
            "error": str(e),
            "components": {}
        }


@router.get("/api/crm/health/readiness")
async def crm_readiness_check():
    """
    CRM readiness check for Kubernetes/orchestration systems.
    
    Returns 200 if CRM is ready to accept requests, 503 otherwise.
    """
    try:
        from ..crm.health_check import get_health_checker
        
        health_checker = get_health_checker()
        
        if health_checker is None or not health_checker.get_readiness():
            return JSONResponse(
                status_code=503,
                content={
                    "ready": False,
                    "message": "CRM not ready to accept requests"
                }
            )
        
        return {
            "ready": True,
            "message": "CRM ready to accept requests"
        }
        
    except Exception as e:
        logger.error(f"CRM readiness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "ready": False,
                "error": str(e)
            }
        )


@router.get("/api/crm/health/liveness")
async def crm_liveness_check():
    """
    CRM liveness check for Kubernetes/orchestration systems.
    
    Returns 200 if CRM process is alive, 503 otherwise.
    """
    try:
        from ..crm.health_check import get_health_checker
        
        health_checker = get_health_checker()
        
        if health_checker is None or not health_checker.get_liveness():
            return JSONResponse(
                status_code=503,
                content={
                    "alive": False,
                    "message": "CRM process not responding"
                }
            )
        
        return {
            "alive": True,
            "message": "CRM process is alive"
        }
        
    except Exception as e:
        logger.error(f"CRM liveness check failed: {e}")
        return JSONResponse(
            status_code=503,
            content={
                "alive": False,
                "error": str(e)
            }
        )


@router.get("/api/crm/metrics/summary")
async def crm_metrics_summary():
    """
    Get CRM metrics summary.
    
    Provides high-level metrics for monitoring dashboards.
    """
    try:
        from ..crm.repository import CommunicationRepository
        
        repository = CommunicationRepository()
        
        # Get metrics from last 24 hours
        metrics = await repository.get_analytics(
            time_range_hours=24
        )
        
        return {
            "timestamp": datetime.utcnow().isoformat(),
            "time_range_hours": 24,
            "metrics": metrics
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve CRM metrics: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="metrics_retrieval_failed",
                message=f"Failed to retrieve metrics: {str(e)}"
            ).dict()
        )


@router.get("/api/crm/alerts")
async def get_crm_alerts(
    severity: Optional[str] = Query(None, description="Filter by severity (critical, high, medium, low)")
):
    """
    Get active CRM alerts.
    
    Returns list of active alerts, optionally filtered by severity.
    """
    try:
        from ..crm.alerting_rules import get_alert_manager, AlertSeverity
        
        alert_manager = get_alert_manager()
        
        # Parse severity filter
        severity_filter = None
        if severity:
            try:
                severity_filter = AlertSeverity(severity.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="invalid_severity",
                        message=f"Invalid severity: {severity}. Must be one of: critical, high, medium, low"
                    ).dict()
                )
        
        # Get active alerts
        alerts = alert_manager.get_active_alerts(severity=severity_filter)
        
        return {
            "total_count": len(alerts),
            "severity_filter": severity,
            "alerts": [alert.to_dict() for alert in alerts]
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve CRM alerts: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="alerts_retrieval_failed",
                message=f"Failed to retrieve alerts: {str(e)}"
            ).dict()
        )


# CRM Analytics Endpoints

@router.get("/api/crm/analytics")
async def get_crm_analytics(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    channel: Optional[str] = Query(None, description="Filter by channel (email, sms, whatsapp)"),
    message_type: Optional[str] = Query(None, description="Filter by message type"),
    export_format: Optional[str] = Query(None, description="Export format (csv, pdf)")
):
    """
    Get comprehensive CRM analytics.
    
    Provides delivery rates, engagement metrics, channel performance,
    message type analysis, and engagement funnel data.
    
    Query Parameters:
    - start_date: Optional start date for filtering (ISO format)
    - end_date: Optional end date for filtering (ISO format)
    - channel: Optional channel filter (email, sms, whatsapp)
    - message_type: Optional message type filter
    - export_format: Optional export format (csv, pdf) - returns file download
    
    Returns:
    - JSON with comprehensive analytics data
    - Or file download if export_format is specified
    """
    try:
        from ..crm.analytics import get_analytics
        from ..crm.export import get_exporter
        from ..crm.models import MessageChannel, MessageType
        from fastapi.responses import Response
        
        logger.info(f"Retrieving CRM analytics from {start_date} to {end_date}")
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            try:
                start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="invalid_date",
                        message=f"Invalid start_date format: {start_date}. Use ISO format."
                    ).dict()
                )
        
        if end_date:
            try:
                end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="invalid_date",
                        message=f"Invalid end_date format: {end_date}. Use ISO format."
                    ).dict()
                )
        
        # Parse channel filter
        channel_filter = None
        if channel:
            try:
                channel_filter = MessageChannel(channel.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="invalid_channel",
                        message=f"Invalid channel: {channel}. Must be one of: email, sms, whatsapp"
                    ).dict()
                )
        
        # Parse message type filter
        message_type_filter = None
        if message_type:
            try:
                message_type_filter = MessageType(message_type.lower())
            except ValueError:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="invalid_message_type",
                        message=f"Invalid message_type: {message_type}"
                    ).dict()
                )
        
        # Get analytics
        analytics = get_analytics()
        analytics_data = analytics.get_comprehensive_analytics(start_dt, end_dt)
        
        # Handle export formats
        if export_format:
            exporter = get_exporter()
            
            if export_format.lower() == 'csv':
                csv_content = exporter.export_to_csv(analytics_data, 'comprehensive')
                filename = f"crm_analytics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
                
                return Response(
                    content=csv_content,
                    media_type="text/csv",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}"
                    }
                )
            
            elif export_format.lower() == 'pdf':
                pdf_content = exporter.export_to_pdf(analytics_data)
                filename = f"crm_analytics_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.pdf"
                
                return Response(
                    content=pdf_content,
                    media_type="application/pdf",
                    headers={
                        "Content-Disposition": f"attachment; filename={filename}"
                    }
                )
            
            else:
                raise HTTPException(
                    status_code=400,
                    detail=ErrorResponse(
                        error="invalid_export_format",
                        message=f"Invalid export_format: {export_format}. Must be 'csv' or 'pdf'"
                    ).dict()
                )
        
        # Return JSON response
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "analytics": analytics_data
        }
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Failed to retrieve CRM analytics: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="analytics_retrieval_failed",
                message=f"Failed to retrieve analytics: {str(e)}"
            ).dict()
        )


@router.get("/api/crm/analytics/channel-performance")
async def get_channel_performance(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    export_format: Optional[str] = Query(None, description="Export format (csv)")
):
    """Get channel performance comparison"""
    try:
        from ..crm.analytics import get_analytics
        from ..crm.export import get_exporter
        from fastapi.responses import Response
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get analytics
        analytics = get_analytics()
        channel_data = analytics.get_channel_performance(start_dt, end_dt)
        
        # Handle export
        if export_format and export_format.lower() == 'csv':
            exporter = get_exporter()
            csv_content = exporter.export_to_csv(channel_data, 'channel')
            filename = f"channel_performance_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "channel_performance": channel_data
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve channel performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="channel_performance_failed",
                message=f"Failed to retrieve channel performance: {str(e)}"
            ).dict()
        )


@router.get("/api/crm/analytics/message-type-performance")
async def get_message_type_performance(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)"),
    export_format: Optional[str] = Query(None, description="Export format (csv)")
):
    """Get message type performance analysis"""
    try:
        from ..crm.analytics import get_analytics
        from ..crm.export import get_exporter
        from fastapi.responses import Response
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get analytics
        analytics = get_analytics()
        message_type_data = analytics.get_message_type_performance(start_dt, end_dt)
        
        # Handle export
        if export_format and export_format.lower() == 'csv':
            exporter = get_exporter()
            csv_content = exporter.export_to_csv(message_type_data, 'message_type')
            filename = f"message_type_performance_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "message_type_performance": message_type_data
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve message type performance: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="message_type_performance_failed",
                message=f"Failed to retrieve message type performance: {str(e)}"
            ).dict()
        )


@router.get("/api/crm/analytics/timeline")
async def get_analytics_timeline(
    start_date: str = Query(..., description="Start date (ISO format)"),
    end_date: str = Query(..., description="End date (ISO format)"),
    granularity: str = Query('day', description="Time granularity (hour, day, week, month)"),
    export_format: Optional[str] = Query(None, description="Export format (csv)")
):
    """Get communication volume timeline"""
    try:
        from ..crm.analytics import get_analytics
        from ..crm.export import get_exporter
        from fastapi.responses import Response
        
        # Parse dates
        start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get analytics
        analytics = get_analytics()
        timeline_data = analytics.get_timeline_data(start_dt, end_dt, granularity)
        
        # Handle export
        if export_format and export_format.lower() == 'csv':
            exporter = get_exporter()
            csv_content = exporter.export_to_csv(timeline_data, 'timeline')
            filename = f"timeline_{datetime.utcnow().strftime('%Y%m%d_%H%M%S')}.csv"
            
            return Response(
                content=csv_content,
                media_type="text/csv",
                headers={"Content-Disposition": f"attachment; filename={filename}"}
            )
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "granularity": granularity,
            "timeline": timeline_data
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve timeline data: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="timeline_retrieval_failed",
                message=f"Failed to retrieve timeline: {str(e)}"
            ).dict()
        )


@router.get("/api/crm/analytics/engagement-funnel")
async def get_engagement_funnel(
    start_date: Optional[str] = Query(None, description="Start date (ISO format)"),
    end_date: Optional[str] = Query(None, description="End date (ISO format)")
):
    """Get engagement funnel metrics"""
    try:
        from ..crm.analytics import get_analytics
        
        # Parse dates
        start_dt = None
        end_dt = None
        if start_date:
            start_dt = datetime.fromisoformat(start_date.replace('Z', '+00:00'))
        if end_date:
            end_dt = datetime.fromisoformat(end_date.replace('Z', '+00:00'))
        
        # Get analytics
        analytics = get_analytics()
        funnel_data = analytics.get_engagement_funnel(start_dt, end_dt)
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "engagement_funnel": funnel_data
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve engagement funnel: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="funnel_retrieval_failed",
                message=f"Failed to retrieve engagement funnel: {str(e)}"
            ).dict()
        )


@router.get("/api/crm/analytics/preference-distribution")
async def get_preference_distribution():
    """Get client preference distribution"""
    try:
        from ..crm.analytics import get_analytics
        
        # Get analytics
        analytics = get_analytics()
        preference_data = analytics.get_preference_distribution()
        
        return {
            "success": True,
            "timestamp": datetime.utcnow().isoformat(),
            "preference_distribution": preference_data
        }
        
    except Exception as e:
        logger.error(f"Failed to retrieve preference distribution: {e}")
        raise HTTPException(
            status_code=500,
            detail=ErrorResponse(
                error="preference_distribution_failed",
                message=f"Failed to retrieve preference distribution: {str(e)}"
            ).dict()
        )
