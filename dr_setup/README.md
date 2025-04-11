# Disaster Recovery Setup

This directory contains scripts and configurations for setting up the Disaster Recovery (DR) site.

## Components

1. **Database Replication**
   - MySQL master-slave replication
   - Automated failover scripts

2. **File System Synchronization**
   - Media files
   - Uploads
   - Static files

3. **Application Deployment**
   - DR site deployment scripts
   - Environment configuration
   - Service management

4. **Monitoring and Alerting**
   - Health checks
   - Automated failover triggers
   - Alert notifications

## Setup Instructions

1. **Prerequisites**
   - Secondary server with matching specifications
   - Network connectivity between primary and DR sites
   - Sufficient storage capacity
   - DNS management access

2. **Database Setup**
   ```bash
   ./dr_setup/setup_database.sh
   ```

3. **File System Setup**
   ```bash
   ./dr_setup/setup_filesystem.sh
   ```

4. **Application Setup**
   ```bash
   ./dr_setup/setup_application.sh
   ```

5. **Monitoring Setup**
   ```bash
   ./dr_setup/setup_monitoring.sh
   ```

## Failover Process

1. Automatic detection of primary site failure
2. DNS failover to DR site
3. Database promotion to master
4. Application service start
5. Verification of services

## Recovery Process

1. Primary site restoration
2. Database synchronization
3. File system synchronization
4. Service verification
5. DNS failback (manual)

## Maintenance

- Regular testing of DR site
- Backup verification
- Performance monitoring
- Documentation updates 