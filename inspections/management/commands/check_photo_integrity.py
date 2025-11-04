"""
Management command to check and fix photo count integrity issues
Identifies mismatches between photos_count field and actual photo records
"""

from django.core.management.base import BaseCommand
from inspections.models import InspectionReport, InspectionPhoto
from django.db.models import Count


class Command(BaseCommand):
    help = 'Check and fix photo count integrity issues in inspection reports'

    def add_arguments(self, parser):
        parser.add_argument(
            '--fix',
            action='store_true',
            help='Fix the count mismatches (update photos_count to match actual photos)',
        )
        parser.add_argument(
            '--verbose',
            action='store_true',
            help='Show detailed output for each inspection',
        )

    def handle(self, *args, **options):
        fix_mode = options['fix']
        verbose = options['verbose']
        
        self.stdout.write(self.style.WARNING('\n=== Inspection Photo Integrity Check ===\n'))
        
        # Get all inspections with photo count annotations
        inspections = InspectionReport.objects.annotate(
            actual_photo_count=Count('photos')
        ).all()
        
        total_inspections = inspections.count()
        mismatches = []
        fixed_count = 0
        
        self.stdout.write(f'Checking {total_inspections} inspection reports...\n')
        
        for inspection in inspections:
            recorded_count = inspection.photos_count or 0
            actual_count = inspection.actual_photo_count
            
            if recorded_count != actual_count:
                mismatches.append({
                    'inspection': inspection,
                    'recorded': recorded_count,
                    'actual': actual_count,
                    'difference': recorded_count - actual_count
                })
                
                if verbose:
                    self.stdout.write(
                        self.style.WARNING(
                            f'Mismatch: {inspection.service_no or inspection.id} '
                            f'- Recorded: {recorded_count}, Actual: {actual_count}'
                        )
                    )
                
                if fix_mode:
                    inspection.photos_count = actual_count
                    inspection.save(update_fields=['photos_count'])
                    fixed_count += 1
                    if verbose:
                        self.stdout.write(self.style.SUCCESS(f'  ✓ Fixed: Updated to {actual_count}'))
        
        # Print summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'\nTotal inspections checked: {total_inspections}'))
        
        if mismatches:
            self.stdout.write(self.style.WARNING(f'Mismatches found: {len(mismatches)}'))
            
            # Group by type of mismatch
            orphaned_records = [m for m in mismatches if m['recorded'] > m['actual']]
            missing_records = [m for m in mismatches if m['recorded'] < m['actual']]
            
            if orphaned_records:
                self.stdout.write(
                    self.style.ERROR(
                        f'\n⚠ Orphaned photo counts (count > actual photos): {len(orphaned_records)}'
                    )
                )
                for item in orphaned_records[:5]:  # Show first 5
                    insp = item['inspection']
                    self.stdout.write(
                        f'  - {insp.service_no or insp.id}: '
                        f'recorded={item["recorded"]}, actual={item["actual"]}'
                    )
                if len(orphaned_records) > 5:
                    self.stdout.write(f'  ... and {len(orphaned_records) - 5} more')
            
            if missing_records:
                self.stdout.write(
                    self.style.WARNING(
                        f'\n⚠ Under-counted photos (count < actual photos): {len(missing_records)}'
                    )
                )
                for item in missing_records[:5]:  # Show first 5
                    insp = item['inspection']
                    self.stdout.write(
                        f'  - {insp.service_no or insp.id}: '
                        f'recorded={item["recorded"]}, actual={item["actual"]}'
                    )
                if len(missing_records) > 5:
                    self.stdout.write(f'  ... and {len(missing_records) - 5} more')
            
            if fix_mode:
                self.stdout.write(self.style.SUCCESS(f'\n✓ Fixed {fixed_count} records'))
            else:
                self.stdout.write(
                    self.style.WARNING(
                        f'\nRun with --fix flag to correct these mismatches'
                    )
                )
        else:
            self.stdout.write(self.style.SUCCESS('\n✓ No photo count mismatches found!'))
        
        # Additional statistics
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS('\nPhoto Statistics:'))
        
        total_photos = InspectionPhoto.objects.count()
        inspections_with_photos = inspections.filter(actual_photo_count__gt=0).count()
        inspections_without_photos = total_inspections - inspections_with_photos
        
        self.stdout.write(f'  Total photo records: {total_photos}')
        self.stdout.write(f'  Inspections with photos: {inspections_with_photos}')
        self.stdout.write(f'  Inspections without photos: {inspections_without_photos}')
        
        if total_photos > 0:
            avg_photos = total_photos / inspections_with_photos if inspections_with_photos > 0 else 0
            self.stdout.write(f'  Average photos per inspection (with photos): {avg_photos:.2f}')
        
        self.stdout.write('\n')

