import re
from django.shortcuts import render, redirect
from django.http import FileResponse, JsonResponse
from datetime import datetime
import json, os
from django.conf import settings

from utils.save_file import save_file
from .models import Categories, First_Category, Secondary_Category, Filetype
from django.shortcuts import render
from django.db.models import Q

from utils.helper_functions import get_kc_dict

from .models import KnowledgeCenter

# Create your views here.
def create(request):
    url_path = request.path.split("/")
    if request.method == 'POST':
        # something
        print("post data: ", request.POST)
        user = request.user
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
        
        file_path = ''
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES ['uploaded_file']
                file_path = 'uploads/knowledge_center/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + uploaded_file.name 
                save_file(uploaded_file,file_path)
        except Exception as ex:
            print("Error:",ex)


        file_type= Filetype.objects.filter(id=filetype).first() if filetype else None
        subtype1_ = First_Category.objects.filter(id=subtype1).first() if subtype1 else None
        subtype2_ = Secondary_Category.objects.filter(id=subtype2).first() if subtype2 else None
        um = KnowledgeCenter(
            filename= filename,
            file_type= file_type.name if file_type else "",
            filepath = file_path,
            section= section,
            sub_category_1 = subtype1_.name if subtype1_ else "",
            sub_category_2 = subtype2_.name if subtype2_ else "",
            region=region,
            created_at = datetime.now().date(),
            updated_at = datetime.now().date(),
            created_by = user.username,
        )
        um.save()
        
        return render(request, 'knowledge-center/create.html', {
                      "url_path": url_path
                      })    
    
    return render(request, 'knowledge-center/create.html', {"url_path": url_path})

def archive_file(request, file_id):

    um = KnowledgeCenter.objects.filter(id=file_id).first()
    um.archived=True
    um.save()
    
    return redirect('/knowledge_center/view_files')

def unarchive_file(request, file_id):

    um = KnowledgeCenter.objects.filter(id=file_id).first()
    um.archived=False
    um.save()
    
    return redirect('/knowledge_center/view_files')

def view_files(request):
    
    files = KnowledgeCenter.objects.filter(archived=False).all()
    
    files_list = []
    for file in files:
        new_file = {
            "id": file.id,
            "filename": file.filename,
            "filetype": file.file_type,
            "section": file.section,
            "subcategory1": file.sub_category_1,
            "subcategory2": file.sub_category_2,
            "region": file.region,
            "archived": file.archived,
            "created_by": file.created_by,
            "created_at": file.created_at,
        }
        files_list.append(new_file)
    
    context = json.dumps(files_list, default=str)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_files.html', {"context": context, "url_path": url_path, "page": "kc_all"})

def view_archived_files(request):
    
    files = KnowledgeCenter.objects.filter(archived=True).all()
    
    files_list = []
    for file in files:
        new_file = {
            "id": file.id,
            "filename": file.filename,
            "filetype": file.file_type,
            "section": file.section,
            "subcategory1": file.sub_category_1,
            "subcategory2": file.sub_category_2,
            "region": file.region,
            "archived": file.archived,
            "created_by": file.created_by,
            "created_at": file.created_at,
        }
        files_list.append(new_file)
    
    context = json.dumps(files_list, default=str)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_files.html', {"context": context, "url_path": url_path, "page": "kc_archived"})

def view_by_category(request):
    
    files = KnowledgeCenter.objects.all()
    
    
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

def get_category(request, file_type, cat_1, cat_2):
    file_ = KnowledgeCenter.objects.filter(file_type=file_type).all()
    file_ = KnowledgeCenter.objects.filter(file_type=file_type, cat_1=cat_1).all()
    file_ = KnowledgeCenter.objects.filter(file_type=file_type, cat_1=cat_1, cat_2=cat_2).all()

def view_myfiles(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_myfiles.html', {"url_path": url_path})

def download_file(request):

    file_id = request.GET['file_id']
    file_record = KnowledgeCenter.objects.filter(id=file_id).first()
    file_path = file_record.filepath

    # search for file in system
    try:
        base_directory_path = os.path.join(settings.BASE_DIR, file_path)
        import mimetypes
        # content_type, _ = mimetypes.guess_type(base_directory_path)
        # print("base_directory_path: ", base_directory_path)
        return FileResponse(open(base_directory_path, 'rb'), content_type='application/pdf')
    except Exception as ex:
        print(ex)

    return redirect('/knowledge_center/view_files')

def edit_file(request, file_id):
    url_path = request.path.split("/")
    if request.method == 'GET':
        print("file_id: ", file_id)
        file_record = KnowledgeCenter.objects.filter(id=file_id).first()
        # fetch section code

        url_path = request.path.split("/")
        return render(request, 'knowledge-center/edit_file.html', {"record": file_record, "url_path": url_path})    
    
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
        
        file_path = ''
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES ['uploaded_file']
                file_path = 'uploads/knowledge_center/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + uploaded_file.name 
                save_file(uploaded_file,file_path)
        except Exception as ex:
            print("Error:",ex)


        file_type= Filetype.objects.filter(id=filetype).first() if filetype else None
        subtype1_ = First_Category.objects.filter(id=subtype1).first() if subtype1 else None
        subtype2_ = Secondary_Category.objects.filter(id=subtype2).first() if subtype2 else None

        um = KnowledgeCenter.objects.filter(id=id).first()
        um.filename= filename
        um.file_type= file_type.name if file_type else ""
        um.filepath = file_path
        um.section= section
        um.sub_category_1 = subtype1_.name if subtype1_ else ""
        um.sub_category_2 = subtype2_.name if subtype2_ else ""
        um.region=region
        um.updated_at = datetime.now().date()
        um.created_by = user.username

        um.save()
        
        return render(request, 'knowledge-center/create.html', {
                      "url_path": url_path
                      })    
    
    return render(request, 'knowledge-center/edit_file.html', {"url_path": url_path})


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
    

def view_legislation(request):
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_legislation.html', {"page_title": "LEGISLATION", "url_path": url_path} )

def view_legal_registers(request):
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/legal_registers.html', {"page_title": "Legal Registers", "url_path": url_path} )

def legal_registers_departments(request, department):
    
    files = KnowledgeCenter.objects.filter(file_type="LEGISLATION", sub_category_1="Legal Registers", sub_category_2=department).all()
    
    url_path = request.path.split("/")
    title = department + " Legal Registers"
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": title, "url_path": url_path})

def fetch_knowledge_center(request, filetype, subtype, subsubtype):
    
    files = []
    # if filetype and subtype and subsubtype:
    files = KnowledgeCenter.objects.filter(file_type=filetype, sub_category_1=subtype, sub_category_2=subsubtype).all()
    url_path = request.path.split("/")
    title = (subsubtype + " " + subtype).capitalize()
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": title, "url_path": url_path})

def view_ea(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Electricity Acts")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Acts of Parliament", "url_path": url_path})


def view_gl(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="General Legislation")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "General Legislation files", "url_path": url_path} )

def view_si(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Statutory Instruments")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Statutory Instruments files", "url_path": url_path} )


def view_firstview(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    
    return render(request, 'knowledge-center/view_firstview.html', {
        "url_path": url_path,
        "page_title": "KNOWLEDGE CENTRE", 
        "results": []})


def view_specifications(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_specifications.html', {"page_title": "SPECIFICATIONS", "results": [], "url_path": url_path})

def view_commercial_spec(request):
    
    files = KnowledgeCenter.objects.filter(file_type="SPECIFICATIONS", sub_category_1="Commercial")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Commercial Files", "url_path": url_path} )

def view_hr_spec(request):
    
    files = KnowledgeCenter.objects.filter(file_type="SPECIFICATIONS", sub_category_1="Human Resources")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Human Resources Files", "url_path": url_path} )

def view_engineering_spec(request):
    
    files = KnowledgeCenter.objects.filter(file_type="SPECIFICATIONS", sub_category_1="Engineering")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{
        "files": files,  "page_title": "Specifications Engineering Files", "url_path": url_path} )

def view_finance_spec(request):
    
    files = KnowledgeCenter.objects.filter(file_type="SPECIFICATIONS", sub_category_1="Finance")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{
        "files": files,  "page_title": "Specifications Finance Files", "url_path": url_path} )

def view_ict_spec(request):
    
    files = KnowledgeCenter.objects.filter(file_type="SPECIFICATIONS", sub_category_1="ICT")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{
        "files": files,  "page_title": "Specifications ICT Files", "url_path": url_path} )

def view_risk_spec(request):
    
    files = KnowledgeCenter.objects.filter(file_type="SPECIFICATIONS", sub_category_1="Risk")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Risk Files", "url_path": url_path} )

def view_relations_spec(request):
    
    files = KnowledgeCenter.objects.filter(file_type="SPECIFICATIONS", sub_category_1="Stakeholder Relations")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Stakeholder Relations Files", "url_path": url_path} )

def view_legal_spec(request):
    
    files = KnowledgeCenter.objects.filter(file_type="SPECIFICATIONS", sub_category_1="Legal")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Legal Files", "url_path": url_path} )

def view_procurement_spec(request):
    
    files = KnowledgeCenter.objects.filter(file_type="SPECIFICATIONS", sub_category_1="Procurement")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Procurement Files", "url_path": url_path} )

def view_policies(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_policies.html',{"page_title": "POLICIES AND GUIDLINES", "url_path": url_path} )

def view_commercial_policies(request):
    
    files = KnowledgeCenter.objects.filter(file_type="POLICIES & GUIDELINES", sub_category_1="Commercial").all()

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies and Guidlines Commercial files", "url_path": url_path} )

def view_hr_policies(request):
    
    files = KnowledgeCenter.objects.filter(file_type="POLICIES & GUIDELINES", sub_category_1="Human Resources")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies Human Resources files", "url_path": url_path} )

def view_engineering(request):
    
    files = KnowledgeCenter.objects.filter(file_type="POLICIES & GUIDELINES", sub_category_1="Engineering")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies and Guidelines Engineering Files", "url_path": url_path} )

def view_finance_policies(request):
    
    files = KnowledgeCenter.objects.filter(file_type="POLICIES & GUIDELINES", sub_category_1="Finance")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html', {"files": files, "page_title": "Policies and Guidelines Finance Files", "url_path": url_path} )

def view_ict_policies(request):
    
    files = KnowledgeCenter.objects.filter(file_type="POLICIES & GUIDELINES", sub_category_1="ICT")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html', {"files": files, "page_title": "Policies and Guidelines ICT Files", "url_path": url_path} )

def view_risk_policies(request):
    
    files = KnowledgeCenter.objects.filter(file_type="POLICIES & GUIDELINES", sub_category_1="Risk")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies and Guidelines Risk Files", "url_path": url_path} )

def view_index(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_index.html',{"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX", "url_path": url_path} )

def view_reports(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Reports")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Reports Files", "url_path": url_path} )

def view_protection(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Protection")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Protection Files", "url_path": url_path} )

def view_earthing(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Earthing")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Earthing Files", "url_path": url_path} )

def view_transformers(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Transformers")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Transformers Files", "url_path": url_path} )

def view_fuses(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Fuses")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Fuses Files", "url_path": url_path} )

def view_imm(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Instruments, Meters and Metering")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Instruments Meters and Metering Files", "url_path": url_path} )

def view_tg(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Transformer Gaskets")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Transformer Gaskets Files", "url_path": url_path} )

def view_switchgear(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Switchgear")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Switchgear Files", "url_path": url_path} )

def view_por(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Post Office Regulations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Post Office Regulations Files", "url_path": url_path} )

def view_io(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="io")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Insulating oils Files", "url_path": url_path} )
def view_1_10(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_1_10.html',{"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(1-10)", "url_path": url_path} )


def view_11_20(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_11_20.html',{"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(11-20)", "url_path": url_path} )

def view_clearance(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Clearance Distances")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Clearance Distances Files", "url_path": url_path} )

def view_mines(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Mines Department Regulations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Mines Department Regulations Files", "url_path": url_path} )

def view_supplies(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Interruption of supply Notice to consumers")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index ISNC Files", "url_path": url_path} )

def view_samples(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Water Samples and Painting to Consumers")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index WSPC Files", "url_path": url_path} )

def view_cables(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Cables")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Cables Files", "url_path": url_path} )

def view_capital(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Capital Works and Expenditure")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Capital Works and Expenditure Files", "url_path": url_path} )

def view_government(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Government planning and Wayleaves")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index GPW Files", "url_path": url_path} )

def view_phases(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Phase Rotation and Colouring")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Phase Rotation and Colouring Files", "url_path": url_path} )

def view_insulators(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Insulators and Bushings")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Insulators and Bushings Files", "url_path": url_path} )

def view_locks(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Locks and Keys")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Locks and Keys Files", "url_path": url_path} )



def view_21_30(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_21_30.html', {"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(21-30)"})

def view_rmasts(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="RMasts, Poles, Stays and Crossarms")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index RMasts, Poles, Stays and Crossarms Files", "url_path": url_path} )

def view_substations(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Substations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Substations Files" } )

def view_fire(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Fire Fighting")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Fire Fighting Files", "url_path": url_path} )

def view_defective(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Defective and Damaged Equipment Insurance & Guarantees")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Defective and Damaged Equipment Insurance & Guarantees Files", "url_path": url_path} )

def view_services(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Services and Service Equipment")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Services and Service Equipment Files", "url_path": url_path} )

def view_consumers(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Consumer's Equipment and installation")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Consumer's Equipment and installation Files"} )

def view_lifting(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Lifting Equipment")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Lifting Equipment Files"} )

def view_transport(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Transport")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Transport Files"} )

def view_lpa(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Lighting Protection and Arrestors")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Lighting Protection and Arrestors Files"} )

def view_insulation(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Insulation")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Insulation Files"} )


def view_31_45(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_31_45.html', {"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(31-45)", "url_path": url_path})

def view_cables(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Cable Jointing Laying ")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Cable Jointing Laying Files"} )

def view_capacitors(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Capacitors and Power Factor Correction")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Capacitors and Power Factor Correction Files"} )

def view_explosive(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Explosive and Magazine")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Explosive and Magazine Files"} )

def view_standard(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Standard Stock Items")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Standard Stock Items Files"} )

def view_cradles(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Cradles and Guards")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Cradles and Guards Files"} )

def view_11kv(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Standard 11Kv Line Construction")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Standard 11kv Line Construction Files"} )

def view_conductors(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Conductors, Earthwires and Accessories")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Conductors, Earthwires and Accessories Files"} )

def view_roads(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Road, Rail, and Line Crossings")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Road, Rail, and Line Crossings Files"} )

def view_zetdc(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Z.E.T.D.C Regulations and Safety Precautions")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Z.E.T.D.C Regulations and sfaety Precautions Files"} )

def view_power(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Power Stations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Power Stations Files"} )

def view_substation(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Substation Batteries")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Substation Batteries Files"} )

def view_safety(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Safety Rules for Operation and Maintenance Switching Authorization")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Safety Rule For Operation and Maintenance Switching Authorization Files"} )

def view_lighting(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="High Mast Lighting")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index High Mast Lighting Files"} )

def view_capacity(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Planning Policy on Firm Capacity")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Planning Policy on Firm Capacity Files"} )

def view_procurement(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Procurement")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "url_path": url_path, "page_title": "Engineering Instructions Main Index Procurement Files"} )


def view_user_manuals(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_user_manuals.html', {"page_title": "USER MANUALS", "url_path": url_path})

def view_commercial_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(file_type="USER MANUALS", sub_category_1="Commercial")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "User Manuals Commercial Files", "url_path": url_path} )

def view_hr_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(file_type="USER MANUALS", sub_category_1="hr")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Human Resources Files", "url_path": url_path} )

def view_finance_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(file_type="USER MANUALS", sub_category_1="Finance")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Finance Files", "url_path": url_path} )

def view_ict_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(file_type="USER MANUALS", sub_category_1="ICT")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals ICT Files", "url_path": url_path} )

def view_relations_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(file_type="USER MANUALS", sub_category_1="Stakeholder Relations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Stakeholder Relations Files", "url_path": url_path} )

def view_legal_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(file_type="USER MANUALS", sub_category_1="Legal")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Legal Files", "url_path": url_path} )

def view_procurement_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(file_type="USER MANUALS", sub_category_1="Procurement")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Procument Files", "url_path": url_path} )

def view_risk_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(file_type ="USER MANUALS", sub_category_1="Risk")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Risk Files", "url_path": url_path} )



def view_eng_manuals(request):
    
    files = KnowledgeCenter.objects.filter(file_type='USER MANUALS', sub_category_1="Engineering").all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_eng_manuals.html', {"page_title": "USER MANUALS (Engineering)", "url_path": url_path, "files": files})

def view_switchgear(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Switchgear")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Switchgear Files", "url_path": url_path} )

def view_dtech(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Drone Technology")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{ "files": files,  "page_title": "User Manuals Drone Technology Files", "url_path": url_path} )

def view_ndm(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="NDM")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals NDM Files", "url_path": url_path} )

def view_gis(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="GIS")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals GIS Files", "url_path": url_path} )

def view_itrack(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="iTrack Zimbabwe Geotrack Connect Manual")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals iTrack Zimbabwe Geotrack Connect Manual Files", "url_path": url_path} )

def view_sap(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="SAP")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files,"page_title": "User Manuals SAP Files" , "url_path": url_path} )

def view_oms(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="OMS")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "User Manuals OMS Files", "url_path": url_path} )


# def view_drawings(request):
    
#     files = KnowledgeCenter.objects.all()
    
#     return render(request, 'knowledge-center/view_drawings.html', {"page_title": "STANDARDS, SPECIFICATIONS AND DRAWINGS"} )

def view_drawing(request):
    
    files = KnowledgeCenter.objects.filter(file_type="Drawings")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Drawings Files", "url_path": url_path} )

def view_standards(request):
    
    files = KnowledgeCenter.objects.filter(file_type="Standards")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Standards Files", "url_path": url_path} )

# def view_specifications(request):
    
#     files = KnowledgeCenter.objects.filter(file_type="Specifications")

#     print("files: ", files)
#     new_dict = get_kc_dict(files)
#     print("new_dict: ", new_dict)
    
#     url_path = request.path.split("/")    
# return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Specifications Files", "url_path": url_path} )

def view_publications(request):
    
    files = KnowledgeCenter.objects.filter(file_type="PUBLICATIONS")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Publications Files", "url_path": url_path} )

def view_external_docs(request):
    
    files = KnowledgeCenter.objects.filter(file_type="Other External Documents")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "External Documents Files", "url_path": url_path} )

def view_drone_tech(request):
    
    files = KnowledgeCenter.objects.filter(file_type="Drone Technology")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Drone Technology Files", "url_path": url_path} )




def view_knowledge_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_knowledge_base.html',{"page_title": "PRINCE2 CENTRE OF EXCELENCE", "url_path": url_path} )


def view_com_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_com_base.html', )


def view_eng_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_eng_base.html', )


def view_ict_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_ict_base.html', )


def test(request):
    
    files = KnowledgeCenter.objects.all()
    
    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/view_legislation.html',{"context": new_dict, "url_path": url_path} )

def view_risk_management(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Risk Management Strategy")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Risk Management Strategy Files", "url_path": url_path} )

def view_communication_management(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Communication Management Strategy")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Communications Management Strategy Files", "url_path": url_path} )

def view_quality_management(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Quality Management Strategy")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Quality Management Strategy Files", "url_path": url_path} )

def view_configuration_management(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Configuration Management Strategy")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Configuration Management Strategy Files", "url_path": url_path} )

def view_risk_register(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Risk Register Template")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Risk Register Template Files", "url_path": url_path} )

def view_lessons_learnt(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Lessons Learnt From Previous Projects")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Lessons Learnt From Previous Projects Files", "url_path": url_path} )

def view_quality_register(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Quality Register Template")
    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Quality Register Template Files", "url_path": url_path} )

def view_configuration_item(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Configuration Item Record Template")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Configuration Item Record Template Files", "url_path": url_path} )

def view_current_projects(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Current Projects")

    
    url_path = request.path.split("/")
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Current Projects Files", "url_path": url_path} )

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