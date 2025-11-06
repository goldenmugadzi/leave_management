"""
Notification Service Layer

Handles email notifications for change request workflow events.
"""

import logging
from typing import Optional, List
from django.template.loader import render_to_string
from django.utils import timezone

from it.change_requests.models import ChangeRequest
from it.users.models import UserProfile, Application, Roles, Responsibilities
from it.users.views import ms_exhange_send_html, ms_exhange_reset_password_html

logger = logging.getLogger(__name__)


class NotificationService:
    """Service for handling change request notifications"""
    
    @staticmethod
    def send_creation_notification(cr: ChangeRequest, request=None) -> bool:
        """
        Send notification when a change request is created.
        Notifies the section head approver.
        """
        try:
            # Get section head approver
            approver = NotificationService._get_section_head_approver(cr)
            
            if not approver:
                logger.warning(f"No section head approver found for CR {cr.cr_id}")
                return False
            
            if not approver.email:
                logger.warning(f"Section head approver {approver.username} has no email")
                return False
            
            # Determine CR type for URL
            cr_type_url = NotificationService._get_cr_type_url(cr)
            
            # Prepare email content
            email_template_name = 'registration/email.html'
            msg = f"{cr.change_type} request submitted successfully"
            type_ = f"{cr.change_type} Request"
            app_base = f"change_requests/{cr_type_url}?i={cr.cr_id}"
            
            context = {
                "email": approver.email,
                "message": msg,
                "type": type_,
                "redirect_app_base": app_base,
                "id": cr.cr_id,
                "domain": request.META.get('HTTP_HOST', '172.16.29.32:9300') if request else '172.16.29.32:9300',
                "site_name": "Zetdc Business Excellence",
                "protocol": 'https' if (request and request.is_secure()) else 'http',
            }
            
            email_html = render_to_string(email_template_name, context, request=request)
            
            # Send email
            ms_exhange_reset_password_html(
                subject=type_,
                to_recipients=[approver.email],
                cc_recipients=[],
                template=email_html,
                kwargs={"kwargs": context}
            )
            
            logger.info(f"Sent creation notification for CR {cr.cr_id} to {approver.email}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending creation notification for CR {cr.cr_id}: {str(e)}")
            return False
    
    @staticmethod
    def send_approval_notification(cr: ChangeRequest, action: str, request=None) -> bool:
        """
        Send notification when a change request is approved.
        Notifies the next approver or creator.
        """
        try:
            if 'APPROVE' in action:
                # Check who approved
                latest_approval = cr.crapproval_set.order_by('-approval_date').first()
                
                if latest_approval and latest_approval.approver_role.role == 'section_head':
                    # Section head approved, notify IT section head
                    approver = NotificationService._get_it_section_head_approver(cr)
                    
                    if approver and approver.email:
                        cr_type_url = NotificationService._get_cr_type_url(cr)
                        
                        ms_exhange_send_html(
                            "Change Request Implementation",
                            [approver.email],
                            [],
                            "emails/email_template.html",
                            {
                                "message": "Change Request Implementation",
                                "type": "Change Request Implementation",
                                "redirect_url": f"https://172.16.29.32:9300/change_requests/{cr_type_url}?i={cr.cr_id}"
                            }
                        )
                        
                        logger.info(f"Sent approval notification for CR {cr.cr_id} to IT section head")
                        return True
                
                elif latest_approval and latest_approval.approver_role.role == 'it_section_head':
                    # IT section head approved/applied, notify creator
                    if cr.created_by.email:
                        NotificationService._send_completion_notification(cr, cr.created_by)
                        return True
            
            elif 'REJECT' in action:
                # Notify creator of rejection
                if cr.created_by.email:
                    NotificationService._send_rejection_notification(cr, cr.created_by)
                    return True
            
            return False
        
        except Exception as e:
            logger.error(f"Error sending approval notification for CR {cr.cr_id}: {str(e)}")
            return False
    
    @staticmethod
    def _get_section_head_approver(cr: ChangeRequest) -> Optional[UserProfile]:
        """Get section head approver for a change request"""
        try:
            application = Application.objects.filter(name="change_requests").first()
            if not application:
                return None
            
            section_head_role = Roles.objects.filter(
                role="section_head",
                app_id=application.id
            ).first()
            
            if not section_head_role or not cr.cost_center:
                return None
            
            approver_responsibilities = Responsibilities.objects.filter(
                role=section_head_role,
                cost_centers__in=[cr.cost_center]
            ).first()
            
            return approver_responsibilities.user if approver_responsibilities else None
        
        except Exception as e:
            logger.error(f"Error getting section head approver for CR {cr.cr_id}: {str(e)}")
            return None
    
    @staticmethod
    def _get_it_section_head_approver(cr: ChangeRequest) -> Optional[UserProfile]:
        """Get IT section head approver for a change request"""
        try:
            application = Application.objects.filter(name="change_requests").first()
            if not application:
                return None
            
            it_section_head_role = Roles.objects.filter(
                role="it_section_head",
                app_id=application.id
            ).first()
            
            if not it_section_head_role or not cr.cost_center:
                return None
            
            approver_responsibilities = Responsibilities.objects.filter(
                role=it_section_head_role,
                cost_centers__in=[cr.cost_center]
            ).first()
            
            return approver_responsibilities.user if approver_responsibilities else None
        
        except Exception as e:
            logger.error(f"Error getting IT section head approver for CR {cr.cr_id}: {str(e)}")
            return None
    
    @staticmethod
    def _get_cr_type_url(cr: ChangeRequest) -> str:
        """Get URL segment based on CR type"""
        type_map = {
            'New Profile': 'new_profile_request',
            'Profile Modification': 'profile_modification_request',
            'Profile Deactivation': 'profile_deactivation_request',
            'Temporary Role Delegation': 'profile_modification_request',
        }
        return type_map.get(cr.change_type, 'view_change_request')
    
    @staticmethod
    def _send_completion_notification(cr: ChangeRequest, recipient: UserProfile) -> bool:
        """Send notification when CR is completed"""
        try:
            if not recipient.email:
                return False
            
            ms_exhange_send_html(
                "Change Request Completed",
                [recipient.email],
                [],
                "emails/email_template.html",
                {
                    "message": f"Your change request {cr.cr_id} has been completed",
                    "type": "Change Request Completed",
                    "redirect_url": f"https://172.16.29.32:9300/change_requests/change_request_index"
                }
            )
            
            logger.info(f"Sent completion notification for CR {cr.cr_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending completion notification: {str(e)}")
            return False
    
    @staticmethod
    def _send_rejection_notification(cr: ChangeRequest, recipient: UserProfile) -> bool:
        """Send notification when CR is rejected"""
        try:
            if not recipient.email:
                return False
            
            ms_exhange_send_html(
                "Change Request Rejected",
                [recipient.email],
                [],
                "emails/email_template.html",
                {
                    "message": f"Your change request {cr.cr_id} has been rejected",
                    "type": "Change Request Rejected",
                    "redirect_url": f"https://172.16.29.32:9300/change_requests/change_request_index"
                }
            )
            
            logger.info(f"Sent rejection notification for CR {cr.cr_id}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending rejection notification: {str(e)}")
            return False
    
    @staticmethod
    def send_delegation_notifications(cr: ChangeRequest, event_type: str, message: str) -> bool:
        """Send delegation-specific notifications (for delegation integration)"""
        try:
            # This is a placeholder for delegation notification logic
            # The actual implementation may vary based on delegation system requirements
            logger.info(f"Delegation notification for CR {cr.cr_id}: {event_type} - {message}")
            return True
        
        except Exception as e:
            logger.error(f"Error sending delegation notification: {str(e)}")
            return False

