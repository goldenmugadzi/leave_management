from django.db import transaction
from django.utils import timezone
from django.core.mail import send_mail
from django.template.loader import render_to_string
from django.conf import settings
from datetime import datetime, timedelta
from .models import (
    Substation, 
    MonthlyInspectionSchedule, 
    MonthlyInspectionReport,
    InspectionChecklistItem
)
import logging

logger = logging.getLogger(__name__)


class InspectionScheduler:
    """Service class for automated inspection scheduling"""
    
    @staticmethod
    def create_monthly_schedules():
        """Create monthly inspection schedules for all active substations"""
        try:
            active_substations = Substation.objects.filter(is_active=True)
            created_count = 0
            
            for substation in active_substations:
                # Check if schedule already exists
                existing_schedule = MonthlyInspectionSchedule.objects.filter(
                    substation=substation,
                    frequency='monthly',
                    is_active=True
                ).first()
                
                if not existing_schedule:
                    MonthlyInspectionSchedule.objects.create(
                        substation=substation,
                        frequency='monthly',
                        day_of_month=1,  # First day of each month
                        reminder_days_before=3,
                        escalation_days_after_due=2
                    )
                    created_count += 1
                    logger.info(f"Created monthly schedule for substation {substation.substation_code}")
            
            logger.info(f"Created {created_count} new monthly schedules")
            return created_count
            
        except Exception as e:
            logger.error(f"Error creating monthly schedules: {str(e)}")
            raise
    
    @staticmethod
    def generate_monthly_inspections():
        """Generate inspection reports for the current month"""
        try:
            current_date = timezone.now().date()
            current_month = current_date.month
            current_year = current_date.year
            
            schedules = MonthlyInspectionSchedule.objects.filter(
                is_active=True,
                frequency='monthly'
            ).select_related('substation', 'assigned_inspector')
            
            created_count = 0
            
            for schedule in schedules:
                # Check if inspection already exists for this month
                existing_inspection = MonthlyInspectionReport.objects.filter(
                    substation=schedule.substation,
                    inspection_date__year=current_year,
                    inspection_date__month=current_month
                ).first()
                
                if not existing_inspection:
                    # Calculate the inspection date for this month
                    inspection_date = current_date.replace(day=min(schedule.day_of_month, 28))
                    
                    MonthlyInspectionReport.objects.create(
                        substation=schedule.substation,
                        inspection_date=inspection_date,
                        scheduled_date=inspection_date,
                        inspector=schedule.assigned_inspector,
                        status='scheduled'
                    )
                    created_count += 1
                    logger.info(f"Created inspection for {schedule.substation.substation_code}")
            
            logger.info(f"Generated {created_count} new monthly inspections")
            return created_count
            
        except Exception as e:
            logger.error(f"Error generating monthly inspections: {str(e)}")
            raise
    
    @staticmethod
    def update_substation_inspection_dates():
        """Update last_inspection_date and next_scheduled_inspection for all substations"""
        try:
            substations = Substation.objects.filter(is_active=True)
            updated_count = 0
            
            for substation in substations:
                # Get the most recent completed inspection
                last_inspection = substation.monthly_reports.filter(
                    status='completed'
                ).order_by('-inspection_date').first()
                
                if last_inspection:
                    substation.last_inspection_date = last_inspection.inspection_date
                
                # Get the next scheduled inspection
                next_schedule = substation.inspection_schedules.filter(
                    is_active=True,
                    frequency='monthly'
                ).first()
                
                if next_schedule:
                    # Calculate next inspection date
                    current_date = timezone.now().date()
                    next_month = current_date.replace(day=1) + timedelta(days=32)
                    next_month = next_month.replace(day=1)
                    next_inspection_date = next_month.replace(day=min(next_schedule.day_of_month, 28))
                    substation.next_scheduled_inspection = next_inspection_date
                
                substation.save()
                updated_count += 1
            
            logger.info(f"Updated inspection dates for {updated_count} substations")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error updating substation inspection dates: {str(e)}")
            raise


class InspectionNotificationService:
    """Service class for inspection notifications"""
    
    @staticmethod
    def send_inspection_reminders():
        """Send reminders for upcoming inspections"""
        try:
            tomorrow = timezone.now().date() + timedelta(days=1)
            
            upcoming_inspections = MonthlyInspectionReport.objects.filter(
                inspection_date=tomorrow,
                status='scheduled'
            ).select_related('substation', 'inspector')
            
            sent_count = 0
            
            for inspection in upcoming_inspections:
                if inspection.inspector and inspection.inspector.email:
                    # Send email notification
                    InspectionNotificationService._send_inspection_reminder_email(inspection)
                    sent_count += 1
                    logger.info(f"Sent reminder for inspection {inspection.report_number}")
            
            logger.info(f"Sent {sent_count} inspection reminders")
            return sent_count
            
        except Exception as e:
            logger.error(f"Error sending inspection reminders: {str(e)}")
            raise
    
    @staticmethod
    def send_overdue_notifications():
        """Send notifications for overdue inspections"""
        try:
            overdue_date = timezone.now().date() - timedelta(days=1)
            
            overdue_inspections = MonthlyInspectionReport.objects.filter(
                inspection_date__lt=overdue_date,
                status__in=['scheduled', 'in_progress']
            ).select_related('substation', 'inspector')
            
            updated_count = 0
            sent_count = 0
            
            for inspection in overdue_inspections:
                # Update status to overdue
                inspection.status = 'overdue'
                inspection.save()
                updated_count += 1
                
                # Send escalation notification
                if inspection.inspector and inspection.inspector.email:
                    InspectionNotificationService._send_overdue_inspection_notification(inspection)
                    sent_count += 1
                    logger.info(f"Sent overdue notification for inspection {inspection.report_number}")
            
            logger.info(f"Updated {updated_count} inspections to overdue, sent {sent_count} notifications")
            return updated_count, sent_count
            
        except Exception as e:
            logger.error(f"Error sending overdue notifications: {str(e)}")
            raise
    
    @staticmethod
    def _send_inspection_reminder_email(inspection):
        """Send email reminder for upcoming inspection"""
        try:
            subject = f"Inspection Reminder: {inspection.substation.name} - {inspection.inspection_date}"
            
            context = {
                'inspection': inspection,
                'substation': inspection.substation,
                'inspector': inspection.inspector,
            }
            
            message = render_to_string('substation_inspections/emails/inspection_reminder.txt', context)
            html_message = render_to_string('substation_inspections/emails/inspection_reminder.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[inspection.inspector.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            logger.error(f"Error sending reminder email for inspection {inspection.report_number}: {str(e)}")
            raise
    
    @staticmethod
    def _send_overdue_inspection_notification(inspection):
        """Send email notification for overdue inspection"""
        try:
            subject = f"URGENT: Overdue Inspection - {inspection.substation.name}"
            
            context = {
                'inspection': inspection,
                'substation': inspection.substation,
                'inspector': inspection.inspector,
            }
            
            message = render_to_string('substation_inspections/emails/inspection_overdue.txt', context)
            html_message = render_to_string('substation_inspections/emails/inspection_overdue.html', context)
            
            send_mail(
                subject=subject,
                message=message,
                from_email=settings.DEFAULT_FROM_EMAIL,
                recipient_list=[inspection.inspector.email],
                html_message=html_message,
                fail_silently=False,
            )
            
        except Exception as e:
            logger.error(f"Error sending overdue notification for inspection {inspection.report_number}: {str(e)}")
            raise


class InspectionAssignmentService:
    """Service class for inspector assignment workflows"""
    
    @staticmethod
    def bulk_assign_inspections(inspections, inspector, notes=''):
        """Bulk assign multiple inspections to an inspector"""
        try:
            updated_count = 0
            
            with transaction.atomic():
                for inspection in inspections:
                    inspection.inspector = inspector
                    inspection.save()
                    updated_count += 1
                    
                    # Log the assignment
                    logger.info(f"Assigned inspection {inspection.report_number} to {inspector.get_full_name()}")
            
            logger.info(f"Bulk assigned {updated_count} inspections to {inspector.get_full_name()}")
            return updated_count
            
        except Exception as e:
            logger.error(f"Error in bulk assignment: {str(e)}")
            raise
    
    @staticmethod
    def auto_assign_inspections():
        """Automatically assign inspections based on schedules"""
        try:
            unassigned_inspections = MonthlyInspectionReport.objects.filter(
                status='scheduled',
                inspector__isnull=True
            ).select_related('substation')
            
            assigned_count = 0
            
            for inspection in unassigned_inspections:
                # Get the schedule for this substation
                schedule = MonthlyInspectionSchedule.objects.filter(
                    substation=inspection.substation,
                    is_active=True,
                    frequency='monthly'
                ).first()
                
                if schedule and schedule.assigned_inspector:
                    inspection.inspector = schedule.assigned_inspector
                    inspection.save()
                    assigned_count += 1
                    logger.info(f"Auto-assigned inspection {inspection.report_number} to {schedule.assigned_inspector.get_full_name()}")
            
            logger.info(f"Auto-assigned {assigned_count} inspections")
            return assigned_count
            
        except Exception as e:
            logger.error(f"Error in auto-assignment: {str(e)}")
            raise
    
    @staticmethod
    def reassign_inspection(inspection, new_inspector, reason=''):
        """Reassign an inspection to a different inspector"""
        try:
            old_inspector = inspection.inspector
            inspection.inspector = new_inspector
            inspection.save()
            
            logger.info(f"Reassigned inspection {inspection.report_number} from {old_inspector.get_full_name() if old_inspector else 'Unassigned'} to {new_inspector.get_full_name()}")
            return True
            
        except Exception as e:
            logger.error(f"Error reassigning inspection {inspection.report_number}: {str(e)}")
            raise


class InspectionMonitoringService:
    """Service class for real-time inspection monitoring"""
    
    @staticmethod
    def get_inspection_dashboard_data():
        """Get data for the inspection monitoring dashboard"""
        try:
            current_date = timezone.now().date()
            
            # Basic statistics
            stats = {
                'total_substations': Substation.objects.filter(is_active=True).count(),
                'pending_inspections': MonthlyInspectionReport.objects.filter(status='scheduled').count(),
                'in_progress_inspections': MonthlyInspectionReport.objects.filter(status='in_progress').count(),
                'completed_this_month': MonthlyInspectionReport.objects.filter(
                    status='completed',
                    inspection_date__month=current_date.month,
                    inspection_date__year=current_date.year
                ).count(),
                'overdue_inspections': MonthlyInspectionReport.objects.filter(status='overdue').count(),
            }
            
            # Recent inspections
            recent_inspections = MonthlyInspectionReport.objects.select_related(
                'substation', 'inspector'
            ).order_by('-created_at')[:10]
            
            # Upcoming inspections (next 7 days)
            upcoming_date = current_date + timedelta(days=7)
            upcoming_inspections = MonthlyInspectionReport.objects.filter(
                inspection_date__lte=upcoming_date,
                inspection_date__gte=current_date,
                status='scheduled'
            ).select_related('substation', 'inspector')
            
            # Overdue inspections
            overdue_inspections = MonthlyInspectionReport.objects.filter(
                status='overdue'
            ).select_related('substation', 'inspector').order_by('inspection_date')
            
            return {
                'stats': stats,
                'recent_inspections': recent_inspections,
                'upcoming_inspections': upcoming_inspections,
                'overdue_inspections': overdue_inspections,
            }
            
        except Exception as e:
            logger.error(f"Error getting dashboard data: {str(e)}")
            raise
    
    @staticmethod
    def get_inspector_workload():
        """Get workload statistics for each inspector"""
        try:
            from django.contrib.auth import get_user_model
            User = get_user_model()
            
            inspectors = User.objects.filter(
                monthlyinspectionreport__isnull=False
            ).distinct().values('id', 'first_name', 'last_name')
            
            workload_data = []
            
            for inspector in inspectors:
                user = User.objects.get(id=inspector['id'])
                
                workload = {
                    'inspector': user,
                    'total_assigned': MonthlyInspectionReport.objects.filter(inspector=user).count(),
                    'pending': MonthlyInspectionReport.objects.filter(
                        inspector=user, 
                        status='scheduled'
                    ).count(),
                    'in_progress': MonthlyInspectionReport.objects.filter(
                        inspector=user, 
                        status='in_progress'
                    ).count(),
                    'completed_this_month': MonthlyInspectionReport.objects.filter(
                        inspector=user,
                        status='completed',
                        inspection_date__month=timezone.now().month,
                        inspection_date__year=timezone.now().year
                    ).count(),
                    'overdue': MonthlyInspectionReport.objects.filter(
                        inspector=user, 
                        status='overdue'
                    ).count(),
                }
                workload_data.append(workload)
            
            return workload_data
            
        except Exception as e:
            logger.error(f"Error getting inspector workload: {str(e)}")
            raise
