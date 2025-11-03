"""
Unit tests for Messaging Sub-Agent.

Tests message composition, length constraints, WhatsApp and SMS sending,
and incoming message handling.
"""

import pytest
import asyncio
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone

from event_planning_agent_v2.crm.messaging_sub_agent import (
    MessagingSubAgent,
    ConciseTextGenerator,
    MessageResult,
)
from event_planning_agent_v2.crm.models import (
    MessageType,
    MessageChannel,
    CommunicationStatus,
)
from event_planning_agent_v2.crm.api_connector import (
    APIConnector,
    WhatsAppConfig,
    TwilioConfig,
    APIResponse,
    ErrorCategory,
)


# Fixtures

@pytest.fixture
def whatsapp_config():
    """Create test WhatsApp configuration."""
    return WhatsAppConfig(
        phone_number_id="test_phone_id",
        access_token="test_access_token",
        webhook_verify_token="test_verify_token"
    )


@pytest.fixture
def twilio_config():
    """Create test Twilio configuration."""
    return TwilioConfig(
        account_sid="test_account_sid",
        auth_token="test_auth_token",
        from_number="+15551234567"
    )


@pytest.fixture
def api_connector(whatsapp_config, twilio_config):
    """Create test API connector."""
    return APIConnector(
        whatsapp_config=whatsapp_config,
        twilio_config=twilio_config
    )


@pytest.fixture
def messaging_agent(api_connector):
    """Create test messaging sub-agent."""
    return MessagingSubAgent(
        api_connector=api_connector,
        repository=None  # No repository for unit tests
    )


@pytest.fixture
def sample_context():
    """Sample message context."""
    return {
        "plan_id": "plan_123",
        "event_type": "wedding",
        "vendor_count": 5,
        "link": "https://planiva.com/plan/123"
    }


# ConciseTextGenerator Tests

class TestConciseTextGenerator:
    """Tests for ConciseTextGenerator."""
    
    def test_generate_sms_welcome(self, sample_context):
        """Test SMS generation for welcome message."""
        message = ConciseTextGenerator.generate_sms(
            message_type=MessageType.WELCOME,
            context=sample_context
        )
        
        assert message is not None
        assert len(message) <= ConciseTextGenerator.SMS_CHAR_LIMIT
        assert "plan_123" in message
        assert "Planiva" in message
    
    def test_generate_sms_budget_summary(self, sample_context):
        """Test SMS generation for budget summary."""
        message = ConciseTextGenerator.generate_sms(
            message_type=MessageType.BUDGET_SUMMARY,
            context=sample_context
        )
        
        assert message is not None
        assert len(message) <= ConciseTextGenerator.SMS_CHAR_LIMIT
        assert "budget" in message.lower()
        assert sample_context["link"] in message
    
    def test_generate_sms_vendor_options(self, sample_context):
        """Test SMS generation for vendor options."""
        message = ConciseTextGenerator.generate_sms(
            message_type=MessageType.VENDOR_OPTIONS,
            context=sample_context
        )
        
        assert message is not None
        assert len(message) <= ConciseTextGenerator.SMS_CHAR_LIMIT
        assert "5" in message  # vendor_count
        assert "wedding" in message
        assert sample_context["link"] in message
    
    def test_generate_sms_selection_confirmation(self, sample_context):
        """Test SMS generation for selection confirmation."""
        message = ConciseTextGenerator.generate_sms(
            message_type=MessageType.SELECTION_CONFIRMATION,
            context=sample_context
        )
        
        assert message is not None
        assert len(message) <= ConciseTextGenerator.SMS_CHAR_LIMIT
        assert "select" in message.lower()
        assert sample_context["link"] in message
    
    def test_generate_sms_blueprint_delivery(self, sample_context):
        """Test SMS generation for blueprint delivery."""
        message = ConciseTextGenerator.generate_sms(
            message_type=MessageType.BLUEPRINT_DELIVERY,
            context=sample_context
        )
        
        assert message is not None
        assert len(message) <= ConciseTextGenerator.SMS_CHAR_LIMIT
        assert "blueprint" in message.lower()
        assert sample_context["link"] in message
    
    def test_generate_sms_reminder(self, sample_context):
        """Test SMS generation for reminder."""
        message = ConciseTextGenerator.generate_sms(
            message_type=MessageType.REMINDER,
            context=sample_context
        )
        
        assert message is not None
        assert len(message) <= ConciseTextGenerator.SMS_CHAR_LIMIT
        assert "reminder" in message.lower()
        assert "plan_123" in message
    
    def test_generate_sms_error_notification(self, sample_context):
        """Test SMS generation for error notification."""
        message = ConciseTextGenerator.generate_sms(
            message_type=MessageType.ERROR_NOTIFICATION,
            context=sample_context
        )
        
        assert message is not None
        assert len(message) <= ConciseTextGenerator.SMS_CHAR_LIMIT
        assert "issue" in message.lower() or "error" in message.lower()
    
    def test_generate_sms_length_constraint(self):
        """Test that all SMS messages respect length constraint."""
        test_contexts = [
            {"plan_id": "plan_123", "link": "https://planiva.com/plan/123"},
            {"plan_id": "plan_456", "event_type": "wedding", "vendor_count": 10, "link": "https://planiva.com/plan/456"},
        ]
        
        for message_type in MessageType:
            for context in test_contexts:
                try:
                    message = ConciseTextGenerator.generate_sms(
                        message_type=message_type,
                        context=context
                    )
                    assert len(message) <= ConciseTextGenerator.SMS_CHAR_LIMIT, \
                        f"Message type {message_type} exceeds SMS limit: {len(message)} chars"
                except (ValueError, KeyError):
                    # Some message types may require specific context keys
                    pass
    
    def test_generate_whatsapp_welcome(self, sample_context):
        """Test WhatsApp generation for welcome message."""
        message = ConciseTextGenerator.generate_whatsapp(
            message_type=MessageType.WELCOME,
            context=sample_context
        )
        
        assert message is not None
        assert "👋" in message  # Emoji
        assert "plan_123" in message
        assert "Planiva" in message
    
    def test_generate_whatsapp_vendor_options(self, sample_context):
        """Test WhatsApp generation for vendor options."""
        message = ConciseTextGenerator.generate_whatsapp(
            message_type=MessageType.VENDOR_OPTIONS,
            context=sample_context
        )
        
        assert message is not None
        assert "🎉" in message  # Emoji
        assert "5" in message  # vendor_count
        assert "wedding" in message
        assert sample_context["link"] in message
    
    def test_generate_whatsapp_blueprint_delivery(self, sample_context):
        """Test WhatsApp generation for blueprint delivery."""
        message = ConciseTextGenerator.generate_whatsapp(
            message_type=MessageType.BLUEPRINT_DELIVERY,
            context=sample_context
        )
        
        assert message is not None
        assert "✨" in message  # Emoji
        assert "blueprint" in message.lower()
        assert sample_context["link"] in message
        assert "timeline" in message.lower()


# MessagingSubAgent Tests

class TestMessagingSubAgent:
    """Tests for MessagingSubAgent."""
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_success(self, messaging_agent, sample_context):
        """Test successful WhatsApp message sending."""
        # Mock API connector response
        mock_response = APIResponse(
            success=True,
            message_id="wa_msg_123",
            status="sent",
            delivery_time_ms=150
        )
        
        with patch.object(
            messaging_agent.api_connector,
            'send_whatsapp_message',
            return_value=mock_response
        ) as mock_send:
            result = await messaging_agent.send_whatsapp(
                phone_number="+15551234567",
                message_type=MessageType.WELCOME,
                context=sample_context
            )
            
            assert result.success is True
            assert result.channel == MessageChannel.WHATSAPP
            assert result.message_id == "wa_msg_123"
            assert result.sent_at is not None
            assert result.recipient == "+15551234567"
            
            # Verify API connector was called
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args.kwargs['phone_number'] == "+15551234567"
            assert "Planiva" in call_args.kwargs['message']
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_failure(self, messaging_agent, sample_context):
        """Test WhatsApp message sending failure."""
        # Mock API connector error response
        mock_response = APIResponse(
            success=False,
            error_message="Rate limit exceeded",
            error_category=ErrorCategory.RATE_LIMIT
        )
        
        with patch.object(
            messaging_agent.api_connector,
            'send_whatsapp_message',
            return_value=mock_response
        ):
            result = await messaging_agent.send_whatsapp(
                phone_number="+15551234567",
                message_type=MessageType.WELCOME,
                context=sample_context
            )
            
            assert result.success is False
            assert result.channel == MessageChannel.WHATSAPP
            assert result.error_message == "Rate limit exceeded"
            assert result.sent_at is None
    
    @pytest.mark.asyncio
    async def test_send_sms_success(self, messaging_agent, sample_context):
        """Test successful SMS sending."""
        # Mock API connector response
        mock_response = APIResponse(
            success=True,
            message_id="sms_msg_456",
            status="queued",
            delivery_time_ms=100
        )
        
        with patch.object(
            messaging_agent.api_connector,
            'send_sms_message',
            return_value=mock_response
        ) as mock_send:
            result = await messaging_agent.send_sms(
                phone_number="+15551234567",
                message_type=MessageType.BUDGET_SUMMARY,
                context=sample_context
            )
            
            assert result.success is True
            assert result.channel == MessageChannel.SMS
            assert result.message_id == "sms_msg_456"
            assert result.sent_at is not None
            assert result.recipient == "+15551234567"
            
            # Verify API connector was called
            mock_send.assert_called_once()
            call_args = mock_send.call_args
            assert call_args.kwargs['phone_number'] == "+15551234567"
            # Verify message is concise (< 160 chars)
            assert len(call_args.kwargs['message']) <= 160
    
    @pytest.mark.asyncio
    async def test_send_sms_failure(self, messaging_agent, sample_context):
        """Test SMS sending failure."""
        # Mock API connector error response
        mock_response = APIResponse(
            success=False,
            error_message="Invalid phone number",
            error_category=ErrorCategory.PERMANENT
        )
        
        with patch.object(
            messaging_agent.api_connector,
            'send_sms_message',
            return_value=mock_response
        ):
            result = await messaging_agent.send_sms(
                phone_number="+15551234567",
                message_type=MessageType.BUDGET_SUMMARY,
                context=sample_context
            )
            
            assert result.success is False
            assert result.channel == MessageChannel.SMS
            assert result.error_message == "Invalid phone number"
            assert result.sent_at is None
    
    @pytest.mark.asyncio
    async def test_send_whatsapp_with_media(self, messaging_agent, sample_context):
        """Test WhatsApp message with media attachment."""
        mock_response = APIResponse(
            success=True,
            message_id="wa_msg_789",
            status="sent"
        )
        
        with patch.object(
            messaging_agent.api_connector,
            'send_whatsapp_message',
            return_value=mock_response
        ) as mock_send:
            result = await messaging_agent.send_whatsapp(
                phone_number="+15551234567",
                message_type=MessageType.BLUEPRINT_DELIVERY,
                context=sample_context,
                media_url="https://planiva.com/blueprints/123.pdf"
            )
            
            assert result.success is True
            
            # Verify media URL was passed
            call_args = mock_send.call_args
            assert call_args.kwargs['media_url'] == "https://planiva.com/blueprints/123.pdf"
    
    @pytest.mark.asyncio
    async def test_handle_incoming_message_confirmation(self, messaging_agent):
        """Test handling incoming confirmation message."""
        result = await messaging_agent.handle_incoming_message(
            phone_number="+15551234567",
            message_body="Yes, I confirm",
            channel=MessageChannel.SMS
        )
        
        assert result['success'] is True
        assert result['intent'] == 'confirmation'
        assert result['phone_number'] == "+15551234567"
        assert result['channel'] == MessageChannel.SMS.value
    
    @pytest.mark.asyncio
    async def test_handle_incoming_message_rejection(self, messaging_agent):
        """Test handling incoming rejection message."""
        result = await messaging_agent.handle_incoming_message(
            phone_number="+15551234567",
            message_body="No, cancel this",
            channel=MessageChannel.WHATSAPP
        )
        
        assert result['success'] is True
        assert result['intent'] == 'rejection'
        assert result['phone_number'] == "+15551234567"
    
    @pytest.mark.asyncio
    async def test_handle_incoming_message_help(self, messaging_agent):
        """Test handling incoming help request."""
        result = await messaging_agent.handle_incoming_message(
            phone_number="+15551234567",
            message_body="I need help with this",
            channel=MessageChannel.SMS
        )
        
        assert result['success'] is True
        assert result['intent'] == 'help_request'
    
    @pytest.mark.asyncio
    async def test_handle_incoming_message_selection(self, messaging_agent):
        """Test handling incoming selection message."""
        result = await messaging_agent.handle_incoming_message(
            phone_number="+15551234567",
            message_body="I choose option 2",
            channel=MessageChannel.SMS
        )
        
        assert result['success'] is True
        assert result['intent'] == 'selection'
        assert result['selection'] == 2
    
    @pytest.mark.asyncio
    async def test_handle_incoming_message_unknown(self, messaging_agent):
        """Test handling incoming message with unknown intent."""
        result = await messaging_agent.handle_incoming_message(
            phone_number="+15551234567",
            message_body="Random message content",
            channel=MessageChannel.SMS
        )
        
        assert result['success'] is True
        assert result['intent'] == 'unknown'
        assert result['message'] == "Random message content"
    
    @pytest.mark.asyncio
    async def test_message_result_to_communication_result(self):
        """Test conversion of MessageResult to CommunicationResult."""
        message_result = MessageResult(
            success=True,
            message_id="msg_123",
            channel=MessageChannel.SMS,
            sent_at=datetime.now(timezone.utc),
            recipient="+15551234567",
            metadata={"test": "data"}
        )
        
        comm_result = message_result.to_communication_result(
            communication_id="comm_456",
            status=CommunicationStatus.DELIVERED
        )
        
        assert comm_result.communication_id == "comm_456"
        assert comm_result.status == CommunicationStatus.DELIVERED
        assert comm_result.channel_used == MessageChannel.SMS
        assert comm_result.sent_at == message_result.sent_at
        assert comm_result.delivered_at == message_result.sent_at
        assert comm_result.metadata == {"test": "data"}
    
    @pytest.mark.asyncio
    async def test_close(self, messaging_agent):
        """Test closing the messaging sub-agent."""
        with patch.object(messaging_agent.api_connector, 'close') as mock_close:
            await messaging_agent.close()
            mock_close.assert_called_once()


# Integration-style Tests

class TestMessagingIntegration:
    """Integration-style tests for messaging workflows."""
    
    @pytest.mark.asyncio
    async def test_complete_whatsapp_workflow(self, messaging_agent, sample_context):
        """Test complete WhatsApp message workflow."""
        # Mock successful send
        mock_response = APIResponse(
            success=True,
            message_id="wa_msg_complete",
            status="sent",
            delivery_time_ms=200
        )
        
        with patch.object(
            messaging_agent.api_connector,
            'send_whatsapp_message',
            return_value=mock_response
        ):
            # Send message
            result = await messaging_agent.send_whatsapp(
                phone_number="+15551234567",
                message_type=MessageType.VENDOR_OPTIONS,
                context=sample_context
            )
            
            assert result.success is True
            assert result.channel == MessageChannel.WHATSAPP
            
            # Simulate incoming response
            incoming = await messaging_agent.handle_incoming_message(
                phone_number="+15551234567",
                message_body="I choose option 1",
                channel=MessageChannel.WHATSAPP
            )
            
            assert incoming['success'] is True
            assert incoming['intent'] == 'selection'
            assert incoming['selection'] == 1
    
    @pytest.mark.asyncio
    async def test_complete_sms_workflow(self, messaging_agent, sample_context):
        """Test complete SMS workflow."""
        # Mock successful send
        mock_response = APIResponse(
            success=True,
            message_id="sms_msg_complete",
            status="queued",
            delivery_time_ms=100
        )
        
        with patch.object(
            messaging_agent.api_connector,
            'send_sms_message',
            return_value=mock_response
        ):
            # Send message
            result = await messaging_agent.send_sms(
                phone_number="+15551234567",
                message_type=MessageType.SELECTION_CONFIRMATION,
                context=sample_context
            )
            
            assert result.success is True
            assert result.channel == MessageChannel.SMS
            
            # Simulate incoming confirmation
            incoming = await messaging_agent.handle_incoming_message(
                phone_number="+15551234567",
                message_body="Yes",
                channel=MessageChannel.SMS
            )
            
            assert incoming['success'] is True
            assert incoming['intent'] == 'confirmation'
