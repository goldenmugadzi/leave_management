from django.core.management.base import BaseCommand
from substation_inspections.services import InspectionNotificationService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Send inspection reminders and overdue notifications'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reminders-only',
            action='store_true',
            help='Send only reminder notifications',
        )
        parser.add_argument(
            '--overdue-only',
            action='store_true',
            help='Send only overdue notifications',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what notifications would be sent without actually sending them',
        )

    def handle(self, *args, **options):
        reminders_only = options['reminders_only']
        overdue_only = options['overdue_only']
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('Starting notification process...')
        )
        
        try:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN MODE - No notifications will be sent')
                )
                # Show what would be sent
                from substation_inspections.models import MonthlyInspectionReport
                from django.utils import timezone
                from datetime import timedelta
                
                if not overdue_only:
                    tomorrow = timezone.now().date() + timedelta(days=1)
                    upcoming_inspections = MonthlyInspectionReport.objects.filter(
                        inspection_date=tomorrow,
                        status='scheduled'
                    ).select_related('substation', 'inspector')
                    
                    self.stdout.write(f'Would send {upcoming_inspections.count()} reminder notifications:')
                    for inspection in upcoming_inspections:
                        if inspection.inspector and inspection.inspector.email:
                            self.stdout.write(
                                f"  - {inspection.substation.name} to {inspection.inspector.get_full_name()} ({inspection.inspector.email})"
                            )
                        else:
                            self.stdout.write(
                                f"  - {inspection.substation.name} (No inspector assigned or no email)"
                            )
                
                if not reminders_only:
                    overdue_date = timezone.now().date() - timedelta(days=1)
                    overdue_inspections = MonthlyInspectionReport.objects.filter(
                        inspection_date__lt=overdue_date,
                        status__in=['scheduled', 'in_progress']
                    ).select_related('substation', 'inspector')
                    
                    self.stdout.write(f'Would send {overdue_inspections.count()} overdue notifications:')
                    for inspection in overdue_inspections:
                        if inspection.inspector and inspection.inspector.email:
                            self.stdout.write(
                                f"  - {inspection.substation.name} to {inspection.inspector.get_full_name()} ({inspection.inspector.email})"
                            )
                        else:
                            self.stdout.write(
                                f"  - {inspection.substation.name} (No inspector assigned or no email)"
                            )
            else:
                total_sent = 0
                
                if not overdue_only:
                    # Send reminders
                    sent_count = InspectionNotificationService.send_inspection_reminders()
                    total_sent += sent_count
                    self.stdout.write(
                        self.style.SUCCESS(f'Sent {sent_count} reminder notifications')
                    )
                
                if not reminders_only:
                    # Send overdue notifications
                    updated_count, sent_count = InspectionNotificationService.send_overdue_notifications()
                    total_sent += sent_count
                    self.stdout.write(
                        self.style.SUCCESS(f'Updated {updated_count} inspections to overdue, sent {sent_count} overdue notifications')
                    )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Total notifications sent: {total_sent}')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error sending notifications: {str(e)}')
            )
            logger.error(f'Error in send_notifications command: {str(e)}')
            raise
