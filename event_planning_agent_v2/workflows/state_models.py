"""
LangGraph workflow state models and type definitions for event planning.
Provides TypedDict definitions, validation utilities, and state transition logging.
"""

import json
import logging
from typing import Dict, Any, Optional, List, TypedDict, Union, Literal
from datetime import datetime
from uuid import uuid4
from pydantic import BaseModel, Field, validator
from enum import Enum

logger = logging.getLogger(__name__)


# Workflow status enumeration
class WorkflowStatus(str, Enum):
    """Enumeration of possible workflow statuses"""
    INITIALIZED = "initialized"
    RUNNING = "running"
    BUDGET_ALLOCATION = "budget_allocation"
    VENDOR_SOURCING = "vendor_sourcing"
    BEAM_SEARCH = "beam_search"
    CLIENT_SELECTION = "client_selection"
    BLUEPRINT_GENERATION = "blueprint_generation"
    COMPLETED = "completed"
    FAILED = "failed"
    PAUSED = "paused"
    RECOVERING = "recovering"


# Core state model as TypedDict for LangGraph compatibility
class EventPlanningState(TypedDict, total=False):
    """
    LangGraph state model for event planning workflow.
    Defines the complete state structure for workflow persistence and transitions.
    
    This TypedDict is used directly by LangGraph for state management and must
    maintain compatibility with LangGraph's state handling requirements.
    """
    # Core workflow identifiers
    plan_id: str
    client_request: Dict[str, Any]
    workflow_status: str
    iteration_count: int
    
    # Agent processing outputs
    budget_allocations: List[Dict[str, Any]]
    vendor_combinations: List[Dict[str, Any]]
    beam_candidates: List[Dict[str, Any]]
    timeline_data: Optional[Dict[str, Any]]
    
    # Task Management Agent output (NEW)
    extended_task_list: Optional[Dict[str, Any]]
    
    # CRM Communication tracking (NEW)
    communications: List[Dict[str, Any]]
    """
    List of communication results from CRM engine.
    
    Each communication record contains:
        - communication_id: Unique identifier
        - message_type: Type of message sent
        - channel_used: Channel used for communication
        - status: Current status (sent, delivered, opened, etc.)
        - sent_at: Timestamp when sent
        - metadata: Additional communication metadata
    """
    last_communication_at: Optional[str]
    """Timestamp of the last communication sent to the client."""
    pending_client_action: Optional[str]
    """Description of any pending action required from the client."""
    """
    Extended task list from Task Management Agent.
    
    Contains comprehensive task data with priorities, granularity, dependencies,
    timelines, vendor assignments, logistics verification, and conflict detection.
    
    Structure:
        {
            'tasks': List[Dict] - List of ExtendedTask objects serialized as dicts
            'processing_summary': Dict - Summary of task processing results
            'metadata': Dict - Additional metadata about task processing
        }
    
    This field is populated by the Task Management Agent after consolidating
    data from sub-agents (Prioritization, Granularity, Resource & Dependency)
    and processing through tools (Timeline, LLM, Vendor, Logistics, Conflict, Venue).
    
    The Blueprint Agent uses this field to generate the final event blueprint.
    """
    
    # Final workflow outputs
    selected_combination: Optional[Dict[str, Any]]
    final_blueprint: Optional[str]
    
    # Workflow configuration and metadata
    started_at: str
    last_updated: str
    beam_width: int
    max_iterations: int
    
    # Error handling and recovery
    error_count: int
    last_error: Optional[str]
    retry_count: int
    
    # State transition tracking
    state_transitions: List[Dict[str, Any]]
    current_node: Optional[str]
    next_node: Optional[str]


# Pydantic models for validation and serialization
class ClientRequest(BaseModel):
    """Validated client request model"""
    client_id: str = Field(..., description="Unique client identifier")
    event_type: str = Field(..., description="Type of event (wedding, corporate, etc.)")
    guest_count: int = Field(..., gt=0, description="Number of guests")
    budget: float = Field(..., gt=0, description="Total budget amount")
    date: str = Field(..., description="Event date in ISO format")
    location: str = Field(..., description="Event location")
    preferences: Dict[str, Any] = Field(default_factory=dict, description="Client preferences")
    requirements: Dict[str, Any] = Field(default_factory=dict, description="Specific requirements")
    
    @validator('date')
    def validate_date(cls, v):
        """Validate date format"""
        try:
            datetime.fromisoformat(v.replace('Z', '+00:00'))
            return v
        except ValueError:
            raise ValueError('Date must be in ISO format')


class BudgetAllocation(BaseModel):
    """Budget allocation model"""
    allocation_id: str = Field(default_factory=lambda: str(uuid4()))
    venue_budget: float = Field(..., ge=0)
    catering_budget: float = Field(..., ge=0)
    photography_budget: float = Field(..., ge=0)
    makeup_budget: float = Field(..., ge=0)
    total_allocated: float = Field(..., ge=0)
    allocation_strategy: str = Field(..., description="Strategy used for allocation")
    fitness_score: Optional[float] = Field(None, ge=0, le=1)


class VendorCombination(BaseModel):
    """Vendor combination model"""
    combination_id: str = Field(default_factory=lambda: str(uuid4()))
    venue: Optional[Dict[str, Any]] = None
    caterer: Optional[Dict[str, Any]] = None
    photographer: Optional[Dict[str, Any]] = None
    makeup_artist: Optional[Dict[str, Any]] = None
    total_cost: float = Field(..., ge=0)
    fitness_score: Optional[float] = Field(None, ge=0, le=1)
    compatibility_score: Optional[float] = Field(None, ge=0, le=1)
    feasibility_check: Optional[Dict[str, Any]] = None


class BeamCandidate(BaseModel):
    """Beam search candidate model"""
    candidate_id: str = Field(default_factory=lambda: str(uuid4()))
    budget_allocation: BudgetAllocation
    vendor_combination: VendorCombination
    combined_score: float = Field(..., ge=0, le=1)
    iteration_created: int = Field(..., ge=0)
    ranking: Optional[int] = Field(None, ge=1)


class StateTransition(BaseModel):
    """State transition tracking model"""
    transition_id: str = Field(default_factory=lambda: str(uuid4()))
    from_status: str
    to_status: str
    from_node: Optional[str] = None
    to_node: Optional[str] = None
    timestamp: str = Field(default_factory=lambda: datetime.utcnow().isoformat())
    trigger: str = Field(..., description="What triggered this transition")
    data: Optional[Dict[str, Any]] = Field(default_factory=dict)
    duration_ms: Optional[int] = Field(None, ge=0)


class WorkflowMetadata(BaseModel):
    """Workflow metadata model"""
    plan_id: str
    client_id: str
    started_at: str
    last_updated: str
    beam_width: int = Field(default=3, ge=1, le=10)
    max_iterations: int = Field(default=20, ge=1, le=100)
    error_count: int = Field(default=0, ge=0)
    retry_count: int = Field(default=0, ge=0)
    last_error: Optional[str] = None


class EventPlanningStateValidator(BaseModel):
    """
    Pydantic model for validating EventPlanningState.
    Provides comprehensive validation and serialization utilities.
    """
    # Core fields
    plan_id: str
    client_request: ClientRequest
    workflow_status: WorkflowStatus
    iteration_count: int = Field(default=0, ge=0)
    
    # Agent outputs
    budget_allocations: List[BudgetAllocation] = Field(default_factory=list)
    vendor_combinations: List[VendorCombination] = Field(default_factory=list)
    beam_candidates: List[BeamCandidate] = Field(default_factory=list)
    timeline_data: Optional[Dict[str, Any]] = None
    
    # Task Management Agent output
    extended_task_list: Optional[Dict[str, Any]] = Field(
        None,
        description="Extended task list from Task Management Agent with priorities, "
                    "dependencies, timelines, vendor assignments, and conflict detection"
    )
    
    # CRM Communication tracking
    communications: List[Dict[str, Any]] = Field(
        default_factory=list,
        description="List of communication results from CRM engine"
    )
    last_communication_at: Optional[str] = Field(
        None,
        description="Timestamp of the last communication sent to the client"
    )
    pending_client_action: Optional[str] = Field(
        None,
        description="Description of any pending action required from the client"
    )
    
    # Final outputs
    selected_combination: Optional[VendorCombination] = None
    final_blueprint: Optional[str] = None
    
    # Metadata
    metadata: WorkflowMetadata
    
    # State transitions
    state_transitions: List[StateTransition] = Field(default_factory=list)
    current_node: Optional[str] = None
    next_node: Optional[str] = None
    
    class Config:
        use_enum_values = True
        validate_assignment = True
    
    @validator('beam_candidates')
    def validate_beam_width(cls, v, values):
        """Ensure beam candidates don't exceed beam width"""
        if 'metadata' in values and len(v) > values['metadata'].beam_width:
            raise ValueError(f"Beam candidates exceed beam width of {values['metadata'].beam_width}")
        return v
    
    @validator('workflow_status')
    def validate_status_transition(cls, v, values):
        """Validate workflow status transitions"""
        # Add custom validation logic for valid status transitions
        return v
    
    def to_langgraph_state(self) -> EventPlanningState:
        """Convert to LangGraph-compatible TypedDict"""
        return EventPlanningState(
            plan_id=self.plan_id,
            client_request=self.client_request.dict(),
            workflow_status=self.workflow_status.value,
            iteration_count=self.iteration_count,
            budget_allocations=[ba.dict() for ba in self.budget_allocations],
            vendor_combinations=[vc.dict() for vc in self.vendor_combinations],
            beam_candidates=[bc.dict() for bc in self.beam_candidates],
            timeline_data=self.timeline_data,
            extended_task_list=self.extended_task_list,
            communications=self.communications,
            last_communication_at=self.last_communication_at,
            pending_client_action=self.pending_client_action,
            selected_combination=self.selected_combination.dict() if self.selected_combination else None,
            final_blueprint=self.final_blueprint,
            started_at=self.metadata.started_at,
            last_updated=self.metadata.last_updated,
            beam_width=self.metadata.beam_width,
            max_iterations=self.metadata.max_iterations,
            error_count=self.metadata.error_count,
            last_error=self.metadata.last_error,
            retry_count=self.metadata.retry_count,
            state_transitions=[st.dict() for st in self.state_transitions],
            current_node=self.current_node,
            next_node=self.next_node
        )
    
    @classmethod
    def from_langgraph_state(cls, state: EventPlanningState) -> 'EventPlanningStateValidator':
        """Create from LangGraph TypedDict state"""
        return cls(
            plan_id=state['plan_id'],
            client_request=ClientRequest(**state['client_request']),
            workflow_status=WorkflowStatus(state['workflow_status']),
            iteration_count=state.get('iteration_count', 0),
            budget_allocations=[BudgetAllocation(**ba) for ba in state.get('budget_allocations', [])],
            vendor_combinations=[VendorCombination(**vc) for vc in state.get('vendor_combinations', [])],
            beam_candidates=[BeamCandidate(**bc) for bc in state.get('beam_candidates', [])],
            timeline_data=state.get('timeline_data'),
            extended_task_list=state.get('extended_task_list'),
            communications=state.get('communications', []),
            last_communication_at=state.get('last_communication_at'),
            pending_client_action=state.get('pending_client_action'),
            selected_combination=VendorCombination(**state['selected_combination']) if state.get('selected_combination') else None,
            final_blueprint=state.get('final_blueprint'),
            metadata=WorkflowMetadata(
                plan_id=state['plan_id'],
                client_id=state['client_request'].get('client_id', 'unknown'),
                started_at=state.get('started_at', datetime.utcnow().isoformat()),
                last_updated=state.get('last_updated', datetime.utcnow().isoformat()),
                beam_width=state.get('beam_width', 3),
                max_iterations=state.get('max_iterations', 20),
                error_count=state.get('error_count', 0),
                retry_count=state.get('retry_count', 0),
                last_error=state.get('last_error')
            ),
            state_transitions=[StateTransition(**st) for st in state.get('state_transitions', [])],
            current_node=state.get('current_node'),
            next_node=state.get('next_node')
        )


# State validation utilities
class StateValidator:
    """Utilities for validating and serializing workflow state"""
    
    @staticmethod
    def validate_state(state: EventPlanningState) -> bool:
        """
        Validate EventPlanningState structure and data integrity
        
        Args:
            state: State to validate
            
        Returns:
            True if valid, False otherwise
        """
        try:
            # Use Pydantic validator for comprehensive validation
            validator = EventPlanningStateValidator.from_langgraph_state(state)
            return True
        except Exception as e:
            logger.error(f"State validation failed: {e}")
            return False
    
    @staticmethod
    def serialize_state(state: EventPlanningState) -> str:
        """
        Serialize state to JSON string
        
        Args:
            state: State to serialize
            
        Returns:
            JSON string representation
        """
        try:
            # Convert datetime objects and other non-serializable types
            serializable_state = {}
            for key, value in state.items():
                if isinstance(value, datetime):
                    serializable_state[key] = value.isoformat()
                else:
                    serializable_state[key] = value
            
            return json.dumps(serializable_state, indent=2, default=str)
        except Exception as e:
            logger.error(f"State serialization failed: {e}")
            return "{}"
    
    @staticmethod
    def deserialize_state(state_json: str) -> Optional[EventPlanningState]:
        """
        Deserialize state from JSON string
        
        Args:
            state_json: JSON string to deserialize
            
        Returns:
            EventPlanningState if successful, None otherwise
        """
        try:
            state_dict = json.loads(state_json)
            
            # Validate and return as EventPlanningState
            if StateValidator.validate_state(state_dict):
                return EventPlanningState(state_dict)
            else:
                return None
        except Exception as e:
            logger.error(f"State deserialization failed: {e}")
            return None


# State transition logging utilities
class StateTransitionLogger:
    """Utilities for logging state transitions and monitoring workflow progress"""
    
    def __init__(self):
        self.logger = logging.getLogger(f"{__name__}.StateTransitionLogger")
    
    def log_transition(
        self,
        state: EventPlanningState,
        from_status: str,
        to_status: str,
        trigger: str,
        from_node: Optional[str] = None,
        to_node: Optional[str] = None,
        additional_data: Optional[Dict[str, Any]] = None
    ) -> EventPlanningState:
        """
        Log a state transition and update the state
        
        Args:
            state: Current workflow state
            from_status: Previous status
            to_status: New status
            trigger: What triggered the transition
            from_node: Previous workflow node
            to_node: New workflow node
            additional_data: Additional transition data
            
        Returns:
            Updated state with transition logged
        """
        transition = StateTransition(
            from_status=from_status,
            to_status=to_status,
            from_node=from_node,
            to_node=to_node,
            trigger=trigger,
            data=additional_data or {}
        )
        
        # Add transition to state
        if 'state_transitions' not in state:
            state['state_transitions'] = []
        
        state['state_transitions'].append(transition.dict())
        state['workflow_status'] = to_status
        state['last_updated'] = datetime.utcnow().isoformat()
        
        if to_node:
            state['current_node'] = to_node
        
        # Log the transition
        self.logger.info(
            f"State transition: {from_status} -> {to_status} "
            f"(trigger: {trigger}, plan: {state.get('plan_id', 'unknown')})"
        )
        
        return state
    
    def log_node_entry(
        self,
        state: EventPlanningState,
        node_name: str,
        input_data: Optional[Dict[str, Any]] = None
    ) -> EventPlanningState:
        """
        Log entry into a workflow node
        
        Args:
            state: Current workflow state
            node_name: Name of the node being entered
            input_data: Input data for the node
            
        Returns:
            Updated state with node entry logged
        """
        return self.log_transition(
            state=state,
            from_status=state.get('workflow_status', 'unknown'),
            to_status=f"processing_{node_name}",
            trigger=f"entering_node_{node_name}",
            from_node=state.get('current_node'),
            to_node=node_name,
            additional_data={'input_data': input_data or {}}
        )
    
    def log_node_exit(
        self,
        state: EventPlanningState,
        node_name: str,
        output_data: Optional[Dict[str, Any]] = None,
        success: bool = True
    ) -> EventPlanningState:
        """
        Log exit from a workflow node
        
        Args:
            state: Current workflow state
            node_name: Name of the node being exited
            output_data: Output data from the node
            success: Whether the node completed successfully
            
        Returns:
            Updated state with node exit logged
        """
        status = f"completed_{node_name}" if success else f"failed_{node_name}"
        
        return self.log_transition(
            state=state,
            from_status=state.get('workflow_status', 'unknown'),
            to_status=status,
            trigger=f"exiting_node_{node_name}",
            from_node=node_name,
            to_node=state.get('next_node'),
            additional_data={
                'output_data': output_data or {},
                'success': success
            }
        )
    
    def get_transition_history(self, state: EventPlanningState) -> List[Dict[str, Any]]:
        """
        Get the complete transition history for a workflow
        
        Args:
            state: Workflow state
            
        Returns:
            List of state transitions
        """
        return state.get('state_transitions', [])
    
    def get_workflow_duration(self, state: EventPlanningState) -> Optional[float]:
        """
        Calculate total workflow duration in seconds
        
        Args:
            state: Workflow state
            
        Returns:
            Duration in seconds if calculable, None otherwise
        """
        try:
            started_at = state.get('started_at')
            last_updated = state.get('last_updated')
            
            if started_at and last_updated:
                start_time = datetime.fromisoformat(started_at.replace('Z', '+00:00'))
                end_time = datetime.fromisoformat(last_updated.replace('Z', '+00:00'))
                return (end_time - start_time).total_seconds()
            
            return None
        except Exception as e:
            self.logger.error(f"Failed to calculate workflow duration: {e}")
            return None


# Global instances
state_validator = StateValidator()
transition_logger = StateTransitionLogger()


# Convenience functions
def create_initial_state(
    client_request: Dict[str, Any],
    plan_id: Optional[str] = None,
    beam_width: int = 3,
    max_iterations: int = 20
) -> EventPlanningState:
    """
    Create initial workflow state
    
    Args:
        client_request: Client's event planning request
        plan_id: Optional plan ID, generates new if None
        beam_width: Beam search width
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
        'workflow_status': WorkflowStatus.INITIALIZED.value,
        'iteration_count': 0,
        'budget_allocations': [],
        'vendor_combinations': [],
        'beam_candidates': [],
        'timeline_data': None,
        'extended_task_list': None,
        'communications': [],
        'last_communication_at': None,
        'pending_client_action': None,
        'selected_combination': None,
        'final_blueprint': None,
        'started_at': now,
        'last_updated': now,
        'beam_width': beam_width,
        'max_iterations': max_iterations,
        'error_count': 0,
        'last_error': None,
        'retry_count': 0,
        'state_transitions': [],
        'current_node': None,
        'next_node': 'initialize'
    }
    
    # Log initial state creation
    transition_logger.log_transition(
        state=initial_state,
        from_status='none',
        to_status=WorkflowStatus.INITIALIZED.value,
        trigger='workflow_creation',
        additional_data={'client_id': client_request.get('client_id', 'unknown')}
    )
    
    return initial_state


def validate_state_transition(
    current_status: str,
    new_status: str
) -> bool:
    """
    Validate if a state transition is allowed
    
    Args:
        current_status: Current workflow status
        new_status: Proposed new status
        
    Returns:
        True if transition is valid, False otherwise
    """
    # Define valid state transitions
    valid_transitions = {
        WorkflowStatus.INITIALIZED: [WorkflowStatus.RUNNING, WorkflowStatus.FAILED],
        WorkflowStatus.RUNNING: [WorkflowStatus.BUDGET_ALLOCATION, WorkflowStatus.FAILED, WorkflowStatus.PAUSED],
        WorkflowStatus.BUDGET_ALLOCATION: [WorkflowStatus.VENDOR_SOURCING, WorkflowStatus.FAILED, WorkflowStatus.PAUSED],
        WorkflowStatus.VENDOR_SOURCING: [WorkflowStatus.BEAM_SEARCH, WorkflowStatus.FAILED, WorkflowStatus.PAUSED],
        WorkflowStatus.BEAM_SEARCH: [WorkflowStatus.VENDOR_SOURCING, WorkflowStatus.CLIENT_SELECTION, WorkflowStatus.FAILED, WorkflowStatus.PAUSED],
        WorkflowStatus.CLIENT_SELECTION: [WorkflowStatus.BLUEPRINT_GENERATION, WorkflowStatus.BEAM_SEARCH, WorkflowStatus.FAILED],
        WorkflowStatus.BLUEPRINT_GENERATION: [WorkflowStatus.COMPLETED, WorkflowStatus.FAILED],
        WorkflowStatus.PAUSED: [WorkflowStatus.RUNNING, WorkflowStatus.FAILED],
        WorkflowStatus.RECOVERING: [WorkflowStatus.RUNNING, WorkflowStatus.FAILED],
        WorkflowStatus.FAILED: [WorkflowStatus.RECOVERING],
        WorkflowStatus.COMPLETED: []  # Terminal state
    }
    
    try:
        current_enum = WorkflowStatus(current_status)
        new_enum = WorkflowStatus(new_status)
        
        return new_enum in valid_transitions.get(current_enum, [])
    except ValueError:
        # Invalid status values
        return False