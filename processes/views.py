import shutil
from django.shortcuts import render, redirect
from django.http import FileResponse, JsonResponse
from datetime import datetime
from django.conf import settings
from django.contrib import messages
from django.core.files.storage import FileSystemStorage
import json, os
from it import users
from it.users.models import Regions
from .models import FileSubType, Process_maps, Processes, SubSubType
from django.apps import apps
from utils.helper_functions import get_kc_dict
Sections = apps.get_model(app_label='users', model_name='Sections')
UserProfile = apps.get_model(app_label="users", model_name="UserProfile")
        
from argparse import FileType
from django.shortcuts import redirect, render
from django.http import FileResponse
import  os, re
from beii_v1 import settings
from process_risks.views import Sections
from processes.models import File_Type, First_Category, Second_Category
from django.contrib.auth.decorators import login_required

@login_required
def index(request):
    return render(request, 'process_maps/index.html')

@login_required
def view_map_diagram(request):
    
    return render(request, 'process_maps/process_map_diagram.html')

@login_required
def create(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    # QuerySet Object
    user_title = request.user.get_full_name()
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    section = user.section
    _filetypes = File_Type.objects.all()
    regions = Regions.objects.all()
    
    if request.method == 'POST':

        filename = request.POST['file_name']
        filetype = request.POST['filetype']
        _filetype = File_Type.objects.filter(id=filetype).first()
        sub_category = ""
        _sub_category = ""
        _subsubtype = ""
        
        try:
            
            if 'subtype' in request.POST:
                sub_category=request.POST['subtype']
                _sub_category = FileSubType.objects.filter(id=sub_category).first()

            else:
                sub_category=""
                sub_category = None
            if 'subsubtype' in request.POST:
                subsubtype=request.POST['subsubtype']
                _subsubtype = SubSubType.objects.filter(id=subsubtype).first()

            else:
                subsubtype=""
                _subsubtype = None
        except Exception as ex:
            print("Error:", ex)
            
        region=request.POST['region']
        created_at = datetime.now()
        updated_at = datetime.now()
        
        file_url = ""
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES['uploaded_file']
                root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'processes')
                fs = FileSystemStorage(location=root_dir)
                filename_ = fs.save(uploaded_file.name, uploaded_file)
                file_url = "uploads" + os.path.sep + "processes" + os.path.sep + filename_
                
                region_ = Regions.objects.filter(id=region).first()     
                processObj = Processes(
                    filename= filename,
                    filetype=_filetype.name if _filetype else None,
                    filetype_id = _filetype if _filetype else None,
                    department = _sub_category.name if _sub_category else "",
                    filesubtype_id = _sub_category if _sub_category else None,
                    region=region,
                    region_id = region_ if region_ else None,
                    filepath = file_url,
                    sub_category= _subsubtype.name if _subsubtype else "",
                    subsubtype_id = _subsubtype if _subsubtype else None,
                    section = section,
                    section_id = section if section else None,
                    cost_center = user.cost_center if user.cost_center else None,
                    created_by = user.username if user else None,
                    done_by = user,
                    created_at=created_at,
                    created_on=datetime.now(),
                    updated_at=updated_at,
                    updated_on=datetime.now(),
                    )
                processObj.save()
                messages.success(request, 'File uploaded successfully')
            else:
                messages.error(request, 'Error please upload a file')
        except Exception as ex:
            print("Error:", ex)
            messages.error(request, 'Error uploading file')
        
        return redirect('/processes/create')

    return render(request,
                   'process_maps/create_process_maps.html',
                   {
                    'user':user,
                    'user_title':user_title,
                    'filetypes':_filetypes,
                    'regions':regions,
                    })


@login_required
def update(request, file_id):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    # QuerySet Object
    user_title = request.user.get_full_name()
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    secction = user.section
    _filetypes = File_Type.objects.all()
    regions = Regions.objects.all()
    process = Processes.objects.filter(id=file_id).first()
    _region = Regions.objects.filter(id=process.region).first() if process.region else None
    
    if request.method == 'POST':
        # try:
            id = request.POST['id']
            filename = request.POST['file_name']
            filetype = request.POST['filetype']
            _filetype = File_Type.objects.filter(id=filetype).first() if filetype else None

            if 'subtype' in request.POST:
                sub_category=request.POST['subtype']
                _sub_category = FileSubType.objects.filter(id=sub_category).first() if sub_category else None
                print(_sub_category)
            else:
                sub_category=""
                sub_category = None
            if 'subsubtype' in request.POST:
                subsubtype=request.POST['subsubtype']
                _subsubtype = SubSubType.objects.filter(id=subsubtype).first() if subsubtype else None
                print(_subsubtype)
            else:
                subsubtype=""
                _subsubtype = None
                
            region=request.POST['region']
            updated_at = datetime.now()
            
            file_url = ""
            try:
                if 'uploaded_file' in request.FILES:
                    uploaded_file = request.FILES['uploaded_file']
                    root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'processes')
                    fs = FileSystemStorage(location=root_dir)
                    filename_ = fs.save(uploaded_file.name, uploaded_file)
                    file_url = "uploads" + os.path.sep + "processes" + os.path.sep + filename_
            except Exception as ex:
                print("Error:", ex)
            
            region_ = Regions.objects.filter(id=region).first() if region else None
            process = Processes.objects.filter(id=id).first()
            if process:
                
                process.filename = filename if filename else process.filename
                process.filetype = _filetype.name if _filetype else process.filetype
                process.filetype_id = _filetype if _filetype else process.filetype_id
                process.department = _sub_category.name if _sub_category else process.department
                process.filesubtype_id = _sub_category if _sub_category else process.filesubtype_id
                process.region = region if region else process.region
                process.region_id = region_ if region_ else process.region_id
                process.filepath = file_url if file_url else process.filepath
                process.sub_category = _subsubtype.name if _subsubtype else process.sub_category
                process.subsubtype_id = _subsubtype if _subsubtype else process.subsubtype_id
                process.updated_at = updated_at
                process.updated_on = datetime.now()
                process.save()
                messages.success(request, 'File updated successfully')
            else:
                messages.error(request, 'Process not found')
        # except Exception as ex:
        #     print("Error:", ex)
        #     messages.error(request, 'Error updating file')
        
            return redirect('/processes/process/update/'+str(id))

    return render(request,
                   'process_maps/edit_process.html',
                   {
                    'user':user,
                    'user_title':user_title,
                    'filetypes':_filetypes,
                    'regions':regions,
                    'record': process,
                    'region_': _region
                    })

@login_required
def get_subtypes(request, filetype):
	subtypes = FileSubType.objects.filter(filetype_id=filetype).all()

	subtypes_list = []
	for subtype in subtypes:
		new_subtype = {
			"id": subtype.id,
			"name": subtype.name,
		}
		subtypes_list.append(new_subtype)
	return JsonResponse(
     {
        'subtypes': subtypes_list
     }, safe=False)

@login_required
def get_subsubtypes(request, subtype):
	subsubtypes = SubSubType.objects.filter(file_subtype_id=subtype).all()
	subsubtypes_list = []
	for subsubtype in subsubtypes:
		new_subsubtype = {
			"id": subsubtype.id,
			"name": subsubtype.name,
		}
		subsubtypes_list.append(new_subsubtype)
	
	print(subsubtypes_list)
	return JsonResponse(
     {
        'subsubtypes': subsubtypes_list
     }, safe=False)

@login_required
def view_process_map_table(request):
    
    # Processes.migrate_fields()
    # Processes.migrate_duplicates()
    # Processes.migrate_filetypes()
    files = Processes.objects.filter(archived=False).all()
    
    files_list = []
    for file in files:
        new_file = {
            "id": file.id,
            "filetype": file.filetype_id.name if file.filetype_id else "",
            "filename": file.filename,
            "file": file.filepath,
            "department": file.subsubtype_id.name if file.subsubtype_id else "",
            "subcategory":file.filesubtype_id.name if file.filesubtype_id else "",
            "created_by": file.done_by.first_name + " " + file.done_by.last_name if file.done_by else "",
            "archived": file.archived,
            "created_at": file.created_on.astimezone().strftime("%Y-%m-%d %H:%M:%S") if file.created_on else "",
        }
        files_list.append(new_file)
    
    files_list = sorted(files_list, key=lambda x: x['created_at'], reverse=True)
    context = json.dumps(files_list, default=str)
    
    return render(request, 'process_maps/process_maps_table.html', {"context": context, "page": "processes_all"})

@login_required
def view_archived_processes(request):
    
    files = Processes.objects.filter(archived=True).all()
    
    files_list = []
    for file in files:
        new_file = {
            "id": file.id,
            "filetype": file.filetype_id.name if file.filetype_id else "",
            "filename": file.filename,
            "file": file.filepath,
            "department": file.subsubtype_id.name if file.subsubtype_id else "",
            "subcategory":file.filesubtype_id.name if file.filesubtype_id else "",
            "created_by": file.done_by.first_name + " " + file.done_by.last_name if file.done_by else "",
            "archived": file.archived,
            "created_at": file.created_on.astimezone().strftime("%Y-%m-%d %H:%M:%S") if file.created_on else "",
        }
        files_list.append(new_file)
    
    files_list = sorted(files_list, key=lambda x: x['created_at'], reverse=True)
    context = json.dumps(files_list, default=str)
    
    return render(request, 'process_maps/process_maps_table.html', {"context": context})

@login_required
def archive_file(request, file_id):

    try:
        um = Processes.objects.filter(id=file_id).first()
        um.archived=True
        um.save()
        messages.success(request, 'File archived successfully')
    except Exception as ex:
        print("Error:", ex)
        messages.error(request, 'Error archiving file')
    
    return redirect('/processes/table')

@login_required
def unarchive_file(request, file_id):

    try:
        um = Processes.objects.filter(id=file_id).first()
        um.archived=False
        um.save()
        messages.success(request, 'File unarchived successfully')
    except Exception as ex:
        print("Error:", ex)
        messages.error(request, 'Error unarchiving file')
    
    return redirect('/processes/table')

@login_required
def bulk_create(request):
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)
    # QuerySet Object
    user_groups = list(l)
    user_title = request.user.get_full_name()
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    
    if request.method == 'GET':

        created_by = user.id
        section = user.section.id
        region = user.region.id
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
        for root, dirnames, filenames in os.walk('static/docx/'):
            for filename in filenames:
                filepath = os.path.join(root, filename)
                file_info = {
                    "name": filename,
                    "path": filepath,
                    # Add other desired file details here (e.g., size, last modified time)
                }
                files.append(file_info)
                directories += dirnames

                if os.path.sep in root:
                    
                    norm = os.path.normpath(root)
                    items = norm.split(os.path.sep)
                    file_path = 'uploads/processes/' + filename
                    
                    destination_folder = 'uploads/processes/'  # Specify the destination folder
                    destination_path = os.path.join(destination_folder, filename)

                    # Copy the file to the destination folder
                    try:
                        if not os.path.exists(destination_path):
                            shutil.copy2(filepath, destination_path)
                        else:
                            print(f"File {filename} already exists in the destination folder.")
                        # shutil.copy2(filepath, destination_path)
                    except shutil.Error as e:
                        print(f"Error occurred while copying file: {e}")
                    
                    ft = items[2] if len(items) >= 3 else ""
                    dp = items[3] if len(items) >= 4 else ""
                    sc = items[4] if len(items) >= 5 else ""
                    
                    processObj = Processes(
                        filetype= ft,
                        filename= filename.split(".")[0],
                        department = dp,
                        region=region,
                        filepath = file_path,
                        sub_category= sc,
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

@login_required
def bulk_risk(request):
    deps = [
		{
			"id": 1,
			"name": "Commercial"
		},
		{
			"id": 2,
			"name": "Engineering"
		},
		{
			"id": 3,
			"name": "Finance"
		},
		{
			"id": 4,
			"name": "Procurement"
		},
		{
			"id": 5,
			"name": "Legal Services"
		},
		{
			"id": 6,
			"name": "Human Resources"
		},
		{
			"id": 7,
			"name": "Stakeholder Relations"
		},
		{
			"id": 8,
			"name": "Risk Management"
		},
		{
			"id": 9,
			"name": "ICT"
		}
	]
    
    files = [
		{
			"id": 22,
			"file_name": "CT Revenue assurance",
			"file": "uploads/process_risks/20240118093111AMCT REV ASS RISK REGISTER (1).pdf",
			"filepath": "uploads/process_risks/20240118093111AMCT REV ASS RISK REGISTER (1).pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 23,
			"file_name": "Advertising ",
			"file": "uploads/process_risks/20240118093232AMAdvertising Risk Register.pdf",
			"filepath": "uploads/process_risks/20240118093232AMAdvertising Risk Register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 24,
			"file_name": "Fault Handling",
			"file": "uploads/process_risks/20240118093541AMFault Handling risk register.pdf",
			"filepath": "uploads/process_risks/20240118093541AMFault Handling risk register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 25,
			"file_name": "Net Metering",
			"file": "uploads/process_risks/20240118093811AMNET metering risk register.pdf",
			"filepath": "uploads/process_risks/20240118093811AMNET metering risk register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 26,
			"file_name": "Debtors Analysis changed",
			"file": "uploads/process_risks/20240118094146AMZETDC HRE FIN 03001 RECOVERABLE DEBTORS  REGISTER.pdf",
			"filepath": "uploads/process_risks/20240205110449AMBanda 2.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 28,
			"file_name": "Competitive Tender",
			"file": "uploads/process_risks/20240118095742AMCompetitive tender.pdf",
			"filepath": "uploads/process_risks/20240118095742AMCompetitive tender.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 4
		},
		{
			"id": 29,
			"file_name": "Direct purchase",
			"file": "uploads/process_risks/20240118100359AMDirect Purchase (2).pdf",
			"filepath": "uploads/process_risks/20240118100359AMDirect Purchase (2).pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 4
		},
		{
			"id": 30,
			"file_name": "Request for Qoutation",
			"file": "uploads/process_risks/20240118100517AMRequest for quotation (2).pdf",
			"filepath": "uploads/process_risks/20240118100517AMRequest for quotation (2).pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 4
		},
		{
			"id": 31,
			"file_name": "Restricted purchase",
			"file": "uploads/process_risks/20240118100753AMRestricted purchase (2).pdf",
			"filepath": "uploads/process_risks/20240118100753AMRestricted purchase (2).pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 4
		},
		{
			"id": 32,
			"file_name": "Office Buildings Plans",
			"file": "uploads/process_risks/20240118101548AMDrawing Office Building  Plans Processing Process risk registe",
			"filepath": "uploads/process_risks/20240118101548AMDrawing Office Building  Plans Processing Process risk register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 33,
			"file_name": "Cable fault",
			"file": "uploads/process_risks/20240118101735AMCABLE FAULT .._.pdf",
			"filepath": "uploads/process_risks/20240118101735AMCABLE FAULT .._.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 34,
			"file_name": "Fault maintenance",
			"file": "uploads/process_risks/20240118101836AMFAULT MAINTANENCE.pdf",
			"filepath": "uploads/process_risks/20240118101836AMFAULT MAINTANENCE.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 35,
			"file_name": "Insulator changing",
			"file": "uploads/process_risks/20240118102017AMINSULATOR CHANGING.pdf",
			"filepath": "uploads/process_risks/20240118102017AMINSULATOR CHANGING.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 36,
			"file_name": "Line Inspection",
			"file": "uploads/process_risks/20240118102225AMLINE INSPECTION.pdf",
			"filepath": "uploads/process_risks/20240118102225AMLINE INSPECTION.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 37,
			"file_name": "Overhead line maintenance",
			"file": "uploads/process_risks/20240118102356AMOVERHEAD LINE MAINTANENCE.pdf",
			"filepath": "uploads/process_risks/20240118102356AMOVERHEAD LINE MAINTANENCE.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 38,
			"file_name": "Pole changing",
			"file": "uploads/process_risks/20240118102429AMPole changing.pdf",
			"filepath": "uploads/process_risks/20240118102429AMPole changing.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 39,
			"file_name": "Wayleave",
			"file": "uploads/process_risks/20240118103839AMWAY LEAVE.pdf",
			"filepath": "uploads/process_risks/20240118103839AMWAY LEAVE.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 40,
			"file_name": "Diary management",
			"file": "uploads/process_risks/20240118104142AMRisk Register  -  Diary Management.pdf",
			"filepath": "uploads/process_risks/20240118104142AMRisk Register  -  Diary Management.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 41,
			"file_name": "Mail handling",
			"file": "uploads/process_risks/20240118104203AMRisk Register  -  Mail Handling.pdf",
			"filepath": "uploads/process_risks/20240118104203AMRisk Register  -  Mail Handling.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 42,
			"file_name": "Meetings",
			"file": "uploads/process_risks/20240118104222AMRisk Register  -  Meetings.pdf",
			"filepath": "uploads/process_risks/20240118104222AMRisk Register  -  Meetings.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 43,
			"file_name": "Records management",
			"file": "uploads/process_risks/20240118104249AMRisk Register  -  Record Management.pdf",
			"filepath": "uploads/process_risks/20240118104249AMRisk Register  -  Record Management.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 44,
			"file_name": "Reports",
			"file": "uploads/process_risks/20240118104305AMRisk Register  -  Reports.pdf",
			"filepath": "uploads/process_risks/20240118104305AMRisk Register  -  Reports.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 45,
			"file_name": "Typing",
			"file": "uploads/process_risks/20240118104334AMRisk Register  -  Typing.pdf",
			"filepath": "uploads/process_risks/20240118104334AMRisk Register  -  Typing.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 47,
			"file_name": "Clear temper",
			"file": "uploads/process_risks/20240118104429AMRisk Register - Clear Temper.pdf",
			"filepath": "uploads/process_risks/20240118104429AMRisk Register - Clear Temper.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 48,
			"file_name": "Receipting and Banking",
			"file": "uploads/process_risks/20240118104800AMRisk Register -  Receipting and Banking.pdf",
			"filepath": "uploads/process_risks/20240118104800AMRisk Register -  Receipting and Banking.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 49,
			"file_name": "Meter reading",
			"file": "uploads/process_risks/20240118104919AMRisk Register - Meter Reading.pdf",
			"filepath": "uploads/process_risks/20240118104919AMRisk Register - Meter Reading.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 50,
			"file_name": "New connection (non standard j",
			"file": "uploads/process_risks/20240118105003AMRisk Register - New Connection (Non Standard Job).pdf",
			"filepath": "uploads/process_risks/20240118105003AMRisk Register - New Connection (Non Standard Job).pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 51,
			"file_name": "New connection (standard job)",
			"file": "uploads/process_risks/20240118105024AMRisk Register - New Connection (Standard Job).pdf",
			"filepath": "uploads/process_risks/20240118105024AMRisk Register - New Connection (Standard Job).pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 52,
			"file_name": "Resolving billing exceptions",
			"file": "uploads/process_risks/20240118105123AMRisk Register - Resolving Billing Exception.pdf",
			"filepath": "uploads/process_risks/20240118105123AMRisk Register - Resolving Billing Exception.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 53,
			"file_name": "Tariff change ",
			"file": "uploads/process_risks/20240118105315AMRisk Register -003-024 Tarrif change process.pdf",
			"filepath": "uploads/process_risks/20240118105315AMRisk Register -003-024 Tarrif change process.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 54,
			"file_name": "Clear credit request",
			"file": "uploads/process_risks/20240118105359AMRisk Register -003-025 Clear Credit request process.pdf",
			"filepath": "uploads/process_risks/20240118105359AMRisk Register -003-025 Clear Credit request process.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 55,
			"file_name": "Disconnection reconnection",
			"file": "uploads/process_risks/20240118105438AMRisk Register -003-027 Disconnection reconnection process.pdf",
			"filepath": "uploads/process_risks/20240118105438AMRisk Register -003-027 Disconnection reconnection process.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 56,
			"file_name": "Meter reading",
			"file": "uploads/process_risks/20240118105531AMRisk Register 03-003 Meter Reading process.pdf",
			"filepath": "uploads/process_risks/20240118105531AMRisk Register 03-003 Meter Reading process.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 1
		},
		{
			"id": 57,
			"file_name": "Faulty transformer replacement",
			"file": "uploads/process_risks/20240118110407AMRisk Register - 03-018 FAULTY TRANSFORMER CHANGE PROCESS.pdf",
			"filepath": "uploads/process_risks/20240118110407AMRisk Register - 03-018 FAULTY TRANSFORMER CHANGE PROCESS.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 58,
			"file_name": "Clear temper",
			"file": "uploads/process_risks/20240118110434AMRisk Register -003-015 Clear Temper request process.pdf",
			"filepath": "uploads/process_risks/20240118110434AMRisk Register -003-015 Clear Temper request process.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 59,
			"file_name": "System reinforcement project",
			"file": "uploads/process_risks/20240118110515AMRisk Register - 03-019 SYSTEM REINFORCEMENT PROJECT PROCESS.pd",
			"filepath": "uploads/process_risks/20240118110515AMRisk Register - 03-019 SYSTEM REINFORCEMENT PROJECT PROCESS.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 60,
			"file_name": "Reticulation project",
			"file": "uploads/process_risks/20240118110542AMRisk Register - 03-020 RETICULATION  PROJECT PROCESS.pdf",
			"filepath": "uploads/process_risks/20240118110542AMRisk Register - 03-020 RETICULATION  PROJECT PROCESS.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 61,
			"file_name": "Meter change",
			"file": "uploads/process_risks/20240118110608AMRisk Register - 03-021 METER CHANGE PROCESS.pdf",
			"filepath": "uploads/process_risks/20240118110608AMRisk Register - 03-021 METER CHANGE PROCESS.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 2
		},
		{
			"id": 62,
			"file_name": "Stores inspection",
			"file": "uploads/process_risks/20240118112838AMSTORES INSPECTION PROCEDURE RISK REGISTER (00000002).pdf",
			"filepath": "uploads/process_risks/20240118112838AMSTORES INSPECTION PROCEDURE RISK REGISTER (00000002).pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 63,
			"file_name": "Goods receipt note and invoice",
			"file": "uploads/process_risks/20240118112943AMGOODS RECEIPT NOTE AND INVOICE PROCESSING RISK.pdf",
			"filepath": "uploads/process_risks/20240118112943AMGOODS RECEIPT NOTE AND INVOICE PROCESSING RISK.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 64,
			"file_name": "Stock replenishment",
			"file": "uploads/process_risks/20240118113014AMSTOCK REPLENISHMENT RISK REG.pdf",
			"filepath": "uploads/process_risks/20240118113014AMSTOCK REPLENISHMENT RISK REG.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 65,
			"file_name": "Stores issuing",
			"file": "uploads/process_risks/20240118113059AMSTORES ISSUING PROCEDURE RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118113059AMSTORES ISSUING PROCEDURE RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 66,
			"file_name": "Stores recieving",
			"file": "uploads/process_risks/20240118113125AMSTORES RECEIVING PROCEDURE RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118113125AMSTORES RECEIVING PROCEDURE RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 67,
			"file_name": "Recoverable debtors",
			"file": "uploads/process_risks/20240118113329AMZETDC HRE FIN 03001 RECOVERABLE DEBTORS  REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118113329AMZETDC HRE FIN 03001 RECOVERABLE DEBTORS  REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 68,
			"file_name": "Petty cash",
			"file": "uploads/process_risks/20240118113341AMZETDC HRE FIN 03002 PETTY CASH REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118113341AMZETDC HRE FIN 03002 PETTY CASH REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 69,
			"file_name": "Bank reconcialation",
			"file": "uploads/process_risks/20240118113403AMZETDC HRE FIN 03003 BANK RECONCILLIATION REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118113403AMZETDC HRE FIN 03003 BANK RECONCILLIATION REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 70,
			"file_name": "Staff debtors",
			"file": "uploads/process_risks/20240118113419AMZETDC HRE FIN 03004 STAFF DEBTORS REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118113419AMZETDC HRE FIN 03004 STAFF DEBTORS REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 71,
			"file_name": "Asset Capitalisation",
			"file": "uploads/process_risks/20240118113438AMZETDC HRE FIN 03005 ASSET CAPITALISATION REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118113438AMZETDC HRE FIN 03005 ASSET CAPITALISATION REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 72,
			"file_name": "ACE",
			"file": "uploads/process_risks/20240118113458AMZETDC HRE FIN 03006 APPLICATION FOR CAPITAL EXPENDITURE REGIST",
			"filepath": "uploads/process_risks/20240118113458AMZETDC HRE FIN 03006 APPLICATION FOR CAPITAL EXPENDITURE REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 73,
			"file_name": "Creditors payment",
			"file": "uploads/process_risks/20240118113535AMZETDC HRE FIN 03007 CREDITORS PAYMENT REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118113535AMZETDC HRE FIN 03007 CREDITORS PAYMENT REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 74,
			"file_name": "Intercompany debtors",
			"file": "uploads/process_risks/20240118113549AMZETDC HRE FIN 03008 INTERCOMPANY DEBTORS REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118113549AMZETDC HRE FIN 03008 INTERCOMPANY DEBTORS REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 3
		},
		{
			"id": 75,
			"file_name": "Funeral assistance",
			"file": "uploads/process_risks/20240118113714AMZETDC HRE FUNERAL ASSISTANCE Risk register .pdf",
			"filepath": "uploads/process_risks/20240118113714AMZETDC HRE FUNERAL ASSISTANCE Risk register .pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 76,
			"file_name": "Emergency preparedness",
			"file": "uploads/process_risks/20240118113742AMEmergency Preparedness and Response  Risk register.pdf",
			"filepath": "uploads/process_risks/20240118113742AMEmergency Preparedness and Response  Risk register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 77,
			"file_name": "Occupational accident",
			"file": "uploads/process_risks/20240118113814AMOcc Accident Risk register.pdf",
			"filepath": "uploads/process_risks/20240118113814AMOcc Accident Risk register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 78,
			"file_name": "Recruitment and selection",
			"file": "uploads/process_risks/20240118113842AMRecruitment and selection risk register.pdf",
			"filepath": "uploads/process_risks/20240118113842AMRecruitment and selection risk register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 79,
			"file_name": "Asset acquisition",
			"file": "uploads/process_risks/20240118113926AMAsset Acquisition RR.pdf",
			"filepath": "uploads/process_risks/20240118113926AMAsset Acquisition RR.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 80,
			"file_name": "Emergency response",
			"file": "uploads/process_risks/20240118114029AMEmergency Response.pdf",
			"filepath": "uploads/process_risks/20240118114029AMEmergency Response.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 81,
			"file_name": "Employee termination",
			"file": "uploads/process_risks/20240118114104AMEmployee Termimation.pdf",
			"filepath": "uploads/process_risks/20240118114104AMEmployee Termimation.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 82,
			"file_name": "Performance management",
			"file": "uploads/process_risks/20240118114156AMZETDC HRE HR PERFORMANCE MANAGEMENT REGISTER - Copy.pdf",
			"filepath": "uploads/process_risks/20240118114156AMZETDC HRE HR PERFORMANCE MANAGEMENT REGISTER - Copy.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 83,
			"file_name": "Staff special fund",
			"file": "uploads/process_risks/20240118114231AMSTAFF SPECIAL FUND.pdf",
			"filepath": "uploads/process_risks/20240118114231AMSTAFF SPECIAL FUND.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 84,
			"file_name": "Death levy",
			"file": "uploads/process_risks/20240118114316AMZETDC HRE DEATH LEVY .pdf",
			"filepath": "uploads/process_risks/20240118114316AMZETDC HRE DEATH LEVY .pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 6
		},
		{
			"id": 85,
			"file_name": "Claim processing",
			"file": "uploads/process_risks/20240118115500AM001 Claim processing Risk register.pdf",
			"filepath": "uploads/process_risks/20240118115500AM001 Claim processing Risk register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 8
		},
		{
			"id": 86,
			"file_name": "Fire accident handling",
			"file": "uploads/process_risks/20240118115533AM003 Fire accident handling process- risk register.pdf",
			"filepath": "uploads/process_risks/20240118115533AM003 Fire accident handling process- risk register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 8
		},
		{
			"id": 87,
			"file_name": "Crime investigation",
			"file": "uploads/process_risks/20240118115600AM002 CRIME INVESTIGATION PROCESS RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118115600AM002 CRIME INVESTIGATION PROCESS RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 8
		},
		{
			"id": 88,
			"file_name": "Cash in transit",
			"file": "uploads/process_risks/20240118115627AM004 Cash in transit process Risk register.docx",
			"filepath": "uploads/process_risks/20240118115627AM004 Cash in transit process Risk register.docx",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 8
		},
		{
			"id": 89,
			"file_name": "Incident management",
			"file": "uploads/process_risks/20240118115817AMZETDC HRE IT 03_001 INCIDENT MANAGEMENT RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118115817AMZETDC HRE IT 03_001 INCIDENT MANAGEMENT RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 9
		},
		{
			"id": 90,
			"file_name": "Problem management",
			"file": "uploads/process_risks/20240118115835AMZETDC HRE IT 03_002 PROBLEM MANAGEMENT RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118115835AMZETDC HRE IT 03_002 PROBLEM MANAGEMENT RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 9
		},
		{
			"id": 91,
			"file_name": "Event management",
			"file": "uploads/process_risks/20240118115859AMZETDC HRE IT 03_003 EVENT MANAGEMENT RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118115859AMZETDC HRE IT 03_003 EVENT MANAGEMENT RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 9
		},
		{
			"id": 92,
			"file_name": "Request fulfilment",
			"file": "uploads/process_risks/20240118115942AMZETDC HRE IT 03_004 REQUEST FULFILMENT RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118115942AMZETDC HRE IT 03_004 REQUEST FULFILMENT RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 9
		},
		{
			"id": 93,
			"file_name": "Change management",
			"file": "uploads/process_risks/20240118120000PMZETDC HRE IT 03_005 CHANGE MANAGEMENT RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118120000PMZETDC HRE IT 03_005 CHANGE MANAGEMENT RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 9
		},
		{
			"id": 94,
			"file_name": "Access management",
			"file": "uploads/process_risks/20240118120021PMZETDC HRE IT 03_006 ACCESS MANAGEMENT RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118120021PMZETDC HRE IT 03_006 ACCESS MANAGEMENT RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 9
		},
		{
			"id": 95,
			"file_name": "Release and deployment",
			"file": "uploads/process_risks/20240118120042PMZETDC HRE IT 03_007 RELEASE AND DEPLOYMENT RISK REGISTER.pdf",
			"filepath": "uploads/process_risks/20240118120042PMZETDC HRE IT 03_007 RELEASE AND DEPLOYMENT RISK REGISTER.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 9
		},
		{
			"id": 96,
			"file_name": "IT added",
			"file": "uploads/process_risks/20240206104718AMCT REV ASS RISK REGISTER (1).pdf",
			"filepath": "uploads/process_risks/20240206104718AMCT REV ASS RISK REGISTER (1).pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 9
		},
		{
			"id": 97,
			"file_name": "Created at 23",
			"file": "uploads/process_risks/20240206105729AMFault Handling risk register.pdf",
			"filepath": "uploads/process_risks/20240206105729AMFault Handling risk register.pdf",
			"section": "2024-02-13 09:46:47.683313+00:00",
			"created_by": "2024-02-13 09:46:47.588092+00:00",
			"created_at": "2024-02-13",
			"updated_at": "2024-02-13",
			"region": "2024-02-13 09:46:47.649969+00:00",
			"cat_id": 9
		}
	]

    for file in files:
        dep_ = ""
        for dep in deps:
            if dep['id'] == file['cat_id']: 
            	dep_ = dep['name']

        process = Processes(
			filetype="RISK_OPPORTUNITY",
			filename=file['file_name'],
			department=dep_ if dep_ else None,
			sub_category="",
			filepath=file['filepath'],
			section=file['section'],
			region=file['region'],
			created_at=file['created_at'],
			updated_at=file['updated_at'],
			created_by=file['created_by']
		)
        process.save()
        
    return redirect('/process_maps/')

@login_required
def bulk_set_up(request):
	processes = Processes.objects.all()

	filetypes = set([proc.filetype for proc in processes])
 
	departments_list = []
	for proc in processes:
		found = False
		for obj in departments_list:
			if obj.get("department") == proc.department and obj.get("filetype") == proc.filetype:
				found = True
				break

		if found:
			print("Object found in the list")
		else:
			dep = {
				"department": proc.department,
				"filetype": proc.filetype
			}
			departments_list.append(dep)
   
	sub_categories = []
	for proc in processes:
   
		found = False
		for obj in sub_categories:
			if obj.get("sub_category") == proc.sub_category and obj.get("filetype") == proc.filetype and obj.get("department") == proc.department:
				found = True
				break

		if not found:
			if proc.sub_category:
				sub = {
					"sub_category": proc.sub_category,
					"filetype": proc.filetype,
					"department": proc.department
				}
				sub_categories.append(sub)
		else:
			print("Object found in the list")
	
 
	# print("departments: ", departments_list)
	# print("sub_categories: ", sub_categories)
	# print("filetypes: ", filetypes)
 
	for _filetype in filetypes:
		filetype = File_Type(name=_filetype)
		filetype.save()
	
	for department in departments_list:
		_filetype = File_Type.objects.filter(name=department['filetype']).first()
		dep = FileSubType(
      		name=department['department'], 
        	filetype_id=_filetype
        )
		dep.save()
  
	print("sub_categories: ", sub_categories)
	for sub_category in sub_categories:
		_filetype = File_Type.objects.filter(name=sub_category['filetype']).first()
		if _filetype:
			_filesubtype = FileSubType.objects.filter(name=sub_category['department'], filetype_id=_filetype.id).first()
			if _filesubtype:
				sub = SubSubType(
					name=sub_category['sub_category'], 
					file_subtype_id=_filesubtype,
					file_type_id=_filetype
				)
				sub.save()
			else:
				print("No department found")
  
	return redirect('/process_maps/')
         
def save_file(f,file_path):
    if f:
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
                return True
            else:
                return False

@login_required
def download_file(request):

    file_id = request.GET['file_id']
    file_record = Processes.objects.filter(id=file_id).first()
    file_path = file_record.filepath

    # search for file in system
    try:
        base_directory_path = os.path.join(settings.BASE_DIR, file_path)
        return FileResponse(open(base_directory_path, 'rb'), content_type='application/pdf')
    except Exception as ex:
        print(ex)
        messages.error(request, "File not found, please check and upload again")

    return redirect('/processes/table/')
    # return render(request, 'processes/view_process.html', {'results': results,})

# ----------------------------
# Process Maps
@login_required
def view_internal(request):
   
    files = Processes.objects.filter(archived=False, filetype="INTERNAL_EXTERNAL").all()
   
    return render(request, 'process_maps/ict.html',
                  { "files": files,
                    "page_title": "Internal & External Issues"},
                    )

@login_required
def view_stakeholder(request):
   
    files = Processes.objects.filter(archived=False, filetype="STAKEHOLDER_RELATIONS").all()
   
    return render(request, 'process_maps/ict.html',
                  { "files": files,
                    "page_title": "Stakeholder Relations"},
                    )
    
@login_required
def view_Client(request):
   
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Commercial", sub_category="client interaction")
   
    return render(request, 'process_maps/ict.html',
                  { "files": files,
                    "page_title": "Client Interaction Process Maps"},
                    )
    
@login_required
def view_payment(request):
   
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Commercial", sub_category="payment")
   
    return render(request, 'process_maps/ict.html',
                  { "files": files,
                    "page_title": "Payment Process Maps"},
                    )
@login_required
def view_revenue_assurance(request):
   
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Commercial", sub_category="revenue assuarance")
    print("files: ", files)
    return render(request, 'process_maps/ict.html',
                  { "files": files,
                    "page_title": "Revenue Process Maps"},
                    )
@login_required
def view_eng_nde(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Engineering", sub_category="Network Development")
    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Network Development", "url_path": url_path} )

#Project procesess
@login_required
def view_eng_transport(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Engineering", sub_category="Transport")

    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Transport", "url_path": url_path} )

@login_required
def view_Maintenance(request):
        files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Engineering", sub_category="Operations and Maintenance")

        url_path = request.path.split("/")
        return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Operations and Maintenance", "url_path": url_path} )

@login_required
def view_eng_districts(request):
        files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Engineering", sub_category="Districts")

        url_path = request.path.split("/")
        return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Districts", "url_path": url_path} )
        
@login_required
def view_Engineering(request):
    
    return render(request, 'process_maps/eng.html',
                  {
                    "page_title": "Engineering Process Maps"})

#NEW ENGINEERING LIST OF PROCESS MAPS

@login_required
def view_Commercial(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Commercial")

    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Commercial", "url_path": url_path} )
    
@login_required
def view_management(request):
    file_type = File_Type.objects.filter(name="PROCESS_MAPS").first()
    print("file_type: ", file_type)
    file_subtype = FileSubType.objects.filter(name="Management", filetype_id=file_type).first()
    print("file_subtype: ", file_subtype)
    file_subsubtype = SubSubType.objects.filter(file_subtype_id=file_subtype.id, file_type_id=file_type).all()
    print("file_subsubtype: ", file_subsubtype)

    folders_list = []
    for folder in file_subsubtype:
        url = ""
        if folder.name.count(" ") > 0:
            url = folder.name.replace(" ", "_").lower()
        else:
            url = folder.name.lower()  
            
        temp = {
            "id": folder.id,
            "name": folder.name,
            "url": url
        }
        folders_list.append(temp)
    url_path = request.path.split("/")
    
    print("folders_list: ", folders_list)
    return render(request, 'process_maps/management.html',{
        "folders": folders_list,  "page_title": "Management Documents", "url_path": url_path} )
    
    
@login_required
def view_managements(request, folder_name):
    name = ""
    if folder_name.count("_") > 0:
        name = folder_name.replace("_", " ").lower()
    else:
        name = folder_name.lower()
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Management", sub_category=name).all()

    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Management", "url_path": url_path} )
  
@login_required
def view_stakeholder_relations(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Stakeholder Relations")

    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Stakeholder Relations", "url_path": url_path} )

@login_required
def view_legal_services(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Legal Services")

    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Legal Services", "url_path": url_path} )
    
@login_required
def fetch_processes(request, filetype, subtype, subsubtype):
    
    files = Processes.objects.filter(archived=False, filetype=filetype, department=subtype, sub_category=subsubtype).all()

    url_path = request.path.split("/")
    title = (subtype + " " + subsubtype).capitalize()
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": title, "url_path": url_path} )


@login_required
def view_Finance(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="FINANCE")

    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "FINANCE process map Files", "url_path": url_path} )

@login_required
def view_ICT(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="ICT")
    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "ICT process map Files", "url_path": url_path} )

@login_required
def view_HR(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="HUMAN RESOURCES")    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Human resources process map Files", "url_path": url_path} )

@login_required
def view_finance(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="Finance")    
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Human resources process map Files", "url_path": url_path} )

@login_required
def view_procurement(request):

    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="procurement")    
    print(files)
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Procurement Processes", "url_path": url_path} )

@login_required
def view_managementx(request):
    return render(request,'processes/management.html',{})

@login_required
def view_Risk(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_MAPS", department="RISK MANAGEMENT")    
    print(files)
    url_path = request.path.split("/")
    return render(request, 'process_maps/ict.html',{
        "files": files,  "page_title": "Risk Processes", "url_path": url_path} )

# -----------------------------
# Process Risks
@login_required
def risk_Commercial(request):
    
    files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="Commercial")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Commercial Process Risks"},
                    )


@login_required
def risk_Procurement(request):
    
    procurement_files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="Procurement")
    return render(request, 'process_maps/ict.html',
                  {"files": procurement_files,
                    "page_title": "Procurement Process Risks"})

@login_required
def risk_Engineering(request):
    
    return render(request, 'process_risks/eng_index.html',
                  {"page_title": "Engineering Process Risks"})

@login_required
def risk_eng_nde(request):
    
    eng_files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="Engineering", sub_category="Network Development").all()
    print(eng_files)
    return render(request, 'process_maps/ict.html',
                  {"files": eng_files,
                    "page_title": "Network Development Risks"})

@login_required
def risk_eng_transport(request):
    
    eng_files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="Engineering", sub_category="Transport").all()
    print(eng_files)
    return render(request, 'process_maps/ict.html',
                  {"files": eng_files,
                    "page_title": "Transport Risks"})
    
@login_required
def risk_eng_districts(request):
    
    eng_files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="Engineering", sub_category="Districts").all()
    print(eng_files)
    return render(request, 'process_maps/ict.html',
                  {"files": eng_files,
                    "page_title": "Districts Risks"})

@login_required
def risk_eng_maintenance(request):
    
    eng_files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="Engineering", sub_category="Maintenance").all()
    print(eng_files)
    return render(request, 'process_maps/ict.html',
                  {"files": eng_files,
                    "page_title": "Operations and Maintenance Risks"})
    
@login_required
def risk_Finance(request):
    
    finance_files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="Finance")
    return render(request, 'process_maps/ict.html',
                  {"files": finance_files,
                    "page_title": "Finance Process Risks"})

@login_required
def risk_ICT(request):
    
    ict_files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="ICT")
    return render(request, 'process_maps/ict.html',
                  {"files": ict_files,
                    "page_title": "ICT Process Risks"})

@login_required
def risk_HR(request):
    
    hr_files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="Human Resources")
    return render(request, 'process_maps/ict.html',
                  {"files": hr_files,
                    "page_title": "HR Process Risks"})

@login_required
def risk_Risk(request):
    
    risk_files = Processes.objects.filter(archived=False, filetype="RISK_OPPORTUNITY", department="Risk Management")
    return render(request, 'process_maps/ict.html',
                  {"files": risk_files,
                    "page_title": "Risk Mnangement Process Risks"})


# -------------------------------------------
#First page after clicking view process maps
@login_required
def view_img(request):
    return render(request,'processes/display.html',{})

@login_required
def download_static(request, filename):
    file_path = os.path.join(settings.STATIC_ROOT, "documents", filename)
    if os.path.exists(file_path):
        with open(file_path, 'rb') as f:
            response = FileResponse(f, content_type='application/pdf')  # Adjust content type as needed
            response['Content-Disposition'] = 'attachment; filename="{}"'.format(filename)
            return response
    else:
        # Handle file not found scenario
        pass

# Search processes and procedures
@login_required
def file_search(request):
    keyword = request.GET.get('keyword', '')
    pattern = r"\b" + str(keyword).lower() + r"\b"
    match = re.search(pattern, keyword)
    if match:
       keyword=match.group()
    results = []
    if keyword:
        # file_path = request.FILES['uploaded_file']

        file_path = ''
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES ['uploaded_file']
                file_path = 'uploads/process_maps/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + uploaded_file.name
                save_file(uploaded_file,file_path)
        except Exception as ex:
            print("Error:",ex)

#FORMS VIEWS
@login_required
def new_view(request):
    return render(request, 'processes/forms/new_view.html',{"page_title": "PROCESSES AND PROCEDURES (clause 4.4)"})

@login_required
def forms_index(request):
    return render(request,'processes/forms/forms_index.html', {"page_title": "FORMS"})

@login_required
def engineering_forms(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_FORMS", department="Engineering")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Engineering Forms"},
                    )

@login_required
def procurement_forms(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_FORMS", department="Procurement")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Procurement Forms"},
                    )
    
@login_required
def finance_forms(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_FORMS", department="Finance")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Finance Forms"},
                    )

@login_required
def hr_forms(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_FORMS", department="HR")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title":"Human Resources Forms"},
                    )

@login_required
def commercial_forms(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_FORMS", department="Commercial")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title":"Commercial Forms"},
                    )

@login_required
def it_forms(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_FORMS", department="ICT")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title":"Information Technology Forms"},
                    )

@login_required
def risk_forms(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCESS_FORMS", department="Risk")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title":"Risk Management Forms"},
                    )


#PROCEDURES AND WORK INSTRUCTIONS
@login_required
def viewWorkInstr(request):
        return render(request, 'processes/procedures_workInstr/home.html', {"page_title":"PROCEDURES AND WORK INSTRUCTIONS (clause 7.5)"})
        
@login_required
def viewEngProcedureHome(request):
        return render(request, 'processes/procedures_workInstr/eng_proceduresHome.html', {"page_title":"Engineering Procedures and Work Instructions"})
    
@login_required
def viewCommercialProcedureHome(request):
        return render(request, 'processes/procedures_workInstr/com_procedureHome.html', {"page_title":"Commercial Procedures and Work Instructions"})
    
@login_required
def viewFinanceProcedures(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="Finance")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Finance Procedures and Work Instructions Files"},
                    )

@login_required
def viewHRProcedures(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="HR")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Human Resources Procedures and Work Instructions Files"},
                    )
    
@login_required
def viewSRProcedures(request):
    return render(request, 'processes/procedures_workInstr/stakeholderRelations.html', {"page_title":"Stakeholder Relations Procedures and Work Instructions Files"})
    
@login_required
def viewLegalProcedures(request):
    return render(request, 'processes/procedures_workInstr/legal_procedures.html', {"page_title":"Legal Procedures and Work Instructions Files"})

#PROCESSES
@login_required
def view_it(request):
    return render(request,'processes/it_process.html', {})

@login_required
def view_engineeringlist(request):
    return render(request,'processes/engineering.html', {})

#Engineering Process maps
@login_required
def view_commercial(request):
    return render(request,'processes/commercial.html',{})

@login_required
def view_client(request):
    return render(request,'processes/client.html',{})

@login_required
def view_revenue(request):
    return render(request,'processes/revenue.html',{})

@login_required
def view_payment(request):
    return render(request,'processes/payment.html',{})
#end

#Engineering Process maps
@login_required
def view_maintenance(request):
    return render(request,'processes/maintenance_processes.html',{})

@login_required
def view_planning(request):
    return render(request,'processes/planning_processes.html',{})

@login_required
def view_project(request):
    return render(request,'processes/project_processes.html',{})

# Procedures
@login_required
def viewProcurementProcedures(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="Risk")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Procurement Procedures and Work Instructions Files"},
                    )


@login_required
def viewICTProcedures(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="ICT")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "ICT Procedures and Work Instructions"})

@login_required
def viewICT_WorkInstr(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="ICT", sub_category="planning")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "ICT Planning Procedures and Work Instructions Files"},
                    )


@login_required
def viewEng_PlanningProcedure(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="Engineering", sub_category="planning")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Engineering Planning Procedures and Work Instructions Files"},
                    )

@login_required
def viewEng_MaintananceProcedure(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="Engineering", sub_category="maintanance")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Engineering Maintanance Procedures and Work Instructions Files"},
                    )

@login_required
def viewEng_ProjectsProcedure(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="Engineering", sub_category="projects")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Engineering Projects Procedures and Work Instructions Files"},
                    )
    
@login_required
def viewRiskProcedures(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="Risk")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Risk Management Procedures and Work Instructions Files"},
                    )

@login_required
def viewClientInteractionProcedures(request):
	
	files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="Commercial", sub_category="client interaction")
	print("files: ", files)
 
	return render(request, 'process_maps/ict.html',
					{"files": files,
					"page_title": "Client Interaction Procedures and Work Instructions Files"},
					)

@login_required
def viewPaymentProcedures(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="Commercial", sub_category="payment")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Payment Procedures and Work Instructions Files"},
                    )

@login_required
def viewRevenueAssuranceProcedures(request):
    
    files = Processes.objects.filter(archived=False, filetype="PROCEDURE_WORK_INSTRUCTIONS", department="Commercial", sub_category="revenue assurance")

    return render(request, 'process_maps/ict.html',
                  {"files": files,
                    "page_title": "Revenue Assurance Procedures and Work Instructions Files"},
                    )

@login_required
def view_Map(request):
    return render(request, 'process_maps/process_map_diagram.html',
                  
            )
