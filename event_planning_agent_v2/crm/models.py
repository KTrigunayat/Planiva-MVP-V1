"""
Core data models for the CRM Communication Engine.

This module defines enums, dataclasses, and database models for managing
multi-channel client communications throughout the event planning lifecycle.
"""

from enum import Enum
from dataclasses import dataclass, field
from datetime import datetime
from typing import Optional, Dict, Any, List
from uuid import UUID, uuid4


class MessageType(str, Enum):
    """Types of messages sent to clients."""
    WELCOME = "welcome"
    BUDGET_SUMMARY = "budget_summary"
    VENDOR_OPTIONS = "vendor_options"
    SELECTION_CONFIRMATION = "selection_confirmation"
    BLUEPRINT_DELIVERY = "blueprint_delivery"
    ERROR_NOTIFICATION = "error_notification"
    REMINDER = "reminder"


class MessageChannel(str, Enum):
    """Communication channels available for messaging."""
    EMAIL = "email"
    SMS = "sms"
    WHATSAPP = "whatsapp"


class UrgencyLevel(str, Enum):
    """Urgency levels for message prioritization and scheduling."""
    CRITICAL = "critical"  # Send immediately
    HIGH = "high"          # Send within 1 hour
    NORMAL = "normal"      # Send during business hours
    LOW = "low"            # Batch and send daily


class CommunicationStatus(str, Enum):
    """Status of a communication throughout its lifecycle."""
    PENDING = "pending"
    QUEUED = "queued"
    SENT = "sent"
    DELIVERED = "delivered"
    OPENED = "opened"
    CLICKED = "clicked"
    FAILED = "failed"
    BOUNCED = "bounced"


@dataclass
class CommunicationRequest:
    """
    Request to send a communication to a client.
    
    This is the input to the CRM Agent Orchestrator from workflow nodes.
    """
    plan_id: str
    client_id: str
    message_type: MessageType
    context: Dict[str, Any]
    urgency: UrgencyLevel = UrgencyLevel.NORMAL
    preferred_channel: Optional[MessageChannel] = None

    def __post_init__(self):
        """Validate the communication request."""
        if not self.plan_id:
            raise ValueError("plan_id is required")
        if not self.client_id:
            raise ValueError("client_id is required")
        if not isinstance(self.message_type, MessageType):
            self.message_type = MessageType(self.message_type)
        if not isinstance(self.urgency, UrgencyLevel):
            self.urgency = UrgencyLevel(self.urgency)
        if self.preferred_channel and not isinstance(self.preferred_channel, MessageChannel):
            self.preferred_channel = MessageChannel(self.preferred_channel)


@dataclass
class CommunicationStrategy:
    """
    Strategy for delivering a communication.
    
    Determined by the Communication Strategy Tool based on message type,
    urgency, client preferences, and timing constraints.
    """
    primary_channel: MessageChannel
    fallback_channels: List[MessageChannel]
    send_time: datetime
    priority: int
    batch_with: Optional[List[str]] = None

    def __post_init__(self):
        """Validate the communication strategy."""
        if not isinstance(self.primary_channel, MessageChannel):
            self.primary_channel = MessageChannel(self.primary_channel)
        self.fallback_channels = [
            ch if isinstance(ch, MessageChannel) else MessageChannel(ch)
            for ch in self.fallback_channels
        ]
        if self.priority < 0 or self.priority > 10:
            raise ValueError("priority must be between 0 and 10")


@dataclass
class CommunicationResult:
    """
    Result of a communication attempt.
    
    Returned by the CRM Agent Orchestrator to workflow nodes.
    """
    communication_id: str
    status: CommunicationStatus
    channel_used: MessageChannel
    sent_at: Optional[datetime] = None
    delivered_at: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)

    def __post_init__(self):
        """Validate the communication result."""
        if not isinstance(self.status, CommunicationStatus):
            self.status = CommunicationStatus(self.status)
        if not isinstance(self.channel_used, MessageChannel):
            self.channel_used = MessageChannel(self.channel_used)

    @property
    def is_successful(self) -> bool:
        """Check if communication was successful."""
        return self.status in [
            CommunicationStatus.SENT,
            CommunicationStatus.DELIVERED,
            CommunicationStatus.OPENED,
            CommunicationStatus.CLICKED
        ]

    @property
    def delivery_time_seconds(self) -> Optional[float]:
        """Calculate delivery time in seconds."""
        if self.sent_at and self.delivered_at:
            return (self.delivered_at - self.sent_at).total_seconds()
        return None


@dataclass
class ClientPreferences:
    """
    Client communication preferences.
    
    Stored in the database and cached in Redis for quick access.
    """
    client_id: str
    preferred_channels: List[MessageChannel] = field(default_factory=lambda: [MessageChannel.EMAIL])
    timezone: str = "UTC"
    quiet_hours_start: str = "22:00"  # Format: "HH:MM"
    quiet_hours_end: str = "08:00"    # Format: "HH:MM"
    opt_out_email: bool = False
    opt_out_sms: bool = False
    opt_out_whatsapp: bool = False
    language_preference: str = "en"

    def __post_init__(self):
        """Validate client preferences."""
        if not self.client_id:
            raise ValueError("client_id is required")
        
        # Convert channels to MessageChannel enum
        self.preferred_channels = [
            ch if isinstance(ch, MessageChannel) else MessageChannel(ch)
            for ch in self.preferred_channels
        ]
        
        # Validate time format
        self._validate_time_format(self.quiet_hours_start, "quiet_hours_start")
        self._validate_time_format(self.quiet_hours_end, "quiet_hours_end")

    def _validate_time_format(self, time_str: str, field_name: str):
        """Validate time format HH:MM."""
        try:
            parts = time_str.split(":")
            if len(parts) != 2:
                raise ValueError
            hour, minute = int(parts[0]), int(parts[1])
            if not (0 <= hour <= 23 and 0 <= minute <= 59):
                raise ValueError
        except (ValueError, AttributeError):
            raise ValueError(f"{field_name} must be in HH:MM format (e.g., '22:00')")

    def get_available_channels(self) -> List[MessageChannel]:
        """Get list of channels that are not opted out."""
        available = []
        if not self.opt_out_email and MessageChannel.EMAIL in self.preferred_channels:
            available.append(MessageChannel.EMAIL)
        if not self.opt_out_sms and MessageChannel.SMS in self.preferred_channels:
            available.append(MessageChannel.SMS)
        if not self.opt_out_whatsapp and MessageChannel.WHATSAPP in self.preferred_channels:
            available.append(MessageChannel.WHATSAPP)
        
        # If all preferred channels are opted out, return non-opted-out channels
        if not available:
            if not self.opt_out_email:
                available.append(MessageChannel.EMAIL)
            if not self.opt_out_sms:
                available.append(MessageChannel.SMS)
            if not self.opt_out_whatsapp:
                available.append(MessageChannel.WHATSAPP)
        
        return available

    def is_channel_available(self, channel: MessageChannel) -> bool:
        """Check if a specific channel is available (not opted out)."""
        if channel == MessageChannel.EMAIL:
            return not self.opt_out_email
        elif channel == MessageChannel.SMS:
            return not self.opt_out_sms
        elif channel == MessageChannel.WHATSAPP:
            return not self.opt_out_whatsapp
        return False


@dataclass
class CommunicationTemplate:
    """
    Template for rendering messages.
    
    Loaded from database and cached for performance.
    """
    template_id: str
    template_name: str
    message_type: MessageType
    channel: MessageChannel
    subject_template: Optional[str]
    body_template: str
    variables: Dict[str, str]
    is_active: bool = True
    version: int = 1

    def __post_init__(self):
        """Validate template."""
        if not isinstance(self.message_type, MessageType):
            self.message_type = MessageType(self.message_type)
        if not isinstance(self.channel, MessageChannel):
            self.channel = MessageChannel(self.channel)

    def render(self, context: Dict[str, Any]) -> tuple[Optional[str], str]:
        """
        Render template with context variables.
        
        Returns:
            Tuple of (subject, body) with variables replaced
        """
        subject = None
        if self.subject_template:
            subject = self._replace_variables(self.subject_template, context)
        
        body = self._replace_variables(self.body_template, context)
        
        return subject, body

    def _replace_variables(self, template: str, context: Dict[str, Any]) -> str:
        """Replace {{variable}} placeholders with context values."""
        result = template
        for key, value in context.items():
            placeholder = f"{{{{{key}}}}}"
            result = result.replace(placeholder, str(value))
        return result


@dataclass
class DeliveryLog:
    """
    Log entry for a delivery attempt.
    
    Tracks API calls and responses for debugging and monitoring.
    """
    log_id: str
    communication_id: str
    channel: MessageChannel
    attempt_number: int
    api_provider: str
    api_request: Dict[str, Any]
    api_response: Dict[str, Any]
    status_code: Optional[int]
    success: bool
    error_details: Optional[str] = None
    delivery_time_ms: Optional[int] = None
    created_at: datetime = field(default_factory=datetime.utcnow)

    def __post_init__(self):
        """Validate delivery log."""
        if not isinstance(self.channel, MessageChannel):
            self.channel = MessageChannel(self.channel)
