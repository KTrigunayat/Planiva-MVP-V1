"""
Messaging Sub-Agent for CRM Communication Engine.

This module provides SMS and WhatsApp message composition, sending,
and incoming message handling capabilities.
"""

import logging
import uuid
from dataclasses import dataclass, field
from datetime import datetime, timezone
from pathlib import Path
from typing import Optional, Dict, Any, List

from .models import (
    MessageType,
    MessageChannel,
    CommunicationStatus,
    CommunicationResult,
    UrgencyLevel,
)
from .api_connector import APIConnector, APIResponse


logger = logging.getLogger(__name__)


@dataclass
class MessageResult:
    """Result of a messaging operation."""
    success: bool
    message_id: Optional[str] = None
    channel: MessageChannel = MessageChannel.SMS
    error_message: Optional[str] = None
    sent_at: Optional[datetime] = None
    recipient: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_communication_result(
        self,
        communication_id: str,
        status: CommunicationStatus
    ) -> CommunicationResult:
        """Convert to CommunicationResult."""
        return CommunicationResult(
            communication_id=communication_id,
            status=status,
            channel_used=self.channel,
            sent_at=self.sent_at,
            delivered_at=self.sent_at if self.success else None,
            error_message=self.error_message,
            metadata=self.metadata
        )


class ConciseTextGenerator:
    """
    Generator for concise SMS messages.
    
    Features:
    - Ensures messages are under 160 characters for SMS
    - Provides templates for common message types
    - Handles variable substitution
    """
    
    # SMS character limit
    SMS_CHAR_LIMIT = 160
    
    # Message templates (concise versions)
    TEMPLATES = {
        MessageType.WELCOME: (
            "Welcome to Planiva! Your event plan #{plan_id} is being created. "
            "We'll notify you when ready."
        ),
        MessageType.BUDGET_SUMMARY: (
            "Your budget strategies are ready! View options: {link}"
        ),
        MessageType.VENDOR_OPTIONS: (
            "We found {vendor_count} vendor combinations for your {event_type}! "
            "Check them out: {link}"
        ),
        MessageType.SELECTION_CONFIRMATION: (
            "Please select your preferred vendor combination: {link}"
        ),
        MessageType.BLUEPRINT_DELIVERY: (
            "Your event blueprint is ready! Download: {link}"
        ),
        MessageType.REMINDER: (
            "Reminder: Please review your vendor options for plan #{plan_id}: {link}"
        ),
        MessageType.ERROR_NOTIFICATION: (
            "We encountered an issue with your event plan. "
            "Our team will contact you shortly."
        ),
    }
    
    @classmethod
    def generate_sms(
        cls,
        message_type: MessageType,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a concise SMS message.
        
        Args:
            message_type: Type of message to generate
            context: Context data for variable substitution
        
        Returns:
            SMS message text (< 160 characters)
        
        Raises:
            ValueError: If message type is not supported
        """
        template = cls.TEMPLATES.get(message_type)
        if not template:
            raise ValueError(f"No SMS template for message type: {message_type}")
        
        # Substitute variables
        message = template.format(**context)
        
        # Truncate if necessary (shouldn't happen with proper templates)
        if len(message) > cls.SMS_CHAR_LIMIT:
            logger.warning(
                f"SMS message exceeds {cls.SMS_CHAR_LIMIT} chars, truncating: "
                f"{message[:50]}..."
            )
            message = message[:cls.SMS_CHAR_LIMIT - 3] + "..."
        
        logger.debug(
            f"Generated SMS ({len(message)} chars): {message[:50]}..."
        )
        
        return message
    
    @classmethod
    def generate_whatsapp(
        cls,
        message_type: MessageType,
        context: Dict[str, Any]
    ) -> str:
        """
        Generate a WhatsApp message.
        
        WhatsApp messages can be longer and include emojis.
        
        Args:
            message_type: Type of message to generate
            context: Context data for variable substitution
        
        Returns:
            WhatsApp message text
        """
        # WhatsApp-specific templates with emojis
        whatsapp_templates = {
            MessageType.WELCOME: (
                "👋 Welcome to Planiva!\n\n"
                "Your event plan #{plan_id} is being created. "
                "We'll notify you as soon as it's ready!"
            ),
            MessageType.BUDGET_SUMMARY: (
                "💰 Your budget strategies are ready!\n\n"
                "We've prepared 3 different budget options for your {event_type}. "
                "View them here: {link}"
            ),
            MessageType.VENDOR_OPTIONS: (
                "🎉 Great news!\n\n"
                "We found {vendor_count} vendor combinations for your {event_type}. "
                "Each option is carefully curated to match your preferences.\n\n"
                "Check them out: {link}"
            ),
            MessageType.SELECTION_CONFIRMATION: (
                "✅ Time to choose!\n\n"
                "Please select your preferred vendor combination: {link}"
            ),
            MessageType.BLUEPRINT_DELIVERY: (
                "✨ Your event blueprint is ready!\n\n"
                "Download your complete event plan: {link}\n\n"
                "This includes all vendor details, timeline, and implementation guide."
            ),
            MessageType.REMINDER: (
                "⏰ Friendly reminder\n\n"
                "Please review your vendor options for plan #{plan_id}: {link}"
            ),
            MessageType.ERROR_NOTIFICATION: (
                "⚠️ We encountered an issue\n\n"
                "There was a problem with your event plan. "
                "Our team is looking into it and will contact you shortly."
            ),
        }
        
        template = whatsapp_templates.get(message_type)
        if not template:
            # Fallback to SMS template
            template = cls.TEMPLATES.get(message_type, "")
        
        # Substitute variables
        message = template.format(**context)
        
        logger.debug(
            f"Generated WhatsApp message ({len(message)} chars): {message[:50]}..."
        )
        
        return message


class MessagingSubAgent:
    """
    Messaging Sub-Agent for SMS and WhatsApp communications.
    
    Features:
    - Concise message composition for SMS (< 160 chars)
    - Rich message composition for WhatsApp
    - API integration via APIConnector
    - Incoming message handling
    - Delivery status tracking
    """
    
    def __init__(
        self,
        api_connector: APIConnector,
        repository=None
    ):
        """
        Initialize the Messaging Sub-Agent.
        
        Args:
            api_connector: API connector for WhatsApp and Twilio
            repository: Communication repository for logging (optional)
        """
        self.api_connector = api_connector
        self.repository = repository
        self.text_generator = ConciseTextGenerator()
        
        logger.info("MessagingSubAgent initialized")
    
    async def send_whatsapp(
        self,
        phone_number: str,
        message_type: MessageType,
        context: Dict[str, Any],
        media_url: Optional[str] = None,
        plan_id: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> MessageResult:
        """
        Send WhatsApp message.
        
        Args:
            phone_number: Recipient phone number (E.164 format)
            message_type: Type of message template to use
            context: Template context data
            media_url: Optional media URL for images/documents
            plan_id: Event plan ID for logging
            client_id: Client ID for logging
        
        Returns:
            MessageResult with delivery status
        """
        communication_id = str(uuid.uuid4())
        
        try:
            # Generate message text
            message_text = self.text_generator.generate_whatsapp(
                message_type=message_type,
                context=context
            )
            
            logger.info(
                f"Sending WhatsApp message: {message_type.value} to {phone_number} "
                f"(communication_id: {communication_id})"
            )
            
            # Send via API connector
            api_response = await self.api_connector.send_whatsapp_message(
                phone_number=phone_number,
                message=message_text,
                media_url=media_url,
                message_id=communication_id
            )
            
            # Create result
            result = self._create_message_result(
                api_response=api_response,
                channel=MessageChannel.WHATSAPP,
                phone_number=phone_number,
                communication_id=communication_id
            )
            
            # Log to database if repository is available
            if self.repository and plan_id and client_id:
                await self._log_to_database(
                    communication_id=communication_id,
                    plan_id=plan_id,
                    client_id=client_id,
                    message_type=message_type,
                    channel=MessageChannel.WHATSAPP,
                    recipient=phone_number,
                    message_text=message_text,
                    result=result
                )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to send WhatsApp message to {phone_number}: {e}",
                exc_info=True
            )
            return MessageResult(
                success=False,
                channel=MessageChannel.WHATSAPP,
                error_message=str(e),
                recipient=phone_number,
                metadata={
                    'message_type': message_type.value,
                    'communication_id': communication_id
                }
            )
    
    async def send_sms(
        self,
        phone_number: str,
        message_type: MessageType,
        context: Dict[str, Any],
        plan_id: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> MessageResult:
        """
        Send SMS message.
        
        Args:
            phone_number: Recipient phone number (E.164 format)
            message_type: Type of message template to use
            context: Template context data
            plan_id: Event plan ID for logging
            client_id: Client ID for logging
        
        Returns:
            MessageResult with delivery status
        """
        communication_id = str(uuid.uuid4())
        
        try:
            # Generate concise message text
            message_text = self.text_generator.generate_sms(
                message_type=message_type,
                context=context
            )
            
            logger.info(
                f"Sending SMS: {message_type.value} to {phone_number} "
                f"(communication_id: {communication_id})"
            )
            
            # Send via API connector
            api_response = await self.api_connector.send_sms_message(
                phone_number=phone_number,
                message=message_text,
                message_id=communication_id
            )
            
            # Create result
            result = self._create_message_result(
                api_response=api_response,
                channel=MessageChannel.SMS,
                phone_number=phone_number,
                communication_id=communication_id
            )
            
            # Log to database if repository is available
            if self.repository and plan_id and client_id:
                await self._log_to_database(
                    communication_id=communication_id,
                    plan_id=plan_id,
                    client_id=client_id,
                    message_type=message_type,
                    channel=MessageChannel.SMS,
                    recipient=phone_number,
                    message_text=message_text,
                    result=result
                )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to send SMS to {phone_number}: {e}",
                exc_info=True
            )
            return MessageResult(
                success=False,
                channel=MessageChannel.SMS,
                error_message=str(e),
                recipient=phone_number,
                metadata={
                    'message_type': message_type.value,
                    'communication_id': communication_id
                }
            )
    
    async def handle_incoming_message(
        self,
        phone_number: str,
        message_body: str,
        channel: MessageChannel,
        webhook_data: Optional[Dict[str, Any]] = None
    ) -> Dict[str, Any]:
        """
        Handle incoming message from client.
        
        This method processes client responses and can trigger workflow actions.
        
        Args:
            phone_number: Sender phone number
            message_body: Message text
            channel: Channel the message came from (SMS or WhatsApp)
            webhook_data: Raw webhook data
        
        Returns:
            Dict with parsed response data
        """
        try:
            logger.info(
                f"Received {channel.value} message from {phone_number}: "
                f"{message_body[:50]}..."
            )
            
            # Parse message for common patterns
            parsed_response = self._parse_client_response(
                message_body=message_body,
                phone_number=phone_number,
                channel=channel
            )
            
            # Log incoming message if repository is available
            if self.repository:
                await self._log_incoming_message(
                    phone_number=phone_number,
                    message_body=message_body,
                    channel=channel,
                    parsed_response=parsed_response,
                    webhook_data=webhook_data
                )
            
            logger.info(
                f"Parsed incoming message: {parsed_response.get('intent', 'unknown')}"
            )
            
            return parsed_response
            
        except Exception as e:
            logger.error(
                f"Failed to handle incoming message from {phone_number}: {e}",
                exc_info=True
            )
            return {
                'success': False,
                'error': str(e),
                'phone_number': phone_number,
                'channel': channel.value
            }
    
    def _create_message_result(
        self,
        api_response: APIResponse,
        channel: MessageChannel,
        phone_number: str,
        communication_id: str
    ) -> MessageResult:
        """
        Create MessageResult from API response.
        
        Args:
            api_response: Response from API connector
            channel: Message channel used
            phone_number: Recipient phone number
            communication_id: Unique communication ID
        
        Returns:
            MessageResult
        """
        sent_at = datetime.now(timezone.utc) if api_response.success else None
        
        return MessageResult(
            success=api_response.success,
            message_id=api_response.message_id or communication_id,
            channel=channel,
            error_message=api_response.error_message,
            sent_at=sent_at,
            recipient=phone_number,
            metadata={
                'communication_id': communication_id,
                'api_status': api_response.status,
                'delivery_time_ms': api_response.delivery_time_ms,
                'error_category': api_response.error_category.value if api_response.error_category else None
            }
        )
    
    def _parse_client_response(
        self,
        message_body: str,
        phone_number: str,
        channel: MessageChannel
    ) -> Dict[str, Any]:
        """
        Parse client response for common patterns.
        
        This is a simple pattern matcher. In production, this could be
        enhanced with NLP or LLM-based intent detection.
        
        Args:
            message_body: Message text
            phone_number: Sender phone number
            channel: Message channel
        
        Returns:
            Dict with parsed intent and data
        """
        message_lower = message_body.lower().strip()
        
        # Common response patterns
        if any(word in message_lower for word in ['yes', 'confirm', 'ok', 'approve']):
            return {
                'success': True,
                'intent': 'confirmation',
                'phone_number': phone_number,
                'channel': channel.value,
                'message': message_body
            }
        
        elif any(word in message_lower for word in ['no', 'cancel', 'stop']):
            return {
                'success': True,
                'intent': 'rejection',
                'phone_number': phone_number,
                'channel': channel.value,
                'message': message_body
            }
        
        elif any(word in message_lower for word in ['help', 'support', 'question']):
            return {
                'success': True,
                'intent': 'help_request',
                'phone_number': phone_number,
                'channel': channel.value,
                'message': message_body
            }
        
        # Check for selection (e.g., "option 1", "choice 2")
        elif 'option' in message_lower or 'choice' in message_lower:
            # Extract number
            import re
            numbers = re.findall(r'\d+', message_body)
            selection = int(numbers[0]) if numbers else None
            
            return {
                'success': True,
                'intent': 'selection',
                'selection': selection,
                'phone_number': phone_number,
                'channel': channel.value,
                'message': message_body
            }
        
        else:
            # Unknown intent - store for manual review
            return {
                'success': True,
                'intent': 'unknown',
                'phone_number': phone_number,
                'channel': channel.value,
                'message': message_body
            }
    
    async def _log_to_database(
        self,
        communication_id: str,
        plan_id: str,
        client_id: str,
        message_type: MessageType,
        channel: MessageChannel,
        recipient: str,
        message_text: str,
        result: MessageResult
    ) -> None:
        """
        Log communication to database.
        
        Args:
            communication_id: Unique communication ID
            plan_id: Event plan ID
            client_id: Client ID
            message_type: Type of message
            channel: Message channel
            recipient: Recipient phone number
            message_text: Message text
            result: Message send result
        """
        try:
            if not self.repository:
                return
            
            # Run database operations in executor (repository methods are synchronous)
            import asyncio
            loop = asyncio.get_event_loop()
            
            # Save communication record
            saved_comm_id = await loop.run_in_executor(
                None,
                lambda: self.repository.save_communication(
                    plan_id=plan_id,
                    client_id=client_id,
                    message_type=message_type,
                    channel=channel,
                    urgency=UrgencyLevel.NORMAL,
                    subject=None,  # No subject for SMS/WhatsApp
                    body=message_text,
                    template_name=f"{channel.value}_{message_type.value}",
                    context_data={
                        'recipient': recipient,
                        'communication_id': communication_id
                    },
                    metadata={
                        'channel': channel.value,
                        'original_communication_id': communication_id,
                        'message_length': len(message_text)
                    }
                )
            )
            
            # Update status based on send result
            status = (
                CommunicationStatus.DELIVERED if result.success
                else CommunicationStatus.FAILED
            )
            
            await loop.run_in_executor(
                None,
                lambda: self.repository.update_status(
                    communication_id=saved_comm_id,
                    status=status,
                    error_message=result.error_message,
                    metadata={
                        'sent_at': result.sent_at.isoformat() if result.sent_at else None,
                        'api_message_id': result.message_id,
                        'delivery_time_ms': result.metadata.get('delivery_time_ms')
                    }
                )
            )
            
            logger.debug(
                f"Logged {channel.value} communication to database: {saved_comm_id} "
                f"(original ID: {communication_id})"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to log communication to database: {e}",
                exc_info=True
            )
    
    async def _log_incoming_message(
        self,
        phone_number: str,
        message_body: str,
        channel: MessageChannel,
        parsed_response: Dict[str, Any],
        webhook_data: Optional[Dict[str, Any]]
    ) -> None:
        """
        Log incoming message to database.
        
        Args:
            phone_number: Sender phone number
            message_body: Message text
            channel: Message channel
            parsed_response: Parsed response data
            webhook_data: Raw webhook data
        """
        try:
            if not self.repository:
                return
            
            # This would typically be logged to a separate incoming_messages table
            # For now, we'll just log it
            logger.info(
                f"Incoming {channel.value} message logged: "
                f"from={phone_number}, intent={parsed_response.get('intent')}"
            )
            
            # In a full implementation, you would:
            # 1. Store in incoming_messages table
            # 2. Link to existing communication if it's a reply
            # 3. Trigger workflow actions based on intent
            
        except Exception as e:
            logger.error(
                f"Failed to log incoming message: {e}",
                exc_info=True
            )
    
    async def close(self):
        """Close the messaging sub-agent and cleanup resources."""
        await self.api_connector.close()
        logger.info("MessagingSubAgent closed")
