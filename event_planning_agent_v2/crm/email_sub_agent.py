"""
Email Sub-Agent for CRM Communication Engine.

This module provides email composition, sending, attachment handling,
and engagement tracking capabilities using SMTP.
"""

import logging
import smtplib
import ssl
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
from pathlib import Path
from typing import Optional, List, Dict, Any, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timezone
import asyncio
from concurrent.futures import ThreadPoolExecutor
import uuid

from .models import (
    MessageType,
    MessageChannel,
    CommunicationStatus,
    CommunicationResult,
)
from .email_template_system import EmailTemplateSystem


logger = logging.getLogger(__name__)


@dataclass
class SMTPConfig:
    """Configuration for SMTP email sending."""
    host: str
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    timeout: int = 30
    max_connections: int = 5
    
    def __post_init__(self):
        """Validate SMTP configuration."""
        if not self.host:
            raise ValueError("SMTP host is required")
        if self.port <= 0 or self.port > 65535:
            raise ValueError("SMTP port must be between 1 and 65535")
        if self.use_tls and self.use_ssl:
            raise ValueError("Cannot use both TLS and SSL")


@dataclass
class Attachment:
    """Email attachment representation."""
    filename: str
    content: bytes
    content_type: str = "application/octet-stream"
    
    def __post_init__(self):
        """Validate attachment."""
        if not self.filename:
            raise ValueError("Attachment filename is required")
        if not self.content:
            raise ValueError("Attachment content is required")
        
        # Validate file size (max 10MB)
        max_size = 10 * 1024 * 1024  # 10MB
        if len(self.content) > max_size:
            raise ValueError(f"Attachment size exceeds maximum of {max_size} bytes")


@dataclass
class EmailResult:
    """Result of an email sending operation."""
    success: bool
    message_id: Optional[str] = None
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
            channel_used=MessageChannel.EMAIL,
            sent_at=self.sent_at,
            delivered_at=self.sent_at if self.success else None,
            error_message=self.error_message,
            metadata=self.metadata
        )


class AttachmentHandler:
    """
    Handles email attachments including PDFs and images.
    
    Features:
    - File validation (type, size)
    - MIME encoding
    - Content type detection
    """
    
    ALLOWED_EXTENSIONS = {
        '.pdf': 'application/pdf',
        '.png': 'image/png',
        '.jpg': 'image/jpeg',
        '.jpeg': 'image/jpeg',
        '.gif': 'image/gif',
        '.txt': 'text/plain',
        '.json': 'application/json',
    }
    
    MAX_ATTACHMENT_SIZE = 10 * 1024 * 1024  # 10MB
    
    @classmethod
    def create_attachment(
        cls,
        filepath: Path,
        filename: Optional[str] = None
    ) -> Attachment:
        """
        Create an attachment from a file.
        
        Args:
            filepath: Path to the file
            filename: Optional custom filename (defaults to file's name)
        
        Returns:
            Attachment object
        
        Raises:
            ValueError: If file is invalid or too large
            FileNotFoundError: If file doesn't exist
        """
        if not filepath.exists():
            raise FileNotFoundError(f"File not found: {filepath}")
        
        # Check file size
        file_size = filepath.stat().st_size
        if file_size > cls.MAX_ATTACHMENT_SIZE:
            raise ValueError(
                f"File size ({file_size} bytes) exceeds maximum "
                f"({cls.MAX_ATTACHMENT_SIZE} bytes)"
            )
        
        # Determine content type
        extension = filepath.suffix.lower()
        content_type = cls.ALLOWED_EXTENSIONS.get(
            extension,
            'application/octet-stream'
        )
        
        # Read file content
        with open(filepath, 'rb') as f:
            content = f.read()
        
        # Use custom filename or file's name
        attachment_filename = filename or filepath.name
        
        logger.debug(
            f"Created attachment: {attachment_filename} "
            f"({len(content)} bytes, {content_type})"
        )
        
        return Attachment(
            filename=attachment_filename,
            content=content,
            content_type=content_type
        )
    
    @classmethod
    def create_attachment_from_bytes(
        cls,
        content: bytes,
        filename: str,
        content_type: Optional[str] = None
    ) -> Attachment:
        """
        Create an attachment from bytes.
        
        Args:
            content: File content as bytes
            filename: Filename for the attachment
            content_type: MIME content type (auto-detected if not provided)
        
        Returns:
            Attachment object
        """
        # Auto-detect content type if not provided
        if content_type is None:
            extension = Path(filename).suffix.lower()
            content_type = cls.ALLOWED_EXTENSIONS.get(
                extension,
                'application/octet-stream'
            )
        
        return Attachment(
            filename=filename,
            content=content,
            content_type=content_type
        )
    
    @classmethod
    def attach_to_message(
        cls,
        message: MIMEMultipart,
        attachment: Attachment
    ) -> None:
        """
        Attach a file to a MIME message.
        
        Args:
            message: MIME message to attach to
            attachment: Attachment to add
        """
        part = MIMEBase(*attachment.content_type.split('/'))
        part.set_payload(attachment.content)
        encoders.encode_base64(part)
        part.add_header(
            'Content-Disposition',
            f'attachment; filename= {attachment.filename}'
        )
        message.attach(part)
        
        logger.debug(f"Attached file: {attachment.filename}")


class EmailSubAgent:
    """
    Email Sub-Agent for composing and sending emails.
    
    Features:
    - Template-based email composition
    - SMTP sending with connection pooling
    - Attachment handling
    - Engagement tracking (opens, clicks)
    - Delivery status logging
    """
    
    def __init__(
        self,
        smtp_config: SMTPConfig,
        template_system: EmailTemplateSystem,
        from_email: str,
        from_name: str = "Planiva Event Planning",
        repository=None
    ):
        """
        Initialize the Email Sub-Agent.
        
        Args:
            smtp_config: SMTP server configuration
            template_system: Email template system
            from_email: Sender email address
            from_name: Sender display name
            repository: Communication repository for logging (optional)
        """
        self.smtp_config = smtp_config
        self.template_system = template_system
        self.from_email = from_email
        self.from_name = from_name
        self.repository = repository
        
        # Thread pool for async SMTP operations
        self._executor = ThreadPoolExecutor(
            max_workers=smtp_config.max_connections
        )
        
        logger.info(
            f"EmailSubAgent initialized with SMTP {smtp_config.host}:{smtp_config.port}"
        )
    
    async def compose_and_send(
        self,
        recipient: str,
        message_type: MessageType,
        context: Dict[str, Any],
        attachments: Optional[List[Attachment]] = None,
        plan_id: Optional[str] = None,
        client_id: Optional[str] = None
    ) -> EmailResult:
        """
        Compose and send an email.
        
        Args:
            recipient: Recipient email address
            message_type: Type of email template to use
            context: Template context data
            attachments: Optional file attachments
            plan_id: Event plan ID for logging
            client_id: Client ID for logging
        
        Returns:
            EmailResult with delivery status
        """
        communication_id = str(uuid.uuid4())
        
        try:
            # Get template name for message type
            template_name = self.template_system.get_template_for_message_type(
                message_type
            )
            
            # Render template
            subject, html_body = self.template_system.render(
                template_name,
                context
            )
            
            logger.info(
                f"Composing email: {message_type.value} to {recipient} "
                f"(communication_id: {communication_id})"
            )
            
            # Create MIME message
            message = self._create_mime_message(
                recipient=recipient,
                subject=subject,
                html_body=html_body,
                attachments=attachments or []
            )
            
            # Send email (async)
            result = await self._send_email_async(
                message=message,
                recipient=recipient,
                communication_id=communication_id
            )
            
            # Log to database if repository is available
            if self.repository and plan_id and client_id:
                await self._log_to_database(
                    communication_id=communication_id,
                    plan_id=plan_id,
                    client_id=client_id,
                    message_type=message_type,
                    recipient=recipient,
                    subject=subject,
                    html_body=html_body,
                    result=result
                )
            
            return result
            
        except Exception as e:
            logger.error(
                f"Failed to compose/send email to {recipient}: {e}",
                exc_info=True
            )
            return EmailResult(
                success=False,
                error_message=str(e),
                recipient=recipient,
                metadata={
                    'message_type': message_type.value,
                    'communication_id': communication_id
                }
            )
    
    def _create_mime_message(
        self,
        recipient: str,
        subject: str,
        html_body: str,
        attachments: List[Attachment]
    ) -> MIMEMultipart:
        """
        Create a MIME multipart message.
        
        Args:
            recipient: Recipient email address
            subject: Email subject
            html_body: HTML email body
            attachments: List of attachments
        
        Returns:
            MIMEMultipart message
        """
        message = MIMEMultipart('alternative')
        message['From'] = f"{self.from_name} <{self.from_email}>"
        message['To'] = recipient
        message['Subject'] = subject
        
        # Add HTML body
        html_part = MIMEText(html_body, 'html', 'utf-8')
        message.attach(html_part)
        
        # Add attachments
        for attachment in attachments:
            AttachmentHandler.attach_to_message(message, attachment)
        
        return message
    
    async def _send_email_async(
        self,
        message: MIMEMultipart,
        recipient: str,
        communication_id: str
    ) -> EmailResult:
        """
        Send email asynchronously using thread pool.
        
        Args:
            message: MIME message to send
            recipient: Recipient email address
            communication_id: Unique communication ID
        
        Returns:
            EmailResult with delivery status
        """
        loop = asyncio.get_event_loop()
        
        try:
            # Run SMTP send in thread pool
            await loop.run_in_executor(
                self._executor,
                self._send_email_sync,
                message,
                recipient
            )
            
            sent_at = datetime.now(timezone.utc)
            
            logger.info(
                f"Email sent successfully to {recipient} "
                f"(communication_id: {communication_id})"
            )
            
            return EmailResult(
                success=True,
                message_id=communication_id,
                sent_at=sent_at,
                recipient=recipient,
                metadata={
                    'communication_id': communication_id,
                    'smtp_host': self.smtp_config.host
                }
            )
            
        except Exception as e:
            logger.error(
                f"Failed to send email to {recipient}: {e}",
                exc_info=True
            )
            return EmailResult(
                success=False,
                error_message=str(e),
                recipient=recipient,
                metadata={
                    'communication_id': communication_id,
                    'smtp_host': self.smtp_config.host
                }
            )
    
    def _send_email_sync(
        self,
        message: MIMEMultipart,
        recipient: str
    ) -> None:
        """
        Send email synchronously via SMTP.
        
        Args:
            message: MIME message to send
            recipient: Recipient email address
        
        Raises:
            Exception: If SMTP send fails
        """
        context = None
        if self.smtp_config.use_tls or self.smtp_config.use_ssl:
            context = ssl.create_default_context()
        
        # Choose SMTP class based on SSL/TLS configuration
        if self.smtp_config.use_ssl:
            smtp_class = smtplib.SMTP_SSL
        else:
            smtp_class = smtplib.SMTP
        
        with smtp_class(
            self.smtp_config.host,
            self.smtp_config.port,
            timeout=self.smtp_config.timeout
        ) as server:
            # Enable debug output if log level is DEBUG
            if logger.isEnabledFor(logging.DEBUG):
                server.set_debuglevel(1)
            
            # Start TLS if configured
            if self.smtp_config.use_tls and not self.smtp_config.use_ssl:
                server.starttls(context=context)
            
            # Login if credentials provided
            if self.smtp_config.username and self.smtp_config.password:
                server.login(
                    self.smtp_config.username,
                    self.smtp_config.password
                )
            
            # Send email
            server.send_message(message)
            
            logger.debug(f"SMTP send completed for {recipient}")
    
    async def track_engagement(
        self,
        communication_id: str,
        event_type: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> None:
        """
        Track email engagement events (opens, clicks).
        
        Args:
            communication_id: Unique communication ID
            event_type: Type of engagement ('opened', 'clicked')
            metadata: Additional event metadata
        """
        try:
            if not self.repository:
                logger.warning(
                    "Cannot track engagement: repository not configured"
                )
                return
            
            # Update communication status based on event type
            if event_type == 'opened':
                status = CommunicationStatus.OPENED
                timestamp_field = 'opened_at'
            elif event_type == 'clicked':
                status = CommunicationStatus.CLICKED
                timestamp_field = 'clicked_at'
            else:
                logger.warning(f"Unknown engagement event type: {event_type}")
                return
            
            # Update in database (repository methods are synchronous)
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self.repository.update_status(
                    communication_id=communication_id,
                    status=status,
                    error_message=None,
                    metadata=metadata or {}
                )
            )
            
            logger.info(
                f"Tracked engagement: {event_type} for "
                f"communication_id: {communication_id}"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to track engagement for {communication_id}: {e}",
                exc_info=True
            )
    
    async def _log_to_database(
        self,
        communication_id: str,
        plan_id: str,
        client_id: str,
        message_type: MessageType,
        recipient: str,
        subject: str,
        html_body: str,
        result: EmailResult
    ) -> None:
        """
        Log communication to database.
        
        Args:
            communication_id: Unique communication ID
            plan_id: Event plan ID
            client_id: Client ID
            message_type: Type of message
            recipient: Recipient email
            subject: Email subject
            html_body: Email body
            result: Email send result
        """
        try:
            if not self.repository:
                return
            
            # Run database operations in executor (repository methods are synchronous)
            loop = asyncio.get_event_loop()
            
            # Save communication record (creates with PENDING status)
            from .models import UrgencyLevel
            saved_comm_id = await loop.run_in_executor(
                None,
                lambda: self.repository.save_communication(
                    plan_id=plan_id,
                    client_id=client_id,
                    message_type=message_type,
                    channel=MessageChannel.EMAIL,
                    urgency=UrgencyLevel.NORMAL,
                    subject=subject,
                    body=html_body[:1000],  # Truncate for storage
                    template_name=self.template_system.get_template_for_message_type(message_type),
                    context_data={
                        'recipient': recipient,
                        'communication_id': communication_id
                    },
                    metadata={
                        'smtp_host': self.smtp_config.host,
                        'original_communication_id': communication_id
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
                        'sent_at': result.sent_at.isoformat() if result.sent_at else None
                    }
                )
            )
            
            logger.debug(
                f"Logged communication to database: {saved_comm_id} "
                f"(original ID: {communication_id})"
            )
            
        except Exception as e:
            logger.error(
                f"Failed to log communication to database: {e}",
                exc_info=True
            )
    
    def close(self):
        """Close the email sub-agent and cleanup resources."""
        self._executor.shutdown(wait=True)
        logger.info("EmailSubAgent closed")
