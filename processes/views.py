from django.shortcuts import render
from django.http import FileResponse
import  os, re
from beii_v1 import settings

# from re import pattern

# def view_process(request):
#     return render(request,'processes/view_process.html')

def view_it(request):
    return render(request,'processes/it_process.html', {"page_title": "IT Process Maps"})

def view_engineeringlist(request):
    return render(request,'processes/engineering.html', {"page_title": "Engineering Process Maps"})

#Engineering Process maps
def view_commercial(request):
    return render(request,'processes/commercial.html',{"page_title": "Commercial Process Maps"})

def view_client(request):
    return render(request,'processes/client.html',{"page_title": "Client Interaction Process Maps"})

def view_revenue(request):
    return render(request,'processes/revenue.html',{"page_title": "Revenue Assuarance Process Maps"})

def view_payment(request):
    return render(request,'processes/revenue.html',{"page_title": "Payment Process Maps"})
#end
def view_finance(request):
    return render(request,'processes/finance_processes.html',{"page_title": "Finance Process Maps"})

def view_procurement(request):
    return render(request,'processes/procurement.html',{"page_title": "Procurement Process Maps"})

def view_HR(request):
    return render(request,'processes/HR_processes.html',{"page_title": "HR Process Maps"})

def view_risk(request):
    return render(request,'processes/risk_processes.html',{"page_title": "Risk Process Maps"})

#Engineering Process maps
def view_maintenance(request):
    return render(request,'processes/maintenance_processes.html',{"page_title": "Maintenance Process Maps"})

def view_planning(request):
    return render(request,'processes/planning_processes.html',{"page_title": "Planning Process Maps"})

def view_project(request):
    return render(request,'processes/project_processes.html',{"page_title": "Project Process Maps"})

#First page after clicking view process maps
def view_img(request):
    return render(request,'processes/display.html',{"page_title": "ZETDC Interrelationship of Processes"})

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

    return render(request, 'processes/view_process.html', {'results': results, "page_title": "Process Maps (clause 4.2)"})