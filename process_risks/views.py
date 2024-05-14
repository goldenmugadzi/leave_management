from django.shortcuts import render, redirect
from django.http import FileResponse, JsonResponse
from datetime import datetime
from django.conf import settings
import json, os
from it import users
from .models import Departments, RiskFiles
from django.apps import apps
Sections = apps.get_model(app_label='users', model_name='Sections')
UserProfile = apps.get_model(app_label="users", model_name="UserProfile")
def index(request):
    
    return render(request, 'process_risks/index.html')

def create(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    # QuerySet Object
    user_groups = list(l)
    user_title = request.user.get_full_name()
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    departments = Departments.objects.all()
    
    if request.method == 'POST':

        filename = request.POST['file_name']
        department = request.POST['department_id']
        section = secction
        created_by = request.user.username
        created_at = datetime.now()
        updated_at = datetime.now()
        
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
            section = section,
            created_by = created_by,
            created_at=created_at,
            updated_at=updated_at,
            )
        riskObj.save()
        return render(request, 
                      'process_risks/create_process_risk.html',
                        {'departments':departments,
                         'user':user,
                         'user_title':user_title,
                         }) 

    return render(request,
                   'process_risks/create_process_risk.html',
                   {'departments':departments,
                    'user':user,
                    'user_title':user_title,
                    })


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
    file=Departments.objects.all()
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
    return render(request, 'process_risks/eng_index.html',
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
                  {"risk_files": risk_files,
                    "page_title": "Risk Mnangement Process Risks"})

def view_files(request):
    
    files = RiskFiles.objects.all()
    
    files_list = []
    for file in files:
        new_file = {
            "id": file.id,
            "filename": file.file_name,
            "file": file.filepath,
            "department": file.cat,
        }
        files_list.append(new_file)
    
    context = json.dumps(files_list, default=str)
    
    return render(request, 'process_risks/risk_table.html', {"context": context})

def edit_file(request):
    departments = Departments.objects.all()
    if request.method == 'POST':
        fileid = request.POST['id']
        filename = request.POST['fileName']
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
        
        department_ = Departments.objects.filter(id=department).first()
        risk = RiskFiles.objects.filter(id=fileid).first()
        risk.file_name = filename
        risk.filepath = file_path
        risk.cat = department_
        risk.save()
        return render(request, 
                      'process_risks/edit_file.html',
                        {'departments':departments,'risk':risk}) 

    risk_id = request.GET['file_id']
    risk = RiskFiles.objects.filter(id=risk_id).first()
    return render(request,
                   'process_risks/edit_file.html',
                   {'departments':departments, 'risk':risk})
