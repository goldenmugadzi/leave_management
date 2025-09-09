from django.core.management.base import BaseCommand
from django.utils import timezone
from executive.general_dashboards.models import WeeklyCollections, WeeklyRevenueLost, DebtorCategory
from it.users.models import Regions, Districts, Depots, UserProfile


class Command(BaseCommand):
    help = 'Create sample dashboard data for testing'

    def handle(self, *args, **options):
        self.stdout.write('Creating sample dashboard data...')
        
        try:
            # Get or create sample location
            region, created = Regions.objects.get_or_create(
                region="HARARE REGION",
                defaults={'code': 'HR'}
            )
            if created:
                self.stdout.write(f'Created region: {region.region}')
            
            district, created = Districts.objects.get_or_create(
                district="HARARE DISTRICT",
                region_id=region.region,
                defaults={'code': 'HD'}
            )
            if created:
                self.stdout.write(f'Created district: {district.district}')
            
            depot, created = Depots.objects.get_or_create(
                depot="HARARE CENTRAL",
                district=district,
                region=region,
                defaults={'code': 'HC'}
            )
            if created:
                self.stdout.write(f'Created depot: {depot.depot}')
            
            self.stdout.write(f'Using region: {region.region} (ID: {region.id})')
            self.stdout.write(f'Using district: {district.district} (ID: {district.id})')
            self.stdout.write(f'Using depot: {depot.depot} (ID: {depot.id})')
            
            # Get a user for the updated_by field
            user = UserProfile.objects.first()
            if not user:
                self.stdout.write(self.style.WARNING('No users found. Please create a user first.'))
                return
            
            current_year = timezone.now().year
            current_month = timezone.now().month
            
            # Create sample weekly collections data
            collections_created = 0
            for week_num in range(1, 7):
                obj, created = WeeklyCollections.objects.get_or_create(
                    week=f"Week {week_num}",
                    year=current_year,
                    week_number=week_num,
                    region=region,
                    district=district,
                    depot=depot,
                    defaults={
                        'zwl_millions': round(5.0 + week_num * 0.5, 2),
                        'usd_millions': round(2.0 + week_num * 0.3, 2),
                        'updated_by': user
                    }
                )
                if created:
                    collections_created += 1
            
            self.stdout.write(f'Created {collections_created} weekly collections records')
            
            # Create sample weekly revenue lost data
            revenue_lost_created = 0
            for week_num in range(1, 6):
                obj, created = WeeklyRevenueLost.objects.get_or_create(
                    week=f"Week {week_num}",
                    year=current_year,
                    week_number=week_num,
                    region=region,
                    district=district,
                    depot=depot,
                    defaults={
                        'faults_mwh': round(10.0 + week_num * 2.0, 2),
                        'maintenance_mwh': round(5.0 + week_num * 1.5, 2),
                        'updated_by': user
                    }
                )
                if created:
                    revenue_lost_created += 1
            
            self.stdout.write(f'Created {revenue_lost_created} weekly revenue lost records')
            
            # Create sample debtor categories
            categories = [
                ('mining', 25.0),
                ('domestic', 20.0),
                ('industry', 15.0),
                ('commercial', 12.0),
                ('farming', 10.0),
                ('government', 8.0),
                ('parastatal', 6.0),
                ('local_authority', 4.0)
            ]
            
            debtors_created = 0
            for category, percentage in categories:
                obj, created = DebtorCategory.objects.get_or_create(
                    category=category,
                    year=current_year,
                    month=current_month,
                    region=region,
                    district=district,
                    depot=depot,
                    defaults={
                        'percentage': percentage,
                        'updated_by': user
                    }
                )
                if created:
                    debtors_created += 1
            
            self.stdout.write(f'Created {debtors_created} debtor category records')
            
            self.stdout.write(
                self.style.SUCCESS(
                    f'Successfully created sample data:\n'
                    f'- {collections_created} weekly collections\n'
                    f'- {revenue_lost_created} weekly revenue lost\n'
                    f'- {debtors_created} debtor categories'
                )
            )
            
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'Error creating sample data: {str(e)}')
            )
