from datetime import datetime
import json
import os
from django.http import FileResponse
from django.shortcuts import redirect, render
from django.contrib import messages
from django.db.models import Count
from beii_v1 import settings
from .models import *
from django.contrib.auth.decorators import login_required


def _format_user(profile):
    if not profile:
        return ""
    first_name = getattr(profile, "first_name", "") or ""
    last_name = getattr(profile, "last_name", "") or ""
    full_name = f"{first_name} {last_name}".strip()
    if full_name:
        return full_name
    username = getattr(profile, "username", "") or ""
    if username:
        return username
    email = getattr(profile, "email", "") or ""
    if email:
        return email
    return str(profile)


def _normalize_report_type(raw_value):
    if not raw_value:
        return None
    mapping = {
        "report": "Report",
        "reports": "Report",
        "plan": "Plan",
        "plans": "Plan",
        "objective": "Objective",
        "objectives": "Objective",
        "ims": "Objective",
        "ims-objectives": "Objective",
    }
    return mapping.get(raw_value.lower(), raw_value.title())


def _serialize_report(report):
    return {
        "id": report.id,
        "uploaded_by": _format_user(report.uploaded_by),
        "created_by": _format_user(report.created_by),
        "region": report.region.region if report.region else "",
        "report_period": report.report_period or "",
        "report_type": (report.report_type or "").title(),
        "section": report.section.section if report.section else "",
        "file_name": report.file_name or "",
        "date_created": report.date_created.strftime("%Y-%m-%d %H:%M") if report.date_created else "",
        "date_updated": report.date_updated.strftime("%Y-%m-%d %H:%M") if report.date_updated else "",
        "status": "Archived" if report.archived else "Active",
    }


def _extract_filter_options(rows):
    def unique_sorted(key):
        return sorted({row[key] for row in rows if row.get(key)})

    return {
        "regions": unique_sorted("region"),
        "sections": unique_sorted("section"),
        "periods": unique_sorted("report_period"),
        "report_types": unique_sorted("report_type"),
    }


def _calculate_type_totals(rows):
    totals = {
        "all": len(rows),
        "reports": 0,
        "plans": 0,
        "objectives": 0,
    }
    for row in rows:
        value = (row.get("report_type") or "").lower()
        if value == "report":
            totals["reports"] += 1
        elif value == "plan":
            totals["plans"] += 1
        elif value == "objective":
            totals["objectives"] += 1
    return totals


def _build_reports_context(queryset, *, default_filters=None, view_mode="active", page_title="Business Excellence Records"):
    records = list(queryset.select_related("region", "section", "uploaded_by", "created_by"))
    rows = [_serialize_report(report) for report in records]
    filter_options = _extract_filter_options(rows)
    totals = _calculate_type_totals(rows)
    return {
        "context": json.dumps(rows, default=str),
        "filter_options": filter_options,
        "totals": totals,
        "default_filters": default_filters or {},
        "view_mode": view_mode,
        "page_title": page_title,
    }


def _build_default_filters(request):
    default_filters = {}
    normalized_type = _normalize_report_type(request.GET.get("type"))
    if normalized_type:
        default_filters["report_type"] = normalized_type
    period = request.GET.get("period")
    if period and period.lower() != "all":
        default_filters["report_period"] = period
    region = request.GET.get("region")
    if region:
        default_filters["region"] = region
    section = request.GET.get("section")
    if section:
        default_filters["section"] = section
    return default_filters

# Create your views here.
@login_required
def all_reports(request):
        
        queryset = Report.objects.filter(archived=False)
        context = _build_reports_context(
            queryset,
            default_filters=_build_default_filters(request),
            view_mode="active",
            page_title="Business Excellence Records"
        )
        
        return render(request, 'plans_reports/view_reports.html', context)
    
@login_required
def archived_reports(request):
        
        queryset = Report.objects.filter(archived=True)
        context = _build_reports_context(
            queryset,
            default_filters=_build_default_filters(request),
            view_mode="archived",
            page_title="Archived Business Excellence Records"
        )
        
        return render(request, 'plans_reports/view_reports.html', context)

@login_required
def plans_reports_index(request):
    
    type_counts = {
        "Report": 0,
        "Plan": 0,
        "Objective": 0,
    }
    for row in Report.objects.filter(archived=False).values("report_type").annotate(total=Count("id")):
        key = (row.get("report_type") or "").title()
        if key in type_counts:
            type_counts[key] = row["total"]
    totals = {
        "all": sum(type_counts.values()),
        "reports": type_counts["Report"],
        "plans": type_counts["Plan"],
        "objectives": type_counts["Objective"],
    }
    cards = [
        {
            "title": "Reports",
            "subtitle": "Operational updates",
            "description": "Opens the unified table filtered to project and operational reports.",
            "href": "/reports/all_reports/?type=reports",
            "count": totals["reports"],
        },
        {
            "title": "Plans",
            "subtitle": "Strategic planning",
            "description": "Jump straight into the table showing only departmental plans.",
            "href": "/reports/all_reports/?type=plans",
            "count": totals["plans"],
        },
        {
            "title": "IMS Objectives & Targets",
            "subtitle": "Objectives tracking",
            "description": "Review IMS objectives in the same table with filters pre-applied.",
            "href": "/reports/all_reports/?type=objectives",
            "count": totals["objectives"],
        },
    ]
    
    return render(request, 'plans_reports/plans_reports.html', {
        "totals": totals,
        "cards": cards,
    })

@login_required
def reports_index(request):
    
    return render(request, 'plans_reports/reports_index.html', {})

@login_required
def plans_index(request):
    
    return render(request, 'plans_reports/plans_index.html', {})

@login_required
def get_reports(request, period):
    period = period.capitalize()
    
    queryset = Report.objects.filter(report_type="Report", archived=False)
    default_filters = {"report_type": "Report"}
    page_title = "All Reports"
    if period != "All":
        queryset = queryset.filter(report_period=period)
        default_filters["report_period"] = period
        page_title = f"{period} Reports"
    
    context = _build_reports_context(
        queryset,
        default_filters=default_filters,
        view_mode="active",
        page_title=page_title
    )
    
    return render(request, 'plans_reports/view_reports.html', context)

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
            selected_section = Sections.objects.filter(id=request.POST.get('section')).first()
            
            # Handle section based on report type
            if report_type == "Objective":
                # For objectives, use logged in user's section and store selected section name in report_period
                section = user.section if getattr(user, "section", None) else selected_section
                report_period = selected_section.section if selected_section else None
            else:
                section = selected_section
                
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
        selected_section = Sections.objects.filter(id=request.POST.get('section')).first()
        
        # Handle section based on report type
        if report_type == "Objective":
            section = request.user.section if getattr(request.user, "section", None) else selected_section
            report_period = selected_section.section if selected_section else None
        else:
            section = selected_section
            
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
    
    queryset = Report.objects.filter(report_type="Plan", archived=False)
    default_filters = {"report_type": "Plan"}
    page_title = "All Plans"
    if period != "All":
        queryset = queryset.filter(report_period=period)
        default_filters["report_period"] = period
        page_title = f"{period} Plans"
    
    context = _build_reports_context(
        queryset,
        default_filters=default_filters,
        view_mode="active",
        page_title=page_title
    )
    
    return render(request, 'plans_reports/view_reports.html', context)

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
    
    default_filters = {
        "report_type": "Objective",
        "report_period": display_name
    }
    
    context = _build_reports_context(
        objectives,
        default_filters=default_filters,
        view_mode="active",
        page_title=f"{display_name} Objectives"
    )
    
    return render(request, 'plans_reports/view_reports.html', context)

@login_required
def objectives_index(request):
    """Display objectives index page with sections as folders"""
    return render(request, 'plans_reports/objectives_index.html', {})

def save_file(f,file_path):
    if not f:
        return False

    absolute_path = os.path.join(settings.BASE_DIR, file_path)
    os.makedirs(os.path.dirname(absolute_path), exist_ok=True)

    with open(absolute_path, 'wb+') as destination:
        for chunk in f.chunks():
            destination.write(chunk)
    return True
            
            
            
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
