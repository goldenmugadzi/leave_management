"""
Django management command to populate IMS processes.
Usage: python manage.py populate_ims_processes
"""

from django.core.management.base import BaseCommand, CommandError
from django.db import transaction
from process_management.ims_importer import IMSDocumentImporter


class Command(BaseCommand):
    help = 'Populate database with predefined IMS processes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force update existing processes',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('Starting IMS processes population...')
        )
        
        try:
            importer = IMSDocumentImporter()
            result = importer.populate_predefined_ims_processes()
            
            if result['success']:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully populated IMS processes:\n"
                        f"- Created: {result['processes_created']}\n"
                        f"- Updated: {result['processes_updated']}\n"
                        f"- Errors: {result['errors_count']}"
                    )
                )
                
                if options['verbose']:
                    self.stdout.write("\nImport Log:")
                    for log_entry in result['import_log']:
                        self.stdout.write(f"  - {log_entry}")
                    
                    if result['error_log']:
                        self.stdout.write("\nError Log:")
                        for error in result['error_log']:
                            self.stdout.write(self.style.ERROR(f"  - {error}"))
                            
            else:
                self.stdout.write(
                    self.style.ERROR(f"Population failed: {result['error']}")
                )
                if result['error_log']:
                    for error in result['error_log']:
                        self.stdout.write(self.style.ERROR(f"  - {error}"))
                
        except Exception as e:
            raise CommandError(f'Population failed: {e}')