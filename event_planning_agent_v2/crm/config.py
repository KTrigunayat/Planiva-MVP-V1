"""
CRM Communication Engine Configuration Classes

This module defines configuration classes for all CRM components including
WhatsApp, Twilio, SMTP, retry logic, and batching behavior.
"""

import os
from dataclasses import dataclass, field
from typing import List, Optional
from enum import Enum

try:
    # Pydantic v2
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator as validator, HttpUrl as AnyHttpUrl
except ImportError:
    # Pydantic v1
    from pydantic import BaseSettings, Field, validator, AnyHttpUrl


class CRMEnvironment(str, Enum):
    """CRM-specific environment types"""
    DEVELOPMENT = "development"
    STAGING = "staging"
    PRODUCTION = "production"
    TESTING = "testing"


@dataclass
class WhatsAppConfig:
    """
    WhatsApp Business API configuration.
    
    Required for sending WhatsApp messages through the Messaging Sub-Agent.
    """
    api_url: str = "https://graph.facebook.com/v18.0"
    phone_number_id: str = ""
    access_token: str = ""
    business_account_id: str = ""
    webhook_verify_token: str = ""
    rate_limit_per_day: int = 1000
    
    @classmethod
    def from_env(cls) -> "WhatsAppConfig":
        """Load WhatsApp configuration from environment variables."""
        return cls(
            api_url=os.getenv("WHATSAPP_API_URL", "https://graph.facebook.com/v18.0"),
            phone_number_id=os.getenv("WHATSAPP_PHONE_NUMBER_ID", ""),
            access_token=os.getenv("WHATSAPP_ACCESS_TOKEN", ""),
            business_account_id=os.getenv("WHATSAPP_BUSINESS_ACCOUNT_ID", ""),
            webhook_verify_token=os.getenv("WHATSAPP_WEBHOOK_VERIFY_TOKEN", ""),
            rate_limit_per_day=int(os.getenv("WHATSAPP_RATE_LIMIT_PER_DAY", "1000"))
        )
    
    def validate(self) -> List[str]:
        """
        Validate WhatsApp configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.phone_number_id:
            errors.append("WHATSAPP_PHONE_NUMBER_ID is required")
        
        if not self.access_token:
            errors.append("WHATSAPP_ACCESS_TOKEN is required")
        
        if not self.webhook_verify_token:
            errors.append("WHATSAPP_WEBHOOK_VERIFY_TOKEN is required")
        
        if self.rate_limit_per_day <= 0:
            errors.append("WHATSAPP_RATE_LIMIT_PER_DAY must be positive")
        
        return errors
    
    def is_configured(self) -> bool:
        """Check if WhatsApp is properly configured."""
        return bool(self.phone_number_id and self.access_token)


@dataclass
class TwilioConfig:
    """
    Twilio SMS API configuration.
    
    Required for sending SMS messages through the Messaging Sub-Agent.
    """
    account_sid: str = ""
    auth_token: str = ""
    from_number: str = ""
    webhook_url: str = ""
    rate_limit_per_second: int = 1
    
    @classmethod
    def from_env(cls) -> "TwilioConfig":
        """Load Twilio configuration from environment variables."""
        return cls(
            account_sid=os.getenv("TWILIO_ACCOUNT_SID", ""),
            auth_token=os.getenv("TWILIO_AUTH_TOKEN", ""),
            from_number=os.getenv("TWILIO_FROM_NUMBER", ""),
            webhook_url=os.getenv("TWILIO_WEBHOOK_URL", ""),
            rate_limit_per_second=int(os.getenv("TWILIO_RATE_LIMIT_PER_SECOND", "1"))
        )
    
    def validate(self) -> List[str]:
        """
        Validate Twilio configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.account_sid:
            errors.append("TWILIO_ACCOUNT_SID is required")
        
        if not self.auth_token:
            errors.append("TWILIO_AUTH_TOKEN is required")
        
        if not self.from_number:
            errors.append("TWILIO_FROM_NUMBER is required")
        elif not self.from_number.startswith("+"):
            errors.append("TWILIO_FROM_NUMBER must be in E.164 format (e.g., +1234567890)")
        
        if self.rate_limit_per_second <= 0:
            errors.append("TWILIO_RATE_LIMIT_PER_SECOND must be positive")
        
        return errors
    
    def is_configured(self) -> bool:
        """Check if Twilio is properly configured."""
        return bool(self.account_sid and self.auth_token and self.from_number)


@dataclass
class SMTPConfig:
    """
    SMTP email server configuration.
    
    Required for sending emails through the Email Sub-Agent.
    """
    host: str = "smtp.gmail.com"
    port: int = 587
    username: str = ""
    password: str = ""
    use_tls: bool = True
    use_ssl: bool = False
    from_email: str = ""
    from_name: str = "Event Planning Team"
    rate_limit_per_hour: int = 100
    connection_timeout: int = 30
    max_connections: int = 5
    
    @classmethod
    def from_env(cls) -> "SMTPConfig":
        """Load SMTP configuration from environment variables."""
        return cls(
            host=os.getenv("SMTP_HOST", "smtp.gmail.com"),
            port=int(os.getenv("SMTP_PORT", "587")),
            username=os.getenv("SMTP_USERNAME", ""),
            password=os.getenv("SMTP_PASSWORD", ""),
            use_tls=os.getenv("SMTP_USE_TLS", "true").lower() == "true",
            use_ssl=os.getenv("SMTP_USE_SSL", "false").lower() == "true",
            from_email=os.getenv("SMTP_FROM_EMAIL", ""),
            from_name=os.getenv("SMTP_FROM_NAME", "Event Planning Team"),
            rate_limit_per_hour=int(os.getenv("SMTP_RATE_LIMIT_PER_HOUR", "100")),
            connection_timeout=int(os.getenv("SMTP_CONNECTION_TIMEOUT", "30")),
            max_connections=int(os.getenv("SMTP_MAX_CONNECTIONS", "5"))
        )
    
    def validate(self) -> List[str]:
        """
        Validate SMTP configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.host:
            errors.append("SMTP_HOST is required")
        
        if not (1 <= self.port <= 65535):
            errors.append("SMTP_PORT must be between 1 and 65535")
        
        if not self.username:
            errors.append("SMTP_USERNAME is required")
        
        if not self.password:
            errors.append("SMTP_PASSWORD is required")
        
        if not self.from_email:
            errors.append("SMTP_FROM_EMAIL is required")
        elif "@" not in self.from_email:
            errors.append("SMTP_FROM_EMAIL must be a valid email address")
        
        if self.use_tls and self.use_ssl:
            errors.append("Cannot use both TLS and SSL simultaneously")
        
        if self.rate_limit_per_hour <= 0:
            errors.append("SMTP_RATE_LIMIT_PER_HOUR must be positive")
        
        if self.connection_timeout <= 0:
            errors.append("SMTP_CONNECTION_TIMEOUT must be positive")
        
        if self.max_connections <= 0:
            errors.append("SMTP_MAX_CONNECTIONS must be positive")
        
        return errors
    
    def is_configured(self) -> bool:
        """Check if SMTP is properly configured."""
        return bool(self.host and self.username and self.password and self.from_email)


@dataclass
class RetryConfig:
    """
    Retry configuration for failed communications.
    
    Implements exponential backoff with jitter to prevent thundering herd.
    """
    max_retries: int = 3
    initial_delay_seconds: int = 60  # 1 minute
    max_delay_seconds: int = 900  # 15 minutes
    exponential_base: int = 5
    jitter_enabled: bool = True
    jitter_max_seconds: int = 30
    
    @classmethod
    def from_env(cls) -> "RetryConfig":
        """Load retry configuration from environment variables."""
        return cls(
            max_retries=int(os.getenv("CRM_MAX_RETRIES", "3")),
            initial_delay_seconds=int(os.getenv("CRM_INITIAL_RETRY_DELAY", "60")),
            max_delay_seconds=int(os.getenv("CRM_MAX_RETRY_DELAY", "900")),
            exponential_base=int(os.getenv("CRM_RETRY_EXPONENTIAL_BASE", "5")),
            jitter_enabled=os.getenv("CRM_RETRY_JITTER_ENABLED", "true").lower() == "true",
            jitter_max_seconds=int(os.getenv("CRM_RETRY_JITTER_MAX", "30"))
        )
    
    def validate(self) -> List[str]:
        """
        Validate retry configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if self.max_retries < 0:
            errors.append("CRM_MAX_RETRIES must be non-negative")
        
        if self.initial_delay_seconds <= 0:
            errors.append("CRM_INITIAL_RETRY_DELAY must be positive")
        
        if self.max_delay_seconds <= 0:
            errors.append("CRM_MAX_RETRY_DELAY must be positive")
        
        if self.max_delay_seconds < self.initial_delay_seconds:
            errors.append("CRM_MAX_RETRY_DELAY must be >= CRM_INITIAL_RETRY_DELAY")
        
        if self.exponential_base < 1:
            errors.append("CRM_RETRY_EXPONENTIAL_BASE must be >= 1")
        
        if self.jitter_max_seconds < 0:
            errors.append("CRM_RETRY_JITTER_MAX must be non-negative")
        
        return errors
    
    def calculate_delay(self, attempt: int) -> int:
        """
        Calculate retry delay for a given attempt number.
        
        Args:
            attempt: Retry attempt number (0-indexed)
            
        Returns:
            Delay in seconds before next retry
        """
        import random
        
        # Calculate exponential backoff
        delay = min(
            self.initial_delay_seconds * (self.exponential_base ** attempt),
            self.max_delay_seconds
        )
        
        # Add jitter if enabled
        if self.jitter_enabled:
            jitter = random.randint(0, self.jitter_max_seconds)
            delay += jitter
        
        return delay


@dataclass
class BatchConfig:
    """
    Batch processing configuration for non-urgent communications.
    
    Batching reduces API costs and prevents overwhelming clients.
    """
    enabled: bool = True
    max_batch_size: int = 3
    batch_window_seconds: int = 300  # 5 minutes
    eligible_urgency_levels: List[str] = field(default_factory=lambda: ["low"])
    
    @classmethod
    def from_env(cls) -> "BatchConfig":
        """Load batch configuration from environment variables."""
        eligible_levels = os.getenv("CRM_BATCH_ELIGIBLE_URGENCY", "low")
        return cls(
            enabled=os.getenv("CRM_BATCH_ENABLED", "true").lower() == "true",
            max_batch_size=int(os.getenv("CRM_BATCH_MAX_SIZE", "3")),
            batch_window_seconds=int(os.getenv("CRM_BATCH_WINDOW_SECONDS", "300")),
            eligible_urgency_levels=[level.strip() for level in eligible_levels.split(",")]
        )
    
    def validate(self) -> List[str]:
        """
        Validate batch configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if self.max_batch_size <= 0:
            errors.append("CRM_BATCH_MAX_SIZE must be positive")
        
        if self.batch_window_seconds <= 0:
            errors.append("CRM_BATCH_WINDOW_SECONDS must be positive")
        
        valid_urgency_levels = {"critical", "high", "normal", "low"}
        for level in self.eligible_urgency_levels:
            if level not in valid_urgency_levels:
                errors.append(f"Invalid urgency level in CRM_BATCH_ELIGIBLE_URGENCY: {level}")
        
        return errors


@dataclass
class SecurityConfig:
    """
    Security configuration for CRM communications.
    
    Handles encryption, credential management, and compliance.
    """
    db_encryption_key: str = ""
    verify_ssl: bool = True
    ssl_cert_path: str = ""
    credential_rotation_interval_days: int = 90
    credential_rotation_warning_days: int = 7
    enable_security_headers: bool = True
    
    @classmethod
    def from_env(cls) -> "SecurityConfig":
        """Load security configuration from environment variables."""
        return cls(
            db_encryption_key=os.getenv("DB_ENCRYPTION_KEY", ""),
            verify_ssl=os.getenv("VERIFY_SSL", "true").lower() == "true",
            ssl_cert_path=os.getenv("SSL_CERT_PATH", ""),
            credential_rotation_interval_days=int(os.getenv("CREDENTIAL_ROTATION_INTERVAL_DAYS", "90")),
            credential_rotation_warning_days=int(os.getenv("CREDENTIAL_ROTATION_WARNING_DAYS", "7")),
            enable_security_headers=os.getenv("ENABLE_SECURITY_HEADERS", "true").lower() == "true"
        )
    
    def validate(self) -> List[str]:
        """
        Validate security configuration.
        
        Returns:
            List of validation error messages (empty if valid)
        """
        errors = []
        
        if not self.db_encryption_key:
            errors.append("DB_ENCRYPTION_KEY is required")
        elif len(self.db_encryption_key) < 32:
            errors.append("DB_ENCRYPTION_KEY must be at least 32 characters")
        
        if self.credential_rotation_interval_days <= 0:
            errors.append("CREDENTIAL_ROTATION_INTERVAL_DAYS must be positive")
        
        if self.credential_rotation_warning_days < 0:
            errors.append("CREDENTIAL_ROTATION_WARNING_DAYS must be non-negative")
        
        if self.credential_rotation_warning_days >= self.credential_rotation_interval_days:
            errors.append("CREDENTIAL_ROTATION_WARNING_DAYS must be < CREDENTIAL_ROTATION_INTERVAL_DAYS")
        
        return errors


class CRMSettings(BaseSettings):
    """
    Pydantic-based CRM settings with validation.
    
    Integrates with the main application settings system.
    """
    
    # WhatsApp Configuration
    whatsapp_enabled: bool = Field(default=False, env="CRM_WHATSAPP_ENABLED")
    whatsapp: WhatsAppConfig = Field(default_factory=WhatsAppConfig.from_env)
    
    # Twilio Configuration
    twilio_enabled: bool = Field(default=False, env="CRM_TWILIO_ENABLED")
    twilio: TwilioConfig = Field(default_factory=TwilioConfig.from_env)
    
    # SMTP Configuration
    smtp_enabled: bool = Field(default=True, env="CRM_SMTP_ENABLED")
    smtp: SMTPConfig = Field(default_factory=SMTPConfig.from_env)
    
    # Retry Configuration
    retry: RetryConfig = Field(default_factory=RetryConfig.from_env)
    
    # Batch Configuration
    batch: BatchConfig = Field(default_factory=BatchConfig.from_env)
    
    # Security Configuration
    security: SecurityConfig = Field(default_factory=SecurityConfig.from_env)
    
    # General CRM Settings
    crm_enabled: bool = Field(default=True, env="CRM_ENABLED")
    default_timezone: str = Field(default="UTC", env="CRM_DEFAULT_TIMEZONE")
    template_cache_ttl: int = Field(default=3600, env="CRM_TEMPLATE_CACHE_TTL", ge=60)
    preference_cache_ttl: int = Field(default=3600, env="CRM_PREFERENCE_CACHE_TTL", ge=60)
    
    class Config:
        env_prefix = "CRM_"
        case_sensitive = False
        validate_assignment = True
    
    def validate_all(self) -> List[str]:
        """
        Validate all CRM configuration components.
        
        Returns:
            List of all validation error messages (empty if valid)
        """
        errors = []
        
        # Validate WhatsApp if enabled
        if self.whatsapp_enabled:
            errors.extend(self.whatsapp.validate())
        
        # Validate Twilio if enabled
        if self.twilio_enabled:
            errors.extend(self.twilio.validate())
        
        # Validate SMTP if enabled
        if self.smtp_enabled:
            errors.extend(self.smtp.validate())
        
        # Always validate retry, batch, and security configs
        errors.extend(self.retry.validate())
        errors.extend(self.batch.validate())
        errors.extend(self.security.validate())
        
        return errors
    
    def get_enabled_channels(self) -> List[str]:
        """Get list of enabled communication channels."""
        channels = []
        if self.smtp_enabled and self.smtp.is_configured():
            channels.append("email")
        if self.twilio_enabled and self.twilio.is_configured():
            channels.append("sms")
        if self.whatsapp_enabled and self.whatsapp.is_configured():
            channels.append("whatsapp")
        return channels


def load_crm_config() -> CRMSettings:
    """
    Load and validate CRM configuration from environment.
    
    Returns:
        Validated CRMSettings instance
        
    Raises:
        ValueError: If configuration validation fails
    """
    settings = CRMSettings()
    
    # Validate all components
    errors = settings.validate_all()
    
    if errors:
        error_msg = "CRM configuration validation failed:\n" + "\n".join(f"  - {err}" for err in errors)
        raise ValueError(error_msg)
    
    return settings


def get_crm_config() -> CRMSettings:
    """
    Get CRM configuration (cached).
    
    Returns:
        CRMSettings instance
    """
    return load_crm_config()
