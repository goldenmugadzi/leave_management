from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.core.cache import cache
from .models import ComparativeSchedules, Committee, CSApproval
from it.users.models import UserProfile, Roles
from enum import Enum

class ApprovalRole(Enum):
    COMMITTEE = 'committee'
    FINANCE_MANAGER = 'finance_manager'
    GENERAL_MANAGER = 'general_manager'

class DocumentStatus(Enum):
    DRAFT = 'draft'
    COMMITTEE_PENDING = 'committee_pending'
    COMMITTEE_APPROVED = 'committee_approved'
    COMMITTEE_REJECTED = 'committee_rejected'
    FM_PENDING = 'fm_pending'
    FM_APPROVED = 'fm_approved'
    FM_REJECTED = 'fm_rejected'
    GM_PENDING = 'gm_pending'
    GM_APPROVED = 'gm_approved'
    GM_REJECTED = 'gm_rejected'
    COMPLETED = 'completed'

def get_user_permissions(user, document):
    """
    Determine user permissions for a specific document
    """
    permissions = {
        'can_view': True,
        'can_edit': False,
        'can_approve': False,
        'can_delete': False,
        'can_resubmit': False,
        'user_role': None,
        'is_creator': False,
        'is_approver': False,
        'approval_stage': None
    }
    
    # Check if user is creator
    if document.created_by == user:
        permissions['is_creator'] = True
        permissions['can_edit'] = True
        permissions['can_delete'] = document.can_be_deleted()
        permissions['can_resubmit'] = document.can_be_resubmitted()
    
    # Check if user is an approver
    user_role = get_user_approval_role(user, document)
    if user_role:
        permissions['is_approver'] = True
        permissions['can_approve'] = can_user_approve_now(user_role, document)
        permissions['user_role'] = user_role.value
        permissions['approval_stage'] = get_current_approval_stage(document)
    
    return permissions

def get_user_approval_role(user, document):
    """
    Get user's role in the approval hierarchy for this document
    """
    # Check committee membership
    committee_member = Committee.objects.filter(
        cs_id=document,
        user=user
    ).first()
    
    if committee_member:
        return ApprovalRole.COMMITTEE
    
    # Check finance manager role
    fm_role = Roles.objects.filter(
        name="Finance Manager",
        application="comparative_schedules"
    ).first()
    
    if fm_role and user.roles.filter(id=fm_role.id).exists():
        return ApprovalRole.FINANCE_MANAGER
    
    # Check general manager role
    gm_role = Roles.objects.filter(
        name="General Manager",
        application="comparative_schedules"
    ).first()
    
    if gm_role and user.roles.filter(id=gm_role.id).exists():
        return ApprovalRole.GENERAL_MANAGER
    
    return None

def can_user_approve_now(user_role, document):
    """
    Check if user can approve at the current stage
    """
    if user_role == ApprovalRole.COMMITTEE:
        # Committee can approve if document is in committee stage
        return document.status in [DocumentStatus.COMMITTEE_PENDING.value, DocumentStatus.DRAFT.value]
    
    elif user_role == ApprovalRole.FINANCE_MANAGER:
        # FM can approve if committee has approved
        return (document.status == DocumentStatus.FM_PENDING.value and 
                document.is_committee_approved())
    
    elif user_role == ApprovalRole.GENERAL_MANAGER:
        # GM can approve if FM has approved
        return (document.status == DocumentStatus.GM_PENDING.value and 
                document.is_fm_approved())
    
    return False

def get_current_approval_stage(document):
    """
    Get the current approval stage for the document
    """
    if document.status == DocumentStatus.DRAFT.value:
        return 'draft'
    elif document.status in [DocumentStatus.COMMITTEE_PENDING.value, DocumentStatus.COMMITTEE_APPROVED.value, DocumentStatus.COMMITTEE_REJECTED.value]:
        return 'committee'
    elif document.status in [DocumentStatus.FM_PENDING.value, DocumentStatus.FM_APPROVED.value, DocumentStatus.FM_REJECTED.value]:
        return 'finance_manager'
    elif document.status in [DocumentStatus.GM_PENDING.value, DocumentStatus.GM_APPROVED.value, DocumentStatus.GM_REJECTED.value]:
        return 'general_manager'
    elif document.status == DocumentStatus.COMPLETED.value:
        return 'completed'
    
    return 'unknown'

def update_document_status(document):
    """
    Update document status based on current approvals
    """
    committee_status = document.get_committee_status()
    fm_status = document.get_fm_approval_status()
    gm_status = document.get_gm_approval_status()
    
    if committee_status == 'rejected':
        document.status = DocumentStatus.COMMITTEE_REJECTED.value
    elif committee_status == 'pending':
        document.status = DocumentStatus.COMMITTEE_PENDING.value
    elif committee_status == 'approved':
        if fm_status == 'rejected':
            document.status = DocumentStatus.FM_REJECTED.value
        elif fm_status == 'pending':
            document.status = DocumentStatus.FM_PENDING.value
        elif fm_status == 'approved':
            if gm_status == 'rejected':
                document.status = DocumentStatus.GM_REJECTED.value
            elif gm_status == 'pending':
                document.status = DocumentStatus.GM_PENDING.value
            elif gm_status == 'approved':
                document.status = DocumentStatus.COMPLETED.value
    
    document.save()
    return document.status

# Add methods to ComparativeSchedules model
def is_committee_approved(self):
    """Check if all committee members have approved"""
    committee_members = Committee.objects.filter(cs_id=self)
    if not committee_members.exists():
        return False
    
    return all(member.committee_approval == "Approved" for member in committee_members)

def is_fm_approved(self):
    """Check if finance manager has approved"""
    fm_approval = CSApproval.objects.filter(
        cs_id=self,
        approver_role="finance_manager"
    ).first()
    return fm_approval and fm_approval.approval == "Approved"

def is_gm_approved(self):
    """Check if general manager has approved"""
    gm_approval = CSApproval.objects.filter(
        cs_id=self,
        approver_role="general_manager"
    ).first()
    return gm_approval and gm_approval.approval == "Approved"

def get_committee_status(self):
    """Get overall committee approval status"""
    committee_members = Committee.objects.filter(cs_id=self)
    if not committee_members.exists():
        return 'pending'
    
    approvals = [member.committee_approval for member in committee_members]
    
    if all(approval == "Approved" for approval in approvals):
        return 'approved'
    elif any(approval == "Rejected" for approval in approvals):
        return 'rejected'
    else:
        return 'pending'

def get_fm_approval_status(self):
    """Get finance manager approval status"""
    fm_approval = CSApproval.objects.filter(
        cs_id=self,
        approver_role="finance_manager"
    ).first()
    
    if not fm_approval:
        return 'pending'
    return fm_approval.approval.lower()

def get_gm_approval_status(self):
    """Get general manager approval status"""
    gm_approval = CSApproval.objects.filter(
        cs_id=self,
        approver_role="general_manager"
    ).first()
    
    if not gm_approval:
        return 'pending'
    return gm_approval.approval.lower()

def can_be_deleted(self):
    """Check if document can be deleted (no approvals yet)"""
    return self.status in [DocumentStatus.DRAFT.value, DocumentStatus.COMMITTEE_PENDING.value]

def can_be_resubmitted(self):
    """Check if document can be resubmitted (was rejected)"""
    return self.status in [
        DocumentStatus.COMMITTEE_REJECTED.value,
        DocumentStatus.FM_REJECTED.value,
        DocumentStatus.GM_REJECTED.value
    ]

# Add methods to ComparativeSchedules model
ComparativeSchedules.is_committee_approved = is_committee_approved
ComparativeSchedules.is_fm_approved = is_fm_approved
ComparativeSchedules.is_gm_approved = is_gm_approved
ComparativeSchedules.get_committee_status = get_committee_status
ComparativeSchedules.get_fm_approval_status = get_fm_approval_status
ComparativeSchedules.get_gm_approval_status = get_gm_approval_status
ComparativeSchedules.can_be_deleted = can_be_deleted
ComparativeSchedules.can_be_resubmitted = can_be_resubmitted

@login_required
def get_user_permissions_api(request, document_id):
    """
    API endpoint to get user permissions for a document
    """
    try:
        document = ComparativeSchedules.objects.get(cs_id=document_id)
        permissions = get_user_permissions(request.user, document)
        
        return JsonResponse({
            'success': True,
            'permissions': permissions
        })
    except ComparativeSchedules.DoesNotExist:
        return JsonResponse({
            'success': False,
            'error': 'Document not found'
        }, status=404)
    except Exception as e:
        return JsonResponse({
            'success': False,
            'error': str(e)
        }, status=400) 