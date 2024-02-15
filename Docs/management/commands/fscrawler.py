from django.core.management.base import BaseCommand
import subprocess
import os
from pathlib import Path
# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent.parent.parent
print(BASE_DIR)

class Command(BaseCommand):
    help = 'Run FSCrawler for the app'

    def handle(self, *args, **options):
        activate_script = BASE_DIR/'be/Scripts/activate' 
        fscrawler_path = BASE_DIR/'fscrawler/bin/fscrawler' 
        app_name = 'Docs' 

        try:
            subprocess.check_call([activate_script, '&&', fscrawler_path, app_name], shell=True)
            self.stdout.write(self.style.SUCCESS("FSCrawler executed successfully"))
        except subprocess.CalledProcessError as e:
            self.stderr.write(f"FSCrawler execution failed with error: {str(e)}")
        
