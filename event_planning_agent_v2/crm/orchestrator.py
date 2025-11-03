"""
CRM Agent Orchestrator

Central coordinator for all CRM communications. Routes requests to appropriate
sub-agents, implements retry logic with exponential backoff, handles fallback
mechanisms, and logs all interactions to the database.
"""

import logging
import asyncio
import random
from typing import Dict, Any, Optional, List
from datetime import datetime, timezone
from dataclasses import dataclass
from enum import Enum

from .models import (
    MessageType,
    MessageChannel,
    UrgencyLevel,
    CommunicationStatus,
    CommunicationRequest,
    CommunicationStrategy,
    CommunicationResult,
    ClientPreferences,
)
from .strategy import CommunicationStrategyTool
from .email_sub_agent import EmailSubAgent
from .messaging_sub_agent import MessagingSubAgent
from .metrics import MetricsCollector
from .logging_config import get_crm_logger

# Import repository conditionally to avoid import errors in tests
try:
    from .repository import CommunicationRepository
except ImportError:
    CommunicationRepository = None


logger = logging.getLogger(__name__)
crm_logger = get_crm_logger(__name__, component="CRMAgentOrchestrator")


class ErrorCategory(str, Enum):
    """Categories of errors for handling logic."""
    TRANSIENT = "transient"  # Retry automatically
    PERMANENT = "permanent"  # Don't retry, log and alert
    RATE_LIMIT = "rate_limit"  # Retry with longer delay
    AUTH_FAILURE = "auth_failure"  # Alert immediately
    INVALID_INPUT = "invalid_input"  # Don't retry, log validation error


@dataclass
class RetryConfig:
    """Configuration for retry logic with exponential backoff."""
    max_retries: int = 3
    initial_delay: int = 60  # seconds
    max_delay: int = 900  # 15 minutes (900 seconds)
    exponential_base: int = 5
    jitter: bool = True


class CRMAgentOrchestrator:
    """
    Central coordinator for all CRM communications.
    
    Responsibilities:
    - Receive communication requests from workflow nodes
    - Determine optimal communication strategy
    - Route requests to appropriate sub-agents
    - Handle responses and update workflow state
    - Implement retry logic and fallback mechanisms
    - Log all interactions to database
    
    Features:
    - Exponential backoff with jitter for retries
    - Multi-channel fallback on failure
    - Error categorization and handling
    - Comprehensive logging and monitoring
    """
    
    def __init__(
        self,
        strategy_tool: CommunicationStrategyTool,
        email_agent: EmailSubAgent,
        messaging_agent: MessagingSubAgent,
        repository=None,
        retry_config: Optional[RetryConfig] = None
    ):
        """
        Initialize the CRM Agent Orchestrator.
        
        Args:
            strategy_tool: Communication strategy determination tool
            email_agent: Email sub-agent for email communications
            messaging_agent: Messaging sub-agent for SMS/WhatsApp
            repository: Database repository for persistence
            retry_config: Optional retry configuration (uses defaults if not provided)
        """
        self.strategy_tool = strategy_tool
        self.email_agent = email_agent
        self.messaging_agent = messaging_agent
        self.repository = repository
        self.retry_config = retry_config or RetryConfig()
        
        logger.info(
            f"CRMAgentOrchestrator initialized with retry config: "
            f"max_retries={self.retry_config.max_retries}, "
            f"initial_delay={self.retry_config.initial_delay}s"
        )
    
    async def process_communication_request(
        self,
        request: CommunicationRequest,
        client_preferences: Optional[ClientPreferences] = None
    ) -> CommunicationResult:
        """
        Process a communication request from the workflow.
        
        This is the main entry point for all communications. It:
        1. Determines the optimal communication strategy
        2. Routes to the appropriate sub-agent
        3. Implements retry logic on failure
        4. Falls back to alternative channels if needed
        5. Logs all interactions to the database
        
        Args:
            request: Communication request with message details
            client_preferences: Optional client preferences (fetched if not provided)
            
        Returns:
            CommunicationResult with status and metadata
        """
        logger.info(
            f"Processing communication request: plan_id={request.plan_id}, "
            f"message_type={request.message_type.value}, urgency={request.urgency.value}"
        )
        
        try:
            # Get client preferences if not provided
            if client_preferences is None:
                client_preferences = await self._get_client_preferences(
                    request.client_id
                )
            
            # Determine communication strategy
            strategy = self.strategy_tool.determine_strategy(
                message_type=request.message_type,
                urgency=request.urgency,
                client_preferences=client_preferences,
                current_time=datetime.now(timezone.utc)
            )
            
            logger.info(
                f"Strategy determined: primary_channel={strategy.primary_channel.value}, "
                f"fallbacks={[ch.value for ch in strategy.fallback_channels]}, "
                f"priority={strategy.priority}"
            )
            
            # Check if we should delay sending based on strategy
            send_time = strategy.send_time
            current_time = datetime.now(timezone.utc)
            
            if send_time > current_time:
                delay_seconds = (send_time - current_time).total_seconds()
                logger.info(
                    f"Delaying communication by {delay_seconds:.0f}s "
                    f"(scheduled for {send_time})"
                )
                # In production, this would queue the message for later
                # For now, we'll send immediately but log the intended delay
                # await asyncio.sleep(delay_seconds)
            
            # Attempt to send via primary channel with retries
            result = await self._send_with_retry(
                request=request,
                channel=strategy.primary_channel,
                client_preferences=client_preferences,
                attempt_number=1
            )
            
            # If primary channel failed, try fallback channels
            if not result.is_successful and strategy.fallback_channels:
                logger.warning(
                    f"Primary channel {strategy.primary_channel.value} failed, "
                    f"attempting fallback channels"
                )
                
                result = await self._fallback_to_alternative(
                    request=request,
                    fallback_channels=strategy.fallback_channels,
                    client_preferences=client_preferences,
                    primary_error=result.error_message
                )
            
            # Log final result and record metrics
            if result.is_successful:
                logger.info(
                    f"Communication successful: communication_id={result.communication_id}, "
                    f"channel={result.channel_used.value}, status={result.status.value}"
                )
                
                # Record metrics
                MetricsCollector.record_communication_sent(
                    message_type=request.message_type.value,
                    channel=result.channel_used.value,
                    status=result.status.value
                )
                
                # Record delivery time if available
                if result.delivery_time_seconds:
                    MetricsCollector.record_delivery_time(
                        channel=result.channel_used.value,
                        delivery_time_seconds=result.delivery_time_seconds
                    )
                
                # Structured logging
                crm_logger.communication_sent(
                    plan_id=request.plan_id,
                    client_id=request.client_id,
                    communication_id=result.communication_id,
                    channel=result.channel_used.value,
                    message_type=request.message_type.value,
                    status=result.status.value
                )
            else:
                logger.error(
                    f"Communication failed after all attempts: "
                    f"communication_id={result.communication_id}, "
                    f"error={result.error_message}"
                )
                
                # Record failure metrics
                MetricsCollector.record_communication_sent(
                    message_type=request.message_type.value,
                    channel=result.channel_used.value,
                    status="failed"
                )
                
                # Structured logging
                crm_logger.communication_failed(
                    communication_id=result.communication_id,
                    channel=result.channel_used.value,
                    error_message=result.error_message or "Unknown error"
                )
                
                # Alert on critical failures
                if request.urgency == UrgencyLevel.CRITICAL:
                    await self._alert_critical_failure(request, result)
            
            return result
            
        except Exception as e:
            logger.error(
                f"Unexpected error processing communication request: {e}",
                exc_info=True
            )
            
            # Return failed result
            return CommunicationResult(
                communication_id="error",
                status=CommunicationStatus.FAILED,
                channel_used=request.preferred_channel or MessageChannel.EMAIL,
                error_message=f"Unexpected error: {str(e)}",
                metadata={
                    'plan_id': request.plan_id,
                    'client_id': request.client_id,
                    'message_type': request.message_type.value
                }
            )
    
    async def route_to_sub_agent(
        self,
        request: CommunicationRequest,
        channel: MessageChannel,
        client_preferences: ClientPreferences
    ) -> CommunicationResult:
        """
        Route communication to appropriate sub-agent based on channel.
        
        Args:
            request: Communication request
            channel: Channel to use for communication
            client_preferences: Client preferences
            
        Returns:
            CommunicationResult from sub-agent
        """
        logger.debug(
            f"Routing to sub-agent: channel={channel.value}, "
            f"message_type={request.message_type.value}"
        )
        
        try:
            if channel == MessageChannel.EMAIL:
                # Route to email sub-agent
                result = await self._route_to_email_agent(request, client_preferences)
            
            elif channel == MessageChannel.SMS:
                # Route to messaging sub-agent (SMS)
                result = await self._route_to_sms_agent(request, client_preferences)
            
            elif channel == MessageChannel.WHATSAPP:
                # Route to messaging sub-agent (WhatsApp)
                result = await self._route_to_whatsapp_agent(request, client_preferences)
            
            else:
                raise ValueError(f"Unsupported channel: {channel}")
            
            return result
            
        except Exception as e:
            logger.error(
                f"Error routing to sub-agent for channel {channel.value}: {e}",
                exc_info=True
            )
            
            return CommunicationResult(
                communication_id="routing_error",
                status=CommunicationStatus.FAILED,
                channel_used=channel,
                error_message=f"Routing error: {str(e)}",
                metadata={
                    'plan_id': request.plan_id,
                    'client_id': request.client_id,
                    'message_type': request.message_type.value
                }
            )
    
    async def handle_client_response(
        self,
        plan_id: str,
        client_id: str,
        response_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Handle incoming client response and update workflow state.
        
        This method processes client responses from SMS/WhatsApp and
        can trigger workflow actions based on the response.
        
        Args:
            plan_id: Event plan ID
            client_id: Client ID
            response_data: Parsed response data from messaging sub-agent
            
        Returns:
            Dict with workflow update instructions
        """
        logger.info(
            f"Handling client response: plan_id={plan_id}, "
            f"client_id={client_id}, intent={response_data.get('intent')}"
        )
        
        try:
            intent = response_data.get('intent', 'unknown')
            
            # Process based on intent
            if intent == 'confirmation':
                # Client confirmed something (e.g., vendor selection)
                return {
                    'success': True,
                    'action': 'proceed',
                    'plan_id': plan_id,
                    'client_id': client_id,
                    'message': 'Client confirmed'
                }
            
            elif intent == 'rejection':
                # Client rejected or wants to cancel
                return {
                    'success': True,
                    'action': 'cancel',
                    'plan_id': plan_id,
                    'client_id': client_id,
                    'message': 'Client rejected'
                }
            
            elif intent == 'selection':
                # Client made a selection
                selection = response_data.get('selection')
                return {
                    'success': True,
                    'action': 'select',
                    'plan_id': plan_id,
                    'client_id': client_id,
                    'selection': selection,
                    'message': f'Client selected option {selection}'
                }
            
            elif intent == 'help_request':
                # Client needs help
                return {
                    'success': True,
                    'action': 'help',
                    'plan_id': plan_id,
                    'client_id': client_id,
                    'message': 'Client requested help'
                }
            
            else:
                # Unknown intent - log for manual review
                logger.warning(
                    f"Unknown client response intent: {intent}, "
                    f"message: {response_data.get('message', '')[:50]}"
                )
                return {
                    'success': True,
                    'action': 'review',
                    'plan_id': plan_id,
                    'client_id': client_id,
                    'message': 'Response requires manual review',
                    'raw_response': response_data
                }
        
        except Exception as e:
            logger.error(
                f"Error handling client response: {e}",
                exc_info=True
            )
            return {
                'success': False,
                'error': str(e),
                'plan_id': plan_id,
                'client_id': client_id
            }
    
    async def _send_with_retry(
        self,
        request: CommunicationRequest,
        channel: MessageChannel,
        client_preferences: ClientPreferences,
        attempt_number: int
    ) -> CommunicationResult:
        """
        Send communication with retry logic and exponential backoff.
        
        Args:
            request: Communication request
            channel: Channel to use
            client_preferences: Client preferences
            attempt_number: Current attempt number (1-indexed)
            
        Returns:
            CommunicationResult
        """
        max_retries = self.retry_config.max_retries
        
        for attempt in range(attempt_number, max_retries + 1):
            logger.info(
                f"Sending communication attempt {attempt}/{max_retries} "
                f"via {channel.value}"
            )
            
            # Route to sub-agent
            result = await self.route_to_sub_agent(
                request=request,
                channel=channel,
                client_preferences=client_preferences
            )
            
            # If successful, return immediately
            if result.is_successful:
                logger.info(
                    f"Communication sent successfully on attempt {attempt}"
                )
                return result
            
            # Categorize error
            error_category = self._categorize_error(result.error_message)
            
            logger.warning(
                f"Communication attempt {attempt} failed: "
                f"error_category={error_category.value}, "
                f"error={result.error_message}"
            )
            
            # Don't retry permanent errors or invalid input
            if error_category in [ErrorCategory.PERMANENT, ErrorCategory.INVALID_INPUT]:
                logger.error(
                    f"Non-retryable error ({error_category.value}), "
                    f"not attempting retry"
                )
                return result
            
            # Alert immediately on auth failures
            if error_category == ErrorCategory.AUTH_FAILURE:
                await self._alert_auth_failure(channel, result.error_message)
                return result
            
            # If this was the last attempt, return the failed result
            if attempt >= max_retries:
                logger.error(
                    f"All {max_retries} retry attempts exhausted"
                )
                return result
            
            # Calculate delay with exponential backoff and jitter
            delay = self._calculate_retry_delay(
                attempt=attempt,
                error_category=error_category
            )
            
            logger.info(
                f"Retrying in {delay:.1f}s (attempt {attempt + 1}/{max_retries})"
            )
            
            # Record retry metrics
            MetricsCollector.record_retry_attempt(
                channel=channel.value,
                attempt_number=attempt + 1
            )
            
            # Structured logging
            crm_logger.retry_attempt(
                communication_id=result.communication_id,
                channel=channel.value,
                attempt_number=attempt + 1,
                max_retries=max_retries,
                delay_seconds=delay
            )
            
            await asyncio.sleep(delay)
        
        # Should not reach here, but return last result just in case
        return result
    
    async def _fallback_to_alternative(
        self,
        request: CommunicationRequest,
        fallback_channels: List[MessageChannel],
        client_preferences: ClientPreferences,
        primary_error: Optional[str]
    ) -> CommunicationResult:
        """
        Attempt to send via fallback channels when primary fails.
        
        Args:
            request: Communication request
            fallback_channels: List of fallback channels to try
            client_preferences: Client preferences
            primary_error: Error message from primary channel
            
        Returns:
            CommunicationResult from successful fallback or final failure
        """
        logger.info(
            f"Attempting fallback channels: {[ch.value for ch in fallback_channels]}"
        )
        
        for fallback_channel in fallback_channels:
            # Check if channel is available (not opted out)
            if not client_preferences.is_channel_available(fallback_channel):
                logger.warning(
                    f"Fallback channel {fallback_channel.value} not available "
                    f"(opted out), skipping"
                )
                continue
            
            logger.info(
                f"Trying fallback channel: {fallback_channel.value}"
            )
            
            # Attempt to send via fallback channel (with retries)
            result = await self._send_with_retry(
                request=request,
                channel=fallback_channel,
                client_preferences=client_preferences,
                attempt_number=1
            )
            
            # If successful, return immediately
            if result.is_successful:
                logger.info(
                    f"Fallback successful via {fallback_channel.value}"
                )
                
                # Record fallback metrics
                MetricsCollector.record_fallback_used(
                    primary_channel=fallback_channels[0].value if fallback_channels else "unknown",
                    fallback_channel=fallback_channel.value
                )
                
                # Structured logging
                crm_logger.fallback_used(
                    communication_id=result.communication_id,
                    primary_channel=fallback_channels[0].value if fallback_channels else "unknown",
                    fallback_channel=fallback_channel.value,
                    primary_error=primary_error or "Unknown error"
                )
                
                # Add metadata about fallback
                result.metadata['fallback_used'] = True
                result.metadata['primary_channel_error'] = primary_error
                
                return result
            
            logger.warning(
                f"Fallback channel {fallback_channel.value} also failed: "
                f"{result.error_message}"
            )
        
        # All fallback channels failed
        logger.error(
            "All fallback channels exhausted, communication failed"
        )
        
        return CommunicationResult(
            communication_id="all_channels_failed",
            status=CommunicationStatus.FAILED,
            channel_used=fallback_channels[-1] if fallback_channels else MessageChannel.EMAIL,
            error_message=(
                f"All channels failed. Primary error: {primary_error}. "
                f"Fallback channels attempted: {[ch.value for ch in fallback_channels]}"
            ),
            metadata={
                'plan_id': request.plan_id,
                'client_id': request.client_id,
                'message_type': request.message_type.value,
                'all_channels_failed': True
            }
        )
    
    def _calculate_retry_delay(
        self,
        attempt: int,
        error_category: ErrorCategory
    ) -> float:
        """
        Calculate retry delay with exponential backoff and jitter.
        
        Args:
            attempt: Current attempt number (1-indexed)
            error_category: Category of error
            
        Returns:
            Delay in seconds
        """
        # Base delay calculation: initial_delay * (exponential_base ^ (attempt - 1))
        # Attempt 1: 60 * (5 ^ 0) = 60 seconds (1 minute)
        # Attempt 2: 60 * (5 ^ 1) = 300 seconds (5 minutes)
        # Attempt 3: 60 * (5 ^ 2) = 1500 seconds (25 minutes, capped at 15 minutes)
        
        base_delay = self.retry_config.initial_delay * (
            self.retry_config.exponential_base ** (attempt - 1)
        )
        
        # Cap at max delay
        delay = min(base_delay, self.retry_config.max_delay)
        
        # For rate limit errors, use longer delay
        if error_category == ErrorCategory.RATE_LIMIT:
            delay = min(delay * 2, self.retry_config.max_delay)
        
        # Add jitter to prevent thundering herd
        if self.retry_config.jitter:
            # Add random jitter of ±20%
            jitter_factor = 1.0 + (random.random() * 0.4 - 0.2)
            delay = delay * jitter_factor
        
        return delay
    
    def _categorize_error(self, error_message: Optional[str]) -> ErrorCategory:
        """
        Categorize error for appropriate handling.
        
        Args:
            error_message: Error message to categorize
            
        Returns:
            ErrorCategory
        """
        if not error_message:
            return ErrorCategory.TRANSIENT
        
        error_lower = error_message.lower()
        
        # Check for authentication failures
        if any(word in error_lower for word in [
            'auth', 'authentication', 'unauthorized', 'forbidden',
            'invalid credentials', 'access denied'
        ]):
            return ErrorCategory.AUTH_FAILURE
        
        # Check for rate limiting
        if any(word in error_lower for word in [
            'rate limit', 'quota', 'too many requests', 'throttle'
        ]):
            return ErrorCategory.RATE_LIMIT
        
        # Check for permanent errors
        if any(word in error_lower for word in [
            'invalid email', 'invalid phone', 'bounced', 'unsubscribed',
            'blocked', 'blacklisted', 'does not exist'
        ]):
            return ErrorCategory.PERMANENT
        
        # Check for invalid input
        if any(word in error_lower for word in [
            'validation', 'invalid format', 'malformed', 'missing required'
        ]):
            return ErrorCategory.INVALID_INPUT
        
        # Default to transient (retryable)
        return ErrorCategory.TRANSIENT
    
    async def _get_client_preferences(
        self,
        client_id: str
    ) -> ClientPreferences:
        """
        Get client preferences from database or use defaults.
        
        Args:
            client_id: Client ID
            
        Returns:
            ClientPreferences
        """
        try:
            # In production, this would fetch from database/cache
            # For now, return default preferences
            logger.debug(f"Using default preferences for client {client_id}")
            
            return ClientPreferences(
                client_id=client_id,
                preferred_channels=[MessageChannel.EMAIL],
                timezone="UTC",
                quiet_hours_start="22:00",
                quiet_hours_end="08:00",
                opt_out_email=False,
                opt_out_sms=False,
                opt_out_whatsapp=False
            )
        
        except Exception as e:
            logger.error(
                f"Error fetching client preferences for {client_id}: {e}",
                exc_info=True
            )
            # Return defaults on error
            return ClientPreferences(client_id=client_id)
    
    async def _route_to_email_agent(
        self,
        request: CommunicationRequest,
        client_preferences: ClientPreferences
    ) -> CommunicationResult:
        """Route request to email sub-agent."""
        # Get recipient email from context
        recipient_email = request.context.get('recipient_email') or request.context.get('client_email')
        
        if not recipient_email:
            return CommunicationResult(
                communication_id="missing_email",
                status=CommunicationStatus.FAILED,
                channel_used=MessageChannel.EMAIL,
                error_message="Recipient email not provided in context",
                metadata={'plan_id': request.plan_id, 'client_id': request.client_id}
            )
        
        # Send via email agent
        email_result = await self.email_agent.compose_and_send(
            recipient=recipient_email,
            message_type=request.message_type,
            context=request.context,
            attachments=request.context.get('attachments'),
            plan_id=request.plan_id,
            client_id=request.client_id
        )
        
        # Convert to CommunicationResult
        status = CommunicationStatus.DELIVERED if email_result.success else CommunicationStatus.FAILED
        
        return email_result.to_communication_result(
            communication_id=email_result.message_id or "email_unknown",
            status=status
        )
    
    async def _route_to_sms_agent(
        self,
        request: CommunicationRequest,
        client_preferences: ClientPreferences
    ) -> CommunicationResult:
        """Route request to messaging sub-agent for SMS."""
        # Get recipient phone from context
        recipient_phone = request.context.get('recipient_phone') or request.context.get('client_phone')
        
        if not recipient_phone:
            return CommunicationResult(
                communication_id="missing_phone",
                status=CommunicationStatus.FAILED,
                channel_used=MessageChannel.SMS,
                error_message="Recipient phone not provided in context",
                metadata={'plan_id': request.plan_id, 'client_id': request.client_id}
            )
        
        # Send via messaging agent
        message_result = await self.messaging_agent.send_sms(
            phone_number=recipient_phone,
            message_type=request.message_type,
            context=request.context,
            plan_id=request.plan_id,
            client_id=request.client_id
        )
        
        # Convert to CommunicationResult
        status = CommunicationStatus.DELIVERED if message_result.success else CommunicationStatus.FAILED
        
        return message_result.to_communication_result(
            communication_id=message_result.message_id or "sms_unknown",
            status=status
        )
    
    async def _route_to_whatsapp_agent(
        self,
        request: CommunicationRequest,
        client_preferences: ClientPreferences
    ) -> CommunicationResult:
        """Route request to messaging sub-agent for WhatsApp."""
        # Get recipient phone from context
        recipient_phone = request.context.get('recipient_phone') or request.context.get('client_phone')
        
        if not recipient_phone:
            return CommunicationResult(
                communication_id="missing_phone",
                status=CommunicationStatus.FAILED,
                channel_used=MessageChannel.WHATSAPP,
                error_message="Recipient phone not provided in context",
                metadata={'plan_id': request.plan_id, 'client_id': request.client_id}
            )
        
        # Send via messaging agent
        message_result = await self.messaging_agent.send_whatsapp(
            phone_number=recipient_phone,
            message_type=request.message_type,
            context=request.context,
            media_url=request.context.get('media_url'),
            plan_id=request.plan_id,
            client_id=request.client_id
        )
        
        # Convert to CommunicationResult
        status = CommunicationStatus.DELIVERED if message_result.success else CommunicationStatus.FAILED
        
        return message_result.to_communication_result(
            communication_id=message_result.message_id or "whatsapp_unknown",
            status=status
        )
    
    async def _alert_critical_failure(
        self,
        request: CommunicationRequest,
        result: CommunicationResult
    ) -> None:
        """
        Alert administrators of critical communication failure.
        
        Args:
            request: Original communication request
            result: Failed communication result
        """
        logger.critical(
            f"CRITICAL COMMUNICATION FAILURE: "
            f"plan_id={request.plan_id}, "
            f"client_id={request.client_id}, "
            f"message_type={request.message_type.value}, "
            f"error={result.error_message}"
        )
        
        # In production, this would:
        # 1. Send alert to PagerDuty
        # 2. Send Slack notification
        # 3. Create incident ticket
        # 4. Escalate to on-call engineer
    
    async def _alert_auth_failure(
        self,
        channel: MessageChannel,
        error_message: Optional[str]
    ) -> None:
        """
        Alert administrators of authentication failure.
        
        Args:
            channel: Channel that experienced auth failure
            error_message: Error message
        """
        logger.critical(
            f"AUTHENTICATION FAILURE: "
            f"channel={channel.value}, "
            f"error={error_message}"
        )
        
        # In production, this would:
        # 1. Send immediate alert to PagerDuty
        # 2. Send Slack notification to #alerts channel
        # 3. Disable the failing channel temporarily
        # 4. Create high-priority incident ticket
    
    async def close(self):
        """Close the orchestrator and cleanup resources."""
        logger.info("Closing CRMAgentOrchestrator")
        
        # Close sub-agents
        if hasattr(self.email_agent, 'close'):
            self.email_agent.close()
        
        if hasattr(self.messaging_agent, 'close'):
            await self.messaging_agent.close()
        
        logger.info("CRMAgentOrchestrator closed")
