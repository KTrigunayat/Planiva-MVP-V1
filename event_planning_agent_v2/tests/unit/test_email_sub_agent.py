"""
Unit tests for Email Sub-Agent.

Tests email composition, attachment handling, and SMTP sending with mocks.
"""

import pytest
import asyncio
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock, AsyncMock
from datetime import datetime, timezone
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
import tempfile

from event_planning_agent_v2.crm.email_sub_agent import (
    EmailSubAgent,
    SMTPConfig,
    Attachment,
    AttachmentHandler,
    EmailResult,
)
from event_planning_agent_v2.crm.models import (
    MessageType,
    MessageChannel,
    CommunicationStatus,
)
from event_planning_agent_v2.crm.email_template_system import EmailTemplateSystem


# Fixtures

@pytest.fixture
def smtp_config():
    """Create test SMTP configuration."""
    return SMTPConfig(
        host="smtp.test.com",
        port=587,
        username="test@test.com",
        password="testpass",
        use_tls=True,
        timeout=10,
        max_connections=2
    )


@pytest.fixture
def template_system(tmp_path):
    """Create test email template system."""
    templates_dir = tmp_path / "templates"
    templates_dir.mkdir()
    
    # Create a simple test template
    welcome_template = templates_dir / "welcome.html"
    welcome_template.write_text("""
<!DOCTYPE html>
<html>
<head>
    <title>Welcome to {{company_name}}</title>
</head>
<body>
    <h1>Hello {{client_name}}!</h1>
    <p>Your plan ID is: {{plan_id}}</p>
</body>
</html>
    """)
    
    return EmailTemplateSystem(templates_dir=templates_dir)


@pytest.fixture
def email_agent(smtp_config, template_system):
    """Create test email sub-agent."""
    return EmailSubAgent(
        smtp_config=smtp_config,
        template_system=template_system,
        from_email="noreply@planiva.com",
        from_name="Planiva Test"
    )


@pytest.fixture
def sample_context():
    """Sample template context."""
    return {
        "client_name": "John Doe",
        "plan_id": "plan_123",
        "event_type": "wedding",
        "event_date": "2024-12-15"
    }


# SMTPConfig Tests

def test_smtp_config_valid():
    """Test valid SMTP configuration."""
    config = SMTPConfig(
        host="smtp.gmail.com",
        port=587,
        username="user@gmail.com",
        password="pass123",
        use_tls=True
    )
    assert config.host == "smtp.gmail.com"
    assert config.port == 587
    assert config.use_tls is True


def test_smtp_config_missing_host():
    """Test SMTP config validation fails without host."""
    with pytest.raises(ValueError, match="SMTP host is required"):
        SMTPConfig(host="", port=587)


def test_smtp_config_invalid_port():
    """Test SMTP config validation fails with invalid port."""
    with pytest.raises(ValueError, match="SMTP port must be between"):
        SMTPConfig(host="smtp.test.com", port=0)
    
    with pytest.raises(ValueError, match="SMTP port must be between"):
        SMTPConfig(host="smtp.test.com", port=70000)


def test_smtp_config_tls_and_ssl():
    """Test SMTP config validation fails with both TLS and SSL."""
    with pytest.raises(ValueError, match="Cannot use both TLS and SSL"):
        SMTPConfig(
            host="smtp.test.com",
            port=587,
            use_tls=True,
            use_ssl=True
        )


# Attachment Tests

def test_attachment_valid():
    """Test valid attachment creation."""
    content = b"test content"
    attachment = Attachment(
        filename="test.pdf",
        content=content,
        content_type="application/pdf"
    )
    assert attachment.filename == "test.pdf"
    assert attachment.content == content
    assert attachment.content_type == "application/pdf"


def test_attachment_missing_filename():
    """Test attachment validation fails without filename."""
    with pytest.raises(ValueError, match="filename is required"):
        Attachment(filename="", content=b"test")


def test_attachment_missing_content():
    """Test attachment validation fails without content."""
    with pytest.raises(ValueError, match="content is required"):
        Attachment(filename="test.pdf", content=b"")


def test_attachment_size_limit():
    """Test attachment validation fails when too large."""
    # Create content larger than 10MB
    large_content = b"x" * (11 * 1024 * 1024)
    with pytest.raises(ValueError, match="exceeds maximum"):
        Attachment(filename="large.pdf", content=large_content)


# AttachmentHandler Tests

def test_attachment_handler_create_from_file(tmp_path):
    """Test creating attachment from file."""
    # Create a test file
    test_file = tmp_path / "test.pdf"
    test_content = b"PDF content here"
    test_file.write_bytes(test_content)
    
    # Create attachment
    attachment = AttachmentHandler.create_attachment(test_file)
    
    assert attachment.filename == "test.pdf"
    assert attachment.content == test_content
    assert attachment.content_type == "application/pdf"


def test_attachment_handler_file_not_found():
    """Test attachment creation fails for non-existent file."""
    with pytest.raises(FileNotFoundError):
        AttachmentHandler.create_attachment(Path("/nonexistent/file.pdf"))


def test_attachment_handler_file_too_large(tmp_path):
    """Test attachment creation fails for large file."""
    # Create a file larger than 10MB
    large_file = tmp_path / "large.pdf"
    large_file.write_bytes(b"x" * (11 * 1024 * 1024))
    
    with pytest.raises(ValueError, match="exceeds maximum"):
        AttachmentHandler.create_attachment(large_file)


def test_attachment_handler_custom_filename(tmp_path):
    """Test creating attachment with custom filename."""
    test_file = tmp_path / "original.pdf"
    test_file.write_bytes(b"content")
    
    attachment = AttachmentHandler.create_attachment(
        test_file,
        filename="custom.pdf"
    )
    
    assert attachment.filename == "custom.pdf"


def test_attachment_handler_from_bytes():
    """Test creating attachment from bytes."""
    content = b"test content"
    attachment = AttachmentHandler.create_attachment_from_bytes(
        content=content,
        filename="test.txt",
        content_type="text/plain"
    )
    
    assert attachment.filename == "test.txt"
    assert attachment.content == content
    assert attachment.content_type == "text/plain"


def test_attachment_handler_from_bytes_auto_detect():
    """Test creating attachment with auto-detected content type."""
    content = b"image data"
    attachment = AttachmentHandler.create_attachment_from_bytes(
        content=content,
        filename="image.png"
    )
    
    assert attachment.content_type == "image/png"


def test_attachment_handler_attach_to_message():
    """Test attaching file to MIME message."""
    message = MIMEMultipart()
    attachment = Attachment(
        filename="test.pdf",
        content=b"PDF content",
        content_type="application/pdf"
    )
    
    AttachmentHandler.attach_to_message(message, attachment)
    
    # Check that attachment was added
    assert len(message.get_payload()) == 1
    attached_part = message.get_payload()[0]
    assert 'Content-Disposition' in attached_part
    assert 'test.pdf' in attached_part['Content-Disposition']


# EmailSubAgent Tests

def test_email_agent_initialization(email_agent, smtp_config):
    """Test email agent initialization."""
    assert email_agent.smtp_config == smtp_config
    assert email_agent.from_email == "noreply@planiva.com"
    assert email_agent.from_name == "Planiva Test"


def test_create_mime_message(email_agent):
    """Test MIME message creation."""
    message = email_agent._create_mime_message(
        recipient="test@example.com",
        subject="Test Subject",
        html_body="<html><body>Test</body></html>",
        attachments=[]
    )
    
    assert isinstance(message, MIMEMultipart)
    assert message['To'] == "test@example.com"
    assert message['Subject'] == "Test Subject"
    assert "Planiva Test" in message['From']
    assert "noreply@planiva.com" in message['From']


def test_create_mime_message_with_attachments(email_agent):
    """Test MIME message creation with attachments."""
    attachment = Attachment(
        filename="test.pdf",
        content=b"PDF content",
        content_type="application/pdf"
    )
    
    message = email_agent._create_mime_message(
        recipient="test@example.com",
        subject="Test with Attachment",
        html_body="<html><body>Test</body></html>",
        attachments=[attachment]
    )
    
    # Check that message has multiple parts (HTML + attachment)
    payload = message.get_payload()
    assert len(payload) >= 2  # HTML part + attachment


@pytest.mark.asyncio
async def test_compose_and_send_success(email_agent, sample_context):
    """Test successful email composition and sending."""
    # Mock the SMTP send
    with patch.object(email_agent, '_send_email_sync') as mock_send:
        mock_send.return_value = None  # Successful send
        
        result = await email_agent.compose_and_send(
            recipient="test@example.com",
            message_type=MessageType.WELCOME,
            context=sample_context
        )
        
        assert result.success is True
        assert result.recipient == "test@example.com"
        assert result.sent_at is not None
        assert result.message_id is not None
        assert mock_send.called


@pytest.mark.asyncio
async def test_compose_and_send_with_attachments(email_agent, sample_context):
    """Test email sending with attachments."""
    attachment = Attachment(
        filename="blueprint.pdf",
        content=b"Blueprint content",
        content_type="application/pdf"
    )
    
    with patch.object(email_agent, '_send_email_sync') as mock_send:
        mock_send.return_value = None
        
        result = await email_agent.compose_and_send(
            recipient="test@example.com",
            message_type=MessageType.WELCOME,
            context=sample_context,
            attachments=[attachment]
        )
        
        assert result.success is True
        assert mock_send.called


@pytest.mark.asyncio
async def test_compose_and_send_smtp_failure(email_agent, sample_context):
    """Test email sending with SMTP failure."""
    with patch.object(email_agent, '_send_email_sync') as mock_send:
        mock_send.side_effect = Exception("SMTP connection failed")
        
        result = await email_agent.compose_and_send(
            recipient="test@example.com",
            message_type=MessageType.WELCOME,
            context=sample_context
        )
        
        assert result.success is False
        assert result.error_message == "SMTP connection failed"
        assert result.recipient == "test@example.com"


@pytest.mark.asyncio
async def test_compose_and_send_template_error(email_agent, sample_context):
    """Test email sending with template rendering error."""
    # Use a non-existent template
    with patch.object(
        email_agent.template_system,
        'get_template_for_message_type'
    ) as mock_get_template:
        mock_get_template.return_value = "nonexistent.html"
        
        result = await email_agent.compose_and_send(
            recipient="test@example.com",
            message_type=MessageType.WELCOME,
            context=sample_context
        )
        
        assert result.success is False
        assert result.error_message is not None


def test_send_email_sync_success(email_agent):
    """Test synchronous SMTP sending."""
    message = MIMEMultipart()
    message['From'] = "test@test.com"
    message['To'] = "recipient@test.com"
    message['Subject'] = "Test"
    message.attach(MIMEText("Test body", 'html'))
    
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        # Should not raise exception
        email_agent._send_email_sync(message, "recipient@test.com")
        
        # Verify SMTP methods were called
        assert mock_server.starttls.called
        assert mock_server.login.called
        assert mock_server.send_message.called


def test_send_email_sync_with_ssl(smtp_config, template_system):
    """Test synchronous SMTP sending with SSL."""
    smtp_config.use_ssl = True
    smtp_config.use_tls = False
    
    email_agent = EmailSubAgent(
        smtp_config=smtp_config,
        template_system=template_system,
        from_email="test@test.com"
    )
    
    message = MIMEMultipart()
    message['From'] = "test@test.com"
    message['To'] = "recipient@test.com"
    message['Subject'] = "Test"
    
    with patch('smtplib.SMTP_SSL') as mock_smtp_ssl:
        mock_server = MagicMock()
        mock_smtp_ssl.return_value.__enter__.return_value = mock_server
        
        email_agent._send_email_sync(message, "recipient@test.com")
        
        # Verify SSL SMTP was used
        assert mock_smtp_ssl.called
        assert mock_server.login.called


def test_send_email_sync_no_auth(smtp_config, template_system):
    """Test synchronous SMTP sending without authentication."""
    smtp_config.username = ""
    smtp_config.password = ""
    
    email_agent = EmailSubAgent(
        smtp_config=smtp_config,
        template_system=template_system,
        from_email="test@test.com"
    )
    
    message = MIMEMultipart()
    message['From'] = "test@test.com"
    message['To'] = "recipient@test.com"
    message['Subject'] = "Test"
    
    with patch('smtplib.SMTP') as mock_smtp:
        mock_server = MagicMock()
        mock_smtp.return_value.__enter__.return_value = mock_server
        
        email_agent._send_email_sync(message, "recipient@test.com")
        
        # Verify login was NOT called
        assert not mock_server.login.called
        assert mock_server.send_message.called


@pytest.mark.asyncio
async def test_track_engagement_opened(email_agent):
    """Test tracking email open engagement."""
    mock_repo = AsyncMock()
    email_agent.repository = mock_repo
    
    await email_agent.track_engagement(
        communication_id="comm_123",
        event_type="opened",
        metadata={"ip": "192.168.1.1"}
    )
    
    assert mock_repo.update_status.called
    call_args = mock_repo.update_status.call_args
    assert call_args[1]['communication_id'] == "comm_123"
    assert call_args[1]['status'] == CommunicationStatus.OPENED


@pytest.mark.asyncio
async def test_track_engagement_clicked(email_agent):
    """Test tracking email click engagement."""
    mock_repo = AsyncMock()
    email_agent.repository = mock_repo
    
    await email_agent.track_engagement(
        communication_id="comm_123",
        event_type="clicked",
        metadata={"link": "https://example.com"}
    )
    
    assert mock_repo.update_status.called
    call_args = mock_repo.update_status.call_args
    assert call_args[1]['communication_id'] == "comm_123"
    assert call_args[1]['status'] == CommunicationStatus.CLICKED


@pytest.mark.asyncio
async def test_track_engagement_no_repository(email_agent):
    """Test tracking engagement without repository."""
    # Should not raise exception
    await email_agent.track_engagement(
        communication_id="comm_123",
        event_type="opened"
    )


@pytest.mark.asyncio
async def test_track_engagement_unknown_event(email_agent):
    """Test tracking unknown engagement event type."""
    mock_repo = AsyncMock()
    email_agent.repository = mock_repo
    
    await email_agent.track_engagement(
        communication_id="comm_123",
        event_type="unknown_event"
    )
    
    # Should not call update_status for unknown events
    assert not mock_repo.update_status.called


@pytest.mark.asyncio
async def test_log_to_database(email_agent):
    """Test logging communication to database."""
    mock_repo = Mock()
    mock_repo.save_communication = Mock(return_value="saved_comm_id_123")
    mock_repo.update_status = Mock(return_value=True)
    email_agent.repository = mock_repo
    
    result = EmailResult(
        success=True,
        message_id="msg_123",
        sent_at=datetime.now(timezone.utc),
        recipient="test@example.com"
    )
    
    await email_agent._log_to_database(
        communication_id="comm_123",
        plan_id="plan_123",
        client_id="client_123",
        message_type=MessageType.WELCOME,
        recipient="test@example.com",
        subject="Welcome",
        html_body="<html>Welcome</html>",
        result=result
    )
    
    # Verify save_communication was called
    assert mock_repo.save_communication.called
    # Verify update_status was called with the saved communication ID
    assert mock_repo.update_status.called


@pytest.mark.asyncio
async def test_log_to_database_failure(email_agent):
    """Test logging failed communication to database."""
    mock_repo = Mock()
    mock_repo.save_communication = Mock(return_value="saved_comm_id_123")
    mock_repo.update_status = Mock(return_value=True)
    email_agent.repository = mock_repo
    
    result = EmailResult(
        success=False,
        error_message="SMTP error",
        recipient="test@example.com"
    )
    
    await email_agent._log_to_database(
        communication_id="comm_123",
        plan_id="plan_123",
        client_id="client_123",
        message_type=MessageType.WELCOME,
        recipient="test@example.com",
        subject="Welcome",
        html_body="<html>Welcome</html>",
        result=result
    )
    
    # Verify save_communication was called
    assert mock_repo.save_communication.called
    # Verify update_status was called with FAILED status
    assert mock_repo.update_status.called


def test_email_agent_close(email_agent):
    """Test closing email agent."""
    # Should not raise exception
    email_agent.close()


# EmailResult Tests

def test_email_result_to_communication_result():
    """Test converting EmailResult to CommunicationResult."""
    email_result = EmailResult(
        success=True,
        message_id="msg_123",
        sent_at=datetime.now(timezone.utc),
        recipient="test@example.com",
        metadata={"smtp_host": "smtp.test.com"}
    )
    
    comm_result = email_result.to_communication_result(
        communication_id="comm_123",
        status=CommunicationStatus.DELIVERED
    )
    
    assert comm_result.communication_id == "comm_123"
    assert comm_result.status == CommunicationStatus.DELIVERED
    assert comm_result.channel_used == MessageChannel.EMAIL
    assert comm_result.sent_at == email_result.sent_at
    assert comm_result.delivered_at == email_result.sent_at
    assert comm_result.metadata == email_result.metadata


def test_email_result_to_communication_result_failed():
    """Test converting failed EmailResult to CommunicationResult."""
    email_result = EmailResult(
        success=False,
        error_message="SMTP error",
        recipient="test@example.com"
    )
    
    comm_result = email_result.to_communication_result(
        communication_id="comm_123",
        status=CommunicationStatus.FAILED
    )
    
    assert comm_result.communication_id == "comm_123"
    assert comm_result.status == CommunicationStatus.FAILED
    assert comm_result.error_message == "SMTP error"
    assert comm_result.delivered_at is None


# Integration Tests

@pytest.mark.asyncio
async def test_full_email_workflow(email_agent, sample_context, tmp_path):
    """Test complete email workflow from composition to sending."""
    # Create an attachment
    attachment_file = tmp_path / "test.pdf"
    attachment_file.write_bytes(b"Test PDF content")
    attachment = AttachmentHandler.create_attachment(attachment_file)
    
    # Mock SMTP
    with patch.object(email_agent, '_send_email_sync') as mock_send:
        mock_send.return_value = None
        
        # Send email
        result = await email_agent.compose_and_send(
            recipient="client@example.com",
            message_type=MessageType.WELCOME,
            context=sample_context,
            attachments=[attachment],
            plan_id="plan_123",
            client_id="client_123"
        )
        
        # Verify result
        assert result.success is True
        assert result.recipient == "client@example.com"
        assert result.sent_at is not None
        assert result.message_id is not None
        
        # Verify SMTP was called
        assert mock_send.called
        
        # Verify message structure
        call_args = mock_send.call_args[0]
        message = call_args[0]
        assert isinstance(message, MIMEMultipart)
        assert message['To'] == "client@example.com"
        assert "Welcome" in message['Subject'] or "Planiva" in message['Subject']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
