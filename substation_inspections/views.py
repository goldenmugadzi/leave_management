from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from datetime import datetime, timedelta
from .models import (
    Substation, 
    MonthlyInspectionSchedule, 
    MonthlyInspectionReport, 
    InspectionChecklistItem, 
    InspectionItemResponse
)
from .forms import (
    SubstationForm, 
    MonthlyInspectionScheduleForm, 
    MonthlyInspectionForm,
    InspectionChecklistItemForm,
    InspectionItemResponseForm,
    InspectionReportSearchForm,
    BulkInspectionAssignmentForm
)


@login_required
def dashboard(request):
    """Main dashboard for substation inspection administration"""
    
    # Get statistics
    total_substations = Substation.objects.filter(is_active=True).count()
    pending_inspections = MonthlyInspectionReport.objects.filter(status='scheduled').count()
    in_progress_inspections = MonthlyInspectionReport.objects.filter(status='in_progress').count()
    completed_this_month = MonthlyInspectionReport.objects.filter(
        status='completed',
        inspection_date__month=timezone.now().month,
        inspection_date__year=timezone.now().year
    ).count()
    overdue_inspections = MonthlyInspectionReport.objects.filter(status='overdue').count()
    
    # Get recent inspections
    recent_inspections = MonthlyInspectionReport.objects.select_related(
        'substation', 'inspector'
    ).order_by('-created_at')[:10]
    
    # Get upcoming inspections (next 7 days)
    upcoming_date = timezone.now().date() + timedelta(days=7)
    upcoming_inspections = MonthlyInspectionReport.objects.filter(
        inspection_date__lte=upcoming_date,
        inspection_date__gte=timezone.now().date(),
        status='scheduled'
    ).select_related('substation', 'inspector')
    
    context = {
        'total_substations': total_substations,
        'pending_inspections': pending_inspections,
        'in_progress_inspections': in_progress_inspections,
        'completed_this_month': completed_this_month,
        'overdue_inspections': overdue_inspections,
        'recent_inspections': recent_inspections,
        'upcoming_inspections': upcoming_inspections,
    }
    
    return render(request, 'substation_inspections/dashboard.html', context)


@login_required
def substation_list(request):
    """List all substations"""
    search_query = request.GET.get('search', '')
    substation_type = request.GET.get('type', '')
    is_active = request.GET.get('active', '')
    
    substations = Substation.objects.all()
    
    if search_query:
        substations = substations.filter(
            Q(substation_code__icontains=search_query) |
            Q(name__icontains=search_query) |
            Q(location__icontains=search_query)
        )
    
    if substation_type:
        substations = substations.filter(substation_type=substation_type)
    
    if is_active:
        substations = substations.filter(is_active=is_active == 'true')
    
    # Pagination
    paginator = Paginator(substations, 20)
    page_number = request.GET.get('page')
    substations = paginator.get_page(page_number)
    
    context = {
        'substations': substations,
        'search_query': search_query,
        'substation_type': substation_type,
        'is_active': is_active,
    }
    
    return render(request, 'substation_inspections/substation_list.html', context)


@login_required
def substation_detail(request, pk):
    """Detail view for a specific substation"""
    substation = get_object_or_404(Substation, pk=pk)
    
    # Get inspection schedules for this substation
    schedules = substation.inspection_schedules.filter(is_active=True)
    
    # Get recent inspection reports
    recent_reports = substation.monthly_reports.order_by('-inspection_date')[:10]
    
    # Get inspection statistics
    total_inspections = substation.monthly_reports.count()
    completed_inspections = substation.monthly_reports.filter(status='completed').count()
    pending_inspections = substation.monthly_reports.filter(status='scheduled').count()
    
    context = {
        'substation': substation,
        'schedules': schedules,
        'recent_reports': recent_reports,
        'total_inspections': total_inspections,
        'completed_inspections': completed_inspections,
        'pending_inspections': pending_inspections,
    }
    
    return render(request, 'substation_inspections/substation_detail.html', context)


@login_required
def substation_create(request):
    """Create a new substation"""
    if request.method == 'POST':
        form = SubstationForm(request.POST)
        if form.is_valid():
            substation = form.save()
            messages.success(request, f'Substation {substation.substation_code} created successfully.')
            return redirect('substation_inspections:substation_detail', pk=substation.pk)
    else:
        form = SubstationForm()
    
    return render(request, 'substation_inspections/substation_form.html', {
        'form': form,
        'title': 'Create New Substation'
    })


@login_required
def substation_edit(request, pk):
    """Edit an existing substation"""
    substation = get_object_or_404(Substation, pk=pk)
    
    if request.method == 'POST':
        form = SubstationForm(request.POST, instance=substation)
        if form.is_valid():
            substation = form.save()
            messages.success(request, f'Substation {substation.substation_code} updated successfully.')
            return redirect('substation_inspections:substation_detail', pk=substation.pk)
    else:
        form = SubstationForm(instance=substation)
    
    return render(request, 'substation_inspections/substation_form.html', {
        'form': form,
        'substation': substation,
        'title': f'Edit {substation.name}'
    })


@login_required
def inspection_report_list(request):
    """List all inspection reports with filtering"""
    search_form = InspectionReportSearchForm(request.GET)
    reports = MonthlyInspectionReport.objects.select_related('substation', 'inspector')
    
    if search_form.is_valid():
        if search_form.cleaned_data.get('substation'):
            reports = reports.filter(substation=search_form.cleaned_data['substation'])
        if search_form.cleaned_data.get('status'):
            reports = reports.filter(status=search_form.cleaned_data['status'])
        if search_form.cleaned_data.get('compliance_status'):
            reports = reports.filter(compliance_status=search_form.cleaned_data['compliance_status'])
        if search_form.cleaned_data.get('inspector'):
            reports = reports.filter(inspector=search_form.cleaned_data['inspector'])
        if search_form.cleaned_data.get('date_from'):
            reports = reports.filter(inspection_date__gte=search_form.cleaned_data['date_from'])
        if search_form.cleaned_data.get('date_to'):
            reports = reports.filter(inspection_date__lte=search_form.cleaned_data['date_to'])
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    reports = paginator.get_page(page_number)
    
    context = {
        'reports': reports,
        'search_form': search_form,
    }
    
    return render(request, 'substation_inspections/inspection_report_list.html', context)


@login_required
def inspection_report_detail(request, pk):
    """Detail view for a specific inspection report"""
    report = get_object_or_404(MonthlyInspectionReport, pk=pk)
    
    # Get all item responses for this report
    item_responses = report.item_responses.select_related('checklist_item').order_by(
        'checklist_item__category', 'checklist_item__item_code'
    )
    
    # Group responses by category
    responses_by_category = {}
    for response in item_responses:
        category = response.checklist_item.get_category_display()
        if category not in responses_by_category:
            responses_by_category[category] = []
        responses_by_category[category].append(response)
    
    context = {
        'report': report,
        'item_responses': item_responses,
        'responses_by_category': responses_by_category,
    }
    
    return render(request, 'substation_inspections/inspection_report_detail.html', context)


@login_required
def inspection_report_create(request):
    """Create a new inspection report"""
    if request.method == 'POST':
        form = MonthlyInspectionForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.inspector = request.user
            report.save()
            messages.success(request, f'Inspection report {report.report_number} created successfully.')
            return redirect('substation_inspections:inspection_report_detail', pk=report.pk)
    else:
        form = MonthlyInspectionForm()
    
    return render(request, 'substation_inspections/inspection_report_form.html', {
        'form': form,
        'title': 'Create New Inspection Report'
    })


@login_required
def inspection_report_edit(request, pk):
    """Edit an existing inspection report"""
    report = get_object_or_404(MonthlyInspectionReport, pk=pk)
    
    # Only allow editing if not completed
    if report.status == 'completed':
        messages.error(request, 'Cannot edit completed inspection reports.')
        return redirect('substation_inspections:inspection_report_detail', pk=report.pk)
    
    if request.method == 'POST':
        form = MonthlyInspectionForm(request.POST, instance=report)
        if form.is_valid():
            report = form.save()
            messages.success(request, f'Inspection report {report.report_number} updated successfully.')
            return redirect('substation_inspections:inspection_report_detail', pk=report.pk)
    else:
        form = MonthlyInspectionForm(instance=report)
    
    return render(request, 'substation_inspections/inspection_report_form.html', {
        'form': form,
        'report': report,
        'title': f'Edit {report.report_number}'
    })


@login_required
def schedule_list(request):
    """List all inspection schedules"""
    schedules = MonthlyInspectionSchedule.objects.select_related('substation', 'assigned_inspector')
    
    # Pagination
    paginator = Paginator(schedules, 20)
    page_number = request.GET.get('page')
    schedules = paginator.get_page(page_number)
    
    context = {
        'schedules': schedules,
    }
    
    return render(request, 'substation_inspections/schedule_list.html', context)


@login_required
def schedule_create(request):
    """Create a new inspection schedule"""
    if request.method == 'POST':
        form = MonthlyInspectionScheduleForm(request.POST)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, f'Inspection schedule created successfully.')
            return redirect('substation_inspections:schedule_list')
    else:
        form = MonthlyInspectionScheduleForm()
    
    return render(request, 'substation_inspections/schedule_form.html', {
        'form': form,
        'title': 'Create New Inspection Schedule'
    })


@login_required
def schedule_edit(request, pk):
    """Edit an existing inspection schedule"""
    schedule = get_object_or_404(MonthlyInspectionSchedule, pk=pk)
    
    if request.method == 'POST':
        form = MonthlyInspectionScheduleForm(request.POST, instance=schedule)
        if form.is_valid():
            schedule = form.save()
            messages.success(request, f'Inspection schedule updated successfully.')
            return redirect('substation_inspections:schedule_list')
    else:
        form = MonthlyInspectionScheduleForm(instance=schedule)
    
    return render(request, 'substation_inspections/schedule_form.html', {
        'form': form,
        'schedule': schedule,
        'title': f'Edit Schedule for {schedule.substation.name}'
    })


@login_required
def checklist_item_list(request):
    """List all inspection checklist items"""
    search_query = request.GET.get('search', '')
    category = request.GET.get('category', '')
    
    items = InspectionChecklistItem.objects.all()
    
    if search_query:
        items = items.filter(
            Q(item_code__icontains=search_query) |
            Q(title__icontains=search_query) |
            Q(description__icontains=search_query)
        )
    
    if category:
        items = items.filter(category=category)
    
    # Pagination
    paginator = Paginator(items, 20)
    page_number = request.GET.get('page')
    items = paginator.get_page(page_number)
    
    context = {
        'items': items,
        'search_query': search_query,
        'category': category,
    }
    
    return render(request, 'substation_inspections/checklist_item_list.html', context)


@login_required
def checklist_item_create(request):
    """Create a new checklist item"""
    if request.method == 'POST':
        form = InspectionChecklistItemForm(request.POST)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Checklist item {item.item_code} created successfully.')
            return redirect('substation_inspections:checklist_item_list')
    else:
        form = InspectionChecklistItemForm()
    
    return render(request, 'substation_inspections/checklist_item_form.html', {
        'form': form,
        'title': 'Create New Checklist Item'
    })


@login_required
def checklist_item_edit(request, pk):
    """Edit an existing checklist item"""
    item = get_object_or_404(InspectionChecklistItem, pk=pk)
    
    if request.method == 'POST':
        form = InspectionChecklistItemForm(request.POST, instance=item)
        if form.is_valid():
            item = form.save()
            messages.success(request, f'Checklist item {item.item_code} updated successfully.')
            return redirect('substation_inspections:checklist_item_list')
    else:
        form = InspectionChecklistItemForm(instance=item)
    
    return render(request, 'substation_inspections/checklist_item_form.html', {
        'form': form,
        'item': item,
        'title': f'Edit {item.item_code}'
    })


@login_required
def bulk_assignment(request):
    """Bulk assignment of inspections to inspectors"""
    if request.method == 'POST':
        form = BulkInspectionAssignmentForm(request.POST)
        if form.is_valid():
            inspections = form.cleaned_data['inspections']
            inspector = form.cleaned_data['inspector']
            notes = form.cleaned_data.get('notes', '')
            
            updated_count = 0
            for inspection in inspections:
                inspection.inspector = inspector
                inspection.save()
                updated_count += 1
            
            messages.success(request, f'{updated_count} inspections assigned to {inspector.get_full_name()}.')
            return redirect('substation_inspections:inspection_report_list')
    else:
        form = BulkInspectionAssignmentForm()
    
    return render(request, 'substation_inspections/bulk_assignment.html', {
        'form': form,
        'title': 'Bulk Assignment'
    })


# API endpoints for AJAX requests
@login_required
def get_substation_details(request, pk):
    """Get substation details as JSON"""
    substation = get_object_or_404(Substation, pk=pk)
    data = {
        'id': str(substation.id),
        'substation_code': substation.substation_code,
        'name': substation.name,
        'substation_type': substation.get_substation_type_display(),
        'voltage_level': substation.get_voltage_level_display(),
        'location': substation.location,
        'district': substation.district,
        'region': substation.region,
        'transformers_count': substation.transformers_count,
        'circuit_breakers_count': substation.circuit_breakers_count,
        'switchgear_count': substation.switchgear_count,
        'is_active': substation.is_active,
        'last_inspection_date': substation.last_inspection_date.isoformat() if substation.last_inspection_date else None,
        'next_scheduled_inspection': substation.next_scheduled_inspection.isoformat() if substation.next_scheduled_inspection else None,
    }
    return JsonResponse(data)


@login_required
def get_inspection_stats(request):
    """Get inspection statistics as JSON"""
    stats = {
        'total_substations': Substation.objects.filter(is_active=True).count(),
        'pending_inspections': MonthlyInspectionReport.objects.filter(status='scheduled').count(),
        'in_progress_inspections': MonthlyInspectionReport.objects.filter(status='in_progress').count(),
        'completed_this_month': MonthlyInspectionReport.objects.filter(
            status='completed',
            inspection_date__month=timezone.now().month,
            inspection_date__year=timezone.now().year
        ).count(),
        'overdue_inspections': MonthlyInspectionReport.objects.filter(status='overdue').count(),
    }
    return JsonResponse(stats)