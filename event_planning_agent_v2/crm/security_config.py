"""
Security Configuration Module

Manages API credentials, encryption keys, and security settings for the CRM Communication Engine.
Implements secure credential loading, validation, and rotation tracking.
"""

import os
import logging
import hashlib
import secrets
from typing import Optional, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from pathlib import Path
from cryptography.fernet import Fernet

try:
    from pydantic_settings import BaseSettings
    from pydantic import Field, field_validator, SecretStr
except ImportError:
    from pydantic import BaseSettings, Field, validator as field_validator, SecretStr


logger = logging.getLogger(__name__)


class CRMSecuritySettings(BaseSettings):
    """
    Security settings for CRM Communication Engine.
    
    Loads sensitive credentials from environment variables with validation.
    """
    
    # Database Encryption Key
    db_encryption_key: SecretStr = Field(
        ...,
        env="DB_ENCRYPTION_KEY",
        description="PostgreSQL pgcrypto encryption key (min 32 characters)"
    )
    
    # WhatsApp Business API Credentials
    whatsapp_access_token: SecretStr = Field(
        ...,
        env="WHATSAPP_ACCESS_TOKEN",
        description="WhatsApp Business API access token"
    )
    whatsapp_phone_number_id: str = Field(
        ...,
        env="WHATSAPP_PHONE_NUMBER_ID",
        description="WhatsApp Business phone number ID"
    )
    whatsapp_business_account_id: str = Field(
        ...,
        env="WHATSAPP_BUSINESS_ACCOUNT_ID",
        description="WhatsApp Business account ID"
    )
    whatsapp_webhook_verify_token: SecretStr = Field(
        default_factory=lambda: SecretStr(secrets.token_urlsafe(32)),
        env="WHATSAPP_WEBHOOK_VERIFY_TOKEN",
        description="WhatsApp webhook verification token"
    )
    
    # Twilio SMS API Credentials
    twilio_account_sid: str = Field(
        ...,
        env="TWILIO_ACCOUNT_SID",
        description="Twilio account SID"
    )
    twilio_auth_token: SecretStr = Field(
        ...,
        env="TWILIO_AUTH_TOKEN",
        description="Twilio authentication token"
    )
    twilio_from_number: str = Field(
        ...,
        env="TWILIO_FROM_NUMBER",
        description="Twilio phone number for sending SMS"
    )
    
    # SMTP Email Credentials
    smtp_host: str = Field(
        default="smtp.gmail.com",
        env="SMTP_HOST",
        description="SMTP server hostname"
    )
    smtp_port: int = Field(
        default=587,
        env="SMTP_PORT",
        ge=1,
        le=65535,
        description="SMTP server port"
    )
    smtp_username: str = Field(
        ...,
        env="SMTP_USERNAME",
        description="SMTP authentication username"
    )
    smtp_password: SecretStr = Field(
        ...,
        env="SMTP_PASSWORD",
        description="SMTP authentication password"
    )
    smtp_use_tls: bool = Field(
        default=True,
        env="SMTP_USE_TLS",
        description="Use TLS for SMTP connection"
    )
    smtp_from_email: str = Field(
        ...,
        env="SMTP_FROM_EMAIL",
        description="From email address for outgoing emails"
    )
    smtp_from_name: str = Field(
        default="Event Planning Team",
        env="SMTP_FROM_NAME",
        description="From name for outgoing emails"
    )
    
    # TLS/HTTPS Validation Settings
    verify_ssl: bool = Field(
        default=True,
        env="VERIFY_SSL",
        description="Verify SSL certificates for external API calls"
    )
    ssl_cert_path: Optional[str] = Field(
        default=None,
        env="SSL_CERT_PATH",
        description="Path to custom SSL certificate bundle"
    )
    
    # Credential Rotation Settings
    credential_rotation_interval_days: int = Field(
        default=90,
        env="CREDENTIAL_ROTATION_INTERVAL_DAYS",
        ge=30,
        le=365,
        description="Days between credential rotations"
    )
    credential_rotation_warning_days: int = Field(
        default=7,
        env="CREDENTIAL_ROTATION_WARNING_DAYS",
        ge=1,
        le=30,
        description="Days before rotation to send warning"
    )
    
    # Security Headers
    enable_security_headers: bool = Field(
        default=True,
        env="ENABLE_SECURITY_HEADERS",
        description="Enable security headers for API responses"
    )
    
    # Rate Limiting for External APIs
    whatsapp_rate_limit_per_day: int = Field(
        default=1000,
        env="WHATSAPP_RATE_LIMIT_PER_DAY",
        ge=1,
        description="WhatsApp API rate limit per day"
    )
    twilio_rate_limit_per_second: int = Field(
        default=1,
        env="TWILIO_RATE_LIMIT_PER_SECOND",
        ge=1,
        description="Twilio API rate limit per second"
    )
    smtp_rate_limit_per_hour: int = Field(
        default=100,
        env="SMTP_RATE_LIMIT_PER_HOUR",
        ge=1,
        description="SMTP rate limit per hour"
    )
    
    @field_validator('db_encryption_key')
    @classmethod
    def validate_encryption_key(cls, v: SecretStr) -> SecretStr:
        """Validate encryption key meets minimum security requirements"""
        key = v.get_secret_value()
        if len(key) < 32:
            raise ValueError('DB_ENCRYPTION_KEY must be at least 32 characters long')
        return v
    
    @field_validator('smtp_from_email')
    @classmethod
    def validate_email(cls, v: str) -> str:
        """Basic email validation"""
        if '@' not in v or '.' not in v.split('@')[1]:
            raise ValueError('Invalid email address format')
        return v
    
    @field_validator('twilio_from_number')
    @classmethod
    def validate_phone_number(cls, v: str) -> str:
        """Validate phone number format"""
        # Remove common formatting characters
        cleaned = v.replace('+', '').replace('-', '').replace(' ', '').replace('(', '').replace(')', '')
        if not cleaned.isdigit() or len(cleaned) < 10:
            raise ValueError('Invalid phone number format')
        return v
    
    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"
        case_sensitive = False


@dataclass
class CredentialMetadata:
    """Metadata for tracking credential usage and rotation"""
    service_name: str
    last_used_at: Optional[datetime] = None
    last_rotated_at: Optional[datetime] = None
    rotation_due_at: Optional[datetime] = None
    rotation_count: int = 0
    is_active: bool = True
    
    def is_rotation_due(self, warning_days: int = 7) -> bool:
        """Check if credential rotation is due or approaching"""
        if not self.rotation_due_at:
            return False
        return datetime.utcnow() >= (self.rotation_due_at - timedelta(days=warning_days))
    
    def is_expired(self) -> bool:
        """Check if credential has expired"""
        if not self.rotation_due_at:
            return False
        return datetime.utcnow() >= self.rotation_due_at


class SecurityManager:
    """
    Manages security operations for CRM Communication Engine.
    
    Responsibilities:
    - Load and validate credentials from environment
    - Encrypt/decrypt sensitive data
    - Track credential usage and rotation
    - Validate TLS/HTTPS connections
    """
    
    def __init__(self, settings: Optional[CRMSecuritySettings] = None):
        """
        Initialize security manager.
        
        Args:
            settings: Optional security settings. If None, loads from environment.
        """
        self.settings = settings or CRMSecuritySettings()
        self._credential_metadata: Dict[str, CredentialMetadata] = {}
        self._initialize_metadata()
        
        logger.info("SecurityManager initialized with credential validation")
    
    def _initialize_metadata(self):
        """Initialize credential metadata tracking"""
        rotation_interval = timedelta(days=self.settings.credential_rotation_interval_days)
        
        services = ['whatsapp', 'twilio', 'smtp', 'database']
        for service in services:
            self._credential_metadata[service] = CredentialMetadata(
                service_name=service,
                last_rotated_at=datetime.utcnow(),
                rotation_due_at=datetime.utcnow() + rotation_interval
            )
    
    def get_whatsapp_credentials(self) -> Dict[str, str]:
        """
        Get WhatsApp API credentials.
        
        Returns:
            Dictionary with access_token, phone_number_id, business_account_id
        """
        self._track_credential_usage('whatsapp')
        
        return {
            'access_token': self.settings.whatsapp_access_token.get_secret_value(),
            'phone_number_id': self.settings.whatsapp_phone_number_id,
            'business_account_id': self.settings.whatsapp_business_account_id,
            'webhook_verify_token': self.settings.whatsapp_webhook_verify_token.get_secret_value()
        }
    
    def get_twilio_credentials(self) -> Dict[str, str]:
        """
        Get Twilio API credentials.
        
        Returns:
            Dictionary with account_sid, auth_token, from_number
        """
        self._track_credential_usage('twilio')
        
        return {
            'account_sid': self.settings.twilio_account_sid,
            'auth_token': self.settings.twilio_auth_token.get_secret_value(),
            'from_number': self.settings.twilio_from_number
        }
    
    def get_smtp_credentials(self) -> Dict[str, Any]:
        """
        Get SMTP server credentials.
        
        Returns:
            Dictionary with host, port, username, password, use_tls, from_email, from_name
        """
        self._track_credential_usage('smtp')
        
        return {
            'host': self.settings.smtp_host,
            'port': self.settings.smtp_port,
            'username': self.settings.smtp_username,
            'password': self.settings.smtp_password.get_secret_value(),
            'use_tls': self.settings.smtp_use_tls,
            'from_email': self.settings.smtp_from_email,
            'from_name': self.settings.smtp_from_name
        }
    
    def get_encryption_key(self) -> str:
        """
        Get database encryption key.
        
        Returns:
            Encryption key string
        """
        self._track_credential_usage('database')
        return self.settings.db_encryption_key.get_secret_value()
    
    def _track_credential_usage(self, service: str):
        """Track when credentials are accessed"""
        if service in self._credential_metadata:
            self._credential_metadata[service].last_used_at = datetime.utcnow()
    
    def check_rotation_status(self) -> Dict[str, Dict[str, Any]]:
        """
        Check rotation status for all credentials.
        
        Returns:
            Dictionary with rotation status for each service
        """
        status = {}
        warning_days = self.settings.credential_rotation_warning_days
        
        for service, metadata in self._credential_metadata.items():
            status[service] = {
                'is_active': metadata.is_active,
                'last_used_at': metadata.last_used_at.isoformat() if metadata.last_used_at else None,
                'last_rotated_at': metadata.last_rotated_at.isoformat() if metadata.last_rotated_at else None,
                'rotation_due_at': metadata.rotation_due_at.isoformat() if metadata.rotation_due_at else None,
                'rotation_count': metadata.rotation_count,
                'is_rotation_due': metadata.is_rotation_due(warning_days),
                'is_expired': metadata.is_expired(),
                'days_until_rotation': (
                    (metadata.rotation_due_at - datetime.utcnow()).days
                    if metadata.rotation_due_at else None
                )
            }
        
        return status
    
    def get_tls_config(self) -> Dict[str, Any]:
        """
        Get TLS/HTTPS configuration for external API calls.
        
        Returns:
            Dictionary with verify_ssl and optional cert_path
        """
        config = {
            'verify': self.settings.verify_ssl
        }
        
        if self.settings.ssl_cert_path:
            cert_path = Path(self.settings.ssl_cert_path)
            if cert_path.exists():
                config['verify'] = str(cert_path)
            else:
                logger.warning(f"SSL cert path not found: {cert_path}, using default verification")
        
        return config
    
    def get_rate_limits(self) -> Dict[str, int]:
        """
        Get rate limits for external APIs.
        
        Returns:
            Dictionary with rate limits for each service
        """
        return {
            'whatsapp_per_day': self.settings.whatsapp_rate_limit_per_day,
            'twilio_per_second': self.settings.twilio_rate_limit_per_second,
            'smtp_per_hour': self.settings.smtp_rate_limit_per_hour
        }
    
    def hash_credential(self, credential: str) -> str:
        """
        Create SHA256 hash of credential for audit logging.
        
        Args:
            credential: Credential string to hash
            
        Returns:
            Hexadecimal hash string
        """
        return hashlib.sha256(credential.encode()).hexdigest()
    
    def validate_credentials(self) -> Dict[str, bool]:
        """
        Validate that all required credentials are present and valid.
        
        Returns:
            Dictionary with validation status for each service
        """
        validation_results = {}
        
        try:
            # Validate WhatsApp credentials
            whatsapp_creds = self.get_whatsapp_credentials()
            validation_results['whatsapp'] = all([
                whatsapp_creds['access_token'],
                whatsapp_creds['phone_number_id'],
                whatsapp_creds['business_account_id']
            ])
        except Exception as e:
            logger.error(f"WhatsApp credential validation failed: {e}")
            validation_results['whatsapp'] = False
        
        try:
            # Validate Twilio credentials
            twilio_creds = self.get_twilio_credentials()
            validation_results['twilio'] = all([
                twilio_creds['account_sid'],
                twilio_creds['auth_token'],
                twilio_creds['from_number']
            ])
        except Exception as e:
            logger.error(f"Twilio credential validation failed: {e}")
            validation_results['twilio'] = False
        
        try:
            # Validate SMTP credentials
            smtp_creds = self.get_smtp_credentials()
            validation_results['smtp'] = all([
                smtp_creds['host'],
                smtp_creds['username'],
                smtp_creds['password'],
                smtp_creds['from_email']
            ])
        except Exception as e:
            logger.error(f"SMTP credential validation failed: {e}")
            validation_results['smtp'] = False
        
        try:
            # Validate encryption key
            encryption_key = self.get_encryption_key()
            validation_results['database'] = len(encryption_key) >= 32
        except Exception as e:
            logger.error(f"Database encryption key validation failed: {e}")
            validation_results['database'] = False
        
        return validation_results


# Global security manager instance
_security_manager: Optional[SecurityManager] = None


def get_security_manager() -> SecurityManager:
    """
    Get global security manager instance (singleton pattern).
    
    Returns:
        SecurityManager instance
    """
    global _security_manager
    
    if _security_manager is None:
        _security_manager = SecurityManager()
    
    return _security_manager


def reload_security_manager() -> SecurityManager:
    """
    Force reload security manager (useful after credential rotation).
    
    Returns:
        New SecurityManager instance
    """
    global _security_manager
    _security_manager = SecurityManager()
    logger.info("Security manager reloaded with updated credentials")
    return _security_manager
