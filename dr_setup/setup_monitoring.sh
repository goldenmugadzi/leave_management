#!/bin/bash

# Monitoring DR Setup Script
# This script configures monitoring and alerting for the DR site

# Configuration
PRIMARY_HOST="primary-host"
DR_HOST="dr-host"
ALERT_EMAIL="admin@yourdomain.com"
PROMETHEUS_PORT="9090"
GRAFANA_PORT="3000"
ALERTMANAGER_PORT="9093"

# Function to install monitoring stack
install_monitoring_stack() {
    echo "Installing monitoring stack..."
    
    # Install Docker if not present
    if ! command -v docker &> /dev/null; then
        curl -fsSL https://get.docker.com -o get-docker.sh
        sh get-docker.sh
    fi
    
    # Create Docker Compose file for monitoring stack
    cat > docker-compose.yml << EOF
version: '3'
services:
  prometheus:
    image: prom/prometheus:latest
    ports:
      - "$PROMETHEUS_PORT:9090"
    volumes:
      - ./prometheus.yml:/etc/prometheus/prometheus.yml
      - prometheus_data:/prometheus
    command:
      - '--config.file=/etc/prometheus/prometheus.yml'
      - '--storage.tsdb.path=/prometheus'
      - '--web.console.libraries=/usr/share/prometheus/console_libraries'
      - '--web.console.templates=/usr/share/prometheus/consoles'
    restart: unless-stopped

  alertmanager:
    image: prom/alertmanager:latest
    ports:
      - "$ALERTMANAGER_PORT:9093"
    volumes:
      - ./alertmanager.yml:/etc/alertmanager/alertmanager.yml
    command:
      - '--config.file=/etc/alertmanager/alertmanager.yml'
      - '--storage.path=/alertmanager'
    restart: unless-stopped

  grafana:
    image: grafana/grafana:latest
    ports:
      - "$GRAFANA_PORT:3000"
    volumes:
      - grafana_data:/var/lib/grafana
    environment:
      - GF_SECURITY_ADMIN_PASSWORD=admin
    restart: unless-stopped

  node-exporter:
    image: prom/node-exporter:latest
    ports:
      - "9100:9100"
    volumes:
      - /proc:/host/proc:ro
      - /sys:/host/sys:ro
      - /:/rootfs:ro
    command:
      - '--path.procfs=/host/proc'
      - '--path.sysfs=/host/sys'
      - '--collector.filesystem.mount-points-exclude=^/(sys|proc|dev|host|etc)($$|/)'
    restart: unless-stopped

volumes:
  prometheus_data:
  grafana_data:
EOF

    # Create Prometheus configuration
    cat > prometheus.yml << EOF
global:
  scrape_interval: 15s
  evaluation_interval: 15s

alerting:
  alertmanagers:
    - static_configs:
        - targets:
          - "alertmanager:9093"

rule_files:
  - "alert_rules.yml"

scrape_configs:
  - job_name: 'prometheus'
    static_configs:
      - targets: ['localhost:9090']

  - job_name: 'node-exporter'
    static_configs:
      - targets: ['node-exporter:9100']

  - job_name: 'application'
    static_configs:
      - targets: ['localhost:8000']
EOF

    # Create Alertmanager configuration
    cat > alertmanager.yml << EOF
global:
  resolve_timeout: 5m

route:
  group_by: ['alertname']
  group_wait: 10s
  group_interval: 10s
  repeat_interval: 1h
  receiver: 'email-notifications'

receivers:
- name: 'email-notifications'
  email_configs:
  - to: '$ALERT_EMAIL'
    from: 'alertmanager@yourdomain.com'
    smarthost: 'smtp.yourdomain.com:587'
    auth_username: 'alertmanager@yourdomain.com'
    auth_password: 'your-smtp-password'
EOF

    # Create alert rules
    cat > alert_rules.yml << EOF
groups:
- name: application
  rules:
  - alert: HighErrorRate
    expr: rate(http_requests_total{status=~"5.."}[5m]) > 0.1
    for: 5m
    labels:
      severity: critical
    annotations:
      summary: High error rate on {{ $labels.instance }}
      description: "Error rate is {{ $value }}"

  - alert: ServiceDown
    expr: up == 0
    for: 1m
    labels:
      severity: critical
    annotations:
      summary: Service {{ $labels.instance }} is down
      description: "{{ $labels.instance }} has been down for more than 1 minute."
EOF

    # Start monitoring stack
    docker-compose up -d
}

# Function to setup health checks
setup_health_checks() {
    echo "Setting up health checks..."
    
    # Create health check script
    cat > /usr/local/bin/check_dr_health.sh << EOF
#!/bin/bash

# Check primary site health
check_primary() {
    if ! curl -s "http://$PRIMARY_HOST/health/" > /dev/null; then
        echo "Primary site is down"
        return 1
    fi
    return 0
}

# Check DR site health
check_dr() {
    if ! curl -s "http://$DR_HOST/health/" > /dev/null; then
        echo "DR site is down"
        return 1
    fi
    return 0
}

# Check database replication
check_replication() {
    if ! mysql -h "$DR_DB_HOST" -u root -p"$DB_PASSWORD" -e "SHOW SLAVE STATUS\G" | grep -q "Slave_IO_Running: Yes"; then
        echo "Database replication is not running"
        return 1
    fi
    return 0
}

# Main health check
if ! check_primary; then
    if check_dr && check_replication; then
        # Trigger failover
        /usr/local/bin/trigger_failover.sh
    fi
fi
EOF

    chmod +x /usr/local/bin/check_dr_health.sh
    
    # Add to crontab
    (crontab -l 2>/dev/null; echo "*/1 * * * * /usr/local/bin/check_dr_health.sh") | crontab -
}

# Function to setup failover script
setup_failover() {
    echo "Setting up failover script..."
    
    cat > /usr/local/bin/trigger_failover.sh << EOF
#!/bin/bash

# Update DNS records
update_dns() {
    # Use your DNS provider's API to update records
    # Example using AWS Route 53:
    aws route53 change-resource-record-sets \\
        --hosted-zone-id YOUR_ZONE_ID \\
        --change-batch '{
            "Changes": [{
                "Action": "UPSERT",
                "ResourceRecordSet": {
                    "Name": "yourdomain.com",
                    "Type": "A",
                    "TTL": 300,
                    "ResourceRecords": [{"Value": "$DR_HOST_IP"}]
                }
            }]
        }'
}

# Promote DR database to master
promote_database() {
    mysql -h "$DR_DB_HOST" -u root -p"$DB_PASSWORD" << EOF
    STOP SLAVE;
    RESET MASTER;
    SET GLOBAL read_only = OFF;
EOF
}

# Send notification
send_notification() {
    echo "Failover triggered at \$(date)" | mail -s "DR Failover Alert" "$ALERT_EMAIL"
}

# Main failover process
update_dns
promote_database
send_notification

echo "Failover completed successfully"
EOF

    chmod +x /usr/local/bin/trigger_failover.sh
}

# Main execution
echo "Starting monitoring DR setup..."

# Setup components
install_monitoring_stack
setup_health_checks
setup_failover

echo "Monitoring DR setup completed successfully!" 