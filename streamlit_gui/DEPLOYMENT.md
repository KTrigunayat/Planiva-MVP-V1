# Deployment Guide

This guide covers deploying the Event Planning Agent v2 Streamlit GUI in various environments.

## Prerequisites

- Docker and Docker Compose installed
- Access to the Event Planning Agent v2 API
- Environment configuration files

## Environment Configuration

Create environment-specific configuration files:

### Development (.env.development)
```bash
# API Configuration
API_BASE_URL=http://localhost:8000
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3

# UI Configuration
APP_TITLE="Event Planning Agent (Dev)"
APP_ICON="🎉"
ENVIRONMENT=development

# Performance
CACHE_TTL=60
ENABLE_DEBUG=true
```

### Production (.env.production)
```bash
# API Configuration
API_BASE_URL=https://api.eventplanning.com
API_TIMEOUT=30
API_RETRY_ATTEMPTS=3

# UI Configuration
APP_TITLE="Event Planning Agent"
APP_ICON="🎉"
ENVIRONMENT=production

# Performance
CACHE_TTL=300
ENABLE_DEBUG=false

# Security
ENABLE_HTTPS=true
SESSION_TIMEOUT=3600
```

## Deployment Methods

### 1. Docker Deployment (Recommended)

#### Quick Start
```bash
# Clone the repository
git clone <repository-url>
cd streamlit_gui

# Build and run
docker-compose up --build
```

#### Production Deployment
```bash
# Use the deployment script
chmod +x scripts/deploy.sh
./scripts/deploy.sh production
```

#### Custom Docker Run
```bash
# Build image
docker build -t event-planning-gui:latest .

# Run container
docker run -d \
  --name event-planning-gui \
  --restart unless-stopped \
  -p 8501:8501 \
  --env-file .env.production \
  event-planning-gui:latest
```

### 2. Direct Python Deployment

#### Install Dependencies
```bash
pip install -r requirements.txt
```

#### Run Application
```bash
# Load environment variables
export $(cat .env.production | grep -v '^#' | xargs)

# Start Streamlit
streamlit run app.py --server.port=8501 --server.address=0.0.0.0
```

### 3. Development Environment

#### Using Docker Compose
```bash
# Start development environment
docker-compose -f docker-compose.dev.yml up --build

# Stop environment
docker-compose -f docker-compose.dev.yml down
```

#### Using Development Script
```bash
chmod +x scripts/dev.sh
./scripts/dev.sh run
```

## Reverse Proxy Configuration

### Nginx Configuration
```nginx
server {
    listen 80;
    server_name your-domain.com;
    
    location / {
        proxy_pass http://localhost:8501;
        proxy_http_version 1.1;
        proxy_set_header Upgrade $http_upgrade;
        proxy_set_header Connection "upgrade";
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_cache_bypass $http_upgrade;
    }
}
```

### Apache Configuration
```apache
<VirtualHost *:80>
    ServerName your-domain.com
    
    ProxyPreserveHost On
    ProxyRequests Off
    ProxyPass / http://localhost:8501/
    ProxyPassReverse / http://localhost:8501/
    
    # WebSocket support
    RewriteEngine on
    RewriteCond %{HTTP:Upgrade} websocket [NC]
    RewriteCond %{HTTP:Connection} upgrade [NC]
    RewriteRule ^/?(.*) "ws://localhost:8501/$1" [P,L]
</VirtualHost>
```

## SSL/HTTPS Configuration

### Using Let's Encrypt with Nginx
```bash
# Install Certbot
sudo apt install certbot python3-certbot-nginx

# Obtain certificate
sudo certbot --nginx -d your-domain.com

# Auto-renewal
sudo crontab -e
# Add: 0 12 * * * /usr/bin/certbot renew --quiet
```

### Using Custom SSL Certificate
```nginx
server {
    listen 443 ssl;
    server_name your-domain.com;
    
    ssl_certificate /path/to/certificate.crt;
    ssl_certificate_key /path/to/private.key;
    
    # SSL configuration
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512;
    ssl_prefer_server_ciphers off;
    
    location / {
        proxy_pass http://localhost:8501;
        # ... other proxy settings
    }
}
```

## Monitoring and Logging

### Health Checks
The application includes built-in health checks:
- Docker health check: `/_stcore/health`
- Custom health endpoint: `/health` (if implemented)

### Logging Configuration
```bash
# Environment variables for logging
STREAMLIT_LOGGER_LEVEL=INFO
STREAMLIT_CLIENT_TOOLBAR_MODE=minimal
STREAMLIT_CLIENT_SHOW_ERROR_DETAILS=false
```

### Log Collection
```bash
# View container logs
docker logs event-planning-gui

# Follow logs in real-time
docker logs -f event-planning-gui

# Export logs
docker logs event-planning-gui > app.log 2>&1
```

## Performance Optimization

### Caching Configuration
```bash
# Environment variables
CACHE_TTL=300
ENABLE_CACHING=true
MAX_CONCURRENT_REQUESTS=10
```

### Resource Limits
```yaml
# docker-compose.yml
services:
  streamlit-gui:
    deploy:
      resources:
        limits:
          cpus: '2.0'
          memory: 2G
        reservations:
          cpus: '1.0'
          memory: 1G
```

### Database Connection Pooling
```bash
# For PostgreSQL connections
DB_POOL_SIZE=20
DB_MAX_OVERFLOW=30
DB_POOL_TIMEOUT=30
```

## Security Considerations

### Environment Variables
- Never commit `.env` files to version control
- Use secrets management for production
- Rotate API keys regularly

### Network Security
```bash
# Firewall rules (UFW example)
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw deny 8501/tcp   # Block direct access to Streamlit
```

### Container Security
```dockerfile
# Use non-root user
RUN useradd -m -u 1000 streamlit
USER streamlit

# Read-only filesystem
docker run --read-only --tmpfs /tmp event-planning-gui
```

## Backup and Recovery

### Data Backup
```bash
# Backup configuration
tar -czf config-backup-$(date +%Y%m%d).tar.gz .env* config/

# Backup logs
docker logs event-planning-gui > logs-backup-$(date +%Y%m%d).log
```

### Disaster Recovery
```bash
# Quick recovery script
#!/bin/bash
docker pull event-planning-gui:latest
docker stop event-planning-gui || true
docker rm event-planning-gui || true
docker run -d --name event-planning-gui --env-file .env.production event-planning-gui:latest
```

## Troubleshooting

### Common Issues

#### Container Won't Start
```bash
# Check logs
docker logs event-planning-gui

# Check configuration
docker exec event-planning-gui env | grep API_

# Test API connectivity
docker exec event-planning-gui curl -f $API_BASE_URL/health
```

#### Performance Issues
```bash
# Check resource usage
docker stats event-planning-gui

# Monitor API response times
curl -w "@curl-format.txt" -o /dev/null -s $API_BASE_URL/health
```

#### SSL Certificate Issues
```bash
# Test SSL configuration
openssl s_client -connect your-domain.com:443 -servername your-domain.com

# Check certificate expiry
echo | openssl s_client -connect your-domain.com:443 2>/dev/null | openssl x509 -noout -dates
```

### Debug Mode
```bash
# Enable debug logging
export STREAMLIT_LOGGER_LEVEL=DEBUG
export ENABLE_DEBUG=true

# Run with debug output
streamlit run app.py --logger.level=debug
```

## Scaling and Load Balancing

### Multiple Instances
```yaml
# docker-compose.yml for multiple instances
version: '3.8'
services:
  streamlit-gui-1:
    image: event-planning-gui:latest
    ports:
      - "8501:8501"
  
  streamlit-gui-2:
    image: event-planning-gui:latest
    ports:
      - "8502:8501"
  
  nginx:
    image: nginx:alpine
    ports:
      - "80:80"
    volumes:
      - ./nginx.conf:/etc/nginx/nginx.conf
```

### Load Balancer Configuration
```nginx
upstream streamlit_backend {
    server localhost:8501;
    server localhost:8502;
}

server {
    listen 80;
    location / {
        proxy_pass http://streamlit_backend;
    }
}
```

## Maintenance

### Updates
```bash
# Update application
git pull origin main
docker-compose build --no-cache
docker-compose up -d

# Update dependencies
pip install -r requirements.txt --upgrade
```

### Cleanup
```bash
# Remove old images
docker image prune -f

# Remove unused volumes
docker volume prune -f

# Clean up logs
find /var/log -name "*.log" -mtime +30 -delete
```

This deployment guide provides comprehensive instructions for deploying the Event Planning Agent v2 Streamlit GUI in various environments with proper security, monitoring, and maintenance procedures.