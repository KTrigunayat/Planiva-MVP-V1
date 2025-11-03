"""
CRM Integration Helper for LangGraph Workflow

Provides helper functions to integrate CRM communications into workflow nodes.
Handles CRM orchestrator initialization and communication triggering.
"""

import logging
import asyncio
from typing import Dict, Any, Optional
from datetime import datetime, timezone

from ..crm.orchestrator import CRMAgentOrchestrator
from ..crm.strategy import CommunicationStrategyTool
from ..crm.email_sub_agent import EmailSubAgent
from ..crm.messaging_sub_agent import MessagingSubAgent
from ..crm.models import (
    MessageType,
    MessageChannel,
    UrgencyLevel,
    CommunicationRequest,
    CommunicationResult,
)
from .state_models import EventPlanningState

logger = logging.getLogger(__name__)


# Global CRM orchestrator instance (lazy initialization)
_crm_orchestrator: Optional[CRMAgentOrchestrator] = None


def get_crm_orchestrator() -> CRMAgentOrchestrator:
    """
    Get or create the global CRM orchestrator instance.
    
    Returns:
        CRMAgentOrchestrator instance
    """
    global _crm_orchestrator
    
    if _crm_orchestrator is None:
        logger.info("Initializing CRM orchestrator for workflow integration")
        
        # Initialize CRM components
        strategy_tool = CommunicationStrategyTool()
        email_agent = EmailSubAgent()
        messaging_agent = MessagingSubAgent()
        
        # Create orchestrator
        _crm_orchestrator = CRMAgentOrchestrator(
            strategy_tool=strategy_tool,
            email_agent=email_agent,
            messaging_agent=messaging_agent,
            repository=None  # Repository optional for now
        )
        
        logger.info("CRM orchestrator initialized successfully")
    
    return _crm_orchestrator


async def trigger_communication(
    state: EventPlanningState,
    message_type: MessageType,
    urgency: UrgencyLevel = UrgencyLevel.NORMAL,
    additional_context: Optional[Dict[str, Any]] = None
) -> EventPlanningState:
    """
    Trigger a CRM communication from a workflow node.
    
    This helper function:
    1. Extracts client information from state
    2. Builds communication context
    3. Sends communication via CRM orchestrator
    4. Updates state with communication result
    
    Args:
        state: Current workflow state
        message_type: Type of message to send
        urgency: Message urgency level
        additional_context: Additional context data for the message
        
    Returns:
        Updated state with communication result
    """
    try:
        # Extract client information
        client_request = state.get('client_request', {})
        plan_id = state.get('plan_id', 'unknown')
        client_id = client_request.get('client_id', 'unknown')
        
        # Build communication context
        context = {
            'client_name': client_request.get('client_name', 'Valued Client'),
            'client_email': client_request.get('email', ''),
            'client_phone': client_request.get('phone', ''),
            'recipient_email': client_request.get('email', ''),
            'recipient_phone': client_request.get('phone', ''),
            'event_type': client_request.get('event_type', 'event'),
            'event_date': client_request.get('date', 'TBD'),
            'guest_count': client_request.get('guest_count', 0),
            'budget': client_request.get('budget', 0),
            'location': client_request.get('location', 'TBD'),
            'plan_id': plan_id,
        }
        
        # Add additional context if provided
        if additional_context:
            context.update(additional_context)
        
        # Create communication request
        request = CommunicationRequest(
            plan_id=plan_id,
            client_id=client_id,
            message_type=message_type,
            context=context,
            urgency=urgency,
            preferred_channel=None  # Let strategy tool decide
        )
        
        # Get CRM orchestrator
        orchestrator = get_crm_orchestrator()
        
        # Send communication
        logger.info(
            f"Triggering {message_type.value} communication for plan {plan_id}"
        )
        
        result = await orchestrator.process_communication_request(request)
        
        # Update state with communication result
        if 'communications' not in state:
            state['communications'] = []
        
        communication_record = {
            'communication_id': result.communication_id,
            'message_type': message_type.value,
            'channel_used': result.channel_used.value,
            'status': result.status.value,
            'sent_at': result.sent_at.isoformat() if result.sent_at else None,
            'delivered_at': result.delivered_at.isoformat() if result.delivered_at else None,
            'error_message': result.error_message,
            'metadata': result.metadata or {}
        }
        
        state['communications'].append(communication_record)
        state['last_communication_at'] = datetime.now(timezone.utc).isoformat()
        
        # Log result
        if result.is_successful:
            logger.info(
                f"Communication sent successfully: "
                f"type={message_type.value}, "
                f"channel={result.channel_used.value}, "
                f"communication_id={result.communication_id}"
            )
        else:
            logger.error(
                f"Communication failed: "
                f"type={message_type.value}, "
                f"error={result.error_message}"
            )
        
        return state
        
    except Exception as e:
        logger.error(
            f"Error triggering communication: {e}",
            exc_info=True
        )
        
        # Don't fail the workflow on communication errors
        # Just log and continue
        return state


def trigger_communication_sync(
    state: EventPlanningState,
    message_type: MessageType,
    urgency: UrgencyLevel = UrgencyLevel.NORMAL,
    additional_context: Optional[Dict[str, Any]] = None
) -> EventPlanningState:
    """
    Synchronous wrapper for trigger_communication.
    
    This is needed because LangGraph nodes are synchronous functions.
    
    Args:
        state: Current workflow state
        message_type: Type of message to send
        urgency: Message urgency level
        additional_context: Additional context data for the message
        
    Returns:
        Updated state with communication result
    """
    try:
        # Run async function in event loop
        loop = asyncio.get_event_loop()
        if loop.is_running():
            # If loop is already running, create a new task
            # This shouldn't happen in normal workflow execution
            logger.warning("Event loop already running, communication may be delayed")
            return state
        else:
            # Run the async function
            return loop.run_until_complete(
                trigger_communication(state, message_type, urgency, additional_context)
            )
    except Exception as e:
        logger.error(
            f"Error in synchronous communication trigger: {e}",
            exc_info=True
        )
        return state


async def trigger_welcome_communication(state: EventPlanningState) -> EventPlanningState:
    """
    Trigger welcome communication after workflow initialization.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with communication result
    """
    return await trigger_communication(
        state=state,
        message_type=MessageType.WELCOME,
        urgency=UrgencyLevel.NORMAL,
        additional_context={
            'next_steps': 'We will analyze your requirements and create budget strategies.',
            'estimated_timeline': '24-48 hours'
        }
    )


async def trigger_budget_summary_communication(state: EventPlanningState) -> EventPlanningState:
    """
    Trigger budget summary communication after budget allocation.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with communication result
    """
    budget_allocations = state.get('budget_allocations', [])
    
    return await trigger_communication(
        state=state,
        message_type=MessageType.BUDGET_SUMMARY,
        urgency=UrgencyLevel.NORMAL,
        additional_context={
            'budget_allocations': budget_allocations,
            'allocation_count': len(budget_allocations)
        }
    )


async def trigger_vendor_options_communication(state: EventPlanningState) -> EventPlanningState:
    """
    Trigger vendor options communication after beam search presents options.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with communication result
    """
    beam_candidates = state.get('beam_candidates', [])
    
    # Set pending client action
    state['pending_client_action'] = 'select_vendor_combination'
    
    return await trigger_communication(
        state=state,
        message_type=MessageType.VENDOR_OPTIONS,
        urgency=UrgencyLevel.HIGH,
        additional_context={
            'vendor_combinations': beam_candidates,
            'combination_count': len(beam_candidates),
            'selection_required': True
        }
    )


async def trigger_selection_confirmation_communication(state: EventPlanningState) -> EventPlanningState:
    """
    Trigger selection confirmation communication after client selects vendors.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with communication result
    """
    selected_combination = state.get('selected_combination', {})
    
    # Clear pending client action
    state['pending_client_action'] = None
    
    return await trigger_communication(
        state=state,
        message_type=MessageType.SELECTION_CONFIRMATION,
        urgency=UrgencyLevel.NORMAL,
        additional_context={
            'selected_combination': selected_combination,
            'next_steps': 'We will now generate your detailed event blueprint.'
        }
    )


async def trigger_blueprint_delivery_communication(state: EventPlanningState) -> EventPlanningState:
    """
    Trigger blueprint delivery communication after blueprint generation.
    
    Args:
        state: Current workflow state
        
    Returns:
        Updated state with communication result
    """
    final_blueprint = state.get('final_blueprint', '')
    
    return await trigger_communication(
        state=state,
        message_type=MessageType.BLUEPRINT_DELIVERY,
        urgency=UrgencyLevel.HIGH,
        additional_context={
            'blueprint_ready': True,
            'blueprint_length': len(final_blueprint),
            'download_available': True
        }
    )


async def trigger_error_notification_communication(
    state: EventPlanningState,
    error_message: str
) -> EventPlanningState:
    """
    Trigger error notification communication when workflow encounters an error.
    
    Args:
        state: Current workflow state
        error_message: Error message to communicate
        
    Returns:
        Updated state with communication result
    """
    return await trigger_communication(
        state=state,
        message_type=MessageType.ERROR_NOTIFICATION,
        urgency=UrgencyLevel.CRITICAL,
        additional_context={
            'error_occurred': True,
            'error_message': error_message,
            'support_contact': 'support@planiva.com'
        }
    )


# Synchronous wrappers for workflow nodes
def trigger_welcome_communication_sync(state: EventPlanningState) -> EventPlanningState:
    """Synchronous wrapper for welcome communication."""
    return trigger_communication_sync(
        state, MessageType.WELCOME, UrgencyLevel.NORMAL,
        {'next_steps': 'We will analyze your requirements and create budget strategies.'}
    )


def trigger_budget_summary_communication_sync(state: EventPlanningState) -> EventPlanningState:
    """Synchronous wrapper for budget summary communication."""
    budget_allocations = state.get('budget_allocations', [])
    return trigger_communication_sync(
        state, MessageType.BUDGET_SUMMARY, UrgencyLevel.NORMAL,
        {'budget_allocations': budget_allocations, 'allocation_count': len(budget_allocations)}
    )


def trigger_vendor_options_communication_sync(state: EventPlanningState) -> EventPlanningState:
    """Synchronous wrapper for vendor options communication."""
    beam_candidates = state.get('beam_candidates', [])
    state['pending_client_action'] = 'select_vendor_combination'
    return trigger_communication_sync(
        state, MessageType.VENDOR_OPTIONS, UrgencyLevel.HIGH,
        {'vendor_combinations': beam_candidates, 'combination_count': len(beam_candidates)}
    )


def trigger_selection_confirmation_communication_sync(state: EventPlanningState) -> EventPlanningState:
    """Synchronous wrapper for selection confirmation communication."""
    selected_combination = state.get('selected_combination', {})
    state['pending_client_action'] = None
    return trigger_communication_sync(
        state, MessageType.SELECTION_CONFIRMATION, UrgencyLevel.NORMAL,
        {'selected_combination': selected_combination}
    )


def trigger_blueprint_delivery_communication_sync(state: EventPlanningState) -> EventPlanningState:
    """Synchronous wrapper for blueprint delivery communication."""
    final_blueprint = state.get('final_blueprint', '')
    return trigger_communication_sync(
        state, MessageType.BLUEPRINT_DELIVERY, UrgencyLevel.HIGH,
        {'blueprint_ready': True, 'blueprint_length': len(final_blueprint)}
    )


def trigger_error_notification_communication_sync(
    state: EventPlanningState,
    error_message: str
) -> EventPlanningState:
    """Synchronous wrapper for error notification communication."""
    return trigger_communication_sync(
        state, MessageType.ERROR_NOTIFICATION, UrgencyLevel.CRITICAL,
        {'error_occurred': True, 'error_message': error_message}
    )
