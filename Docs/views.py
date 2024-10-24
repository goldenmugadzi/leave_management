from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import os
from pathlib import Path
from datetime import datetime
import fitz
from PIL import Image
from tika import parser
from elasticsearch import Elasticsearch
import pytesseract
from django.utils import timezone
documents_path = os.path.join(
    Path(__file__).resolve().parent.parent, "static", "documents"
)


def search_view(request):
    # Get the search query from the request
    query = request.GET.get("q", "")

    # try:
    #     # url = "http://172.16.8.99:9200/_search"
    #     # params = {"q": query}

    #     # response = requests.get(
    #     #     url, params=params, auth=("elastic", "Password1234567890")
    #     # )
    #     # print("response: ", response)

    #     url = 'http://localhost:9200/_all/_search'
    #     params = {'q': 'content:' + query}

    #     response = requests.get(url, params=params)
    #     results = []
    #     if response.status_code == 200:
    #         data = response.json()
    #         hits = data.get("hits", {}).get("hits", [])
    #         print("hits: ", hits)
    #         cleaned_hits = []
    #         for hit in hits:
    #             file_path = hit["_source"]["file"]["url"]
    #             static_index = file_path.find("static")
    #             if static_index != -1:
    #                 url = "/" + file_path[static_index:]
    #             else:
    #                 url = ""

    #             cleaned_hit = {
    #                 "file": hit["_source"]["file"]["filename"][:-4],
    #                 "author": (
    #                     hit["_source"]["meta"]["author"]
    #                     if "meta" in hit["_source"]
    #                     else ""
    #                 ),
    #                 "date_created": (
    #                     datetime.strptime(
    #                         hit["_source"]["meta"]["created"], "%Y-%m-%dT%H:%M:%S.%f%z"
    #                     ).strftime("%B %d, %Y %H:%M")
    #                     if "meta" in hit["_source"]
    #                     else ""
    #                 ),
    #                 # 'url':url ,
    #                 "url": hit["_source"]["path"]["real"],
    #             }
    #             cleaned_hits.append(cleaned_hit)

    #         return render(
    #             request,
    #             "Docs/search.html",
    #             {"results": results, "cleaned_hits": cleaned_hits},
    #         )

    #     else:
    #         print(f"Request failed with status code {response.status_code}")

    #     # Render the search results template
    #     return render(request, "Docs/search.html", {"results": results})

    # except Exception as e:
    #     print(f"An error occurred: {str(e)}")

    #     # Handle the error appropriately, such as displaying an error page or message
    #     return render(request, "Docs/search.html", {"results": "results"})
    es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])  # Adjust host, port, and scheme if necessary
    # query = request.GET.get('query', '')
    
    results = []

    if query:
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "metadata"]
                }
            }
        }
        response = es.search(index='documents', body=search_body)
        results = response['hits']['hits']

    search_results = []
    for result in results:
        search_result = {
            'file_path': result['_source']['file_path'],
            'metadata': result['_source']['metadata'],
            'content': result['_source']['content'],
            'filename':result['filename']
        }
        search_results.append(search_result)
    if search_results:
        print(search_results[0]['metadata'])
    return render(request, "Docs/search.html", {"results": search_results, "query": query})
    # return render(request, "Docs/search.html", {"results": search_results})

def index_files(request):
    es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])  # Adjust host and port if necessary
    print("index_files")
    documents_path = os.path.join(Path(__file__).resolve().parent.parent, "static")
    subdirectories = ['process_maps', 'job_descriptions', 'plans_and_reports', 'network_development', 'petty_cash', 'comparative', 'ace']
    content = None

    for subdirectory in subdirectories:
        subdirectory_path = os.path.join(documents_path, subdirectory)
        for root, dirs, files in os.walk(subdirectory_path):
            for file in files:
                file_path = os.path.join(root, file)
                # print(file_path)
                parsed = parser.from_file(file_path)
                metadata = parsed.get("metadata", {})
                content = parsed.get("content", "")
                print(parsed)
                if not content:
                    content = ocr_pdf(file_path)
                    # print(content)
                
                # Index the content to Elasticsearch
                doc = {
                    'file_path': file_path,
                    'filename':metadata['resourceName'][2:-1],
                    'content': content,
                    'uploaded_at': timezone.now(),
                    'uploaded_by': request.user.get_full_name(),
                }
                try:
                    es.index(index='documents', body=doc)
                except Exception as e:
                    print(f"Failed to connect to Elasticsearch: {e}")
                    return render(request, "Docs/index_files.html", {"content": content, "error_message": "Failed to connect to Elasticsearch. Please ensure the server is running."})
    
    context = {"content": content}
    return render(request, "Docs/index_files.html", context)
def ocr_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text += pytesseract.image_to_string(img)
    return text

def search_files(request):
    es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])  # Adjust host, port, and scheme if necessary
    query = request.GET.get('query', '')
    
    results = []

    if query:
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "metadata"]
                }
            }
        }
        response = es.search(index='documents', body=search_body)
        results = response['hits']['hits']

    search_results = []
    for result in results:
        search_result = {
            'file_path': result['_source']['file_path'],
            'metadata': result['_source']['metadata'],
            'content': result['_source']['content']
        }
        search_results.append(search_result)
    if search_results:
        print(search_results[0]['metadata'])

    return render(request, "Docs/index_files.html", {"results": search_results, "query": query})
def view_pdf(request):
    if request.method == "POST":
        pdf_url = request.POST.get("pdf_url")
        file_path = "/static/" + os.path.relpath(pdf_url, "static")
        file_path = file_path.replace("\\", "/")
        print(file_path)
        try:
            return render(request, "pdf_template.html", {"pdf_path": file_path})
        except FileNotFoundError:
            messages.error(request, "File not found!")
            return redirect("/")
    else:
        messages.error(request, "Invalid request!")
        return redirect("/")

