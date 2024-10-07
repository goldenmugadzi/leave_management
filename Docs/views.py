from django.shortcuts import render, redirect
from django.contrib import messages
import requests
import os
from pathlib import Path
from datetime import datetime

documents_path = os.path.join(
    Path(__file__).resolve().parent.parent, "static", "documents"
)


def search_view(request):
    # Get the search query from the request
    query = request.GET.get("q", "")

    try:
        url = "http://172.16.8.99:9200/_search"
        params = {"q": query}

        response = requests.get(
            url, params=params, auth=("elastic", "Password1234567890")
        )
        print("response: ", response)

        # url = 'http://localhost:9200/_all/_search'
        # params = {'q': 'content:' + query}

        # response = requests.get(url, params=params)
        results = []
        if response.status_code == 200:
            data = response.json()
            hits = data.get("hits", {}).get("hits", [])
            print("hits: ", hits)
            cleaned_hits = []
            for hit in hits:
                file_path = hit["_source"]["file"]["url"]
                static_index = file_path.find("static")
                if static_index != -1:
                    url = "/" + file_path[static_index:]
                else:
                    url = ""

                cleaned_hit = {
                    "file": hit["_source"]["file"]["filename"][:-4],
                    "author": (
                        hit["_source"]["meta"]["author"]
                        if "meta" in hit["_source"]
                        else ""
                    ),
                    "date_created": (
                        datetime.strptime(
                            hit["_source"]["meta"]["created"], "%Y-%m-%dT%H:%M:%S.%f%z"
                        ).strftime("%B %d, %Y %H:%M")
                        if "meta" in hit["_source"]
                        else ""
                    ),
                    # 'url':url ,
                    "url": hit["_source"]["path"]["real"],
                }
                cleaned_hits.append(cleaned_hit)

            return render(
                request,
                "Docs/search.html",
                {"results": results, "cleaned_hits": cleaned_hits},
            )

        else:
            print(f"Request failed with status code {response.status_code}")

        # Render the search results template
        return render(request, "Docs/search.html", {"results": results})

    except Exception as e:
        print(f"An error occurred: {str(e)}")

        # Handle the error appropriately, such as displaying an error page or message
        return render(request, "Docs/search.html", {"results": "results"})


def index_files(request):
    from tika import parser
    print("index_files")
    documents_path = os.path.join(Path(__file__).resolve().parent.parent, "static")
    subdirectories = ['process_maps','job_descriptions','plans_and_reports','network_development','petty_cash','comparative','ace',]    
    content = None
    pdf_path = "C:\\Users\\User\\Documents\\beii_v1-main\\static\\network_development\\reticulations\\20230207033551PMTD2301196 ZEBRA.pdf"
    
    ZEBRA_text = parser.from_file(pdf_path)
    print(ZEBRA_text)
    content = ZEBRA_text.get("content", "")
    if not content:
        content = ocr_pdf(pdf_path)
        print('ocr_pdf', content)
   
    # for subdirectory in subdirectories:
    #     subdirectory_path = os.path.join(documents_path, subdirectory)
    #     for root, dirs, files in os.walk(subdirectory_path):
    #         for file in files:
    #             file_path = os.path.join(root, file)
    #             print(file_path)
    #             parsed = parser.from_file(file_path)
    #             metadata = parsed.get("metadata", {})
    #             content = parsed.get("content", "")
    #             if not content:
    #                 content = ocr_pdf(file_path)
    #                 print(content)
   
    context = { "content": content}
    return render(request, "Docs/index_files.html", context)

import pytesseract
from pdf2image import convert_from_path
from tika import parser


def ocr_pdf(pdf_path):
    print("ocr_pdf")
    text = "\n"
    pages = convert_from_path(pdf_path)
    print("pages", pages)
    # for count, page in enumerate(pages):
    #    print("count", count)
    #    text.join(parser.from_file(page))
    # page.save(f'out{count}.jpg', 'JPEG')

    # text = "\n".join(pytesseract.image_to_string(image) for image in convert_from_path(pdf_path, 500))
    print("text", text)
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
