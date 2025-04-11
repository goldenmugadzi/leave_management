#!/bin/bash

# Application DR Setup Script
# This script configures the application deployment on the DR site

# Configuration
APP_DIR="/var/www/beii_v1"
VENV_DIR="/var/www/venv"
GIT_REPO="your-git-repo-url"
BRANCH="main"
APP_USER="www-data"
APP_GROUP="www-data"
ENV_FILE=".env.dr"

# Function to setup Python virtual environment
setup_virtualenv() {
    echo "Setting up Python virtual environment..."
    
    # Install Python and virtualenv if not present
    if ! command -v python3 &> /dev/null; then
        apt-get update && apt-get install -y python3 python3-pip python3-venv
    fi
    
    # Create and activate virtual environment
    python3 -m venv "$VENV_DIR"
    source "$VENV_DIR/bin/activate"
    
    # Install required packages
    pip install -r "$APP_DIR/requirements.txt"
    pip install gunicorn
}

# Function to setup application directory
setup_app_dir() {
    echo "Setting up application directory..."
    
    # Create directory if it doesn't exist
    mkdir -p "$APP_DIR"
    
    # Clone repository if not already present
    if [ ! -d "$APP_DIR/.git" ]; then
        git clone "$GIT_REPO" "$APP_DIR"
        cd "$APP_DIR"
        git checkout "$BRANCH"
    else
        cd "$APP_DIR"
        git pull origin "$BRANCH"
    fi
    
    # Set permissions
    chown -R "$APP_USER:$APP_GROUP" "$APP_DIR"
    chmod -R 755 "$APP_DIR"
}

# Function to setup environment variables
setup_env() {
    echo "Setting up environment variables..."
    
    # Copy and modify environment file
    cp "$APP_DIR/.env" "$APP_DIR/$ENV_FILE"
    
    # Update DR-specific settings
    sed -i 's/DEBUG=True/DEBUG=False/' "$APP_DIR/$ENV_FILE"
    sed -i "s/DATABASE_HOST=.*/DATABASE_HOST=$DR_DB_HOST/" "$APP_DIR/$ENV_FILE"
    sed -i "s/ALLOWED_HOSTS=.*/ALLOWED_HOSTS=dr.yourdomain.com/" "$APP_DIR/$ENV_FILE"
}

# Function to setup Gunicorn service
setup_gunicorn() {
    echo "Setting up Gunicorn service..."
    
    cat > /etc/systemd/system/gunicorn.service << EOF
[Unit]
Description=gunicorn daemon
After=network.target

[Service]
User=$APP_USER
Group=$APP_GROUP
WorkingDirectory=$APP_DIR
Environment="PATH=$VENV_DIR/bin"
Environment="DJANGO_SETTINGS_MODULE=beii_v1.settings"
ExecStart=$VENV_DIR/bin/gunicorn \\
    --access-logfile - \\
    --workers 3 \\
    --bind unix:$APP_DIR/gunicorn.sock \\
    beii_v1.wsgi:application

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable gunicorn
    systemctl start gunicorn
}

# Function to setup Nginx
setup_nginx() {
    echo "Setting up Nginx..."
    
    # Install Nginx if not present
    if ! command -v nginx &> /dev/null; then
        apt-get update && apt-get install -y nginx
    fi
    
    # Create Nginx configuration
    cat > /etc/nginx/sites-available/beii_v1 << EOF
server {
    listen 80;
    server_name dr.yourdomain.com;

    location = /favicon.ico { access_log off; log_not_found off; }
    location /static/ {
        root $APP_DIR;
    }

    location /media/ {
        root $APP_DIR;
    }

    location / {
        include proxy_params;
        proxy_pass http://unix:$APP_DIR/gunicorn.sock;
    }
}
EOF

    # Enable site and restart Nginx
    ln -sf /etc/nginx/sites-available/beii_v1 /etc/nginx/sites-enabled/
    nginx -t
    systemctl restart nginx
}

# Function to setup SSL
setup_ssl() {
    echo "Setting up SSL..."
    
    # Install Certbot if not present
    if ! command -v certbot &> /dev/null; then
        apt-get update && apt-get install -y certbot python3-certbot-nginx
    fi
    
    # Obtain SSL certificate
    certbot --nginx -d dr.yourdomain.com --non-interactive --agree-tos --email admin@yourdomain.com
}

# Function to setup monitoring
setup_app_monitoring() {
    echo "Setting up application monitoring..."
    
    # Install monitoring tools
    apt-get update && apt-get install -y prometheus-node-exporter
    
    # Create health check script
    cat > /usr/local/bin/check_app_health.sh << EOF
#!/bin/bash

# Check if Gunicorn is running
if ! systemctl is-active --quiet gunicorn; then
    systemctl restart gunicorn
fi

# Check if Nginx is running
if ! systemctl is-active --quiet nginx; then
    systemctl restart nginx
fi

# Check application health endpoint
curl -s http://localhost/health/ > /dev/null
if [ \$? -ne 0 ]; then
    systemctl restart gunicorn
fi
EOF

    chmod +x /usr/local/bin/check_app_health.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/5 * * * * /usr/local/bin/check_app_health.sh") | crontab -
}

# Main execution
echo "Starting application DR setup..."

# Setup components
setup_virtualenv
setup_app_dir
setup_env
setup_gunicorn
setup_nginx
setup_ssl
setup_app_monitoring

echo "Application DR setup completed successfully!" 