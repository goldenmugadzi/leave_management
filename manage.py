import os, subprocess, sys, requests
from django.core.management import execute_from_command_line
from pathlib import Path

def start_elasticsearch():
    try:
        response = requests.get('http://localhost:9200')
        response.raise_for_status()
        print('Elasticsearch is already running')
    except requests.exceptions.RequestException:
        print('Starting Elasticsearch')
        elasticsearch_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'elasticsearch-8.12.0', 'bin', 'elasticsearch.bat')
        subprocess.Popen(elasticsearch_path, creationflags=subprocess.CREATE_NEW_CONSOLE)
        print('Elasticsearch has been started')


start_elasticsearch()

if __name__ == '__main__':
    os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'beii_v1.settings')
    execute_from_command_line(sys.argv)