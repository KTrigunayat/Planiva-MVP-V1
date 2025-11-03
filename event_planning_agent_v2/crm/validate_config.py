"""
CRM Configuration Validation Script

This script validates the CRM configuration and provides detailed feedback
on any issues found.
"""

import sys
import os
from pathlib import Path
from typing import List, Tuple

# Add parent directory to path
sys.path.insert(0, str(Path(__file__).parent.parent))

from crm.config import (
    WhatsAppConfig,
    TwilioConfig,
    SMTPConfig,
    RetryConfig,
    BatchConfig,
    SecurityConfig,
    load_crm_config
)


def print_header(title: str):
    """Print a formatted header."""
    print("\n" + "=" * 70)
    print(f"  {title}")
    print("=" * 70)


def print_section(title: str):
    """Print a formatted section header."""
    print(f"\n{title}")
    print("-" * 70)


def print_result(passed: bool, message: str):
    """Print a validation result."""
    symbol = "✓" if passed else "✗"
    print(f"{symbol} {message}")


def validate_whatsapp() -> Tuple[bool, List[str]]:
    """Validate WhatsApp configuration."""
    config = WhatsAppConfig.from_env()
    errors = config.validate()
    
    is_enabled = os.getenv("CRM_WHATSAPP_ENABLED", "false").lower() == "true"
    
    if not is_enabled:
        return True, ["WhatsApp is disabled (CRM_WHATSAPP_ENABLED=false)"]
    
    if errors:
        return False, errors
    
    return True, ["WhatsApp configuration is valid"]


def validate_twilio() -> Tuple[bool, List[str]]:
    """Validate Twilio configuration."""
    config = TwilioConfig.from_env()
    errors = config.validate()
    
    is_enabled = os.getenv("CRM_TWILIO_ENABLED", "false").lower() == "true"
    
    if not is_enabled:
        return True, ["Twilio is disabled (CRM_TWILIO_ENABLED=false)"]
    
    if errors:
        return False, errors
    
    return True, ["Twilio configuration is valid"]


def validate_smtp() -> Tuple[bool, List[str]]:
    """Validate SMTP configuration."""
    config = SMTPConfig.from_env()
    errors = config.validate()
    
    is_enabled = os.getenv("CRM_SMTP_ENABLED", "true").lower() == "true"
    
    if not is_enabled:
        return False, ["SMTP is disabled but is required for CRM operation"]
    
    if errors:
        return False, errors
    
    return True, ["SMTP configuration is valid"]


def validate_retry() -> Tuple[bool, List[str]]:
    """Validate retry configuration."""
    config = RetryConfig.from_env()
    errors = config.validate()
    
    if errors:
        return False, errors
    
    # Test delay calculation
    try:
        delay1 = config.calculate_delay(0)
        delay2 = config.calculate_delay(1)
        delay3 = config.calculate_delay(2)
        
        return True, [
            "Retry configuration is valid",
            f"  Retry delays: {delay1}s, {delay2}s, {delay3}s"
        ]
    except Exception as e:
        return False, [f"Error calculating retry delays: {e}"]


def validate_batch() -> Tuple[bool, List[str]]:
    """Validate batch configuration."""
    config = BatchConfig.from_env()
    errors = config.validate()
    
    if errors:
        return False, errors
    
    if not config.enabled:
        return True, ["Batch processing is disabled"]
    
    return True, [
        "Batch configuration is valid",
        f"  Max batch size: {config.max_batch_size}",
        f"  Batch window: {config.batch_window_seconds}s",
        f"  Eligible urgency: {', '.join(config.eligible_urgency_levels)}"
    ]


def validate_security() -> Tuple[bool, List[str]]:
    """Validate security configuration."""
    config = SecurityConfig.from_env()
    errors = config.validate()
    
    if errors:
        return False, errors
    
    messages = ["Security configuration is valid"]
    
    # Check encryption key strength
    key_length = len(config.db_encryption_key)
    if key_length < 40:
        messages.append(f"  ⚠ Encryption key length: {key_length} (recommend 40+)")
    else:
        messages.append(f"  Encryption key length: {key_length}")
    
    # Check SSL verification
    if not config.verify_ssl:
        messages.append("  ⚠ SSL verification is disabled (not recommended for production)")
    
    return True, messages


def check_environment_file() -> Tuple[bool, List[str]]:
    """Check if .env file exists."""
    env_file = Path(".env")
    
    if not env_file.exists():
        return False, [
            ".env file not found",
            "  Run: cp .env.template .env"
        ]
    
    return True, [".env file exists"]


def check_enabled_channels() -> Tuple[bool, List[str]]:
    """Check which communication channels are enabled."""
    channels = []
    
    smtp_enabled = os.getenv("CRM_SMTP_ENABLED", "true").lower() == "true"
    twilio_enabled = os.getenv("CRM_TWILIO_ENABLED", "false").lower() == "true"
    whatsapp_enabled = os.getenv("CRM_WHATSAPP_ENABLED", "false").lower() == "true"
    
    if smtp_enabled:
        smtp = SMTPConfig.from_env()
        if smtp.is_configured():
            channels.append("Email (SMTP)")
    
    if twilio_enabled:
        twilio = TwilioConfig.from_env()
        if twilio.is_configured():
            channels.append("SMS (Twilio)")
    
    if whatsapp_enabled:
        whatsapp = WhatsAppConfig.from_env()
        if whatsapp.is_configured():
            channels.append("WhatsApp")
    
    if not channels:
        return False, ["No communication channels are properly configured"]
    
    return True, [f"Enabled channels: {', '.join(channels)}"]


def main():
    """Main validation function."""
    print_header("CRM Configuration Validation")
    
    all_passed = True
    
    # Check environment file
    print_section("Environment File")
    passed, messages = check_environment_file()
    for msg in messages:
        print_result(passed, msg)
    all_passed = all_passed and passed
    
    # Validate each component
    components = [
        ("SMTP Configuration", validate_smtp),
        ("Twilio Configuration", validate_twilio),
        ("WhatsApp Configuration", validate_whatsapp),
        ("Retry Configuration", validate_retry),
        ("Batch Configuration", validate_batch),
        ("Security Configuration", validate_security),
    ]
    
    for title, validator in components:
        print_section(title)
        passed, messages = validator()
        for msg in messages:
            print_result(passed, msg)
        all_passed = all_passed and passed
    
    # Check enabled channels
    print_section("Enabled Channels")
    passed, messages = check_enabled_channels()
    for msg in messages:
        print_result(passed, msg)
    all_passed = all_passed and passed
    
    # Try to load full configuration
    print_section("Full Configuration Load")
    try:
        config = load_crm_config()
        print_result(True, "CRM configuration loaded successfully")
        print(f"  Enabled channels: {', '.join(config.get_enabled_channels())}")
        all_passed = all_passed and True
    except ValueError as e:
        print_result(False, "Failed to load CRM configuration")
        print(f"  Error: {e}")
        all_passed = False
    except Exception as e:
        print_result(False, f"Unexpected error: {e}")
        all_passed = False
    
    # Final summary
    print_header("Validation Summary")
    if all_passed:
        print("✓ All validations passed!")
        print("\nYour CRM configuration is ready to use.")
        print("\nNext steps:")
        print("  1. Run database migration: python database/run_crm_migration.py")
        print("  2. Test communication channels")
        print("  3. Configure templates and preferences")
        return 0
    else:
        print("✗ Some validations failed!")
        print("\nPlease fix the errors above and run validation again.")
        print("\nFor help, see: crm/CRM_CONFIGURATION_README.md")
        return 1


if __name__ == "__main__":
    exit_code = main()
    sys.exit(exit_code)
