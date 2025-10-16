from django.core.management.base import BaseCommand
from django.utils import timezone
from substation_inspections.services import InspectionScheduler
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    help = 'Generate monthly inspection reports for all active substations'

    def add_arguments(self, parser):
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be created without actually creating inspections',
        )
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force creation even if inspections already exist for this month',
        )

    def handle(self, *args, **options):
        dry_run = options['dry_run']
        force = options['force']
        
        self.stdout.write(
            self.style.SUCCESS('Starting monthly inspection generation...')
        )
        
        try:
            if dry_run:
                self.stdout.write(
                    self.style.WARNING('DRY RUN MODE - No inspections will be created')
                )
                # Show what would be created
                from substation_inspections.models import MonthlyInspectionSchedule, MonthlyInspectionReport
                from django.utils import timezone
                
                current_date = timezone.now().date()
                current_month = current_date.month
                current_year = current_date.year
                
                schedules = MonthlyInspectionSchedule.objects.filter(
                    is_active=True,
                    frequency='monthly'
                ).select_related('substation', 'assigned_inspector')
                
                would_create = 0
                already_exists = 0
                
                for schedule in schedules:
                    existing_inspection = MonthlyInspectionReport.objects.filter(
                        substation=schedule.substation,
                        inspection_date__year=current_year,
                        inspection_date__month=current_month
                    ).first()
                    
                    if existing_inspection:
                        already_exists += 1
                        self.stdout.write(
                            f"  - {schedule.substation.substation_code}: Already exists ({existing_inspection.report_number})"
                        )
                    else:
                        would_create += 1
                        self.stdout.write(
                            f"  - {schedule.substation.substation_code}: Would create (Inspector: {schedule.assigned_inspector.get_full_name() if schedule.assigned_inspector else 'Unassigned'})"
                        )
                
                self.stdout.write(
                    self.style.SUCCESS(f'Would create {would_create} inspections, {already_exists} already exist')
                )
            else:
                created_count = InspectionScheduler.generate_monthly_inspections()
                self.stdout.write(
                    self.style.SUCCESS(f'Successfully created {created_count} monthly inspections')
                )
                
                # Update substation inspection dates
                updated_count = InspectionScheduler.update_substation_inspection_dates()
                self.stdout.write(
                    self.style.SUCCESS(f'Updated inspection dates for {updated_count} substations')
                )
                
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error generating inspections: {str(e)}')
            )
            logger.error(f'Error in generate_inspections command: {str(e)}')
            raise
