# Change Requests User Guide

## Table of Contents

1. [Introduction](#introduction)
2. [Getting Started](#getting-started)
3. [Creating Change Requests](#creating-change-requests)
4. [Managing Change Requests](#managing-change-requests)
5. [Approval Workflow](#approval-workflow)
6. [Bulk Operations](#bulk-operations)
7. [Reports and Analytics](#reports-and-analytics)
8. [Troubleshooting](#troubleshooting)
9. [Best Practices](#best-practices)
10. [Frequently Asked Questions](#frequently-asked-questions)

## Introduction

The Change Requests system allows users to request changes to user profiles, including creating new profiles, modifying existing profiles, and deactivating profiles. All changes go through an approval workflow to ensure proper authorization and control.

### Key Features

- **New Profile Creation**: Request creation of new user accounts
- **Profile Modifications**: Request changes to existing user profiles
- **Profile Deactivation**: Request deactivation of user accounts
- **Approval Workflow**: Two-level approval process (Section Head → IT Section Head)
- **Soft Delete**: Ability to delete and restore change requests
- **Bulk Operations**: Manage multiple change requests at once
- **Role Delegation**: Temporarily delegate roles to other users with approval workflow
- **Audit Trail**: Complete history of all changes and approvals
- **Security**: CSRF protection, input validation, and permission controls

## Getting Started

### Accessing the System

1. **Login**: Access the system through your organization's portal
2. **Navigation**: Navigate to the Change Requests section
3. **Dashboard**: You'll see the main dashboard with your change requests

### User Roles and Permissions

- **Regular Users**: Can create and manage their own change requests
- **Section Heads**: Can approve change requests for their cost centers
- **IT Section Heads**: Can approve and apply changes
- **Administrators**: Can restore deleted change requests

### Dashboard Overview

The main dashboard displays:
- **Change Requests List**: All your change requests with status
- **Filter Options**: Filter by type, status, date range, etc.
- **Search**: Search through change requests
- **Actions**: Create, edit, delete, and approve change requests

## Creating Change Requests

### 1. New Profile Request

To create a new user profile:

1. **Navigate** to "Create Change Request" → "New Profile"
2. **Fill Required Fields**:
   - **Change Reason**: Why you need this new profile (max 500 characters)
   - **Change Description**: Detailed description of the request (max 1000 characters)
   - **Username**: Desired username (max 15 characters, must be unique)
   - **First Name**: User's first name (max 100 characters)
   - **Last Name**: User's last name (max 100 characters)
   - **Email**: User's email address (max 100 characters)

3. **Fill Optional Fields**:
   - **Designation**: User's job title/position
   - **Cost Center**: User's cost center
   - **Application**: Which application this is for
   - **Roles to Action**: What roles should be assigned

4. **Submit**: Click "Submit" to create the change request

**Validation Rules**:
- All required fields must be filled
- Username must be unique across the system
- Email must be in valid format
- Field lengths must not exceed limits

### 2. Profile Modification Request

To modify an existing user profile:

1. **Navigate** to "Create Change Request" → "Profile Modification"
2. **Select User**: Choose the user whose profile needs modification
3. **Fill Required Fields**:
   - **Change Reason**: Why the modification is needed
   - **Change Description**: What changes are being requested
   - **Application**: Which application this affects

4. **Specify Changes**:
   - **Roles to Action**: What roles should be added/removed
   - **Roles Actions**: Detailed description of role changes

5. **Submit**: Click "Submit" to create the change request

### 3. Profile Deactivation Request

To deactivate a user profile:

1. **Navigate** to "Create Change Request" → "Profile Deactivation"
2. **Select User**: Choose the user to be deactivated
3. **Fill Required Fields**:
   - **Change Reason**: Why the deactivation is needed
   - **Change Description**: Details about the deactivation
   - **Application**: Which application this affects

4. **Submit**: Click "Submit" to create the change request

## Managing Change Requests

### Viewing Change Requests

1. **Dashboard**: View all your change requests on the main dashboard
2. **Filtering**: Use filters to narrow down the list:
   - **Type**: New Profile, Profile Modification, Profile Deactivation
   - **Status**: Pending SH, Pending IT, Complete, Rejected
   - **Date Range**: Filter by creation date
   - **Cost Center**: Filter by cost center
   - **Application**: Filter by application

3. **Search**: Use the search box to find specific change requests
4. **Sorting**: Click column headers to sort by different criteria

### Editing Change Requests

**Note**: You can only edit change requests that haven't been approved yet.

1. **Find the Request**: Locate the change request you want to edit
2. **Click Edit**: Click the "Edit" button for the request
3. **Make Changes**: Modify the fields you need to change
4. **Save**: Click "Save" to update the request

**Restrictions**:
- Cannot edit approved change requests
- Cannot edit change requests created by other users (unless you're a section head)
- Cannot edit deleted change requests

### Deleting Change Requests

**Soft Delete**: Change requests are never permanently deleted, only marked as deleted.

1. **Find the Request**: Locate the change request you want to delete
2. **Click Delete**: Click the "Delete" button for the request
3. **Confirm**: Confirm the deletion

**Restrictions**:
- Cannot delete approved change requests
- Cannot delete change requests created by other users (unless you're a section head)
- Deleted requests can be restored by administrators

### Restoring Deleted Change Requests

**Note**: Only administrators or the user who deleted the request can restore it.

1. **Find Deleted Request**: Locate the deleted change request
2. **Click Restore**: Click the "Restore" button
3. **Confirm**: Confirm the restoration

## Approval Workflow

### Understanding the Workflow

The approval process has two levels:

1. **Section Head Approval**: First level of approval
2. **IT Section Head Approval**: Second level of approval
3. **Application**: IT section head applies the changes

### Status Meanings

- **Pending SH**: Waiting for Section Head approval
- **Pending IT**: Approved by Section Head, waiting for IT approval
- **Complete**: Fully approved and applied
- **Rejected**: Rejected at any level

### Approving Change Requests

**For Section Heads**:

1. **Review Request**: Click on the change request to review details
2. **Approve or Reject**: 
   - Click "Approve" to approve the request
   - Click "Reject" to reject with a reason
3. **Add Comments**: Provide approval/rejection comments
4. **Submit**: Submit your decision

**For IT Section Heads**:

1. **Review Request**: Review the change request and Section Head approval
2. **Approve or Reject**: Make your decision
3. **Apply Changes**: If approving, click "Apply" to implement the changes
4. **Add Comments**: Document your decision

### Rejecting Change Requests

1. **Click Reject**: Click the "Reject" button
2. **Provide Reason**: Enter a detailed reason for rejection
3. **Submit**: Submit the rejection

**Note**: Rejected requests cannot be edited and must be recreated if changes are needed.

## Bulk Operations

### Bulk Delete

To delete multiple change requests at once:

1. **Select Requests**: Check the boxes next to the requests you want to delete
2. **Click Bulk Delete**: Click the "Bulk Delete" button
3. **Confirm**: Confirm the bulk deletion

**Restrictions**:
- Only requests you have permission to delete will be deleted
- Approved requests will be skipped
- You'll see a summary of how many requests were deleted

### Bulk Operations Best Practices

- **Review Selection**: Double-check your selection before performing bulk operations
- **Check Permissions**: Ensure you have permission for all selected requests
- **Consider Impact**: Bulk operations affect multiple requests at once

## Role Delegation

### Understanding Role Delegation

Role delegation allows you to temporarily transfer your roles and permissions to another user for a specific time period. This is particularly useful when:

- You're going on leave or vacation
- You need someone to handle your responsibilities temporarily
- You're attending training or meetings
- You need to redistribute workload

### Creating a Role Delegation

1. **Navigate** to "Role Delegation" → "Create Delegation"
2. **Select Delegatee**: Choose the user who will receive your roles
3. **Choose Roles**: Select which roles you want to delegate
4. **Set Time Period**: 
   - **Start Date**: When the delegation becomes active
   - **End Date**: When the delegation expires (maximum 90 days)
5. **Provide Reason**: Explain why you're delegating your roles
6. **Submit**: Click "Submit" to create the delegation request

**Validation Rules**:
- You can only delegate to users in the same region
- You can only delegate roles that you currently have
- Start date cannot be in the past
- End date must be after start date
- Delegation period cannot exceed 90 days

### Delegation Workflow

1. **Create Request**: You create a delegation request
2. **Pending Approval**: The request waits for approval
3. **Approval Process**: An administrator or section head reviews and approves/rejects
4. **Activation**: If approved, the delegation becomes active at the start date
5. **Active Period**: The delegatee has your roles during the active period
6. **Expiry**: The delegation automatically expires at the end date
7. **Restoration**: You regain full access to your roles

### Managing Delegations

#### Viewing Your Delegations

1. **Dashboard**: View delegation statistics and recent activity
2. **List View**: See all your delegations with filtering options
3. **Calendar View**: Visual timeline of all delegations
4. **Notifications**: Check for delegation-related notifications

#### Cancelling a Delegation

1. **Find the Delegation**: Locate the delegation you want to cancel
2. **Click Cancel**: Click the "Cancel" button
3. **Provide Reason**: Enter a reason for cancellation (optional)
4. **Confirm**: Confirm the cancellation

**Note**: You can cancel delegations that are pending, approved, or active.

### Approving Delegations

**For Administrators and Section Heads**:

1. **Review Request**: Click on the delegation request to review details
2. **Check Information**: Verify the delegator, delegatee, roles, and time period
3. **Approve or Reject**: 
   - Click "Approve" to approve the delegation
   - Click "Reject" to reject with a reason
4. **Add Comments**: Provide approval/rejection comments
5. **Submit**: Submit your decision

### Delegation Notifications

The system sends notifications for:

- **Delegation Created**: When a new delegation request is created
- **Delegation Approved**: When a delegation is approved
- **Delegation Rejected**: When a delegation is rejected
- **Delegation Activated**: When a delegation becomes active
- **Delegation Expired**: When a delegation expires
- **Delegation Cancelled**: When a delegation is cancelled
- **Reminder Notifications**: 24 hours before expiry

### Best Practices for Role Delegation

1. **Plan Ahead**: Create delegations well in advance of your absence
2. **Choose Appropriate Delegatees**: Select users who are capable and available
3. **Provide Clear Reasons**: Explain why the delegation is necessary
4. **Set Appropriate Time Periods**: Don't delegate for longer than necessary
5. **Monitor Active Delegations**: Check on active delegations regularly
6. **Cancel When No Longer Needed**: Cancel delegations if circumstances change
7. **Communicate**: Inform relevant parties about the delegation

## Reports and Analytics

### Accessing Reports

1. **Navigate** to "Change Request Reports"
2. **Select Report Type**: Choose the type of report you need
3. **Apply Filters**: Set date ranges and other filters
4. **Generate Report**: Click "Generate Report"

### Available Reports

- **Change Request Summary**: Overview of all change requests
- **Approval Status Report**: Status of approvals by user/role
- **Performance Metrics**: Processing times and efficiency metrics
- **User Activity Report**: Activity by user and role

### Exporting Data

1. **Apply Filters**: Set your desired filters
2. **Click Export**: Click the "Export" button
3. **Choose Format**: Select CSV or Excel format
4. **Download**: Download the exported file

## Troubleshooting

### Common Issues

#### "Change request not found"
- **Cause**: The change request may have been deleted or doesn't exist
- **Solution**: Check if the request was soft-deleted and restore it if needed

#### "Insufficient permissions"
- **Cause**: You don't have permission to perform this action
- **Solution**: Contact your administrator or section head for permission

#### "Cannot delete approved change request"
- **Cause**: Approved requests cannot be deleted to maintain audit trail
- **Solution**: Create a new change request to modify or deactivate the user

#### "Username already exists"
- **Cause**: The username is already taken by another user
- **Solution**: Choose a different username

#### "Validation error"
- **Cause**: Required fields are missing or invalid
- **Solution**: Check all required fields and ensure they meet validation rules

### Error Messages

The system provides clear error messages for common issues:

- **Red Messages**: Critical errors that prevent operation
- **Yellow Messages**: Warnings about potential issues
- **Green Messages**: Success confirmations

### Getting Help

If you encounter issues not covered in this guide:

1. **Check Error Messages**: Read the error message carefully
2. **Contact Support**: Reach out to your IT support team
3. **Document Issue**: Note the steps that led to the error
4. **Provide Details**: Include error messages and screenshots

## Best Practices

### Creating Change Requests

1. **Be Specific**: Provide detailed reasons and descriptions
2. **Use Clear Language**: Write in clear, professional language
3. **Include Context**: Explain why the change is needed
4. **Check Details**: Verify all information before submitting
5. **Follow Naming Conventions**: Use consistent username formats

### Managing Requests

1. **Regular Review**: Check your requests regularly for updates
2. **Respond Promptly**: Respond to approval requests quickly
3. **Keep Records**: Maintain your own records of important requests
4. **Follow Up**: Follow up on pending requests if needed

### Approval Process

1. **Review Thoroughly**: Carefully review all details before approving
2. **Document Decisions**: Provide clear approval/rejection comments
3. **Consider Impact**: Think about the impact of the changes
4. **Verify Permissions**: Ensure the requester has proper authority

### Security

1. **Protect Credentials**: Never share your login credentials
2. **Logout Properly**: Always logout when finished
3. **Report Issues**: Report any security concerns immediately
4. **Follow Policies**: Adhere to your organization's security policies

## Frequently Asked Questions

### Q: How long does the approval process take?
**A**: The approval process typically takes 1-3 business days, depending on the workload of approvers and the complexity of the request.

### Q: Can I edit a change request after it's been approved?
**A**: No, approved change requests cannot be edited. You would need to create a new change request for any modifications.

### Q: What happens if I delete a change request by mistake?
**A**: Deleted change requests can be restored by administrators or the user who deleted them. Contact your administrator if you need help restoring a request.

### Q: Can I see who approved my change request?
**A**: Yes, the approval history is visible in the change request details, showing who approved it and when.

### Q: What if I need to change a user's role after their profile is created?
**A**: You would need to create a new "Profile Modification" change request to change their roles.

### Q: Can I create a change request for someone else?
**A**: Yes, you can create change requests for other users, but you should have proper authorization to do so.

### Q: What's the difference between "Pending SH" and "Pending IT"?
**A**: "Pending SH" means waiting for Section Head approval, while "Pending IT" means approved by Section Head and waiting for IT Section Head approval.

### Q: Can I export my change requests?
**A**: Yes, you can export change request data using the export functionality in the reports section.

### Q: What if I forget my password?
**A**: Use your organization's standard password reset process. The change requests system uses your organization's authentication system.

### Q: Can I see all change requests in the system?
**A**: You can only see change requests that you created or that you have permission to view based on your role and cost center.

### Q: What is role delegation?
**A**: Role delegation allows you to temporarily delegate your roles to another user for a specific time period. This is useful when you're going on leave or need someone to handle your responsibilities temporarily.

### Q: How do I delegate my roles to someone else?
**A**: Go to the Role Delegation section, click "Create Delegation", select the user, choose the roles to delegate, set the time period, and provide a reason. The delegation will need approval before it becomes active.

### Q: Who can approve role delegations?
**A**: Administrators and section heads can approve role delegations. The system will notify them when a new delegation request is created.

### Q: How long can I delegate my roles for?
**A**: Role delegations can be set for any period up to 90 days. The system will automatically expire the delegation at the end date.

### Q: Can I cancel a delegation after it's been approved?
**A**: Yes, you can cancel a delegation at any time if you're the delegator or if you have approval permissions. The system will notify all parties involved.

### Q: What happens when a delegation expires?
**A**: When a delegation expires, the delegatee automatically loses the delegated roles, and the delegator regains full access to their roles. The system sends notifications to both parties.

### Q: Can I see who has delegated roles to me?
**A**: Yes, you can view all delegations where you are the delegatee in the delegation dashboard and list views.

### Q: How do I know if I have delegated roles active?
**A**: The system will show your active delegated roles in your user profile and in the delegation dashboard. You'll also receive notifications when delegations become active or expire.

### Q: What happens if a change request is rejected?
**A**: Rejected change requests cannot be edited. You would need to create a new change request with the necessary corrections.

### Q: Can I track the history of a change request?
**A**: Yes, the system maintains a complete audit trail of all changes, approvals, and modifications to change requests.

### Q: What if I need to deactivate a user immediately?
**A**: For urgent deactivations, contact your IT support team directly. The change request system is for planned changes.

### Q: Can I create multiple change requests at once?
**A**: You need to create each change request individually, but you can manage multiple requests using the bulk operations features.

### Q: What information do I need to create a new profile request?
**A**: You need the user's basic information (name, email, username) and details about their role and access requirements.

### Q: How do I know if my change request was successful?
**A**: You'll receive success messages when operations complete, and you can check the status of your requests on the dashboard.

---

## Support and Contact

For additional support or questions not covered in this guide:

- **IT Support**: Contact your organization's IT support team
- **System Administrator**: Reach out to your system administrator
- **Documentation**: Refer to the API documentation for technical details
- **Training**: Request additional training if needed

---

*This user guide is updated regularly. Please check for the latest version to ensure you have the most current information.*
