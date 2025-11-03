"""
Integration tests for CRM communication triggers in LangGraph workflow.

Tests end-to-end communication flow from each workflow node and verifies
that workflow state is properly updated after communications.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, AsyncMock
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional

# Import CRM models directly
from event_planning_agent_v2.crm.models import (
    MessageType,
    MessageChannel,
    CommunicationStatus,
    CommunicationResult,
)


@pytest.fixture
def sample_client_request():
    """Sample client request for testing."""
    return {
        'client_id': 'test_client_123',
        'client_name': 'John Doe',
        'email': 'john.doe@example.com',
        'phone': '+1234567890',
        'event_type': 'wedding',
        'guest_count': 150,
        'budget': 50000.0,
        'date': '2025-12-15',
        'location': 'San Francisco, CA',
        'preferences': {'style': 'modern', 'cuisine': 'italian'}
    }


@pytest.fixture
def initial_state(sample_client_request):
    """Create initial workflow state for testing."""
    return {
        'plan_id': 'test_plan_123',
        'client_request': sample_client_request,
        'workflow_status': 'initialized',
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
        'started_at': datetime.now(timezone.utc).isoformat(),
        'last_updated': datetime.now(timezone.utc).isoformat(),
        'beam_width': 3,
        'max_iterations': 20,
        'error_count': 0,
        'last_error': None,
        'retry_count': 0,
        'state_transitions': [],
        'current_node': None,
        'next_node': 'initialize'
    }


@pytest.fixture
def mock_crm_result():
    """Mock successful CRM communication result."""
    return CommunicationResult(
        communication_id='comm_123',
        status=CommunicationStatus.DELIVERED,
        channel_used=MessageChannel.EMAIL,
        sent_at=datetime.now(timezone.utc),
        delivered_at=datetime.now(timezone.utc),
        error_message=None,
        metadata={'test': True}
    )


class TestWelcomeCommunication:
    """Test welcome communication trigger from initialize_planning node."""
    
    @pytest.mark.asyncio
    async def test_welcome_communication_success(self, initial_state, mock_crm_result):
        """Test successful welcome communication trigger."""
        # Import here to avoid circular imports
        from event_planning_agent_v2.workflows.crm_integration import trigger_welcome_communication
        
        with patch('event_planning_agent_v2.workflows.crm_integration.get_crm_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_communication_request = AsyncMock(return_value=mock_crm_result)
            mock_get_orch.return_value = mock_orchestrator
            
            # Trigger welcome communication
            updated_state = await trigger_welcome_communication(initial_state)
            
            # Verify communication was triggered
            assert mock_orchestrator.process_communication_request.called
            call_args = mock_orchestrator.process_communication_request.call_args[0][0]
            assert call_args.message_type == MessageType.WELCOME
            assert call_args.plan_id == 'test_plan_123'
            assert call_args.client_id == 'test_client_123'
            
            # Verify state was updated
            assert 'communications' in updated_state
            assert len(updated_state['communications']) == 1
            
            comm = updated_state['communications'][0]
            assert comm['communication_id'] == 'comm_123'
            assert comm['message_type'] == MessageType.WELCOME.value
            assert comm['channel_used'] == MessageChannel.EMAIL.value
            assert comm['status'] == CommunicationStatus.DELIVERED.value
            
            # Verify last_communication_at was set
            assert updated_state['last_communication_at'] is not None
    
    @pytest.mark.asyncio
    async def test_welcome_communication_failure_doesnt_break_workflow(self, initial_state):
        """Test that communication failure doesn't break workflow."""
        from event_planning_agent_v2.workflows.crm_integration import trigger_welcome_communication
        
        with patch('event_planning_agent_v2.workflows.crm_integration.get_crm_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_communication_request = AsyncMock(
                side_effect=Exception("Communication failed")
            )
            mock_get_orch.return_value = mock_orchestrator
            
            # Trigger welcome communication (should not raise exception)
            updated_state = await trigger_welcome_communication(initial_state)
            
            # Verify state is still valid (workflow continues)
            assert updated_state['plan_id'] == 'test_plan_123'
            assert updated_state['workflow_status'] == 'initialized'


class TestBudgetSummaryCommunication:
    """Test budget summary communication trigger from budget_allocation_node."""
    
    @pytest.mark.asyncio
    async def test_budget_summary_communication_success(self, initial_state, mock_crm_result):
        """Test successful budget summary communication trigger."""
        from event_planning_agent_v2.workflows.crm_integration import trigger_budget_summary_communication
        
        # Add budget allocations to state
        initial_state['budget_allocations'] = [
            {
                'allocation_id': 'alloc_1',
                'strategy': 'balanced',
                'venue_budget': 20000,
                'catering_budget': 20000,
                'photography_budget': 7500,
                'makeup_budget': 2500,
                'total_allocated': 50000
            },
            {
                'allocation_id': 'alloc_2',
                'strategy': 'venue_focused',
                'venue_budget': 25000,
                'catering_budget': 15000,
                'photography_budget': 7500,
                'makeup_budget': 2500,
                'total_allocated': 50000
            }
        ]
        
        with patch('event_planning_agent_v2.workflows.crm_integration.get_crm_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_communication_request = AsyncMock(return_value=mock_crm_result)
            mock_get_orch.return_value = mock_orchestrator
            
            # Trigger budget summary communication
            updated_state = await trigger_budget_summary_communication(initial_state)
            
            # Verify communication was triggered with budget data
            assert mock_orchestrator.process_communication_request.called
            call_args = mock_orchestrator.process_communication_request.call_args[0][0]
            assert call_args.message_type == MessageType.BUDGET_SUMMARY
            assert 'budget_allocations' in call_args.context
            assert call_args.context['allocation_count'] == 2
            
            # Verify state was updated
            assert len(updated_state['communications']) == 1
            assert updated_state['communications'][0]['message_type'] == MessageType.BUDGET_SUMMARY.value


class TestVendorOptionsCommunication:
    """Test vendor options communication trigger from client_selection node."""
    
    @pytest.mark.asyncio
    async def test_vendor_options_communication_success(self, initial_state, mock_crm_result):
        """Test successful vendor options communication trigger."""
        from event_planning_agent_v2.workflows.crm_integration import trigger_vendor_options_communication
        
        # Add beam candidates to state
        initial_state['beam_candidates'] = [
            {
                'combination_id': 'combo_1',
                'rank': 1,
                'fitness_score': 0.95,
                'total_cost': 48000,
                'vendors': {
                    'venue': {'name': 'Grand Hall', 'cost': 20000},
                    'caterer': {'name': 'Gourmet Catering', 'cost': 18000},
                    'photographer': {'name': 'Pro Photos', 'cost': 7500},
                    'makeup_artist': {'name': 'Beauty Studio', 'cost': 2500}
                }
            },
            {
                'combination_id': 'combo_2',
                'rank': 2,
                'fitness_score': 0.92,
                'total_cost': 49500,
                'vendors': {
                    'venue': {'name': 'Elegant Venue', 'cost': 22000},
                    'caterer': {'name': 'Fine Dining', 'cost': 17000},
                    'photographer': {'name': 'Photo Masters', 'cost': 8000},
                    'makeup_artist': {'name': 'Glam Squad', 'cost': 2500}
                }
            }
        ]
        
        with patch('event_planning_agent_v2.workflows.crm_integration.get_crm_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_communication_request = AsyncMock(return_value=mock_crm_result)
            mock_get_orch.return_value = mock_orchestrator
            
            # Trigger vendor options communication
            updated_state = await trigger_vendor_options_communication(initial_state)
            
            # Verify communication was triggered with vendor data
            assert mock_orchestrator.process_communication_request.called
            call_args = mock_orchestrator.process_communication_request.call_args[0][0]
            assert call_args.message_type == MessageType.VENDOR_OPTIONS
            assert 'vendor_combinations' in call_args.context
            assert call_args.context['combination_count'] == 2
            assert call_args.context['selection_required'] is True
            
            # Verify pending client action was set
            assert updated_state['pending_client_action'] == 'select_vendor_combination'
            
            # Verify state was updated
            assert len(updated_state['communications']) == 1
            assert updated_state['communications'][0]['message_type'] == MessageType.VENDOR_OPTIONS.value


class TestSelectionConfirmationCommunication:
    """Test selection confirmation communication trigger."""
    
    @pytest.mark.asyncio
    async def test_selection_confirmation_communication_success(self, initial_state, mock_crm_result):
        """Test successful selection confirmation communication trigger."""
        from event_planning_agent_v2.workflows.crm_integration import trigger_selection_confirmation_communication
        
        # Add selected combination to state
        initial_state['selected_combination'] = {
            'combination_id': 'combo_1',
            'rank': 1,
            'fitness_score': 0.95,
            'total_cost': 48000,
            'vendors': {
                'venue': {'name': 'Grand Hall', 'cost': 20000},
                'caterer': {'name': 'Gourmet Catering', 'cost': 18000},
                'photographer': {'name': 'Pro Photos', 'cost': 7500},
                'makeup_artist': {'name': 'Beauty Studio', 'cost': 2500}
            }
        }
        initial_state['pending_client_action'] = 'select_vendor_combination'
        
        with patch('event_planning_agent_v2.workflows.crm_integration.get_crm_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_communication_request = AsyncMock(return_value=mock_crm_result)
            mock_get_orch.return_value = mock_orchestrator
            
            # Trigger selection confirmation communication
            updated_state = await trigger_selection_confirmation_communication(initial_state)
            
            # Verify communication was triggered with selection data
            assert mock_orchestrator.process_communication_request.called
            call_args = mock_orchestrator.process_communication_request.call_args[0][0]
            assert call_args.message_type == MessageType.SELECTION_CONFIRMATION
            assert 'selected_combination' in call_args.context
            
            # Verify pending client action was cleared
            assert updated_state['pending_client_action'] is None
            
            # Verify state was updated
            assert len(updated_state['communications']) == 1
            assert updated_state['communications'][0]['message_type'] == MessageType.SELECTION_CONFIRMATION.value


class TestBlueprintDeliveryCommunication:
    """Test blueprint delivery communication trigger from blueprint_generation node."""
    
    @pytest.mark.asyncio
    async def test_blueprint_delivery_communication_success(self, initial_state, mock_crm_result):
        """Test successful blueprint delivery communication trigger."""
        from event_planning_agent_v2.workflows.crm_integration import trigger_blueprint_delivery_communication
        
        # Add final blueprint to state
        initial_state['final_blueprint'] = """
        # Event Blueprint
        
        ## Executive Summary
        Your wedding event has been planned with the following vendors...
        
        ## Vendor Details
        - Venue: Grand Hall
        - Catering: Gourmet Catering
        - Photography: Pro Photos
        - Makeup: Beauty Studio
        
        ## Timeline
        ...
        """
        
        with patch('event_planning_agent_v2.workflows.crm_integration.get_crm_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_communication_request = AsyncMock(return_value=mock_crm_result)
            mock_get_orch.return_value = mock_orchestrator
            
            # Trigger blueprint delivery communication
            updated_state = await trigger_blueprint_delivery_communication(initial_state)
            
            # Verify communication was triggered with blueprint data
            assert mock_orchestrator.process_communication_request.called
            call_args = mock_orchestrator.process_communication_request.call_args[0][0]
            assert call_args.message_type == MessageType.BLUEPRINT_DELIVERY
            assert call_args.context['blueprint_ready'] is True
            assert call_args.context['blueprint_length'] > 0
            
            # Verify state was updated
            assert len(updated_state['communications']) == 1
            assert updated_state['communications'][0]['message_type'] == MessageType.BLUEPRINT_DELIVERY.value


class TestErrorNotificationCommunication:
    """Test error notification communication trigger from error handlers."""
    
    @pytest.mark.asyncio
    async def test_error_notification_communication_success(self, initial_state, mock_crm_result):
        """Test successful error notification communication trigger."""
        from event_planning_agent_v2.workflows.crm_integration import trigger_error_notification_communication
        
        error_message = "Failed to allocate budget: Database connection error"
        
        with patch('event_planning_agent_v2.workflows.crm_integration.get_crm_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_communication_request = AsyncMock(return_value=mock_crm_result)
            mock_get_orch.return_value = mock_orchestrator
            
            # Trigger error notification communication
            updated_state = await trigger_error_notification_communication(initial_state, error_message)
            
            # Verify communication was triggered with error data
            assert mock_orchestrator.process_communication_request.called
            call_args = mock_orchestrator.process_communication_request.call_args[0][0]
            assert call_args.message_type == MessageType.ERROR_NOTIFICATION
            assert call_args.context['error_occurred'] is True
            assert call_args.context['error_message'] == error_message
            
            # Verify state was updated
            assert len(updated_state['communications']) == 1
            assert updated_state['communications'][0]['message_type'] == MessageType.ERROR_NOTIFICATION.value


class TestWorkflowStateUpdates:
    """Test that workflow state is properly updated after communications."""
    
    @pytest.mark.asyncio
    async def test_multiple_communications_tracked(self, initial_state, mock_crm_result):
        """Test that multiple communications are tracked in state."""
        from event_planning_agent_v2.workflows.crm_integration import (
            trigger_welcome_communication,
            trigger_budget_summary_communication
        )
        
        with patch('event_planning_agent_v2.workflows.crm_integration.get_crm_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_communication_request = AsyncMock(return_value=mock_crm_result)
            mock_get_orch.return_value = mock_orchestrator
            
            # Trigger multiple communications
            state = await trigger_welcome_communication(initial_state)
            
            # Add budget allocations
            state['budget_allocations'] = [{'allocation_id': 'alloc_1'}]
            state = await trigger_budget_summary_communication(state)
            
            # Verify both communications are tracked
            assert len(state['communications']) == 2
            assert state['communications'][0]['message_type'] == MessageType.WELCOME.value
            assert state['communications'][1]['message_type'] == MessageType.BUDGET_SUMMARY.value
            
            # Verify last_communication_at is updated
            assert state['last_communication_at'] is not None
    
    @pytest.mark.asyncio
    async def test_communication_metadata_preserved(self, initial_state, mock_crm_result):
        """Test that communication metadata is preserved in state."""
        from event_planning_agent_v2.workflows.crm_integration import trigger_welcome_communication
        
        mock_crm_result.metadata = {
            'channel_fallback': False,
            'retry_count': 0,
            'delivery_time_ms': 150
        }
        
        with patch('event_planning_agent_v2.workflows.crm_integration.get_crm_orchestrator') as mock_get_orch:
            mock_orchestrator = AsyncMock()
            mock_orchestrator.process_communication_request = AsyncMock(return_value=mock_crm_result)
            mock_get_orch.return_value = mock_orchestrator
            
            # Trigger communication
            updated_state = await trigger_welcome_communication(initial_state)
            
            # Verify metadata is preserved
            comm = updated_state['communications'][0]
            assert 'metadata' in comm
            assert comm['metadata']['channel_fallback'] is False
            assert comm['metadata']['retry_count'] == 0
            assert comm['metadata']['delivery_time_ms'] == 150


if __name__ == '__main__':
    pytest.main([__file__, '-v'])
