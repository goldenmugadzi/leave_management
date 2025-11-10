"""
Context Builder Service

Handles building template context data for change requests.
"""

import logging
from typing import Dict, Any
from django.db.models import Q

from it.change_requests.models import ChangeRequest
from it.users.models import (
    UserProfile, Application, Designations, 
    Sections, Districts, Regions
)

logger = logging.getLogger(__name__)


class ContextBuilder:
    """Service for building template context"""
    
    @staticmethod
    def get_base_template_context(user: UserProfile, cr: ChangeRequest) -> Dict[str, Any]:
        """
        Get common context data for all profile request views.
        This is the base context that all CR types share.
        """
        try:
            requestor_role = user.get_user_roles_for_application("change_requests") if user else None
            
            context = {
                "user_applications": Application.objects.all(),
                "user_designations": Designations.objects.all(),
                "sections": Sections.objects.all(),
                "districts": Districts.objects.all(),
                "regions": Regions.objects.all(),
                "user_title": user.get_full_name() if user else "",
                "user_groups": list(user.groups.values_list('name', flat=True)) if user else [],
                "requestor_role": requestor_role,
                "modal_auto_show": False,
                "change_request": cr
            }
            
            return context
        
        except Exception as e:
            logger.error(f"Error building base template context: {str(e)}")
            return {}
    
    @staticmethod
    def build_cr_context(cr: ChangeRequest, profile_data: Dict[str, Any]) -> Dict[str, Any]:
        """
        Build the standardized CR context dict.
        This is used in all templates to display CR information.
        """
        context = {
            "user": profile_data,
            "cr_id": cr.cr_id,
            "change_reason": cr.change_reason,
            "change_description": cr.change_description,
            "application": cr.application,
            "created_by": cr.created_by.get_full_name() if cr.created_by else "",
            "creator_designation": cr.creator_designation.description if cr.creator_designation else "",
            "created_at": cr.created_at,
            "change_type": cr.change_type,
        }
        
        return context
    
    @staticmethod
    def add_approval_context(context: Dict[str, Any], permissions: Dict[str, bool], 
                            approval_status: Dict[str, Any]) -> Dict[str, Any]:
        """
        Add approval-related context to the base context.
        This includes permissions and approval status flags.
        """
        context.update({
            "section_head_allowed": permissions.get('section_head_allowed', False),
            "it_section_head_allowed": permissions.get('it_section_head_allowed', False),
            "section_head_awaiting_action": approval_status.get('section_head_awaiting_action', True),
            "it_section_head_awaiting_action": approval_status.get('it_section_head_awaiting_action', True),
            "cr_approvals": approval_status.get('cr_approvals', []),
        })
        
        return context

