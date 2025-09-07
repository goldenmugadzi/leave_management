# Change Request Constants
# This file contains all constants used in the change requests application

# Change Request Types
CHANGE_TYPES = {
    'NEW_PROFILE': 'New Profile',
    'PROFILE_MODIFICATION': 'Profile Modification',
    'PROFILE_DEACTIVATION': 'Profile Deactivation'
}

# Approval Roles
APPROVAL_ROLES = {
    'SECTION_HEAD': 'section_head',
    'IT_SECTION_HEAD': 'it_section_head'
}

# Approval Status
APPROVAL_STATUS = {
    'PENDING': 'Pending',
    'APPROVED': 'Approved',
    'REJECTED': 'Rejected'
}

# Field Length Limits
MAX_DESCRIPTION_LENGTH = 1000
MAX_REASON_LENGTH = 500
MAX_USERNAME_LENGTH = 15
MAX_NAME_LENGTH = 100
MAX_EMAIL_LENGTH = 100

# Cache Settings
CACHE_TIMEOUT = 300  # 5 minutes in seconds
USER_DATA_CACHE_KEY_PREFIX = "user_data_"

# Pagination Settings
DEFAULT_PAGE_SIZE = 10
MAX_PAGE_SIZE = 100

# Error Messages
ERROR_MESSAGES = {
    'CHANGE_REQUEST_NOT_FOUND': 'Change request not found',
    'INSUFFICIENT_PERMISSIONS': 'Insufficient permissions',
    'CANNOT_DELETE_APPROVED': 'Cannot delete approved change request',
    'CANNOT_RESTORE': 'Insufficient permissions to restore',
    'VALIDATION_ERROR': 'Validation error occurred',
    'DUPLICATE_USERNAME': 'Username already exists',
    'REQUIRED_FIELD_MISSING': 'Required field is missing',
    'FIELD_TOO_LONG': 'Field exceeds maximum length',
}

# Success Messages
SUCCESS_MESSAGES = {
    'CHANGE_REQUEST_CREATED': 'Change request created successfully',
    'CHANGE_REQUEST_UPDATED': 'Change request updated successfully',
    'CHANGE_REQUEST_DELETED': 'Change request deleted successfully',
    'CHANGE_REQUEST_RESTORED': 'Change request restored successfully',
    'BULK_DELETE_SUCCESS': 'Successfully deleted {count} change requests',
    'APPROVAL_SUCCESS': 'Change request approved successfully',
    'REJECTION_SUCCESS': 'Change request rejected successfully',
}

# Warning Messages
WARNING_MESSAGES = {
    'ALREADY_APPROVED': 'Change request has already been approved by the section head. You cannot update it',
    'NO_CHANGES_MADE': 'No changes were made to the change request',
}

# Application Names
APPLICATION_NAMES = {
    'CHANGE_REQUESTS': 'change_requests',
    'BUSINESS_EXCELLENCE': 'BUSINESS EXCELLENCE',
}

# Database Query Settings
SELECT_RELATED_FIELDS = [
    'new_profile',
    'profile_change__user',
    'profile_deactivation__user',
    'created_by',
    'creator_designation',
    'region',
    'cost_center'
]

PREFETCH_RELATED_FIELDS = [
    'crapproval_set__approver',
    'crapproval_set__approver_role'
]

# Required Fields for Validation
REQUIRED_CHANGE_REQUEST_FIELDS = [
    'change_reason',
    'change_description'
]

REQUIRED_NEW_PROFILE_FIELDS = [
    'username',
    'first_name',
    'last_name',
    'email'
]

# URL Patterns
URL_PATTERNS = {
    'CHANGE_REQUEST_INDEX': '/change_requests/change_request_index',
    'CREATE_CHANGE_REQUEST': '/change_requests/create_change_request',
    'UPDATE_CHANGE_REQUEST': '/change_requests/update_change_request',
    'DELETE_CHANGE_REQUEST': '/change_requests/delete_change_request',
    'RESTORE_CHANGE_REQUEST': '/change_requests/restore_change_request',
    'BULK_DELETE_CHANGE_REQUESTS': '/change_requests/bulk_delete_change_requests',
}

# Logging Configuration
LOG_LEVELS = {
    'INFO': 'INFO',
    'WARNING': 'WARNING',
    'ERROR': 'ERROR',
    'DEBUG': 'DEBUG'
}

LOG_MESSAGES = {
    'CHANGE_REQUEST_CREATED': 'Change request created: {cr_id} by {username}',
    'CHANGE_REQUEST_UPDATED': 'Change request updated: {cr_id} by {username}',
    'CHANGE_REQUEST_DELETED': 'Change request deleted: {cr_id} by {username}',
    'CHANGE_REQUEST_RESTORED': 'Change request restored: {cr_id} by {username}',
    'BULK_DELETE': 'Bulk delete performed: {count} requests by {username}',
    'PERMISSION_DENIED': 'Permission denied for user {username} on change request {cr_id}',
    'VALIDATION_ERROR': 'Validation error for user {username}: {errors}',
    'APPROVAL_ACTION': 'Approval action: {action} on {cr_id} by {username}',
}
