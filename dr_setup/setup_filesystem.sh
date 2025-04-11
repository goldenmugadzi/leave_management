#!/bin/bash

# File System DR Setup Script
# This script configures file synchronization between primary and DR sites

# Configuration
PRIMARY_HOST="primary-host"
DR_HOST="dr-host"
SYNC_USER="sync_user"
SYNC_DIRS=(
    "/path/to/media"
    "/path/to/uploads"
    "/path/to/staticfiles"
)
BACKUP_DIR="/backup"
LOG_FILE="/var/log/dr_sync.log"

# Function to setup SSH keys
setup_ssh_keys() {
    echo "Setting up SSH keys for synchronization..."
    
    # Generate SSH key if it doesn't exist
    if [ ! -f ~/.ssh/id_rsa ]; then
        ssh-keygen -t rsa -N "" -f ~/.ssh/id_rsa
    fi
    
    # Copy public key to DR server
    ssh-copy-id -i ~/.ssh/id_rsa.pub "$SYNC_USER@$DR_HOST"
}

# Function to create backup directory
setup_backup_dir() {
    echo "Setting up backup directory..."
    mkdir -p "$BACKUP_DIR"
    chmod 700 "$BACKUP_DIR"
}

# Function to setup rsync script
setup_rsync_script() {
    echo "Setting up rsync synchronization script..."
    
    cat > /usr/local/bin/sync_dr.sh << EOF
#!/bin/bash

# Log function
log() {
    echo "\$(date '+%Y-%m-%d %H:%M:%S') - \$1" >> "$LOG_FILE"
}

# Sync function
sync_dir() {
    local src_dir="\$1"
    local dest_dir="\$2"
    
    log "Starting sync of \$src_dir to \$dest_dir"
    rsync -avz --delete --exclude='*.tmp' --exclude='*.lock' \
        "\$src_dir/" "$SYNC_USER@$DR_HOST:\$dest_dir/"
    
    if [ \$? -eq 0 ]; then
        log "Successfully synced \$src_dir"
    else
        log "Error syncing \$src_dir"
        exit 1
    fi
}

# Main sync process
for dir in "${SYNC_DIRS[@]}"; do
    sync_dir "\$dir" "\$dir"
done

log "Synchronization completed"
EOF

    chmod +x /usr/local/bin/sync_dr.sh
}

# Function to setup cron job
setup_cron() {
    echo "Setting up cron job for regular synchronization..."
    
    # Add cron job to run every hour
    (crontab -l 2>/dev/null; echo "0 * * * * /usr/local/bin/sync_dr.sh") | crontab -
}

# Function to setup monitoring
setup_monitoring() {
    echo "Setting up file system monitoring..."
    
    # Install inotify-tools if not present
    if ! command -v inotifywait &> /dev/null; then
        apt-get update && apt-get install -y inotify-tools
    fi
    
    # Create monitoring script
    cat > /usr/local/bin/monitor_changes.sh << EOF
#!/bin/bash

# Monitor directories for changes and trigger sync
for dir in "${SYNC_DIRS[@]}"; do
    inotifywait -m -r -e modify,create,delete "\$dir" |
    while read path action file; do
        /usr/local/bin/sync_dr.sh
    done &
done
EOF

    chmod +x /usr/local/bin/monitor_changes.sh
    
    # Start monitoring service
    cat > /etc/systemd/system/dr-monitor.service << EOF
[Unit]
Description=DR File System Monitor
After=network.target

[Service]
Type=simple
ExecStart=/usr/local/bin/monitor_changes.sh
Restart=always

[Install]
WantedBy=multi-user.target
EOF

    systemctl daemon-reload
    systemctl enable dr-monitor
    systemctl start dr-monitor
}

# Main execution
echo "Starting file system DR setup..."

# Setup components
setup_ssh_keys
setup_backup_dir
setup_rsync_script
setup_cron
setup_monitoring

echo "File system DR setup completed successfully!" 