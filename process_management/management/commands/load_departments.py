from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.db import transaction
from process_management.models import ProcessDepartment


class Command(BaseCommand):
    help = 'Load initial department data for process management'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force reload of departments even if they already exist',
        )

    def handle(self, *args, **options):
        force = options['force']
        
        try:
            with transaction.atomic():
                # Check if departments already exist
                if ProcessDepartment.objects.exists() and not force:
                    self.stdout.write(
                        self.style.WARNING(
                            'Departments already exist. Use --force to reload.'
                        )
                    )
                    return

                # Clear existing departments if force is used
                if force:
                    self.stdout.write('Clearing existing departments...')
                    ProcessDepartment.objects.all().delete()

                # Load the fixture
                self.stdout.write('Loading department data...')
                call_command('loaddata', 'initial_departments.json')

                # Verify the data was loaded
                count = ProcessDepartment.objects.count()
                self.stdout.write(
                    self.style.SUCCESS(
                        f'Successfully loaded {count} departments'
                    )
                )

                # Display loaded departments
                departments = ProcessDepartment.objects.all().order_by('order')
                self.stdout.write('\nLoaded departments:')
                for dept in departments:
                    self.stdout.write(f'  {dept.order}. {dept.name}')

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error loading departments: {str(e)}')
            )
            raise