from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import re
import os
import subprocess
import sys
import socket
import time
from pathlib import Path
import psutil
from datetime import datetime
import yaml
from django.http import FileResponse

documents_path = os.path.join(Path(__file__).resolve().parent.parent, 'static', 'documents')

def search_view(request):
    # Get the search query from the request
    query = request.GET.get('q', '')

    try:
        url = 'http://localhost:9200/_all/_search'
        params = {'q': 'content:' + query}

        response = requests.get(url, params=params)
        results = []
        if response.status_code == 200:
            data = response.json()

            hits = data.get('hits', {}).get('hits', [])
            cleaned_hits = []
            for hit in hits:
                file_path = hit['_source']['file']['url']
                static_index = file_path.find('static')
                if static_index != -1:
                    url = '/' + file_path[static_index:]
                else:
                    url = ''
                
                cleaned_hit = {
                    'file': hit['_source']['file']['filename'][:-4],
                    'author': hit['_source']['meta']['author'],
                    'date_created': datetime.strptime(hit['_source']['meta']['created'], "%Y-%m-%dT%H:%M:%S.%f%z").strftime("%B %d, %Y %H:%M"),
                    # 'url':url ,
                    'url':hit['_source']['path']['real'] ,
                }
                cleaned_hits.append(cleaned_hit)
            
            return render(request, 'Docs/search.html', {'results': results, 'cleaned_hits': cleaned_hits})

        else:
            print(f"Request failed with status code {response.status_code}")

        # Render the search results template
        return render(request, 'Docs/search.html', {'results': results})

    except Exception as e:
        print(f"An error occurred: {str(e)}")

        # Handle the error appropriately, such as displaying an error page or message
        return render(request, 'Docs/search.html', {'results': "results"})

def start_fscrawler(request):
    fscrawler_path = os.path.join(Path(__file__).resolve().parent.parent, 'fscrawler-2.10', 'bin', 'fscrawler.bat')

    config_file_path = os.path.join('fscrawler-2.10', 'DOCS', 'docs', '_settings.yaml')

    with open(config_file_path, 'r') as file:
        config = yaml.safe_load(file)

    config['fs']['url'] = documents_path

    with open(config_file_path, 'w') as file:
        yaml.safe_dump(config, file)
  
    print('Running FS crawler...')
    command_to_run = f'start cmd /k {fscrawler_path} --config_dir ./DOCS docs'
    subprocess.Popen(command_to_run, shell=True)
    print('FS crawler has been started')

    messages.success(request, 'FS crawler has been started')
    return redirect('/', messages.SUCCESS)

from wsgiref.util import FileWrapper

def view_pdf(request):
    if request.method == 'POST':
        pdf_url = request.POST.get('pdf_url')

        # Convert the URL to a file path
        file_path = os.path.join('static', pdf_url.replace('/', os.sep))

        try:
            # Open the file without the context manager
            file = open(file_path, 'rb')
            file_wrapper = FileWrapper(file)
            response = FileResponse(file_wrapper, content_type='application/pdf')
            response['Content-Disposition'] = 'inline; filename="your_pdf_filename.pdf"'
            return render(request, 'pdf_template.html', {'pdf_response': response})
        except FileNotFoundError:
            # Handle the case when the file is not found
            return render(request, 'file_not_found.html')
    else:
        return render(request, 'pdf_form.html')