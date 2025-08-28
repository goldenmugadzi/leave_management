from django.core.management.base import BaseCommand
from django.utils import timezone
from decimal import Decimal
import random
from django.db import connection
from it.users.models import Regions, Districts, Depots, UserProfile


class Command(BaseCommand):
    help = 'Seed sample data for new dashboard sections: Weekly Collections, Weekly Revenue Lost, and Debtor Categories'

    def add_arguments(self, parser):
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing data before seeding',
        )
        parser.add_argument(
            '--weeks',
            type=int,
            default=8,
            help='Number of weeks of data to generate (default: 8)',
        )
        parser.add_argument(
            '--year',
            type=int,
            default=2025,
            help='Year for the data (default: 2025)',
        )
        parser.add_argument(
            '--locations-only',
            action='store_true',
            help='Only create sample locations, skip data seeding',
        )
        parser.add_argument(
            '--collections-only',
            action='store_true',
            help='Only seed weekly collections data',
        )
        parser.add_argument(
            '--revenue-lost-only',
            action='store_true',
            help='Only seed weekly revenue lost data',
        )
        parser.add_argument(
            '--debtors-only',
            action='store_true',
            help='Only seed debtor categories data',
        )
        parser.add_argument(
            '--no-variations',
            action='store_true',
            help='Skip adding realistic data variations',
        )

    def handle(self, *args, **options):
        if options['clear']:
            self.stdout.write('Clearing existing new dashboard data...')
            with connection.cursor() as cursor:
                cursor.execute('DELETE FROM general_dashboards_weeklycollections')
                cursor.execute('DELETE FROM general_dashboards_weeklyrevenuelost')
                cursor.execute('DELETE FROM general_dashboards_debtorcategory')
            self.stdout.write(self.style.SUCCESS('Existing data cleared'))

        # Get or create sample locations
        regions, districts, depots = self.create_sample_locations()
        
        # If only creating locations, stop here
        if options['locations_only']:
            self.stdout.write(self.style.SUCCESS('Successfully created sample locations'))
            return
        
        # Get a sample user for audit trail
        sample_user = self.get_sample_user()
        
        # Generate data for different location levels
        locations_to_seed = [
            {'region_id': None, 'district_id': None, 'depot_id': None, 'name': 'National'},
        ]
        
        # Add regional data
        for region in regions[:3]:  # Limit to first 3 regions
            locations_to_seed.append({
                'region_id': region.id, 'district_id': None, 'depot_id': None, 
                'name': f'Region: {region.region}'
            })
        
        # Add district data
        for district in districts[:5]:  # Limit to first 5 districts
            locations_to_seed.append({
                'region_id': None, 'district_id': district.id, 'depot_id': None,
                'name': f'District: {district.district}'
            })
        
        # Add depot data
        for depot in depots[:3]:  # Limit to first 3 depots
            locations_to_seed.append({
                'region_id': depot.region.id, 'district_id': depot.district.id, 'depot_id': depot.id,
                'name': f'Depot: {depot.depot}'
            })

        # Seed data based on options
        if options['collections_only']:
            self.seed_weekly_collections(locations_to_seed, options['weeks'], options['year'], sample_user)
        elif options['revenue_lost_only']:
            self.seed_weekly_revenue_lost(locations_to_seed, options['weeks'], options['year'], sample_user)
        elif options['debtors_only']:
            self.seed_debtor_categories(locations_to_seed, options['year'], sample_user)
            self.seed_multiple_months_debtor_data(locations_to_seed, options['year'], sample_user)
        else:
            # Seed all data types
            self.seed_weekly_collections(locations_to_seed, options['weeks'], options['year'], sample_user)
            self.seed_weekly_revenue_lost(locations_to_seed, options['weeks'], options['year'], sample_user)
            self.seed_debtor_categories(locations_to_seed, options['year'], sample_user)
            self.seed_multiple_months_debtor_data(locations_to_seed, options['year'], sample_user)
        
        # Add realistic variations to the data (unless disabled)
        if not options['no_variations'] and not any([
            options['collections_only'], 
            options['revenue_lost_only'], 
            options['debtors_only']
        ]):
            self.add_sample_data_variations(options['weeks'], options['year'])

        self.stdout.write(
            self.style.SUCCESS(f'Successfully seeded new dashboard data for {len(locations_to_seed)} locations')
        )

    def create_sample_locations(self):
        """Create or get sample regions, districts, and depots"""
        self.stdout.write('Creating sample locations...')
        
        # Sample regions (Zimbabwe provinces)
        region_names = [
            'Harare', 'Bulawayo', 'Manicaland', 'Mashonaland Central',
            'Mashonaland East', 'Mashonaland West', 'Masvingo',
            'Matabeleland North', 'Matabeleland South', 'Midlands'
        ]
        
        regions = []
        for i, name in enumerate(region_names, 1):
            region, created = Regions.objects.get_or_create(
                region=name,
                defaults={'code': f'REG{i:02d}'}
            )
            regions.append(region)
            if created:
                self.stdout.write(f'  Created region: {name}')
        
        # Sample districts
        district_data = [
            ('Harare Central', 'HAR01', '1'),
            ('Harare South', 'HAR02', '1'),
            ('Bulawayo Central', 'BUL01', '2'),
            ('Bulawayo Industrial', 'BUL02', '2'),
            ('Mutare', 'MUT01', '3'),
            ('Chipinge', 'CHI01', '3'),
            ('Bindura', 'BIN01', '4'),
            ('Shamva', 'SHA01', '4'),
            ('Marondera', 'MAR01', '5'),
            ('Ruwa', 'RUW01', '5'),
        ]
        
        districts = []
        for name, code, region_id in district_data:
            district, created = Districts.objects.get_or_create(
                district=name,
                defaults={'code': code, 'region_id': region_id}
            )
            districts.append(district)
            if created:
                self.stdout.write(f'  Created district: {name}')
        
        # Sample depots
        depot_data = [
            ('Harare Main Depot', 'HAR_MAIN', districts[0], regions[0]),
            ('Harare South Depot', 'HAR_SOUTH', districts[1], regions[0]),
            ('Bulawayo Central Depot', 'BUL_CENT', districts[2], regions[1]),
            ('Bulawayo Industrial Depot', 'BUL_IND', districts[3], regions[1]),
            ('Mutare Depot', 'MUT_MAIN', districts[4], regions[2]),
        ]
        
        depots = []
        for name, code, district, region in depot_data:
            depot, created = Depots.objects.get_or_create(
                depot=name,
                defaults={'code': code, 'district': district, 'region': region}
            )
            depots.append(depot)
            if created:
                self.stdout.write(f'  Created depot: {name}')
        
        return regions, districts, depots

    def get_sample_user(self):
        """Get or create a sample user for audit trail"""
        try:
            return UserProfile.objects.first()
        except:
            return None

    def seed_weekly_collections(self, locations, weeks, year, user):
        """Seed Weekly Collections data"""
        self.stdout.write('Creating weekly collections data...')
        
        with connection.cursor() as cursor:
            for location in locations:
                for week_num in range(1, weeks + 1):
                    # Generate realistic collection amounts
                    if location['region_id'] is None and location['district_id'] is None and location['depot_id'] is None:
                        # National level
                        base_zwl = random.uniform(800, 1200)  # 800M - 1200M ZWL
                        base_usd = random.uniform(4, 8)       # 4M - 8M USD
                    elif location['depot_id'] is not None:
                        # Depot level (smallest)
                        base_zwl = random.uniform(50, 150)    # 50M - 150M ZWL
                        base_usd = random.uniform(0.3, 0.8)   # 0.3M - 0.8M USD
                    elif location['district_id'] is not None:
                        # District level
                        base_zwl = random.uniform(200, 400)   # 200M - 400M ZWL
                        base_usd = random.uniform(1, 2.5)     # 1M - 2.5M USD
                    else:
                        # Regional level
                        base_zwl = random.uniform(400, 800)   # 400M - 800M ZWL
                        base_usd = random.uniform(2, 5)       # 2M - 5M USD
                    
                    # Add some weekly variation
                    weekly_variation = random.uniform(0.8, 1.2)
                    zwl_amount = round(base_zwl * weekly_variation, 2)
                    usd_amount = round(base_usd * weekly_variation, 2)
                    
                    # Check if record already exists
                    cursor.execute("""
                        SELECT id FROM general_dashboards_weeklycollections 
                        WHERE week_number = %s AND year = %s 
                        AND region_id <=> %s AND district_id <=> %s AND depot_id <=> %s
                    """, [week_num, year, location['region_id'], location['district_id'], location['depot_id']])
                    
                    if not cursor.fetchone():
                        # Insert new record
                        cursor.execute("""
                            INSERT INTO general_dashboards_weeklycollections 
                            (week, week_number, year, zwl_millions, usd_millions, 
                             region_id, district_id, depot_id, updated_by_id, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, [
                            f'Week {week_num}', week_num, year, zwl_amount, usd_amount,
                            location['region_id'], location['district_id'], location['depot_id'],
                            user.id if user else None
                        ])
                        
                        self.stdout.write(f'  Created collections for {location["name"]} - Week {week_num}: ZWL {zwl_amount}M, USD {usd_amount}M')
                    else:
                        self.stdout.write(f'  Collections already exist for {location["name"]} - Week {week_num}')

    def seed_weekly_revenue_lost(self, locations, weeks, year, user):
        """Seed Weekly Revenue Lost data"""
        self.stdout.write('Creating weekly revenue lost data...')
        
        with connection.cursor() as cursor:
            for location in locations:
                for week_num in range(1, weeks + 1):
                    # Generate realistic revenue lost amounts in MWh
                    if location['region_id'] is None and location['district_id'] is None and location['depot_id'] is None:
                        # National level
                        base_faults = random.uniform(150, 300)      # 150-300 MWh lost to faults
                        base_maintenance = random.uniform(100, 200) # 100-200 MWh lost to maintenance
                    elif location['depot_id'] is not None:
                        # Depot level (smallest)
                        base_faults = random.uniform(10, 30)        # 10-30 MWh
                        base_maintenance = random.uniform(5, 20)    # 5-20 MWh
                    elif location['district_id'] is not None:
                        # District level
                        base_faults = random.uniform(40, 80)        # 40-80 MWh
                        base_maintenance = random.uniform(20, 50)   # 20-50 MWh
                    else:
                        # Regional level
                        base_faults = random.uniform(80, 150)       # 80-150 MWh
                        base_maintenance = random.uniform(40, 100)  # 40-100 MWh
                    
                    # Add some weekly variation
                    weekly_variation = random.uniform(0.7, 1.3)
                    faults_mwh = round(base_faults * weekly_variation, 2)
                    maintenance_mwh = round(base_maintenance * weekly_variation, 2)
                    total_mwh = faults_mwh + maintenance_mwh
                    
                    # Check if record already exists
                    cursor.execute("""
                        SELECT id FROM general_dashboards_weeklyrevenuelost 
                        WHERE week_number = %s AND year = %s 
                        AND region_id <=> %s AND district_id <=> %s AND depot_id <=> %s
                    """, [week_num, year, location['region_id'], location['district_id'], location['depot_id']])
                    
                    if not cursor.fetchone():
                        # Insert new record using the current database column names
                        cursor.execute("""
                            INSERT INTO general_dashboards_weeklyrevenuelost 
                            (week, week_number, year, faults_mwh, maintenance_mwh, 
                             total_mwh, region_id, district_id, depot_id, updated_by_id, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, [
                            f'Week {week_num}', week_num, year, faults_mwh, maintenance_mwh, total_mwh,
                            location['region_id'], location['district_id'], location['depot_id'],
                            user.id if user else None
                        ])
                        
                        self.stdout.write(f'  Created revenue lost for {location["name"]} - Week {week_num}: Faults {faults_mwh} MWh, Maintenance {maintenance_mwh} MWh, Total {total_mwh} MWh')
                    else:
                        self.stdout.write(f'  Revenue lost already exists for {location["name"]} - Week {week_num}')

    def seed_debtor_categories(self, locations, year, user):
        """Seed Debtor Categories data"""
        self.stdout.write('Creating debtor categories data...')
        
        # Define the 8 debtor categories matching the model choices
        categories = [
            'mining', 'domestic', 'industry', 'commercial', 
            'farming', 'government', 'parastatal', 'local_authority'
        ]
        
        with connection.cursor() as cursor:
            for location in locations:
                # Generate realistic percentage distribution for each location
                # Start with base percentages that sum to 100%
                base_percentages = {
                    'domestic': 35.0,      # Largest segment
                    'commercial': 20.0,    # Second largest
                    'industry': 15.0,      # Industrial customers
                    'government': 10.0,    # Government institutions
                    'mining': 8.0,         # Mining operations
                    'farming': 5.0,        # Agricultural customers
                    'parastatal': 4.0,     # Parastatal organizations
                    'local_authority': 3.0  # Local authorities
                }
                
                # Add some location-based variation
                variation_factor = random.uniform(0.8, 1.2)
                adjusted_percentages = {}
                
                for category in categories:
                    # Apply variation and some randomness
                    base_pct = base_percentages[category]
                    varied_pct = base_pct * variation_factor * random.uniform(0.7, 1.3)
                    adjusted_percentages[category] = max(0.1, varied_pct)  # Minimum 0.1%
                
                # Normalize to ensure they sum to 100%
                total = sum(adjusted_percentages.values())
                normalized_percentages = {
                    cat: round((pct / total) * 100, 2) 
                    for cat, pct in adjusted_percentages.items()
                }
                
                # Adjust the largest category to ensure exact 100% total
                largest_cat = max(normalized_percentages, key=normalized_percentages.get)
                current_total = sum(normalized_percentages.values())
                normalized_percentages[largest_cat] += round(100.0 - current_total, 2)
                
                # Create records for each category at this location
                for category in categories:
                    percentage = normalized_percentages[category]
                    
                    # Check if record already exists for this category and location
                    cursor.execute("""
                        SELECT id FROM general_dashboards_debtorcategory 
                        WHERE category = %s AND year = %s AND month = 1
                        AND region_id <=> %s AND district_id <=> %s AND depot_id <=> %s
                    """, [category, year, location['region_id'], location['district_id'], location['depot_id']])
                    
                    if not cursor.fetchone():
                        # Insert new debtor category record
                        cursor.execute("""
                            INSERT INTO general_dashboards_debtorcategory 
                            (category, percentage, year, month, region_id, district_id, depot_id, 
                             updated_by_id, created_at, updated_at)
                            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                        """, [
                            category, percentage, year, 1,  # Default to January
                            location['region_id'], location['district_id'], location['depot_id'],
                            user.id if user else None
                        ])
                        
                        self.stdout.write(f'  Created debtor category for {location["name"]}: {category.title()} = {percentage}%')
                    else:
                        self.stdout.write(f'  Debtor category already exists for {location["name"]}: {category.title()}')
                
                # Verify the total is 100% for this location
                cursor.execute("""
                    SELECT SUM(percentage) FROM general_dashboards_debtorcategory 
                    WHERE year = %s AND month = 1
                    AND region_id <=> %s AND district_id <=> %s AND depot_id <=> %s
                """, [year, location['region_id'], location['district_id'], location['depot_id']])
                
                total_pct = cursor.fetchone()[0] or 0
                self.stdout.write(f'  Total percentage for {location["name"]}: {total_pct}%')

    def generate_realistic_data_patterns(self):
        """Generate realistic seasonal and weekly patterns for the data"""
        # This could be extended to add seasonal variations, 
        # holiday effects, maintenance schedules, etc.
        pass

    def seed_multiple_months_debtor_data(self, locations, year, user):
        """Seed debtor data for multiple months to show trends"""
        self.stdout.write('Creating multi-month debtor category data...')
        
        # Define seasonal patterns for different categories
        seasonal_patterns = {
            'domestic': [1.0, 1.0, 0.95, 0.9, 0.85, 0.8, 0.8, 0.85, 0.9, 0.95, 1.0, 1.05],  # Lower in winter
            'commercial': [1.0, 0.95, 1.0, 1.05, 1.1, 1.15, 1.2, 1.15, 1.1, 1.05, 1.0, 0.95],  # Higher in summer
            'industry': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # Stable year-round
            'mining': [1.2, 1.15, 1.1, 1.05, 1.0, 0.95, 0.9, 0.95, 1.0, 1.05, 1.1, 1.15],  # Higher in dry season
            'farming': [0.8, 0.8, 0.9, 1.0, 1.2, 1.3, 1.2, 1.0, 0.9, 0.8, 0.8, 0.8],  # Peak during harvest
            'government': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # Stable
            'parastatal': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0],  # Stable
            'local_authority': [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0]  # Stable
        }
        
        categories = list(seasonal_patterns.keys())
        
        with connection.cursor() as cursor:
            for location in locations:
                for month in range(2, 13):  # Months 2-12 (January already created)
                    # Generate base percentages for this month
                    base_percentages = {
                        'domestic': 35.0,
                        'commercial': 20.0,
                        'industry': 15.0,
                        'government': 10.0,
                        'mining': 8.0,
                        'farming': 5.0,
                        'parastatal': 4.0,
                        'local_authority': 3.0
                    }
                    
                    # Apply seasonal patterns
                    seasonal_percentages = {}
                    for category in categories:
                        seasonal_factor = seasonal_patterns[category][month - 1]
                        seasonal_percentages[category] = base_percentages[category] * seasonal_factor
                    
                    # Normalize to 100%
                    total = sum(seasonal_percentages.values())
                    normalized_percentages = {
                        cat: round((pct / total) * 100, 2) 
                        for cat, pct in seasonal_percentages.items()
                    }
                    
                    # Adjust for exact 100%
                    largest_cat = max(normalized_percentages, key=normalized_percentages.get)
                    current_total = sum(normalized_percentages.values())
                    normalized_percentages[largest_cat] += round(100.0 - current_total, 2)
                    
                    # Create records for each category
                    for category in categories:
                        percentage = normalized_percentages[category]
                        
                        # Check if record already exists
                        cursor.execute("""
                            SELECT id FROM general_dashboards_debtorcategory 
                            WHERE category = %s AND year = %s AND month = %s
                            AND region_id <=> %s AND district_id <=> %s AND depot_id <=> %s
                        """, [category, year, month, location['region_id'], location['district_id'], location['depot_id']])
                        
                        if not cursor.fetchone():
                            cursor.execute("""
                                INSERT INTO general_dashboards_debtorcategory 
                                (category, percentage, year, month, region_id, district_id, depot_id, 
                                 updated_by_id, created_at, updated_at)
                                VALUES (%s, %s, %s, %s, %s, %s, %s, %s, NOW(), NOW())
                            """, [
                                category, percentage, year, month,
                                location['region_id'], location['district_id'], location['depot_id'],
                                user.id if user else None
                            ])

    def add_sample_data_variations(self, weeks, year):
        """Add realistic variations to the sample data"""
        self.stdout.write('Adding realistic data variations...')
        
        # Add some weeks with zero collections (maintenance periods)
        # Add some weeks with high revenue lost (major faults)
        # Add gradual trends over time
        
        with connection.cursor() as cursor:
            # Simulate a major fault in week 3 that affects multiple locations
            cursor.execute("""
                UPDATE general_dashboards_weeklyrevenuelost 
                SET faults_mwh = faults_mwh * 2.5, 
                    total_mwh = (faults_mwh * 2.5) + maintenance_mwh
                WHERE week_number = 3 AND year = %s
            """, [year])
            
            # Simulate maintenance shutdown in week 6
            cursor.execute("""
                UPDATE general_dashboards_weeklyrevenuelost 
                SET maintenance_mwh = maintenance_mwh * 3.0,
                    total_mwh = faults_mwh + (maintenance_mwh * 3.0)
                WHERE week_number = 6 AND year = %s
            """, [year])
            
            # Simulate good collection week (week 4)
            cursor.execute("""
                UPDATE general_dashboards_weeklycollections 
                SET zwl_millions = zwl_millions * 1.3,
                    usd_millions = usd_millions * 1.3
                WHERE week_number = 4 AND year = %s
            """, [year])
            
            self.stdout.write('  Added realistic variations to sample data')