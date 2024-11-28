import re
from django.shortcuts import render, redirect, HttpResponse
from django.contrib import messages
import subprocess, requests, os,fitz,time
from pathlib import Path
from datetime import datetime
from PIL import Image
from tika import parser
from elasticsearch import Elasticsearch
from django.contrib.auth.decorators import login_required
import pytesseract
from django.utils import timezone
documents_path = os.path.join(
    Path(__file__).resolve().parent.parent, "static", "documents"
)


def search_view(request):
    # Get the search query from the request
    query = request.GET.get("q", "")
    es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])  # Adjust host, port, and scheme if necessary
    results = []

    if query:
        search_body = {
            "query": {
                "multi_match": {
                    "query": query,
                    "fields": ["content", "file_path", "filename", "uploaded_at", "uploaded_by"]
                }
            }
        }
        response = es.search(index='documents', body=search_body)
        results = response['hits']['hits']

    search_results = []
    for result in results:
        search_result=result["_source"]
        search_result["uploaded_at"] = datetime.strptime(search_result["uploaded_at"], "%Y-%m-%d %H:%M:%S").strftime("%B %d, %Y %H:%M")
        search_results.append(search_result)
    return render(request, "Docs/search.html", {"results": search_results, "query": query})

def  start_tika_server():
    tika_jar_path = os.path.join(Path(__file__).resolve().parent.parent, "static","tika","tika-server-standard-2.9.2.jar")
    try:
        response = requests.get('http://localhost:9998/tika')
        if response.status_code == 200:
            print("Tika server is already running.")
            return
    except requests.ConnectionError:
        print("Tika server is not running. Starting the server...")
    try:
        subprocess.Popen(['java', '-jar', tika_jar_path], stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        print("Tika server started. Waiting for it to initialize...")
        time.sleep(15)
        response = requests.get('http://localhost:9998/tika')
        if response.status_code == 200:
            print("Tika server is now running.")
        else:
            print("Failed to start Tika server.")
    except Exception as e:
        print(f"An error occurred while starting the Tika server: {e}")
    return     
@login_required
def index_files(request):
    # start_tika_server()
    es = Elasticsearch([{'host': 'localhost', 'port': 9200, 'scheme': 'http'}])  # Adjust host and port if necessary
    print("index_files")
    documents_path = os.path.join(Path(__file__).resolve().parent.parent, "static")
    subdirectories = ['process_maps', 'job_descriptions', 'plans_and_reports', 'network_development', 'petty_cash', 'comparative', 'ace']
    processed_files = set()

    for subdirectory in subdirectories:
        subdirectory_path = os.path.join(documents_path, subdirectory)
        for root, dirs, files in os.walk(subdirectory_path):
            for file in files:
                file_path = os.path.join(root, file)
                file_path = os.path.normpath(file_path).replace("\\", "/")
                if file_path in processed_files:
                    continue  # Skip if the file has already been processed

                if not os.path.isfile(file_path):
                    return HttpResponse("File not found", status=404) 
                try:
                    parsed = parser.from_file(file_path)
                except Exception as e:
                    print(f"Error processing file: {e}")
                    return HttpResponse(f"Error processing file: {e} \n Tika server may not be running", status=500)
                
                metadata = parsed.get("metadata", {})
                content = parsed.get("content", "")
                if not content:
                    content = ocr_pdf(file_path)
                
                uploaded_at = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
                # Index the content to Elasticsearch
                doc = {
                    'file_path': file_path[file_path.index("/static"):],
                    'filename': filename,
                    'content': content,
                    'uploaded_at': uploaded_at,
                    'uploaded_by': request.user.get_full_name(),
                }
                try:
                    es.index(index='documents', body=doc)
                    processed_files.add(file_path)  # Mark file as processed
                    print("Indexed file:", filename)
                except Exception as e:
                    print(f"Failed to index document: {e}")

    return HttpResponse("Indexing completed successfully.")
def ocr_pdf(pdf_path):
    doc = fitz.open(pdf_path)
    text = ""
    for page_num in range(len(doc)):
        page = doc.load_page(page_num)
        pix = page.get_pixmap()
        img = Image.frombytes("RGB", [pix.width, pix.height], pix.samples)
        text += pytesseract.image_to_string(img)
    return text

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

