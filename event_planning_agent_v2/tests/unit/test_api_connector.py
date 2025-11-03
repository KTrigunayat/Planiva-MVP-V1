"""
Unit tests for API Connector.

Tests WhatsApp and Twilio API integration with mocks, webhook handling,
and rate limiting logic.
"""

import pytest
import pytest_asyncio
import asyncio
from unittest.mock import Mock, patch, AsyncMock, MagicMock
from datetime import datetime, timezone, timedelta
from aiohttp import ClientSession, ClientTimeout
import json

from event_planning_agent_v2.crm.api_connector import (
    APIConnector,
    WhatsAppConfig,
    TwilioConfig,
    APIResponse,
    WebhookResult,
    RateLimitInfo,
    ErrorCategory,
)


# Fixtures

@pytest.fixture
def whatsapp_config():
    """Create test WhatsApp configuration."""
    return WhatsAppConfig(
        phone_number_id="123456789",
        access_token="test_access_token",
        webhook_verify_token="test_verify_token"
    )


@pytest.fixture
def twilio_config():
    """Create test Twilio configuration."""
    return TwilioConfig(
        account_sid="AC1234567890",
        auth_token="test_auth_token",
        from_number="+15551234567"
    )


@pytest_asyncio.fixture
async def api_connector(whatsapp_config, twilio_config):
    """Create test API connector."""
    connector = APIConnector(
        whatsapp_config=whatsapp_config,
        twilio_config=twilio_config
    )
    yield connector
    await connector.close()


# Configuration Tests

def test_whatsapp_config_valid(whatsapp_config):
    """Test valid WhatsApp configuration."""
    assert whatsapp_config.phone_number_id == "123456789"
    assert whatsapp_config.access_token == "test_access_token"


def test_whatsapp_config_missing_phone_number_id():
    """Test WhatsApp config validation fails without phone_number_id."""
    with pytest.raises(ValueError, match="phone_number_id is required"):
        WhatsAppConfig(
            phone_number_id="",
            access_token="token",
            webhook_verify_token="verify"
        )


def test_whatsapp_config_missing_access_token():
    """Test WhatsApp config validation fails without access_token."""
    with pytest.raises(ValueError, match="access_token is required"):
        WhatsAppConfig(
            phone_number_id="123",
            access_token="",
            webhook_verify_token="verify"
        )


def test_twilio_config_valid(twilio_config):
    """Test valid Twilio configuration."""
    assert twilio_config.account_sid == "AC1234567890"
    assert twilio_config.auth_token == "test_auth_token"
    assert twilio_config.from_number == "+15551234567"


def test_twilio_config_missing_account_sid():
    """Test Twilio config validation fails without account_sid."""
    with pytest.raises(ValueError, match="account_sid is required"):
        TwilioConfig(
            account_sid="",
            auth_token="token",
            from_number="+1234567890"
        )


def test_twilio_config_missing_from_number():
    """Test Twilio config validation fails without from_number."""
    with pytest.raises(ValueError, match="from_number is required"):
        TwilioConfig(
            account_sid="AC123",
            auth_token="token",
            from_number=""
        )


# APIConnector Initialization Tests

@pytest.mark.asyncio
async def test_api_connector_initialization(whatsapp_config, twilio_config):
    """Test API connector initialization."""
    connector = APIConnector(
        whatsapp_config=whatsapp_config,
        twilio_config=twilio_config
    )
    
    assert connector.whatsapp_config == whatsapp_config
    assert connector.twilio_config == twilio_config
    assert connector._session is None
    
    await connector.close()


@pytest.mark.asyncio
async def test_api_connector_context_manager(whatsapp_config, twilio_config):
    """Test API connector as async context manager."""
    async with APIConnector(
        whatsapp_config=whatsapp_config,
        twilio_config=twilio_config
    ) as connector:
        assert connector._session is not None
        assert not connector._session.closed


# WhatsApp API Tests

@pytest.mark.asyncio
async def test_send_whatsapp_message_success(api_connector):
    """Test successful WhatsApp message sending."""
    mock_response = {
        "messages": [{"id": "wamid.123456"}]
    }
    
    # Ensure session is created
    await api_connector._ensure_session()
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        mock_post.return_value = mock_resp
        
        result = await api_connector.send_whatsapp_message(
            phone_number="+15551234567",
            message="Test message"
        )
        
        assert result.success is True
        assert result.message_id == "wamid.123456"
        assert result.status == "sent"


@pytest.mark.asyncio
async def test_send_whatsapp_message_with_media(api_connector):
    """Test WhatsApp message with media URL."""
    mock_response = {
        "messages": [{"id": "wamid.789"}]
    }
    
    await api_connector._ensure_session()
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 200
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        mock_post.return_value = mock_resp
        
        result = await api_connector.send_whatsapp_message(
            phone_number="+15551234567",
            message="Check this out",
            media_url="https://example.com/image.jpg"
        )
        
        assert result.success is True


@pytest.mark.asyncio
async def test_send_whatsapp_message_auth_failure(api_connector):
    """Test WhatsApp message with authentication failure."""
    mock_response = {
        "error": {
            "code": 190,
            "message": "Invalid OAuth access token"
        }
    }
    
    await api_connector._ensure_session()
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 401
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        mock_post.return_value = mock_resp
        
        result = await api_connector.send_whatsapp_message(
            phone_number="+15551234567",
            message="Test"
        )
        
        assert result.success is False
        assert result.error_category == ErrorCategory.AUTH_FAILURE


@pytest.mark.asyncio
async def test_send_whatsapp_message_rate_limit(api_connector):
    """Test WhatsApp message with rate limit error."""
    mock_response = {
        "error": {
            "code": 4,
            "message": "Rate limit exceeded"
        }
    }
    
    await api_connector._ensure_session()
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 429
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        mock_post.return_value = mock_resp
        
        result = await api_connector.send_whatsapp_message(
            phone_number="+15551234567",
            message="Test"
        )
        
        assert result.success is False
        assert result.error_category == ErrorCategory.RATE_LIMIT


@pytest.mark.asyncio
async def test_send_whatsapp_message_no_config():
    """Test WhatsApp message without configuration."""
    connector = APIConnector()
    
    result = await connector.send_whatsapp_message(
        phone_number="+15551234567",
        message="Test"
    )
    
    assert result.success is False
    assert result.error_category == ErrorCategory.INVALID_INPUT


# Twilio SMS API Tests

@pytest.mark.asyncio
async def test_send_sms_message_success(api_connector):
    """Test successful SMS sending via Twilio."""
    mock_response = {
        "sid": "SM123456",
        "status": "queued"
    }
    
    await api_connector._ensure_session()
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 201
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        mock_post.return_value = mock_resp
        
        result = await api_connector.send_sms_message(
            phone_number="+15559876543",
            message="Test SMS"
        )
        
        assert result.success is True
        assert result.message_id == "SM123456"
        assert result.status == "queued"


@pytest.mark.asyncio
async def test_send_sms_message_auth_failure(api_connector):
    """Test SMS sending with authentication failure."""
    mock_response = {
        "code": 20003,
        "message": "Authenticate"
    }
    
    await api_connector._ensure_session()
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 401
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        mock_post.return_value = mock_resp
        
        result = await api_connector.send_sms_message(
            phone_number="+15559876543",
            message="Test"
        )
        
        assert result.success is False
        assert result.error_category == ErrorCategory.AUTH_FAILURE


@pytest.mark.asyncio
async def test_send_sms_message_invalid_number(api_connector):
    """Test SMS sending with invalid phone number."""
    mock_response = {
        "code": 21211,
        "message": "Invalid 'To' Phone Number"
    }
    
    await api_connector._ensure_session()
    
    with patch('aiohttp.ClientSession.post') as mock_post:
        mock_resp = AsyncMock()
        mock_resp.status = 400
        mock_resp.json = AsyncMock(return_value=mock_response)
        mock_resp.__aenter__ = AsyncMock(return_value=mock_resp)
        mock_resp.__aexit__ = AsyncMock(return_value=None)
        mock_post.return_value = mock_resp
        
        result = await api_connector.send_sms_message(
            phone_number="invalid",
            message="Test"
        )
        
        assert result.success is False
        assert result.error_category == ErrorCategory.INVALID_INPUT


@pytest.mark.asyncio
async def test_send_sms_message_no_config():
    """Test SMS sending without configuration."""
    connector = APIConnector()
    
    result = await connector.send_sms_message(
        phone_number="+15551234567",
        message="Test"
    )
    
    assert result.success is False
    assert result.error_category == ErrorCategory.INVALID_INPUT


# Webhook Handling Tests

@pytest.mark.asyncio
async def test_handle_whatsapp_webhook_status(api_connector):
    """Test handling WhatsApp status webhook."""
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid.123",
                        "status": "delivered",
                        "timestamp": "1234567890"
                    }]
                }
            }]
        }]
    }
    
    result = await api_connector.handle_webhook(webhook_data, "whatsapp")
    
    assert result.success is True
    assert result.message_id == "wamid.123"
    assert result.status == "delivered"


@pytest.mark.asyncio
async def test_handle_whatsapp_webhook_incoming_message(api_connector):
    """Test handling WhatsApp incoming message webhook."""
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "id": "wamid.456",
                        "from": "+15551234567",
                        "type": "text",
                        "timestamp": "1234567890",
                        "text": {"body": "Hello"}
                    }]
                }
            }]
        }]
    }
    
    result = await api_connector.handle_webhook(webhook_data, "whatsapp")
    
    assert result.success is True
    assert result.message_id == "wamid.456"
    assert result.status == "received"
    assert result.metadata["content"] == "Hello"


@pytest.mark.asyncio
async def test_handle_twilio_webhook_status(api_connector):
    """Test handling Twilio status webhook."""
    webhook_data = {
        "MessageSid": "SM123456",
        "MessageStatus": "delivered",
        "From": "+15551234567",
        "To": "+15559876543"
    }
    
    result = await api_connector.handle_webhook(webhook_data, "twilio")
    
    assert result.success is True
    assert result.message_id == "SM123456"
    assert result.status == "delivered"


@pytest.mark.asyncio
async def test_handle_webhook_auto_detect_whatsapp(api_connector):
    """Test auto-detecting WhatsApp webhook."""
    webhook_data = {
        "entry": [{
            "changes": [{
                "value": {
                    "statuses": [{
                        "id": "wamid.789",
                        "status": "sent",
                        "timestamp": "1234567890"
                    }]
                }
            }]
        }]
    }
    
    result = await api_connector.handle_webhook(webhook_data, "auto")
    
    assert result.success is True
    assert result.message_id == "wamid.789"


@pytest.mark.asyncio
async def test_handle_webhook_auto_detect_twilio(api_connector):
    """Test auto-detecting Twilio webhook."""
    webhook_data = {
        "SmsSid": "SM789",
        "SmsStatus": "sent"
    }
    
    result = await api_connector.handle_webhook(webhook_data, "auto")
    
    assert result.success is True
    assert result.message_id == "SM789"


def test_verify_whatsapp_webhook_success(api_connector):
    """Test WhatsApp webhook verification success."""
    challenge = api_connector.verify_whatsapp_webhook(
        mode="subscribe",
        token="test_verify_token",
        challenge="challenge_string"
    )
    
    assert challenge == "challenge_string"


def test_verify_whatsapp_webhook_failure(api_connector):
    """Test WhatsApp webhook verification failure."""
    challenge = api_connector.verify_whatsapp_webhook(
        mode="subscribe",
        token="wrong_token",
        challenge="challenge_string"
    )
    
    assert challenge is None


def test_verify_twilio_webhook_success(api_connector):
    """Test Twilio webhook signature verification success."""
    url = "https://example.com/webhook"
    params = {"From": "+15551234567", "Body": "Test"}
    
    # Mock signature verification
    with patch('hmac.compare_digest', return_value=True):
        result = api_connector.verify_twilio_webhook(url, params, "signature")
        assert result is True


def test_verify_twilio_webhook_failure(api_connector):
    """Test Twilio webhook signature verification failure."""
    url = "https://example.com/webhook"
    params = {"From": "+15551234567", "Body": "Test"}
    
    # Mock signature verification
    with patch('hmac.compare_digest', return_value=False):
        result = api_connector.verify_twilio_webhook(url, params, "wrong_signature")
        assert result is False


# Rate Limiting Tests

@pytest.mark.asyncio
async def test_rate_limit_allows_requests(api_connector):
    """Test rate limiting allows requests within limit."""
    # First request should be allowed
    allowed1 = await api_connector._check_rate_limit("test_api", 5)
    assert allowed1 is True
    
    # Second request should be allowed
    allowed2 = await api_connector._check_rate_limit("test_api", 5)
    assert allowed2 is True


@pytest.mark.asyncio
async def test_rate_limit_blocks_excess_requests(api_connector):
    """Test rate limiting blocks requests exceeding limit."""
    # Use up the limit
    for _ in range(3):
        await api_connector._check_rate_limit("test_api", 3)
    
    # Next request should be blocked
    allowed = await api_connector._check_rate_limit("test_api", 3)
    assert allowed is False


@pytest.mark.asyncio
async def test_rate_limit_resets_after_window(api_connector):
    """Test rate limit resets after time window."""
    # Use up the limit
    for _ in range(2):
        await api_connector._check_rate_limit("test_api", 2)
    
    # Manually reset the window
    rate_info = api_connector.get_rate_limit_info("test_api")
    rate_info.reset_time = datetime.now(timezone.utc) - timedelta(seconds=1)
    
    # Next request should be allowed after reset
    allowed = await api_connector._check_rate_limit("test_api", 2)
    assert allowed is True


def test_get_rate_limit_info(api_connector):
    """Test getting rate limit information."""
    # Create rate limit entry
    api_connector.rate_limit_storage["test_api:60"] = RateLimitInfo(
        api_name="test_api",
        limit=100,
        remaining=50,
        reset_time=datetime.now(timezone.utc),
        window_seconds=60
    )
    
    info = api_connector.get_rate_limit_info("test_api")
    
    assert info is not None
    assert info.api_name == "test_api"
    assert info.limit == 100
    assert info.remaining == 50


# Helper Method Tests

def test_normalize_phone_number(api_connector):
    """Test phone number normalization."""
    # Test with various formats
    assert api_connector._normalize_phone_number("+1 555 123 4567") == "+15551234567"
    assert api_connector._normalize_phone_number("555-123-4567") == "+5551234567"
    assert api_connector._normalize_phone_number("(555) 123-4567") == "+5551234567"
    assert api_connector._normalize_phone_number("+15551234567") == "+15551234567"


def test_detect_media_type(api_connector):
    """Test media type detection from URL."""
    assert api_connector._detect_media_type("https://example.com/image.jpg") == "image"
    assert api_connector._detect_media_type("https://example.com/doc.pdf") == "document"
    assert api_connector._detect_media_type("https://example.com/video.mp4") == "video"
    assert api_connector._detect_media_type("https://example.com/audio.mp3") == "audio"
    assert api_connector._detect_media_type("https://example.com/file.unknown") == "document"


def test_detect_webhook_type(api_connector):
    """Test webhook type detection."""
    whatsapp_webhook = {"entry": []}
    assert api_connector._detect_webhook_type(whatsapp_webhook) == "whatsapp"
    
    twilio_webhook = {"MessageSid": "SM123"}
    assert api_connector._detect_webhook_type(twilio_webhook) == "twilio"
    
    unknown_webhook = {"unknown": "data"}
    assert api_connector._detect_webhook_type(unknown_webhook) == "unknown"


def test_categorize_whatsapp_error(api_connector):
    """Test WhatsApp error categorization."""
    assert api_connector._categorize_whatsapp_error("190", 401) == ErrorCategory.AUTH_FAILURE
    assert api_connector._categorize_whatsapp_error("4", 429) == ErrorCategory.RATE_LIMIT
    assert api_connector._categorize_whatsapp_error("100", 400) == ErrorCategory.INVALID_INPUT
    assert api_connector._categorize_whatsapp_error("131026", 400) == ErrorCategory.PERMANENT
    assert api_connector._categorize_whatsapp_error("999", 500) == ErrorCategory.TRANSIENT


def test_categorize_twilio_error(api_connector):
    """Test Twilio error categorization."""
    assert api_connector._categorize_twilio_error("20003", 401) == ErrorCategory.AUTH_FAILURE
    assert api_connector._categorize_twilio_error("20429", 429) == ErrorCategory.RATE_LIMIT
    assert api_connector._categorize_twilio_error("21211", 400) == ErrorCategory.INVALID_INPUT
    assert api_connector._categorize_twilio_error("21610", 400) == ErrorCategory.PERMANENT
    assert api_connector._categorize_twilio_error("999", 500) == ErrorCategory.TRANSIENT


# APIResponse Tests

def test_api_response_is_retryable():
    """Test APIResponse retryable check."""
    transient_response = APIResponse(
        success=False,
        error_category=ErrorCategory.TRANSIENT
    )
    assert transient_response.is_retryable is True
    
    rate_limit_response = APIResponse(
        success=False,
        error_category=ErrorCategory.RATE_LIMIT
    )
    assert rate_limit_response.is_retryable is True
    
    permanent_response = APIResponse(
        success=False,
        error_category=ErrorCategory.PERMANENT
    )
    assert permanent_response.is_retryable is False


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
