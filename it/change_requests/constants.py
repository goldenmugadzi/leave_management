# Change Request Constants
# This file contains all constants used in the change requests application

# Change Request Types
CHANGE_TYPES = {
    'NEW_PROFILE': 'New Profile',
    'PROFILE_MODIFICATION': 'Profile Modification',
    'PROFILE_DEACTIVATION': 'Profile Deactivation',
    'TEMPORARY_ROLE_DELEGATION': 'Temporary Role Delegation'
}

# CR Type Configuration - Unified configuration for all CR types
CR_TYPE_CONFIG = {
    'NEW_PROFILE': {
        'name': 'New Profile',
        'operation_value': 'new_profile',
        'model_field': 'new_profile',
        'view_template': 'change_requests/components/sections/new_profile_details.html',
        'form_partial': 'change_requests/components/forms/new_profile_fields.html',
        'edit_partial': 'change_requests/components/forms/edit/new_profile_fields.html',
        'handler_class': 'NewProfileHandler',
        'requires_roles_implementation': True,
        'url_segment': 'new_profile_request',
        'form_section_id': 'new-profile-fields',
        'field_groups': [
            {
                'key': 'identity',
                'title': 'New User Profile Information',
                'fields': [
                    'ec_number', 'first_name', 'last_name', 'username', 'email',
                    'job_title', 'company', 'designation', 'region', 'cost_center',
                    'section', 'district', 'depot_office', 'sub_module'
                ]
            },
            {
                'key': 'training',
                'title': 'Training Details',
                'fields': ['training_date', 'training_confirmation_link']
            },
            {
                'key': 'roles',
                'title': 'Roles & Implementation',
                'fields': ['roles_to_action', 'roles_actions']
            }
        ]
        ,
        'view_sections': [
            'section_a',
            'section_b_change_type',
            'section_c_new_profile',
            'section_c_training',
            'section_roles_implementation',
            'section_f_creator',
            'section_g_status'
        ]
    },
    'PROFILE_MODIFICATION': {
        'name': 'Profile Modification',
        'operation_value': 'profile_modification',
        'model_field': 'profile_change',
        'view_template': 'change_requests/components/sections/profile_modification_details.html',
        'form_partial': 'change_requests/components/forms/profile_modification_fields.html',
        'edit_partial': 'change_requests/components/forms/edit/profile_modification_fields.html',
        'handler_class': 'ProfileModificationHandler',
        'requires_roles_implementation': True,
        'url_segment': 'profile_modification_request',
        'form_section_id': 'profile-modification-fields',
        'field_groups': [
            {
                'key': 'identity',
                'title': 'Existing User Profile',
                'fields': [
                    'firstname', 'lastname', 'username', 'email',
                    'current_user_id', 'ec_number', 'designation',
                    'region', 'district', 'section', 'cost_center'
                ]
            },
            {
                'key': 'roles',
                'title': 'Role Change Instructions',
                'fields': [
                    'roles_to_action', 'roles_actions', 'reason_assign',
                    'reason_remove', 'correspondence_link'
                ]
            }
        ]
        ,
        'view_sections': [
            'section_a',
            'section_b_change_type',
            'section_d_change_details',
            'section_d_existing_user',
            'section_d_role_change',
            'section_f_creator',
            'section_g_status'
        ]
    },
    'PROFILE_DEACTIVATION': {
        'name': 'Profile Deactivation',
        'operation_value': 'profile_deactivation',
        'model_field': 'profile_deactivation',
        'view_template': 'change_requests/components/sections/profile_deactivation_details.html',
        'form_partial': 'change_requests/components/forms/profile_deactivation_fields.html',
        'edit_partial': 'change_requests/components/forms/edit/profile_deactivation_fields.html',
        'handler_class': 'ProfileDeactivationHandler',
        'requires_roles_implementation': False,
        'url_segment': 'profile_deactivation_request',
        'form_section_id': 'profile-deactivation-fields',
        'field_groups': [
            {
                'key': 'identity',
                'title': 'User Profile',
                'fields': ['username', 'first_name', 'last_name', 'email', 'designation']
            },
            {
                'key': 'deactivation',
                'title': 'Deactivation Details',
                'fields': [
                    'effective_start_date', 'reactivation_date', 'deactivation_reason',
                    'correspondence_link'
                ]
            }
        ]
        ,
        'view_sections': [
            'section_a',
            'section_b_change_type',
            'section_deactivation_user',
            'section_deactivation_details',
            'section_f_creator',
            'section_g_status'
        ]
    },
    'TEMPORARY_ROLE_DELEGATION': {
        'name': 'Temporary Role Delegation',
        'operation_value': 'profile_modification',
        'model_field': 'profile_change',
        'view_template': 'change_requests/components/sections/profile_modification_details.html',
        'form_partial': 'change_requests/components/forms/profile_modification_fields.html',
        'edit_partial': 'change_requests/components/forms/edit/profile_modification_fields.html',
        'handler_class': 'ProfileModificationHandler',
        'requires_roles_implementation': True,
        'url_segment': 'profile_modification_request',
        'form_section_id': 'profile-modification-fields',
        'field_groups': [
            {
                'key': 'identity',
                'title': 'Delegatee',
                'fields': ['firstname', 'lastname', 'username', 'email', 'designation']
            },
            {
                'key': 'delegation',
                'title': 'Delegation Window',
                'source': 'delegation_info',
                'fields': [
                    'delegator_name', 'delegator_username',
                    'delegatee_name', 'delegatee_username',
                    'start_date', 'end_date', 'delegation_reason'
                ]
            },
            {
                'key': 'roles',
                'title': 'Roles To Delegate',
                'fields': ['roles_to_action', 'roles_actions']
            }
        ]
        ,
        'view_sections': [
            'section_a',
            'section_b_change_type',
            'section_d_change_details',
            'section_d_existing_user',
            'section_delegation_window',
            'section_d_role_change',
            'section_f_creator',
            'section_g_status'
        ]
    }
}

# Quick lookup from display name back to config key
CR_TYPE_NAME_MAP = {
    config['name']: key for key, config in CR_TYPE_CONFIG.items()
}

VIEW_SECTION_DEFINITIONS = {
    'section_a': {
        'section_label': 'A',
        'title': 'Change Request Originator',
        'source': 'cr',
        'description': 'Details about the request originator and the change raised.',
        'fields': [
            {'key': 'change_type', 'label': 'Change Type'},
            {'key': 'cr_id', 'label': 'CR ID'},
            {'key': 'originator_company', 'label': 'Originator Company'},
            {'key': 'originator_site', 'label': 'Originator Site'},
            {'key': 'change_reason', 'label': 'Reason for Change'},
            {'key': 'change_description', 'label': 'Change Description'},
            {'key': 'date_resolution_required', 'label': 'Resolution Required By'},
            {'key': 'application', 'label': 'Application'},
        ]
    },
    'section_b_change_type': {
        'section_label': 'B',
        'title': 'Type of Change',
        'source': 'cr',
        'description': 'Reference of the requested action. Only the selected change type is highlighted.',
        'options': [
            {'label': 'Creation of New Profile', 'match': 'New Profile'},
            {'label': 'Modification of Current Profile – Assignment/Removal of Role', 'match': 'Profile Modification'},
            {'label': 'Temporary Role Delegation', 'match': 'Temporary Role Delegation'},
            {'label': 'Deactivation of Profile', 'match': 'Profile Deactivation'},
        ]
    },
    'section_c_new_profile': {
        'section_label': 'C',
        'title': 'Creation of New Profile',
        'source': 'user',
        'description': 'Personal and work details for the new user profile.',
        'fields': [
            {'key': 'ec_number', 'label': 'EC Number'},
            {'key': 'firstname', 'label': 'First Name'},
            {'key': 'lastname', 'label': 'Last Name'},
            {'key': 'username', 'label': 'Username'},
            {'key': 'email', 'label': 'Email'},
            {'key': 'job_title', 'label': 'Job Title'},
            {'key': 'company', 'label': 'Company'},
            {'key': 'region', 'label': 'Region'},
            {'key': 'district', 'label': 'District'},
            {'key': 'depot_office', 'label': 'Depot / Office'},
            {'key': 'designation', 'label': 'Designation'},
            {'key': 'section', 'label': 'Section'},
            {'key': 'cost_center', 'label': 'Cost Centre'},
            {'key': 'sub_module', 'label': 'Sub Module'},
        ]
    },
    'section_c_training': {
        'section_label': 'C',
        'title': 'Training Details',
        'source': 'user',
        'description': 'Confirmation of training prior to provisioning access.',
        'fields': [
            {'key': 'training_date', 'label': 'Date of Training'},
            {'key': 'training_confirmation_link', 'label': 'Training Confirmation Link'},
            {'key': 'training_confirmation_notes', 'label': 'Training Confirmation Notes'},
        ]
    },
    'section_roles_implementation': {
        'section_label': 'G',
        'title': 'Roles & Implementation',
        'source': 'user',
        'description': 'Implementation tracking for assigned roles.',
        'fields': [
            {'key': 'roles_to_action', 'label': 'Roles to Action'},
            {'key': 'roles_actions', 'label': 'Roles Implemented'},
        ]
    },
    'section_d_change_details': {
        'section_label': 'D',
        'title': 'Profile Modification Details',
        'source': 'cr',
        'description': 'High-level summary of the requested modification.',
        'fields': [
            {'key': 'change_type', 'label': 'Change Type'},
            {'key': 'application', 'label': 'Application'},
        ]
    },
    'section_d_existing_user': {
        'section_label': 'D',
        'title': 'Existing User Profile',
        'source': 'user',
        'description': 'Current profile information for the targeted user.',
        'fields': [
            {'key': 'firstname', 'label': 'First Name'},
            {'key': 'lastname', 'label': 'Last Name'},
            {'key': 'username', 'label': 'Username'},
            {'key': 'email', 'label': 'Email'},
            {'key': 'current_user_id', 'label': 'Current User ID'},
            {'key': 'ec_number', 'label': 'EC Number'},
            {'key': 'designation', 'label': 'Designation'},
            {'key': 'region', 'label': 'Region'},
            {'key': 'district', 'label': 'District'},
            {'key': 'section', 'label': 'Section'},
            {'key': 'cost_center', 'label': 'Cost Centre'},
        ]
    },
    'section_d_role_change': {
        'section_label': 'D',
        'title': 'Role Change Instructions',
        'source': 'user',
        'description': 'Detailed instructions for assigning or removing roles.',
        'fields': [
            {'key': 'roles_to_action', 'label': 'Roles to Action'},
            {'key': 'roles_to_assign_notes', 'label': 'New Roles to Assign'},
            {'key': 'roles_to_remove_notes', 'label': 'Roles to Remove'},
            {'key': 'reason_assign', 'label': 'Reason for Assigning New Roles'},
            {'key': 'reason_remove', 'label': 'Reason for Removing Current Roles'},
            {'key': 'correspondence_link', 'label': 'Correspondence / Instruction Link'},
        ]
    },
    'section_delegation_window': {
        'section_label': 'D',
        'title': 'Delegation Window',
        'source': 'delegation_info',
        'description': 'Delegation timeline and participants.',
        'fields': [
            {'key': 'delegator_name', 'label': 'Delegator Name'},
            {'key': 'delegator_username', 'label': 'Delegator Username'},
            {'key': 'delegatee_name', 'label': 'Delegatee Name'},
            {'key': 'delegatee_username', 'label': 'Delegatee Username'},
            {'key': 'start_date', 'label': 'Delegation Start Date'},
            {'key': 'end_date', 'label': 'Delegation End Date'},
            {'key': 'delegation_reason', 'label': 'Delegation Reason'},
            {'key': 'formatted_display', 'label': 'Delegated Roles'},
        ]
    },
    'section_deactivation_user': {
        'section_label': 'E',
        'title': 'User Profile',
        'source': 'user',
        'description': 'Profile targeted for deactivation.',
        'fields': [
            {'key': 'firstname', 'label': 'First Name'},
            {'key': 'lastname', 'label': 'Last Name'},
            {'key': 'username', 'label': 'Username'},
            {'key': 'email', 'label': 'Email'},
            {'key': 'designation', 'label': 'Designation'},
            {'key': 'region', 'label': 'Region'},
            {'key': 'district', 'label': 'District'},
            {'key': 'section', 'label': 'Section'},
            {'key': 'cost_center', 'label': 'Cost Centre'},
        ]
    },
    'section_deactivation_details': {
        'section_label': 'E',
        'title': 'Deactivation Details',
        'source': 'user',
        'description': 'Timeline and rationale for deactivation.',
        'fields': [
            {'key': 'effective_start_date', 'label': 'Effective Start Date'},
            {'key': 'reactivation_date', 'label': 'Reactivation Date'},
            {'key': 'deactivation_reason', 'label': 'Reason for Deactivation'},
            {'key': 'correspondence_link', 'label': 'Correspondence / Instruction Link'},
        ]
    },
    'section_f_creator': {
        'section_label': 'F',
        'title': 'Change Authorisation',
        'source': 'cr',
        'description': 'Authorisation trail for the change request.',
        'fields': [
            {'key': 'created_by', 'label': 'Created By'},
            {'key': 'creator_designation', 'label': 'Creator Designation'},
            {'key': 'created_at', 'label': 'Date Created'},
        ]
    },
    'section_g_status': {
        'section_label': 'G',
        'title': 'Implementation Status',
        'source': 'cr',
        'description': 'Implementation feedback and current status.',
        'fields': [
            {'key': 'overall_status', 'label': 'Overall Status'},
        ]
    },
}

# Approval Roles
APPROVAL_ROLES = {
    'SECTION_HEAD': 'section_head',
    'IT_SECTION_HEAD': 'it_section_head'
}

# Approval Workflow Configuration
APPROVAL_WORKFLOW = {
    'steps': ['section_head', 'it_section_head'],
    'step_names': {
        'section_head': 'Section Head Approval',
        'it_section_head': 'IT Section Head Approval & Implementation'
    },
    'notifications': {
        'created': 'section_head',
        'section_head_approved': 'it_section_head',
        'section_head_rejected': 'creator',
        'it_section_head_approved': 'creator',
        'it_section_head_rejected': 'creator',
    },
    'status_transitions': {
        'PENDING': {
            'section_head_approve': 'APPROVED',
            'section_head_reject': 'REJECTED'
        },
        'APPROVED': {
            'it_section_head_approve': 'IMPLEMENTED',
            'it_section_head_reject': 'REJECTED'
        }
    }
}

# Profile Change Status
PROFILE_CHANGE_STATUS = {
    'PENDING': 'PENDING',
    'APPROVED': 'APPROVED',
    'REJECTED': 'REJECTED',
    'IMPLEMENTED': 'IMPLEMENTED'
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
    'NO_ROLES_TO_ASSIGN': 'Change request approved with no role changes - no roles were specified for assignment',
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
    'change_description',
    'originator_company',
    'originator_site',
    'date_resolution_required'
]

REQUIRED_NEW_PROFILE_FIELDS = [
    'username',
    'first_name',
    'last_name',
    'email',
    'np_ec_number',
    'np_company'
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
    'NO_ROLES_APPROVAL': 'IT approved change request {cr_id} with no roles to assign by {username}',
}
