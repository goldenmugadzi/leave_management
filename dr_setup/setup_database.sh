#!/bin/bash

# Database DR Setup Script
# This script configures MySQL replication between primary and DR sites

# Configuration
PRIMARY_DB_HOST="primary-db-host"
DR_DB_HOST="dr-db-host"
DB_USER="replication_user"
DB_PASSWORD="secure_password"
DB_NAME="your_database"

# Function to check if MySQL is running
check_mysql() {
    if ! mysqladmin ping -h "$1" -u root -p"$DB_PASSWORD" &>/dev/null; then
        echo "Error: MySQL is not running on $1"
        exit 1
    fi
}

# Function to configure primary server
configure_primary() {
    echo "Configuring primary MySQL server..."
    
    # Create replication user
    mysql -h "$PRIMARY_DB_HOST" -u root -p"$DB_PASSWORD" << EOF
    CREATE USER '$DB_USER'@'%' IDENTIFIED BY '$DB_PASSWORD';
    GRANT REPLICATION SLAVE ON *.* TO '$DB_USER'@'%';
    FLUSH PRIVILEGES;
EOF

    # Configure server ID and binary logging
    cat > /etc/mysql/conf.d/replication.cnf << EOF
[mysqld]
server-id = 1
log_bin = mysql-bin
binlog_format = ROW
binlog_do_db = $DB_NAME
EOF

    # Restart MySQL
    systemctl restart mysql
}

# Function to configure DR server
configure_dr() {
    echo "Configuring DR MySQL server..."
    
    # Configure server ID
    cat > /etc/mysql/conf.d/replication.cnf << EOF
[mysqld]
server-id = 2
log_bin = mysql-bin
binlog_format = ROW
binlog_do_db = $DB_NAME
EOF

    # Restart MySQL
    systemctl restart mysql

    # Set up replication
    mysql -h "$DR_DB_HOST" -u root -p"$DB_PASSWORD" << EOF
    STOP SLAVE;
    CHANGE MASTER TO
    MASTER_HOST='$PRIMARY_DB_HOST',
    MASTER_USER='$DB_USER',
    MASTER_PASSWORD='$DB_PASSWORD',
    MASTER_LOG_FILE='$(mysql -h "$PRIMARY_DB_HOST" -u root -p"$DB_PASSWORD" -e "SHOW MASTER STATUS" | awk 'NR==2 {print $1}')',
    MASTER_LOG_POS=$(mysql -h "$PRIMARY_DB_HOST" -u root -p"$DB_PASSWORD" -e "SHOW MASTER STATUS" | awk 'NR==2 {print $2}');
    START SLAVE;
EOF
}

# Main execution
echo "Starting database DR setup..."

# Check MySQL status on both servers
check_mysql "$PRIMARY_DB_HOST"
check_mysql "$DR_DB_HOST"

# Configure servers
configure_primary
configure_dr

# Verify replication
echo "Verifying replication status..."
mysql -h "$DR_DB_HOST" -u root -p"$DB_PASSWORD" -e "SHOW SLAVE STATUS\G"

echo "Database DR setup completed successfully!" 