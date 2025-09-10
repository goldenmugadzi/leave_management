from django.core.management.base import BaseCommand
from substation_inspections.services import InspectionAssignmentService
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Automatically assign unassigned inspections to inspectors based on schedules'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what assignments would be made without actually making them',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        
        self.stdout.write(
            self.style.SUCCESS('Starting automatic inspection assignment...')
        )
        
        try:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN MODE - No assignments will be made')
                )
                # Show what would be assigned
                from substation_inspections.models import MonthlyInspectionReport, MonthlyInspectionSchedule
                
                unassigned_inspections = MonthlyInspectionReport.objects.filter(
                    status='scheduled',
                    inspector__isnull=True
                ).select_related('substation')
                
                would_assign = 0
                no_schedule = 0
                
                self.stdout.write(f'Found {unassigned_inspections.count()} unassigned inspections:')
                
                for inspection in unassigned_inspections:
                    schedule = MonthlyInspectionSchedule.objects.filter(
                        substation=inspection.substation,
                        is_active=True,
                        frequency='monthly'
                    ).first()
                    
                    if schedule and schedule.assigned_inspector:
                        would_assign += 1
                        self.stdout.write(
                            f"  - {inspection.substation.substation_code}: Would assign to {schedule.assigned_inspector.get_full_name()}"
                        )
                    else:
                        no_schedule += 1
                        self.stdout.write(
                            f"  - {inspection.substation.substation_code}: No schedule or inspector found"
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Would assign {would_assign} inspections, {no_schedule} have no schedule')
                )
            else:
                assigned_count = InspectionAssignmentService.auto_assign_inspections()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully assigned {assigned_count} inspections')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error in auto assignment: {str(e)}')
            )
            logger.error(f'Error in auto_assign command: {str(e)}')
            raise
