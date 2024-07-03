import re
from django.shortcuts import render, redirect
from django.http import FileResponse, JsonResponse
from datetime import datetime
import json, os
from django.conf import settings
from django.contrib import messages

from it.users.models import CostCenter, Regions, Sections
from utils.save_file import save_file
from .models import Categories, First_Category, Secondary_Category, Filetype
from django.shortcuts import render
from django.db.models import Q
from django.contrib.auth.decorators import login_required

from utils.helper_functions import get_kc_dict

from .models import KnowledgeCenter
from django.core.files.storage import FileSystemStorage

# Create your views here.
@login_required
def create(request):
    url_path = request.path.split("/")
    if request.method == 'POST':
        # something
        print("post data: ", request.POST)
        user = request.user
        filename = request.POST['filename']
        filetype = request.POST['category_id']
        section = request.POST['section']
        region = request.POST['region']
        subtype1 = ""
        subtype2 = ""
        try:
            if 'subtype1' in request.POST:
                subtype1 = request.POST['subtype1']
            if 'subtype2' in request.POST:
                subtype2 = request.POST['subtype2']
        except Exception as ex:
            # messages.error(request, "Error uploading file: "+str(ex))
            print("Error:",ex)
        
        file_path = ''
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES['uploaded_file']
                root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'knowledge_center')
                fs = FileSystemStorage(location=root_dir)
                filename_ = fs.save(uploaded_file.name, uploaded_file)
                file_url = "uploads" + os.path.sep + "knowledge_center" + os.path.sep + filename_
                print("file_url: ", file_url)
                # save_file(uploaded_file,file_path)        
                file_type= Filetype.objects.filter(id=filetype).first() if filetype else None
                subtype1_ = First_Category.objects.filter(id=subtype1).first() if subtype1 else None
                subtype2_ = Secondary_Category.objects.filter(id=subtype2).first() if subtype2 else None
                
                try:
                    region_ = Regions.objects.filter(id=region).first() if region else None
                    section_ = Sections.objects.filter(id=section).first() if section else None
                    cost_center = CostCenter.objects.filter(code=section_.code).first() if section_ else None
                except Exception as ex:
                    region_ = None
                    section_ = None
                    cost_center = None
                    messages.error(request, "Error uploading file: "+str(ex))
                    print(ex)
                
                um = KnowledgeCenter(
                    filename= filename, # uploaded_file.name,
                    file_type= file_type.name if file_type else "",
                    file_type_id = file_type,
                    filepath = file_url,
                    section = section,
                    region = region,
                    section_id= section_,
                    sub_category_1 = subtype1_.name if subtype1_ else "",
                    subtype = subtype1_,
                    sub_category_2 = subtype2_.name if subtype2_ else "",
                    subsubtype = subtype2_,
                    region_id=region_,
                    cost_center=cost_center,
                    done_by=user,
                    created_on = datetime.now(),
                    updated_on = datetime.now(),
                    created_at = datetime.now().date(),
                    updated_at = datetime.now().date(),
                    created_by = user.username,
                )
                um.save()
                messages.success(request, "File uploaded successfully")
        except Exception as ex:
            messages.error(request, "Error uploading file")
            print("Error:",ex)
        
        return redirect('/knowledge_center/create')   
    
    regions = Regions.objects.all()
    sections = Sections.objects.all()
    cost_centers = CostCenter.objects.all()
    filetypes = Filetype.objects.all()
    return render(request, 'knowledge-center/create.html', {"url_path": url_path, "regions": regions, "sections": sections, "cost_centers": cost_centers, "filetypes": filetypes})

@login_required
def archive_file(request, file_id):

    try:
        um = KnowledgeCenter.objects.filter(id=file_id).first()
        um.archived=True
        um.save()
        messages.success(request, "File archived successfully")
    except Exception as ex:
        messages.error(request, "Error archiving file")
        print("Error:",ex)
    
    return redirect('/knowledge_center/knowledge_center_files')

@login_required
def unarchive_file(request, file_id):

    try:
        um = KnowledgeCenter.objects.filter(id=file_id).first()
        um.archived=False
        um.save()
        messages.success(request, "File unarchived successfully")
    except Exception as ex:
        messages.error(request, "Error unarchiving file")
        print("Error:",ex)
    
    return redirect('/knowledge_center/knowledge_center_files')

@login_required
def view_files(request):
    
    # KnowledgeCenter.migrate_filetypes()
    # Secondary_Category.migrate_duplicates()
    files = KnowledgeCenter.objects.filter(archived=False).all()
    
    files_list = []
    for file in files:
        new_file = {
            "id": file.id,
            "filename": file.filename,
            "filetype": file.file_type,
            "section": file.section_id.section if file.section_id else "",
            "subcategory1": file.sub_category_1,
            "subcategory2": file.sub_category_2,
            "region": file.region_id.region if file.region_id else "",
            "archived": file.archived,
            "created_by": file.done_by.first_name + " " + file.done_by.last_name if file.done_by else "",
            "created_at": file.created_on.astimezone().strftime("%Y-%m-%d %H:%M:%S") if file.created_on else "",
        }
        files_list.append(new_file)
    
    files_list = sorted(files_list, key=lambda x: x['created_at'], reverse=True)
    context = json.dumps(files_list, default=str)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_files.html', {"context": context, "url_path": url_path, "page": "kc_all"})

@login_required
def view_archived_files(request):
    
    files = KnowledgeCenter.objects.filter(archived=True).all()
    
    files_list = []
    for file in files:
        new_file = {
            "id": file.id,
            "filename": file.filename,
            "filetype": file.file_type,
            "section": file.section_id.section if file.section_id else "",
            "subcategory1": file.sub_category_1,
            "subcategory2": file.sub_category_2,
            "region": file.region_id.region if file.region_id else "",
            "archived": file.archived,
            "created_by": file.created_by,
            "created_at": file.created_on.astimezone().strftime("%Y-%m-%d %H:%M:%S") if file.created_on else "",
        }
        files_list.append(new_file)
    
    context = json.dumps(files_list, default=str)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_files.html', {"context": context, "url_path": url_path, "page": "kc_archived"})

@login_required
def view_by_category(request):
    
    files = KnowledgeCenter.objects.all()
    
    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    # for file in files:
    #     new_file = {
    #         "id": file.id,
    #         "filename": file.filename,
    #         "filetype": file.file_type,
    #         "section": file.section,
    #         "subcategory1": file.sub_category_1,
    #         "subcategory2": file.sub_category_2,
    #         "region": file.region,
    #         "created_by": file.created_by,
    #         "created_at": file.created_at,
    #     }
    #     files_list.append(new_file)
    
    # context = json.dumps(files_list, default=str)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_myfiles.html', {"context": new_dict, "url_path": url_path})

@login_required
def get_category(request, file_type, cat_1, cat_2):
    file_ = KnowledgeCenter.objects.filter(file_type=file_type).all()
    file_ = KnowledgeCenter.objects.filter(file_type=file_type, cat_1=cat_1).all()
    file_ = KnowledgeCenter.objects.filter(file_type=file_type, cat_1=cat_1, cat_2=cat_2).all()

@login_required
def view_myfiles(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_myfiles.html', {"url_path": url_path})

@login_required
def download_file(request):

    file_id = request.GET['file_id']
    file_record = KnowledgeCenter.objects.filter(id=file_id).first()
    file_path = file_record.filepath

    # search for file in system
    try:
        # base_directory_path = request.build_absolute_uri(settings.MEDIA_URL + file_path)
        base_directory_path = os.path.join(settings.BASE_DIR, file_path)
        print("base_directory_path: ", base_directory_path)
        return FileResponse(open(base_directory_path, 'rb'), content_type='application/pdf')
    except Exception as ex:
        print(ex)

    return redirect('/knowledge_center/knowledge_center_files')

@login_required
def edit_file(request, file_id):
    url_path = request.path.split("/")
    if request.method == 'GET':
        print("file_id: ", file_id)
        file_record = KnowledgeCenter.objects.filter(id=file_id).first()
        # fetch section code

        url_path = request.path.split("/")
        regions = Regions.objects.all()
        sections = Sections.objects.all()
        cost_centers = CostCenter.objects.all()
        filetypes = Filetype.objects.all()
        
        return render(request, 'knowledge-center/edit_file.html', {"record": file_record, "url_path": url_path, "regions": regions, "sections": sections, "cost_centers": cost_centers, "filetypes": filetypes}) 
    
    if request.method == 'POST':
        # something
        print("post data: ", request.POST)
        user = request.user
        id = request.POST['id']
        filename = request.POST['filename']
        filetype = request.POST['category_id']
        section = request.POST['section']
        subtype1 = ""
        if 'subtype1' in request.POST:
            subtype1 = request.POST['subtype1']
        subtype2 = ""
        if 'subtype2' in request.POST:
            subtype2 = request.POST['subtype2']
        region = request.POST['region']
        
        file_url = ''
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES ['uploaded_file']
                root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'knowledge_center')
                fs = FileSystemStorage(location=root_dir)
                filename_ = fs.save(uploaded_file.name, uploaded_file)
                file_url = "uploads" + os.path.sep + "knowledge_center" + os.path.sep + filename_
                print("file_url: ", file_url)
        except Exception as ex:
            # messages.error(request, "Error uploading file")
            print("Error:",ex)

        file_type= Filetype.objects.filter(id=filetype).first() if filetype else None
        subtype1_ = First_Category.objects.filter(id=subtype1).first() if subtype1 else None
        subtype2_ = Secondary_Category.objects.filter(id=subtype2).first() if subtype2 else None
                
        try:
            region_ = Regions.objects.filter(id=region).first() if region else None
            section_ = Sections.objects.filter(id=section).first() if section else None
            cost_center = CostCenter.objects.filter(code=section_.code).first() if section_ else None
        except Exception as ex:
            region_ = None
            section_ = None
            cost_center = None
            messages.error(request, "Error uploading file: "+str(ex))
            print(ex)
                    
        um = KnowledgeCenter.objects.filter(id=id).first()
        um.filename= filename if filename else um.filename
        um.file_type= file_type.name if file_type else um.file_type
        um.file_type_id = file_type if file_type else um.file_type_id
        um.filepath = file_url if file_url else um.filepath
        um.section= section if section else um.section
        um.sub_category_1 = subtype1_.name if subtype1_ else um.sub_category_1
        um.subtype = subtype1_ if subtype1_ else um.subtype
        um.sub_category_2 = subtype2_.name if subtype2_ else um.sub_category_2
        um.subsubtype = subtype2_ if subtype2_ else um.subsubtype
        um.region=region if region else um.region
        um.updated_at = datetime.now().date()
        um.region_id = region_ if region_ else um.region_id
        um.section_id = section_ if section_ else um.section_id
        um.cost_center = cost_center if cost_center else um.cost_center
        um.done_by = user
        um.updated_on = datetime.now()

        um.save()
        messages.success(request, "File updated successfully")
        return redirect('/knowledge_center/edit_file/' + str(id))   
    regions = Regions.objects.all()
    sections = Sections.objects.all()
    cost_centers = CostCenter.objects.all()
    filetypes = Filetype.objects.all()
    
    return render(request, 'knowledge-center/edit_file.html', {"url_path": url_path, "regions": regions, "sections": sections, "cost_centers": cost_centers, "filetypes": filetypes})


@login_required
def get_files(request, file_type_id):
    if request.method == "GET":
        # Connect to the database and query for relevant options
        
        options = First_Category.objects.filter(file_type_id=file_type_id).all()

        options_list = []

        for op in options:
            newobj = {
                "id": op.id,
                "file_type_id": op.file_type_id,
                "name": op.name,
                
            }
            options_list.append(newobj)
        

        return JsonResponse({"options": list(options_list)})
    
@login_required
def get_cat2(request, file_type, selected_cat):
    if request.method == "GET":
        # Connect to the database and query for relevant options
        
        second_option = Secondary_Category.objects.filter(file_id=file_type, category_id=selected_cat).all()

        print("cats: ", second_option)
        options_list = []

        for op in second_option:
            newobj = {
                "id": op.id,
                "file_id": op.file_id,
                "name": op.name,
                "category_id": op.category_id
                
            }
            options_list.append(newobj)

        print("option_list: ", options_list)

        return JsonResponse({"options_list": list(options_list)})
    

@login_required
def view_legislation(request):
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_legislation.html', {"page_title": "LEGISLATION", "url_path": url_path} )

@login_required
def view_legal_registers(request):
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/legal_registers.html', {"page_title": "Legal Registers", "url_path": url_path} )

@login_required
def legal_registers_departments(request, department):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="LEGISLATION", sub_category_1="Legal Registers", sub_category_2=department).all()
    
    url_path = request.path.split("/")
    title = department + " Legal Registers"
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": title, "url_path": url_path})

@login_required
def fetch_knowledge_center(request, filetype, subtype, subsubtype):
    
    files = []
    # if filetype and subtype and subsubtype:
    files = KnowledgeCenter.objects.filter(archived=False, file_type=filetype, sub_category_1=subtype, sub_category_2=subsubtype).all()
    url_path = request.path.split("/")
    title = (subsubtype + " " + subtype).capitalize()
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": title, "url_path": url_path})

@login_required
def view_ea(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_1="Electricity Acts")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Acts of Parliament", "url_path": url_path})


@login_required
def view_gl(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_1="General Legislation")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "General Legislation files", "url_path": url_path} )

@login_required
def view_si(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_1="Statutory Instruments")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Statutory Instruments files", "url_path": url_path} )


@login_required
def view_firstview(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    
    return render(request, 'knowledge-center/view_firstview.html', {
        "url_path": url_path,
        "page_title": "KNOWLEDGE CENTRE", 
        "results": []})


@login_required
def view_specifications(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_specifications.html', {"page_title": "SPECIFICATIONS", "results": [], "url_path": url_path})

@login_required
def view_commercial_spec(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="SPECIFICATIONS", sub_category_1="Commercial")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Commercial Files", "url_path": url_path} )

@login_required
def view_hr_spec(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="SPECIFICATIONS", sub_category_1="Human Resources")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Human Resources Files", "url_path": url_path} )

@login_required
def view_engineering_spec(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="SPECIFICATIONS", sub_category_1="Engineering")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{
        "files": files,  "page_title": "Specifications Engineering Files", "url_path": url_path} )

@login_required
def view_finance_spec(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="SPECIFICATIONS", sub_category_1="Finance")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{
        "files": files,  "page_title": "Specifications Finance Files", "url_path": url_path} )

@login_required
def view_ict_spec(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="SPECIFICATIONS", sub_category_1="ICT")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{
        "files": files,  "page_title": "Specifications ICT Files", "url_path": url_path} )

@login_required
def view_risk_spec(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="SPECIFICATIONS", sub_category_1="Risk")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Risk Files", "url_path": url_path} )

@login_required
def view_relations_spec(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="SPECIFICATIONS", sub_category_1="Stakeholder Relations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Stakeholder Relations Files", "url_path": url_path} )

@login_required
def view_legal_spec(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="SPECIFICATIONS", sub_category_1="Legal")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Legal Files", "url_path": url_path} )

@login_required
def view_procurement_spec(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="SPECIFICATIONS", sub_category_1="Procurement")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Procurement Files", "url_path": url_path} )

@login_required
def view_policies(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_policies.html',{"page_title": "POLICIES AND GUIDLINES", "url_path": url_path} )

@login_required
def view_commercial_policies(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="POLICIES & GUIDELINES", sub_category_1="Commercial").all()

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies and Guidlines Commercial files", "url_path": url_path} )

@login_required
def view_hr_policies(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="POLICIES & GUIDELINES", sub_category_1="Human Resources")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies Human Resources files", "url_path": url_path} )

@login_required
def view_engineering(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="POLICIES & GUIDELINES", sub_category_1="Engineering")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies and Guidelines Engineering Files", "url_path": url_path} )

@login_required
def view_finance_policies(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="POLICIES & GUIDELINES", sub_category_1="Finance")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html', {"files": files, "page_title": "Policies and Guidelines Finance Files", "url_path": url_path} )

@login_required
def view_ict_policies(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="POLICIES & GUIDELINES", sub_category_1="ICT")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html', {"files": files, "page_title": "Policies and Guidelines ICT Files", "url_path": url_path} )

@login_required
def view_risk_policies(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="POLICIES & GUIDELINES", sub_category_1="Risk")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies and Guidelines Risk Files", "url_path": url_path} )

@login_required
def view_index(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_index.html',{"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX", "url_path": url_path} )

@login_required
def view_reports(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Reports")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Reports Files", "url_path": url_path} )

@login_required
def view_protection(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Protection")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Protection Files", "url_path": url_path} )

@login_required
def view_earthing(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Earthing")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Earthing Files", "url_path": url_path} )

@login_required
def view_transformers(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Transformers")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Transformers Files", "url_path": url_path} )

@login_required
def view_fuses(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Fuses")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Fuses Files", "url_path": url_path} )

@login_required
def view_imm(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Instruments, Meters and Metering")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Instruments Meters and Metering Files", "url_path": url_path} )

@login_required
def view_tg(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Transformer Gaskets")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Transformer Gaskets Files", "url_path": url_path} )

@login_required
def view_switchgear(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Switchgear")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Switchgear Files", "url_path": url_path} )

@login_required
def view_por(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Post Office Regulations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Post Office Regulations Files", "url_path": url_path} )

@login_required
def view_io(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="io")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Insulating oils Files", "url_path": url_path} )
@login_required
def view_1_10(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_1_10.html',{"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(1-10)", "url_path": url_path} )


@login_required
def view_11_20(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_11_20.html',{"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(11-20)", "url_path": url_path} )

@login_required
def view_clearance(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Clearance Distances")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Clearance Distances Files", "url_path": url_path} )

@login_required
def view_mines(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Mines Department Regulations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Mines Department Regulations Files", "url_path": url_path} )

@login_required
def view_supplies(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Interruption of supply Notice to consumers")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index ISNC Files", "url_path": url_path} )

@login_required
def view_samples(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Water Samples and Painting to Consumers")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index WSPC Files", "url_path": url_path} )

@login_required
def view_cables(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Cables")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Cables Files", "url_path": url_path} )

@login_required
def view_capital(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Capital Works and Expenditure")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Capital Works and Expenditure Files", "url_path": url_path} )

@login_required
def view_government(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Government planning and Wayleaves")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index GPW Files", "url_path": url_path} )

@login_required
def view_phases(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Phase Rotation and Colouring")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Phase Rotation and Colouring Files", "url_path": url_path} )

@login_required
def view_insulators(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Insulators and Bushings")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Insulators and Bushings Files", "url_path": url_path} )

@login_required
def view_locks(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Locks and Keys")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Locks and Keys Files", "url_path": url_path} )



@login_required
def view_21_30(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_21_30.html', {"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(21-30)"})

@login_required
def view_rmasts(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="RMasts, Poles, Stays and Crossarms")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index RMasts, Poles, Stays and Crossarms Files", "url_path": url_path} )

@login_required
def view_substations(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Substations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Substations Files" } )

@login_required
def view_fire(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Fire Fighting")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Fire Fighting Files", "url_path": url_path} )

@login_required
def view_defective(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Defective and Damaged Equipment Insurance & Guarantees")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Defective and Damaged Equipment Insurance & Guarantees Files", "url_path": url_path} )

@login_required
def view_services(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Services and Service Equipment")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Services and Service Equipment Files", "url_path": url_path} )

@login_required
def view_consumers(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Consumer's Equipment and installation")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Consumer's Equipment and installation Files"} )

@login_required
def view_lifting(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Lifting Equipment")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Lifting Equipment Files"} )

@login_required
def view_transport(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Transport")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Transport Files"} )

@login_required
def view_lpa(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Lighting Protection and Arrestors")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Lighting Protection and Arrestors Files"} )

@login_required
def view_insulation(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Insulation")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Insulation Files"} )


@login_required
def view_31_45(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_31_45.html', {"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(31-45)", "url_path": url_path})

@login_required
def view_cables(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Cable Jointing Laying ")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Cable Jointing Laying Files"} )

@login_required
def view_capacitors(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Capacitors and Power Factor Correction")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Capacitors and Power Factor Correction Files"} )

@login_required
def view_explosive(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Explosive and Magazine")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Explosive and Magazine Files"} )

@login_required
def view_standard(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Standard Stock Items")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Standard Stock Items Files"} )

@login_required
def view_cradles(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Cradles and Guards")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Cradles and Guards Files"} )

@login_required
def view_11kv(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Standard 11Kv Line Construction")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Standard 11kv Line Construction Files"} )

@login_required
def view_conductors(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Conductors, Earthwires and Accessories")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Conductors, Earthwires and Accessories Files"} )

@login_required
def view_roads(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Road, Rail, and Line Crossings")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Road, Rail, and Line Crossings Files"} )

@login_required
def view_zetdc(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Z.E.T.D.C Regulations and Safety Precautions")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Z.E.T.D.C Regulations and sfaety Precautions Files"} )

@login_required
def view_power(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Power Stations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Power Stations Files"} )

@login_required
def view_substation(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Substation Batteries")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Substation Batteries Files"} )

@login_required
def view_safety(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Safety Rules for Operation and Maintenance Switching Authorization")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Safety Rule For Operation and Maintenance Switching Authorization Files"} )

@login_required
def view_lighting(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="High Mast Lighting")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index High Mast Lighting Files"} )

@login_required
def view_capacity(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Planning Policy on Firm Capacity")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Planning Policy on Firm Capacity Files"} )

@login_required
def view_procurement(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Procurement")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Procurement Files"} )


@login_required
def view_user_manuals(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_user_manuals.html', {"page_title": "USER MANUALS", "url_path": url_path})

@login_required
def view_commercial_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="USER MANUALS", sub_category_1="Commercial")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "User Manuals Commercial Files", "url_path": url_path} )

@login_required
def view_hr_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="USER MANUALS", sub_category_1="hr")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Human Resources Files", "url_path": url_path} )

@login_required
def view_finance_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="USER MANUALS", sub_category_1="Finance")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Finance Files", "url_path": url_path} )

@login_required
def view_ict_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="USER MANUALS", sub_category_1="ICT")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals ICT Files", "url_path": url_path} )

@login_required
def view_relations_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="USER MANUALS", sub_category_1="Stakeholder Relations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Stakeholder Relations Files", "url_path": url_path} )

@login_required
def view_legal_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="USER MANUALS", sub_category_1="Legal")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Legal Files", "url_path": url_path} )

@login_required
def view_procurement_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="USER MANUALS", sub_category_1="Procurement")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Procument Files", "url_path": url_path} )

@login_required
def view_risk_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type ="USER MANUALS", sub_category_1="Risk")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Risk Files", "url_path": url_path} )



@login_required
def view_eng_manuals(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type='USER MANUALS', sub_category_1="Engineering").all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_eng_manuals.html', {"page_title": "USER MANUALS (Engineering)", "url_path": url_path, "files": files})

@login_required
def view_switchgear(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Switchgear")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Switchgear Files", "url_path": url_path} )

@login_required
def view_dtech(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="Drone Technology")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files,  "page_title": "User Manuals Drone Technology Files", "url_path": url_path} )

@login_required
def view_ndm(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="NDM")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals NDM Files", "url_path": url_path} )

@login_required
def view_gis(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="GIS")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals GIS Files", "url_path": url_path} )

@login_required
def view_itrack(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="iTrack Zimbabwe Geotrack Connect Manual")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals iTrack Zimbabwe Geotrack Connect Manual Files", "url_path": url_path} )

@login_required
def view_sap(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="SAP")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,"page_title": "User Manuals SAP Files" , "url_path": url_path} )

@login_required
def view_oms(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, sub_category_2="OMS")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "User Manuals OMS Files", "url_path": url_path} )


# @login_required
# def view_drawings(request):
    
#     files = KnowledgeCenter.objects.all()
    
#     return render(request, 'knowledge-center/view_drawings.html', {"page_title": "STANDARDS, SPECIFICATIONS AND DRAWINGS"} )

@login_required
def view_drawing(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="Drawings")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Drawings Files", "url_path": url_path} )

@login_required
def view_standards(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="Standards")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Standards Files", "url_path": url_path} )

# @login_required
# def view_specifications(request):
    
#     files = KnowledgeCenter.objects.filter(archived=False, file_type="Specifications")

#     print("files: ", files)
#     new_dict = get_kc_dict(files)
#     print("new_dict: ", new_dict)
    
#     url_path = request.path.split("/")    
# return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Specifications Files", "url_path": url_path} )

@login_required
def view_publications(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PUBLICATIONS")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Publications Files", "url_path": url_path} )

@login_required
def view_external_docs(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="Other External Documents")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "External Documents Files", "url_path": url_path} )

@login_required
def view_drone_tech(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="Drone Technology")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Drone Technology Files", "url_path": url_path} )




@login_required
def view_knowledge_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_knowledge_base.html',{"page_title": "PRINCE2 CENTRE OF EXCELENCE", "url_path": url_path} )


@login_required
def view_com_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_com_base.html', )


@login_required
def view_eng_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_eng_base.html', )


@login_required
def view_ict_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_ict_base.html', )


@login_required
def test(request):
    
    files = KnowledgeCenter.objects.all()
    
    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_legislation.html',{"context": new_dict, "url_path": url_path} )

@login_required
def view_risk_management(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PRINCE2 CENTRE OF EXCELLENCE", sub_category_1="Risk Management Strategy")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Risk Management Strategy Files", "url_path": url_path} )

@login_required
def view_communication_management(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PRINCE2 CENTRE OF EXCELLENCE", sub_category_1="Communication Management Strategy")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Communications Management Strategy Files", "url_path": url_path} )

@login_required
def view_quality_management(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PRINCE2 CENTRE OF EXCELLENCE", sub_category_1="Quality Management Strategy")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Quality Management Strategy Files", "url_path": url_path} )

@login_required
def view_configuration_management(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PRINCE2 CENTRE OF EXCELLENCE", sub_category_1="Configuration Management Strategy")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Configuration Management Strategy Files", "url_path": url_path} )

@login_required
def view_risk_register(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PRINCE2 CENTRE OF EXCELLENCE", sub_category_1="Risk Register Template")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Risk Register Template Files", "url_path": url_path} )

@login_required
def view_lessons_learnt(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PRINCE2 CENTRE OF EXCELLENCE", sub_category_1="Lessons Learnt From Previous Projects")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Lessons Learnt From Previous Projects Files", "url_path": url_path} )

@login_required
def view_quality_register(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PRINCE2 CENTRE OF EXCELLENCE", sub_category_1="Quality Register Template")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Quality Register Template Files", "url_path": url_path} )

@login_required
def view_configuration_item(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PRINCE2 CENTRE OF EXCELLENCE", sub_category_1="Configuration Item Record Template")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Configuration Item Record Template Files", "url_path": url_path} )

@login_required
def view_current_projects(request):
    
    files = KnowledgeCenter.objects.filter(archived=False, file_type="PRINCE2 CENTRE OF EXCELLENCE", sub_category_1="Current Projects")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Current Projects Files", "url_path": url_path} )

@login_required
def file_search(request):
    keyword = request.GET.get('filename', '')
    pattern = r"\b" + str(keyword).lower() + r"\b"
    match = re.search(pattern, keyword)
    print(keyword, pattern, match)
    if match:
       keyword=match.group()
    results = []
    if keyword:
        all_files= KnowledgeCenter.objects.filter(filename__contains=keyword).all()
        print(all_files)
        for file in all_files:
            file_path = file.filepath
            # filename = os.path.basename(file_path)
            results.append({
                "name": file.filename,
                "id": file.id
            })
            # print(re.search(pattern, str(file_path).lower()))
            # if re.search(pattern, str(file_path).lower()):
            #     filename = os.path.basename(file_path)
            #     results.append({
            #         "name": filename,
            #         "path": file_path
            #     })
        print(results)

    else:
        print("Keyword not found")

    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_firstview.html', {"page_title": "KNOWLEDGE CENTRE", "results": results})

def save_file(f,file_path):
    if f:
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
                return True
            else:
                return False