import csv
import os
from django.core.management.base import BaseCommand, CommandError
from django.conf import settings
from substation_inspections.models import InspectionChecklistItem


class Command(BaseCommand):
    help = 'Load inspection checklist items from CSV files'

    def add_arguments(self, parser):
        parser.add_argument(
            '--file',
            type=str,
            help='Specific CSV file to load (substation, transformer, circuit_breaker, or all)',
            choices=['substation', 'transformer', 'circuit_breaker', 'all']
        )
        parser.add_argument(
            '--clear',
            action='store_true',
            help='Clear existing checklist items before loading'
        )

    def handle(self, *args, **options):
        file_choice = options.get('file', 'all')
        clear_existing = options.get('clear', False)

        if clear_existing:
            self.stdout.write('Clearing existing checklist items...')
            InspectionChecklistItem.objects.all().delete()
            self.stdout.write(
                self.style.SUCCESS('Successfully cleared existing checklist items')
            )

        if file_choice in ['substation', 'all']:
            self.load_substation_items()

        if file_choice in ['transformer', 'all']:
            self.load_transformer_items()

        if file_choice in ['circuit_breaker', 'all']:
            self.load_circuit_breaker_items()

        self.stdout.write(
            self.style.SUCCESS('Successfully loaded checklist items')
        )

    def load_substation_items(self):
        """Load substation inspection checklist items"""
        csv_file = os.path.join(
            settings.BASE_DIR,
            'substation_inspections',
            'data',
            'monthly_substation_checklist_items.csv'
        )
        
        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')

        self.stdout.write('Loading substation checklist items...')
        loaded_count = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                item, created = InspectionChecklistItem.objects.get_or_create(
                    item_code=row['item_code'],
                    defaults={
                        'title': row['title'],
                        'description': row['description'],
                        'equipment_type': row['equipment_type'],
                        'category': row['category'],
                        'severity': row['severity'],
                        'is_mandatory': row['is_mandatory'].lower() == 'true',
                        'is_active': row['is_active'].lower() == 'true',
                        'reference_standard': row['reference_standard'],
                        'frequency': row['frequency'],
                    }
                )
                
                if created:
                    loaded_count += 1
                    self.stdout.write(f'  Created: {item.item_code} - {item.title}')
                else:
                    self.stdout.write(f'  Skipped (exists): {item.item_code} - {item.title}')

        self.stdout.write(
            self.style.SUCCESS(f'Loaded {loaded_count} substation checklist items')
        )

    def load_transformer_items(self):
        """Load transformer inspection checklist items"""
        csv_file = os.path.join(
            settings.BASE_DIR,
            'substation_inspections',
            'data',
            'monthly_transformer_checklist_items.csv'
        )
        
        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')

        self.stdout.write('Loading transformer checklist items...')
        loaded_count = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                item, created = InspectionChecklistItem.objects.get_or_create(
                    item_code=row['item_code'],
                    defaults={
                        'title': row['title'],
                        'description': row['description'],
                        'equipment_type': row['equipment_type'],
                        'category': row['category'],
                        'severity': row['severity'],
                        'is_mandatory': row['is_mandatory'].lower() == 'true',
                        'is_active': row['is_active'].lower() == 'true',
                        'reference_standard': row['reference_standard'],
                        'frequency': row['frequency'],
                    }
                )
                
                if created:
                    loaded_count += 1
                    self.stdout.write(f'  Created: {item.item_code} - {item.title}')
                else:
                    self.stdout.write(f'  Skipped (exists): {item.item_code} - {item.title}')

        self.stdout.write(
            self.style.SUCCESS(f'Loaded {loaded_count} transformer checklist items')
        )

    def load_circuit_breaker_items(self):
        """Load circuit breaker inspection checklist items"""
        csv_file = os.path.join(
            settings.BASE_DIR,
            'substation_inspections',
            'data',
            'monthly_circuit_breaker_checklist_items.csv'
        )
        
        if not os.path.exists(csv_file):
            raise CommandError(f'CSV file not found: {csv_file}')

        self.stdout.write('Loading circuit breaker checklist items...')
        loaded_count = 0

        with open(csv_file, 'r', encoding='utf-8') as file:
            reader = csv.DictReader(file)
            for row in reader:
                item, created = InspectionChecklistItem.objects.get_or_create(
                    item_code=row['item_code'],
                    defaults={
                        'title': row['title'],
                        'description': row['description'],
                        'equipment_type': row['equipment_type'],
                        'category': row['category'],
                        'severity': row['severity'],
                        'is_mandatory': row['is_mandatory'].lower() == 'true',
                        'is_active': row['is_active'].lower() == 'true',
                        'reference_standard': row['reference_standard'],
                        'frequency': row['frequency'],
                    }
                )
                
                if created:
                    loaded_count += 1
                    self.stdout.write(f'  Created: {item.item_code} - {item.title}')
                else:
                    self.stdout.write(f'  Skipped (exists): {item.item_code} - {item.title}')

        self.stdout.write(
            self.style.SUCCESS(f'Loaded {loaded_count} circuit breaker checklist items')
        )
