from django.core.management.base import BaseCommand
from django.apps import apps
import csv
import os
from django.conf import settings

class Command(BaseCommand):
    help = 'Export all database tables (Django models) to separate CSV files.'

    def handle(self, *args, **options):
        output_dir = os.path.join(settings.BASE_DIR, 'output')
        os.makedirs(output_dir, exist_ok=True)
        all_models = apps.get_models()
        for model in all_models:
            model_name = model._meta.label.replace('.', '_')
            file_path = os.path.join(output_dir, f'{model_name}.csv')
            fields = [field.name for field in model._meta.fields]
            with open(file_path, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.writer(csvfile)
                writer.writerow(fields)
                for obj in model.objects.all():
                    row = [getattr(obj, field) for field in fields]
                    writer.writerow(row)
            self.stdout.write(self.style.SUCCESS(f'Exported {model_name} to {file_path}'))
        self.stdout.write(self.style.SUCCESS('All tables exported to CSV.'))
