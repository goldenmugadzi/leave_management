from django.core.management.base import BaseCommand
from executive.general_dashboards.models import WeeklyCollections, WeeklyRevenueLost, DebtorCategory


class Command(BaseCommand):
    help = 'Clear all general dashboard data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--confirm',
            action='store_true',
            help='Confirm that you want to delete all dashboard data',
        )

    def handle(self, *args, **options):
        if not options['confirm']:
            self.stdout.write(
                self.style.WARNING(
                    'This will delete ALL dashboard data. Use --confirm to proceed.'
                )
            )
            return

        try:
            # Count records before deletion
            collections_count = WeeklyCollections.objects.count()
            revenue_lost_count = WeeklyRevenueLost.objects.count()
            debtors_count = DebtorCategory.objects.count()

            # Delete all data
            WeeklyCollections.objects.all().delete()
            WeeklyRevenueLost.objects.all().delete()
            DebtorCategory.objects.all().delete()

            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully cleared dashboard data:\n'
                    f'  - Weekly Collections: {collections_count} records\n'
                    f'  - Weekly Revenue Lost: {revenue_lost_count} records\n'
                    f'  - Debtor Categories: {debtors_count} records'
                )
            )

        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error clearing dashboard data: {str(e)}')
            )
