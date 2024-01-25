import re
from django.shortcuts import render, redirect
from django.http import FileResponse, JsonResponse
from datetime import datetime
import json, os
from django.conf import settings
from .models import Categories, First_Category, Secondary_Category, Filetype
from django.shortcuts import render
from django.db.models import Q


from utils.helper_functions import get_kc_dict

from .models import KnowledgeCenter

# Create your views here.
def create(request):
    
    if request.method == 'POST':
        # something
        print("post data: ", request.POST)
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
            created_by = "Max",
        )
        um.save()
        return render(request, 'knowledge-center/create.html', {})    
    
    return render(request, 'knowledge-center/create.html', {})

def view_files(request):
    
    files = KnowledgeCenter.objects.all()
    
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
            "created_by": file.created_by,
            "created_at": file.created_at,
        }
        files_list.append(new_file)
    
    context = json.dumps(files_list, default=str)
    
    return render(request, 'knowledge-center/view_files.html', {"context": context})


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
    
    return render(request, 'knowledge-center/view_myfiles.html', {"context": new_dict})


def get_category(request, file_type, cat_1, cat_2):
    file_ = KnowledgeCenter.objects.filter(file_type=file_type).all()
    file_ = KnowledgeCenter.objects.filter(file_type=file_type, cat_1=cat_1).all()
    file_ = KnowledgeCenter.objects.filter(file_type=file_type, cat_1=cat_1, cat_2=cat_2).all()


def view_myfiles(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_myfiles.html', )


def download_file(request):

    file_id = request.GET['file_id']
    file_record = KnowledgeCenter.objects.filter(id=file_id).first()
    file_path = file_record.filepath

    # search for file in system
    try:
        base_directory_path = os.path.join(settings.BASE_DIR, file_path)

        return FileResponse(open(base_directory_path, 'rb'), content_type='application/pdf')
    except Exception as ex:
        print(ex)

    return redirect('/knowledge-center/view_files')


def edit_file(request, file_id):

    if request.method == 'GET':
        print("file_id: ", file_id)
        file_record = KnowledgeCenter.objects.filter(id=file_id).first()
        # fetch section code

        return render(request, 'knowledge-center/edit_file.html', {"record": file_record})    
    
    return render(request, 'knowledge-center/edit_file.html', {})


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
    
    files = KnowledgeCenter.objects.all()

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/view_legislation.html', {"page_title": "LEGISLATION"} )


def view_ea(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Electricity Acts")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Electricity Acts files"})


def view_gl(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="General Legislation")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "General Legislation files"} )

def view_si(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Statutory Instruments")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Statutory Instruments files"} )


def view_firstview(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_firstview.html', {"page_title": "KNOWLEDGE CENTRE", "results": []})


def view_specifications(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_specifications.html', {"page_title": "SPECIFICATIONS", "results": []})

def view_commercial_spec(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Commercial")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Commercial Files"} )

def view_hr_spec(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Human Resources")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Human Resources Files"} )

def view_engineering_spec(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Engineering")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Engineering Files"} )

def view_finance_spec(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Finance")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Finance Files"} )

def view_ict_spec(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="ICT")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications ICT Files"} )

def view_risk_spec(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Risk")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Risk Files"} )

def view_relations_spec(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Stakeholder Relations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Stakeholder Relations Files"} )

def view_legal_spec(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Legal")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Legal Files"} )

def view_procurement_spec(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Procurement")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "Specifications Procurement Files"} )

def view_policies(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_policies.html',{"page_title": "POLICIES AND GUIDLINES"} )

def view_commercial_policies(request):
    
    files = KnowledgeCenter.objects.filter(file_type="POLICIES & GUIDELINES", sub_category_1="Commercial").all()

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies and Guidlines Commercial files"} )

def view_hr_policies(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Human Resources")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies Human Resources files"} )

def view_engineering(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Engineering")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies and Guidelines Engineering Files"} )

def view_finance_policies(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Finance")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html', {"files": files, "page_title": "Policies and Guidelines Finance Files"} )

def view_ict_policies(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="ICT")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html', {"files": files, "page_title": "Policies and Guidelines ICT Files"} )

def view_risk_policies(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Risk")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Policies and Guidelines Risk Files"} )

def view_index(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_index.html',{"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX"} )

def view_reports(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Reports")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Reports Files"} )

def view_protection(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Protection")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Protection Files"} )

def view_earthing(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Earthing")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Earthing Files"} )

def view_transformers(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Transformers")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Transformers Files"} )

def view_fuses(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Fuses")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Fuses Files"} )

def view_imm(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Instruments, Meters and Metering")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Instruments Meters and Metering Files"} )

def view_tg(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Transformer Gaskets")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Transformer Gaskets Files"} )

def view_switchgear(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Switchgear")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Switchgear Files"} )

def view_por(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Post Office Regulations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Post Office Regulations Files"} )

def view_io(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="io")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Insulating oils Files"} )
def view_1_10(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_1_10.html',{"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(1-10)"} )


def view_11_20(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_11_20.html',{"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(11-20)"} )

def view_clearance(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Clearance Distances")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Clearance Distances Files"} )

def view_mines(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Mines Department Regulations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Mines Department Regulations Files"} )

def view_supplies(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Interruption of supply Notice to consumers")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index ISNC Files"} )

def view_samples(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Water Samples and Painting to Consumers")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index WSPC Files"} )

def view_cables(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Cables")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Cables Files"} )

def view_capital(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Capital Works and Expenditure")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Capital Works and Expenditure Files"} )

def view_government(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Government planning and Wayleaves")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index GPW Files"} )

def view_phases(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Phase Rotation and Colouring")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Phase Rotation and Colouring Files"} )

def view_insulators(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Insulators and Bushings")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Insulators and Bushings Files"} )

def view_locks(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Locks and Keys")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index Locks and Keys Files"} )



def view_21_30(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_21_30.html', {"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(21-30)"})

def view_rmasts(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="RMasts, Poles, Stays and Crossarms")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Engineering Instructions Main Index RMasts, Poles, Stays and Crossarms Files"} )

def view_substations(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Substations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_fire(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Fire Fighting")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_defective(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Defective and Damaged Equipment Insurance & Guarantees")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_services(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Services and Service Equipment")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_consumers(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Consumer's Equipment and installation")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_lifting(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Lifting Equipment")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_transport(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Transport")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_lpa(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Lighting Protection and Arrestors")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_insulation(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Insulation")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )


def view_31_45(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_31_45.html', {"page_title": "ENGINEERING INSTRUCTIONS MAIN INDEX(31-45)"})

def view_cables(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Cable Jointing Laying ")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_capacitors(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Capacitors and Power Factor Correction")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_explosive(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Explosive and Magazine")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_standard(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Standard Stock Items")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_cradles(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Cradles and Guards")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_11kv(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Standard 11Kv Line Construction")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_conductors(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Conductors, Earthwires and Accessories")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_roads(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Road, Rail, and Line Crossings")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_zetdc(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Z.E.T.D.C Regulations and Safety Precautions")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_power(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Power Stations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_substation(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Substation Batteries")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_safety(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Safety Rules for Operation and Maintenance Switching Authorization")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_lighting(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="High Mast Lighting")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_capacity(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Planning Policy on Firm Capacity")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )

def view_procurement(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Procurement")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"context": new_dict, "files": files} )


def view_user_manuals(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_user_manuals.html', {"page_title": "USER MANUALS"})

def view_commercial_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Commercial")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "User Manuals Commercial Files"} )

def view_hr_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="hr")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Human Resources Files"} )

def view_finance_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Finance")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Finance Files"} )

def view_ict_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="ICT")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals ICT Files"} )

def view_relations_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Stakeholder Relations")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Stakeholder Relations Files"} )

def view_legal_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Legal")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Legal Files"} )

def view_procurement_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Procurement")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Procument Files"} )

def view_risk_usermanuals(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_1="Risk")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Risk Files"} )



def view_eng_manuals(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_eng_manuals.html', {"page_title": "USER MANUALS (Engineering)"})

def view_switchgear(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Switchgear")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals Switchgear Files"} )

def view_dtech(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Drone Technology")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{ "files": files,  "page_title": "User Manuals Drone Technology Files"} )

def view_ndm(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="NDM")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals NDM Files"} )

def view_gis(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="GIS")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals GIS Files"} )

def view_itrack(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="iTrack Zimbabwe Geotrack Connect Manual")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,  "page_title": "User Manuals iTrack Zimbabwe Geotrack Connect Manual Files"} )

def view_sap(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="SAP")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files,"page_title": "User Manuals SAP Files" } )

def view_oms(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="OMS")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "User Manuals OMS Files"} )


def view_drawings(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_drawings.html', {"page_title": "STANDARDS, SPECIFICATIONS AND DRAWINGS"} )

def view_drawing(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Drawings")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Drawings Files"} )

def view_standards(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Standards")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Standards Files"} )

# def view_specifications(request):
    
#     files = KnowledgeCenter.objects.filter(sub_category_2="Specifications")

#     print("files: ", files)
#     new_dict = get_kc_dict(files)
#     print("new_dict: ", new_dict)
    
#     return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Specifications Files"} )

def view_publications(request):
    
    files = KnowledgeCenter.objects.filter(file_type="PUBLICATIONS")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Publications Files"} )

def view_external_docs(request):
    
    files = KnowledgeCenter.objects.filter(file_type="Other External Documents")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "External Documents Files"} )

def view_drone_tech(request):
    
    files = KnowledgeCenter.objects.filter(file_type="Drone Technology")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Drone Technology Files"} )




def view_knowledge_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_knowledge_base.html',{"page_title": "PRINCE2 CENTRE OF EXCELENCE"} )


def view_com_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_com_base.html', )


def view_eng_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_eng_base.html', )


def view_ict_base(request):
    
    files = KnowledgeCenter.objects.all()
    
    return render(request, 'knowledge-center/view_ict_base.html', )


def test(request):
    
    files = KnowledgeCenter.objects.all()
    
    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/view_legislation.html',{"context": new_dict} )

def view_risk_management(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Risk Management Strategy")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Risk Management Strategy Files"} )

def view_communication_management(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Communication Management Strategy")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Communications Management Strategy Files"} )

def view_quality_management(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Quality Management Strategy")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Quality Management Strategy Files"} )

def view_configuration_management(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Configuration Management Strategy")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Configuration Management Strategy Files"} )

def view_risk_register(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Risk Register Template")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Risk Register Template Files"} )

def view_lessons_learnt(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Lessons Learnt From Previous Projects")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Lessons Learnt From Previous Projects Files"} )

def view_quality_register(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Quality Register Template")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Quality Register Template Files"} )

def view_configuration_item(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Configuration Item Record Template")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Configuration Item Record Template Files"} )

def view_current_projects(request):
    
    files = KnowledgeCenter.objects.filter(sub_category_2="Current Projects")

    print("files: ", files)
    new_dict = get_kc_dict(files)
    print("new_dict: ", new_dict)
    
    return render(request, 'knowledge-center/test.html',{"files": files, "page_title": "Current Projects Files"} )

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

    return render(request, 'knowledge-center/view_firstview.html', {"page_title": "KNOWLEDGE CENTRE", "results": results})


def save_file(f,file_path):
    if f:
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
                return True
            else:
                return False