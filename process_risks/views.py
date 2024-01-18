from django.shortcuts import render, redirect
from django.http import FileResponse, JsonResponse
from datetime import datetime
from django.conf import settings
import json, os
from .models import Departments, RiskFiles
def index(request):
    
    return render(request, 'process_risks/index.html')

def create(request):
    departments = Departments.objects.all()
    if request.method == 'POST':

        filename = request.POST['file_name']
        department = request.POST['department_id']
        # file_path = request.FILES['uploadedfile']

        file_path = ''
        try:
            if 'uploadedfile' in request.FILES:
                uploaded_file = request.FILES ['uploadedfile']
                file_path = 'uploads/process_risks/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + uploaded_file.name
                save_file(uploaded_file,file_path)
        except Exception as ex:
            print("Error:",ex)


        riskObj = RiskFiles(
            file_name= filename,
            cat_id = department,
            file = file_path,
            filepath = file_path,

            )
        riskObj.save()
        return render(request, 
                      'process_risks/create_process_risk.html',
                        {'departments':departments}) 

    return render(request,
                   'process_risks/create_process_risk.html',
                   {'departments':departments} )


def save_file(f,file_path):
    if f:
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
                return True
            else:
                return False



def download_file(request):

    file_id = request.GET['file_id']
    file_record = RiskFiles.objects.filter(id=file_id).first()
    file_path = file_record.filepath

    # search for file in system
    try:
        base_directory_path = os.path.join(settings.BASE_DIR, file_path)

        return FileResponse(open(base_directory_path, 'rb'), content_type='application/pdf')
    except Exception as ex:
        print(ex)

    return redirect('/process_risks/')

def view_Commercial(request):
    file=RiskFiles.objects.all()
    files = RiskFiles.objects.filter(cat_id="1")
   
    # even =False
    # for f in file:
    #     fileid = int(f.id)
    #     if fileid%2==0:
    #       even= True

    #     else:
    #       even=False
    return render(request, 'process_risks/commercial.html',
                  {"files": files,
                    "page_title": "Commercial Process Risks"},
                    )


def view_Procurement(request):
    
    procurement_files = RiskFiles.objects.filter(cat_id="4")
    return render(request, 'process_risks/procurement.html',
                  {"procurement_files": procurement_files,
                    "page_title": "Procurement Process Risks"})

def view_Engineering(request):
    
    eng_files = RiskFiles.objects.filter(cat_id="2")
    return render(request, 'process_risks/engineering.html',
                  {"eng_files": eng_files,
                    "page_title": "Engineering Process Risks"})

def view_Finance(request):
    
    finance_files = RiskFiles.objects.filter(cat_id="3")
    return render(request, 'process_risks/finance.html',
                  {"finance_files": finance_files,
                    "page_title": "Finance Process Risks"})

def view_ICT(request):
    
    ict_files = RiskFiles.objects.filter(cat_id="9")
    return render(request, 'process_risks/ict.html',
                  {"ict_files": ict_files,
                    "page_title": "ICT Process Risks"})

def view_HR(request):
    
    hr_files = RiskFiles.objects.filter(cat_id="6")
    return render(request, 'process_risks/hr.html',
                  {"hr_files": hr_files,
                    "page_title": "HR Process Risks"})

def view_Risk(request):
    
    risk_files = RiskFiles.objects.filter(cat_id="8")
    return render(request, 'process_risks/risk.html',
                  {"finance_files": risk_files,
                    "page_title": "Risk Mnangement Process Risks"})
