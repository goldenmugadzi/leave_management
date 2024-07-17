from django.http import JsonResponse
import os
from django.conf import settings
import fitz  # PyMuPDF
import pytesseract
from PIL import Image
from docx import Document
import openpyxl
import pandas as pd

def extract_text_pdf(file_path):
    text = ''
    with fitz.open(file_path) as doc:
        for page in doc:
            text += page.get_text()
    return text

def extract_text_image(file_path):
    return pytesseract.image_to_string(Image.open(file_path))

def extract_text_docx(file_path):
    doc = Document(file_path)
    return '\n'.join([paragraph.text for paragraph in doc.paragraphs])

def extract_text_xlsx(file_path):
    df = pd.read_excel(file_path)
    return df.to_string()

def index_all_files(request):
    path = os.path.join(settings.STATICFILES_DIRS[0], 'comparative', 'adverts')
    files = os.listdir(path)
    extracted_Json = {}
    for file in files:
        file_path = os.path.join(path, file)
        if file.lower().endswith('.pdf'):
            with open(file_path, 'r', encoding='utf-8') as f:
                core_properties = f.core_properties
                author = core_properties.author
                title = core_properties.title
                date = core_properties.created
                size = core_properties.size
            
            extracted_Json[file] = {'path': file_path, 'author': author, 'title': title, 'date': date,'size':size , 'text': extract_text_pdf(file_path)}
        elif file.lower().endswith(('.txt', '.json', '.csv')):
            with open(file_path, 'r', encoding='utf-8') as f:
                core_properties = f.core_properties
                author = core_properties.author
                title = core_properties.title
                date = core_properties.created
                size = core_properties.size
                extracted_Json[file] = {'path': file_path, 'author': author, 'title': title, 'date': date,'size':size , 'text': f.read()}
                     
                
        elif file.lower().endswith(('.jpg', '.png', '.jpeg')):

            extracted_Json[file] = extract_text_image(file_path)
        elif file.lower().endswith('.docx'):
            core_properties = f.core_properties
            author = core_properties.author
            title = core_properties.title
            date = core_properties.created
            size = core_properties.size

            extracted_Json[file] = {'path': file_path, 'author': author, 'title': title, 'date': date, 'text': extract_text_docx(file_path)}

        elif file.lower().endswith('.xlsx'):
            extracted_Json[file] = extract_text_xlsx(file_path)
        else:
            extracted_Json[file] = "Unsupported file type."
    return JsonResponse(extracted_Json)