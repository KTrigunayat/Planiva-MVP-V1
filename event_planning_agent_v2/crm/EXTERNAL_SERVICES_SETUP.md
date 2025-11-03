# External Services Setup Guide

This guide provides detailed instructions for setting up and configuring external services required by the CRM Communication Engine.

## Table of Contents

1. [WhatsApp Business API](#whatsapp-business-api)
2. [Twilio SMS](#twilio-sms)
3. [SMTP Email Services](#smtp-email-services)
4. [Troubleshooting](#troubleshooting)

---

## WhatsApp Business API

### Overview

WhatsApp Business API enables automated messaging to clients through WhatsApp. This is ideal for urgent notifications and rich media content.

### Prerequisites

- Facebook Business Manager account
- Verified business
- Phone number not currently on WhatsApp
- Business verification documents

### Step-by-Step Setup

#### 1. Create Facebook Business Manager Account

1. Go to [business.facebook.com](https://business.facebook.com)
2. Click "Create Account"
3. Enter your business name and details
4. Verify your email address

#### 2. Set Up WhatsApp Business Account

1. In Business Manager, go to **Business Settings**
2. Click **Accounts** > **WhatsApp Accounts**
3. Click **Add** > **Create a WhatsApp Business Account**
4. Follow the setup wizard:
   - Enter business display name
   - Select business category
   - Provide business description
   - Upload business profile photo

#### 3. Add Phone Number

1. In WhatsApp Business Account settings, click **Phone Numbers**
2. Click **Add Phone Number**
3. Choose one of these options:
   - **New number**: Get a number from Facebook
   - **Existing number**: Migrate an existing business number
   - **Landline**: Use a landline with SMS verification

4. Complete verification:
   - Enter the phone number
   - Receive verification code via SMS or voice call
   - Enter the code to verify

**Important**: The phone number cannot be:
- Currently registered on WhatsApp (personal or business)
- A VoIP number (in most cases)
- Shared across multiple WhatsApp Business accounts

#### 4. Get API Credentials

1. In Business Manager, go to **WhatsApp** > **API Setup**
2. Note the following credentials:

```
Phone Number ID: 1234567890
WhatsApp Business Account ID: 9876543210
Temporary Access Token: EAAxxxxxxxxxxxxx (valid for 24 hours)
```

#### 5. Generate Permanent Access Token

**Option A: Using System User (Recommended for Production)**

1. In Business Settings, go to **Users** > **System Users**
2. Click **Add** and create a system user
3. Assign the system user to your WhatsApp Business Account:
   - Go to **Accounts** > **WhatsApp Accounts**
   - Select your account
   - Click **Add People** > **Add System Users**
   - Select your system user and assign **Admin** role

4. Generate access token:
   - Go back to **System Users**
   - Click **Generate New Token**
   - Select your WhatsApp app
   - Select permissions: `whatsapp_business_messaging`, `whatsapp_business_management`
   - Copy the token (it won't be shown again!)

**Option B: Using App Access Token (Development)**

1. Go to [developers.facebook.com](https://developers.facebook.com)
2. Select your app
3. Go to **WhatsApp** > **Getting Started**
4. Copy the temporary token
5. For permanent token, follow Option A

#### 6. Configure Webhook

Webhooks receive delivery receipts and incoming messages.

1. In WhatsApp API Setup, go to **Configuration**
2. Click **Edit** next to Webhook
3. Enter webhook details:

```
Callback URL: https://your-domain.com/api/crm/webhooks/whatsapp
Verify Token: your_random_verify_token_here
```

4. Generate a secure verify token:
```bash
python -c "import secrets; print(secrets.token_urlsafe(32))"
```

5. Subscribe to webhook fields:
   - ✅ messages
   - ✅ message_status
   - ✅ message_echoes (optional)

6. Click **Verify and Save**

#### 7. Configure Environment Variables

Add to your `.env` file:

```bash
# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID=1234567890
WHATSAPP_BUSINESS_ACCOUNT_ID=9876543210
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxx
WHATSAPP_WEBHOOK_VERIFY_TOKEN=your_random_verify_token_here
WHATSAPP_API_VERSION=v18.0
WHATSAPP_API_URL=https://graph.facebook.com
```

#### 8. Test WhatsApp Integration

Create a test script `test_whatsapp.py`:

```python
import requests
import os
from dotenv import load_dotenv

load_dotenv()

def test_whatsapp():
    url = f"https://graph.facebook.com/{os.getenv('WHATSAPP_API_VERSION')}/{os.getenv('WHATSAPP_PHONE_NUMBER_ID')}/messages"
    
    headers = {
        "Authorization": f"Bearer {os.getenv('WHATSAPP_ACCESS_TOKEN')}",
        "Content-Type": "application/json"
    }
    
    data = {
        "messaging_product": "whatsapp",
        "to": "919876543210",  # Replace with your test number
        "type": "text",
        "text": {
            "body": "Test message from CRM Engine"
        }
    }
    
    response = requests.post(url, headers=headers, json=data)
    print(f"Status: {response.status_code}")
    print(f"Response: {response.json()}")

if __name__ == "__main__":
    test_whatsapp()
```

Run the test:
```bash
python test_whatsapp.py
```

#### 9. Production Considerations

**Rate Limits**:
- Free tier: 1,000 messages per day
- Paid tier: Higher limits based on quality rating

**Quality Rating**:
- Maintain high quality rating to avoid restrictions
- Avoid spam and unsolicited messages
- Respond to user messages promptly
- Use message templates for proactive messaging

**Message Templates**:
For proactive messaging (outside 24-hour window), you need approved templates:

1. Go to **WhatsApp Manager** > **Message Templates**
2. Click **Create Template**
3. Fill in template details:
   - Name: `budget_ready`
   - Category: `TRANSACTIONAL`
   - Language: English
   - Content: "Your budget strategies are ready! View them here: {{1}}"
4. Submit for approval (usually approved within 24 hours)

**Costs**:
- Free tier: 1,000 conversations/month
- After free tier: ~$0.005-0.02 per conversation (varies by country)
- Conversation = 24-hour window after first message

---

## Twilio SMS

### Overview

Twilio provides reliable SMS delivery worldwide with excellent API and webhook support.

### Prerequisites

- Valid email address
- Phone number for verification
- Credit card (for paid account)

### Step-by-Step Setup

#### 1. Create Twilio Account

1. Go to [twilio.com/try-twilio](https://www.twilio.com/try-twilio)
2. Sign up with email and password
3. Verify your email address
4. Verify your phone number

#### 2. Get a Twilio Phone Number

1. In Twilio Console, go to **Phone Numbers** > **Manage** > **Buy a number**
2. Select country (e.g., United States)
3. Filter by capabilities:
   - ✅ SMS
   - ✅ MMS (optional, for images)
4. Search and select a number
5. Click **Buy** (costs ~$1/month)

**For India**:
- Indian numbers require additional verification
- Alternative: Use international number for testing
- For production: Complete DLT registration

#### 3. Get API Credentials

1. In Twilio Console Dashboard, find:

```
Account SID: ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
Auth Token: your_auth_token_here (click to reveal)
```

2. Copy these credentials securely

#### 4. Configure Webhook

1. Go to **Phone Numbers** > **Manage** > **Active Numbers**
2. Click on your phone number
3. Scroll to **Messaging Configuration**
4. Under **A MESSAGE COMES IN**:
   - Webhook: `https://your-domain.com/api/crm/webhooks/twilio`
   - HTTP Method: `POST`

5. Under **PRIMARY HANDLER FAILS** (optional):
   - Webhook: `https://your-domain.com/api/crm/webhooks/twilio/fallback`
   - HTTP Method: `POST`

6. Click **Save**

#### 5. Configure Environment Variables

Add to your `.env` file:

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token_here
TWILIO_PHONE_NUMBER=+11234567890
TWILIO_WEBHOOK_URL=https://your-domain.com/api/crm/webhooks/twilio
```

#### 6. Test Twilio Integration

Create a test script `test_twilio.py`:

```python
from twilio.rest import Client
import os
from dotenv import load_dotenv

load_dotenv()

def test_twilio():
    client = Client(
        os.getenv('TWILIO_ACCOUNT_SID'),
        os.getenv('TWILIO_AUTH_TOKEN')
    )
    
    message = client.messages.create(
        body="Test message from CRM Engine",
        from_=os.getenv('TWILIO_PHONE_NUMBER'),
        to='+919876543210'  # Replace with your test number
    )
    
    print(f"Message SID: {message.sid}")
    print(f"Status: {message.status}")

if __name__ == "__main__":
    test_twilio()
```

Run the test:
```bash
pip install twilio
python test_twilio.py
```

#### 7. Production Considerations

**Rate Limits**:
- Default: 1 message per second per phone number
- Can be increased by contacting support

**Costs** (US numbers):
- Outbound SMS: $0.0079 per message
- Inbound SMS: $0.0079 per message
- Phone number: $1.00 per month

**Message Length**:
- Single SMS: 160 characters
- Longer messages: Split into multiple segments (charged per segment)
- Unicode (emojis): 70 characters per segment

**Compliance**:
- Include opt-out instructions (e.g., "Reply STOP to unsubscribe")
- Honor opt-out requests immediately
- Don't send to numbers on Do Not Call lists
- Follow TCPA regulations (US)

**Delivery Reports**:
Twilio provides detailed delivery status:
- `queued`: Message queued for sending
- `sent`: Sent to carrier
- `delivered`: Delivered to recipient
- `failed`: Delivery failed
- `undelivered`: Could not be delivered

---

## SMTP Email Services

### Option 1: Gmail SMTP

#### Setup Steps

1. **Enable 2-Factor Authentication**:
   - Go to [myaccount.google.com/security](https://myaccount.google.com/security)
   - Enable 2-Step Verification

2. **Generate App Password**:
   - Go to [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Select "Mail" and "Other (Custom name)"
   - Enter "CRM Engine"
   - Click **Generate**
   - Copy the 16-character password

3. **Configure Environment Variables**:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=abcd efgh ijkl mnop  # App password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Planiva Event Planning
SMTP_USE_TLS=true
```

4. **Test Configuration**:
```python
import smtplib
from email.mime.text import MIMEText
import os
from dotenv import load_dotenv

load_dotenv()

def test_gmail():
    msg = MIMEText("Test email from CRM Engine")
    msg['Subject'] = 'Test Email'
    msg['From'] = os.getenv('SMTP_FROM_EMAIL')
    msg['To'] = 'recipient@example.com'
    
    with smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT'))) as server:
        server.starttls()
        server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
        server.send_message(msg)
    
    print("Email sent successfully!")

if __name__ == "__main__":
    test_gmail()
```

**Limitations**:
- 500 emails per day (free Gmail)
- 2,000 emails per day (Google Workspace)
- Not recommended for high-volume production use

---

### Option 2: SendGrid

#### Setup Steps

1. **Create SendGrid Account**:
   - Go to [sendgrid.com/pricing](https://sendgrid.com/pricing)
   - Sign up for free tier (100 emails/day)

2. **Verify Sender Identity**:
   - Go to **Settings** > **Sender Authentication**
   - Choose **Single Sender Verification** (quick) or **Domain Authentication** (recommended)
   
   **Single Sender**:
   - Click **Create New Sender**
   - Fill in your details
   - Verify email address

   **Domain Authentication** (recommended for production):
   - Click **Authenticate Your Domain**
   - Enter your domain
   - Add DNS records provided by SendGrid
   - Wait for verification (can take up to 48 hours)

3. **Create API Key**:
   - Go to **Settings** > **API Keys**
   - Click **Create API Key**
   - Name: "CRM Engine"
   - Permissions: **Full Access** or **Restricted Access** (Mail Send only)
   - Click **Create & View**
   - Copy the API key (shown only once!)

4. **Configure Environment Variables**:
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey  # Literally the word "apikey"
SMTP_PASSWORD=SG.xxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxxx
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Planiva Event Planning
SMTP_USE_TLS=true
```

5. **Test Configuration**:
```python
import sendgrid
from sendgrid.helpers.mail import Mail, Email, To, Content
import os
from dotenv import load_dotenv

load_dotenv()

def test_sendgrid():
    sg = sendgrid.SendGridAPIClient(api_key=os.getenv('SMTP_PASSWORD'))
    
    message = Mail(
        from_email=Email(os.getenv('SMTP_FROM_EMAIL'), os.getenv('SMTP_FROM_NAME')),
        to_emails=To('recipient@example.com'),
        subject='Test Email',
        html_content=Content("text/html", "<p>Test email from CRM Engine</p>")
    )
    
    response = sg.send(message)
    print(f"Status: {response.status_code}")

if __name__ == "__main__":
    test_sendgrid()
```

**Pricing**:
- Free: 100 emails/day
- Essentials: $19.95/month (50,000 emails)
- Pro: $89.95/month (1.5M emails)

**Features**:
- Email validation
- Detailed analytics
- Template management
- A/B testing
- Dedicated IP addresses (Pro+)

---

### Option 3: AWS SES

#### Setup Steps

1. **Create AWS Account**:
   - Go to [aws.amazon.com](https://aws.amazon.com)
   - Sign up or log in

2. **Navigate to SES**:
   - Go to AWS Console
   - Search for "SES" (Simple Email Service)
   - Select your region (e.g., us-east-1)

3. **Verify Email Address or Domain**:
   
   **Email Verification** (for testing):
   - Go to **Verified identities** > **Create identity**
   - Select **Email address**
   - Enter your email
   - Click **Create identity**
   - Check your email and click verification link

   **Domain Verification** (for production):
   - Go to **Verified identities** > **Create identity**
   - Select **Domain**
   - Enter your domain (e.g., yourdomain.com)
   - Enable DKIM signing
   - Add DNS records provided by AWS
   - Wait for verification

4. **Request Production Access**:
   - By default, SES is in sandbox mode (can only send to verified addresses)
   - Go to **Account dashboard** > **Request production access**
   - Fill in the form:
     - Use case: Transactional emails for event planning platform
     - Expected sending volume
     - Bounce/complaint handling process
   - Submit request (usually approved within 24 hours)

5. **Create SMTP Credentials**:
   - Go to **SMTP settings**
   - Click **Create SMTP credentials**
   - Enter IAM user name: "crm-smtp-user"
   - Click **Create**
   - Download credentials (shown only once!)

6. **Configure Environment Variables**:
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=AKIAIOSFODNN7EXAMPLE  # From SMTP credentials
SMTP_PASSWORD=wJalrXUtnFEMI/K7MDENG/bPxRfiCYEXAMPLEKEY
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Planiva Event Planning
SMTP_USE_TLS=true
```

7. **Configure SNS for Bounce/Complaint Handling**:
   - Go to **Verified identities** > Select your domain
   - Click **Notifications** tab
   - Configure SNS topics for:
     - Bounces
     - Complaints
     - Deliveries (optional)

8. **Test Configuration**:
```python
import boto3
from botocore.exceptions import ClientError
import os
from dotenv import load_dotenv

load_dotenv()

def test_ses():
    client = boto3.client(
        'ses',
        region_name='us-east-1',
        aws_access_key_id=os.getenv('SMTP_USERNAME'),
        aws_secret_access_key=os.getenv('SMTP_PASSWORD')
    )
    
    try:
        response = client.send_email(
            Source=os.getenv('SMTP_FROM_EMAIL'),
            Destination={'ToAddresses': ['recipient@example.com']},
            Message={
                'Subject': {'Data': 'Test Email'},
                'Body': {'Html': {'Data': '<p>Test email from CRM Engine</p>'}}
            }
        )
        print(f"Email sent! Message ID: {response['MessageId']}")
    except ClientError as e:
        print(f"Error: {e.response['Error']['Message']}")

if __name__ == "__main__":
    test_ses()
```

**Pricing**:
- $0.10 per 1,000 emails
- Free tier: 62,000 emails/month (if sent from EC2)
- No monthly fees

**Features**:
- High deliverability
- Detailed sending statistics
- Dedicated IP addresses available
- Email receiving capabilities
- Integration with other AWS services

---

## Troubleshooting

### WhatsApp Issues

**Problem**: "Invalid access token"
- **Solution**: Regenerate access token using system user
- Ensure token has correct permissions

**Problem**: "Phone number not registered"
- **Solution**: Complete phone number verification in Business Manager
- Check that number is not registered on personal WhatsApp

**Problem**: "Message template not approved"
- **Solution**: Review template guidelines
- Ensure template follows WhatsApp policies
- Resubmit with corrections

**Problem**: "Rate limit exceeded"
- **Solution**: Implement exponential backoff
- Upgrade to paid tier for higher limits
- Improve quality rating

### Twilio Issues

**Problem**: "Authentication failed"
- **Solution**: Verify Account SID and Auth Token
- Check for extra spaces in credentials

**Problem**: "Invalid phone number"
- **Solution**: Use E.164 format (+country code + number)
- Example: +919876543210

**Problem**: "Message blocked"
- **Solution**: Check recipient hasn't opted out
- Verify number is not on Do Not Call list
- Ensure compliance with TCPA

**Problem**: "Insufficient balance"
- **Solution**: Add funds to Twilio account
- Set up auto-recharge

### SMTP Issues

**Problem**: "Authentication failed" (Gmail)
- **Solution**: Use App Password, not regular password
- Ensure 2FA is enabled
- Check for typos in password

**Problem**: "Connection timeout"
- **Solution**: Check firewall allows outbound port 587
- Try port 465 (SSL) instead of 587 (TLS)
- Verify SMTP host is correct

**Problem**: "Sender address rejected" (SendGrid/SES)
- **Solution**: Verify sender email/domain
- Check DNS records are properly configured
- Wait for domain verification to complete

**Problem**: "Daily sending quota exceeded"
- **Solution**: Upgrade to paid tier
- Implement message queuing
- Spread sends over time

---

## Support Resources

### WhatsApp
- Documentation: [developers.facebook.com/docs/whatsapp](https://developers.facebook.com/docs/whatsapp)
- Support: [business.facebook.com/business/help](https://business.facebook.com/business/help)

### Twilio
- Documentation: [twilio.com/docs/sms](https://www.twilio.com/docs/sms)
- Support: [support.twilio.com](https://support.twilio.com)

### SendGrid
- Documentation: [docs.sendgrid.com](https://docs.sendgrid.com)
- Support: [support.sendgrid.com](https://support.sendgrid.com)

### AWS SES
- Documentation: [docs.aws.amazon.com/ses](https://docs.aws.amazon.com/ses)
- Support: [console.aws.amazon.com/support](https://console.aws.amazon.com/support)
