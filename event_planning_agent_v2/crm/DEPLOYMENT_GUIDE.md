# CRM Communication Engine - Deployment Guide

## Table of Contents

1. [Prerequisites](#prerequisites)
2. [System Requirements](#system-requirements)
3. [Environment Setup](#environment-setup)
4. [Database Setup](#database-setup)
5. [Redis Setup](#redis-setup)
6. [External Service Configuration](#external-service-configuration)
7. [Application Deployment](#application-deployment)
8. [Verification and Testing](#verification-and-testing)
9. [Production Considerations](#production-considerations)
10. [Rollback Procedures](#rollback-procedures)

---

## Prerequisites

Before deploying the CRM Communication Engine, ensure you have:

### Required Accounts and Services

- [ ] PostgreSQL 13+ database instance
- [ ] Redis 6+ instance (for caching)
- [ ] WhatsApp Business API account (optional but recommended)
- [ ] Twilio account with SMS capabilities (optional but recommended)
- [ ] SMTP server credentials (Gmail, SendGrid, AWS SES, etc.)
- [ ] SSL/TLS certificates for production deployment

### Required Tools

- [ ] Python 3.9 or higher
- [ ] pip (Python package manager)
- [ ] Git
- [ ] Docker and Docker Compose (optional, for containerized deployment)
- [ ] PostgreSQL client tools (psql)
- [ ] Redis client tools (redis-cli)

### Access Requirements

- [ ] Database admin credentials
- [ ] Server SSH access (for production deployment)
- [ ] DNS configuration access (for custom domains)
- [ ] Firewall configuration access

---

## System Requirements

### Minimum Requirements (Development)

- **CPU**: 2 cores
- **RAM**: 4 GB
- **Storage**: 20 GB
- **Network**: 10 Mbps

### Recommended Requirements (Production)

- **CPU**: 4+ cores
- **RAM**: 8+ GB
- **Storage**: 100+ GB SSD
- **Network**: 100+ Mbps
- **Load Balancer**: Nginx or AWS ALB

### Supported Operating Systems

- Ubuntu 20.04 LTS or higher
- Debian 11 or higher
- CentOS 8 or higher
- macOS 11+ (development only)
- Windows 10/11 with WSL2 (development only)

---

## Environment Setup

### Step 1: Clone the Repository

```bash
git clone https://github.com/your-org/event-planning-agent-v2.git
cd event-planning-agent-v2
```

### Step 2: Create Virtual Environment

```bash
# Create virtual environment
python3 -m venv venv

# Activate virtual environment
# On Linux/macOS:
source venv/bin/activate

# On Windows:
venv\Scripts\activate
```

### Step 3: Install Dependencies

```bash
# Upgrade pip
pip install --upgrade pip

# Install production dependencies
pip install -r requirements.txt

# For development, also install dev dependencies
pip install -r requirements_dev.txt
```

### Step 4: Configure Environment Variables

Create a `.env` file in the project root:

```bash
cp .env.template .env
```

Edit `.env` with your configuration (see [Environment Variables](#environment-variables) section below).

---

## Database Setup

### Step 1: Create Database

```bash
# Connect to PostgreSQL
psql -U postgres -h localhost

# Create database
CREATE DATABASE event_planning_crm;

# Create user (if not exists)
CREATE USER crm_user WITH PASSWORD 'your_secure_password';

# Grant privileges
GRANT ALL PRIVILEGES ON DATABASE event_planning_crm TO crm_user;

# Exit psql
\q
```

### Step 2: Enable Required Extensions

```bash
psql -U crm_user -d event_planning_crm

# Enable UUID extension
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

# Enable pgcrypto for encryption
CREATE EXTENSION IF NOT EXISTS "pgcrypto";

# Exit
\q
```

### Step 3: Run Database Migrations

```bash
# Navigate to database directory
cd event_planning_agent_v2/database

# Run CRM schema migration
python run_crm_migration.py

# Verify migration
psql -U crm_user -d event_planning_crm -c "\dt"
```

Expected tables:
- `crm_communications`
- `crm_client_preferences`
- `crm_communication_templates`
- `crm_delivery_logs`

### Step 4: Verify Database Setup

```bash
# Run database verification script
python -c "
from event_planning_agent_v2.database.db_manager import DatabaseManager
db = DatabaseManager()
print('Database connection: OK')
"
```

---

## Redis Setup

### Option 1: Local Redis Installation

#### Ubuntu/Debian

```bash
sudo apt update
sudo apt install redis-server

# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Verify Redis is running
redis-cli ping
# Expected output: PONG
```

#### macOS

```bash
brew install redis

# Start Redis
brew services start redis

# Verify
redis-cli ping
```

### Option 2: Docker Redis

```bash
docker run -d \
  --name redis-crm \
  -p 6379:6379 \
  -v redis-data:/data \
  redis:7-alpine \
  redis-server --appendonly yes
```

### Step 3: Configure Redis

Edit `/etc/redis/redis.conf` (Linux) or `/usr/local/etc/redis.conf` (macOS):

```conf
# Set password
requirepass your_redis_password

# Set max memory
maxmemory 2gb
maxmemory-policy allkeys-lru

# Enable persistence
save 900 1
save 300 10
save 60 10000
```

Restart Redis:
```bash
sudo systemctl restart redis-server
```

### Step 4: Verify Redis Setup

```bash
# Test connection
redis-cli -a your_redis_password ping

# Test set/get
redis-cli -a your_redis_password SET test "Hello"
redis-cli -a your_redis_password GET test
```

---

## External Service Configuration

### WhatsApp Business API Setup

#### Step 1: Create WhatsApp Business Account

1. Go to [Facebook Business Manager](https://business.facebook.com/)
2. Create a new business account or use existing
3. Navigate to WhatsApp > API Setup
4. Follow the verification process

#### Step 2: Get API Credentials

1. In WhatsApp API Settings, note:
   - **Phone Number ID**: `1234567890`
   - **WhatsApp Business Account ID**: `9876543210`
   - **Access Token**: `EAAxxxxxxxxxxxxx`

2. Set up webhook:
   - **Webhook URL**: `https://your-domain.com/api/crm/webhooks/whatsapp`
   - **Verify Token**: Generate a random string (e.g., `whatsapp_verify_token_xyz`)

#### Step 3: Configure in .env

```bash
# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID=1234567890
WHATSAPP_BUSINESS_ACCOUNT_ID=9876543210
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxx
WHATSAPP_WEBHOOK_VERIFY_TOKEN=whatsapp_verify_token_xyz
WHATSAPP_API_VERSION=v18.0
```

#### Step 4: Test WhatsApp Integration

```bash
python event_planning_agent_v2/crm/test_whatsapp.py
```

---

### Twilio SMS Setup

#### Step 1: Create Twilio Account

1. Sign up at [Twilio](https://www.twilio.com/try-twilio)
2. Verify your email and phone number
3. Get a Twilio phone number

#### Step 2: Get API Credentials

1. From Twilio Console Dashboard:
   - **Account SID**: `ACxxxxxxxxxxxxx`
   - **Auth Token**: `your_auth_token`
   - **Phone Number**: `+11234567890`

2. Configure webhook:
   - Go to Phone Numbers > Manage > Active Numbers
   - Select your number
   - Under Messaging, set:
     - **Webhook URL**: `https://your-domain.com/api/crm/webhooks/twilio`
     - **HTTP Method**: POST

#### Step 3: Configure in .env

```bash
# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+11234567890
TWILIO_WEBHOOK_URL=https://your-domain.com/api/crm/webhooks/twilio
```

#### Step 4: Test Twilio Integration

```bash
python event_planning_agent_v2/crm/test_twilio.py
```

---

### SMTP Email Setup

#### Option 1: Gmail SMTP

1. Enable 2-Factor Authentication on your Google account
2. Generate an App Password:
   - Go to Google Account > Security > App Passwords
   - Select "Mail" and "Other (Custom name)"
   - Copy the generated password

3. Configure in .env:
```bash
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Planiva Event Planning
SMTP_USE_TLS=true
```

#### Option 2: SendGrid

1. Sign up at [SendGrid](https://sendgrid.com/)
2. Create an API key
3. Verify sender identity

Configure in .env:
```bash
SMTP_HOST=smtp.sendgrid.net
SMTP_PORT=587
SMTP_USERNAME=apikey
SMTP_PASSWORD=your_sendgrid_api_key
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Planiva Event Planning
SMTP_USE_TLS=true
```

#### Option 3: AWS SES

1. Set up AWS SES in your region
2. Verify domain or email address
3. Create SMTP credentials

Configure in .env:
```bash
SMTP_HOST=email-smtp.us-east-1.amazonaws.com
SMTP_PORT=587
SMTP_USERNAME=your_ses_smtp_username
SMTP_PASSWORD=your_ses_smtp_password
SMTP_FROM_EMAIL=noreply@yourdomain.com
SMTP_FROM_NAME=Planiva Event Planning
SMTP_USE_TLS=true
```

#### Test SMTP Configuration

```bash
python event_planning_agent_v2/crm/test_smtp.py
```

---

## Application Deployment

### Development Deployment

```bash
# Activate virtual environment
source venv/bin/activate

# Run database migrations
python event_planning_agent_v2/database/run_crm_migration.py

# Start the application
python event_planning_agent_v2/main.py

# Or use uvicorn directly
uvicorn event_planning_agent_v2.api.app:app --reload --host 0.0.0.0 --port 8000
```

Access the application at `http://localhost:8000`

---

### Production Deployment with Docker

#### Step 1: Build Docker Image

```bash
# Build the image
docker build -t event-planning-crm:latest -f docker/Dockerfile .

# Verify image
docker images | grep event-planning-crm
```

#### Step 2: Create Docker Compose Configuration

Create `docker-compose.prod.yml`:

```yaml
version: '3.8'

services:
  app:
    image: event-planning-crm:latest
    container_name: crm-app
    restart: unless-stopped
    ports:
      - "8000:8000"
    environment:
      - DATABASE_URL=${DATABASE_URL}
      - REDIS_URL=${REDIS_URL}
      - WHATSAPP_ACCESS_TOKEN=${WHATSAPP_ACCESS_TOKEN}
      - TWILIO_AUTH_TOKEN=${TWILIO_AUTH_TOKEN}
      - SMTP_PASSWORD=${SMTP_PASSWORD}
    depends_on:
      - postgres
      - redis
    networks:
      - crm-network
    volumes:
      - ./logs:/app/logs
      - ./templates:/app/templates

  postgres:
    image: postgres:15-alpine
    container_name: crm-postgres
    restart: unless-stopped
    environment:
      - POSTGRES_DB=event_planning_crm
      - POSTGRES_USER=crm_user
      - POSTGRES_PASSWORD=${DB_PASSWORD}
    volumes:
      - postgres-data:/var/lib/postgresql/data
    networks:
      - crm-network

  redis:
    image: redis:7-alpine
    container_name: crm-redis
    restart: unless-stopped
    command: redis-server --requirepass ${REDIS_PASSWORD}
    volumes:
      - redis-data:/data
    networks:
      - crm-network

  nginx:
    image: nginx:alpine
    container_name: crm-nginx
    restart: unless-stopped
    ports:
      - "80:80"
      - "443:443"
    volumes:
      - ./nginx/nginx.conf:/etc/nginx/nginx.conf
      - ./nginx/ssl:/etc/nginx/ssl
    depends_on:
      - app
    networks:
      - crm-network

volumes:
  postgres-data:
  redis-data:

networks:
  crm-network:
    driver: bridge
```

#### Step 3: Deploy with Docker Compose

```bash
# Start all services
docker-compose -f docker-compose.prod.yml up -d

# Check status
docker-compose -f docker-compose.prod.yml ps

# View logs
docker-compose -f docker-compose.prod.yml logs -f app
```

---

### Production Deployment with Systemd

#### Step 1: Create Systemd Service File

Create `/etc/systemd/system/crm-app.service`:

```ini
[Unit]
Description=Event Planning CRM Communication Engine
After=network.target postgresql.service redis.service

[Service]
Type=simple
User=crm-user
Group=crm-user
WorkingDirectory=/opt/event-planning-crm
Environment="PATH=/opt/event-planning-crm/venv/bin"
EnvironmentFile=/opt/event-planning-crm/.env
ExecStart=/opt/event-planning-crm/venv/bin/uvicorn event_planning_agent_v2.api.app:app --host 0.0.0.0 --port 8000 --workers 4
Restart=always
RestartSec=10

[Install]
WantedBy=multi-user.target
```

#### Step 2: Enable and Start Service

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service
sudo systemctl enable crm-app

# Start service
sudo systemctl start crm-app

# Check status
sudo systemctl status crm-app

# View logs
sudo journalctl -u crm-app -f
```

---

### Nginx Configuration

Create `/etc/nginx/sites-available/crm-app`:

```nginx
upstream crm_backend {
    server 127.0.0.1:8000;
}

server {
    listen 80;
    server_name your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com;

    # SSL Configuration
    ssl_certificate /etc/nginx/ssl/cert.pem;
    ssl_certificate_key /etc/nginx/ssl/key.pem;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers HIGH:!aNULL:!MD5;

    # Security Headers
    add_header X-Frame-Options "SAMEORIGIN" always;
    add_header X-Content-Type-Options "nosniff" always;
    add_header X-XSS-Protection "1; mode=block" always;

    # Logging
    access_log /var/log/nginx/crm-access.log;
    error_log /var/log/nginx/crm-error.log;

    # API Proxy
    location /api/ {
        proxy_pass http://crm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        
        # Timeouts
        proxy_connect_timeout 60s;
        proxy_send_timeout 60s;
        proxy_read_timeout 60s;
    }

    # Webhook endpoints (no auth required)
    location /api/crm/webhooks/ {
        proxy_pass http://crm_backend;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        
        # Larger body size for webhooks
        client_max_body_size 10M;
    }

    # Health check
    location /health {
        proxy_pass http://crm_backend;
        access_log off;
    }
}
```

Enable the site:
```bash
sudo ln -s /etc/nginx/sites-available/crm-app /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

---

## Verification and Testing

### Step 1: Health Check

```bash
curl http://localhost:8000/api/crm/health
```

Expected response:
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

### Step 2: Database Connectivity

```bash
python -c "
from event_planning_agent_v2.crm.repository import CommunicationRepository
repo = CommunicationRepository()
print('Database: OK')
"
```

### Step 3: Redis Connectivity

```bash
python -c "
from event_planning_agent_v2.crm.cache_manager import CacheManager
cache = CacheManager()
cache.set('test', 'value', ttl=60)
print('Redis: OK')
"
```

### Step 4: Send Test Communication

```bash
python event_planning_agent_v2/crm/test_end_to_end.py
```

### Step 5: Run Integration Tests

```bash
pytest event_planning_agent_v2/tests/integration/test_crm_end_to_end.py -v
```

---

## Production Considerations

### Security Hardening

1. **Enable Firewall**:
```bash
sudo ufw allow 22/tcp
sudo ufw allow 80/tcp
sudo ufw allow 443/tcp
sudo ufw enable
```

2. **Secure Database**:
```bash
# Edit PostgreSQL config
sudo nano /etc/postgresql/13/main/pg_hba.conf

# Change to:
# local   all   all   md5
# host    all   all   127.0.0.1/32   md5
```

3. **Rotate Credentials**:
- Set up quarterly credential rotation
- Use secrets management (AWS Secrets Manager, HashiCorp Vault)

4. **Enable Audit Logging**:
```bash
# In .env
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_PATH=/var/log/crm/audit.log
```

### Monitoring Setup

1. **Prometheus Metrics**:
```bash
# Access metrics endpoint
curl http://localhost:8000/metrics
```

2. **Grafana Dashboard**:
- Import dashboard from `monitoring/grafana-dashboard.json`
- Configure data source to Prometheus

3. **Alerting**:
```bash
# Configure alerting rules
cp event_planning_agent_v2/crm/alerting_rules.py /etc/prometheus/rules/
```

### Backup Strategy

1. **Database Backups**:
```bash
# Daily backup script
#!/bin/bash
pg_dump -U crm_user event_planning_crm | gzip > /backups/crm_$(date +%Y%m%d).sql.gz

# Add to crontab
0 2 * * * /opt/scripts/backup_db.sh
```

2. **Redis Backups**:
```bash
# Redis automatically saves to dump.rdb
# Copy to backup location
cp /var/lib/redis/dump.rdb /backups/redis_$(date +%Y%m%d).rdb
```

### Scaling Considerations

1. **Horizontal Scaling**:
- Deploy multiple app instances behind load balancer
- Use Redis for distributed caching
- Configure session affinity if needed

2. **Database Scaling**:
- Set up read replicas for analytics queries
- Implement connection pooling (max 20 connections per instance)

3. **Rate Limiting**:
- Configure Nginx rate limiting
- Implement application-level rate limiting

---

## Rollback Procedures

### Application Rollback

```bash
# Stop current version
sudo systemctl stop crm-app

# Restore previous version
cd /opt/event-planning-crm
git checkout <previous-tag>
source venv/bin/activate
pip install -r requirements.txt

# Start service
sudo systemctl start crm-app
```

### Database Rollback

```bash
# Restore from backup
gunzip < /backups/crm_20251026.sql.gz | psql -U crm_user event_planning_crm

# Or use point-in-time recovery
# (requires WAL archiving to be enabled)
```

### Docker Rollback

```bash
# Stop current containers
docker-compose -f docker-compose.prod.yml down

# Deploy previous version
docker pull event-planning-crm:previous-tag
docker-compose -f docker-compose.prod.yml up -d
```

---

## Environment Variables

Complete list of required environment variables:

```bash
# Database Configuration
DATABASE_URL=postgresql://crm_user:password@localhost:5432/event_planning_crm
DB_ENCRYPTION_KEY=your_32_character_encryption_key

# Redis Configuration
REDIS_URL=redis://:password@localhost:6379/0
REDIS_PASSWORD=your_redis_password

# WhatsApp Configuration
WHATSAPP_PHONE_NUMBER_ID=1234567890
WHATSAPP_BUSINESS_ACCOUNT_ID=9876543210
WHATSAPP_ACCESS_TOKEN=EAAxxxxxxxxxxxxx
WHATSAPP_WEBHOOK_VERIFY_TOKEN=whatsapp_verify_token_xyz
WHATSAPP_API_VERSION=v18.0

# Twilio Configuration
TWILIO_ACCOUNT_SID=ACxxxxxxxxxxxxx
TWILIO_AUTH_TOKEN=your_auth_token
TWILIO_PHONE_NUMBER=+11234567890
TWILIO_WEBHOOK_URL=https://your-domain.com/api/crm/webhooks/twilio

# SMTP Configuration
SMTP_HOST=smtp.gmail.com
SMTP_PORT=587
SMTP_USERNAME=your-email@gmail.com
SMTP_PASSWORD=your_app_password
SMTP_FROM_EMAIL=your-email@gmail.com
SMTP_FROM_NAME=Planiva Event Planning
SMTP_USE_TLS=true

# Application Configuration
APP_ENV=production
LOG_LEVEL=INFO
ENABLE_AUDIT_LOGGING=true
AUDIT_LOG_PATH=/var/log/crm/audit.log

# Security Configuration
JWT_SECRET_KEY=your_jwt_secret_key
JWT_ALGORITHM=HS256
JWT_EXPIRATION_MINUTES=60

# Monitoring Configuration
PROMETHEUS_ENABLED=true
PROMETHEUS_PORT=9090
```

---

## Troubleshooting

See [TROUBLESHOOTING_GUIDE.md](./TROUBLESHOOTING_GUIDE.md) for common issues and solutions.

---

## Support

For deployment support:
- Email: devops@planiva.com
- Slack: #crm-deployment
- Documentation: https://docs.planiva.com/deployment
