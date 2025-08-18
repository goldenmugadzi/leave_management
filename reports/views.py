from datetime import datetime
import json
import os
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from beii_v1 import settings
from .models import *
from django.contrib.auth.decorators import login_required

# Create your views here.
@login_required
def all_reports(request):
        
        plans_and_reports_fields = Report.objects.filter(archived=False).all()
        
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
                "file_path": file.file_path,
            }
            files_list.append(new_file)
            
        context = json.dumps(files_list, default=str)
        
        return render(request, 'plans_reports/view_reports.html', {'context':context})
    
@login_required
def archived_reports(request):
        
        plans_and_reports_fields = Report.objects.filter(archived=True).all()
        
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
                "file_path": file.file_path,
            }
            files_list.append(new_file)
            
        context = json.dumps(files_list, default=str)
        
        return render(request, 'plans_reports/view_reports.html', {'context':context})

@login_required
def plans_reports_index(request):
    
    return render(request, 'plans_reports/plans_reports.html', {})

@login_required
def reports_index(request):
    
    return render(request, 'plans_reports/reports_index.html', {})

@login_required
def plans_index(request):
    
    return render(request, 'plans_reports/plans_index.html', {})

@login_required
def get_reports(request, period):
    period = period.capitalize()
    
    if period == "All":
        plans_and_reports_fields = Report.objects.filter(report_type="Report", archived=False).all()
    else:
        plans_and_reports_fields = Report.objects.filter(report_type="Report", report_period=period, archived=False).all()
        
    regions = Regions.objects.all()
    sections = Sections.objects.all()
    
    files_list = []
    for file in plans_and_reports_fields:
        fullname = file.created_by.first_name + " " + file.created_by.last_name if file.created_by else None
        new_file = {
            "id": file.id,
            "uploaded_by": file.uploaded_by,
            "region": file.region.region,
            "report_period": file.report_period,
            "date_created": file.date_created.strftime("%Y-%m-%d %H:%M") if file.date_created else "",
            "date_updated": file.date_updated.strftime("%Y-%m-%d %H:%M") if file.date_updated else "",
            "section": file.section.section,
            "file_name": file.file_name,
            "file_path": file.file_path,
            "created_by": fullname
        }
        files_list.append(new_file)
        
    context = json.dumps(files_list, default=str)
    
    return render(request, 'plans_reports/view_reports.html', {
        'context':context,
        'regions': regions,
        'sections': sections
        })

@login_required
def create_report(request):
    
    if request.method == 'POST':
        
        user = request.user
        report_period = request.POST.get('report_period')
        report_type = request.POST.get('report_type')
        file_name = request.POST.get('file_name')
        file_path = ""
        
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES['uploaded_file']
                file_path = 'uploads/plans_and_reports/' + \
                    datetime.now().strftime("%Y%m%d%I%M%S%p") + uploaded_file.name
                save_file(uploaded_file, file_path)
                
        except Exception as ex:
            print("Error:", ex)
        
        try:
            region = Regions.objects.filter(id=request.POST.get('region')).first()
            
            # Handle section based on report type
            if report_type == "Objective":
                # For objectives, use logged in user's section and store section name in report_period
                section = user.section if user.section else None
                # Store the section name in report_period field for objectives
                report_period = request.POST.get('section') if request.POST.get('section') else None
            else:
                # For reports and plans, use the existing logic
                section = Sections.objects.filter(id=request.POST.get('section')).first()
                
            created_by = UserProfile.objects.filter(id=user.id).first()
            new_plans_and_reports_fields = Report(
                uploaded_by=user if user else "",
                region=region if region else None,
                report_period=report_period if report_period else None,
                report_type=report_type if report_type else None,
                date_created=datetime.now().strftime("%Y%m%d"),
                date_updated=datetime.now().strftime("%Y%m%d"),
                section=section if section else None,
                file_name=file_name if file_name else "",
                file_path=file_path,
                created_by=created_by if created_by else None
            )
            new_plans_and_reports_fields.save()       
            
            messages.success(request, 'Report created successfully')        
            if report_type == "Objective":
                # For objectives, redirect to the objectives index
                return redirect('/reports/objectives_index')
            elif report_period:
                period = report_period.lower()
                report = report_type.lower()+'s'
            else:
                period = "all"
                report = report_type.lower()+'s'

            return redirect('/reports/'+report+'/'+period)
        except Exception as ex:
            print("Error:", ex)
    
    sections = Sections.objects.all()
    regions = Regions.objects.all()
    return render(request, 'plans_reports/create_report.html', {
        "sections": sections,
        "regions": regions
    })

@login_required
def download_file(request):

    file_id = request.GET['file_id']
    file_record = Report.objects.filter(id=file_id).first()
    print(file_record)
    file_path = file_record.file_path

    # search for file in system
    try:
        base_directory_path = os.path.join(settings.BASE_DIR, file_path)
        import mimetypes
        content_type, _ = mimetypes.guess_type(base_directory_path)
        if content_type is None:
            content_type = 'application/octet-stream'  # Default to binary file type if MIME type cannot be guessed
        print("content_type: ", content_type)
        print("base_directory_path: ", base_directory_path)
        return FileResponse(open(base_directory_path, 'rb'), content_type=content_type)
    except Exception as ex:
        print(ex)

    return redirect('/reports/reports_index/')

@login_required
def edit_report(request):

    if request.method == 'POST':

        print("request.POST: ", request.POST)
        report_id = request.POST.get('report_id')
        report_period = request.POST.get('report_period')
        report_type = request.POST.get('report_type')
        file_name = request.POST.get('file_name')
        file_path = ""
        
        try:
            if 'uploaded_file' in request.FILES:
                uploaded_file = request.FILES['uploaded_file']
                file_path = 'uploads/plans_and_reports/' + \
                    datetime.now().strftime("%Y%m%d%I%M%S%p") + uploaded_file.name
                save_file(uploaded_file, file_path)

        except Exception as ex:
            print("Error:", ex)
        
        region = Regions.objects.filter(id=request.POST.get('region')).first()
        
        # Handle section based on report type
        if report_type == "Objective":
            # For objectives, use logged in user's section and store section name in report_period
            section = request.user.section if request.user.section else None
            # Store the section name in report_period field for objectives
            report_period = request.POST.get('section') if request.POST.get('section') else None
        else:
            # For reports and plans, use the existing logic
            section = Sections.objects.filter(id=request.POST.get('section')).first()
            
        report_ = Report.objects.filter(id=report_id).first()

        if report_:
            if file_path:
                report_.file_path = file_path
            if report_type:
                report_.report_type = report_type
            if report_period:
                report_.report_period = report_period
            if file_name:
                report_.file_name = file_name
            if region:
                report_.region = region
            if section:
                report_.section = section
            report_.date_updated = datetime.now().strftime("%Y%m%d")

            report_.save()       
        
        if report_type == "Objective":
            # For objectives, redirect to the objectives index
            messages.success(request, 'Objective updated successfully')
            return redirect('/reports/objectives_index')
        elif report_period:
            period = report_period.lower()
            report = report_type.lower()+'s'
        else:
            period = "all"
            report = report_type.lower()+'s'

        messages.success(request, 'Report updated successfully')
        return redirect('/reports/'+report+'/'+period)
    
    file_id = request.GET['i']
    report = Report.objects.filter(id=file_id).first()
    sections = Sections.objects.all()
    regions = Regions.objects.all()
    print("report: ", report)
    return render(request, 'plans_reports/update_report.html', {
        "report": report,
        "sections": sections,
        "regions": regions
        })    
    
# return render(request, 'dashboards/plans_and_reports/edit_reports.html', {})

@login_required
def get_plans(request, period):
    period = period.capitalize()
    
    if period == "All":
        plans_and_reports_fields = Report.objects.filter(report_type="Plan", archived=False).all()
    else:
        plans_and_reports_fields = Report.objects.filter(report_type="Plan", report_period=period, archived=False).all()
    
    files_list = []
    for file in plans_and_reports_fields:
        new_file = {
            "id": file.id,
            "uploaded_by": file.uploaded_by,
            "region": file.region,
            "report_period": file.report_period,
            "report_type": file.report_type,
            "date_created": file.date_created,
            "date_updated": file.date_updated,
            "section": file.section,
            "file_name": file.file_name,
            "file_path": file.file_path,
        }
        files_list.append(new_file)
        
    context = json.dumps(files_list, default=str)
    
    return render(request, 'plans_reports/view_reports.html', {'context':context})

@login_required
def get_objectives(request, section_name):
    """Get objectives filtered by section name stored in report_period field"""
    # Map URL section names to display names
    section_mapping = {
        'commercial': 'COMMERCIAL',
        'hr': 'HUMAN RESOURCES', 
        'engineering': 'ENGINEERING',
        'ict': 'ICT',
        'risk': 'RISK',
        'finance': 'FINANCE',
        'stakeholder-relations': 'STAKEHOLDER RELATIONS',
        'legal': 'LEGAL',
        'procurement': 'PROCUREMENT'
    }
    
    display_name = section_mapping.get(section_name, section_name.upper())
    
    # For objectives, filter by report_period field which contains the section name
    objectives = Report.objects.filter(
        report_type="Objective", 
        report_period=display_name, 
        archived=False
    ).all()
    
    files_list = []
    for file in objectives:
        fullname = file.created_by.first_name + " " + file.created_by.last_name if file.created_by else None
        new_file = {
            "id": file.id,
            "uploaded_by": file.uploaded_by,
            "region": file.region.region if file.region else "",
            "report_period": file.report_period,  # This contains the section name for objectives
            "date_created": file.date_created.strftime("%Y-%m-%d %H:%M") if file.date_created else "",
            "date_updated": file.date_updated.strftime("%Y-%m-%d %H:%M") if file.date_updated else "",
            "section": file.section.section if file.section else "",
            "file_name": file.file_name,
            "file_path": file.file_path,
            "created_by": fullname
        }
        files_list.append(new_file)
        
    context = json.dumps(files_list, default=str)
    
    return render(request, 'plans_reports/view_reports.html', {
        'context': context,
        'section_name': display_name
    })

@login_required
def objectives_index(request):
    """Display objectives index page with sections as folders"""
    return render(request, 'plans_reports/objectives_index.html', {})

def save_file(f,file_path):
    if f:
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
            return True
    else:
        return False
            
            
            
# start region - new views for Plans and Reports

@login_required
def plans_and_reports_view(request):
    
    plans_and_reports_fields = Report.objects.filter(report_type="Report").all()
    
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
