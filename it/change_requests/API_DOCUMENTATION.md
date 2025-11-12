# Change Requests API Documentation

## Overview

The Change Requests API provides comprehensive functionality for managing user profile changes, approvals, and administrative operations. This document describes all available endpoints, request/response formats, and usage examples.

## Table of Contents

1. [Authentication](#authentication)
2. [Base URL](#base-url)
3. [Error Handling](#error-handling)
4. [Endpoints](#endpoints)
   - [Change Request Management](#change-request-management)
   - [Profile Operations](#profile-operations)
   - [Approval Workflow](#approval-workflow)
   - [Bulk Operations](#bulk-operations)
   - [Data Retrieval](#data-retrieval)
5. [Models](#models)
6. [Constants](#constants)
7. [Examples](#examples)

## Authentication

All API endpoints require user authentication. Users must be logged in to access any functionality.

**Authentication Method**: Django Session Authentication
**Required**: `@login_required` decorator on all endpoints

## Base URL

```
/change_requests/
```

## Error Handling

The API uses Django's message framework for user feedback and standard HTTP status codes:

- **200 OK**: Successful GET request
- **302 Redirect**: Successful POST request (redirects to appropriate page)
- **403 Forbidden**: Insufficient permissions
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server error

### Error Message Types

- **Error Messages**: Critical issues that prevent operation
- **Warning Messages**: Non-critical issues that should be noted
- **Success Messages**: Confirmation of successful operations

## Endpoints

### Change Request Management

#### 1. Change Request Index
**Endpoint**: `GET /change_requests/change_request_index`

**Description**: Displays the main change requests dashboard with filtering and search capabilities.

**Response**: HTML page with change requests list

**Template**: `change_requests/change_request_index.html`

---

#### 2. Create Change Request
**Endpoint**: `GET /change_requests/create_change_request`

**Description**: Displays the form for creating new change requests.

**Response**: HTML form page

**Template**: `change_requests/create_change_request.html`

---

#### 3. Create New Profile
**Endpoint**: `POST /change_requests/create_new_profile`

**Description**: Creates a new profile change request.

**Request Parameters**:
```json
{
    "change_reason": "string (required, max 500 chars)",
    "change_description": "string (required, max 1000 chars)",
    "originator_company": "string (required)",
    "originator_site": "string (required)",
    "date_resolution_required": "string (required, YYYY-MM-DD)",
    "username": "string (required, max 15 chars)",
    "first_name": "string (required, max 100 chars)",
    "last_name": "string (required, max 100 chars)",
    "email": "string (required, max 100 chars)",
    "designation": "integer (designation ID)",
    "cost_center": "integer (cost center ID)",
    "for_application": "integer (application ID)",
    "roles_to_action": "string (max 300 chars)",
    "np_ec_number": "string (required)",
    "np_job_title": "string (required)",
    "np_company": "string (required)",
    "np_sub_module": "string (optional)",
    "np_depot_office": "string (optional)",
    "np_training_date": "string (optional, YYYY-MM-DD)",
    "np_training_confirmation_link": "string (optional, URL)"
}
```

**Validation**:
- All required fields must be provided
- Originator metadata must be supplied (company, site, date required)
- EC number, job title, and company values must be specified for new profile
- Username must be unique
- Email must be valid format
- Field lengths must not exceed limits

**Response**: Redirect to change request index with success/error message

**Security Features**:
- CSRF protection
- Input sanitization
- Permission checking

---

#### 4. Update Change Request
**Endpoint**: `POST /change_requests/update_change_request`

**Description**: Updates an existing change request.

**Request Parameters**:
```json
{
    "cr_id": "string (required)",
    "change_reason": "string (optional)",
    "change_description": "string (optional)",
    "roles_to_action": "string (optional)",
    "roles_actions": "string (optional)"
}
```

**Validation**:
- Change request must exist
- User must have permission to update
- Change request must not be approved

**Response**: Redirect to change request index with success/error message

---

#### 5. Delete Change Request
**Endpoint**: `POST /change_requests/delete_change_request`

**Description**: Soft deletes a change request.

**Request Parameters**:
```json
{
    "cr_id": "string (required)"
}
```

**Validation**:
- Change request must exist and not be deleted
- User must have permission to delete
- Change request must not be approved

**Response**: Redirect to change request index with success/error message

**Security Features**:
- Permission checking
- Approval status validation
- Audit logging

---

#### 6. Restore Change Request
**Endpoint**: `POST /change_requests/restore_change_request`

**Description**: Restores a soft-deleted change request.

**Request Parameters**:
```json
{
    "cr_id": "string (required)"
}
```

**Validation**:
- Change request must exist and be deleted
- User must be admin or original deleter

**Response**: Redirect to change request index with success/error message

---

#### 7. Bulk Delete Change Requests
**Endpoint**: `POST /change_requests/bulk_delete_change_requests`

**Description**: Soft deletes multiple change requests.

**Request Parameters**:
```json
{
    "cr_ids[]": ["string", "string", ...]
}
```

**Validation**:
- Each change request must exist and not be deleted
- User must have permission for each request
- Approved requests are skipped

**Response**: Redirect to change request index with success message showing count

### Profile Operations

#### 8. Profile Modification Request
**Endpoint**: `POST /change_requests/profile_modification/create`

**Description**: Creates a profile modification change request.

**Request Parameters**:
```json
{
    "change_reason": "string (required)",
    "change_description": "string (required)",
    "originator_company": "string (required)",
    "originator_site": "string (required)",
    "date_resolution_required": "string (required, YYYY-MM-DD)",
    "change_type": "string (required, PERMANENT|TEMPORARY_DELEGATION)",
    "for_application": "string (required)",
    "user_profile": "string (required when change_type=PERMANENT)",
    "delegator": "string (required when change_type=TEMPORARY_DELEGATION)",
    "delegatee": "string (required when change_type=TEMPORARY_DELEGATION)",
    "roles_to_action": "string (optional)",
    "mod_current_user_id": "string (required)",
    "mod_ec_number": "string (required)",
    "mod_reason_assign": "string (required)",
    "mod_reason_remove": "string (required when mod_roles_remove is provided)",
    "mod_correspondence_link": "string (optional, URL)",
    "roles": "array[string] (optional, role IDs to assign)",
    "mod_roles_remove": "array[string] (optional, role IDs to remove)",
    "delegation_start_date": "string (required when change_type=TEMPORARY_DELEGATION, YYYY-MM-DDTHH:MM)",
    "delegation_end_date": "string (required when change_type=TEMPORARY_DELEGATION, YYYY-MM-DDTHH:MM)",
    "delegation_reason": "string (required when change_type=TEMPORARY_DELEGATION)"
}
```

**Response**: Redirect to change request index

---

#### 9. Profile Deactivation Request
**Endpoint**: `POST /change_requests/profile_deactivation_request`

**Description**: Creates a profile deactivation change request.

**Request Parameters**:
```json
{
    "change_reason": "string (required)",
    "change_description": "string (required)",
    "originator_company": "string (required)",
    "originator_site": "string (required)",
    "date_resolution_required": "string (required, YYYY-MM-DD)",
    "user_profile": "string (username, required)",
    "for_application": "string (required)",
    "deactivation_effective_start": "string (required, YYYY-MM-DDTHH:MM)",
    "deactivation_reactivation_date": "string (optional, YYYY-MM-DDTHH:MM)",
    "deactivation_reason": "string (required)",
    "deactivation_correspondence_link": "string (optional, URL)"
}
```

**Response**: Redirect to change request index

---

#### 10. Update New Profile Request
**Endpoint**: `POST /change_requests/update_new_profile_request`

**Description**: Updates a new profile change request.

**Request Parameters**:
```json
{
    "cr_id": "string (required)",
    "change_reason": "string (optional)",
    "change_description": "string (optional)",
    "roles_to_action": "string (optional)",
    "roles_actions": "string (optional)",
    "firstname": "string (optional)",
    "lastname": "string (optional)",
    "username": "string (optional)",
    "email": "string (optional)",
    "region": "integer (optional)",
    "cost_center": "integer (optional)",
    "district": "integer (optional)",
    "section": "string (optional)",
    "designation": "integer (optional)"
}
```

**Response**: Redirect to change request index

### Approval Workflow

#### 11. Approve Profile Request
**Endpoint**: `POST /change_requests/approve_change_request`

**Description**: Approves or rejects a change request.

**Request Parameters**:
```json
{
    "actionButton": "string (APPROVE|REJECT|APPLY)",
    "cr_id": "string (required)",
    "approvalReason": "string (optional, for approval)",
    "rejectReason": "string (optional, for rejection)",
    "roles_actions": "string (optional, for APPLY action)"
}
```

**Actions**:
- **APPROVE**: Approves the change request
- **REJECT**: Rejects the change request
- **APPLY**: Applies the change (IT section head only)

**Response**: Redirect to change request index

**Security Features**:
- Role-based access control
- Approval workflow validation
- Audit logging

### Data Retrieval

#### 12. Get User Data
**Endpoint**: `GET /change_requests/profile_modification/get_user_data/<username>`

**Description**: Retrieves user data for profile modification.

**URL Parameters**:
- `username`: Target user's username

**Response**: JSON object with user data
```json
{
    "applications": [
        {
            "id": "integer",
            "name": "string",
            "fullname": "string"
        }
    ],
    "userData": {
        "application_name": [
            {
                "id": "integer",
                "name": "string",
                "role": "string"
            }
        ]
    },
    "active_roles": {
        "application_name": {
            "id": "integer",
            "name": "string",
            "role": "string"
        }
    }
}
```

**Caching**: Results are cached for 5 minutes

---

#### 13. Data Table Data
**Endpoint**: `GET /change_requests/datatables/<view>`

**Description**: Provides data for DataTables with filtering, sorting, and pagination.

**URL Parameters**:
- `view`: View type (filter, export, etc.)

**Query Parameters**:
```json
{
    "draw": "integer (DataTables draw counter)",
    "start": "integer (starting record)",
    "length": "integer (page size)",
    "search[value]": "string (search term)",
    "order[0][column]": "integer (sort column)",
    "order[0][dir]": "string (asc|desc)",
    "region": "integer (optional filter)",
    "cr_type": "string (optional filter)",
    "cr_app": "string (optional filter)",
    "status": "string (optional filter)",
    "cost_center": "integer (optional filter)",
    "start_date": "string (optional filter)",
    "end_date": "string (optional filter)"
}
```

**Response**: DataTables JSON format
```json
{
    "draw": "integer",
    "recordsTotal": "integer",
    "recordsFiltered": "integer",
    "data": [
        {
            "cr_id": "string",
            "change_type": "string",
            "change_reason": "string",
            "created_by": "string",
            "created_at": "string",
            "section_head_approval": "string",
            "it_section_head_approval": "string"
        }
    ]
}
```

---

#### 14. CSV Export
**Endpoint**: `GET /change_requests/datatables/export`

**Description**: Exports change requests data to CSV format.

**Query Parameters**: Same as DataTable endpoint

**Response**: CSV file download

---

#### 15. Change Request Reports
**Endpoint**: `GET /change_requests/change_request_reports`

**Description**: Displays change request reports and analytics.

**Response**: HTML page with reports

**Template**: `change_requests/change_request_reports.html`

---

#### 16. View Profile Request
**Endpoint**: `GET /change_requests/view_change_request`

**Description**: Displays detailed view of a specific change request.

**Query Parameters**:
```json
{
    "i": "string (change request ID)"
}
```

**Response**: HTML page with change request details

**Template**: `change_requests/view_profile_request.html`

---

#### 17. New Profile Request
**Endpoint**: `GET /change_requests/new_profile_request`

**Description**: Displays form for creating new profile requests.

**Response**: HTML form page

**Template**: `change_requests/new_profile_request.html`

---

#### 18. Roles Modal
**Endpoint**: `POST /change_requests/roles_modal`

**Description**: Handles role assignment modal functionality.

**Request Parameters**:
```json
{
    "appid": "integer (application ID)",
    "userid": "integer (user ID)"
}
```

**Response**: JSON with form data and role information

## Models

### ChangeRequest Model

**Primary Key**: `cr_id` (CharField, max_length=100)

**Fields**:
- `application`: CharField (max_length=100, optional)
- `change_type`: CharField (max_length=100)
- `new_profile`: ForeignKey to NewProfile (optional)
- `profile_change`: ForeignKey to ProfileChange (optional)
- `profile_deactivation`: ForeignKey to ProfileDeactivation (optional)
- `change_description`: TextField (optional)
- `change_reason`: TextField (optional)
- `originator_company`: CharField (optional)
- `originator_site`: CharField (optional)
- `date_resolution_required`: DateField (optional)
- `creator_designation`: ForeignKey to Designations
- `created_by`: ForeignKey to UserProfile
- `region`: ForeignKey to Regions
- `cost_center`: ForeignKey to CostCenter (optional)
- `created_at`: DateTimeField (auto_now_add=True)
- `is_deleted`: BooleanField (default=False)
- `deleted_at`: DateTimeField (optional)
- `deleted_by`: ForeignKey to UserProfile (optional)

**Methods**:
- `soft_delete(user)`: Marks record as deleted
- `restore()`: Restores deleted record

### NewProfile Model

**Fields**:
- `username`: CharField (max_length=15, optional)
- `ec_number`: CharField (optional)
- `first_name`: CharField (max_length=100, optional)
- `last_name`: CharField (max_length=100, optional)
- `email`: EmailField (max_length=100, optional)
- `job_title`: CharField (optional)
- `company`: CharField (optional)
- `designation`: ForeignKey to Designations (optional)
- `section`: ForeignKey to Sections (optional)
- `cost_center`: ForeignKey to CostCenter (optional)
- `district`: ForeignKey to Districts (optional)
- `depot_office`: CharField (optional)
- `sub_module`: CharField (optional)
- `training_date`: DateField (optional)
- `training_confirmation_link`: URLField (optional)
- `roles_to_action`: CharField (max_length=300, optional)
- `roles_actions`: CharField (max_length=300, optional)
- `roles`: ManyToManyField to Roles
- `region`: ForeignKey to Regions (optional)
- `created_at`: DateTimeField (auto_now_add=True)

### CRApproval Model

**Fields**:
- `cr_id`: ForeignKey to ChangeRequest
- `approver`: ForeignKey to UserProfile
- `approver_role`: ForeignKey to Roles
- `approval_status`: BooleanField
- `comment`: TextField (optional)
- `approval_date`: DateTimeField

## Constants

### Change Types
- `NEW_PROFILE`: "New Profile"
- `PROFILE_MODIFICATION`: "Profile Modification"
- `PROFILE_DEACTIVATION`: "Profile Deactivation"

### Approval Roles
- `SECTION_HEAD`: "section_head"
- `IT_SECTION_HEAD`: "it_section_head"

### Field Length Limits
- `MAX_DESCRIPTION_LENGTH`: 1000
- `MAX_REASON_LENGTH`: 500
- `MAX_USERNAME_LENGTH`: 15
- `MAX_NAME_LENGTH`: 100
- `MAX_EMAIL_LENGTH`: 100

### Cache Settings
- `CACHE_TIMEOUT`: 300 (5 minutes)
- `USER_DATA_CACHE_KEY_PREFIX`: "user_data_"

## Examples

### Creating a New Profile Request

```javascript
// POST /change_requests/create_new_profile
const formData = new FormData();
formData.append('change_reason', 'New employee onboarding');
formData.append('change_description', 'Creating account for new team member');
formData.append('originator_company', 'ZETDC');
formData.append('originator_site', 'Harare Region');
formData.append('date_resolution_required', '2025-12-31');
formData.append('username', 'newemployee');
formData.append('first_name', 'John');
formData.append('last_name', 'Doe');
formData.append('email', 'john.doe@company.com');
formData.append('designation', '1');
formData.append('cost_center', '1');
formData.append('for_application', '1');
formData.append('roles_to_action', 'Add basic user role');
formData.append('np_ec_number', '1234567');
formData.append('np_job_title', 'Analyst');
formData.append('np_company', 'ZETDC');
formData.append('np_training_date', '2025-11-01');
formData.append('np_training_confirmation_link', 'https://example.com/training-proof');

fetch('/change_requests/create_new_profile', {
    method: 'POST',
    body: formData,
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    }
});
```

### Approving a Change Request

```javascript
// POST /change_requests/approve_change_request
const formData = new FormData();
formData.append('actionButton', 'APPROVE');
formData.append('cr_id', 'CR001');
formData.append('approvalReason', 'Approved after review');

fetch('/change_requests/approve_change_request', {
    method: 'POST',
    body: formData,
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    }
});
```

### Bulk Delete Operations

```javascript
// POST /change_requests/bulk_delete_change_requests
const formData = new FormData();
formData.append('cr_ids[]', 'CR001');
formData.append('cr_ids[]', 'CR002');
formData.append('cr_ids[]', 'CR003');

fetch('/change_requests/bulk_delete_change_requests', {
    method: 'POST',
    body: formData,
    headers: {
        'X-CSRFToken': getCookie('csrftoken')
    }
});
```

### Getting User Data

```javascript
// GET /change_requests/profile_modification/get_user_data/username
fetch('/change_requests/profile_modification/get_user_data/johndoe')
    .then(response => response.json())
    .then(data => {
        console.log('Applications:', data.applications);
        console.log('User Data:', data.userData);
        console.log('Active Roles:', data.active_roles);
    });
```

## Security Considerations

1. **CSRF Protection**: All POST endpoints are protected with CSRF tokens
2. **Input Sanitization**: All user input is sanitized to prevent XSS attacks
3. **Permission Checking**: Users can only access/modify resources they have permission for
4. **Audit Logging**: All operations are logged for security monitoring
5. **Soft Delete**: Data is never permanently deleted, maintaining audit trail
6. **Validation**: All input is validated before processing

## Performance Optimizations

1. **Database Indexing**: Strategic indexes on frequently queried fields
2. **Query Optimization**: Use of select_related and prefetch_related
3. **Caching**: User data is cached for 5 minutes to reduce database load
4. **Pagination**: Large datasets are paginated for better performance

## Error Codes and Messages

### Common Error Messages
- `CHANGE_REQUEST_NOT_FOUND`: "Change request not found"
- `INSUFFICIENT_PERMISSIONS`: "Insufficient permissions"
- `CANNOT_DELETE_APPROVED`: "Cannot delete approved change request"
- `CANNOT_RESTORE`: "Insufficient permissions to restore"
- `VALIDATION_ERROR`: "Validation error occurred"
- `DUPLICATE_USERNAME`: "Username already exists"

### Success Messages
- `CHANGE_REQUEST_CREATED`: "Change request created successfully"
- `CHANGE_REQUEST_UPDATED`: "Change request updated successfully"
- `CHANGE_REQUEST_DELETED`: "Change request deleted successfully"
- `CHANGE_REQUEST_RESTORED`: "Change request restored successfully"
- `BULK_DELETE_SUCCESS`: "Successfully deleted {count} change requests"

## Role Delegation API

### Delegation Endpoints

#### 1. Delegation Dashboard
**Endpoint**: `GET /users/delegation-dashboard`

**Description**: Main dashboard for role delegation management with statistics and recent activity.

**Response**: HTML page with delegation dashboard

**Template**: `users/delegation_dashboard.html`

---

#### 2. Create Delegation
**Endpoint**: `POST /users/delegation/create`

**Description**: Create a new role delegation request.

**Request Parameters**:
```json
{
    "delegatee": "integer (user ID, required)",
    "roles": ["integer", "integer", ...] (role IDs, required),
    "applications": ["integer", "integer", ...] (application IDs, required),
    "start_date": "datetime (required)",
    "end_date": "datetime (required)",
    "reason": "string (required, max 1000 chars)"
}
```

**Validation**:
- Delegatee must be in the same region as delegator
- Roles must be roles that the delegator currently has
- Start date cannot be in the past
- End date must be after start date
- Delegation period cannot exceed 90 days

**Response**: Redirect to delegation dashboard with success/error message

---

#### 3. Delegation List
**Endpoint**: `GET /users/delegation/list`

**Description**: List all delegations with filtering and search capabilities.

**Query Parameters**:
```json
{
    "status": "string (optional)",
    "delegation_type": "string (optional)",
    "start_date": "date (optional)",
    "end_date": "date (optional)",
    "search": "string (optional)"
}
```

**Response**: HTML page with filtered delegation list

---

#### 4. Delegation Detail
**Endpoint**: `GET /users/delegation/<delegation_id>/`

**Description**: View detailed information about a specific delegation.

**Response**: HTML page with delegation details and history

---

#### 5. Approve Delegation
**Endpoint**: `POST /users/delegation/<delegation_id>/approve`

**Description**: Approve or reject a delegation request.

**Request Parameters**:
```json
{
    "action": "string (APPROVE|REJECT, required)",
    "comments": "string (optional)"
}
```

**Response**: Redirect to delegation detail with success/error message

---

#### 6. Cancel Delegation
**Endpoint**: `POST /users/delegation/<delegation_id>/cancel`

**Description**: Cancel an active or pending delegation.

**Request Parameters**:
```json
{
    "reason": "string (optional)"
}
```

**Response**: Redirect to delegation detail with success/error message

---

#### 7. Delegation Notifications
**Endpoint**: `GET /users/delegation/notifications`

**Description**: View delegation notifications for the current user.

**Response**: HTML page with notification list

---

#### 8. Delegation Calendar
**Endpoint**: `GET /users/delegation/calendar`

**Description**: Calendar view of delegations with visual timeline.

**Response**: HTML page with calendar interface

### Delegation Models

#### RoleDelegation Model
```python
{
    "id": "integer (primary key)",
    "delegator": "UserProfile (foreign key)",
    "delegatee": "UserProfile (foreign key)",
    "roles": "ManyToManyField to Roles",
    "applications": "ManyToManyField to Application",
    "start_date": "datetime",
    "end_date": "datetime",
    "reason": "text",
    "status": "PENDING|APPROVED|ACTIVE|EXPIRED|CANCELLED|REJECTED",
    "approved_by": "UserProfile (foreign key, nullable)",
    "approved_at": "datetime (nullable)",
    "rejection_reason": "text (nullable)",
    "created_at": "datetime",
    "updated_at": "datetime",
    "is_active": "boolean",
    "created_by": "UserProfile (foreign key, nullable)"
}
```

#### DelegationNotification Model
```python
{
    "id": "integer (primary key)",
    "delegation": "RoleDelegation (foreign key)",
    "recipient": "UserProfile (foreign key)",
    "notification_type": "string",
    "message": "text",
    "sent_at": "datetime",
    "is_read": "boolean"
}
```

### Delegation Workflow

1. **Create Delegation**: User creates delegation request
2. **Pending Approval**: Delegation waits for approval
3. **Approval Process**: Admin/section head approves or rejects
4. **Activation**: Approved delegations become active at start date
5. **Active Period**: Delegatee has delegated roles during active period
6. **Expiry**: Delegation automatically expires at end date
7. **Cancellation**: Delegation can be cancelled at any time

### Delegation Permissions

- **Create Delegation**: Users with roles can delegate to same region users
- **Approve Delegation**: Admins and section heads can approve delegations
- **View Delegations**: Users can view their own delegations, admins can view all
- **Cancel Delegation**: Delegator or approvers can cancel delegations

### Delegation Automation

The system includes automated processes:

- **Automatic Activation**: Delegations activate at their start date
- **Automatic Expiry**: Delegations expire at their end date
- **Reminder Notifications**: Notifications sent 24 hours before expiry
- **Status Updates**: Automatic status transitions based on dates

### Management Commands

#### Process Delegations
```bash
python manage.py process_delegations
```

**Options**:
- `--dry-run`: Show what would be done without making changes

**Functionality**:
- Activates approved delegations past their start date
- Expires active delegations past their end date
- Sends reminder notifications for expiring delegations

## Version History

- **v1.0**: Initial implementation with basic CRUD operations
- **v1.1**: Added soft delete functionality
- **v1.2**: Added bulk operations
- **v1.3**: Added comprehensive security features
- **v1.4**: Added performance optimizations and caching
- **v1.5**: Added comprehensive testing and documentation
- **v1.6**: Added role delegation system with approval workflow
