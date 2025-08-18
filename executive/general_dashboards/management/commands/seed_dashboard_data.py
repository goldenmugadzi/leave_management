from django.core.management.base import BaseCommand
from django.utils import timezone
from executive.general_dashboards.models import (
    DashboardMetric, WeeklySales, WeeklyOutage, WeeklyFaultMaintenance, TopDebtor
)


class Command(BaseCommand):
    help = 'Seed initial dashboard data'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing dashboard data...')
            DashboardMetric.objects.all().delete()
            WeeklySales.objects.all().delete()
            WeeklyOutage.objects.all().delete()
            WeeklyFaultMaintenance.objects.all().delete()
            TopDebtor.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Existing data cleared'))

        # Create initial metrics
        self.stdout.write('Creating dashboard metrics...')
        
        metrics_data = [
            {
                'metric_type': 'energy_sold',
                'value': '1000',
                'unit': 'GWh',
                'target': '100000',
                'target_unit': 'GWh',
                'progress': 10
            },
            {
                'metric_type': 'growth',
                'value': '9000',
                'unit': 'Clients',
                'target': '10000',
                'target_unit': 'Clients',
                'progress': 90
            },
            {
                'metric_type': 'revenue_usd',
                'value': '17000000',
                'unit': 'USD',
                'target': '10000000',
                'target_unit': 'USD',
                'progress': 170
            },
            {
                'metric_type': 'revenue_zwl',
                'value': '6000000000',
                'unit': 'ZWL',
                'target': '6000000000',
                'target_unit': 'ZWL',
                'progress': 100
            },
            {
                'metric_type': 'faults',
                'value': '8000',
                'unit': 'Complaints',
                'target': '10000',
                'target_unit': '',
                'progress': 80
            },
            {
                'metric_type': 'maintenance',
                'value': '950',
                'unit': 'Maintained',
                'target': '1000',
                'target_unit': '',
                'progress': 95
            }
        ]

        for metric_data in metrics_data:
            metric, created = DashboardMetric.objects.get_or_create(
                metric_type=metric_data['metric_type'],
                region__isnull=True,
                district__isnull=True,
                depot__isnull=True,
                defaults=metric_data
            )
            if created:
                self.stdout.write(f'  Created metric: {metric.get_metric_type_display()}')
            else:
                self.stdout.write(f'  Metric already exists: {metric.get_metric_type_display()}')

        # Create weekly sales data
        self.stdout.write('Creating weekly sales data...')
        
        weekly_sales_data = [
            {'week': 'Week 1', 'zwl': '500,000,000', 'usd': '2,500', 'week_number': 1},
            {'week': 'Week 2', 'zwl': '750,000,000', 'usd': '3,750', 'week_number': 2},
            {'week': 'Week 3', 'zwl': '620,000,000', 'usd': '3,100', 'week_number': 3},
            {'week': 'Week 4', 'zwl': '890,000,000', 'usd': '4,450', 'week_number': 4},
            {'week': 'Week 5', 'zwl': '1,200,000,000', 'usd': '6,000', 'week_number': 5}
        ]

        for sales_data in weekly_sales_data:
            sales, created = WeeklySales.objects.get_or_create(
                week_number=sales_data['week_number'],
                year=2024,
                region__isnull=True,
                district__isnull=True,
                depot__isnull=True,
                defaults=sales_data
            )
            if created:
                self.stdout.write(f'  Created sales data: {sales.week}')

        # Create weekly outages data
        self.stdout.write('Creating weekly outages data...')
        
        weekly_outages_data = [
            {'week': 'Week 1', 'outages': 5, 'resolved': 3, 'pending': 2, 'week_number': 1},
            {'week': 'Week 2', 'outages': 8, 'resolved': 6, 'pending': 2, 'week_number': 2},
            {'week': 'Week 3', 'outages': 12, 'resolved': 9, 'pending': 3, 'week_number': 3},
            {'week': 'Week 4', 'outages': 7, 'resolved': 5, 'pending': 2, 'week_number': 4},
            {'week': 'Week 5', 'outages': 15, 'resolved': 11, 'pending': 4, 'week_number': 5}
        ]

        for outage_data in weekly_outages_data:
            outage, created = WeeklyOutage.objects.get_or_create(
                week_number=outage_data['week_number'],
                year=2024,
                region__isnull=True,
                district__isnull=True,
                depot__isnull=True,
                defaults=outage_data
            )
            if created:
                self.stdout.write(f'  Created outage data: {outage.week}')

        # Create weekly faults and maintenance data
        self.stdout.write('Creating weekly faults and maintenance data...')
        
        weekly_faults_data = [
            {'week': 'Week 1', 'faults': 8, 'maintenance': 12, 'completed': 15, 'pending': 5, 'week_number': 1},
            {'week': 'Week 2', 'faults': 6, 'maintenance': 15, 'completed': 18, 'pending': 3, 'week_number': 2},
            {'week': 'Week 3', 'faults': 10, 'maintenance': 9, 'completed': 14, 'pending': 5, 'week_number': 3},
            {'week': 'Week 4', 'faults': 4, 'maintenance': 18, 'completed': 20, 'pending': 2, 'week_number': 4},
            {'week': 'Week 5', 'faults': 12, 'maintenance': 8, 'completed': 16, 'pending': 4, 'week_number': 5}
        ]

        for fault_data in weekly_faults_data:
            fault, created = WeeklyFaultMaintenance.objects.get_or_create(
                week_number=fault_data['week_number'],
                year=2024,
                region__isnull=True,
                district__isnull=True,
                depot__isnull=True,
                defaults=fault_data
            )
            if created:
                self.stdout.write(f'  Created fault/maintenance data: {fault.week}')

        # Create top debtors data
        self.stdout.write('Creating top debtors data...')
        
        top_debtors_data = [
            {'name': 'ABC Manufacturing Ltd', 'amount': '$45,000', 'rank': 1},
            {'name': 'XYZ Construction Co', 'amount': '$38,500', 'rank': 2},
            {'name': 'Premier Mining Corp', 'amount': '$32,800', 'rank': 3},
            {'name': 'Delta Industries', 'amount': '$28,200', 'rank': 4},
            {'name': 'Metro Holdings', 'amount': '$25,600', 'rank': 5},
            {'name': 'Eastern Logistics', 'amount': '$22,400', 'rank': 6},
            {'name': 'Central Textiles', 'amount': '$19,800', 'rank': 7},
            {'name': 'Southern Farms Ltd', 'amount': '$17,300', 'rank': 8}
        ]

        for debtor_data in top_debtors_data:
            debtor, created = TopDebtor.objects.get_or_create(
                rank=debtor_data['rank'],
                region__isnull=True,
                district__isnull=True,
                depot__isnull=True,
                defaults=debtor_data
            )
            if created:
                self.stdout.write(f'  Created debtor: {debtor.name}')

        self.stdout.write(
            self.style.SUCCESS('Successfully seeded dashboard data')
        ) 