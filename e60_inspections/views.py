from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import HttpResponse, JsonResponse
from django.db import transaction
from datetime import datetime
import logging

from .models import (
    E60InspectionReport,
    E60TransformerInspection,
    E60CircuitBreakerInspection,
    E60MeteringInspection,
    E60HousingInspection,
    E60FuseInspection,
    E60SurgeArrestorInspection,
    E60GeneralStateInspection,
    E60SafetyInspection,
    E60ConsumerInstallationInspection,
)

from .forms import (
    E60InspectionReportForm,
    E60TransformerInspectionForm,
    E60CircuitBreakerInspectionForm,
    E60MeteringInspectionForm,
    E60HousingInspectionForm,
    E60FuseInspectionForm,
    E60SurgeArrestorInspectionForm,
    E60GeneralStateInspectionForm,
    E60SafetyInspectionForm,
    E60ConsumerInstallationInspectionForm,
)

logger = logging.getLogger(__name__)


@login_required
def e60_inspection_list(request):
    """List all E60 inspection reports with filtering and pagination"""
    inspections = E60InspectionReport.objects.all().order_by('-inspection_date')
    
    # Add filtering logic
    search_query = request.GET.get('search', '')
    status_filter = request.GET.get('status', '')
    inspection_type_filter = request.GET.get('inspection_type', '')
    
    if search_query:
        inspections = inspections.filter(
            Q(substation_name__icontains=search_query) |
            Q(service_number__icontains=search_query) |
            Q(section__icontains=search_query) |
            Q(report_number__icontains=search_query)
        )
    
    if status_filter:
        inspections = inspections.filter(status=status_filter)
    
    if inspection_type_filter:
        inspections = inspections.filter(inspection_type=inspection_type_filter)
    
    # Add pagination
    paginator = Paginator(inspections, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_query': search_query,
        'status_filter': status_filter,
        'inspection_type_filter': inspection_type_filter,
        'status_choices': E60InspectionReport.STATUS_CHOICES,
        'inspection_type_choices': E60InspectionReport.INSPECTION_TYPE_CHOICES,
    }
    
    return render(request, 'e60_inspections/inspection_list.html', context)


@login_required
def e60_inspection_create(request):
    """Create a new E60 inspection report"""
    if request.method == 'POST':
        form = E60InspectionReportForm(request.POST)
        if form.is_valid():
            inspection = form.save(commit=False)
            inspection.inspector = request.user
            inspection.save()
            messages.success(request, f'E60 Inspection Report {inspection.report_number} created successfully.')
            return redirect('e60_inspections:e60_inspection_detail', pk=inspection.pk)
    else:
        form = E60InspectionReportForm()
    
    context = {
        'form': form,
        'title': 'Create E60 Inspection Report'
    }
    
    return render(request, 'e60_inspections/inspection_form.html', context)


@login_required
def e60_inspection_detail(request, pk):
    """Display detailed E60 inspection report with all sections"""
    inspection = get_object_or_404(E60InspectionReport, pk=pk)
    
    # Get all related inspection data
    transformer_inspection = getattr(inspection, 'transformer_inspection', None)
    circuit_breaker_inspection = getattr(inspection, 'circuit_breaker_inspection', None)
    metering_inspection = getattr(inspection, 'metering_inspection', None)
    housing_inspection = getattr(inspection, 'housing_inspection', None)
    fuse_inspection = getattr(inspection, 'fuse_inspection', None)
    surge_arrestor_inspections = inspection.surge_arrestor_inspections.all()
    general_state_inspection = getattr(inspection, 'general_state_inspection', None)
    safety_inspection = getattr(inspection, 'safety_inspection', None)
    consumer_installation_inspection = getattr(inspection, 'consumer_installation_inspection', None)
    
    context = {
        'inspection': inspection,
        'transformer_inspection': transformer_inspection,
        'circuit_breaker_inspection': circuit_breaker_inspection,
        'metering_inspection': metering_inspection,
        'housing_inspection': housing_inspection,
        'fuse_inspection': fuse_inspection,
        'surge_arrestor_inspections': surge_arrestor_inspections,
        'general_state_inspection': general_state_inspection,
        'safety_inspection': safety_inspection,
        'consumer_installation_inspection': consumer_installation_inspection,
    }
    
    return render(request, 'e60_inspections/inspection_detail.html', context)


@login_required
def e60_inspection_edit(request, pk):
    """Edit the main E60 inspection report details"""
    inspection = get_object_or_404(E60InspectionReport, pk=pk)
    
    if request.method == 'POST':
        form = E60InspectionReportForm(request.POST, instance=inspection)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inspection report updated successfully.')
            return redirect('e60_inspections:e60_inspection_detail', pk=inspection.pk)
    else:
        form = E60InspectionReportForm(instance=inspection)
    
    context = {
        'form': form,
        'inspection': inspection,
        'title': f'Edit E60 Inspection Report - {inspection.report_number}'
    }
    
    return render(request, 'e60_inspections/inspection_form.html', context)


@login_required
def e60_inspection_delete(request, pk):
    """Delete an E60 inspection report"""
    inspection = get_object_or_404(E60InspectionReport, pk=pk)
    
    if request.method == 'POST':
        report_number = inspection.report_number
        inspection.delete()
        messages.success(request, f'Inspection report {report_number} deleted successfully.')
        return redirect('e60_inspections:e60_inspection_list')
    
    context = {
        'inspection': inspection,
        'title': f'Delete E60 Inspection Report - {inspection.report_number}'
    }
    
    return render(request, 'e60_inspections/inspection_confirm_delete.html', context)


@login_required
def e60_transformer_edit(request, pk):
    """Edit transformer inspection section"""
    inspection = get_object_or_404(E60InspectionReport, pk=pk)
    transformer_inspection, created = E60TransformerInspection.objects.get_or_create(
        inspection_report=inspection
    )
    
    logger.info(f"Transformer edit view accessed - Method: {request.method}, User: {request.user}, Inspection: {inspection.pk}")
    
    if request.method == 'POST':
        logger.info(f"POST data received: {request.POST}")
        form = E60TransformerInspectionForm(request.POST, instance=transformer_inspection)
        logger.info(f"Form created, is_valid: {form.is_valid()}")
        if form.is_valid():
            saved_instance = form.save()
            logger.info(f"Form saved successfully. Make: {saved_instance.make}, KVA: {saved_instance.kva_rating}")
            messages.success(request, f'Transformer inspection section updated successfully! Make: {saved_instance.make}, KVA: {saved_instance.kva_rating}kVA')
            return redirect('e60_inspections:e60_inspection_detail', pk=inspection.pk)
        else:
            logger.error(f"Form validation failed: {form.errors}")
            messages.error(request, f'Form validation failed: {form.errors}')
    else:
        form = E60TransformerInspectionForm(instance=transformer_inspection)
        logger.info(f"GET request - Form initialized with instance: {transformer_inspection.pk}")
    
    context = {
        'form': form,
        'inspection': inspection,
        'section_title': 'Section A: TRANSFORMERS',
        'title': f'Edit Transformer Inspection - {inspection.report_number}'
    }
    
    return render(request, 'e60_inspections/section_form.html', context)


@login_required
def e60_circuit_breaker_edit(request, pk):
    """Edit circuit breaker inspection section"""
    inspection = get_object_or_404(E60InspectionReport, pk=pk)
    circuit_breaker_inspection, created = E60CircuitBreakerInspection.objects.get_or_create(
        inspection_report=inspection
    )
    
    if request.method == 'POST':
        form = E60CircuitBreakerInspectionForm(request.POST, instance=circuit_breaker_inspection)
        if form.is_valid():
            form.save()
            messages.success(request, 'Circuit breaker inspection section updated successfully.')
            return redirect('e60_inspections:e60_inspection_detail', pk=inspection.pk)
    else:
        form = E60CircuitBreakerInspectionForm(instance=circuit_breaker_inspection)
    
    context = {
        'form': form,
        'inspection': inspection,
        'section_title': 'Section B: A.C.B or O.C.B',
        'title': f'Edit Circuit Breaker Inspection - {inspection.report_number}'
    }
    
    return render(request, 'e60_inspections/section_form.html', context)


# Additional views will be added in the next phase
# For now, implementing placeholder views to avoid URL errors

@login_required
def e60_metering_edit(request, pk):
    """Edit metering inspection section - placeholder"""
    messages.info(request, 'Metering section editing will be fully implemented in the next phase.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_housing_edit(request, pk):
    """Edit housing inspection section - placeholder"""
    messages.info(request, 'Housing section editing will be fully implemented in the next phase.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_fuse_edit(request, pk):
    """Edit fuse inspection section - placeholder"""
    messages.info(request, 'Fuse section editing will be fully implemented in the next phase.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_surge_arrestor_edit(request, pk):
    """Edit surge arrestor inspection section - placeholder"""
    messages.info(request, 'Surge arrestor section editing will be fully implemented in the next phase.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_general_state_edit(request, pk):
    """Edit general state inspection section - placeholder"""
    messages.info(request, 'General state section editing will be fully implemented in the next phase.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_safety_edit(request, pk):
    """Edit safety inspection section - placeholder"""
    messages.info(request, 'Safety section editing will be fully implemented in the next phase.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_consumer_installation_edit(request, pk):
    """Edit consumer installation inspection section - placeholder"""
    messages.info(request, 'Consumer installation section editing will be fully implemented in the next phase.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_inspection_print(request, pk):
    """Print-friendly view of E60 inspection report - placeholder"""
    messages.info(request, 'Print functionality will be implemented in Phase 3.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_inspection_pdf(request, pk):
    """Generate PDF export of E60 inspection report - placeholder"""
    messages.info(request, 'PDF generation feature will be implemented in Phase 3.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_inspection_export(request, pk):
    """Export E60 inspection report data - placeholder"""
    messages.info(request, 'Data export feature will be implemented in Phase 3.')
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_inspection_approve(request, pk):
    """Approve an E60 inspection report"""
    inspection = get_object_or_404(E60InspectionReport, pk=pk)
    
    if request.method == 'POST':
        inspection.status = 'approved'
        inspection.save()
        messages.success(request, f'Inspection report {inspection.report_number} approved successfully.')
    
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_inspection_submit(request, pk):
    """Submit an E60 inspection report for approval"""
    inspection = get_object_or_404(E60InspectionReport, pk=pk)
    
    if request.method == 'POST':
        inspection.status = 'completed'
        inspection.save()
        messages.success(request, f'Inspection report {inspection.report_number} submitted for approval.')
    
    return redirect('e60_inspections:e60_inspection_detail', pk=pk)

@login_required
def e60_dashboard(request):
    """Dashboard view for E60 inspections overview"""
    # Basic statistics
    total_inspections = E60InspectionReport.objects.count()
    pending_inspections = E60InspectionReport.objects.filter(status='draft').count()
    completed_inspections = E60InspectionReport.objects.filter(status='completed').count()
    approved_inspections = E60InspectionReport.objects.filter(status='approved').count()
    
    # Recent inspections
    recent_inspections = E60InspectionReport.objects.order_by('-created_at')[:10]
    
    context = {
        'total_inspections': total_inspections,
        'pending_inspections': pending_inspections,
        'completed_inspections': completed_inspections,
        'approved_inspections': approved_inspections,
        'recent_inspections': recent_inspections,
    }
    
    return render(request, 'e60_inspections/dashboard.html', context)

@login_required
def e60_analytics(request):
    """Analytics view for E60 inspections"""
    # This will be implemented later with detailed analytics
    messages.info(request, 'Analytics feature will be implemented in Phase 3.')
    return redirect('e60_inspections:e60_dashboard')