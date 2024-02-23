from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import os
from pathlib import Path
from datetime import datetime

documents_path = os.path.join(Path(__file__).resolve().parent.parent, 'static', 'documents')

def search_view(request):
    # Get the search query from the request
    query = request.GET.get('q', '')

    try:
        url = 'http://172.16.8.98:9200/_search'
        params = {
            'q': query
        }

        response = requests.get(url, params=params, auth=("elastic", "Password1234567890"))
        
        # url = 'http://localhost:9200/_all/_search'
        # params = {'q': 'content:' + query}

        # response = requests.get(url, params=params)
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

# def start_fscrawler(request):
#     fscrawler_path = os.path.join(Path(__file__).resolve().parent.parent, 'fscrawler-2.10', 'bin', 'fscrawler.bat')

#     config_file_path = os.path.join('fscrawler-2.10', 'DOCS', 'docs', '_settings.yaml')

#     with open(config_file_path, 'r') as file:
#         config = yaml.safe_load(file)

#     config['fs']['url'] = documents_path

#     with open(config_file_path, 'w') as file:
#         yaml.safe_dump(config, file)
  
#     print('Running FS crawler...')
#     command_to_run = f'start cmd /k {fscrawler_path} --config_dir ./DOCS docs'
#     subprocess.Popen(command_to_run, shell=True)
#     print('FS crawler has been started')

#     messages.success(request, 'FS crawler has been started')
#     return redirect('/', messages.SUCCESS)

def view_pdf(request):
    if request.method == 'POST':
        pdf_url = request.POST.get('pdf_url')
        file_path = '/static/' + os.path.relpath(pdf_url, "static")
        file_path = file_path.replace('\\', '/')
        print(file_path)
        try:
            return render(request, 'pdf_template.html', {'pdf_path': file_path})
        except FileNotFoundError:
            messages.error(request, 'File not found!')
            return redirect('/')
    else:
        messages.error(request, 'Invalid request!')
        return redirect('/')