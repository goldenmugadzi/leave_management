"""
Change Request Type Handlers

Specific handlers for each CR type (New Profile, Profile Modification, Profile Deactivation).
Each handler knows how to extract and format data for its specific CR type.
"""

import logging
from typing import Dict, Any

from it.change_requests.models import ChangeRequest, NewProfile, ProfileChange, ProfileDeactivation
from it.users.models import UserProfile

logger = logging.getLogger(__name__)


class NewProfileHandler:
    """Handler for New Profile change requests"""
    
    @staticmethod
    def get_profile_data(cr: ChangeRequest) -> Dict[str, Any]:
        """
        Extract profile data from NewProfile model.
        Returns standardized dict format used in templates.
        """
        if not cr.new_profile:
            logger.error(f"CR {cr.cr_id} is New Profile type but has no new_profile object")
            return {}
        
        new_profile = cr.new_profile
        
        return {
            "id": new_profile.pk,
            "username": new_profile.username,
            "first_name": new_profile.first_name,
            "last_name": new_profile.last_name,
            "firstname": new_profile.first_name,  # For template compatibility
            "lastname": new_profile.last_name,    # For template compatibility
            "email": new_profile.email,
            "roles_to_action": new_profile.roles_to_action,
            "roles_actions": new_profile.roles_actions,
            "section": new_profile.section,
            "district": new_profile.district,
            "region": new_profile.region,
            "cost_center": new_profile.cost_center,
            "designation": new_profile.designation,
        }
    
    @staticmethod
    def get_template_name() -> str:
        """Return template name for this CR type"""
        return "change_requests/components/sections/new_profile_details.html"


class ProfileModificationHandler:
    """Handler for Profile Modification and Temporary Role Delegation change requests"""
    
    @staticmethod
    def get_profile_data(cr: ChangeRequest) -> Dict[str, Any]:
        """
        Extract profile data from ProfileChange model.
        Returns standardized dict format used in templates.
        """
        if not cr.profile_change:
            logger.error(f"CR {cr.cr_id} is Profile Modification type but has no profile_change object")
            return {}
        
        profile_change = cr.profile_change
        user = profile_change.user
        
        try:
            cost_center = user.cost_center
        except Exception as ex:
            logger.error(f"Error getting cost center for user {user.username}: {ex}")
            cost_center = None
        
        # FIXED: Build roles_to_action display from actual assigned roles for delegations
        roles_to_action_display = profile_change.roles_to_action
        if cr.change_type == "Temporary Role Delegation":
            # Get actual roles from role_to_assign ManyToMany field
            assigned_roles = profile_change.role_to_assign.all()
            if assigned_roles.exists():
                # Build a readable string of role names
                role_names = [role.role for role in assigned_roles]
                roles_to_action_display = ", ".join(role_names)
            else:
                # Fallback if no roles assigned
                roles_to_action_display = profile_change.roles_to_action or "TEMPORARY_DELEGATION (No roles specified)"
        
        profile_data = {
            "id": user.pk,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "firstname": user.first_name,  # For template compatibility
            "lastname": user.last_name,    # For template compatibility
            "email": user.email,
            "section": user.section,
            "district": user.district,
            "region": user.region,
            "cost_center": cost_center,
            "designation": user.designation,
            "roles_to_action": roles_to_action_display,  # FIXED: Shows actual roles for delegations
            "roles_actions": profile_change.roles_actions,
        }
        
        return profile_data
    
    @staticmethod
    def get_delegation_info(cr: ChangeRequest) -> Dict[str, Any]:
        """
        Parse delegation data for proper display.
        This is specific to profile modification/delegation requests.
        """
        if not cr.profile_change:
            return {
                'display_type': 'permanent',
                'is_delegation': False,
                'delegator_name': '',
                'delegatee_name': '',
                'formatted_display': '',
                'assigned_roles': [],
                'assigned_role_names': [],
            }
        
        profile_change = cr.profile_change
        roles_to_action = profile_change.roles_to_action or ''
        
        # Check if this is a delegation request
        is_delegation = cr.change_type == "Temporary Role Delegation"
        
        # Get delegator from changed_by field (who initiated the delegation)
        delegator_name = ''
        delegator_username = ''
        if is_delegation and profile_change.changed_by:
            delegator_obj = profile_change.changed_by
            delegator_name = delegator_obj.get_full_name()
            delegator_username = delegator_obj.username
        
        # Get delegatee (the user being modified)
        delegatee_name = profile_change.user.get_full_name() if profile_change.user else ''
        delegatee_username = profile_change.user.username if profile_change.user else ''
        
        # FIXED: Get actual assigned roles from role_to_assign ManyToMany field
        assigned_roles = []
        assigned_role_names = []
        start_date = ''
        end_date = ''
        reason = ''
        
        if is_delegation:
            assigned_roles_list = list(profile_change.role_to_assign.all())
            assigned_roles = assigned_roles_list
            assigned_role_names = [role.role for role in assigned_roles_list]
            
            # Parse delegation metadata from roles_actions JSON field
            if profile_change.roles_actions:
                try:
                    import json
                    from datetime import datetime
                    data = json.loads(profile_change.roles_actions)
                    
                    # Get delegation dates
                    start_date_raw = data.get('start_date', '')
                    end_date_raw = data.get('end_date', '')
                    
                    if start_date_raw:
                        try:
                            start_dt = datetime.fromisoformat(start_date_raw.replace('T', ' '))
                            start_date = start_dt.strftime('%B %d, %Y at %I:%M %p')
                        except:
                            start_date = start_date_raw
                    
                    if end_date_raw:
                        try:
                            end_dt = datetime.fromisoformat(end_date_raw.replace('T', ' '))
                            end_date = end_dt.strftime('%B %d, %Y at %I:%M %p')
                        except:
                            end_date = end_date_raw
                    
                    reason = data.get('reason', '')
                except (json.JSONDecodeError, Exception) as e:
                    logger.error(f"Error parsing delegation metadata: {e}")
        
        # Build formatted display
        if is_delegation and assigned_role_names:
            formatted_display = ", ".join(assigned_role_names)
        else:
            formatted_display = roles_to_action
        
        return {
            'display_type': 'delegation' if is_delegation else 'permanent',
            'is_delegation': is_delegation,
            'delegator_name': delegator_name,
            'delegator_username': delegator_username,
            'delegatee_name': delegatee_name,
            'delegatee_username': delegatee_username,
            'formatted_display': formatted_display,
            'assigned_roles': assigned_roles,  # ADDED: Role objects for template
            'assigned_role_names': assigned_role_names,  # ADDED: Role names for display
            'start_date': start_date,  # ADDED: Delegation start date
            'end_date': end_date,  # ADDED: Delegation end date
            'reason': reason,  # ADDED: Delegation reason
        }
    
    @staticmethod
    def get_change_request_context(cr: ChangeRequest) -> Dict[str, Any]:
        """
        Get context specific to profile modification/delegation requests.
        """
        delegation_info = ProfileModificationHandler.get_delegation_info(cr)
        
        context = {
            'change_type': cr.change_type,
            'is_new_profile': False,
            'is_profile_change': True,
            'is_profile_deactivation': False,
            'application': cr.application,
            'is_business_excellence': cr.application == 'BUSINESS EXCELLENCE',
            'delegation_info': delegation_info,
            'display_type': delegation_info['display_type'],
            'requires_roles': delegation_info['display_type'] != 'deactivation',
            'roles_label': ProfileModificationHandler._get_roles_label(delegation_info['display_type'], 
                                                                       cr.application == 'BUSINESS EXCELLENCE'),
            'implementation_label': ProfileModificationHandler._get_implementation_label(delegation_info['display_type'])
        }
        
        return context
    
    @staticmethod
    def _get_roles_label(display_type: str, is_business_excellence: bool) -> str:
        """Get label for roles field based on context"""
        if display_type == 'delegation':
            return 'Delegation Details'
        elif is_business_excellence:
            return 'Roles to Assign/Designations to Action'
        else:
            return 'Roles/Permissions to Action'
    
    @staticmethod
    def _get_implementation_label(display_type: str) -> str:
        """Get label for implementation status field"""
        if display_type == 'delegation':
            return 'Delegation Implementation'
        else:
            return 'Implementation Status'
    
    @staticmethod
    def get_template_name() -> str:
        """Return template name for this CR type"""
        return "change_requests/components/sections/profile_modification_details.html"


class ProfileDeactivationHandler:
    """Handler for Profile Deactivation change requests"""
    
    @staticmethod
    def get_profile_data(cr: ChangeRequest) -> Dict[str, Any]:
        """
        Extract profile data from ProfileDeactivation model.
        Returns standardized dict format used in templates.
        """
        if not cr.profile_deactivation:
            logger.error(f"CR {cr.cr_id} is Profile Deactivation type but has no profile_deactivation object")
            return {}
        
        profile_deactivation = cr.profile_deactivation
        user = profile_deactivation.user
        
        return {
            "id": user.pk,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "firstname": user.first_name,  # For template compatibility
            "lastname": user.last_name,    # For template compatibility
            "email": user.email,
            "section": user.section,
            "district": user.district,
            "region": user.region,
            "cost_center": user.cost_center,
            "designation": user.designation,
        }
    
    @staticmethod
    def get_change_request_context(cr: ChangeRequest) -> Dict[str, Any]:
        """
        Get context specific to profile deactivation requests.
        """
        return {
            'change_type': cr.change_type,
            'is_new_profile': False,
            'is_profile_change': False,
            'is_profile_deactivation': True,
            'application': cr.application,
            'is_business_excellence': cr.application == 'BUSINESS EXCELLENCE',
            'display_type': 'deactivation',
            'requires_roles': False,
            'implementation_label': 'Deactivation Status'
        }
    
    @staticmethod
    def get_template_name() -> str:
        """Return template name for this CR type"""
        return "change_requests/components/sections/profile_deactivation_details.html"

