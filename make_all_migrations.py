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
    for app in custom_apps:
        try:
            print(f"\nMaking migrations for {app}...")
            call_command('makemigrations', app)
            print(f"✓ Successfully made migrations for {app}")
        except Exception as e:
            print(f"× Error making migrations for {app}: {str(e)}")

    print("\nMigration process completed!")

if __name__ == "__main__":
    make_migrations() 