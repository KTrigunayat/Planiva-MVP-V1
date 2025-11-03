# Credential Rotation Guide

## Overview

This guide provides procedures for rotating API credentials and encryption keys for the CRM Communication Engine. Regular credential rotation is a critical security practice that reduces the risk of unauthorized access.

## Rotation Schedule

| Credential Type | Recommended Interval | Warning Period |
|----------------|---------------------|----------------|
| Database Encryption Key | 90 days | 7 days before |
| WhatsApp Access Token | 90 days | 7 days before |
| Twilio Auth Token | 90 days | 7 days before |
| SMTP Password | 90 days | 7 days before |

## Prerequisites

Before rotating credentials:

1. **Backup Current Configuration**
   ```bash
   cp .env .env.backup.$(date +%Y%m%d)
   ```

2. **Verify System Health**
   ```bash
   python -m event_planning_agent_v2.crm.security_config
   ```

3. **Schedule Maintenance Window**
   - Notify users of potential service interruption
   - Choose low-traffic period (e.g., 2-4 AM local time)
   - Allocate 30-60 minutes for rotation

## Rotation Procedures

### 1. Database Encryption Key Rotation

**CRITICAL**: This is the most sensitive rotation. Existing encrypted data must be re-encrypted.

#### Step 1: Generate New Key
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### Step 2: Prepare Migration Script
```sql
-- Save as: rotate_encryption_key.sql

-- Store old key temporarily (will be deleted after migration)
CREATE TEMP TABLE temp_encryption_keys (
    old_key TEXT,
    new_key TEXT
);

INSERT INTO temp_encryption_keys VALUES (
    'OLD_KEY_HERE',
    'NEW_KEY_HERE'
);

-- Re-encrypt all sensitive data
UPDATE crm_client_preferences
SET 
    email_encrypted = encrypt_sensitive_data(
        decrypt_sensitive_data(email_encrypted, (SELECT old_key FROM temp_encryption_keys)),
        (SELECT new_key FROM temp_encryption_keys)
    ),
    phone_number_encrypted = encrypt_sensitive_data(
        decrypt_sensitive_data(phone_number_encrypted, (SELECT old_key FROM temp_encryption_keys)),
        (SELECT new_key FROM temp_encryption_keys)
    ),
    full_name_encrypted = encrypt_sensitive_data(
        decrypt_sensitive_data(full_name_encrypted, (SELECT old_key FROM temp_encryption_keys)),
        (SELECT new_key FROM temp_encryption_keys)
    )
WHERE email_encrypted IS NOT NULL 
   OR phone_number_encrypted IS NOT NULL 
   OR full_name_encrypted IS NOT NULL;

-- Clean up
DROP TABLE temp_encryption_keys;

-- Log rotation
INSERT INTO security_credential_rotations (
    credential_type,
    rotated_by,
    rotation_reason,
    next_rotation_due
) VALUES (
    'db_encryption_key',
    current_user,
    'Scheduled 90-day rotation',
    NOW() + INTERVAL '90 days'
);
```

#### Step 3: Execute Rotation
```bash
# 1. Stop application services
systemctl stop event-planning-api

# 2. Update .env file with new key
sed -i 's/DB_ENCRYPTION_KEY=.*/DB_ENCRYPTION_KEY=NEW_KEY_HERE/' .env

# 3. Run migration script
psql -U eventuser -d eventdb -f rotate_encryption_key.sql

# 4. Verify re-encryption
psql -U eventuser -d eventdb -c "SELECT COUNT(*) FROM crm_client_preferences WHERE email_encrypted IS NOT NULL;"

# 5. Restart application services
systemctl start event-planning-api

# 6. Verify system health
curl http://localhost:8000/health
```

#### Step 4: Verify and Clean Up
```bash
# Test decryption with new key
python -c "
from event_planning_agent_v2.crm.security_config import get_security_manager
sm = get_security_manager()
print('Encryption key loaded successfully:', len(sm.get_encryption_key()) >= 32)
"

# Remove backup after 24 hours of successful operation
# rm .env.backup.YYYYMMDD
```

### 2. WhatsApp Access Token Rotation

#### Step 1: Generate New Token
1. Log in to [Meta Business Suite](https://business.facebook.com/)
2. Navigate to WhatsApp Business API settings
3. Generate new access token
4. Copy token immediately (shown only once)

#### Step 2: Update Configuration
```bash
# Update .env file
nano .env
# Update: WHATSAPP_ACCESS_TOKEN=new_token_here

# Or use sed
sed -i 's/WHATSAPP_ACCESS_TOKEN=.*/WHATSAPP_ACCESS_TOKEN=new_token_here/' .env
```

#### Step 3: Reload Application
```bash
# Graceful reload (no downtime)
systemctl reload event-planning-api

# Or restart if reload not supported
systemctl restart event-planning-api
```

#### Step 4: Verify
```bash
# Test WhatsApp API connectivity
python -c "
from event_planning_agent_v2.crm.api_connector import APIConnector
from event_planning_agent_v2.crm.security_config import get_security_manager

sm = get_security_manager()
connector = APIConnector(sm)
# Test connection (implement test method)
print('WhatsApp API connection successful')
"
```

#### Step 5: Revoke Old Token
1. Return to Meta Business Suite
2. Revoke previous access token
3. Confirm revocation

### 3. Twilio Auth Token Rotation

#### Step 1: Generate New Token
1. Log in to [Twilio Console](https://console.twilio.com/)
2. Navigate to Account > API Keys & Tokens
3. Create new Auth Token
4. Copy token (shown only once)

#### Step 2: Update Configuration
```bash
# Update .env file
sed -i 's/TWILIO_AUTH_TOKEN=.*/TWILIO_AUTH_TOKEN=new_token_here/' .env
```

#### Step 3: Test Before Full Deployment
```bash
# Test with new token
python -c "
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()
client = Client(
    os.getenv('TWILIO_ACCOUNT_SID'),
    os.getenv('TWILIO_AUTH_TOKEN')
)
# Test API call
account = client.api.accounts(os.getenv('TWILIO_ACCOUNT_SID')).fetch()
print(f'Twilio connection successful: {account.friendly_name}')
"
```

#### Step 4: Deploy and Verify
```bash
# Reload application
systemctl reload event-planning-api

# Send test SMS
python -c "
from event_planning_agent_v2.crm.messaging_sub_agent import MessagingSubAgent
# Send test message to admin number
"
```

### 4. SMTP Password Rotation

#### Step 1: Generate New Password
- For Gmail: Generate new App Password in Google Account settings
- For other providers: Follow provider-specific password reset procedure

#### Step 2: Update Configuration
```bash
# Update .env file
sed -i 's/SMTP_PASSWORD=.*/SMTP_PASSWORD=new_password_here/' .env
```

#### Step 3: Test SMTP Connection
```bash
python -c "
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()
server = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT')))
server.starttls()
server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
server.quit()
print('SMTP connection successful')
"
```

#### Step 4: Deploy
```bash
systemctl reload event-planning-api
```

## Automated Rotation Monitoring

### Check Rotation Status

```python
from event_planning_agent_v2.crm.security_config import get_security_manager

sm = get_security_manager()
status = sm.check_rotation_status()

for service, info in status.items():
    print(f"\n{service.upper()}:")
    print(f"  Last rotated: {info['last_rotated_at']}")
    print(f"  Rotation due: {info['rotation_due_at']}")
    print(f"  Days until rotation: {info['days_until_rotation']}")
    print(f"  Is rotation due: {info['is_rotation_due']}")
    print(f"  Is expired: {info['is_expired']}")
```

### Set Up Rotation Alerts

Add to cron for daily checks:

```bash
# /etc/cron.daily/check-credential-rotation
#!/bin/bash

python3 << 'EOF'
from event_planning_agent_v2.crm.security_config import get_security_manager
import smtplib
from email.mime.text import MIMEText

sm = get_security_manager()
status = sm.check_rotation_status()

alerts = []
for service, info in status.items():
    if info['is_expired']:
        alerts.append(f"CRITICAL: {service} credentials have EXPIRED!")
    elif info['is_rotation_due']:
        alerts.append(f"WARNING: {service} credentials rotation due in {info['days_until_rotation']} days")

if alerts:
    # Send email alert
    msg = MIMEText('\n'.join(alerts))
    msg['Subject'] = 'Credential Rotation Alert'
    msg['From'] = 'alerts@eventplanning.example.com'
    msg['To'] = 'admin@eventplanning.example.com'
    
    # Send email (configure SMTP)
    # ...
    
    print('\n'.join(alerts))
EOF
```

## Emergency Rotation Procedure

If credentials are compromised:

### Immediate Actions (Within 1 Hour)

1. **Revoke Compromised Credentials**
   ```bash
   # Immediately revoke at provider
   # - WhatsApp: Meta Business Suite
   # - Twilio: Twilio Console
   # - SMTP: Email provider settings
   ```

2. **Generate New Credentials**
   ```bash
   # Follow standard rotation procedures above
   # But skip maintenance window - do immediately
   ```

3. **Update and Deploy**
   ```bash
   # Update .env
   # Restart services immediately
   systemctl restart event-planning-api
   ```

4. **Verify No Unauthorized Access**
   ```sql
   -- Check for suspicious activity
   SELECT * FROM crm_data_access_log
   WHERE access_timestamp > NOW() - INTERVAL '24 hours'
   ORDER BY access_timestamp DESC;
   
   SELECT * FROM crm_communications
   WHERE created_at > NOW() - INTERVAL '24 hours'
   AND status = 'sent'
   ORDER BY created_at DESC;
   ```

5. **Notify Stakeholders**
   - Security team
   - System administrators
   - Compliance officer

### Post-Incident Actions (Within 24 Hours)

1. **Audit Logs**
   ```sql
   -- Generate comprehensive audit report
   SELECT 
       client_id,
       access_type,
       accessed_by,
       access_timestamp,
       ip_address,
       purpose
   FROM crm_data_access_log
   WHERE access_timestamp BETWEEN 'INCIDENT_START' AND 'INCIDENT_END'
   ORDER BY access_timestamp;
   ```

2. **Review Security Measures**
   - Update firewall rules
   - Review access controls
   - Strengthen monitoring

3. **Document Incident**
   - Create incident report
   - Document timeline
   - Identify root cause
   - Implement preventive measures

## Best Practices

1. **Never Commit Credentials to Version Control**
   ```bash
   # Verify .env is in .gitignore
   grep -q "^\.env$" .gitignore || echo ".env" >> .gitignore
   ```

2. **Use Strong, Unique Credentials**
   ```bash
   # Generate strong passwords
   python -c "import secrets; print(secrets.token_urlsafe(32))"
   ```

3. **Limit Credential Access**
   - Use principle of least privilege
   - Restrict .env file permissions
   ```bash
   chmod 600 .env
   chown eventuser:eventuser .env
   ```

4. **Monitor Credential Usage**
   - Enable API usage alerts
   - Review access logs regularly
   - Set up anomaly detection

5. **Document All Rotations**
   ```sql
   -- All rotations are logged automatically
   SELECT * FROM security_credential_rotations
   ORDER BY rotated_at DESC
   LIMIT 10;
   ```

6. **Test Rotation Procedures**
   - Practice rotations in staging environment
   - Document any issues encountered
   - Update procedures based on lessons learned

## Troubleshooting

### Issue: Application Won't Start After Rotation

**Solution:**
```bash
# Check logs
journalctl -u event-planning-api -n 100

# Verify .env syntax
python -c "from dotenv import load_dotenv; load_dotenv(); print('OK')"

# Restore from backup if needed
cp .env.backup.YYYYMMDD .env
systemctl restart event-planning-api
```

### Issue: Decryption Fails After Key Rotation

**Solution:**
```bash
# Check if re-encryption completed
psql -U eventuser -d eventdb -c "
SELECT COUNT(*) as total,
       COUNT(CASE WHEN email_encrypted IS NOT NULL THEN 1 END) as encrypted
FROM crm_client_preferences;
"

# If mismatch, re-run migration with old key
# Then update to new key
```

### Issue: API Calls Failing After Token Rotation

**Solution:**
```bash
# Verify new token is valid
# Test API connection manually
# Check for typos in .env file
# Ensure application reloaded configuration
```

## Support

For assistance with credential rotation:
- Email: security@eventplanning.example.com
- Slack: #security-ops
- On-call: +1-555-SECURITY

## Compliance

This rotation procedure complies with:
- SOC 2 Type II requirements
- PCI DSS credential management standards
- GDPR data protection requirements
- Industry best practices for credential lifecycle management
