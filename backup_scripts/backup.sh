#!/bin/bash

# Backup configuration
BACKUP_ROOT="/var/backups/beii"
DB_NAME="beii_db"
DB_USER="root"
DB_PASSWORD=""
DB_HOST="localhost"
RETENTION_DAYS=7
PROJECT_ROOT="/c/Users/kwara/Music/Dev/zetdc/beii_v1"  # Update this to your actual project path

# Create timestamp for backup folder
TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_PATH="${BACKUP_ROOT}/${TIMESTAMP}"
LOG_FILE="${BACKUP_ROOT}/backup.log"

# Function to log messages
log_message() {
    echo "$(date '+%Y-%m-%d %H:%M:%S'): $1" | tee -a "$LOG_FILE"
}

# Create backup directories
mkdir -p "${BACKUP_PATH}/database"
mkdir -p "${BACKUP_PATH}/files"

# Database backup function
backup_database() {
    log_message "Starting database backup..."
    
    if mysqldump --single-transaction \
        --routines \
        --triggers \
        --events \
        --set-gtid-purged=OFF \
        -h "$DB_HOST" \
        -u "$DB_USER" \
        -p"$DB_PASSWORD" \
        "$DB_NAME" > "${BACKUP_PATH}/database/database_backup.sql"; then
        
        # Compress the SQL file
        cd "${BACKUP_PATH}/database" || exit
        tar czf database_backup.tar.gz database_backup.sql
        rm database_backup.sql
        
        log_message "Database backup completed successfully"
        return 0
    else
        log_message "Database backup failed"
        return 1
    fi
}

# File system backup function
backup_files() {
    log_message "Starting file system backup..."
    
    # Create exclude file
    EXCLUDE_FILE="/tmp/backup_exclude.txt"
    cat > "$EXCLUDE_FILE" << EOF
*/node_modules/*
*/staticfiles/*
*/.git/*
*/backup_scripts/*
*/media/*
*/uploads/*
EOF

    # Backup files
    if tar --exclude-from="$EXCLUDE_FILE" \
        -czf "${BACKUP_PATH}/files/files_backup.tar.gz" \
        -C "$(dirname "$PROJECT_ROOT")" "$(basename "$PROJECT_ROOT")"; then
        
        log_message "File system backup completed successfully"
        rm "$EXCLUDE_FILE"
        return 0
    else
        log_message "File system backup failed"
        rm "$EXCLUDE_FILE"
        return 1
    fi
}

# Media files backup function
backup_media() {
    log_message "Starting media files backup..."
    
    if tar -czf "${BACKUP_PATH}/files/media_backup.tar.gz" \
        -C "$PROJECT_ROOT" media uploads; then
        
        log_message "Media files backup completed successfully"
        return 0
    else
        log_message "Media files backup failed"
        return 1
    fi
}

# Cleanup old backups
cleanup_old_backups() {
    log_message "Cleaning up old backups..."
    find "$BACKUP_ROOT" -type d -mtime +"$RETENTION_DAYS" -exec rm -rf {} \;
}

# Main backup process
main() {
    log_message "Starting backup process"
    
    # Check if backup root exists
    if [ ! -d "$BACKUP_ROOT" ]; then
        mkdir -p "$BACKUP_ROOT"
    fi
    
    # Perform database backup
    if ! backup_database; then
        log_message "Database backup failed, stopping backup process"
        exit 1
    fi
    
    # Perform file system backup
    if ! backup_files; then
        log_message "File system backup failed, stopping backup process"
        exit 1
    fi
    
    # Perform media files backup
    if ! backup_media; then
        log_message "Media files backup failed, stopping backup process"
        exit 1
    fi
    
    # Cleanup old backups
    cleanup_old_backups
    
    log_message "Backup process completed successfully"
    
    # Calculate backup size
    BACKUP_SIZE=$(du -sh "$BACKUP_PATH" | cut -f1)
    log_message "Backup size: $BACKUP_SIZE"
}

# Run main backup process
main 