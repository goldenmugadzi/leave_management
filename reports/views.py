from datetime import datetime
import json
import os
from django.http import FileResponse
from django.shortcuts import redirect, render

from beii_v1 import settings
from .models import *


# Create your views here.
def index(request):
    
    plans_and_reports_fields = Report.objects.all()
    regions = Regions.objects.all()
    sections = Sections.objects.all()
    
    files_list = []
    for file in plans_and_reports_fields:
        new_file = {
            "id": file.id,
            "uploaded_by": file.uploaded_by,
            "region": file.region,
            "report_period": file.report_period,
            "date_created": file.date_created,
            "date_updated": file.date_updated,
            "section": file.section,
            "file_name": file.file_name,
            "file_type": file.file_type,
            "file_path": file.file_path,
        }
        files_list.append(new_file)
        
    context = json.dumps(files_list, default=str)
    
    return render(request, 'plans_reports/view_reports.html', {
        'context':context,
        'regions': regions,
        'sections': sections
        })

def create_report(request):
    
    if request.method == 'POST':
        
        user = request.user
        file_path = ""
        file_type = ""
        
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES['uploaded_file']
                file_path = 'uploads/plans_and_reports/' + \
                    datetime.now().strftime("%Y%m%d%I%M%S%p") + uploaded_file.name
                save_file(uploaded_file, file_path)
                
        except Exception as ex:
            print("Error:", ex)
        
        new_plans_and_reports_fields = Report(
            uploaded_by=user if user else "",
            region=request.POST['region'],
            report_period=request.POST['report_period'],
            date_created=datetime.now().strftime("%Y%m%d"),
            date_updated=datetime.now().strftime("%Y%m%d"),
            section=request.POST['section'],
            file_name=request.POST['file_name'],
            file_type="",
            file_path=file_path,
        )
        new_plans_and_reports_fields.save()       

        
        return redirect('/reports/reports_index/')
    
    return render(request, 'plans_reports/create_report.html', {})


def download_file(request):

    file_id = request.GET['file_id']
    file_record = Report.objects.filter(id=file_id).first()
    print(file_record)
    file_path = file_record.file_path

    # search for file in system
    try:
        base_directory_path = os.path.join(settings.BASE_DIR, file_path)
        print(base_directory_path)
        return FileResponse(open(base_directory_path, 'rb'), content_type='application/pdf')
    except Exception as ex:
        print(ex)

    return redirect('/dashboards/dashboard/plans_and_reports/view')


def edit_file(request, file_id):

    if request.method == 'POST':
        print("file_id: ", file_id)
        file_record = Report.objects.filter(id=file_id).first()
        # fetch section code

        return render(request, 'dashboards/plans_and_reports/edit_reports.html', {"record": file_record})    
    
    return render(request, 'dashboards/plans_and_reports/edit_reports.html', {})

# start region - new views for Plans and Reports

def plans_and_reports_view(request):
    
    plans_and_reports_fields = Report.objects.all()
    
    files_list = []
    for file in plans_and_reports_fields:
        new_file = {
            "id": file.id,
            "uploaded_by": file.uploaded_by,
            "region": file.region,
            "report_period": file.report_period,
            "date_created": file.date_created,
            "date_updated": file.date_updated,
            "section": file.section,
            "file_name": file.file_name,
            "file_type": file.file_type,
            "file_path": file.file_path,
        }
        files_list.append(new_file)
        
    context = json.dumps(files_list, default=str)
    
    return render(request, 'dashboards/plans_and_reports/view_reports.html', {'context':context})

def save_file(f,file_path):
    if f:
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
                return True
            else:
                return False