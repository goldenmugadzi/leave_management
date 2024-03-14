import shutil
from django.shortcuts import render, redirect
from django.http import FileResponse, JsonResponse
from datetime import datetime
from django.conf import settings
import json, os
from it import users
from .models import Process_maps
from django.apps import apps
from utils.helper_functions import get_kc_dict
Sections = apps.get_model(app_label='users', model_name='Sections')
UserProfile = apps.get_model(app_label="users", model_name="UserProfile")
def index(request):
    
    return render(request, 'process_maps/index.html')

def view_map_diagram(request):
    
    return render(request, 'process_maps/process_map_diagram.html')

def create(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    # QuerySet Object
    user_groups = list(l)
    user_title = request.user.get_full_name()
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    # departments = Departments.objects.all()
    
    if request.method == 'POST':

        filename = request.POST['file_name']
        department = request.POST['category_id']
        if 'subtype' in request.POST:
           sub_category=request.POST['subtype']
        else:
            sub_category=""
        region=request.POST['region']
        section = secction
        created_by = request.user.username
        created_at = datetime.now()
        updated_at = datetime.now()

        
        # file_path = request.FILES['uploaded_file']

        file_path = ''
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES ['uploaded_file']
                file_path = 'uploads/process_maps/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + uploaded_file.name
                save_file(uploaded_file,file_path)
        except Exception as ex:
            print("Error:",ex)

       
       
    
        processObj = Process_maps(
            filename= filename,
            department = department,
            region=region,
            filepath = file_path,
            sub_category= sub_category,
            section = section,
            created_by = created_by,
            created_at=created_at,
            updated_at=updated_at,
            )
        processObj.save()
        return render(request, 
                      'process_maps/create_process_maps.html',
                        {
                         'user':user,
                         'user_title':user_title,
                         }) 

    return render(request,
                   'process_maps/create_process_maps.html',
                   {
                    'user':user,
                    'user_title':user_title,
                    })

def bulk_create(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    # QuerySet Object
    user_groups = list(l)
    user_title = request.user.get_full_name()
    user_id = request.user.id
    user = UserProfile.objects.filter(user_id=user_id).first()
    secction = user.section
    # departments = Departments.objects.all()
    
    if request.method == 'GET':

        created_by = UserProfile.objects.filter(id=1).first()
        section = created_by.section
        region = created_by.region
        created_at = datetime.now()
        updated_at = datetime.now()

        """
        Walks through a directory recursively, collecting information about files and directories.

        Args:
            directory: The directory path to explore.

        Returns:
            A dictionary containing:
                - files: A list of dictionaries, each containing information about a file.
                - directories: A list of strings, representing the names of subdirectories.
        """
        files = []
        directories = []
        for root, dirnames, filenames in os.walk('static/documents/'):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                file_info = {
                    "name": filename,
                    "path": filepath,
                    # Add other desired file details here (e.g., size, last modified time)
                }
                files.append(file_info)
                directories += dirnames

                if '\\' in root:
                    _department = root.split("/")[2]
                    department = _department.split("\\")[0]
                    subtype = root.split("\\")[1]
                    file_path = 'uploads/process_maps/' + filename
                    processObj = Process_maps(
                        filename= filename.split(".")[0],
                        department = department,
                        region=region,
                        filepath = file_path,
                        sub_category= subtype + " processes",
                        section = section,
                        created_by = created_by,
                        created_at=created_at,
                        updated_at=updated_at,
                        )
                    processObj.save()


        return render(request, 
                      'process_maps/create_process_maps.html',
                        {
                         'user':user,
                         'user_title':user_title,
                         }) 

    return render(request,
                   'process_maps/create_process_maps.html',
                   {
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
    file_record = Process_maps.objects.filter(id=file_id).first()
    file_path = file_record.filepath

    # search for file in system
    try:
        base_directory_path = os.path.join(settings.BASE_DIR, file_path)

        return FileResponse(open(base_directory_path, 'rb'), content_type='application/pdf')
    except Exception as ex:
        print(ex)

    return redirect('/process_maps/')

def view_Client(request):
   
    files = Process_maps.objects.filter(sub_category="client interaction processes")
   

    return render(request, 'process_maps/ict.html',
                  { "files": files,
                    "page_title": "Client Interaction Process Maps"},
                    )
def view_payment(request):
   
    files = Process_maps.objects.filter(sub_category="payment processes")
   

    return render(request, 'process_maps/ict.html',
                  { " files": files,
                    "page_title": "Payment Process Maps"},
                    )
def view_revenue_assurance(request):
   
    files = Process_maps.objects.filter(sub_category="revenue assuarance processes")
   

    return render(request, 'process_maps/ict.html',
                  { " files": files,
                    "page_title": "Revenue Process Maps"},
                    )
def view_eng_planning(request):
    
    files = Process_maps.objects.filter(department="ENGINEERING", sub_category="Planning processes")

    print("files: ", files)
    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Planning process map Files", "url_path": url_path} )

#Project procesess

def view_eng_project(request):
    
    files = Process_maps.objects.filter(department="ENGINEERING", sub_category="projects processes")

    
    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Planning process map Files", "url_path": url_path} )

def view_Maintenance(request):
        files = Process_maps.objects.filter(department="ENGINEERING", sub_category="Maintenance processes")

    
    
        url_path = request.path.split("/")
        return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Maintenace process map Files", "url_path": url_path} )

def view_Procurement(request):
    
    files = Process_maps.objects.filter(department="PROCUREMENT")

    
    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Procurement process map Files", "url_path": url_path} )

def view_Engineering(request):
    
    return render(request, 'process_maps/eng.html',
                  {
                    "page_title": "Engineering Process Maps"})
#NEW ENGINEERING LIST OF PROCESS MAPS


def view_Commercial(request):
    
    return render(request, 'process_maps/commercial.html',
                  {
                    "page_title": "Commercial Process Risks"})



    
     

def view_Finance(request):
    
    files = Process_maps.objects.filter(department="FINANCE")

    
    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "FINANCE process map Files", "url_path": url_path} )

def view_ICT(request):
    
    
    files = Process_maps.objects.filter(department="ICT")

    
    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "ICT process map Files", "url_path": url_path} )

def view_HR(request):
    
    
    files = Process_maps.objects.filter(department="HUMAN RESOURCES")

    
    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Human resources process map Files", "url_path": url_path} )

def view_Risk(request):
    
    
    files = Process_maps.objects.filter(department="RISK MANAGEMENT")

    
    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Risk management process map Files", "url_path": url_path} )

def view_Map(request):
    return render(request, 'process_maps/process_map_diagram.html',
                  
            )

def view_process_map_table(request):
    
    files = Process_maps.objects.all()
    
    files_list = []
    for file in files:
        new_file = {
            "id": file.id,
            "filename": file.filename,
            "file": file.filepath,
            "department": file.department,
            "subcategory":file.sub_category,
            "created_by": file.created_by,
        }
        files_list.append(new_file)
    
    context = json.dumps(files_list, default=str)
    
    return render(request, 'process_maps/process_maps_table.html', {"context": context})

# def edit_file(request):
#     departments = Departments.objects.all()
#     if request.method == 'POST':
#         fileid = request.POST['id']
#         filename = request.POST['fileName']
#         department = request.POST['department_id']
#         # file_path = request.FILES['uploaded_file']

#         file_path = ''
#         try:
#             if 'uploaded_file' in request.FILES:
#                 uploaded_file = request.FILES ['uploaded_file']
#                 file_path = 'uploads/process_maps/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + uploaded_file.name
#                 save_file(uploaded_file,file_path)
#         except Exception as ex:
#             print("Error:",ex)
        
#         department_ = Departments.objects.filter(id=department).first()
#         risk = RiskFiles.objects.filter(id=fileid).first()
#         risk.file_name = filename
#         risk.filepath = file_path
#         risk.cat = department_
#         risk.save()
#         return render(request, 
#                       'process_maps/edit_file.html',
#                         {'departments':departments,'risk':risk}) 

#     risk_id = request.GET['file_id']
#     risk = RiskFiles.objects.filter(id=risk_id).first()
#     return render(request,
#                    'process_maps/edit_file.html',
#                    {'departments':departments, 'risk':risk})
