# CRM Configuration Quick Start Guide

## 5-Minute Setup

This guide will get your CRM Communication Engine configured and running in 5 minutes.

### Step 1: Generate Encryption Key (30 seconds)

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

Copy the output and add to `.env`:
```bash
DB_ENCRYPTION_KEY=<paste-your-generated-key-here>
```

### Step 2: Configure Email (2 minutes)

#### Option A: Gmail (Recommended for Development)

1. Enable 2-Factor Authentication on your Google Account
2. Generate App Password: https://myaccount.google.com/apppasswords
3. Add to `.env`:

```bash
CRM_SMTP_ENABLED=true
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your-16-char-app-password
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Event Planning Team
```

#### Option B: SendGrid (Recommended for Production)

1. Sign up at https://sendgrid.com/
2. Create API key with "Mail Send" permissions
3. Add to `.env`:

```bash
CRM_SMTP_ENABLED=true
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=SG.your-api-key-here
SMTP_USE_TLS=true
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Event Planning Team
```

### Step 3: Validate Configuration (30 seconds)

```bash
cd event_planning_agent_v2
python crm/validate_config.py
```

Expected output:
```
✓ All validations passed!
```

### Step 4: Run Database Migration (1 minute)

```bash
python database/run_crm_migration.py
```

Expected output:
```
✓ CRM Migration Completed Successfully!
```

### Step 5: Test Email Sending (1 minute)

```python
from crm.email_sub_agent import EmailSubAgent
from crm.config import SMTPConfig

# Initialize
smtp_config = SMTPConfig.from_env()
email_agent = EmailSubAgent(smtp_config)

# Send test email
result = await email_agent.send_test_email(
    to="your-email@example.com",
    subject="CRM Test Email",
    body="If you receive this, your CRM is configured correctly!"
)

print(f"Email sent: {result.is_successful}")
```

## Done! 🎉

Your CRM Communication Engine is now configured and ready to use.

## Optional: Enable SMS and WhatsApp

### SMS (Twilio)

1. Sign up at https://www.twilio.com/try-twilio
2. Get credentials from Console Dashboard
3. Buy a phone number
4. Add to `.env`:

```bash
CRM_TWILIO_ENABLED=true
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your-auth-token
TWILIO_FROM_NUMBER=+1234567890
```

### WhatsApp Business API

1. Create Facebook Business Account
2. Set up WhatsApp Business API
3. Get credentials from Meta for Developers
4. Add to `.env`:

```bash
CRM_WHATSAPP_ENABLED=true
WHATSAPP_ACCESS_TOKEN=your-access-token
WHATSAPP_PHONE_NUMBER_ID=your-phone-number-id
WHATSAPP_BUSINESS_ACCOUNT_ID=your-business-account-id
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your-verify-token
```

## Troubleshooting

### "SMTP authentication failed"

- For Gmail: Make sure you're using an App Password, not your regular password
- Verify 2FA is enabled
- Check username is your full email address

### "DB_ENCRYPTION_KEY must be at least 32 characters"

```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

### "Failed to connect to database"

- Check PostgreSQL is running: `pg_isready`
- Verify `DATABASE_URL` in `.env`
- Ensure database exists

## Next Steps

1. **Configure Templates:** Set up email and message templates
2. **Set Client Preferences:** Configure default preferences for new clients
3. **Enable Monitoring:** Set up Prometheus metrics and alerts
4. **Test Workflows:** Send test communications through the workflow

For detailed documentation, see:
- `CRM_CONFIGURATION_README.md` - Complete configuration guide
- `MONITORING_README.md` - Monitoring and observability setup
- `SECURITY_README.md` - Security best practices
