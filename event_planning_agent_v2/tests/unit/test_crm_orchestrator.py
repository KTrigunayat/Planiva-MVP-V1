"""
Unit tests for CRMAgentOrchestrator

Tests communication request processing, routing logic, retry mechanism with
exponential backoff, and fallback channel logic.
"""

import pytest
import asyncio
from unittest.mock import Mock, AsyncMock, patch, MagicMock
from datetime import datetime, timezone

from event_planning_agent_v2.crm.models import (
    MessageType,
    MessageChannel,
    UrgencyLevel,
    CommunicationStatus,
    CommunicationRequest,
    CommunicationStrategy,
    CommunicationResult,
    ClientPreferences,
)
from event_planning_agent_v2.crm.orchestrator import (
    CRMAgentOrchestrator,
    RetryConfig,
    ErrorCategory,
)
from event_planning_agent_v2.crm.strategy import CommunicationStrategyTool
from event_planning_agent_v2.crm.email_sub_agent import EmailSubAgent, EmailResult
from event_planning_agent_v2.crm.messaging_sub_agent import MessagingSubAgent, MessageResult


class TestCommunicationRequestProcessing:
    """Test communication request processing end-to-end."""

    @pytest.fixture
    def mock_strategy_tool(self):
        """Create mock strategy tool."""
        tool = Mock(spec=CommunicationStrategyTool)
        tool.determine_strategy = Mock(return_value=CommunicationStrategy(
            primary_channel=MessageChannel.EMAIL,
            fallback_channels=[MessageChannel.SMS],
            send_time=datetime.now(timezone.utc),
            priority=5
        ))
        return tool

    @pytest.fixture
    def mock_email_agent(self):
        """Create mock email agent."""
        agent = Mock(spec=EmailSubAgent)
        agent.compose_and_send = AsyncMock(return_value=EmailResult(
            success=True,
            message_id="email_123",
            sent_at=datetime.now(timezone.utc),
            recipient="test@example.com"
        ))
        return agent

    @pytest.fixture
    def mock_messaging_agent(self):
        """Create mock messaging agent."""
        agent = Mock(spec=MessagingSubAgent)
        agent.send_sms = AsyncMock(return_value=MessageResult(
            success=True,
            message_id="sms_123",
            channel=MessageChannel.SMS,
            sent_at=datetime.now(timezone.utc),
            recipient="+1234567890"
        ))
        agent.send_whatsapp = AsyncMock(return_value=MessageResult(
            success=True,
            message_id="wa_123",
            channel=MessageChannel.WHATSAPP,
            sent_at=datetime.now(timezone.utc),
            recipient="+1234567890"
        ))
        return agent

    @pytest.fixture
    def mock_repository(self):
        """Create mock repository."""
        repo = Mock()
        repo.save_communication = Mock(return_value="comm_123")
        repo.update_status = Mock(return_value=True)
        return repo

    @pytest.fixture
    def orchestrator(self, mock_strategy_tool, mock_email_agent, mock_messaging_agent, mock_repository):
        """Create orchestrator with mocked dependencies."""
        return CRMAgentOrchestrator(
            strategy_tool=mock_strategy_tool,
            email_agent=mock_email_agent,
            messaging_agent=mock_messaging_agent,
            repository=mock_repository,
            retry_config=RetryConfig(max_retries=3, initial_delay=1, max_delay=10)
        )

    @pytest.mark.asyncio
    async def test_successful_email_communication(
        self, orchestrator, mock_strategy_tool, mock_email_agent
    ):
        """Test successful email communication processing."""
        request = CommunicationRequest(
            plan_id="plan_001",
            client_id="client_001",
            message_type=MessageType.WELCOME,
            context={
                "client_name": "John Doe",
                "recipient_email": "john@example.com"
            },
            urgency=UrgencyLevel.NORMAL
        )

        result = await orchestrator.process_communication_request(request)

        assert result.is_successful
        assert result.channel_used == MessageChannel.EMAIL
        assert result.status in [CommunicationStatus.SENT, CommunicationStatus.DELIVERED]
        mock_strategy_tool.determine_strategy.assert_called_once()
        mock_email_agent.compose_and_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_successful_sms_communication(
        self, orchestrator, mock_strategy_tool, mock_messaging_agent
    ):
        """Test successful SMS communication processing."""
        # Configure strategy to use SMS
        mock_strategy_tool.determine_strategy.return_value = CommunicationStrategy(
            primary_channel=MessageChannel.SMS,
            fallback_channels=[MessageChannel.EMAIL],
            send_time=datetime.now(timezone.utc),
            priority=7
        )

        request = CommunicationRequest(
            plan_id="plan_002",
            client_id="client_002",
            message_type=MessageType.REMINDER,
            context={
                "client_name": "Jane Doe",
                "recipient_phone": "+1234567890",
                "link": "https://example.com/plan/002"
            },
            urgency=UrgencyLevel.HIGH
        )

        result = await orchestrator.process_communication_request(request)

        assert result.is_successful
        assert result.channel_used == MessageChannel.SMS
        mock_messaging_agent.send_sms.assert_called_once()


class TestRoutingLogic:
    """Test routing logic to appropriate sub-agents."""

    @pytest.fixture
    def orchestrator_with_mocks(self):
        """Create orchestrator with all mocked dependencies."""
        strategy_tool = Mock(spec=CommunicationStrategyTool)
        email_agent = Mock(spec=EmailSubAgent)
        messaging_agent = Mock(spec=MessagingSubAgent)
        repository = Mock()
        
        email_agent.compose_and_send = AsyncMock(return_value=EmailResult(
            success=True,
            message_id="email_123",
            sent_at=datetime.now(timezone.utc),
            recipient="test@example.com"
        ))
        
        messaging_agent.send_sms = AsyncMock(return_value=MessageResult(
            success=True,
            message_id="sms_123",
            channel=MessageChannel.SMS,
            sent_at=datetime.now(timezone.utc),
            recipient="+1234567890"
        ))
        
        messaging_agent.send_whatsapp = AsyncMock(return_value=MessageResult(
            success=True,
            message_id="wa_123",
            channel=MessageChannel.WHATSAPP,
            sent_at=datetime.now(timezone.utc),
            recipient="+1234567890"
        ))
        
        orchestrator = CRMAgentOrchestrator(
            strategy_tool=strategy_tool,
            email_agent=email_agent,
            messaging_agent=messaging_agent,
            repository=repository
        )
        
        return orchestrator, email_agent, messaging_agent

    @pytest.mark.asyncio
    async def test_route_to_email_agent(self, orchestrator_with_mocks):
        """Test routing to email sub-agent."""
        orchestrator, email_agent, _ = orchestrator_with_mocks
        
        request = CommunicationRequest(
            plan_id="plan_001",
            client_id="client_001",
            message_type=MessageType.BUDGET_SUMMARY,
            context={"recipient_email": "test@example.com", "budget": "$5000"},
            urgency=UrgencyLevel.NORMAL
        )
        
        client_prefs = ClientPreferences(client_id="client_001")
        
        result = await orchestrator.route_to_sub_agent(
            request=request,
            channel=MessageChannel.EMAIL,
            client_preferences=client_prefs
        )
        
        assert result.is_successful
        assert result.channel_used == MessageChannel.EMAIL
        email_agent.compose_and_send.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_sms_agent(self, orchestrator_with_mocks):
        """Test routing to SMS sub-agent."""
        orchestrator, _, messaging_agent = orchestrator_with_mocks
        
        request = CommunicationRequest(
            plan_id="plan_002",
            client_id="client_002",
            message_type=MessageType.REMINDER,
            context={"recipient_phone": "+1234567890", "plan_id": "plan_002", "link": "https://example.com"},
            urgency=UrgencyLevel.HIGH
        )
        
        client_prefs = ClientPreferences(client_id="client_002")
        
        result = await orchestrator.route_to_sub_agent(
            request=request,
            channel=MessageChannel.SMS,
            client_preferences=client_prefs
        )
        
        assert result.is_successful
        assert result.channel_used == MessageChannel.SMS
        messaging_agent.send_sms.assert_called_once()

    @pytest.mark.asyncio
    async def test_route_to_whatsapp_agent(self, orchestrator_with_mocks):
        """Test routing to WhatsApp sub-agent."""
        orchestrator, _, messaging_agent = orchestrator_with_mocks
        
        request = CommunicationRequest(
            plan_id="plan_003",
            client_id="client_003",
            message_type=MessageType.WELCOME,
            context={"recipient_phone": "+1234567890", "plan_id": "plan_003"},
            urgency=UrgencyLevel.NORMAL
        )
        
        client_prefs = ClientPreferences(client_id="client_003")
        
        result = await orchestrator.route_to_sub_agent(
            request=request,
            channel=MessageChannel.WHATSAPP,
            client_preferences=client_prefs
        )
        
        assert result.is_successful
        assert result.channel_used == MessageChannel.WHATSAPP
        messaging_agent.send_whatsapp.assert_called_once()

    @pytest.mark.asyncio
    async def test_missing_recipient_email(self, orchestrator_with_mocks):
        """Test error handling when recipient email is missing."""
        orchestrator, email_agent, _ = orchestrator_with_mocks
        
        request = CommunicationRequest(
            plan_id="plan_004",
            client_id="client_004",
            message_type=MessageType.WELCOME,
            context={"client_name": "Test User"},  # Missing recipient_email
            urgency=UrgencyLevel.NORMAL
        )
        
        client_prefs = ClientPreferences(client_id="client_004")
        
        result = await orchestrator.route_to_sub_agent(
            request=request,
            channel=MessageChannel.EMAIL,
            client_preferences=client_prefs
        )
        
        assert not result.is_successful
        assert result.status == CommunicationStatus.FAILED
        assert "email" in result.error_message.lower()
        email_agent.compose_and_send.assert_not_called()


class TestRetryMechanism:
    """Test retry mechanism with exponential backoff."""

    @pytest.fixture
    def orchestrator_with_failing_agent(self):
        """Create orchestrator with agent that fails initially."""
        strategy_tool = Mock(spec=CommunicationStrategyTool)
        email_agent = Mock(spec=EmailSubAgent)
        messaging_agent = Mock(spec=MessagingSubAgent)
        repository = Mock()
        
        # Configure email agent to fail twice, then succeed
        email_agent.compose_and_send = AsyncMock(side_effect=[
            EmailResult(success=False, error_message="Connection timeout", recipient="test@example.com"),
            EmailResult(success=False, error_message="Connection timeout", recipient="test@example.com"),
            EmailResult(success=True, message_id="email_123", sent_at=datetime.now(timezone.utc), recipient="test@example.com")
        ])
        
        orchestrator = CRMAgentOrchestrator(
            strategy_tool=strategy_tool,
            email_agent=email_agent,
            messaging_agent=messaging_agent,
            repository=repository,
            retry_config=RetryConfig(max_retries=3, initial_delay=0.1, max_delay=1, exponential_base=2)
        )
        
        return orchestrator, email_agent

    @pytest.mark.asyncio
    async def test_retry_on_transient_failure(self, orchestrator_with_failing_agent):
        """Test that transient failures trigger retries."""
        orchestrator, email_agent = orchestrator_with_failing_agent
        
        request = CommunicationRequest(
            plan_id="plan_005",
            client_id="client_005",
            message_type=MessageType.WELCOME,
            context={"recipient_email": "test@example.com", "client_name": "Test"},
            urgency=UrgencyLevel.NORMAL
        )
        
        client_prefs = ClientPreferences(client_id="client_005")
        
        result = await orchestrator._send_with_retry(
            request=request,
            channel=MessageChannel.EMAIL,
            client_preferences=client_prefs,
            attempt_number=1
        )
        
        # Should succeed after retries
        assert result.is_successful
        # Should have been called 3 times (2 failures + 1 success)
        assert email_agent.compose_and_send.call_count == 3

    @pytest.mark.asyncio
    async def test_exponential_backoff_calculation(self):
        """Test exponential backoff delay calculation."""
        orchestrator = CRMAgentOrchestrator(
            strategy_tool=Mock(),
            email_agent=Mock(),
            messaging_agent=Mock(),
            repository=Mock(),
            retry_config=RetryConfig(
                max_retries=3,
                initial_delay=60,
                max_delay=900,
                exponential_base=5,
                jitter=False  # Disable jitter for predictable testing
            )
        )
        
        # Test delay calculations
        delay_1 = orchestrator._calculate_retry_delay(1, ErrorCategory.TRANSIENT)
        delay_2 = orchestrator._calculate_retry_delay(2, ErrorCategory.TRANSIENT)
        delay_3 = orchestrator._calculate_retry_delay(3, ErrorCategory.TRANSIENT)
        
        # Attempt 1: 60 * (5^0) = 60 seconds
        assert delay_1 == 60
        
        # Attempt 2: 60 * (5^1) = 300 seconds
        assert delay_2 == 300
        
        # Attempt 3: 60 * (5^2) = 1500, capped at 900
        assert delay_3 == 900

    @pytest.mark.asyncio
    async def test_rate_limit_error_longer_delay(self):
        """Test that rate limit errors use longer delays."""
        orchestrator = CRMAgentOrchestrator(
            strategy_tool=Mock(),
            email_agent=Mock(),
            messaging_agent=Mock(),
            repository=Mock(),
            retry_config=RetryConfig(
                max_retries=3,
                initial_delay=60,
                max_delay=900,
                exponential_base=5,
                jitter=False
            )
        )
        
        # Rate limit errors should have 2x delay
        normal_delay = orchestrator._calculate_retry_delay(1, ErrorCategory.TRANSIENT)
        rate_limit_delay = orchestrator._calculate_retry_delay(1, ErrorCategory.RATE_LIMIT)
        
        assert rate_limit_delay == normal_delay * 2

    @pytest.mark.asyncio
    async def test_no_retry_on_permanent_error(self):
        """Test that permanent errors don't trigger retries."""
        strategy_tool = Mock(spec=CommunicationStrategyTool)
        email_agent = Mock(spec=EmailSubAgent)
        messaging_agent = Mock(spec=MessagingSubAgent)
        repository = Mock()
        
        # Configure email agent to return permanent error
        email_agent.compose_and_send = AsyncMock(return_value=EmailResult(
            success=False,
            error_message="Invalid email address",
            recipient="invalid@"
        ))
        
        orchestrator = CRMAgentOrchestrator(
            strategy_tool=strategy_tool,
            email_agent=email_agent,
            messaging_agent=messaging_agent,
            repository=repository,
            retry_config=RetryConfig(max_retries=3, initial_delay=0.1)
        )
        
        request = CommunicationRequest(
            plan_id="plan_006",
            client_id="client_006",
            message_type=MessageType.WELCOME,
            context={"recipient_email": "invalid@", "client_name": "Test"},
            urgency=UrgencyLevel.NORMAL
        )
        
        client_prefs = ClientPreferences(client_id="client_006")
        
        result = await orchestrator._send_with_retry(
            request=request,
            channel=MessageChannel.EMAIL,
            client_preferences=client_prefs,
            attempt_number=1
        )
        
        # Should fail without retries
        assert not result.is_successful
        # Should only be called once (no retries for permanent errors)
        assert email_agent.compose_and_send.call_count == 1


class TestFallbackChannelLogic:
    """Test fallback to alternative channels when primary fails."""

    @pytest.fixture
    def orchestrator_with_fallback(self):
        """Create orchestrator configured for fallback testing."""
        strategy_tool = Mock(spec=CommunicationStrategyTool)
        email_agent = Mock(spec=EmailSubAgent)
        messaging_agent = Mock(spec=MessagingSubAgent)
        repository = Mock()
        
        # Email fails
        email_agent.compose_and_send = AsyncMock(return_value=EmailResult(
            success=False,
            error_message="SMTP server unavailable",
            recipient="test@example.com"
        ))
        
        # SMS succeeds
        messaging_agent.send_sms = AsyncMock(return_value=MessageResult(
            success=True,
            message_id="sms_fallback_123",
            channel=MessageChannel.SMS,
            sent_at=datetime.now(timezone.utc),
            recipient="+1234567890"
        ))
        
        orchestrator = CRMAgentOrchestrator(
            strategy_tool=strategy_tool,
            email_agent=email_agent,
            messaging_agent=messaging_agent,
            repository=repository,
            retry_config=RetryConfig(max_retries=2, initial_delay=0.1)
        )
        
        return orchestrator, email_agent, messaging_agent

    @pytest.mark.asyncio
    async def test_fallback_to_sms_when_email_fails(self, orchestrator_with_fallback):
        """Test fallback to SMS when email fails."""
        orchestrator, email_agent, messaging_agent = orchestrator_with_fallback
        
        request = CommunicationRequest(
            plan_id="plan_007",
            client_id="client_007",
            message_type=MessageType.REMINDER,
            context={
                "recipient_email": "test@example.com",
                "recipient_phone": "+1234567890",
                "plan_id": "plan_007",
                "link": "https://example.com"
            },
            urgency=UrgencyLevel.HIGH
        )
        
        client_prefs = ClientPreferences(
            client_id="client_007",
            preferred_channels=[MessageChannel.EMAIL, MessageChannel.SMS]
        )
        
        fallback_channels = [MessageChannel.SMS, MessageChannel.WHATSAPP]
        
        result = await orchestrator._fallback_to_alternative(
            request=request,
            fallback_channels=fallback_channels,
            client_preferences=client_prefs,
            primary_error="SMTP server unavailable"
        )
        
        # Should succeed via SMS fallback
        assert result.is_successful
        assert result.channel_used == MessageChannel.SMS
        assert result.metadata.get('fallback_used') is True
        messaging_agent.send_sms.assert_called()

    @pytest.mark.asyncio
    async def test_all_channels_fail(self):
        """Test behavior when all channels fail."""
        strategy_tool = Mock(spec=CommunicationStrategyTool)
        email_agent = Mock(spec=EmailSubAgent)
        messaging_agent = Mock(spec=MessagingSubAgent)
        repository = Mock()
        
        # All channels fail
        email_agent.compose_and_send = AsyncMock(return_value=EmailResult(
            success=False,
            error_message="SMTP error",
            recipient="test@example.com"
        ))
        
        messaging_agent.send_sms = AsyncMock(return_value=MessageResult(
            success=False,
            error_message="SMS gateway error",
            channel=MessageChannel.SMS,
            recipient="+1234567890"
        ))
        
        messaging_agent.send_whatsapp = AsyncMock(return_value=MessageResult(
            success=False,
            error_message="WhatsApp API error",
            channel=MessageChannel.WHATSAPP,
            recipient="+1234567890"
        ))
        
        orchestrator = CRMAgentOrchestrator(
            strategy_tool=strategy_tool,
            email_agent=email_agent,
            messaging_agent=messaging_agent,
            repository=repository,
            retry_config=RetryConfig(max_retries=1, initial_delay=0.1)
        )
        
        request = CommunicationRequest(
            plan_id="plan_008",
            client_id="client_008",
            message_type=MessageType.ERROR_NOTIFICATION,
            context={
                "recipient_email": "test@example.com",
                "recipient_phone": "+1234567890"
            },
            urgency=UrgencyLevel.CRITICAL
        )
        
        client_prefs = ClientPreferences(client_id="client_008")
        
        fallback_channels = [MessageChannel.SMS, MessageChannel.WHATSAPP]
        
        result = await orchestrator._fallback_to_alternative(
            request=request,
            fallback_channels=fallback_channels,
            client_preferences=client_prefs,
            primary_error="SMTP error"
        )
        
        # Should fail after all channels exhausted
        assert not result.is_successful
        assert result.metadata.get('all_channels_failed') is True
        assert "All channels failed" in result.error_message

    @pytest.mark.asyncio
    async def test_skip_opted_out_fallback_channels(self):
        """Test that opted-out fallback channels are skipped."""
        strategy_tool = Mock(spec=CommunicationStrategyTool)
        email_agent = Mock(spec=EmailSubAgent)
        messaging_agent = Mock(spec=MessagingSubAgent)
        repository = Mock()
        
        # Email fails
        email_agent.compose_and_send = AsyncMock(return_value=EmailResult(
            success=False,
            error_message="SMTP error",
            recipient="test@example.com"
        ))
        
        # WhatsApp succeeds (SMS is opted out)
        messaging_agent.send_whatsapp = AsyncMock(return_value=MessageResult(
            success=True,
            message_id="wa_fallback_123",
            channel=MessageChannel.WHATSAPP,
            sent_at=datetime.now(timezone.utc),
            recipient="+1234567890"
        ))
        
        orchestrator = CRMAgentOrchestrator(
            strategy_tool=strategy_tool,
            email_agent=email_agent,
            messaging_agent=messaging_agent,
            repository=repository,
            retry_config=RetryConfig(max_retries=1, initial_delay=0.1)
        )
        
        request = CommunicationRequest(
            plan_id="plan_009",
            client_id="client_009",
            message_type=MessageType.WELCOME,
            context={
                "recipient_email": "test@example.com",
                "recipient_phone": "+1234567890"
            },
            urgency=UrgencyLevel.NORMAL
        )
        
        # Client opted out of SMS
        client_prefs = ClientPreferences(
            client_id="client_009",
            opt_out_sms=True
        )
        
        fallback_channels = [MessageChannel.SMS, MessageChannel.WHATSAPP]
        
        result = await orchestrator._fallback_to_alternative(
            request=request,
            fallback_channels=fallback_channels,
            client_preferences=client_prefs,
            primary_error="SMTP error"
        )
        
        # Should succeed via WhatsApp (SMS skipped due to opt-out)
        assert result.is_successful
        assert result.channel_used == MessageChannel.WHATSAPP
        messaging_agent.send_whatsapp.assert_called_once()


class TestErrorCategorization:
    """Test error categorization logic."""

    def setup_method(self):
        """Set up test fixtures."""
        self.orchestrator = CRMAgentOrchestrator(
            strategy_tool=Mock(),
            email_agent=Mock(),
            messaging_agent=Mock(),
            repository=Mock()
        )

    def test_categorize_auth_failure(self):
        """Test authentication failure categorization."""
        errors = [
            "Authentication failed",
            "Unauthorized access",
            "Invalid credentials",
            "Access denied"
        ]
        
        for error in errors:
            category = self.orchestrator._categorize_error(error)
            assert category == ErrorCategory.AUTH_FAILURE

    def test_categorize_rate_limit(self):
        """Test rate limit error categorization."""
        errors = [
            "Rate limit exceeded",
            "Too many requests",
            "Quota exceeded",
            "Throttled"
        ]
        
        for error in errors:
            category = self.orchestrator._categorize_error(error)
            assert category == ErrorCategory.RATE_LIMIT

    def test_categorize_permanent_error(self):
        """Test permanent error categorization."""
        errors = [
            "Invalid email address",
            "Email bounced",
            "User unsubscribed",
            "Number blocked"
        ]
        
        for error in errors:
            category = self.orchestrator._categorize_error(error)
            assert category == ErrorCategory.PERMANENT

    def test_categorize_invalid_input(self):
        """Test invalid input categorization."""
        errors = [
            "Validation error",
            "Invalid format",
            "Malformed request",
            "Missing required field"
        ]
        
        for error in errors:
            category = self.orchestrator._categorize_error(error)
            assert category == ErrorCategory.INVALID_INPUT

    def test_categorize_transient_error(self):
        """Test transient error categorization (default)."""
        errors = [
            "Connection timeout",
            "Network error",
            "Service temporarily unavailable",
            "Unknown error"
        ]
        
        for error in errors:
            category = self.orchestrator._categorize_error(error)
            assert category == ErrorCategory.TRANSIENT


class TestClientResponseHandling:
    """Test handling of incoming client responses."""

    @pytest.fixture
    def orchestrator(self):
        """Create orchestrator for testing."""
        return CRMAgentOrchestrator(
            strategy_tool=Mock(),
            email_agent=Mock(),
            messaging_agent=Mock(),
            repository=Mock()
        )

    @pytest.mark.asyncio
    async def test_handle_confirmation_response(self, orchestrator):
        """Test handling client confirmation."""
        response_data = {
            'success': True,
            'intent': 'confirmation',
            'phone_number': '+1234567890',
            'channel': 'sms',
            'message': 'yes'
        }
        
        result = await orchestrator.handle_client_response(
            plan_id="plan_010",
            client_id="client_010",
            response_data=response_data
        )
        
        assert result['success'] is True
        assert result['action'] == 'proceed'
        assert result['plan_id'] == "plan_010"

    @pytest.mark.asyncio
    async def test_handle_rejection_response(self, orchestrator):
        """Test handling client rejection."""
        response_data = {
            'success': True,
            'intent': 'rejection',
            'phone_number': '+1234567890',
            'channel': 'sms',
            'message': 'no'
        }
        
        result = await orchestrator.handle_client_response(
            plan_id="plan_011",
            client_id="client_011",
            response_data=response_data
        )
        
        assert result['success'] is True
        assert result['action'] == 'cancel'

    @pytest.mark.asyncio
    async def test_handle_selection_response(self, orchestrator):
        """Test handling client selection."""
        response_data = {
            'success': True,
            'intent': 'selection',
            'selection': 2,
            'phone_number': '+1234567890',
            'channel': 'whatsapp',
            'message': 'option 2'
        }
        
        result = await orchestrator.handle_client_response(
            plan_id="plan_012",
            client_id="client_012",
            response_data=response_data
        )
        
        assert result['success'] is True
        assert result['action'] == 'select'
        assert result['selection'] == 2

    @pytest.mark.asyncio
    async def test_handle_help_request(self, orchestrator):
        """Test handling client help request."""
        response_data = {
            'success': True,
            'intent': 'help_request',
            'phone_number': '+1234567890',
            'channel': 'sms',
            'message': 'help'
        }
        
        result = await orchestrator.handle_client_response(
            plan_id="plan_013",
            client_id="client_013",
            response_data=response_data
        )
        
        assert result['success'] is True
        assert result['action'] == 'help'

    @pytest.mark.asyncio
    async def test_handle_unknown_intent(self, orchestrator):
        """Test handling unknown client intent."""
        response_data = {
            'success': True,
            'intent': 'unknown',
            'phone_number': '+1234567890',
            'channel': 'sms',
            'message': 'some random text'
        }
        
        result = await orchestrator.handle_client_response(
            plan_id="plan_014",
            client_id="client_014",
            response_data=response_data
        )
        
        assert result['success'] is True
        assert result['action'] == 'review'
        assert 'raw_response' in result
