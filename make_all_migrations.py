import os
import django
from django.core.management import call_command
from beii_v1.settings import INSTALLED_APPS

# Set up Django environment
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
django.setup()

# Filter out Django's built-in apps and keep only custom apps
custom_apps = [
    app for app in INSTALLED_APPS 
    if not app.startswith('django.') and 
       not app.startswith('rest_framework') and
       not app.startswith('corsheaders') and
       not app.startswith('clearcache') and
       not app.startswith('sweetify') and
       not app.startswith('mathfilters')
]

def get_app_label(app_path):
    # Split the path and get the last part
    parts = app_path.split('.')
    return parts[-1]

def make_migrations():
    print("Starting migrations for all apps...")
    
    # First make migrations for all apps together
    try:
        print("\nMaking migrations for all apps together...")
        call_command('makemigrations')
        print("✓ Successfully made general migrations")
    except Exception as e:
        print(f"× Error making general migrations: {str(e)}")

    # Then make migrations for each app individually
    for app_path in custom_apps:
        app_label = get_app_label(app_path)
        try:
            print(f"\nMaking migrations for {app_label}...")
            call_command('makemigrations', app_label)
            print(f"✓ Successfully made migrations for {app_label}")
        except Exception as e:
            print(f"× Error making migrations for {app_label}: {str(e)}")

    print("\nMigration process completed!")

if __name__ == "__main__":
    make_migrations() 