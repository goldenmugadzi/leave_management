# Change Requests Deployment Guide

## Table of Contents

1. [Overview](#overview)
2. [Prerequisites](#prerequisites)
3. [Installation](#installation)
4. [Configuration](#configuration)
5. [Database Setup](#database-setup)
6. [Deployment](#deployment)
7. [Post-Deployment](#post-deployment)
8. [Monitoring](#monitoring)
9. [Maintenance](#maintenance)
10. [Troubleshooting](#troubleshooting)

## Overview

This guide provides step-by-step instructions for deploying the Change Requests system in a production environment. The system is built with Django and requires proper configuration for security, performance, and reliability.

## Prerequisites

### System Requirements

- **Operating System**: Linux (Ubuntu 20.04+ recommended)
- **Python**: 3.8 or higher
- **Django**: 3.2 or higher
- **Database**: MySQL 8.0+ or PostgreSQL 12+
- **Web Server**: Nginx or Apache
- **WSGI Server**: Gunicorn or uWSGI
- **Cache**: Redis (recommended) or Memcached

### Software Dependencies

```bash
# Python packages
Django>=3.2.0
mysqlclient>=2.0.0  # For MySQL
psycopg2-binary>=2.8.0  # For PostgreSQL
redis>=3.5.0
gunicorn>=20.0.0
celery>=5.0.0  # For background tasks (optional)

# System packages
nginx
supervisor  # For process management
```

### User and Permissions

Create a dedicated user for the application:

```bash
sudo useradd -m -s /bin/bash change_requests
sudo usermod -aG www-data change_requests
```

## Installation

### 1. Clone the Repository

```bash
cd /var/www
sudo git clone <repository-url> beii_v1
sudo chown -R change_requests:change_requests /var/www/beii_v1
```

### 2. Create Virtual Environment

```bash
cd /var/www/beii_v1
sudo -u change_requests python3 -m venv env-beii
sudo -u change_requests /var/www/env-beii/bin/pip install --upgrade pip
```

### 3. Install Dependencies

```bash
sudo -u change_requests /var/www/env-beii/bin/pip install -r requirements.txt
```

### 4. Install System Dependencies

#### Ubuntu/Debian
```bash
sudo apt update
sudo apt install -y python3-dev python3-pip python3-venv
sudo apt install -y mysql-server mysql-client libmysqlclient-dev
sudo apt install -y nginx supervisor redis-server
```

#### CentOS/RHEL
```bash
sudo yum update
sudo yum install -y python3-devel python3-pip
sudo yum install -y mysql-server mysql-devel
sudo yum install -y nginx supervisor redis
```

## Configuration

### 1. Environment Variables

Create environment configuration file:

```bash
sudo -u change_requests cp /var/www/beii_v1/.env.example /var/www/beii_v1/.env
```

Edit the environment file:

```bash
# Database Configuration
DATABASE_URL=mysql://username:password@localhost/beii_v1
# or for PostgreSQL:
# DATABASE_URL=postgresql://username:password@localhost/beii_v1

# Cache Configuration
REDIS_URL=redis://localhost:6379/0

# Security
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=your-domain.com,www.your-domain.com

# Logging
LOG_LEVEL=INFO
LOG_FILE=/var/log/change_requests/change_requests.log

# Email Configuration (for notifications)
EMAIL_HOST=smtp.your-provider.com
EMAIL_PORT=587
EMAIL_USE_TLS=True
EMAIL_HOST_USER=your-email@domain.com
EMAIL_HOST_PASSWORD=your-email-password
```

### 2. Django Settings

Update Django settings for production:

```python
# settings.py
import os
from pathlib import Path

# Build paths inside the project
BASE_DIR = Path(__file__).resolve().parent.parent

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY')
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'
ALLOWED_HOSTS = os.environ.get('ALLOWED_HOSTS', '').split(',')

# Database
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.mysql',
        'NAME': os.environ.get('DB_NAME', 'beii_v1'),
        'USER': os.environ.get('DB_USER', 'change_requests'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST', 'localhost'),
        'PORT': os.environ.get('DB_PORT', '3306'),
        'OPTIONS': {
            'init_command': "SET sql_mode='STRICT_TRANS_TABLES'",
        },
    }
}

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django_redis.cache.RedisCache',
        'LOCATION': os.environ.get('REDIS_URL', 'redis://127.0.0.1:6379/1'),
        'OPTIONS': {
            'CLIENT_CLASS': 'django_redis.client.DefaultClient',
        }
    }
}

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'file': {
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'class': 'logging.handlers.RotatingFileHandler',
            'filename': os.environ.get('LOG_FILE', '/var/log/change_requests/change_requests.log'),
            'maxBytes': 1024*1024*15,  # 15MB
            'backupCount': 10,
            'formatter': 'verbose',
        },
        'console': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'it.change_requests': {
            'handlers': ['file', 'console'],
            'level': os.environ.get('LOG_LEVEL', 'INFO'),
            'propagate': True,
        },
    },
}

# Static files
STATIC_URL = '/static/'
STATIC_ROOT = os.path.join(BASE_DIR, 'staticfiles')

# Media files
MEDIA_URL = '/media/'
MEDIA_ROOT = os.path.join(BASE_DIR, 'media')

# Security settings
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
SECURE_HSTS_SECONDS = 31536000
SECURE_HSTS_INCLUDE_SUBDOMAINS = True
SECURE_HSTS_PRELOAD = True

# Session settings
SESSION_COOKIE_SECURE = True
CSRF_COOKIE_SECURE = True
SESSION_COOKIE_HTTPONLY = True
CSRF_COOKIE_HTTPONLY = True
```

## Database Setup

### 1. Create Database

#### MySQL
```sql
CREATE DATABASE beii_v1 CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci;
CREATE USER 'change_requests'@'localhost' IDENTIFIED BY 'secure_password';
GRANT ALL PRIVILEGES ON beii_v1.* TO 'change_requests'@'localhost';
FLUSH PRIVILEGES;
```

#### PostgreSQL
```sql
CREATE DATABASE beii_v1;
CREATE USER change_requests WITH PASSWORD 'secure_password';
GRANT ALL PRIVILEGES ON DATABASE beii_v1 TO change_requests;
```

### 2. Run Migrations

```bash
cd /var/www/beii_v1
sudo -u change_requests /var/www/env-beii/bin/python manage.py migrate
```

### 3. Create Superuser

```bash
sudo -u change_requests /var/www/env-beii/bin/python manage.py createsuperuser
```

### 4. Collect Static Files

```bash
sudo -u change_requests /var/www/env-beii/bin/python manage.py collectstatic --noinput
```

## Deployment

### 1. Gunicorn Configuration

Create Gunicorn configuration file:

```bash
sudo -u change_requests mkdir -p /var/www/beii_v1/config
```

```python
# config/gunicorn.conf.py
bind = "127.0.0.1:8000"
workers = 3
worker_class = "sync"
worker_connections = 1000
max_requests = 1000
max_requests_jitter = 100
timeout = 30
keepalive = 2
preload_app = True
user = "change_requests"
group = "change_requests"
tmp_upload_dir = None
```

### 2. Supervisor Configuration

Create Supervisor configuration:

```bash
sudo nano /etc/supervisor/conf.d/change_requests.conf
```

```ini
[program:change_requests]
command=/var/www/env-beii/bin/gunicorn --config /var/www/beii_v1/config/gunicorn.conf.py beii_v1.wsgi:application
directory=/var/www/beii_v1
user=change_requests
autostart=true
autorestart=true
redirect_stderr=true
stdout_logfile=/var/log/change_requests/gunicorn.log
stdout_logfile_maxbytes=50MB
stdout_logfile_backups=10
```

### 3. Nginx Configuration

Create Nginx configuration:

```bash
sudo nano /etc/nginx/sites-available/change_requests
```

```nginx
server {
    listen 80;
    server_name your-domain.com www.your-domain.com;
    
    # Redirect HTTP to HTTPS
    return 301 https://$server_name$request_uri;
}

server {
    listen 443 ssl http2;
    server_name your-domain.com www.your-domain.com;
    
    # SSL Configuration
    ssl_certificate /path/to/your/certificate.crt;
    ssl_certificate_key /path/to/your/private.key;
    ssl_protocols TLSv1.2 TLSv1.3;
    ssl_ciphers ECDHE-RSA-AES256-GCM-SHA512:DHE-RSA-AES256-GCM-SHA512:ECDHE-RSA-AES256-GCM-SHA384:DHE-RSA-AES256-GCM-SHA384;
    ssl_prefer_server_ciphers off;
    ssl_session_cache shared:SSL:10m;
    ssl_session_timeout 10m;
    
    # Security headers
    add_header X-Frame-Options DENY;
    add_header X-Content-Type-Options nosniff;
    add_header X-XSS-Protection "1; mode=block";
    add_header Strict-Transport-Security "max-age=31536000; includeSubDomains" always;
    
    # Static files
    location /static/ {
        alias /var/www/beii_v1/staticfiles/;
        expires 1y;
        add_header Cache-Control "public, immutable";
    }
    
    # Media files
    location /media/ {
        alias /var/www/beii_v1/media/;
        expires 1y;
        add_header Cache-Control "public";
    }
    
    # Application
    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
        proxy_redirect off;
        
        # Timeouts
        proxy_connect_timeout 30s;
        proxy_send_timeout 30s;
        proxy_read_timeout 30s;
    }
    
    # Health check
    location /health/ {
        access_log off;
        return 200 "healthy\n";
        add_header Content-Type text/plain;
    }
}
```

Enable the site:

```bash
sudo ln -s /etc/nginx/sites-available/change_requests /etc/nginx/sites-enabled/
sudo nginx -t
sudo systemctl reload nginx
```

### 4. Start Services

```bash
# Start Redis
sudo systemctl start redis-server
sudo systemctl enable redis-server

# Start Supervisor
sudo systemctl start supervisor
sudo systemctl enable supervisor

# Reload Supervisor configuration
sudo supervisorctl reread
sudo supervisorctl update
sudo supervisorctl start change_requests

# Start Nginx
sudo systemctl start nginx
sudo systemctl enable nginx
```

## Post-Deployment

### 1. Create Log Directory

```bash
sudo mkdir -p /var/log/change_requests
sudo chown change_requests:change_requests /var/log/change_requests
sudo chmod 755 /var/log/change_requests
```

### 2. Set Up Log Rotation

```bash
sudo nano /etc/logrotate.d/change_requests
```

```
/var/log/change_requests/*.log {
    daily
    missingok
    rotate 30
    compress
    delaycompress
    notifempty
    create 644 change_requests change_requests
    postrotate
        supervisorctl restart change_requests
    endscript
}
```

### 3. Set Up Monitoring

#### Basic Health Check Script

```bash
sudo nano /usr/local/bin/change_requests_health.sh
```

```bash
#!/bin/bash

# Health check script for Change Requests
URL="https://your-domain.com/health/"
RESPONSE=$(curl -s -o /dev/null -w "%{http_code}" $URL)

if [ $RESPONSE -eq 200 ]; then
    echo "Change Requests is healthy"
    exit 0
else
    echo "Change Requests is unhealthy (HTTP $RESPONSE)"
    exit 1
fi
```

```bash
sudo chmod +x /usr/local/bin/change_requests_health.sh
```

#### Cron Job for Health Checks

```bash
sudo crontab -e
```

```
# Health check every 5 minutes
*/5 * * * * /usr/local/bin/change_requests_health.sh
```

### 4. Backup Configuration

#### Database Backup Script

```bash
sudo nano /usr/local/bin/backup_change_requests.sh
```

```bash
#!/bin/bash

# Database backup script
BACKUP_DIR="/var/backups/change_requests"
DATE=$(date +%Y%m%d_%H%M%S)
DB_NAME="beii_v1"
DB_USER="change_requests"

# Create backup directory
mkdir -p $BACKUP_DIR

# Create database backup
mysqldump -u $DB_USER -p$DB_PASSWORD $DB_NAME > $BACKUP_DIR/db_backup_$DATE.sql

# Compress backup
gzip $BACKUP_DIR/db_backup_$DATE.sql

# Keep only last 7 days of backups
find $BACKUP_DIR -name "db_backup_*.sql.gz" -mtime +7 -delete

echo "Backup completed: db_backup_$DATE.sql.gz"
```

```bash
sudo chmod +x /usr/local/bin/backup_change_requests.sh
```

#### Daily Backup Cron Job

```bash
sudo crontab -e
```

```
# Daily backup at 2 AM
0 2 * * * /usr/local/bin/backup_change_requests.sh
```

## Monitoring

### 1. Application Monitoring

#### Log Monitoring
```bash
# Monitor application logs
tail -f /var/log/change_requests/change_requests.log

# Monitor Gunicorn logs
tail -f /var/log/change_requests/gunicorn.log

# Monitor Nginx logs
tail -f /var/log/nginx/access.log
tail -f /var/log/nginx/error.log
```

#### System Monitoring
```bash
# Monitor system resources
htop
iostat -x 1
free -h
df -h
```

### 2. Database Monitoring

```sql
-- Monitor database connections
SHOW PROCESSLIST;

-- Monitor slow queries
SHOW VARIABLES LIKE 'slow_query_log';
SHOW VARIABLES LIKE 'long_query_time';

-- Monitor database size
SELECT 
    table_schema AS 'Database',
    ROUND(SUM(data_length + index_length) / 1024 / 1024, 2) AS 'Size (MB)'
FROM information_schema.tables
WHERE table_schema = 'beii_v1'
GROUP BY table_schema;
```

### 3. Performance Monitoring

#### Cache Monitoring
```bash
# Redis monitoring
redis-cli info memory
redis-cli info stats
```

#### Application Performance
```bash
# Monitor Gunicorn workers
sudo supervisorctl status change_requests

# Monitor response times
curl -w "@curl-format.txt" -o /dev/null -s "https://your-domain.com/"
```

## Maintenance

### 1. Regular Maintenance Tasks

#### Weekly Tasks
- Review application logs for errors
- Check disk space usage
- Verify backup integrity
- Update system packages

#### Monthly Tasks
- Review database performance
- Clean up old log files
- Update application dependencies
- Review security logs

#### Quarterly Tasks
- Security audit
- Performance review
- Backup strategy review
- Disaster recovery testing

### 2. Database Maintenance

```sql
-- Optimize tables
OPTIMIZE TABLE change_requests_changerequest;
OPTIMIZE TABLE change_requests_crapproval;

-- Clean up old soft-deleted records (optional)
DELETE FROM change_requests_changerequest 
WHERE is_deleted = 1 
AND deleted_at < DATE_SUB(NOW(), INTERVAL 1 YEAR);
```

### 3. Application Updates

```bash
# Update application code
cd /var/www/beii_v1
sudo -u change_requests git pull origin main

# Update dependencies
sudo -u change_requests /var/www/env-beii/bin/pip install -r requirements.txt

# Run migrations
sudo -u change_requests /var/www/env-beii/bin/python manage.py migrate

# Collect static files
sudo -u change_requests /var/www/env-beii/bin/python manage.py collectstatic --noinput

# Restart application
sudo supervisorctl restart change_requests
```

## Troubleshooting

### Common Issues

#### 1. Application Won't Start

**Check logs:**
```bash
sudo supervisorctl status change_requests
sudo supervisorctl tail change_requests
```

**Common causes:**
- Database connection issues
- Missing environment variables
- Permission problems
- Port conflicts

#### 2. Database Connection Issues

**Check database status:**
```bash
sudo systemctl status mysql
mysql -u change_requests -p -e "SELECT 1;"
```

**Common causes:**
- Database service not running
- Incorrect credentials
- Network connectivity issues
- Database permissions

#### 3. Performance Issues

**Check system resources:**
```bash
htop
iostat -x 1
free -h
```

**Check application logs:**
```bash
grep "ERROR" /var/log/change_requests/change_requests.log
grep "WARNING" /var/log/change_requests/change_requests.log
```

**Common causes:**
- High database load
- Memory issues
- Slow queries
- Cache problems

#### 4. SSL Certificate Issues

**Check certificate:**
```bash
openssl x509 -in /path/to/certificate.crt -text -noout
```

**Test SSL:**
```bash
openssl s_client -connect your-domain.com:443
```

### Debug Mode

For troubleshooting, temporarily enable debug mode:

```python
# settings.py
DEBUG = True
LOGGING['loggers']['it.change_requests']['level'] = 'DEBUG'
```

**Remember to disable debug mode in production!**

### Emergency Procedures

#### 1. Application Recovery
```bash
# Restart all services
sudo supervisorctl restart change_requests
sudo systemctl restart nginx
sudo systemctl restart redis-server
```

#### 2. Database Recovery
```bash
# Restore from backup
mysql -u change_requests -p beii_v1 < /var/backups/change_requests/db_backup_YYYYMMDD_HHMMSS.sql
```

#### 3. Rollback Deployment
```bash
# Rollback to previous version
cd /var/www/beii_v1
sudo -u change_requests git checkout previous-commit-hash
sudo supervisorctl restart change_requests
```

---

## Security Considerations

### 1. Firewall Configuration
```bash
# Allow only necessary ports
sudo ufw allow 22/tcp    # SSH
sudo ufw allow 80/tcp    # HTTP
sudo ufw allow 443/tcp   # HTTPS
sudo ufw enable
```

### 2. Regular Security Updates
```bash
# Update system packages
sudo apt update && sudo apt upgrade

# Update Python packages
sudo -u change_requests /var/www/env-beii/bin/pip list --outdated
sudo -u change_requests /var/www/env-beii/bin/pip install --upgrade package_name
```

### 3. Access Control
- Use strong passwords
- Implement two-factor authentication
- Regular security audits
- Monitor access logs

---

*This deployment guide should be reviewed and updated regularly to ensure it reflects the current system configuration and best practices.*
