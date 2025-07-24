from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from ACE2.models import Ace2, AceAssetNumber
from it.users.models import UserProfile

User = get_user_model()

class Command(BaseCommand):
    help = 'Migrate legacy asset numbers to enhanced format'

    def add_arguments(self, parser):
        parser.add_argument(
            '--ace-id',
            type=str,
            help='Migrate specific ACE by Ace_id2',
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be migrated without making changes',
        )
        parser.add_argument(
            '--user-id',
            type=int,
            help='User ID to use for migration (default: first admin user)',
        )

    def handle(self, *args, **options):
        # Get user for migration
        if options['user_id']:
            try:
                user = UserProfile.objects.get(id=options['user_id'])
            except UserProfile.DoesNotExist:
                self.stdout.write(
                    self.style.ERROR(f'User with ID {options["user_id"]} not found')
                )
                return
        else:
            # Try to find an admin user
            user = UserProfile.objects.filter(is_superuser=True).first()
            if not user:
                user = UserProfile.objects.first()
            
            if not user:
                self.stdout.write(
                    self.style.ERROR('No users found. Please create a user first.')
                )
                return

        self.stdout.write(f'Using user: {user.get_full_name()} ({user.username})')

        # Get ACEs to migrate
        if options['ace_id']:
            aces = Ace2.objects.filter(Ace_id2=options['ace_id'])
            if not aces.exists():
                self.stdout.write(
                    self.style.ERROR(f'ACE with ID {options["ace_id"]} not found')
                )
                return
        else:
            # Get all ACEs with legacy asset numbers but no enhanced ones
            aces = Ace2.objects.exclude(
                asset_number__isnull=True
            ).exclude(
                asset_number__exact=''
            ).filter(
                enhanced_asset_numbers__isnull=True
            )

        total_aces = aces.count()
        self.stdout.write(f'Found {total_aces} ACEs to migrate')

        if options['dry_run']:
            self.stdout.write(self.style.WARNING('DRY RUN - No changes will be made'))
            
            for ace in aces[:10]:  # Show first 10 as sample
                asset_list = [an.strip() for an in ace.asset_number.split(',') if an.strip()]
                self.stdout.write(f'ACE {ace.Ace_id2}: {len(asset_list)} assets - {asset_list}')
            
            if total_aces > 10:
                self.stdout.write(f'... and {total_aces - 10} more ACEs')
            
            return

        # Actual migration
        migrated_count = 0
        error_count = 0

        for ace in aces:
            try:
                count = ace.migrate_to_enhanced_assets(user)
                if count > 0:
                    migrated_count += count
                    self.stdout.write(f'✓ ACE {ace.Ace_id2}: migrated {count} assets')
                else:
                    self.stdout.write(f'- ACE {ace.Ace_id2}: no assets to migrate')
            except Exception as e:
                error_count += 1
                self.stdout.write(
                    self.style.ERROR(f'✗ ACE {ace.Ace_id2}: error - {str(e)}')
                )

        self.stdout.write(
            self.style.SUCCESS(
                f'Migration completed: {migrated_count} assets migrated, {error_count} errors'
            )
        )
