# CRM Communication Engine - Configuration Guide

## Overview

This guide provides comprehensive instructions for configuring the CRM Communication Engine, including all required environment variables, external service setup, and database migrations.

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [Environment Configuration](#environment-configuration)
3. [External Service Setup](#external-service-setup)
4. [Database Migration](#database-migration)
5. [Configuration Validation](#configuration-validation)
6. [Troubleshooting](#troubleshooting)

---

## Prerequisites

Before configuring the CRM Communication Engine, ensure you have:

- **PostgreSQL 13+** with `uuid-ossp` and `pgcrypto` extensions
- **Redis 6+** for caching (optional but recommended)
- **Python 3.9+** with required dependencies installed
- Access to external service accounts (WhatsApp, Twilio, SMTP)

---

## Environment Configuration

### 1. Copy Environment Template

```bash
cp .env.template .env
```

### 2. Generate Encryption Key

The database encryption key must be at least 32 characters. Generate a secure key:

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Update `.env`:
```bash
DB_ENCRYPTION_KEY=your-generated-key-here
```

### 3. Configure Communication Channels

#### Email (SMTP) - Required

Email is the primary communication channel and should always be configured.

**Gmail Configuration:**
```bash
CRM_SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Event Planning Team
```

**Note:** For Gmail, you need to generate an [App Password](https://support.google.com/accounts/answer/185833).

**Other Providers:**
- **Outlook:** `smtp.office365.com:587`
- **SendGrid:** `smtp.sendgrid.net:587`
- **AWS SES:** `email-smtp.us-east-1.amazonaws.com:587`

#### SMS (Twilio) - Optional

```bash
CRM_TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890
TWILIO_WEBHOOK_URL=https://yourdomain.com/api/crm/webhooks/twilio
```

#### WhatsApp Business API - Optional

```bash
CRM_WHATSAPP_ENABLED=true
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-account-id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-verify-token
```

### 4. Configure Retry and Batch Settings

**Retry Configuration:**
```bash
CRM_MAX_RETRIES=3
CRM_INITIAL_RETRY_DELAY=60
CRM_MAX_RETRY_DELAY=900
CRM_RETRY_EXPONENTIAL_BASE=5
CRM_RETRY_JITTER_ENABLED=true
```

**Batch Configuration:**
```bash
CRM_BATCH_ENABLED=true
CRM_BATCH_MAX_SIZE=3
CRM_BATCH_WINDOW_SECONDS=300
CRM_BATCH_ELIGIBLE_URGENCY=low
```

### 5. Security Settings

```bash
VERIFY_SSL=true
ENABLE_SECURITY_HEADERS=true
CREDENTIAL_ROTATION_INTERVAL_DAYS=90
CREDENTIAL_ROTATION_WARNING_DAYS=7
```

---

## External Service Setup

### WhatsApp Business API Setup

1. **Create Facebook Business Account**
   - Go to [Facebook Business](https://business.facebook.com/)
   - Create a new business account

2. **Set Up WhatsApp Business API**
   - Navigate to [Meta for Developers](https://developers.facebook.com/)
   - Create a new app and select "Business" type
   - Add WhatsApp product to your app

3. **Get Credentials**
   - Phone Number ID: Found in WhatsApp > API Setup
   - Access Token: Generate in App Settings > Basic
   - Business Account ID: Found in Business Settings

4. **Configure Webhook**
   - Set webhook URL: `https://yourdomain.com/api/crm/webhooks/whatsapp`
   - Subscribe to message events
   - Set verify token (same as `WHATSAPP_WEBHOOK_VERIFY_TOKEN`)

### Twilio SMS Setup

1. **Create Twilio Account**
   - Sign up at [Twilio](https://www.twilio.com/try-twilio)
   - Verify your email and phone number

2. **Get Credentials**
   - Account SID: Found in Console Dashboard
   - Auth Token: Found in Console Dashboard (click to reveal)

3. **Get Phone Number**
   - Navigate to Phone Numbers > Buy a Number
   - Purchase a number with SMS capabilities
   - Format: E.164 format (+1234567890)

4. **Configure Webhook**
   - Go to Phone Numbers > Manage > Active Numbers
   - Select your number
   - Set webhook URL for incoming messages: `https://yourdomain.com/api/crm/webhooks/twilio`

### SMTP Setup (Gmail Example)

1. **Enable 2-Factor Authentication**
   - Go to Google Account Settings
   - Security > 2-Step Verification
   - Enable 2FA

2. **Generate App Password**
   - Security > App passwords
   - Select app: Mail
   - Select device: Other (Custom name)
   - Generate and copy the 16-character password

3. **Update Configuration**
   - Use the app password as `SMTP_PASSWORD`
   - Use your Gmail address as `SMTP_USERNAME`

---

## Database Migration

### Run CRM Schema Migration

The CRM engine requires specific database tables. Run the migration:

```bash
cd event_planning_agent_v2
python database/run_crm_migration.py
```

**Expected Output:**
```
======================================================================
CRM Database Migration Runner
======================================================================
Database URL: localhost:5432/eventdb
✓ Database connection established
Running migration: 003_crm_complete_schema.sql
✓ Migration completed: 003_crm_complete_schema.sql

======================================================================
Verifying Migration
======================================================================
Verifying CRM tables...
✓ Table exists: crm_communications
✓ Table exists: crm_client_preferences
✓ Table exists: crm_communication_templates
✓ Table exists: crm_delivery_logs
Verifying CRM indexes...
✓ Index exists: idx_crm_communications_plan_id
✓ Index exists: idx_crm_communications_client_id
...
✓ View exists: crm_communication_analytics

======================================================================
✓ CRM Migration Completed Successfully!
======================================================================
```

### Manual Migration (Alternative)

If the Python script fails, run the SQL directly:

```bash
psql -U eventuser -d eventdb -f database/migrations/003_crm_complete_schema.sql
```

---

## Configuration Validation

### Validate Configuration

Use the built-in validation to check your configuration:

```python
from crm.config import load_crm_config

try:
    config = load_crm_config()
    print("✓ Configuration valid!")
    print(f"Enabled channels: {config.get_enabled_channels()}")
except ValueError as e:
    print(f"✗ Configuration errors:\n{e}")
```

### Test Individual Components

**Test SMTP:**
```python
from crm.config import SMTPConfig

smtp = SMTPConfig.from_env()
errors = smtp.validate()
if errors:
    print("SMTP errors:", errors)
else:
    print("✓ SMTP configured correctly")
```

**Test WhatsApp:**
```python
from crm.config import WhatsAppConfig

whatsapp = WhatsAppConfig.from_env()
if whatsapp.is_configured():
    print("✓ WhatsApp configured")
else:
    print("✗ WhatsApp not configured")
```

---

## Troubleshooting

### Common Issues

#### 1. Database Connection Failed

**Error:** `Failed to connect to database`

**Solution:**
- Verify `DATABASE_URL` in `.env`
- Check PostgreSQL is running: `pg_isready`
- Verify credentials and database exists

#### 2. SMTP Authentication Failed

**Error:** `SMTP authentication error`

**Solutions:**
- For Gmail: Use App Password, not regular password
- Verify 2FA is enabled
- Check username is full email address
- Verify TLS/SSL settings match provider requirements

#### 3. Encryption Key Too Short

**Error:** `DB_ENCRYPTION_KEY must be at least 32 characters`

**Solution:**
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

#### 4. Migration Already Applied

**Error:** `relation "crm_communications" already exists`

**Solution:**
This is normal if migration was previously run. The migration uses `CREATE TABLE IF NOT EXISTS` so it's safe to re-run.

#### 5. WhatsApp Rate Limit Exceeded

**Error:** `Rate limit exceeded`

**Solution:**
- Free tier: 1000 messages/day
- Upgrade to paid tier for higher limits
- Adjust `WHATSAPP_RATE_LIMIT_PER_DAY` to match your tier

### Validation Checklist

- [ ] Database connection successful
- [ ] CRM tables created (run migration)
- [ ] Encryption key generated (32+ characters)
- [ ] At least one communication channel configured
- [ ] SMTP credentials valid (test email send)
- [ ] Redis connection working (if using cache)
- [ ] Webhook URLs accessible (for SMS/WhatsApp)
- [ ] SSL certificates valid (if using custom certs)

### Getting Help

If you encounter issues not covered here:

1. Check application logs: `logs/event_planning.log`
2. Enable debug logging: `LOG_LEVEL=DEBUG`
3. Review CRM-specific logs in the monitoring dashboard
4. Consult the main documentation: `Event_Planning_Agent_v2_Complete_Documentation.md`

---

## Configuration Examples

### Development Environment

```bash
# Minimal configuration for development
CRM_ENABLED=true
CRM_SMTP_ENABLED=true
CRM_TWILIO_ENABLED=false
CRM_WHATSAPP_ENABLED=false

# Use local SMTP server or Gmail
SMTP_HOST=localhost
SMTP_PORT=1025
SMTP_USERNAME=dev@localhost
SMTP_PASSWORD=dev
SMTP_USE_TLS=false
SMTP_FROM_EMAIL=dev@localhost

# Relaxed security for development
DB_ENCRYPTION_KEY=dev-key-minimum-32-characters-long
VERIFY_SSL=false
```

### Production Environment

```bash
# Full configuration for production
CRM_ENABLED=true
CRM_SMTP_ENABLED=true
CRM_TWILIO_ENABLED=true
CRM_WHATSAPP_ENABLED=true

# Production SMTP (SendGrid example)
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxx
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_RATE_LIMIT_PER_HOUR=1000

# Production security
DB_ENCRYPTION_KEY=<strong-generated-key>
VERIFY_SSL=true
ENABLE_SECURITY_HEADERS=true
CREDENTIAL_ROTATION_INTERVAL_DAYS=90
```

---

## Next Steps

After configuration:

1. **Test Communication Channels:** Send test messages through each channel
2. **Configure Templates:** Set up email and message templates
3. **Set Up Monitoring:** Configure Prometheus metrics and alerts
4. **Review Analytics:** Check the CRM dashboard for communication metrics
5. **Configure Client Preferences:** Set up default preferences for new clients

For implementation details, see:
- `CRM_IMPLEMENTATION_GUIDE.md`
- `MONITORING_README.md`
- `SECURITY_README.md`
