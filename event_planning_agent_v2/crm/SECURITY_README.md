# CRM Security Implementation

## Overview

This directory contains the security implementation for the CRM Communication Engine, including encryption, credential management, GDPR compliance, and CAN-SPAM compliance.

## Components

### 1. Security Configuration (`security_config.py`)
- Centralized credential management
- Environment variable loading with validation
- Credential rotation tracking
- TLS/HTTPS configuration
- Rate limiting configuration

### 2. Encryption (`encryption.py`)
- Database-level encryption using PostgreSQL pgcrypto
- Field-level encryption for sensitive data (email, phone, name)
- API credential encryption using Fernet (AES-128)
- Secure key management

### 3. GDPR Compliance (`gdpr_compliance.py`)
- Right to erasure (right to be forgotten)
- Right to data portability (data export)
- Data access audit logging
- Data retention management
- Automated cleanup of expired data

### 4. CAN-SPAM Compliance (`canspam_compliance.py`)
- Opt-out/unsubscribe handling
- Opt-out tracking and logging
- Unsubscribe link generation
- Compliant email footer generation
- Email compliance validation
- Opt-out statistics

### 5. Database Migration (`../database/migrations/002_security_encryption.sql`)
- pgcrypto extension setup
- Encrypted column creation
- GDPR compliance tables
- Credential rotation tracking tables
- Audit log tables
- Helper functions for encryption/decryption

## Quick Start

### 1. Set Up Environment Variables

Copy the template and fill in your credentials:

```bash
cp .env.template .env
nano .env
```

Required variables:
```bash
# Database Encryption (REQUIRED - min 32 characters)
DB_ENCRYPTION_KEY=your-encryption-key-here-change-in-production-min-32-chars

# WhatsApp Business API
WHATSAPP_ACCESS_TOKEN=your-whatsapp-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-account-id

# Twilio SMS API
TWILIO_ACCOUNT_SID=your-twilio-account-sid
TWILIO_AUTH_TOKEN=your-twilio-auth-token
TWILIO_FROM_NUMBER=+1234567890

# SMTP Email
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@example.com
SMTP_PASSWORD=your-smtp-password
SMTP_FROM_EMAIL=noreply@eventplanning.example.com
```

### 2. Run Database Migration

```bash
psql -U eventuser -d eventdb -f event_planning_agent_v2/database/migrations/002_security_encryption.sql
```

### 3. Test Security Implementation

```bash
python event_planning_agent_v2/crm/test_security.py
```

## Usage Examples

### Security Manager

```python
from event_planning_agent_v2.crm import get_security_manager

# Get security manager instance
security_mgr = get_security_manager()

# Get API credentials
whatsapp_creds = security_mgr.get_whatsapp_credentials()
twilio_creds = security_mgr.get_twilio_credentials()
smtp_creds = security_mgr.get_smtp_credentials()

# Check credential rotation status
rotation_status = security_mgr.check_rotation_status()
for service, status in rotation_status.items():
    if status['is_rotation_due']:
        print(f"WARNING: {service} needs rotation!")

# Validate all credentials
validation = security_mgr.validate_credentials()
if not all(validation.values()):
    print("Some credentials are invalid!")
```

### Encryption

```python
from event_planning_agent_v2.crm import EncryptionManager
from event_planning_agent_v2.database.connection import get_sync_session

with get_sync_session() as session:
    encryption_mgr = EncryptionManager(session)
    
    # Encrypt and save client data
    encryption_mgr.save_encrypted_client_data(
        client_id="client-123",
        email="client@example.com",
        phone_number="+1234567890",
        full_name="John Doe"
    )
    
    # Retrieve and decrypt
    data = encryption_mgr.get_decrypted_client_data("client-123")
    print(data['email'])  # "client@example.com"
```

### GDPR Compliance

```python
from event_planning_agent_v2.crm import GDPRComplianceManager
from event_planning_agent_v2.database.connection import get_sync_session

with get_sync_session() as session:
    gdpr_mgr = GDPRComplianceManager(session)
    
    # Request data deletion (Right to be Forgotten)
    gdpr_mgr.request_data_deletion(
        client_id="client-123",
        deletion_reason="Client request",
        requester_info={'ip_address': '192.168.1.1'}
    )
    
    # Export client data (Right to Data Portability)
    export_data = gdpr_mgr.export_client_data("client-123")
    
    # Log data access
    gdpr_mgr.log_data_access(
        client_id="client-123",
        access_type="read",
        accessed_by="admin@example.com",
        purpose="Customer support"
    )
```

### CAN-SPAM Compliance

```python
from event_planning_agent_v2.crm import CANSPAMComplianceManager
from event_planning_agent_v2.crm.models import MessageChannel
from event_planning_agent_v2.database.connection import get_sync_session

with get_sync_session() as session:
    canspam_mgr = CANSPAMComplianceManager(session)
    
    # Process opt-out
    canspam_mgr.process_opt_out(
        client_id="client-123",
        channel=MessageChannel.EMAIL,
        opt_out_info={'ip_address': '192.168.1.1'}
    )
    
    # Check opt-out status before sending
    if canspam_mgr.check_opt_out_status("client-123", MessageChannel.EMAIL):
        print("Client has opted out, do not send email")
    
    # Generate compliant email footer
    footer = canspam_mgr.generate_email_footer(
        client_id="client-123",
        communication_id="comm-456"
    )
    email_body = f"{main_content}{footer}"
```

## Security Best Practices

1. **Never commit credentials to version control**
   ```bash
   # Ensure .env is in .gitignore
   echo ".env" >> .gitignore
   ```

2. **Restrict file permissions**
   ```bash
   chmod 600 .env
   chown eventuser:eventuser .env
   ```

3. **Rotate credentials regularly**
   - See [CREDENTIAL_ROTATION_GUIDE.md](./CREDENTIAL_ROTATION_GUIDE.md)
   - Default rotation interval: 90 days
   - Warning period: 7 days before expiration

4. **Use strong encryption keys**
   ```python
   import secrets
   encryption_key = secrets.token_urlsafe(32)  # Min 32 characters
   ```

5. **Monitor security metrics**
   - Credential rotation status
   - Data access patterns
   - Opt-out rates
   - Failed authentication attempts

## Documentation

- **[SECURITY_IMPLEMENTATION.md](./SECURITY_IMPLEMENTATION.md)** - Comprehensive security documentation
- **[CREDENTIAL_ROTATION_GUIDE.md](./CREDENTIAL_ROTATION_GUIDE.md)** - Step-by-step rotation procedures
- **[test_security.py](./test_security.py)** - Security test suite

## Compliance

This implementation supports:
- ✅ **GDPR** (General Data Protection Regulation)
- ✅ **CAN-SPAM Act** (Email marketing compliance)
- ✅ **SOC 2 Type II** (Security controls)
- ✅ **PCI DSS** (Payment data security - if applicable)

## Monitoring

### Check Credential Rotation Status

```python
from event_planning_agent_v2.crm import get_security_manager

security_mgr = get_security_manager()
status = security_mgr.check_rotation_status()

for service, info in status.items():
    print(f"{service}: {info['days_until_rotation']} days until rotation")
```

### View Audit Logs

```sql
-- Recent data access
SELECT * FROM crm_data_access_log
WHERE access_timestamp > NOW() - INTERVAL '24 hours'
ORDER BY access_timestamp DESC;

-- Credential rotation history
SELECT * FROM security_credential_rotations
ORDER BY rotated_at DESC
LIMIT 10;
```

## Troubleshooting

### Issue: Missing Environment Variables

**Error:** `Field required` validation errors

**Solution:**
1. Copy `.env.template` to `.env`
2. Fill in all required credentials
3. Ensure minimum key lengths (32+ characters for encryption key)

### Issue: Encryption/Decryption Fails

**Error:** `Failed to decrypt data`

**Solution:**
1. Verify `DB_ENCRYPTION_KEY` is correct
2. Check if key was rotated recently
3. Ensure pgcrypto extension is installed

### Issue: GDPR Deletion Not Working

**Error:** `gdpr_delete_client_data function not found`

**Solution:**
1. Run database migration: `002_security_encryption.sql`
2. Verify pgcrypto extension is enabled
3. Check database user permissions

## Support

For security-related issues:
- Email: security@eventplanning.example.com
- Documentation: See [SECURITY_IMPLEMENTATION.md](./SECURITY_IMPLEMENTATION.md)
- Incident Response: See incident response section in documentation

## Testing

Run the complete security test suite:

```bash
python event_planning_agent_v2/crm/test_security.py
```

Expected output:
```
============================================================
Test Summary
============================================================
Security Configuration: ✓ PASSED
Encryption: ✓ PASSED
GDPR Compliance: ✓ PASSED
CAN-SPAM Compliance: ✓ PASSED
Database Migration: ✓ PASSED

Total: 5/5 tests passed

🎉 All security tests passed!
```

## License

This security implementation is part of the Event Planning Agent v2 system.
All security features are designed to comply with industry standards and regulations.
