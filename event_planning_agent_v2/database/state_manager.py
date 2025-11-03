"""
LangGraph state persistence layer for workflow checkpointing and state management.
Provides state serialization, persistence, and recovery for event planning workflows.
"""

import json
import logging
from typing import Dict, Any, Optional, List, TypedDict, Union
from datetime import datetime
from uuid import UUID, uuid4
from sqlalchemy import select, update, delete
from sqlalchemy.exc import SQLAlchemyError

from .connection import get_sync_session, get_async_session
from .models import EventPlan, AgentPerformance, WorkflowMetrics
from ..config.settings import get_settings

logger = logging.getLogger(__name__)


class EventPlanningState(TypedDict, total=False):
    """
    LangGraph state model for event planning workflow.
    Defines the complete state structure for workflow persistence.
    """
    # Core workflow data
    plan_id: str
    client_request: Dict[str, Any]
    workflow_status: str
    iteration_count: int
    
    # Agent outputs
    budget_allocations: List[Dict[str, Any]]
    vendor_combinations: List[Dict[str, Any]]
    beam_candidates: List[Dict[str, Any]]
    timeline_data: Optional[Dict[str, Any]]
    
    # Final outputs
    selected_combination: Optional[Dict[str, Any]]
    final_blueprint: Optional[str]
    
    # Workflow metadata
    started_at: str
    last_updated: str
    beam_width: int
    max_iterations: int
    
    # Error handling
    error_count: int
    last_error: Optional[str]
    retry_count: int


class WorkflowStateManager:
    """
    Manages LangGraph workflow state persistence and recovery.
    Handles state serialization, checkpointing, and recovery operations.
    """
    
    def __init__(self):
        self.settings = get_settings()
        self.max_beam_history = getattr(self.settings, 'max_beam_history_size', 100)
        self.checkpoint_interval = getattr(self.settings, 'state_checkpoint_interval', 5)  # Save every N iterations
    
    def create_workflow_state(
        self,
        client_request: Dict[str, Any],
        plan_id: Optional[str] = None,
        beam_width: int = 3,
        max_iterations: int = 20
    ) -> EventPlanningState:
        """
        Create initial workflow state for a new planning session
        
        Args:
            client_request: Client's event planning request
            plan_id: Optional existing plan ID, generates new if None
            beam_width: Beam search width (default 3)
            max_iterations: Maximum workflow iterations
        
        Returns:
            Initial EventPlanningState
        """
        if plan_id is None:
            plan_id = str(uuid4())
        
        now = datetime.utcnow().isoformat()
        
        initial_state: EventPlanningState = {
            'plan_id': plan_id,
            'client_request': client_request,
            'workflow_status': 'initialized',
            'iteration_count': 0,
            'budget_allocations': [],
            'vendor_combinations': [],
            'beam_candidates': [],
            'timeline_data': None,
            'selected_combination': None,
            'final_blueprint': None,
            'started_at': now,
            'last_updated': now,
            'beam_width': beam_width,
            'max_iterations': max_iterations,
            'error_count': 0,
            'last_error': None,
            'retry_count': 0
        }
        
        # Persist initial state
        self.save_workflow_state(initial_state)
        
        logger.info(f"Created new workflow state for plan {plan_id}")
        return initial_state
    
    def save_workflow_state(self, state: EventPlanningState) -> bool:
        """
        Save workflow state to database with checkpointing
        
        Args:
            state: Current workflow state
        
        Returns:
            True if save successful, False otherwise
        """
        try:
            plan_id = UUID(state['plan_id'])
            state['last_updated'] = datetime.utcnow().isoformat()
            
            with get_sync_session() as session:
                # Check if event plan exists
                existing_plan = session.get(EventPlan, plan_id)
                
                if existing_plan:
                    # Update existing plan
                    existing_plan.workflow_state = state
                    existing_plan.status = state['workflow_status']
                    existing_plan.updated_at = datetime.utcnow()
                    
                    # Update beam history if we have beam candidates
                    if state.get('beam_candidates'):
                        self._update_beam_history(existing_plan, state)
                    
                    # Update final outputs if available
                    if state.get('selected_combination'):
                        existing_plan.selected_combination = state['selected_combination']
                    
                    if state.get('final_blueprint'):
                        existing_plan.final_blueprint = state['final_blueprint']
                
                else:
                    # Create new event plan
                    new_plan = EventPlan(
                        plan_id=plan_id,
                        client_id=state['client_request'].get('client_id', 'unknown'),
                        status=state['workflow_status'],
                        plan_data=state['client_request'],
                        workflow_state=state,
                        beam_history={'iterations': []},
                        agent_logs={'logs': []},
                        selected_combination=state.get('selected_combination'),
                        final_blueprint=state.get('final_blueprint')
                    )
                    session.add(new_plan)
                
                session.commit()
                logger.debug(f"Saved workflow state for plan {plan_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save workflow state: {e}")
            return False
    
    def load_workflow_state(self, plan_id: str) -> Optional[EventPlanningState]:
        """
        Load workflow state from database
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            EventPlanningState if found, None otherwise
        """
        try:
            plan_uuid = UUID(plan_id)
            
            with get_sync_session() as session:
                event_plan = session.get(EventPlan, plan_uuid)
                
                if event_plan and event_plan.workflow_state:
                    state = EventPlanningState(event_plan.workflow_state)
                    logger.debug(f"Loaded workflow state for plan {plan_id}")
                    return state
                else:
                    logger.warning(f"No workflow state found for plan {plan_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to load workflow state for plan {plan_id}: {e}")
            return None
    
    def update_workflow_status(self, plan_id: str, status: str, error_message: Optional[str] = None) -> bool:
        """
        Update workflow status and optionally record error
        
        Args:
            plan_id: Plan identifier
            status: New workflow status
            error_message: Optional error message
        
        Returns:
            True if update successful, False otherwise
        """
        try:
            state = self.load_workflow_state(plan_id)
            if not state:
                return False
            
            state['workflow_status'] = status
            state['last_updated'] = datetime.utcnow().isoformat()
            
            if error_message:
                state['last_error'] = error_message
                state['error_count'] = state.get('error_count', 0) + 1
            
            return self.save_workflow_state(state)
            
        except Exception as e:
            logger.error(f"Failed to update workflow status: {e}")
            return False
    
    def checkpoint_workflow(self, state: EventPlanningState) -> bool:
        """
        Create workflow checkpoint for recovery purposes
        
        Args:
            state: Current workflow state
        
        Returns:
            True if checkpoint successful, False otherwise
        """
        # Only checkpoint at specified intervals or on important state changes
        iteration = state.get('iteration_count', 0)
        
        should_checkpoint = (
            iteration % self.checkpoint_interval == 0 or
            state.get('workflow_status') in ['completed', 'failed', 'paused'] or
            state.get('selected_combination') is not None
        )
        
        if should_checkpoint:
            return self.save_workflow_state(state)
        
        return True  # No checkpoint needed
    
    def _update_beam_history(self, event_plan: EventPlan, state: EventPlanningState):
        """Update beam search history with current iteration data"""
        if not event_plan.beam_history:
            event_plan.beam_history = {'iterations': []}
        
        # Add current iteration to history
        iteration_data = {
            'iteration': state.get('iteration_count', 0),
            'timestamp': datetime.utcnow().isoformat(),
            'beam_candidates': state.get('beam_candidates', []),
            'status': state.get('workflow_status', 'unknown')
        }
        
        event_plan.beam_history['iterations'].append(iteration_data)
        
        # Limit history size to prevent excessive growth
        if len(event_plan.beam_history['iterations']) > self.max_beam_history:
            event_plan.beam_history['iterations'] = event_plan.beam_history['iterations'][-self.max_beam_history:]
    
    def get_beam_history(self, plan_id: str) -> List[Dict[str, Any]]:
        """
        Get beam search history for a plan
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            List of beam search iterations
        """
        try:
            plan_uuid = UUID(plan_id)
            
            with get_sync_session() as session:
                event_plan = session.get(EventPlan, plan_uuid)
                
                if event_plan and event_plan.beam_history:
                    return event_plan.beam_history.get('iterations', [])
                else:
                    return []
                    
        except Exception as e:
            logger.error(f"Failed to get beam history for plan {plan_id}: {e}")
            return []
    
    def recover_workflow_state(self, plan_id: str) -> Optional[EventPlanningState]:
        """
        Recover workflow state from last checkpoint
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            Recovered EventPlanningState if available, None otherwise
        """
        state = self.load_workflow_state(plan_id)
        
        if state:
            # Reset error state for recovery
            state['last_error'] = None
            state['retry_count'] = state.get('retry_count', 0) + 1
            
            # Update status to indicate recovery
            if state['workflow_status'] == 'failed':
                state['workflow_status'] = 'recovering'
            
            logger.info(f"Recovered workflow state for plan {plan_id} (retry #{state['retry_count']})")
            
            # Save recovery state
            self.save_workflow_state(state)
            
        return state
    
    def delete_workflow_state(self, plan_id: str) -> bool:
        """
        Delete workflow state and associated data
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            True if deletion successful, False otherwise
        """
        try:
            plan_uuid = UUID(plan_id)
            
            with get_sync_session() as session:
                # Delete associated performance and metrics data
                session.execute(delete(AgentPerformance).where(AgentPerformance.plan_id == plan_uuid))
                session.execute(delete(WorkflowMetrics).where(WorkflowMetrics.plan_id == plan_uuid))
                
                # Delete event plan
                session.execute(delete(EventPlan).where(EventPlan.plan_id == plan_uuid))
                
                session.commit()
                logger.info(f"Deleted workflow state for plan {plan_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to delete workflow state for plan {plan_id}: {e}")
            return False
    
    def list_active_workflows(self) -> List[Dict[str, Any]]:
        """
        List all active workflow states
        
        Returns:
            List of active workflow summaries
        """
        try:
            with get_sync_session() as session:
                result = session.execute(
                    select(EventPlan).where(
                        EventPlan.status.in_(['initialized', 'running', 'paused', 'recovering'])
                    )
                ).scalars().all()
                
                workflows = []
                for plan in result:
                    workflow_info = {
                        'plan_id': str(plan.plan_id),
                        'client_id': plan.client_id,
                        'status': plan.status,
                        'created_at': plan.created_at.isoformat() if plan.created_at else None,
                        'updated_at': plan.updated_at.isoformat() if plan.updated_at else None,
                    }
                    
                    # Add workflow state info if available
                    if plan.workflow_state:
                        workflow_info.update({
                            'iteration_count': plan.workflow_state.get('iteration_count', 0),
                            'error_count': plan.workflow_state.get('error_count', 0),
                            'beam_width': plan.workflow_state.get('beam_width', 3)
                        })
                    
                    workflows.append(workflow_info)
                
                return workflows
                
        except Exception as e:
            logger.error(f"Failed to list active workflows: {e}")
            return []


# Global state manager instance
_state_manager: Optional[WorkflowStateManager] = None


def get_state_manager() -> WorkflowStateManager:
    """Get global workflow state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = WorkflowStateManager()
    return _state_manager


# Convenience functions
def create_workflow_state(
    client_request: Dict[str, Any],
    plan_id: Optional[str] = None,
    beam_width: int = 3,
    max_iterations: int = 20
) -> EventPlanningState:
    """Create new workflow state"""
    return get_state_manager().create_workflow_state(client_request, plan_id, beam_width, max_iterations)


def save_workflow_state(state: EventPlanningState) -> bool:
    """Save workflow state to database"""
    return get_state_manager().save_workflow_state(state)


def load_workflow_state(plan_id: str) -> Optional[EventPlanningState]:
    """Load workflow state from database"""
    return get_state_manager().load_workflow_state(plan_id)


def checkpoint_workflow(state: EventPlanningState) -> bool:
    """Create workflow checkpoint"""
    return get_state_manager().checkpoint_workflow(state)


def recover_workflow_state(plan_id: str) -> Optional[EventPlanningState]:
    """Recover workflow state from checkpoint"""
    return get_state_manager().recover_workflow_state(plan_id)


class PlanManager:
    """
    Manages event plan data for API operations.
    Provides CRUD operations for event plans with proper serialization.
    """
    
    def __init__(self):
        self.settings = get_settings()
    
    def save_plan(self, plan_data: Dict[str, Any]) -> bool:
        """
        Save event plan data
        
        Args:
            plan_data: Plan data dictionary
        
        Returns:
            True if save successful, False otherwise
        """
        try:
            plan_id = UUID(plan_data['plan_id'])
            
            with get_sync_session() as session:
                existing_plan = session.get(EventPlan, plan_id)
                
                if existing_plan:
                    # Update existing plan
                    existing_plan.status = plan_data.get('status', existing_plan.status)
                    existing_plan.plan_data = plan_data.get('client_request', existing_plan.plan_data)
                    existing_plan.selected_combination = plan_data.get('selected_combination')
                    existing_plan.final_blueprint = plan_data.get('final_blueprint')
                    existing_plan.updated_at = datetime.utcnow()
                    
                    # Store additional metadata
                    if 'combinations' in plan_data:
                        if not existing_plan.workflow_state:
                            existing_plan.workflow_state = {}
                        existing_plan.workflow_state['beam_candidates'] = plan_data['combinations']
                    
                else:
                    # Create new plan
                    new_plan = EventPlan(
                        plan_id=plan_id,
                        client_id=plan_data.get('client_name', 'unknown'),
                        status=plan_data.get('status', 'pending'),
                        plan_data=plan_data.get('client_request', {}),
                        workflow_state={'beam_candidates': plan_data.get('combinations', [])},
                        beam_history={'iterations': []},
                        agent_logs={'logs': []},
                        selected_combination=plan_data.get('selected_combination'),
                        final_blueprint=plan_data.get('final_blueprint'),
                        created_at=datetime.utcnow(),
                        updated_at=datetime.utcnow()
                    )
                    session.add(new_plan)
                
                session.commit()
                logger.debug(f"Saved plan data for {plan_id}")
                return True
                
        except Exception as e:
            logger.error(f"Failed to save plan data: {e}")
            return False
    
    def load_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """
        Load event plan data
        
        Args:
            plan_id: Plan identifier
        
        Returns:
            Plan data dictionary if found, None otherwise
        """
        try:
            plan_uuid = UUID(plan_id)
            
            with get_sync_session() as session:
                event_plan = session.get(EventPlan, plan_uuid)
                
                if event_plan:
                    plan_data = {
                        'plan_id': str(event_plan.plan_id),
                        'status': event_plan.status,
                        'client_name': event_plan.client_id,
                        'client_request': event_plan.plan_data or {},
                        'combinations': [],
                        'selected_combination': event_plan.selected_combination,
                        'final_blueprint': event_plan.final_blueprint,
                        'created_at': event_plan.created_at,
                        'updated_at': event_plan.updated_at
                    }
                    
                    # Extract combinations from workflow state
                    if event_plan.workflow_state and 'beam_candidates' in event_plan.workflow_state:
                        plan_data['combinations'] = event_plan.workflow_state['beam_candidates']
                    
                    logger.debug(f"Loaded plan data for {plan_id}")
                    return plan_data
                else:
                    logger.warning(f"No plan found for {plan_id}")
                    return None
                    
        except Exception as e:
            logger.error(f"Failed to load plan data for {plan_id}: {e}")
            return None
    
    def list_plans(
        self,
        page: int = 1,
        page_size: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """
        List event plans with pagination and filtering
        
        Args:
            page: Page number (1-based)
            page_size: Number of items per page
            filters: Optional filters (status, client_name, etc.)
        
        Returns:
            Tuple of (plans_list, total_count)
        """
        try:
            with get_sync_session() as session:
                # Build query
                query = select(EventPlan)
                
                # Apply filters
                if filters:
                    if 'status' in filters:
                        query = query.where(EventPlan.status == filters['status'])
                    if 'client_name' in filters:
                        query = query.where(EventPlan.client_id.ilike(f"%{filters['client_name']}%"))
                
                # Get total count
                count_query = select(EventPlan.plan_id)
                if filters:
                    if 'status' in filters:
                        count_query = count_query.where(EventPlan.status == filters['status'])
                    if 'client_name' in filters:
                        count_query = count_query.where(EventPlan.client_id.ilike(f"%{filters['client_name']}%"))
                
                total_count = len(session.execute(count_query).scalars().all())
                
                # Apply pagination
                offset = (page - 1) * page_size
                query = query.offset(offset).limit(page_size)
                
                # Order by creation date (newest first)
                query = query.order_by(EventPlan.created_at.desc())
                
                # Execute query
                result = session.execute(query).scalars().all()
                
                # Convert to plan data format
                plans = []
                for event_plan in result:
                    plan_data = {
                        'plan_id': str(event_plan.plan_id),
                        'status': event_plan.status,
                        'client_name': event_plan.client_id,
                        'client_request': event_plan.plan_data or {},
                        'combinations': [],
                        'selected_combination': event_plan.selected_combination,
                        'final_blueprint': event_plan.final_blueprint,
                        'created_at': event_plan.created_at,
                        'updated_at': event_plan.updated_at
                    }
                    
                    # Extract combinations from workflow state
                    if event_plan.workflow_state and 'beam_candidates' in event_plan.workflow_state:
                        plan_data['combinations'] = event_plan.workflow_state['beam_candidates']
                    
                    plans.append(plan_data)
                
                logger.debug(f"Listed {len(plans)} plans (page {page}, total {total_count})")
                return plans, total_count
                
        except Exception as e:
            logger.error(f"Failed to list plans: {e}")
            return [], 0
    
    def health_check(self) -> bool:
        """
        Check database connectivity
        
        Returns:
            True if database is accessible, False otherwise
        """
        try:
            with get_sync_session() as session:
                # Simple query to test connectivity
                session.execute(select(EventPlan.plan_id).limit(1))
                return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# Extend state manager with plan management
class ExtendedStateManager(WorkflowStateManager):
    """Extended state manager with plan management capabilities"""
    
    def __init__(self):
        super().__init__()
        self.plan_manager = PlanManager()
    
    def save_plan(self, plan_data: Dict[str, Any]) -> bool:
        """Save event plan data"""
        return self.plan_manager.save_plan(plan_data)
    
    def load_plan(self, plan_id: str) -> Optional[Dict[str, Any]]:
        """Load event plan data"""
        return self.plan_manager.load_plan(plan_id)
    
    def list_plans(
        self,
        page: int = 1,
        page_size: int = 10,
        filters: Optional[Dict[str, Any]] = None
    ) -> tuple[List[Dict[str, Any]], int]:
        """List event plans with pagination"""
        return self.plan_manager.list_plans(page, page_size, filters)
    
    def health_check(self) -> bool:
        """Check database connectivity"""
        return self.plan_manager.health_check()


# Update global state manager to use extended version
def get_state_manager() -> ExtendedStateManager:
    """Get global extended state manager instance"""
    global _state_manager
    if _state_manager is None:
        _state_manager = ExtendedStateManager()
    return _state_manager