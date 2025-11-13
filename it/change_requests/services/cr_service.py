"""
Change Request Service Layer

Handles business logic for change request operations including
validation, creation, and data retrieval.
"""

import logging
from datetime import datetime
from typing import Dict, List, Optional, Any
from django.db import transaction
from django.utils import timezone
from django.core.exceptions import ValidationError
from django.core.validators import validate_email

from it.change_requests.models import (
    ChangeRequest, NewProfile, ProfileChange, ProfileDeactivation, CRApproval
)
from it.users.models import (
    UserProfile, Designations, CostCenter, Regions, 
    Sections, Districts, Roles, Application
)
from it.change_requests.constants import (
    ERROR_MESSAGES, MAX_DESCRIPTION_LENGTH, MAX_REASON_LENGTH,
    REQUIRED_CHANGE_REQUEST_FIELDS, REQUIRED_NEW_PROFILE_FIELDS
)

logger = logging.getLogger(__name__)


class ChangeRequestService:
    """Service for managing change requests"""
    
    @staticmethod
    def get_cr_with_details(cr_id: str) -> ChangeRequest:
        """
        Get change request with optimized database queries.
        Prefetches related objects to minimize database hits.
        """
        try:
            cr = ChangeRequest.objects.select_related(
                'created_by',
                'creator_designation',
                'region',
                'cost_center',
                'new_profile',
                'new_profile__designation',
                'new_profile__section',
                'new_profile__cost_center',
                'new_profile__district',
                'new_profile__region',
                'profile_change',
                'profile_change__user',
                'profile_change__user__designation',
                'profile_change__user__section',
                'profile_change__user__cost_center',
                'profile_change__user__district',
                'profile_change__user__region',
                'profile_deactivation',
                'profile_deactivation__user',
                'profile_deactivation__user__designation',
                'profile_deactivation__user__section',
                'profile_deactivation__user__cost_center',
                'profile_deactivation__user__district',
                'profile_deactivation__user__region',
            ).prefetch_related(
                'crapproval_set',
                'crapproval_set__approver',
                'crapproval_set__approver_role',
            ).get(cr_id=cr_id)
            
            return cr
        except ChangeRequest.DoesNotExist:
            logger.error(f"Change request not found: {cr_id}")
            raise
        except Exception as e:
            logger.error(f"Error fetching change request {cr_id}: {str(e)}")
            raise
    
    @staticmethod
    def validate_cr_data(cr_type: str, data: Dict[str, Any]) -> List[str]:
        """
        Validate change request data based on type.
        Returns list of error messages (empty if valid).
        """
        errors = []
        
        # Common validation
        change_reason = data.get('change_reason', '').strip()
        change_description = data.get('change_description', '').strip()
        originator_company = data.get('originator_company', '').strip()
        originator_site = data.get('originator_site', '').strip()
        date_resolution_required = data.get('date_resolution_required', '').strip()
        
        if not change_reason:
            errors.append(ERROR_MESSAGES.get('REQUIRED_FIELD_MISSING', 'Change reason is required'))
        elif len(change_reason) > MAX_REASON_LENGTH:
            errors.append(f"Change reason exceeds maximum length of {MAX_REASON_LENGTH} characters")
        
        if not change_description:
            errors.append(ERROR_MESSAGES.get('REQUIRED_FIELD_MISSING', 'Change description is required'))
        elif len(change_description) > MAX_DESCRIPTION_LENGTH:
            errors.append(f"Change description exceeds maximum length of {MAX_DESCRIPTION_LENGTH} characters")
        
        if not originator_company:
            errors.append("Originator company is required")
        if not originator_site:
            errors.append("Originator site is required")
        if not date_resolution_required:
            errors.append("Date resolution required is required")
        else:
            try:
                datetime.strptime(date_resolution_required, "%Y-%m-%d")
            except ValueError:
                errors.append("Date resolution required must be in YYYY-MM-DD format")
        
        return errors
    
    @staticmethod
    def validate_new_profile_data(data: Dict[str, Any]) -> List[str]:
        """Validate new profile specific data"""
        errors = []
        
        username = data.get('username', '').strip()
        first_name = data.get('first_name', '').strip()
        last_name = data.get('last_name', '').strip()
        email = data.get('email', '').strip()
        ec_number = (data.get('np_ec_number') or data.get('ec_number') or '').strip()
        job_title = (data.get('np_job_title') or data.get('job_title') or '').strip()
        company = (data.get('np_company') or data.get('company') or '').strip()
        
        if not username:
            errors.append("Username is required")
        elif len(username) > 15:
            errors.append("Username exceeds maximum length of 15 characters")
        
        if not first_name:
            errors.append("First name is required")
        elif len(first_name) > 100:
            errors.append("First name exceeds maximum length of 100 characters")
        
        if not last_name:
            errors.append("Last name is required")
        elif len(last_name) > 100:
            errors.append("Last name exceeds maximum length of 100 characters")
        
        if email:
            try:
                validate_email(email)
            except ValidationError:
                errors.append("Invalid email format")
        
        if not ec_number:
            errors.append("EC number is required")
        if not job_title:
            errors.append("Job title is required")
        if not company:
            errors.append("Company is required")
        
        return errors
    
    @staticmethod
    @transaction.atomic
    def create_new_profile_cr(data: Dict[str, Any], user: UserProfile) -> ChangeRequest:
        """Create a new profile change request"""
        # Create NewProfile instance
        region = Regions.objects.filter(id=user.region.id).first() if user.region else None
        cost_center = CostCenter.objects.filter(id=data.get('cost_center')).first() if data.get('cost_center') else None
        designation = Designations.objects.filter(id=data.get('designation')).first() if data.get('designation') else None
        section = Sections.objects.filter(id=data.get('section')).first() if data.get('section') else None
        district = Districts.objects.filter(id=data.get('district')).first() if data.get('district') else None
        
        # Parse optional dates
        parsed_date_resolution = None
        if data.get('date_resolution_required'):
            parsed_date_resolution = datetime.strptime(data['date_resolution_required'], "%Y-%m-%d").date()
        
        parsed_training_date = None
        training_date_value = data.get('np_training_date') or data.get('training_date')
        if training_date_value:
            parsed_training_date = datetime.strptime(training_date_value, "%Y-%m-%d").date()
        
        new_profile = NewProfile(
            username=data.get('username'),
            ec_number=data.get('np_ec_number') or data.get('ec_number'),
            first_name=data.get('first_name'),
            last_name=data.get('last_name'),
            email=data.get('email'),
            job_title=data.get('np_job_title') or data.get('job_title'),
            company=data.get('np_company') or data.get('company'),
            designation=designation,
            section=section,
            cost_center=cost_center,
            district=district,
            region=region,
            depot_office=data.get('np_depot_office') or data.get('depot_office'),
            sub_module=data.get('np_sub_module') or data.get('sub_module'),
            training_date=parsed_training_date,
            training_confirmation_link=data.get('np_training_confirmation_link') or data.get('training_confirmation_link'),
            roles_to_action=data.get('roles_to_action')
        )
        new_profile.save()
        
        # Create ChangeRequest
        cr_id = "CR-" + timezone.now().strftime("%Y%m%d%I%M%S")
        change_request = ChangeRequest(
            cr_id=cr_id,
            application=data.get('for_application'),
            change_type="New Profile",
            new_profile=new_profile,
            change_description=data.get('change_description'),
            change_reason=data.get('change_reason'),
            originator_company=data.get('originator_company'),
            originator_site=data.get('originator_site'),
            date_resolution_required=parsed_date_resolution,
            creator_designation=user.designation,
            created_by=user,
            region=region,
            cost_center=user.cost_center,
            created_at=timezone.now()
        )
        change_request.save()
        
        logger.info(f"Created new profile change request: {cr_id}")
        return change_request
    
    @staticmethod
    @transaction.atomic
    def create_profile_modification_cr(data: Dict[str, Any], user: UserProfile) -> ChangeRequest:
        """Create a profile modification change request"""
        delegator_username = data.get('delegator')
        delegatee_username = data.get('delegatee')
        
        delegator = UserProfile.objects.filter(username=delegator_username).first()
        delegatee = UserProfile.objects.filter(username=delegatee_username).first()
        
        if not delegator:
            raise ValueError(f"Delegator '{delegator_username}' not found")
        if not delegatee:
            raise ValueError(f"Delegatee '{delegatee_username}' not found")
        
        # Parse optional originator metadata
        parsed_date_resolution = None
        if data.get('date_resolution_required'):
            parsed_date_resolution = datetime.strptime(data['date_resolution_required'], "%Y-%m-%d").date()
        
        # Create ProfileChange instance
        profile_change = ProfileChange(
            user=delegatee,
            application=data.get('for_application'),
            roles_to_action=data.get('roles_to_action'),
            change_date=timezone.now(),
            changed_by=user,
            current_user_id=data.get('mod_current_user_id') or data.get('mod_ec_number') or data.get('current_user_id'),
            ec_number=data.get('mod_ec_number') or data.get('ec_number'),
            reason_assign=data.get('mod_reason_assign') or data.get('reason_assign'),
            reason_remove=data.get('mod_reason_remove') or data.get('reason_remove'),
            correspondence_link=data.get('mod_correspondence_link') or data.get('correspondence_link'),
            status='PENDING'
        )
        profile_change.save()
        
        # Create ChangeRequest
        cr_id = "CR-" + timezone.now().strftime("%Y%m%d%I%M%S")
        change_type = data.get('change_type', 'PERMANENT')
        
        if change_type == 'TEMPORARY':
            change_type_name = "Temporary Role Delegation"
        else:
            change_type_name = "Profile Modification"
        
        change_request = ChangeRequest(
            cr_id=cr_id,
            application=data.get('for_application'),
            change_type=change_type_name,
            profile_change=profile_change,
            change_description=data.get('change_description'),
            change_reason=data.get('change_reason'),
            originator_company=data.get('originator_company'),
            originator_site=data.get('originator_site'),
            date_resolution_required=parsed_date_resolution,
            creator_designation=user.designation,
            created_by=user,
            region=user.region,
            cost_center=user.cost_center,
            created_at=timezone.now()
        )
        change_request.save()
        
        logger.info(f"Created profile modification change request: {cr_id}")
        return change_request
    
    @staticmethod
    @transaction.atomic
    def create_profile_deactivation_cr(data: Dict[str, Any], user: UserProfile) -> ChangeRequest:
        """Create a profile deactivation change request"""
        username_to_deactivate = data.get('username') or data.get('user_profile')
        user_to_deactivate = UserProfile.objects.filter(username=username_to_deactivate).first()
        
        if not user_to_deactivate:
            raise ValueError(f"User '{username_to_deactivate}' not found")
        
        parsed_date_resolution = None
        if data.get('date_resolution_required'):
            parsed_date_resolution = datetime.strptime(data['date_resolution_required'], "%Y-%m-%d").date()
        
        effective_start = None
        if data.get('deactivation_effective_start'):
            naive_start = datetime.strptime(data['deactivation_effective_start'], "%Y-%m-%dT%H:%M")
            effective_start = timezone.make_aware(naive_start, timezone.get_current_timezone())
        
        reactivation_date = None
        if data.get('deactivation_reactivation_date'):
            naive_reactivation = datetime.strptime(data['deactivation_reactivation_date'], "%Y-%m-%dT%H:%M")
            reactivation_date = timezone.make_aware(naive_reactivation, timezone.get_current_timezone())
        
        # Create ProfileDeactivation instance
        profile_deactivation = ProfileDeactivation(
            user=user_to_deactivate,
            application=data.get('for_application'),
            deactivation_date=effective_start or timezone.now(),
            effective_start_date=effective_start,
            reactivation_date=reactivation_date,
            deactivation_reason=data.get('deactivation_reason'),
            correspondence_link=data.get('deactivation_correspondence_link'),
            deactivated_by=user
        )
        profile_deactivation.save()
        
        # Create ChangeRequest
        cr_id = "CR-" + timezone.now().strftime("%Y%m%d%I%M%S")
        change_request = ChangeRequest(
            cr_id=cr_id,
            application=data.get('for_application'),
            change_type="Profile Deactivation",
            profile_deactivation=profile_deactivation,
            change_description=data.get('change_description'),
            change_reason=data.get('change_reason'),
            originator_company=data.get('originator_company'),
            originator_site=data.get('originator_site'),
            date_resolution_required=parsed_date_resolution,
            creator_designation=user.designation,
            created_by=user,
            region=user.region,
            cost_center=user.cost_center,
            created_at=timezone.now()
        )
        change_request.save()
        
        logger.info(f"Created profile deactivation change request: {cr_id}")
        return change_request


class CRTypeHandler:
    """Base class for change request type-specific handlers"""
    
    @staticmethod
    def get_handler(change_type: str) -> 'CRTypeHandler':
        """Factory method to get appropriate handler for CR type"""
        from .cr_type_handlers import (
            NewProfileHandler, 
            ProfileModificationHandler, 
            ProfileDeactivationHandler
        )
        
        handlers = {
            'New Profile': NewProfileHandler,
            'Profile Modification': ProfileModificationHandler,
            'Profile Deactivation': ProfileDeactivationHandler,
            'Temporary Role Delegation': ProfileModificationHandler,  # Uses same handler
        }
        
        handler_class = handlers.get(change_type)
        if not handler_class:
            logger.error(f"Unknown change request type: {change_type}")
            raise ValueError(f"Unknown change request type: {change_type}")
        
        return handler_class()
    
    def get_profile_data(self, cr: ChangeRequest) -> Dict[str, Any]:
        """Get profile data specific to CR type (to be overridden)"""
        raise NotImplementedError("Subclasses must implement get_profile_data")
    
    def build_context(self, cr: ChangeRequest, user: UserProfile, 
                      permissions: Dict[str, bool], approval_status: Dict[str, Any]) -> Dict[str, Any]:
        """Build template context for this CR type"""
        from .context_builder import ContextBuilder
        
        # Get profile data
        profile_data = self.get_profile_data(cr)
        
        # Build base context
        base_context = ContextBuilder.get_base_template_context(user, cr)
        
        # Build CR context
        cr_context = {
            "user": profile_data,
            "cr_id": cr.cr_id,
            "change_reason": cr.change_reason,
            "change_description": cr.change_description,
            "application": cr.application,
            "created_by": cr.created_by.get_full_name(),
            "creator_designation": cr.creator_designation.description if cr.creator_designation else "",
            "created_at": cr.created_at,
            "change_type": cr.change_type,
        }
        
        # Merge all contexts
        context = {**base_context}
        context.update({
            "section_head_allowed": permissions.get('section_head_allowed', False),
            "it_section_head_allowed": permissions.get('it_section_head_allowed', False),
            "section_head_awaiting_action": approval_status.get('section_head_awaiting_action', True),
            "it_section_head_awaiting_action": approval_status.get('it_section_head_awaiting_action', True),
            "cr_approvals": approval_status.get('cr_approvals', []),
            "cr": cr_context,
        })
        
        return context

