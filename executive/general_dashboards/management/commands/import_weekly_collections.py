from django.core.management.base import BaseCommand, CommandError
import pandas as pd
from decimal import Decimal
from executive.general_dashboards.models import WeeklyCollections
from it.users.models import Regions, Districts, Depots

class Command(BaseCommand):
    help = 'Import weekly collections data from CSV/Excel file'
    
    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to CSV/Excel file')
        parser.add_argument('--year', type=int, required=True, help='Year for the data')
        parser.add_argument('--location-type', choices=['region', 'district', 'depot'], 
                          default='depot', help='Location level for the data')
        parser.add_argument('--dry-run', action='store_true', 
                          help='Show what would be imported without saving')
        parser.add_argument('--skip-duplicates', action='store_true',
                          help='Skip existing records instead of showing errors')
    
    def handle(self, *args, **options):
        file_path = options['file_path']
        year = options['year']
        location_type = options['location_type']
        dry_run = options['dry_run']
        skip_duplicates = options['skip_duplicates']
        
        try:
            # Read file
            if file_path.endswith('.csv'):
                df = pd.read_csv(file_path)
            else:
                df = pd.read_excel(file_path)
            
            # Validate required columns
            required_cols = ['week', 'week_number', 'zwl_millions', 'usd_millions']
            if location_type == 'region':
                required_cols.append('region')
            elif location_type == 'district':
                required_cols.extend(['region', 'district'])
            else:
                required_cols.extend(['region', 'district', 'depot'])
            
            missing_cols = [col for col in required_cols if col not in df.columns]
            if missing_cols:
                raise CommandError(f"Missing required columns: {missing_cols}")
            
            # Process data
            records_created = 0
            records_updated = 0
            records_skipped = 0
            errors = []
            
            for index, row in df.iterrows():
                try:
                    # Get or create location objects
                    region = None
                    district = None
                    depot = None
                    
                    if 'region' in df.columns:
                        region, _ = Regions.objects.get_or_create(
                            region=row['region'],
                            defaults={'code': row['region'][:2].upper()}
                        )
                    
                    if 'district' in df.columns:
                        district, _ = Districts.objects.get_or_create(
                            district=row['district'],
                            region_id=region.region,
                            defaults={'code': row['district'][:2].upper()}
                        )
                    
                    if 'depot' in df.columns:
                        depot, _ = Depots.objects.get_or_create(
                            depot=row['depot'],
                            district=district,
                            region=region,
                            defaults={'code': row['depot'][:2].upper()}
                        )
                    
                    # Check if record exists
                    existing_record = WeeklyCollections.objects.filter(
                        week=row['week'],
                        year=year,
                        week_number=row['week_number'],
                        region=region,
                        district=district,
                        depot=depot
                    ).first()
                    
                    if existing_record:
                        if skip_duplicates:
                            records_skipped += 1
                            continue
                        else:
                            # Update existing record
                            existing_record.zwl_millions = Decimal(str(row['zwl_millions']))
                            existing_record.usd_millions = Decimal(str(row['usd_millions']))
                            if not dry_run:
                                existing_record.save()
                            records_updated += 1
                    else:
                        # Create new record
                        if not dry_run:
                            WeeklyCollections.objects.create(
                                week=row['week'],
                                year=year,
                                week_number=row['week_number'],
                                region=region,
                                district=district,
                                depot=depot,
                                zwl_millions=Decimal(str(row['zwl_millions'])),
                                usd_millions=Decimal(str(row['usd_millions']))
                            )
                        records_created += 1
                        
                except Exception as e:
                    errors.append(f"Row {index + 1}: {str(e)}")
            
            # Report results
            if dry_run:
                self.stdout.write(
                    self.style.WARNING(
                        f"DRY RUN - Would create {records_created}, update {records_updated}, skip {records_skipped} records"
                    )
                )
            else:
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Successfully imported data: {records_created} created, {records_updated} updated, {records_skipped} skipped"
                    )
                )
            
            if errors:
                self.stdout.write(
                    self.style.ERROR(f"Errors encountered: {len(errors)}")
                )
                for error in errors[:10]:  # Show first 10 errors
                    self.stdout.write(f"  {error}")
                    
        except Exception as e:
            raise CommandError(f"Import failed: {str(e)}")
