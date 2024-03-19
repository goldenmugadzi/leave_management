from argparse import FileType
import datetime
from django.shortcuts import redirect, render
from django.http import FileResponse
import  os, re
from beii_v1 import settings
from process_risks.views import Sections
from processes.models import File_Type, First_Category, Procedures_WorkInstr, Second_Category

#UPLOAD PROCEDURES AND WORK INSTR FILES



#PROCESSES

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


#FORMS VIEWS
def new_view(request):
    return render(request, 'processes/forms/new_view.html',{"page_title": "PROCESSES AND PROCEDURES (clause 4.4)"})

def forms_index(request):
    return render(request,'processes/forms/forms_index.html', {"page_title": "FORMS"})

def engineering_forms(request):
    return render(request,'processes/forms/engineering_forms.html', {"page_title":"Engineering Forms"})
    
def finance_forms(request):
    return render(request,'processes/forms/finance_forms.html', {"page_title":"Finance Forms"})

def hr_forms(request):
    return render(request,'processes/forms/hr_forms.html', {"page_title":"Human Resources Forms"})

def commercial_forms(request):
    return render(request,'processes/forms/commercial_forms.html', {"page_title":"Commercial Forms"})

def it_forms(request):
    return render(request,'processes/forms/it_forms.html', {"page_title":"Information Technology Forms"})

def risk_forms(request):
    return render(request,'processes/forms/risk_forms.html', {"page_title":"Risk Management Forms"})


#PROCEDURES AND WORK INSTRUCTIONS
def viewWorkInstr(request):
        return render(request, 'processes/procedures_workInstr/home.html', {"page_title":"PROCEDURES AND WORK INSTRUCTIONS (clause 7.5)"})
        
def viewEngProcedureHome(request):
        return render(request, 'processes/procedures_workInstr/eng_proceduresHome.html', {"page_title":"Engineering Procedures and Work Instructions"})
    
def viewCommercialProcedureHome(request):
        return render(request, 'processes/procedures_workInstr/com_procedureHome.html', {"page_title":"Commercial Procedures and Work Instructions"})
    
def viewFinanceProcedures(request):
        return render(request, 'processes/procedures_workInstr/finance_procedures.html', {"page_title":"Finance Procedures and Work Instructions Files"})

def viewHRProcedures(request):
        return render(request, 'processes/procedures_workInstr/hr_procedure.html', {"page_title":"Human Resources Procedures and Work Instructions Files"})
    
def viewSRProcedures(request):
    return render(request, 'processes/procedures_workInstr/stakeholderRelations.html', {"page_title":"Stakeholder Relations Procedures and Work Instructions Files"})
    
def viewLegalProcedures(request):
    return render(request, 'processes/procedures_workInstr/legal_procedures.html', {"page_title":"Legal Procedures and Work Instructions Files"})

   
def viewProcurementProcedures(request):
    return render(request, 'processes/procedures_workInstr/procurement_procedures.html', {"page_title":"Procurement Procedures and Work Instructions Files"})


def viewICTProcedures(request):
    return render(request, 'processes/procedures_workInstr/ict_procedures.html', {"page_title":"ICT Procedures and Work Instructions"})

def viewICT_WorkInstr(request):
    return render(request, 'processes/procedures_workInstr/ict_workInstr.html', {"page_title":"ICT Planning Procedures and Work Instructions Files"})


def viewEng_PlanningProcedure(request):
    return render(request, 'processes/procedures_workInstr/engPlanning.html',{"page_title":"Engineering Planning Procedures and Work Instructions Files"})

def viewEng_MaintananceProcedure(request):
    return render(request, 'processes/procedures_workInstr/engMaintanance.html',{"page_title":"Engineering Maintanance Procedures and Work Instructions Files"})

def viewEng_ProjectsProcedure(request):
    return render(request, 'processes/procedures_workInstr/engProjectsPlanning.html',{"page_title":"Engineering Projects Procedures and Work Instructions Files"})

def viewRiskProcedures(request):
    return render(request, 'processes/procedures_workInstr/riskProcedures.html', {"page_title":"Risk Management Procedures and Work Instructions Files"})

def viewClientInteractionProcedures(request):
    return render(request, 'processes/procedures_workInstr/clientProcedures.html', {"page_title":"Client Interaction Procedures and Work Instructions Files"})

def viewPaymentProcedures(request):
    return render(request, 'processes/procedures_workInstr/paymentProcedures.html', {"page_title":"Payment Procedures and Work Instructions Files"})

def viewRevenueAssuranceProcedures(request):
    return render(request, 'processes/procedures_workInstr/revenueProcedures.html', {"page_title":"Revenue Assurance Procedures and Work Instructions Files"})


