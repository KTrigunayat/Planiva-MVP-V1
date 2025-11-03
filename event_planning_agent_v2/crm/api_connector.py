"""
API Connector for WhatsApp Business API and Twilio SMS.

This module provides integration with external messaging APIs including
authentication, request signing, rate limiting, and webhook handling.
"""

import asyncio
import hashlib
import hmac
import json
import ssl
import time
from dataclasses import dataclass, field
from datetime import datetime, timezone
from enum import Enum
from typing import Optional, Dict, Any, List
from urllib.parse import urlencode

import aiohttp
from aiohttp import ClientSession, ClientTimeout, TCPConnector


class ErrorCategory(str, Enum):
    """Categories of API errors for handling and retry logic."""
    TRANSIENT = "transient"  # Retry automatically
    PERMANENT = "permanent"  # Don't retry, log and alert
    RATE_LIMIT = "rate_limit"  # Retry with longer delay
    AUTH_FAILURE = "auth_failure"  # Alert immediately
    INVALID_INPUT = "invalid_input"  # Don't retry, log validation error


@dataclass
class WhatsAppConfig:
    """Configuration for WhatsApp Business API."""
    api_url: str = "https://graph.facebook.com/v18.0"
    phone_number_id: str = ""
    access_token: str = ""
    webhook_verify_token: str = ""
    api_version: str = "v18.0"
    
    def __post_init__(self):
        """Validate WhatsApp configuration."""
        if not self.phone_number_id:
            raise ValueError("WhatsApp phone_number_id is required")
        if not self.access_token:
            raise ValueError("WhatsApp access_token is required")
        if not self.webhook_verify_token:
            raise ValueError("WhatsApp webhook_verify_token is required")


@dataclass
class TwilioConfig:
    """Configuration for Twilio SMS API."""
    account_sid: str = ""
    auth_token: str = ""
    from_number: str = ""
    webhook_url: str = ""
    api_url: str = "https://api.twilio.com/2010-04-01"
    
    def __post_init__(self):
        """Validate Twilio configuration."""
        if not self.account_sid:
            raise ValueError("Twilio account_sid is required")
        if not self.auth_token:
            raise ValueError("Twilio auth_token is required")
        if not self.from_number:
            raise ValueError("Twilio from_number is required")


@dataclass
class APIResponse:
    """Response from messaging API."""
    success: bool
    message_id: Optional[str] = None
    status: Optional[str] = None
    error_code: Optional[str] = None
    error_message: Optional[str] = None
    error_category: Optional[ErrorCategory] = None
    raw_response: Dict[str, Any] = field(default_factory=dict)
    delivery_time_ms: Optional[int] = None
    
    @property
    def is_retryable(self) -> bool:
        """Check if error is retryable."""
        return self.error_category in [
            ErrorCategory.TRANSIENT,
            ErrorCategory.RATE_LIMIT
        ]


@dataclass
class WebhookResult:
    """Result of webhook processing."""
    success: bool
    message_id: Optional[str] = None
    status: Optional[str] = None
    timestamp: Optional[datetime] = None
    error_message: Optional[str] = None
    metadata: Dict[str, Any] = field(default_factory=dict)


@dataclass
class RateLimitInfo:
    """Rate limit tracking information."""
    api_name: str
    limit: int
    remaining: int
    reset_time: datetime
    window_seconds: int = 60


class APIConnector:
    """
    Connector for WhatsApp Business API and Twilio SMS API.
    
    Handles authentication, request signing, rate limiting, and webhook processing.
    """
    
    def __init__(
        self,
        whatsapp_config: Optional[WhatsAppConfig] = None,
        twilio_config: Optional[TwilioConfig] = None,
        rate_limit_storage: Optional[Dict[str, RateLimitInfo]] = None,
        timeout_seconds: int = 30,
        verify_ssl: bool = True,
        ssl_cert_path: Optional[str] = None
    ):
        """
        Initialize API connector.
        
        Args:
            whatsapp_config: WhatsApp Business API configuration
            twilio_config: Twilio SMS API configuration
            rate_limit_storage: Optional external rate limit storage (e.g., Redis)
            timeout_seconds: Request timeout in seconds
            verify_ssl: Whether to verify SSL certificates (default: True)
            ssl_cert_path: Optional path to custom SSL certificate bundle
        """
        self.whatsapp_config = whatsapp_config
        self.twilio_config = twilio_config
        self.rate_limit_storage = rate_limit_storage or {}
        self.timeout = ClientTimeout(total=timeout_seconds)
        self.verify_ssl = verify_ssl
        self.ssl_cert_path = ssl_cert_path
        self._session: Optional[ClientSession] = None
        
        # Rate limits (per minute)
        self.whatsapp_rate_limit = 80  # Conservative limit
        self.twilio_rate_limit = 60  # 1 per second
    
    async def __aenter__(self):
        """Async context manager entry."""
        await self._ensure_session()
        return self
    
    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        await self.close()
    
    async def _ensure_session(self):
        """Ensure aiohttp session exists with TLS/SSL validation."""
        if self._session is None or self._session.closed:
            # Create SSL context for HTTPS/TLS validation
            ssl_context = None
            if self.verify_ssl:
                ssl_context = ssl.create_default_context()
                if self.ssl_cert_path:
                    ssl_context.load_verify_locations(self.ssl_cert_path)
            else:
                # Only disable SSL verification if explicitly configured
                # This should only be used in development/testing
                ssl_context = False
            
            # Create connector with SSL context
            connector = TCPConnector(ssl=ssl_context)
            self._session = ClientSession(timeout=self.timeout, connector=connector)
    
    async def close(self):
        """Close the aiohttp session."""
        if self._session and not self._session.closed:
            await self._session.close()
            self._session = None
    
    # WhatsApp Business API Methods
    
    async def send_whatsapp_message(
        self,
        phone_number: str,
        message: str,
        media_url: Optional[str] = None,
        message_id: Optional[str] = None
    ) -> APIResponse:
        """
        Send WhatsApp message via Business API.
        
        Args:
            phone_number: Recipient phone number (E.164 format)
            message: Message text
            media_url: Optional media URL for images/documents
            message_id: Optional message ID for tracking
            
        Returns:
            APIResponse with delivery status
        """
        if not self.whatsapp_config:
            return APIResponse(
                success=False,
                error_message="WhatsApp configuration not provided",
                error_category=ErrorCategory.INVALID_INPUT
            )
        
        # Check rate limit
        if not await self._check_rate_limit("whatsapp", self.whatsapp_rate_limit):
            return APIResponse(
                success=False,
                error_message="WhatsApp rate limit exceeded",
                error_category=ErrorCategory.RATE_LIMIT
            )
        
        # Normalize phone number
        phone_number = self._normalize_phone_number(phone_number)
        
        # Build request
        url = f"{self.whatsapp_config.api_url}/{self.whatsapp_config.phone_number_id}/messages"
        headers = {
            "Authorization": f"Bearer {self.whatsapp_config.access_token}",
            "Content-Type": "application/json"
        }
        
        # Build message payload
        payload: Dict[str, Any] = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": phone_number,
        }
        
        if media_url:
            # Send media message
            media_type = self._detect_media_type(media_url)
            payload["type"] = media_type
            payload[media_type] = {
                "link": media_url,
                "caption": message if message else ""
            }
        else:
            # Send text message
            payload["type"] = "text"
            payload["text"] = {"body": message}
        
        # Send request
        start_time = time.time()
        try:
            await self._ensure_session()
            async with self._session.post(url, headers=headers, json=payload) as response:
                delivery_time_ms = int((time.time() - start_time) * 1000)
                response_data = await response.json()
                
                if response.status == 200:
                    # Success
                    wa_message_id = response_data.get("messages", [{}])[0].get("id")
                    return APIResponse(
                        success=True,
                        message_id=wa_message_id,
                        status="sent",
                        raw_response=response_data,
                        delivery_time_ms=delivery_time_ms
                    )
                else:
                    # Error
                    error_data = response_data.get("error", {})
                    error_code = str(error_data.get("code", response.status))
                    error_message = error_data.get("message", "Unknown error")
                    error_category = self._categorize_whatsapp_error(error_code, response.status)
                    
                    return APIResponse(
                        success=False,
                        error_code=error_code,
                        error_message=error_message,
                        error_category=error_category,
                        raw_response=response_data,
                        delivery_time_ms=delivery_time_ms
                    )
        
        except asyncio.TimeoutError:
            return APIResponse(
                success=False,
                error_message="Request timeout",
                error_category=ErrorCategory.TRANSIENT
            )
        except aiohttp.ClientError as e:
            return APIResponse(
                success=False,
                error_message=f"Network error: {str(e)}",
                error_category=ErrorCategory.TRANSIENT
            )
        except Exception as e:
            return APIResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                error_category=ErrorCategory.TRANSIENT
            )
    
    # Twilio SMS API Methods
    
    async def send_sms_message(
        self,
        phone_number: str,
        message: str,
        message_id: Optional[str] = None
    ) -> APIResponse:
        """
        Send SMS via Twilio API.
        
        Args:
            phone_number: Recipient phone number (E.164 format)
            message: Message text (max 160 chars recommended)
            message_id: Optional message ID for tracking
            
        Returns:
            APIResponse with delivery status
        """
        if not self.twilio_config:
            return APIResponse(
                success=False,
                error_message="Twilio configuration not provided",
                error_category=ErrorCategory.INVALID_INPUT
            )
        
        # Check rate limit
        if not await self._check_rate_limit("twilio", self.twilio_rate_limit):
            return APIResponse(
                success=False,
                error_message="Twilio rate limit exceeded",
                error_category=ErrorCategory.RATE_LIMIT
            )
        
        # Normalize phone number
        phone_number = self._normalize_phone_number(phone_number)
        
        # Build request
        url = f"{self.twilio_config.api_url}/Accounts/{self.twilio_config.account_sid}/Messages.json"
        
        # Twilio uses HTTP Basic Auth
        auth = aiohttp.BasicAuth(
            self.twilio_config.account_sid,
            self.twilio_config.auth_token
        )
        
        # Build payload
        payload = {
            "From": self.twilio_config.from_number,
            "To": phone_number,
            "Body": message
        }
        
        if self.twilio_config.webhook_url:
            payload["StatusCallback"] = self.twilio_config.webhook_url
        
        # Send request
        start_time = time.time()
        try:
            await self._ensure_session()
            async with self._session.post(url, auth=auth, data=payload) as response:
                delivery_time_ms = int((time.time() - start_time) * 1000)
                response_data = await response.json()
                
                if response.status in [200, 201]:
                    # Success
                    sms_sid = response_data.get("sid")
                    sms_status = response_data.get("status")
                    
                    return APIResponse(
                        success=True,
                        message_id=sms_sid,
                        status=sms_status,
                        raw_response=response_data,
                        delivery_time_ms=delivery_time_ms
                    )
                else:
                    # Error
                    error_code = str(response_data.get("code", response.status))
                    error_message = response_data.get("message", "Unknown error")
                    error_category = self._categorize_twilio_error(error_code, response.status)
                    
                    return APIResponse(
                        success=False,
                        error_code=error_code,
                        error_message=error_message,
                        error_category=error_category,
                        raw_response=response_data,
                        delivery_time_ms=delivery_time_ms
                    )
        
        except asyncio.TimeoutError:
            return APIResponse(
                success=False,
                error_message="Request timeout",
                error_category=ErrorCategory.TRANSIENT
            )
        except aiohttp.ClientError as e:
            return APIResponse(
                success=False,
                error_message=f"Network error: {str(e)}",
                error_category=ErrorCategory.TRANSIENT
            )
        except Exception as e:
            return APIResponse(
                success=False,
                error_message=f"Unexpected error: {str(e)}",
                error_category=ErrorCategory.TRANSIENT
            )
    
    # Webhook Handling
    
    async def handle_webhook(
        self,
        webhook_data: Dict[str, Any],
        webhook_type: str = "auto"
    ) -> WebhookResult:
        """
        Process webhook from messaging APIs.
        
        Args:
            webhook_data: Webhook payload
            webhook_type: Type of webhook ("whatsapp", "twilio", or "auto")
            
        Returns:
            WebhookResult with parsed data
        """
        # Auto-detect webhook type if not specified
        if webhook_type == "auto":
            webhook_type = self._detect_webhook_type(webhook_data)
        
        if webhook_type == "whatsapp":
            return await self._handle_whatsapp_webhook(webhook_data)
        elif webhook_type == "twilio":
            return await self._handle_twilio_webhook(webhook_data)
        else:
            return WebhookResult(
                success=False,
                error_message=f"Unknown webhook type: {webhook_type}"
            )
    
    async def _handle_whatsapp_webhook(
        self,
        webhook_data: Dict[str, Any]
    ) -> WebhookResult:
        """Handle WhatsApp webhook."""
        try:
            # WhatsApp webhook structure
            entry = webhook_data.get("entry", [{}])[0]
            changes = entry.get("changes", [{}])[0]
            value = changes.get("value", {})
            
            # Check for status update
            statuses = value.get("statuses", [])
            if statuses:
                status_data = statuses[0]
                message_id = status_data.get("id")
                status = status_data.get("status")
                timestamp = status_data.get("timestamp")
                
                return WebhookResult(
                    success=True,
                    message_id=message_id,
                    status=status,
                    timestamp=datetime.fromtimestamp(int(timestamp), tz=timezone.utc) if timestamp else None,
                    metadata={"raw": webhook_data}
                )
            
            # Check for incoming message
            messages = value.get("messages", [])
            if messages:
                message_data = messages[0]
                message_id = message_data.get("id")
                from_number = message_data.get("from")
                message_type = message_data.get("type")
                timestamp = message_data.get("timestamp")
                
                # Extract message content
                content = ""
                if message_type == "text":
                    content = message_data.get("text", {}).get("body", "")
                
                return WebhookResult(
                    success=True,
                    message_id=message_id,
                    status="received",
                    timestamp=datetime.fromtimestamp(int(timestamp), tz=timezone.utc) if timestamp else None,
                    metadata={
                        "from": from_number,
                        "type": message_type,
                        "content": content,
                        "raw": webhook_data
                    }
                )
            
            return WebhookResult(
                success=False,
                error_message="No status or message data in webhook"
            )
        
        except Exception as e:
            return WebhookResult(
                success=False,
                error_message=f"Error parsing WhatsApp webhook: {str(e)}"
            )
    
    async def _handle_twilio_webhook(
        self,
        webhook_data: Dict[str, Any]
    ) -> WebhookResult:
        """Handle Twilio webhook."""
        try:
            # Twilio webhook structure
            message_sid = webhook_data.get("MessageSid") or webhook_data.get("SmsSid")
            message_status = webhook_data.get("MessageStatus") or webhook_data.get("SmsStatus")
            from_number = webhook_data.get("From")
            to_number = webhook_data.get("To")
            body = webhook_data.get("Body")
            
            return WebhookResult(
                success=True,
                message_id=message_sid,
                status=message_status,
                timestamp=datetime.now(timezone.utc),
                metadata={
                    "from": from_number,
                    "to": to_number,
                    "body": body,
                    "raw": webhook_data
                }
            )
        
        except Exception as e:
            return WebhookResult(
                success=False,
                error_message=f"Error parsing Twilio webhook: {str(e)}"
            )
    
    def verify_whatsapp_webhook(
        self,
        mode: str,
        token: str,
        challenge: str
    ) -> Optional[str]:
        """
        Verify WhatsApp webhook subscription.
        
        Args:
            mode: Verification mode
            token: Verification token
            challenge: Challenge string
            
        Returns:
            Challenge string if verification succeeds, None otherwise
        """
        if not self.whatsapp_config:
            return None
        
        if mode == "subscribe" and token == self.whatsapp_config.webhook_verify_token:
            return challenge
        
        return None
    
    def verify_twilio_webhook(
        self,
        url: str,
        params: Dict[str, str],
        signature: str
    ) -> bool:
        """
        Verify Twilio webhook signature.
        
        Args:
            url: Full webhook URL
            params: POST parameters
            signature: X-Twilio-Signature header
            
        Returns:
            True if signature is valid
        """
        if not self.twilio_config:
            return False
        
        # Build data string
        data_string = url
        for key in sorted(params.keys()):
            data_string += key + params[key]
        
        # Compute HMAC-SHA1
        computed_signature = hmac.new(
            self.twilio_config.auth_token.encode('utf-8'),
            data_string.encode('utf-8'),
            hashlib.sha1
        ).digest()
        
        # Base64 encode
        import base64
        computed_signature_b64 = base64.b64encode(computed_signature).decode('utf-8')
        
        return hmac.compare_digest(computed_signature_b64, signature)
    
    # Rate Limiting
    
    async def _check_rate_limit(
        self,
        api_name: str,
        limit: int,
        window_seconds: int = 60
    ) -> bool:
        """
        Check if API rate limit allows sending.
        
        Args:
            api_name: Name of API (whatsapp, twilio)
            limit: Maximum requests per window
            window_seconds: Time window in seconds
            
        Returns:
            True if request is allowed
        """
        now = datetime.now(timezone.utc)
        key = f"{api_name}:{window_seconds}"
        
        # Get or create rate limit info
        if key not in self.rate_limit_storage:
            self.rate_limit_storage[key] = RateLimitInfo(
                api_name=api_name,
                limit=limit,
                remaining=limit,
                reset_time=now,
                window_seconds=window_seconds
            )
        
        rate_info = self.rate_limit_storage[key]
        
        # Check if window has reset
        if now >= rate_info.reset_time:
            rate_info.remaining = limit
            rate_info.reset_time = now.replace(
                second=0,
                microsecond=0
            ).replace(minute=now.minute + 1)
        
        # Check if request is allowed
        if rate_info.remaining > 0:
            rate_info.remaining -= 1
            return True
        
        return False
    
    def get_rate_limit_info(self, api_name: str) -> Optional[RateLimitInfo]:
        """Get current rate limit information for an API."""
        for key, info in self.rate_limit_storage.items():
            if info.api_name == api_name:
                return info
        return None
    
    # Helper Methods
    
    def _normalize_phone_number(self, phone_number: str) -> str:
        """Normalize phone number to E.164 format."""
        # Remove common formatting characters
        cleaned = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
        
        # Add + if missing
        if not cleaned.startswith("+"):
            cleaned = "+" + cleaned
        
        return cleaned
    
    def _detect_media_type(self, media_url: str) -> str:
        """Detect media type from URL."""
        url_lower = media_url.lower()
        if any(ext in url_lower for ext in [".jpg", ".jpeg", ".png", ".gif"]):
            return "image"
        elif any(ext in url_lower for ext in [".pdf", ".doc", ".docx"]):
            return "document"
        elif any(ext in url_lower for ext in [".mp4", ".mov"]):
            return "video"
        elif any(ext in url_lower for ext in [".mp3", ".wav"]):
            return "audio"
        else:
            return "document"  # Default
    
    def _detect_webhook_type(self, webhook_data: Dict[str, Any]) -> str:
        """Auto-detect webhook type from payload structure."""
        # WhatsApp webhooks have "entry" field
        if "entry" in webhook_data:
            return "whatsapp"
        
        # Twilio webhooks have "MessageSid" or "SmsSid"
        if "MessageSid" in webhook_data or "SmsSid" in webhook_data:
            return "twilio"
        
        return "unknown"
    
    def _categorize_whatsapp_error(
        self,
        error_code: str,
        status_code: int
    ) -> ErrorCategory:
        """Categorize WhatsApp API error."""
        # Authentication errors
        if status_code == 401 or error_code in ["190", "102"]:
            return ErrorCategory.AUTH_FAILURE
        
        # Rate limit errors
        if status_code == 429 or error_code in ["4", "80007"]:
            return ErrorCategory.RATE_LIMIT
        
        # Permanent errors (invalid phone number, etc.) - check before invalid input
        if error_code in ["131026", "131047", "131051"]:
            return ErrorCategory.PERMANENT
        
        # Invalid input errors
        if status_code == 400 or error_code in ["100", "131031"]:
            return ErrorCategory.INVALID_INPUT
        
        # Default to transient for unknown errors
        return ErrorCategory.TRANSIENT
    
    def _categorize_twilio_error(
        self,
        error_code: str,
        status_code: int
    ) -> ErrorCategory:
        """Categorize Twilio API error."""
        # Authentication errors
        if status_code == 401 or error_code in ["20003"]:
            return ErrorCategory.AUTH_FAILURE
        
        # Rate limit errors
        if status_code == 429 or error_code in ["20429"]:
            return ErrorCategory.RATE_LIMIT
        
        # Permanent errors (invalid phone number, unsubscribed, etc.) - check first
        if error_code in ["21610", "21614", "21408"]:
            return ErrorCategory.PERMANENT
        
        # Invalid input errors
        if error_code in ["21211"]:
            return ErrorCategory.INVALID_INPUT
        
        # Default to transient for unknown errors
        return ErrorCategory.TRANSIENT
