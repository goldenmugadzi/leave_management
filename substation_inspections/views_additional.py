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
