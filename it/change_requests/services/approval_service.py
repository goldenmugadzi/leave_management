"""
Approval Service Layer

Handles approval workflow logic, permissions, and change request application.
"""

import json
import logging
from typing import Dict, Optional, Tuple, Any
from datetime import datetime
from django.db import transaction
from django.utils import timezone

from it.change_requests.models import ChangeRequest, CRApproval, NewProfile, ProfileChange, ProfileDeactivation
from it.users.models import UserProfile, Roles, Application, Responsibilities, RoleDelegation, DelegationNotification
from it.change_requests.constants import APPLICATION_NAMES, WARNING_MESSAGES, LOG_MESSAGES

logger = logging.getLogger(__name__)


class ApprovalWorkflow:
    """Manages approval workflow state and transitions"""
    
    WORKFLOW_STEPS = ['section_head', 'it_section_head']
    
    @staticmethod
    def get_current_step(cr: ChangeRequest) -> str:
        """Determine current workflow step for a change request"""
        approvals = CRApproval.objects.filter(cr_id=cr)
        
        sh_approval = approvals.filter(approver_role__role='section_head').first()
        it_approval = approvals.filter(approver_role__role='it_section_head').first()
        
        if not sh_approval:
            return 'section_head'
        elif sh_approval.approval_status == False:
            return 'rejected_by_sh'
        elif not it_approval:
            return 'it_section_head'
        elif it_approval.approval_status == False:
            return 'rejected_by_it'
        else:
            return 'complete'
    
    @staticmethod
    def can_user_approve(cr: ChangeRequest, user: UserProfile, role: str) -> bool:
        """Check if user can approve at current workflow step"""
        if cr.created_by == user:
            logger.warning(f"User {user.username} attempted to approve their own change request {cr.cr_id}")
            return False
        
        current_step = ApprovalWorkflow.get_current_step(cr)
        logger.info(
            f"Evaluating approval permission | CR={cr.cr_id} | user={user.username} | "
            f"user_role={role} | workflow_step={current_step}"
        )
        
        if current_step == 'section_head' and role == 'section_head':
            # Check if user is section head for this cost center
            user_role = user.get_user_role_for_application("change_requests")
            if not user_role or user_role.role != 'section_head':
                logger.warning(
                    f"Approval denied | CR={cr.cr_id} | user={user.username} | "
                    f"reason=missing_or_mismatched_section_head_role"
                )
                return False
            
            user_responsibilities = Responsibilities.objects.filter(
                user=user, 
                role=user_role
            ).first()
            
            if not user_responsibilities:
                logger.warning(
                    f"Approval denied | CR={cr.cr_id} | user={user.username} | "
                    f"reason=no_responsibilities_record"
                )
                return False
            
            if not cr.cost_center:
                logger.warning(
                    f"Approval denied | CR={cr.cr_id} | user={user.username} | "
                    f"reason=cr_missing_cost_center"
                )
                return False
            
            if cr.cost_center in user_responsibilities.cost_centers.all():
                return True
            
            logger.warning(
                f"Approval denied | CR={cr.cr_id} | user={user.username} | "
                f"reason=cost_center_mismatch | cr_cost_center={cr.cost_center_id}"
            )
            return False
        
        elif current_step == 'it_section_head' and role == 'it_section_head':
            # Check if user is IT section head
            user_role = user.get_user_role_for_application("change_requests")
            if user_role and user_role.role == 'it_section_head':
                return True
            
            logger.warning(
                f"Approval denied | CR={cr.cr_id} | user={user.username} | "
                f"reason=missing_or_mismatched_it_section_head_role"
            )
            return False
        
        logger.warning(
            f"Approval denied | CR={cr.cr_id} | user={user.username} | "
            f"reason=workflow_step_role_mismatch | workflow_step={current_step} | user_role={role}"
        )
        return False
    
    @staticmethod
    def get_next_approver(cr: ChangeRequest) -> Optional[UserProfile]:
        """Get next approver in the workflow"""
        current_step = ApprovalWorkflow.get_current_step(cr)
        
        try:
            application = Application.objects.filter(name="change_requests").first()
            
            if current_step == 'section_head':
                # Get section head for this cost center
                section_head_role = Roles.objects.filter(
                    role="section_head", 
                    app_id=application.id
                ).first()
                
                if section_head_role and cr.cost_center:
                    approver_responsibilities = Responsibilities.objects.filter(
                        role=section_head_role,
                        cost_centers__in=[cr.cost_center]
                    ).first()
                    return approver_responsibilities.user if approver_responsibilities else None
            
            elif current_step == 'it_section_head':
                # Get IT section head
                it_section_head_role = Roles.objects.filter(
                    role="it_section_head", 
                    app_id=application.id
                ).first()
                
                if it_section_head_role and cr.cost_center:
                    approver_responsibilities = Responsibilities.objects.filter(
                        role=it_section_head_role,
                        cost_centers__in=[cr.cost_center]
                    ).first()
                    return approver_responsibilities.user if approver_responsibilities else None
        
        except Exception as e:
            logger.error(f"Error getting next approver for CR {cr.cr_id}: {str(e)}")
        
        return None


class ApprovalService:
    """Service for handling approval operations"""
    
    @staticmethod
    def get_approval_status(cr: ChangeRequest) -> Dict[str, Any]:
        """
        Get approval status and determine what actions are awaiting.
        Returns dict with approval status flags.
        """
        cr_approvals = CRApproval.objects.filter(cr_id=cr).select_related(
            'approver', 'approver_role'
        ).all()
        
        section_head_awaiting_action = True
        it_section_head_awaiting_action = True
        
        for approval in cr_approvals:
            if approval.approver_role.role == "section_head":
                section_head_awaiting_action = False
                if approval.approval_status == False:
                    it_section_head_awaiting_action = False
            if approval.approver_role.role == "it_section_head":
                it_section_head_awaiting_action = False
        
        return {
            'cr_approvals': cr_approvals,
            'section_head_awaiting_action': section_head_awaiting_action,
            'it_section_head_awaiting_action': it_section_head_awaiting_action
        }
    
    @staticmethod
    def get_user_permissions(user: UserProfile, cr: ChangeRequest) -> Dict[str, bool]:
        """Get user permissions for a change request"""
        permissions = {
            'section_head_allowed': False,
            'it_section_head_allowed': False,
            'can_delete': False,
            'can_edit': False,
        }
        
        user_role = user.get_user_role_for_application("change_requests")
        
        if user_role:
            if user_role.role == "section_head":
                # Check if user is section head for this cost center
                user_responsibilities = Responsibilities.objects.filter(
                    user=user, 
                    role=user_role
                ).first()
                
                if user_responsibilities and cr.cost_center:
                    if cr.cost_center in user_responsibilities.cost_centers.all():
                        permissions['section_head_allowed'] = True
            
            elif user_role.role == "it_section_head":
                permissions['it_section_head_allowed'] = True
        
        # Check delete/edit permissions
        if cr.created_by == user:
            permissions['can_delete'] = True
            permissions['can_edit'] = True
        
        return permissions
    
    @staticmethod
    @transaction.atomic
    def approve_cr(cr: ChangeRequest, user: UserProfile) -> Tuple[bool, str]:
        """
        Approve a change request.
        Returns (success, message).
        """
        try:
            user_role_obj = user.get_user_role_for_application("change_requests")
            if not user_role_obj:
                logger.warning(
                    f"Approval attempt without role | CR={cr.cr_id} | user={user.username}"
                )
                return False, "Error. Please check your Change Request role"
            
            user_role = user_role_obj.role
            
            # Check if user can approve at current step
            if not ApprovalWorkflow.can_user_approve(cr, user, user_role):
                return False, "You don't have permission to approve this request at this stage"
            
            # Check if already approved by this role
            existing_approval = CRApproval.objects.filter(
                cr_id=cr,
                approver_role__role=user_role
            ).first()
            
            if existing_approval:
                return False, "This request has already been approved by your role"
            
            # Create approval record
            cr_approval = CRApproval(
                cr_id=cr,
                approver=user,
                approver_role=user_role_obj,
                approval_status=True,
                approval_date=timezone.now()
            )
            cr_approval.save()
            
            # Update change request status
            if user_role == 'section_head':
                cr.status = 'APPROVED'
            elif user_role == 'it_section_head':
                cr.status = 'APPROVED'
            
            cr.save()
            
            logger.info(f"Change request {cr.cr_id} approved by {user.username} ({user_role})")
            return True, "Change Request approved successfully"
        
        except Exception as e:
            logger.error(f"Error approving change request {cr.cr_id}: {str(e)}")
            return False, f"Error approving change request: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def reject_cr(cr: ChangeRequest, user: UserProfile, reason: str) -> Tuple[bool, str]:
        """
        Reject a change request.
        Returns (success, message).
        """
        try:
            user_role_obj = user.get_user_role_for_application("change_requests")
            if not user_role_obj:
                return False, "Error. Please check your Change Request role"
            
            # Create rejection record
            cr_approval = CRApproval(
                cr_id=cr,
                approver=user,
                approver_role=user_role_obj,
                approval_status=False,
                comment=reason,
                approval_date=timezone.now()
            )
            cr_approval.save()
            
            # Update change request status
            cr.status = 'REJECTED'
            cr.save()
            
            logger.info(f"Change request {cr.cr_id} rejected by {user.username}")
            return True, "Change Request rejected successfully"
        
        except Exception as e:
            logger.error(f"Error rejecting change request {cr.cr_id}: {str(e)}")
            return False, f"Error rejecting change request: {str(e)}"
    
    @staticmethod
    @transaction.atomic
    def apply_cr(cr: ChangeRequest, user: UserProfile, roles_actions: Optional[str] = None) -> Tuple[bool, str]:
        """
        Apply/implement a change request.
        Returns (success, message).
        """
        try:
            user_role_obj = user.get_user_role_for_application("change_requests")
            if not user_role_obj or user_role_obj.role != 'it_section_head':
                return False, "Only IT section heads can apply change requests"
            
            # Check if section head has approved
            sh_approval = CRApproval.objects.filter(
                cr_id=cr,
                approver_role__role='section_head',
                approval_status=True
            ).first()
            
            if not sh_approval:
                return False, "Cannot apply - section head approval required first"
            
            # Validate roles_actions if required
            has_roles_to_assign = ApprovalApplicationService.check_roles_required(cr)
            
            if has_roles_to_assign and not roles_actions:
                return False, "Please enter the roles implemented"
            
            if not roles_actions and not has_roles_to_assign:
                roles_actions = "No roles applied - no roles were specified for assignment"
            
            # Save roles_actions to appropriate model
            if cr.change_type == "New Profile" and cr.new_profile:
                cr.new_profile.roles_actions = roles_actions
                cr.new_profile.save()
            elif cr.change_type in ["Profile Modification", "Temporary Role Delegation"] and cr.profile_change:
                cr.profile_change.roles_actions = roles_actions
                cr.profile_change.save()
            
            # Apply the change request
            success, message = ApprovalApplicationService.apply_change_request(cr)
            
            if not success:
                return False, message
            
            # Create IT approval record
            cr_approval = CRApproval(
                cr_id=cr,
                approver=user,
                approver_role=user_role_obj,
                approval_status=True,
                approval_date=timezone.now()
            )
            cr_approval.save()
            
            logger.info(f"Change request {cr.cr_id} applied by {user.username}")
            return True, message
        
        except Exception as e:
            logger.error(f"Error applying change request {cr.cr_id}: {str(e)}")
            return False, f"Error applying change request: {str(e)}"


class ApprovalApplicationService:
    """Service for applying/implementing change requests"""
    
    @staticmethod
    def check_roles_required(cr: ChangeRequest) -> bool:
        """Check if CR requires roles to be assigned"""
        if cr.change_type == "New Profile" and cr.new_profile:
            return bool(
                cr.new_profile.roles_to_action and 
                cr.new_profile.roles_to_action.strip() and 
                cr.new_profile.roles_to_action.strip() not in ['No roles or designations specified', 'None', '']
            )
        elif cr.change_type in ["Profile Modification", "Temporary Role Delegation"] and cr.profile_change:
            return bool(
                cr.profile_change.roles_to_action and 
                cr.profile_change.roles_to_action.strip() and 
                cr.profile_change.roles_to_action.strip() not in ['No roles or designations specified', 'None', '']
            )
        return False
    
    @staticmethod
    @transaction.atomic
    def apply_change_request(cr: ChangeRequest) -> Tuple[bool, str]:
        """Apply the appropriate change based on CR type"""
        if cr.change_type == "New Profile":
            return ApprovalApplicationService.apply_new_profile(cr)
        elif cr.change_type == "Profile Modification":
            return ApprovalApplicationService.apply_profile_modification(cr)
        elif cr.change_type == "Profile Deactivation":
            return ApprovalApplicationService.apply_profile_deactivation(cr)
        elif cr.change_type == "Temporary Role Delegation":
            return ApprovalApplicationService.apply_delegation(cr)
        else:
            return False, f"Unknown change request type: {cr.change_type}"
    
    @staticmethod
    def apply_new_profile(cr: ChangeRequest) -> Tuple[bool, str]:
        """Apply new profile change request"""
        try:
            if cr.application == APPLICATION_NAMES.get('BUSINESS_EXCELLENCE', 'BUSINESS EXCELLENCE'):
                new_profile = cr.new_profile
                
                # Create actual UserProfile from NewProfile
                user_profile = UserProfile.objects.create(
                    username=new_profile.username,
                    first_name=new_profile.first_name,
                    last_name=new_profile.last_name,
                    email=new_profile.email,
                    designation=new_profile.designation,
                    section=new_profile.section,
                    cost_center=new_profile.cost_center,
                    district=new_profile.district,
                    region=new_profile.region,
                    is_active=True
                )
                
                # Assign roles from NewProfile
                if new_profile.roles.exists():
                    user_profile.roles.set(new_profile.roles.all())
                
                logger.info(f"Created UserProfile {user_profile.username} from NewProfile CR {cr.cr_id}")
            
            # Update status
            cr.status = 'IMPLEMENTED'
            cr.save()
            
            return True, "Change request applied successfully"
        
        except Exception as e:
            logger.error(f"Error applying new profile CR {cr.cr_id}: {str(e)}")
            return False, f"Error applying change: {str(e)}"
    
    @staticmethod
    def apply_profile_modification(cr: ChangeRequest) -> Tuple[bool, str]:
        """Apply profile modification change request"""
        try:
            if cr.application == APPLICATION_NAMES.get('BUSINESS_EXCELLENCE', 'BUSINESS EXCELLENCE'):
                profile_change = cr.profile_change
                user = profile_change.user
                
                # Apply role additions
                if profile_change.role_to_assign.exists():
                    user.roles.add(*profile_change.role_to_assign.all())
                
                # Apply role removals
                if profile_change.role_to_remove.exists():
                    user.roles.remove(*profile_change.role_to_remove.all())
                
                # Update profile change status
                profile_change.status = 'IMPLEMENTED'
                profile_change.save()
                
                logger.info(
                    f"Applied profile modification CR {cr.cr_id} - "
                    f"assign_reason='{profile_change.reason_assign}', "
                    f"remove_reason='{profile_change.reason_remove}'"
                )
                
                logger.info(f"Applied profile changes for {user.username} from CR {cr.cr_id}")
            
            # Update CR status
            cr.status = 'IMPLEMENTED'
            cr.save()
            
            return True, "Change request applied successfully"
        
        except Exception as e:
            logger.error(f"Error applying profile modification CR {cr.cr_id}: {str(e)}")
            return False, f"Error applying change: {str(e)}"
    
    @staticmethod
    def apply_profile_deactivation(cr: ChangeRequest) -> Tuple[bool, str]:
        """Apply profile deactivation change request"""
        try:
            profile_deactivation = cr.profile_deactivation
            user = profile_deactivation.user
            effective_start = profile_deactivation.effective_start_date or timezone.now()
            
            if effective_start > timezone.now():
                logger.info(f"Deactivation for user {user.username} scheduled ahead of effective start {effective_start.isoformat()}. Applying immediately per approval.")
            
            # Align deactivation date with effective start
            profile_deactivation.deactivation_date = effective_start
            profile_deactivation.save(update_fields=['deactivation_date'])
            
            # Deactivate user
            user.is_active = False
            user.save()
            
            # Update CR status
            cr.status = 'IMPLEMENTED'
            cr.save()
            
            logger.info(f"Deactivated user {user.username} from CR {cr.cr_id}")
            return True, "User deactivated successfully"
        
        except Exception as e:
            logger.error(f"Error applying profile deactivation CR {cr.cr_id}: {str(e)}")
            return False, f"Error deactivating user: {str(e)}"
    
    @staticmethod
    def apply_delegation(cr: ChangeRequest) -> Tuple[bool, str]:
        """Apply temporary role delegation - creates delegation with APPROVED status"""
        try:
            profile_change = cr.profile_change
            if not profile_change:
                return False, "Profile change data not found for delegation"
            
            # Validate roles_to_action indicates this is a delegation
            if profile_change.roles_to_action != "TEMPORARY_DELEGATION":
                return False, "Not a delegation request"
            
            # Parse delegation metadata from roles_actions JSON
            if not profile_change.roles_actions:
                return False, "Delegation metadata missing"
            
            try:
                metadata = json.loads(profile_change.roles_actions)
            except json.JSONDecodeError as e:
                logger.error(f"Invalid delegation metadata JSON for CR {cr.cr_id}: {str(e)}")
                return False, "Invalid delegation metadata format"
            
            # Validate required fields
            required_fields = ['delegator_id', 'start_date', 'end_date', 'reason']
            missing_fields = [field for field in required_fields if field not in metadata]
            if missing_fields:
                return False, f"Missing required delegation fields: {', '.join(missing_fields)}"
            
            # Parse dates
            try:
                start_date = datetime.fromisoformat(metadata['start_date'])
                end_date = datetime.fromisoformat(metadata['end_date'])
            except (ValueError, TypeError) as e:
                logger.error(f"Invalid date format in delegation metadata for CR {cr.cr_id}: {str(e)}")
                return False, "Invalid date format in delegation metadata"
            
            # Validate date logic
            if end_date <= start_date:
                return False, "End date must be after start date"
            
            # Create RoleDelegation record with APPROVED status (will be activated on start_date)
            delegation = RoleDelegation.objects.create(
                delegator_id=metadata['delegator_id'],
                delegatee=profile_change.user,
                start_date=start_date,
                end_date=end_date,
                reason=metadata['reason'],
                status='APPROVED',  # Will be activated by management command on start_date
                created_by=cr.created_by
            )
            
            # Add roles to delegation
            if profile_change.role_to_assign.exists():
                delegation.roles.set(profile_change.role_to_assign.all())
            else:
                logger.warning(f"No roles assigned to delegation for CR {cr.cr_id}")
            
            # Add applications to delegation
            if cr.application:
                app = Application.objects.filter(name=cr.application).first()
                if app:
                    delegation.applications.add(app)
                else:
                    logger.warning(f"Application {cr.application} not found for CR {cr.cr_id}")
            
            # Create notification for delegatee
            DelegationNotification.objects.create(
                delegation=delegation,
                recipient=delegation.delegatee,
                notification_type='DELEGATION_APPROVED',
                message=f"Role delegation from {delegation.delegator.get_full_name()} has been approved. It will activate on {start_date.strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Create notification for delegator
            DelegationNotification.objects.create(
                delegation=delegation,
                recipient=delegation.delegator,
                notification_type='DELEGATION_APPROVED',
                message=f"Your role delegation to {delegation.delegatee.get_full_name()} has been approved. It will activate on {start_date.strftime('%Y-%m-%d %H:%M')}"
            )
            
            # Update CR status
            cr.status = 'IMPLEMENTED'
            cr.save()
            
            logger.info(f"Created delegation for CR {cr.cr_id} with status APPROVED (ID: {delegation.id})")
            return True, f"Delegation approved and scheduled to activate on {start_date.strftime('%Y-%m-%d %H:%M')}"
        
        except Exception as e:
            logger.error(f"Error applying delegation CR {cr.cr_id}: {str(e)}", exc_info=True)
            return False, f"Error applying delegation: {str(e)}"

