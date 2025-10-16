# Substation Inspections Module - User Guide

## Table of Contents
1. [Overview](#overview)
2. [User Roles and Permissions](#user-roles-and-permissions)
3. [Module Features](#module-features)
4. [Step-by-Step Workflow](#step-by-step-workflow)
5. [Detailed User Guide](#detailed-user-guide)
6. [Testing Scenarios](#testing-scenarios)
7. [Troubleshooting](#troubleshooting)

## Overview

The Substation Inspections Module is a comprehensive system for managing electrical substation inspections, scheduling, reporting, and monitoring. It provides automated scheduling, real-time monitoring, bulk assignment capabilities, and detailed inspection reporting with checklist management.

### Key Features
- **Substation Management**: Create and manage substation information
- **Automated Scheduling**: Set up recurring inspection schedules
- **Inspection Reporting**: Conduct detailed inspections with checklists
- **Bulk Operations**: Assign multiple inspections efficiently
- **Real-time Monitoring**: Track inspection status and progress
- **Notification System**: Automated reminders and escalations
- **Compliance Tracking**: Monitor compliance status and issues

## User Roles and Permissions

The Substation Inspections Module uses the BEII system's custom role management with the following roles:

### 1. System Administrator
**Role Code**: `system_admin`
**Full Access to All Features**
- Create, edit, and delete substations
- Manage all inspection schedules
- Create and edit checklist items
- View all inspection reports
- Perform bulk assignments
- Access monitoring dashboard
- Send notifications
- Generate monthly inspections
- Reassign inspections
- View inspector workload
- Manage user roles and permissions

### 2. Inspection Supervisor
**Role Code**: `inspection_supervisor`
**Management and Oversight**
- View all substations and inspection reports
- Create and edit inspection schedules
- Perform bulk assignments
- Access monitoring dashboard
- Send notifications
- Reassign inspections
- View inspector workload
- Approve inspection reports
- Generate monthly inspections

### 3. Field Inspector
**Role Code**: `field_inspector`
**Inspection Execution**
- View assigned substations
- Create inspection reports
- Edit own inspection reports (if not completed)
- View inspection schedules
- Access basic dashboard
- Update inspection status

### 4. Read-Only User
**Role Code**: `readonly_user`
**Viewing and Reporting**
- View substations and inspection reports
- Access basic dashboard
- View inspection schedules
- Generate reports (if reporting features are enabled)

### Role Assignment
Roles are assigned through the BEII user management system:
1. Navigate to User Management
2. Select the user
3. Assign the appropriate substation inspection role
4. Save changes

### Role Verification
To check your current role:
1. Look at the user information in the dashboard
2. Your role will be displayed as "System Administrator", "Inspection Supervisor", "Field Inspector", or "Read-Only User"

## Module Features

### Core Components
1. **Substation Management**
   - Substation registration and configuration
   - Equipment inventory tracking
   - Location and regional management

2. **Inspection Scheduling**
   - Automated monthly/quarterly/annual schedules
   - Inspector assignment
   - Reminder and escalation settings

3. **Inspection Reporting**
   - Detailed inspection forms
   - Checklist-based inspections
   - Photo and measurement capture
   - Defect tracking and corrective actions

4. **Monitoring and Analytics**
   - Real-time dashboard
   - Inspector workload tracking
   - Compliance monitoring
   - Overdue inspection alerts

5. **Bulk Operations**
   - Mass assignment of inspections
   - Auto-assignment based on schedules
   - Bulk status updates

## Step-by-Step Workflow

### Phase 1: Initial Setup
1. **Create Substations**
   - Register all substations in the system
   - Configure equipment inventory
   - Set up regional classifications

2. **Create Checklist Items**
   - Define inspection criteria
   - Set up categories and severity levels
   - Configure reference standards

3. **Set Up Inspection Schedules**
   - Create recurring schedules for each substation
   - Assign inspectors to schedules
   - Configure notification settings

### Phase 2: Monthly Operations
1. **Generate Monthly Inspections**
   - System automatically creates inspection reports
   - Assigns inspectors based on schedules

2. **Conduct Inspections**
   - Inspectors complete assigned inspections
   - Fill out detailed reports with checklists
   - Document issues and recommendations

3. **Review and Approve**
   - Supervisors review completed reports
   - Approve or request modifications
   - Track compliance status

### Phase 3: Monitoring and Maintenance
1. **Monitor Progress**
   - Track inspection completion rates
   - Monitor overdue inspections
   - Review inspector workload

2. **Handle Issues**
   - Address overdue inspections
   - Reassign inspections when needed
   - Escalate critical issues

3. **Generate Reports**
   - Create compliance reports
   - Analyze inspection trends
   - Export data for external systems

## Detailed User Guide

### 1. Dashboard Overview

The main dashboard provides a comprehensive view of the inspection system:

**Statistics Cards:**
- Total Substations: Number of active substations
- Pending Inspections: Scheduled but not started
- Completed This Month: Successfully completed inspections
- Overdue Inspections: Past due inspections

**Quick Actions:**
- Monitoring Dashboard: Advanced analytics
- Add New Substation: Create new substation
- Create Inspection Report: Manual report creation
- Schedule Inspection: Set up new schedule
- Bulk Assignment: Mass assign inspections

**Recent Activity:**
- Latest inspection reports
- Upcoming inspections
- System notifications

### 2. Substation Management

#### Creating a New Substation
1. Navigate to **Substations** → **Add New Substation**
2. Fill in required information:
   - **Substation Code**: Unique identifier (auto-generated if empty)
   - **Name**: Descriptive name
   - **Type**: Primary, Secondary, Distribution, or Transmission
   - **Voltage Level**: 11kV, 33kV, 132kV, or 400kV
   - **Location**: Physical address
   - **District**: Administrative district
   - **Region**: Geographic region
   - **Equipment Counts**: Transformers, Circuit Breakers, Switchgear
   - **Status**: Active/Inactive
3. Click **Save**

#### Managing Existing Substations
- **View Details**: Click on substation name to see full details
- **Edit**: Click **Edit** to modify information
- **Search**: Use search bar to find specific substations
- **Filter**: Filter by type, status, or region

### 3. Inspection Scheduling

#### Creating Inspection Schedules
1. Navigate to **Schedules** → **Create New Schedule**
2. Configure schedule:
   - **Substation**: Select target substation
   - **Frequency**: Monthly, Quarterly, or Annually
   - **Day of Month**: Which day to conduct inspection
   - **Assigned Inspector**: Who will perform inspection
   - **Reminder Days**: How many days before to send reminder
   - **Escalation Days**: How many days after due date to escalate
   - **Status**: Active/Inactive
3. Click **Save**

#### Managing Schedules
- **View All**: See all active schedules
- **Edit**: Modify existing schedules
- **Deactivate**: Stop recurring inspections

### 4. Inspection Reporting

#### Creating Inspection Reports
1. Navigate to **Reports** → **Create New Report**
2. Fill in basic information:
   - **Substation**: Select substation to inspect
   - **Inspection Date**: When inspection was conducted
   - **Weather Conditions**: Environmental conditions
   - **Temperature**: Ambient temperature
   - **Humidity**: Humidity percentage
3. Complete detailed assessment:
   - **Overall Condition**: General assessment
   - **Critical Issues**: Any major problems found
   - **Recommendations**: Suggested improvements
4. Click **Save**

#### Conducting Checklist Inspections
1. Open the inspection report
2. Navigate to **Checklist Items** section
3. For each checklist item:
   - Select response: Pass, Fail, Not Applicable, or Pending
   - Add observations and notes
   - Upload photos if needed
   - Record measurements
   - Mark defects if found
   - Specify corrective actions if required
4. Update inspection status to "In Progress" or "Completed"

### 5. Bulk Operations

#### Bulk Assignment
1. Navigate to **Bulk Assignment**
2. Select inspections to assign:
   - Check boxes for multiple inspections
   - Use filters to narrow selection
3. Choose inspector:
   - Select from dropdown list
   - Add assignment notes
4. Click **Assign Inspections**

#### Auto-Assignment
1. Navigate to **Auto-Assign**
2. Review unassigned inspections
3. Click **Auto-Assign** to automatically assign based on schedules
4. System will assign inspections to scheduled inspectors

### 6. Monitoring and Analytics

#### Monitoring Dashboard
- **Real-time Statistics**: Live updates of inspection status
- **Inspector Workload**: Individual inspector assignments and progress
- **Compliance Tracking**: Overall compliance status
- **Trend Analysis**: Historical data and patterns

#### Inspector Workload View
- **Individual Workloads**: See each inspector's assignments
- **Pending Inspections**: What's scheduled for each inspector
- **Completion Rates**: Performance metrics
- **Overdue Items**: Items requiring attention

### 7. Notification System

#### Sending Notifications
1. Navigate to **Notifications**
2. Choose notification type:
   - **Reminders**: For upcoming inspections
   - **Overdue**: For past due inspections
   - **Both**: Send all pending notifications
3. Click **Send Notifications**

#### Automated Notifications
- **Reminder Emails**: Sent 3 days before inspection date
- **Overdue Alerts**: Sent when inspections are past due
- **Escalation Notices**: Sent to supervisors for critical delays

## Testing Scenarios

### Scenario 1: Complete Inspection Workflow
**Objective**: Test the full inspection process from setup to completion

**Steps**:
1. **Setup Phase**:
   - Create 3 test substations (different types and voltage levels)
   - Create 10 checklist items across different categories
   - Set up monthly inspection schedules for all substations
   - Assign different inspectors to each schedule

2. **Execution Phase**:
   - Generate monthly inspections
   - Conduct inspections with different outcomes:
     - One with all items passing
     - One with some failures and defects
     - One with critical issues requiring attention
   - Complete all inspection reports

3. **Verification**:
   - Check dashboard statistics update correctly
   - Verify compliance status calculations
   - Confirm notification system works
   - Test bulk operations

### Scenario 2: Bulk Assignment and Management
**Objective**: Test bulk operations and inspector management

**Steps**:
1. Create 20 inspection reports without assigned inspectors
2. Use bulk assignment to assign 10 inspections to Inspector A
3. Use auto-assignment for remaining inspections
4. Reassign 5 inspections from Inspector A to Inspector B
5. Verify workload distribution is correct

### Scenario 3: Overdue and Escalation Testing
**Objective**: Test overdue handling and escalation procedures

**Steps**:
1. Create inspections with past due dates
2. Run overdue notification process
3. Verify status updates to "overdue"
4. Test escalation notifications
5. Reassign overdue inspections
6. Update to completed status

### Scenario 4: Different User Roles
**Objective**: Test role-based access and permissions

**Steps**:
1. **As System Administrator**:
   - Create substations and schedules
   - Access all features
   - Perform bulk operations

2. **As Inspection Supervisor**:
   - View all data
   - Assign inspections
   - Approve reports
   - Access monitoring features

3. **As Field Inspector**:
   - View assigned inspections only
   - Create and edit own reports
   - Update inspection status

4. **As Read-Only User**:
   - View data only
   - Cannot edit or create

## Test Data Setup

### Sample Substations
```
Substation Code: SUB-001
Name: Main Distribution Station
Type: Primary Substation
Voltage Level: 132kV
Location: Industrial Area, District A
District: District A
Region: Northern Region
Transformers: 3
Circuit Breakers: 12
Switchgear: 8
```

### Sample Checklist Items
```
Item Code: CHK-SAF-001
Title: Safety Equipment Check
Category: Safety
Severity: High
Description: Verify all safety equipment is present and functional
Reference Standard: IEEE 141
Frequency: Monthly
```

### Sample Inspection Schedule
```
Substation: Main Distribution Station
Frequency: Monthly
Day of Month: 1
Assigned Inspector: John Smith
Reminder Days: 3
Escalation Days: 2
Status: Active
```

## Troubleshooting

### Common Issues

#### 1. Inspections Not Generating
**Problem**: Monthly inspections not being created automatically
**Solution**: 
- Check if schedules are active
- Verify substations are active
- Run manual generation from monitoring dashboard

#### 2. Notifications Not Sending
**Problem**: Email notifications not being delivered
**Solution**:
- Check email configuration in Django settings
- Verify inspector email addresses are correct
- Check SMTP server settings

#### 3. Bulk Assignment Failing
**Problem**: Bulk assignment not working properly
**Solution**:
- Ensure selected inspections are in "scheduled" status
- Verify inspector is active
- Check for database constraints

#### 4. Dashboard Not Updating
**Problem**: Real-time updates not working
**Solution**:
- Check HTMX configuration
- Verify JavaScript is enabled
- Clear browser cache

### Performance Optimization

#### 1. Large Dataset Handling
- Use pagination for large lists
- Implement search and filtering
- Consider database indexing

#### 2. Real-time Updates
- Use HTMX for partial page updates
- Implement caching for frequently accessed data
- Optimize database queries

#### 3. File Upload Management
- Implement file size limits
- Use cloud storage for photos
- Compress images before storage

## Best Practices

### 1. Data Management
- Regular backup of inspection data
- Archive completed inspections
- Maintain data integrity

### 2. User Training
- Provide role-specific training
- Create user documentation
- Regular system updates

### 3. System Maintenance
- Monitor system performance
- Regular security updates
- Database optimization

### 4. Compliance
- Regular audit of inspection data
- Maintain inspection standards
- Document all procedures

## Support and Maintenance

### Getting Help
- Contact system administrator for technical issues
- Refer to this user guide for common procedures
- Check system logs for error details

### Regular Maintenance
- Monthly system health checks
- Quarterly data archiving
- Annual security reviews

### Updates and Enhancements
- Regular feature updates
- Performance improvements
- Security patches

---

*This user guide is maintained by the BEII development team. For questions or suggestions, please contact the system administrator.*
