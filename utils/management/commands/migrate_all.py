from django.core.management.base import BaseCommand, CommandError
from django.core.management import call_command
from django.conf import settings
from django.apps import apps
from pathlib import Path
import os


class Command(BaseCommand):
    help = 'Create and apply migrations for all Django apps automatically'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force migration creation even if no changes detected',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without actually doing it',
        )

    def handle(self, *args, **options):
        self.stdout.write(
            self.style.SUCCESS('🚀 Django Migration Management Command')
        )
        self.stdout.write('=' * 50)

        # Check database connection
        self.stdout.write('🔌 Checking database connection...')
        try:
            call_command('check', '--database', 'default')
            self.stdout.write(
                self.style.SUCCESS('✅ Database connection successful')
            )
        except CommandError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Database connection failed: {e}')
            )
            return

        # Create migration folders for missing apps
        self.create_migration_folders()

        # Show initial status
        self.stdout.write('\n📊 Initial migration status:')
        call_command('showmigrations')

        # Run makemigrations
        self.stdout.write('\n🔄 Running makemigrations for all apps...')
        try:
            makemigrations_args = []
            if options['force']:
                makemigrations_args.append('--force')
            if options['dry_run']:
                makemigrations_args.append('--dry-run')
            
            call_command('makemigrations', *makemigrations_args)
            self.stdout.write(
                self.style.SUCCESS('✅ makemigrations completed successfully')
            )
        except CommandError as e:
            self.stdout.write(
                self.style.ERROR(f'❌ makemigrations failed: {e}')
            )
            return

        # Run migrate
        if not options['dry_run']:
            self.stdout.write('\n🚀 Running migrate for all apps...')
            try:
                call_command('migrate')
                self.stdout.write(
                    self.style.SUCCESS('✅ migrate completed successfully')
                )
            except CommandError as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ migrate failed: {e}')
                )
                return

        # Show final status
        self.stdout.write('\n📊 Final migration status:')
        call_command('showmigrations')

        self.stdout.write(
            self.style.SUCCESS('\n🎉 Migration process completed!')
        )

    def create_migration_folders(self):
        """Create migration folders for apps that don't have them."""
        self.stdout.write('🔍 Checking for missing migration folders...')
        
        for app_config in apps.get_app_configs():
            app_name = app_config.name
            app_path = Path(app_config.path)
            migrations_path = app_path / 'migrations'
            
            # Skip Django built-in apps
            if app_name.startswith('django.contrib.'):
                continue
                
            if not migrations_path.exists():
                self.stdout.write(
                    f'📁 Creating migration folder for {app_name}'
                )
                migrations_path.mkdir(exist_ok=True)
                
                # Create __init__.py file
                init_file = migrations_path / '__init__.py'
                if not init_file.exists():
                    init_file.touch()
                    self.stdout.write(
                        f'   ✅ Created __init__.py for {app_name}'
                    ) 