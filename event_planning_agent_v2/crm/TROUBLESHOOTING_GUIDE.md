# CRM Communication Engine - Troubleshooting Guide

This guide helps diagnose and resolve common issues with the CRM Communication Engine.

## Table of Contents

1. [Quick Diagnostics](#quick-diagnostics)
2. [Database Issues](#database-issues)
3. [Redis Cache Issues](#redis-cache-issues)
4. [Email Delivery Issues](#email-delivery-issues)
5. [SMS/WhatsApp Issues](#smswhatsapp-issues)
6. [Performance Issues](#performance-issues)
7. [Configuration Issues](#configuration-issues)
8. [Monitoring and Logging](#monitoring-and-logging)
9. [Common Error Messages](#common-error-messages)

---

## Quick Diagnostics

### Health Check

Run the health check to identify which components are failing:

```bash
curl http://localhost:8000/api/crm/health
```

Expected healthy response:
```json
{
  "status": "healthy",
  "components": {
    "orchestrator": "healthy",
    "email_agent": "healthy",
    "messaging_agent": "healthy",
    "database": "healthy",
    "redis_cache": "healthy"
  }
}
```

### Component-Specific Tests

**Test Database Connection**:
```bash
python -c "
from event_planning_agent_v2.crm.repository import CommunicationRepository
repo = CommunicationRepository()
print('Database: OK')
"
```

**Test Redis Connection**:
```bash
python -c "
from event_planning_agent_v2.crm.cache_manager import CacheManager
cache = CacheManager()
cache.set('test', 'value', ttl=60)
print('Redis: OK')
"
```

**Test Email Agent**:
```bash
python event_planning_agent_v2/crm/test_smtp.py
```

**Test Messaging Agent**:
```bash
python event_planning_agent_v2/crm/test_twilio.py
python event_planning_agent_v2/crm/test_whatsapp.py
```

### Check Logs

```bash
# Application logs
tail -f logs/crm_app.log

# Error logs only
tail -f logs/crm_app.log | grep ERROR

# Specific component logs
tail -f logs/crm_app.log | grep "CRMAgentOrchestrator"
```

---

## Database Issues

### Issue: "Connection refused" or "Could not connect to database"

**Symptoms**:
- Health check shows database as "unhealthy"
- Error: `psycopg2.OperationalError: could not connect to server`

**Diagnosis**:
```bash
# Check if PostgreSQL is running
sudo systemctl status postgresql

# Test connection manually
psql -U crm_user -d event_planning_crm -h localhost
```

**Solutions**:

1. **Start PostgreSQL**:
```bash
sudo systemctl start postgresql
sudo systemctl enable postgresql
```

2. **Check connection parameters**:
```bash
# Verify .env file
cat .env | grep DATABASE_URL

# Should be:
# DATABASE_URL=postgresql://crm_user:password@localhost:5432/event_planning_crm
```

3. **Check PostgreSQL is listening**:
```bash
sudo netstat -plnt | grep 5432
```

4. **Check pg_hba.conf**:
```bash
sudo nano /etc/postgresql/13/main/pg_hba.conf

# Ensure this line exists:
# host    all    all    127.0.0.1/32    md5
```

5. **Restart PostgreSQL**:
```bash
sudo systemctl restart postgresql
```

---

### Issue: "Authentication failed for user"

**Symptoms**:
- Error: `FATAL: password authentication failed for user "crm_user"`

**Solutions**:

1. **Reset password**:
```bash
sudo -u postgres psql

ALTER USER crm_user WITH PASSWORD 'new_secure_password';
\q
```

2. **Update .env file**:
```bash
DATABASE_URL=postgresql://crm_user:new_secure_password@localhost:5432/event_planning_crm
```

3. **Test connection**:
```bash
psql -U crm_user -d event_planning_crm -h localhost
```

---

### Issue: "Table does not exist"

**Symptoms**:
- Error: `relation "crm_communications" does not exist`

**Solutions**:

1. **Run migrations**:
```bash
cd event_planning_agent_v2/database
python run_crm_migration.py
```

2. **Verify tables exist**:
```bash
psql -U crm_user -d event_planning_crm -c "\dt"
```

Expected tables:
- crm_communications
- crm_client_preferences
- crm_communication_templates
- crm_delivery_logs

3. **If migration fails, run SQL manually**:
```bash
psql -U crm_user -d event_planning_crm -f migrations/003_crm_complete_schema.sql
```

---

### Issue: "Too many connections"

**Symptoms**:
- Error: `FATAL: sorry, too many clients already`

**Solutions**:

1. **Check current connections**:
```bash
psql -U postgres -c "SELECT count(*) FROM pg_stat_activity;"
```

2. **Increase max_connections**:
```bash
sudo nano /etc/postgresql/13/main/postgresql.conf

# Change:
max_connections = 200  # Default is 100
```

3. **Restart PostgreSQL**:
```bash
sudo systemctl restart postgresql
```

4. **Implement connection pooling** (in application):
```python
# In database config
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
```

---

## Redis Cache Issues

### Issue: "Connection refused" to Redis

**Symptoms**:
- Health check shows redis_cache as "unhealthy"
- Error: `redis.exceptions.ConnectionError: Error connecting to Redis`

**Diagnosis**:
```bash
# Check if Redis is running
sudo systemctl status redis-server

# Test connection
redis-cli ping
```

**Solutions**:

1. **Start Redis**:
```bash
sudo systemctl start redis-server
sudo systemctl enable redis-server
```

2. **Check Redis is listening**:
```bash
sudo netstat -plnt | grep 6379
```

3. **Test with password**:
```bash
redis-cli -a your_redis_password ping
```

4. **Check .env configuration**:
```bash
cat .env | grep REDIS_URL

# Should be:
# REDIS_URL=redis://:password@localhost:6379/0
```

---

### Issue: "NOAUTH Authentication required"

**Symptoms**:
- Error: `redis.exceptions.ResponseError: NOAUTH Authentication required`

**Solutions**:

1. **Add password to .env**:
```bash
REDIS_URL=redis://:your_redis_password@localhost:6379/0
REDIS_PASSWORD=your_redis_password
```

2. **Or disable password** (not recommended for production):
```bash
sudo nano /etc/redis/redis.conf

# Comment out:
# requirepass your_redis_password
```

3. **Restart Redis**:
```bash
sudo systemctl restart redis-server
```

---

### Issue: "Out of memory" in Redis

**Symptoms**:
- Error: `OOM command not allowed when used memory > 'maxmemory'`

**Solutions**:

1. **Check memory usage**:
```bash
redis-cli -a password INFO memory
```

2. **Increase maxmemory**:
```bash
sudo nano /etc/redis/redis.conf

# Change:
maxmemory 2gb  # Increase as needed
maxmemory-policy allkeys-lru
```

3. **Restart Redis**:
```bash
sudo systemctl restart redis-server
```

4. **Clear cache if needed**:
```bash
redis-cli -a password FLUSHDB
```

---

## Email Delivery Issues

### Issue: "SMTP authentication failed"

**Symptoms**:
- Emails not sending
- Error: `SMTPAuthenticationError: (535, b'5.7.8 Username and Password not accepted')`

**Solutions**:

1. **For Gmail - Use App Password**:
   - Enable 2FA on Google account
   - Generate App Password at [myaccount.google.com/apppasswords](https://myaccount.google.com/apppasswords)
   - Use App Password in .env (not regular password)

2. **Verify credentials**:
```bash
cat .env | grep SMTP

# Check for extra spaces or special characters
```

3. **Test SMTP connection**:
```python
import smtplib
import os
from dotenv import load_dotenv

load_dotenv()

try:
    server = smtplib.SMTP(os.getenv('SMTP_HOST'), int(os.getenv('SMTP_PORT')))
    server.starttls()
    server.login(os.getenv('SMTP_USERNAME'), os.getenv('SMTP_PASSWORD'))
    print("SMTP authentication successful!")
    server.quit()
except Exception as e:
    print(f"SMTP authentication failed: {e}")
```

---

### Issue: "Connection timeout" when sending email

**Symptoms**:
- Error: `socket.timeout: timed out`
- Emails stuck in "pending" status

**Solutions**:

1. **Check firewall allows outbound SMTP**:
```bash
# Test port 587 (TLS)
telnet smtp.gmail.com 587

# Test port 465 (SSL)
telnet smtp.gmail.com 465
```

2. **Try alternative port**:
```bash
# In .env, try port 465 instead of 587
SMTP_PORT=465
SMTP_USE_TLS=false
SMTP_USE_SSL=true
```

3. **Check network connectivity**:
```bash
ping smtp.gmail.com
```

4. **Disable firewall temporarily** (for testing):
```bash
sudo ufw disable
# Test email sending
sudo ufw enable
```

---

### Issue: "Emails going to spam"

**Symptoms**:
- Emails delivered but in spam folder
- Low open rates

**Solutions**:

1. **Set up SPF record**:
```
TXT record for yourdomain.com:
v=spf1 include:_spf.google.com ~all
```

2. **Set up DKIM**:
   - For Gmail: Follow [Google Workspace DKIM setup](https://support.google.com/a/answer/174124)
   - For SendGrid: Enable DKIM in domain authentication
   - For AWS SES: Enable DKIM signing

3. **Set up DMARC**:
```
TXT record for _dmarc.yourdomain.com:
v=DMARC1; p=quarantine; rua=mailto:dmarc@yourdomain.com
```

4. **Improve email content**:
   - Avoid spam trigger words ("free", "urgent", "act now")
   - Include unsubscribe link
   - Use proper HTML structure
   - Include plain text version

5. **Warm up IP address** (for dedicated IPs):
   - Start with low volume
   - Gradually increase over 2-4 weeks

---

### Issue: "Attachment too large"

**Symptoms**:
- Error: `Message size exceeds maximum allowed`

**Solutions**:

1. **Check attachment size**:
```python
import os
file_size = os.path.getsize('attachment.pdf')
print(f"Size: {file_size / 1024 / 1024:.2f} MB")
```

2. **Compress PDF**:
```bash
# Using Ghostscript
gs -sDEVICE=pdfwrite -dCompatibilityLevel=1.4 -dPDFSETTINGS=/ebook \
   -dNOPAUSE -dQUIET -dBATCH -sOutputFile=compressed.pdf input.pdf
```

3. **Use cloud storage link instead**:
   - Upload to S3/Google Drive
   - Include download link in email
   - Avoid attaching large files

4. **Increase SMTP size limit** (if using own server):
```bash
# In postfix main.cf
message_size_limit = 20971520  # 20 MB
```

---

## SMS/WhatsApp Issues

### Issue: "Invalid phone number format"

**Symptoms**:
- Error: `Invalid 'To' Phone Number`
- Messages not sending

**Solutions**:

1. **Use E.164 format**:
```
Correct: +919876543210
Wrong: 9876543210
Wrong: +91 98765 43210
Wrong: 09876543210
```

2. **Validate phone numbers**:
```python
import phonenumbers

def validate_phone(number):
    try:
        parsed = phonenumbers.parse(number, None)
        if phonenumbers.is_valid_number(parsed):
            return phonenumbers.format_number(parsed, phonenumbers.PhoneNumberFormat.E164)
        else:
            return None
    except:
        return None

# Test
print(validate_phone("+919876543210"))  # Valid
print(validate_phone("9876543210"))     # Invalid
```

---

### Issue: "WhatsApp message not delivered"

**Symptoms**:
- Message status stuck at "sent"
- No delivery receipt received

**Solutions**:

1. **Check recipient has WhatsApp**:
   - Recipient must have WhatsApp installed
   - Number must be registered on WhatsApp

2. **Verify access token**:
```bash
curl -X GET "https://graph.facebook.com/v18.0/me?access_token=YOUR_TOKEN"
```

3. **Check webhook is receiving updates**:
```bash
# View webhook logs
tail -f logs/crm_app.log | grep webhook
```

4. **Verify phone number ID**:
```bash
curl -X GET "https://graph.facebook.com/v18.0/YOUR_PHONE_NUMBER_ID" \
  -H "Authorization: Bearer YOUR_TOKEN"
```

5. **Check quality rating**:
   - Go to WhatsApp Manager
   - Check quality rating (should be "High" or "Medium")
   - If "Low", reduce message frequency

---

### Issue: "Twilio rate limit exceeded"

**Symptoms**:
- Error: `429 Too Many Requests`
- Messages queued but not sending

**Solutions**:

1. **Implement rate limiting**:
```python
import time
from functools import wraps

def rate_limit(max_per_second=1):
    min_interval = 1.0 / max_per_second
    last_called = [0.0]
    
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            elapsed = time.time() - last_called[0]
            left_to_wait = min_interval - elapsed
            if left_to_wait > 0:
                time.sleep(left_to_wait)
            ret = func(*args, **kwargs)
            last_called[0] = time.time()
            return ret
        return wrapper
    return decorator

@rate_limit(max_per_second=1)
def send_sms(to, message):
    # Send SMS
    pass
```

2. **Use message queuing**:
   - Implement Redis queue
   - Process messages with delay

3. **Request rate limit increase**:
   - Contact Twilio support
   - Provide use case and expected volume

---

### Issue: "Message blocked by carrier"

**Symptoms**:
- Error: `30007: Message filtered`
- Messages to certain numbers fail

**Solutions**:

1. **Check opt-out list**:
```python
from twilio.rest import Client

client = Client(account_sid, auth_token)
opt_outs = client.messages.list(status='undelivered')
for msg in opt_outs:
    if 'filtered' in msg.error_message.lower():
        print(f"Blocked: {msg.to}")
```

2. **Honor opt-outs**:
   - Maintain opt-out list in database
   - Check before sending

3. **Include opt-out instructions**:
   - Add "Reply STOP to unsubscribe" to messages
   - Handle STOP responses

4. **Avoid spam content**:
   - Don't use all caps
   - Avoid excessive punctuation!!!
   - Include business name

---

## Performance Issues

### Issue: "Slow email sending"

**Symptoms**:
- Emails taking > 10 seconds to send
- High latency in communication delivery

**Solutions**:

1. **Enable connection pooling**:
```python
# In email_sub_agent.py
from smtplib import SMTP
from email.mime.text import MIMEText

class EmailSubAgent:
    def __init__(self):
        self.smtp_pool = []  # Connection pool
    
    def get_smtp_connection(self):
        # Reuse existing connection
        if self.smtp_pool:
            return self.smtp_pool.pop()
        # Create new connection
        smtp = SMTP(host, port)
        smtp.starttls()
        smtp.login(username, password)
        return smtp
    
    def return_smtp_connection(self, smtp):
        self.smtp_pool.append(smtp)
```

2. **Use async email sending**:
```python
import asyncio
import aiosmtplib

async def send_email_async(to, subject, body):
    await aiosmtplib.send(
        message,
        hostname=smtp_host,
        port=smtp_port,
        username=smtp_user,
        password=smtp_pass,
        use_tls=True
    )
```

3. **Batch email sending**:
   - Group non-urgent emails
   - Send in batches of 10-50

---

### Issue: "High database query time"

**Symptoms**:
- Slow API responses
- Database CPU usage high

**Solutions**:

1. **Add missing indexes**:
```sql
-- Check slow queries
SELECT query, mean_exec_time, calls
FROM pg_stat_statements
ORDER BY mean_exec_time DESC
LIMIT 10;

-- Add indexes
CREATE INDEX idx_crm_communications_plan_client 
ON crm_communications(plan_id, client_id);

CREATE INDEX idx_crm_communications_created_at 
ON crm_communications(created_at DESC);
```

2. **Enable query caching**:
```python
from functools import lru_cache

@lru_cache(maxsize=100)
def get_client_preferences(client_id):
    # Query database
    pass
```

3. **Use Redis for frequently accessed data**:
```python
def get_client_preferences(client_id):
    # Try cache first
    cached = redis.get(f"prefs:{client_id}")
    if cached:
        return json.loads(cached)
    
    # Query database
    prefs = db.query(...)
    
    # Cache for 1 hour
    redis.setex(f"prefs:{client_id}", 3600, json.dumps(prefs))
    return prefs
```

---

### Issue: "Memory usage growing"

**Symptoms**:
- Application memory usage increasing over time
- Eventually crashes with OOM error

**Solutions**:

1. **Check for memory leaks**:
```python
import tracemalloc

tracemalloc.start()

# Run your code

snapshot = tracemalloc.take_snapshot()
top_stats = snapshot.statistics('lineno')

for stat in top_stats[:10]:
    print(stat)
```

2. **Clear template cache periodically**:
```python
# In email_template_system.py
def clear_old_cache(self):
    if len(self.template_cache) > 100:
        # Keep only 50 most recent
        self.template_cache = dict(list(self.template_cache.items())[-50:])
```

3. **Limit connection pool size**:
```python
DATABASE_POOL_SIZE = 20
DATABASE_MAX_OVERFLOW = 10
```

4. **Restart application periodically**:
```bash
# Add to crontab
0 3 * * * systemctl restart crm-app
```

---

## Configuration Issues

### Issue: "Environment variables not loaded"

**Symptoms**:
- Error: `KeyError: 'SMTP_HOST'`
- Configuration values are None

**Solutions**:

1. **Check .env file exists**:
```bash
ls -la .env
```

2. **Load .env in application**:
```python
from dotenv import load_dotenv
import os

# Load .env file
load_dotenv()

# Verify
print(os.getenv('SMTP_HOST'))
```

3. **Check .env file format**:
```bash
# Correct format (no spaces around =)
SMTP_HOST=smtp.gmail.com

# Wrong format
SMTP_HOST = smtp.gmail.com
```

4. **For systemd service, use EnvironmentFile**:
```ini
[Service]
EnvironmentFile=/opt/event-planning-crm/.env
```

---

### Issue: "Invalid configuration values"

**Symptoms**:
- Application fails to start
- Error: `ValidationError: Invalid configuration`

**Solutions**:

1. **Run configuration validator**:
```bash
python event_planning_agent_v2/crm/validate_config.py
```

2. **Check required variables**:
```bash
# List all required variables
grep "required" event_planning_agent_v2/crm/config.py
```

3. **Use .env.template as reference**:
```bash
diff .env .env.template
```

---

## Monitoring and Logging

### Enable Debug Logging

```bash
# In .env
LOG_LEVEL=DEBUG

# Restart application
systemctl restart crm-app

# View debug logs
tail -f logs/crm_app.log | grep DEBUG
```

### View Structured Logs

```bash
# View logs as JSON
tail -f logs/crm_app.log | jq '.'

# Filter by component
tail -f logs/crm_app.log | jq 'select(.component=="CRMAgentOrchestrator")'

# Filter by error level
tail -f logs/crm_app.log | jq 'select(.level=="ERROR")'
```

### Check Prometheus Metrics

```bash
# View all metrics
curl http://localhost:8000/metrics

# View specific metric
curl http://localhost:8000/metrics | grep crm_communications_total
```

---

## Common Error Messages

### "Communication failed after 3 retries"

**Cause**: All retry attempts exhausted  
**Solution**: Check external service status, verify credentials, check network connectivity

### "Template not found: budget_summary"

**Cause**: Email template file missing  
**Solution**: Ensure template exists in `crm/templates/email/budget_summary.html`

### "Client preferences not found"

**Cause**: Client has no preference record  
**Solution**: This is normal - system uses defaults. To create preferences, call preference API

### "Rate limit exceeded for WhatsApp API"

**Cause**: Too many messages sent  
**Solution**: Implement rate limiting, upgrade to paid tier, improve quality rating

### "Database connection pool exhausted"

**Cause**: Too many concurrent database connections  
**Solution**: Increase pool size, optimize queries, close connections properly

---

## Getting Help

If you can't resolve the issue:

1. **Collect diagnostic information**:
```bash
# Run diagnostic script
python event_planning_agent_v2/crm/diagnostics.py > diagnostics.txt
```

2. **Check logs**:
```bash
# Last 100 lines of logs
tail -n 100 logs/crm_app.log > recent_logs.txt
```

3. **Contact support**:
   - Email: support@planiva.com
   - Include: diagnostics.txt, recent_logs.txt, error message
   - Describe: what you were trying to do, what happened, what you expected

4. **Check documentation**:
   - API Documentation: `API_DOCUMENTATION.md`
   - Deployment Guide: `DEPLOYMENT_GUIDE.md`
   - External Services: `EXTERNAL_SERVICES_SETUP.md`
