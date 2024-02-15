from argparse import FileType
import datetime
from django.shortcuts import redirect, render
from django.http import FileResponse
import  os, re
from beii_v1 import settings
from process_risks.views import Sections

#from processes.models import FormsUploads

# from re import pattern

# def view_process(request):
#     return render(request,'processes/view_process.html')

def view_it(request):
    return render(request,'processes/it_process.html', {})

def view_engineeringlist(request):
    return render(request,'processes/engineering.html', {})

#Engineering Process maps
def view_commercial(request):
    return render(request,'processes/commercial.html',{})

def view_client(request):
    return render(request,'processes/client.html',{})

def view_revenue(request):
    return render(request,'processes/revenue.html',{})

def view_payment(request):
    return render(request,'processes/payment.html',{})
#end
def view_finance(request):
    return render(request,'processes/finance_processes.html',{})

def view_procurement(request):
    return render(request,'processes/procurement.html',{})

def view_management(request):
    return render(request,'processes/management.html',{})

def view_HR(request):
    return render(request,'processes/HR_processes.html',{})

def view_risk(request):
    return render(request,'processes/risk_processes.html',{})

#Engineering Process maps
def view_maintenance(request):
    return render(request,'processes/maintenance_processes.html',{})

def view_planning(request):
    return render(request,'processes/planning_processes.html',{})

def view_project(request):
    return render(request,'processes/project_processes.html',{})

#First page after clicking view process maps
def view_img(request):
    return render(request,'processes/display.html',{})

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
def file_search(request):
    keyword = request.GET.get('keyword', '')
    pattern = r"\b" + str(keyword).lower() + r"\b"
    match = re.search(pattern, keyword)
    if match:
       keyword=match.group()
    results = []
    if keyword:

        
        # Specify the directory where you want to search for files
        directory = 'C:\\Users\ze366375\Documents\\beii\\static\\documents'
        print(directory)
        # Walk through the directory and search for files
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if re.search(pattern, str(file_path).lower()):
                    filename = os.path.basename(file_path)
                    results.append({
                        "name": filename,
                        "path": file_path
                    })
        print(results)

    else:
        print("Keyword not found")

    return render(request, 'processes/view_process.html', {'results': results,})
# Create your views here.
#FORMS VIEWS
def new_view(request):
    return render(request, 'processes/forms/new_view.html',{})

def forms_index(request):
    return render(request,'processes/forms/forms_index.html', {})

#save forms
def save_file(f,file_path):
    if f:
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
                return True
            else:
                return False
#FORMS UPLOAD 
def forms_upload(request):
    
    if request.method == 'POST':
        # something
        print("post data: ", request.POST)
        filename = request.POST['filename']
        file_type = request.POST['filetype']
        section = request.POST['section']
        region = request.POST['region']
        
        file_path = ''
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES ['uploaded_file']
                file_path = 'uploads/forms/'+datetime.now().strftime('%Y%m%d%I%M%S%p') + uploaded_file.name 
                save_file(uploaded_file,file_path)
        except Exception as ex:
            print("Error:",ex)


        file_type= Filetype.objects.filter(id=FileType).first() if file_type else None
        um = FormsUploads(
            filename= filename,
            file_type= file_type.name if file_type else "",
            filepath = file_path,
            section= section,
            region=region,
            created_at = datetime.now().date(),
            updated_at = datetime.now().date(),
            
        )
        um.save()
        return render(request,'processes/forms/forms_upload.html', {})   
    
    return render(request,'processes/forms/forms_upload.html', {})




def engineering_forms(request):
    return render(request,'processes/forms/engineering_forms.html', {})
    
def finance_forms(request):
    return render(request,'processes/forms/finance_forms.html', {})

def hr_forms(request):
    return render(request,'processes/forms/hr_forms.html', {})

def commercial_forms(request):
    return render(request,'processes/forms/commercial_forms.html', {})

def it_forms(request):
    return render(request,'processes/forms/it_forms.html', {})

def risk_forms(request):
    return render(request,'processes/forms/risk_forms.html', {})


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

# Search forms
def file_searchx(request):
    keyword = request.GET.get('keyword', '')
    pattern = r"\b" + str(keyword).lower() + r"\b"
    match = re.search(pattern, keyword)
    if match:
       keyword=match.group()
    results = []
    if keyword:

        
# Specify the directory where you want to search for files
        directory = 'C:\\Users\\Admin\\Desktop\\BEII\\beii\\static\\documents'
        print(directory)
        # Walk through the directory and search for files
        for root, dirs, files in os.walk(directory):
            for file in files:
                file_path = os.path.join(root, file)
                if re.search(pattern, str(file_path).lower()):
                    filename = os.path.basename(file_path)
                    results.append({
                        "name": filename,
                        "path": file_path
                    })
        print(results)

    else:
        print("Keyword not found")

    return render(request, 'processes/forms/forms_index.html', {'results': results,})

#PROCEDURES AND WORK INSTRUCTIONS
def viewWorkInstr(request):
        return render(request, 'processes/procedures_workInstr/home.html')
        
def viewEngProcedureHome(request):
        return render(request, 'processes/procedures_workInstr/eng_proceduresHome.html')
    
def viewCommercialProcedureHome(request):
        return render(request, 'processes/procedures_workInstr/com_procedureHome.html')
    
def viewFinanceProcedures(request):
        return render(request, 'processes/procedures_workInstr/finance_procedures.html')

def viewHRProcedures(request):
        return render(request, 'processes/procedures_workInstr/hr_procedure.html')
    
def viewSRProcedures(request):
    return render(request, 'processes/procedures_workInstr/stakeholderRelations.html')
    
def viewLegalProcedures(request):
    return render(request, 'processes/procedures_workInstr/legal_procedures.html')

   
def viewProcurementProcedures(request):
    return render(request, 'processes/procedures_workInstr/procurement_procedures.html')


def viewICTProcedures(request):
    return render(request, 'processes/procedures_workInstr/ict_procedures.html')

def viewICT_WorkInstr(request):
    return render(request, 'processes/procedures_workInstr/ict_workInstr.html')


def viewEng_PlanningProcedure(request):
    return render(request, 'processes/procedures_workInstr/engPlanning.html')

def viewEng_MaintananceProcedure(request):
    return render(request, 'processes/procedures_workInstr/engMaintanance.html')

def viewEng_ProjectsProcedure(request):
    return render(request, 'processes/procedures_workInstr/engProjectsPlanning.html')

def viewRiskProcedures(request):
    return render(request, 'processes/procedures_workInstr/riskProcedures.html')

def viewClientInteractionProcedures(request):
    return render(request, 'processes/procedures_workInstr/clientProcedures.html')

def viewPaymentProcedures(request):
    return render(request, 'processes/procedures_workInstr/paymentProcedures.html')

def viewRevenueAssuranceProcedures(request):
    return render(request, 'processes/procedures_workInstr/revenueProcedures.html')


