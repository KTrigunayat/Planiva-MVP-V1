"""
CRM Communication Engine for Event Planning Agent v2.

This module provides multi-channel client communication capabilities including
email, SMS, and WhatsApp messaging with intelligent routing and tracking.
"""

from .models import (
    MessageType,
    MessageChannel,
    UrgencyLevel,
    CommunicationStatus,
    CommunicationRequest,
    CommunicationStrategy,
    CommunicationResult,
    ClientPreferences,
    CommunicationTemplate,
    DeliveryLog,
)
from .strategy import CommunicationStrategyTool
from .email_template_system import EmailTemplateSystem
from .email_sub_agent import (
    EmailSubAgent,
    SMTPConfig,
    Attachment,
    AttachmentHandler,
    EmailResult,
)
from .api_connector import (
    APIConnector,
    WhatsAppConfig,
    TwilioConfig,
    APIResponse,
    WebhookResult,
    RateLimitInfo,
    ErrorCategory,
)
from .messaging_sub_agent import (
    MessagingSubAgent,
    ConciseTextGenerator,
    MessageResult,
)
from .orchestrator import (
    CRMAgentOrchestrator,
)

# Import configuration classes
from .config import (
    WhatsAppConfig as WhatsAppConfigNew,
    TwilioConfig as TwilioConfigNew,
    SMTPConfig as SMTPConfigNew,
    RetryConfig,
    BatchConfig,
    SecurityConfig,
    CRMSettings,
    load_crm_config,
    get_crm_config,
)

# Import repository conditionally to avoid import errors in tests
try:
    from .repository import CommunicationRepository
    _repository_available = True
except ImportError:
    _repository_available = False
    CommunicationRepository = None

# Import security modules
from .security_config import (
    CRMSecuritySettings,
    SecurityManager,
    get_security_manager,
    reload_security_manager,
)
from .encryption import (
    EncryptionManager,
    encrypt_api_credential,
    decrypt_api_credential,
)
from .gdpr_compliance import GDPRComplianceManager
from .canspam_compliance import CANSPAMComplianceManager

# Import monitoring modules
from .metrics import (
    MetricsCollector,
    initialize_metrics,
    crm_communications_total,
    crm_delivery_time_seconds,
    crm_open_rate,
    crm_click_rate,
    crm_api_errors_total,
)
from .logging_config import (
    configure_crm_logging,
    get_crm_logger,
    CRMLogger,
    LogLevel,
)
from .health_check import (
    CRMHealthChecker,
    initialize_health_checker,
    get_health_checker,
    HealthStatus,
    ComponentHealth,
    CRMHealthStatus,
)
from .alerting_rules import (
    AlertManager,
    get_alert_manager,
    AlertSeverity,
    AlertCondition,
    Alert,
)
from .monitoring_init import (
    initialize_crm_monitoring,
    shutdown_crm_monitoring,
)

__all__ = [
    "MessageType",
    "MessageChannel",
    "UrgencyLevel",
    "CommunicationStatus",
    "CommunicationRequest",
    "CommunicationStrategy",
    "CommunicationResult",
    "ClientPreferences",
    "CommunicationTemplate",
    "DeliveryLog",
    "CommunicationStrategyTool",
    "EmailTemplateSystem",
    "EmailSubAgent",
    "SMTPConfig",
    "Attachment",
    "AttachmentHandler",
    "EmailResult",
    "APIConnector",
    "WhatsAppConfig",
    "TwilioConfig",
    "APIResponse",
    "WebhookResult",
    "RateLimitInfo",
    "ErrorCategory",
    "MessagingSubAgent",
    "ConciseTextGenerator",
    "MessageResult",
    "CRMAgentOrchestrator",
    "RetryConfig",
    "BatchConfig",
    "SecurityConfig",
    "CRMSettings",
    "load_crm_config",
    "get_crm_config",
    # Security modules
    "CRMSecuritySettings",
    "SecurityManager",
    "get_security_manager",
    "reload_security_manager",
    "EncryptionManager",
    "encrypt_api_credential",
    "decrypt_api_credential",
    "GDPRComplianceManager",
    "CANSPAMComplianceManager",
    # Monitoring modules
    "MetricsCollector",
    "initialize_metrics",
    "crm_communications_total",
    "crm_delivery_time_seconds",
    "crm_open_rate",
    "crm_click_rate",
    "crm_api_errors_total",
    "configure_crm_logging",
    "get_crm_logger",
    "CRMLogger",
    "LogLevel",
    "CRMHealthChecker",
    "initialize_health_checker",
    "get_health_checker",
    "HealthStatus",
    "ComponentHealth",
    "CRMHealthStatus",
    "AlertManager",
    "get_alert_manager",
    "AlertSeverity",
    "AlertCondition",
    "Alert",
    "initialize_crm_monitoring",
    "shutdown_crm_monitoring",
]

if _repository_available:
    __all__.append("CommunicationRepository")
