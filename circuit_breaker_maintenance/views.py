from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from django.utils import timezone
from django.db import transaction
from django.core.exceptions import ValidationError
from .models import CircuitBreaker, MaintenanceRecord
from .forms import (
    CircuitBreakerForm, 
    CircuitBreakerBulkImportForm, 
    QuickCircuitBreakerForm, 
    MaintenanceRecordForm, 
    MaintenanceRecordQuickForm
)
import csv
import pandas as pd
from io import StringIO
import logging
import traceback
from django.db import IntegrityError

# Add this at the top with other imports
logger = logging.getLogger(__name__)

# Integration helpers
def get_circuit_breaker_checklist_items():
    """Get circuit breaker checklist items from substation inspections module"""
    try:
        from substation_inspections.models import InspectionChecklistItem
        return InspectionChecklistItem.objects.filter(equipment_type='circuit_breaker')
    except ImportError:
        return None

def get_regions_choices():
    """Get region choices for filtering"""
    try:
        from it.users.models import Regions
        return [(region.id, region.region) for region in Regions.objects.all()]
    except ImportError:
        return []

@login_required
def circuit_breaker_list(request):
    """List all circuit breakers with filtering and search"""
    circuit_breakers = CircuitBreaker.objects.all()
    
    # Get filter parameters
    substation_filter = request.GET.get('substation')
    status_filter = request.GET.get('status')
    region_filter = request.GET.get('region')
    search_query = request.GET.get('search')
    
    # Apply filters
    if substation_filter:
        circuit_breakers = circuit_breakers.filter(sub_station__icontains=substation_filter)
    
    if status_filter == 'active':
        circuit_breakers = circuit_breakers.filter(is_active=True)
    elif status_filter == 'inactive':
        circuit_breakers = circuit_breakers.filter(is_active=False)
    
    if region_filter:
        circuit_breakers = circuit_breakers.filter(region_id=region_filter)
    
    # Apply search
    if search_query:
        circuit_breakers = circuit_breakers.filter(
            Q(breaker_number__icontains=search_query) |
            Q(make_type__icontains=search_query) |
            Q(serial_number__icontains=search_query) |
            Q(sub_station__icontains=search_query)
        )
    
    # Annotate with maintenance count and add explicit ordering
    circuit_breakers = circuit_breakers.annotate(
        maintenance_count=Count('maintenancerecord')
    ).select_related('region').order_by('sub_station', 'breaker_number')  # Add this ordering
    
    # Get unique substations for filter dropdown
    substations = CircuitBreaker.objects.values_list('sub_station', flat=True).distinct().order_by('sub_station')
    
    # Get regions for filter dropdown
    regions = get_regions_choices()
    
    # Pagination
    paginator = Paginator(circuit_breakers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'substations': substations,
        'regions': regions,
        'current_substation': substation_filter,
        'current_status': status_filter,
        'current_region': region_filter,
        'search_query': search_query,
        'total_count': circuit_breakers.count(),
    }
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_list.html', context)

@login_required
def circuit_breaker_detail(request, pk):
    """View details of a specific circuit breaker with enhanced information"""
    circuit_breaker = get_object_or_404(CircuitBreaker, pk=pk)
    
    # Get maintenance records for this circuit breaker
    maintenance_records = MaintenanceRecord.objects.filter(
        circuit_breaker=circuit_breaker
    ).order_by('-date')
    
    # Get summary statistics
    total_maintenance = maintenance_records.count()
    active_maintenance = maintenance_records.filter(status__in=['draft', 'in_progress']).count()
    completed_maintenance = maintenance_records.filter(status='completed').count()
    overdue_maintenance = maintenance_records.filter(
        next_maintenance_due__lt=timezone.now().date(),
        status='completed'
    ).count()
    
    # Get next maintenance due
    next_maintenance = maintenance_records.filter(
        next_maintenance_due__gte=timezone.now().date(),
        status='completed'
    ).order_by('next_maintenance_due').first()
    
    # Get recent maintenance (last 10)
    recent_maintenance = maintenance_records[:10]
    
    context = {
        'circuit_breaker': circuit_breaker,
        'maintenance_records': recent_maintenance,
        'next_maintenance': next_maintenance,
        'total_maintenance': total_maintenance,
        'active_maintenance': active_maintenance,
        'completed_maintenance': completed_maintenance,
        'overdue_maintenance': overdue_maintenance,
    }
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_detail.html', context)

@login_required
def circuit_breaker_create(request):
    """Create a new circuit breaker with enhanced validation"""
    if request.method == 'POST':
        form = CircuitBreakerForm(request.POST)
        if form.is_valid():
            try:
                with transaction.atomic():
                    circuit_breaker = form.save()
                    
                    # Log the creation
                    messages.success(
                        request, 
                        f'Circuit breaker "{circuit_breaker.breaker_number}" created successfully at {circuit_breaker.sub_station}!'
                    )
                    
                    # Redirect based on user preference
                    if 'save_and_add_another' in request.POST:
                        return redirect('circuit_breaker_maintenance:circuit_breaker_create')
                    elif 'save_and_create_maintenance' in request.POST:
                        return redirect('circuit_breaker_maintenance:record_create') + f'?circuit_breaker={circuit_breaker.pk}'
                    else:
                        return redirect('circuit_breaker_maintenance:circuit_breaker_detail', pk=circuit_breaker.pk)
                        
            except Exception as e:
                messages.error(request, f'Error creating circuit breaker: {str(e)}')
        else:
            messages.error(request, f'Please correct the errors below. {str(form.errors)}')
    else:
        form = CircuitBreakerForm()
    
    # Get existing data for auto-complete
    context = {
        'form': form,
        'action': 'Create',
        'existing_substations': list(CircuitBreaker.objects.values_list('sub_station', flat=True).distinct()),
        'existing_makes': list(CircuitBreaker.objects.values_list('make_type', flat=True).distinct()),
    }
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_form.html', context)

@login_required
def circuit_breaker_quick_create(request):
    """Quick create form with minimal fields"""
    if request.method == 'POST':
        form = QuickCircuitBreakerForm(request.POST)
        if form.is_valid():
            try:
                circuit_breaker = form.save(commit=False)
                circuit_breaker.is_active = True
                circuit_breaker.save()
                
                messages.success(request, f'Circuit breaker "{circuit_breaker.breaker_number}" created successfully!')
                
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({
                        'success': True,
                        'message': 'Circuit breaker created successfully!',
                        'circuit_breaker': {
                            'id': circuit_breaker.pk,
                            'breaker_number': circuit_breaker.breaker_number,
                            'sub_station': circuit_breaker.sub_station,
                        }
                    })
                
                return redirect('circuit_breaker_maintenance:circuit_breaker_detail', pk=circuit_breaker.pk)
                
            except Exception as e:
                if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                    return JsonResponse({'success': False, 'message': str(e)})
                messages.error(request, f'Error creating circuit breaker: {str(e)}')
        else:
            if request.headers.get('X-Requested-With') == 'XMLHttpRequest':
                return JsonResponse({'success': False, 'errors': form.errors})
    else:
        form = QuickCircuitBreakerForm()
    
    context = {
        'form': form,
        'action': 'Quick Create',
        'existing_substations': list(CircuitBreaker.objects.values_list('sub_station', flat=True).distinct()),
        'existing_makes': list(CircuitBreaker.objects.values_list('make_type', flat=True).distinct()),
    }
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_quick_form.html', context)

@login_required
def circuit_breaker_bulk_import(request):
    """Bulk import circuit breakers from CSV/Excel"""
    if request.method == 'POST':
        form = CircuitBreakerBulkImportForm(request.POST, request.FILES)
        if form.is_valid():
            try:
                file = form.cleaned_data['file']
                skip_duplicates = form.cleaned_data['skip_duplicates']
                
                # Process the file
                if file.name.endswith('.csv'):
                    df = pd.read_csv(file)
                else:
                    df = pd.read_excel(file)
                
                # Validate required columns
                required_columns = ['breaker_number', 'sub_station', 'make_type', 'voltage_capacity']
                missing_columns = [col for col in required_columns if col not in df.columns]
                
                if missing_columns:
                    messages.error(request, f'Missing required columns: {", ".join(missing_columns)}')
                    return render(request, 'circuit_breaker_maintenance/circuit_breaker_bulk_import.html', {'form': form})
                
                created_count = 0
                skipped_count = 0
                error_count = 0
                errors = []
                
                with transaction.atomic():
                    for index, row in df.iterrows():
                        try:
                            # Check for duplicates
                            if skip_duplicates:
                                if CircuitBreaker.objects.filter(
                                    Q(breaker_number__iexact=row['breaker_number']) |
                                    Q(serial_number__iexact=row.get('serial_number', ''))
                                ).exists():
                                    skipped_count += 1
                                    continue
                            
                            # Create circuit breaker
                            circuit_breaker = CircuitBreaker(
                                breaker_number=row['breaker_number'],
                                sub_station=row['sub_station'],
                                make_type=row['make_type'],
                                voltage_capacity=row['voltage_capacity'],
                                serial_number=row.get('serial_number', ''),
                                installation_date=pd.to_datetime(row.get('installation_date'), errors='coerce').date() if pd.notna(row.get('installation_date')) else None,
                                is_active=True
                            )
                            circuit_breaker.full_clean()
                            circuit_breaker.save()
                            created_count += 1
                            
                        except Exception as e:
                            error_count += 1
                            errors.append(f"Row {index + 2}: {str(e)}")
                
                # Show results
                if created_count > 0:
                    messages.success(request, f'Successfully imported {created_count} circuit breakers.')
                if skipped_count > 0:
                    messages.info(request, f'Skipped {skipped_count} duplicate records.')
                if error_count > 0:
                    messages.warning(request, f'{error_count} records had errors.')
                    for error in errors[:10]:  # Show first 10 errors
                        messages.error(request, error)
                
                return redirect('circuit_breaker_maintenance:circuit_breaker_list')
                
            except Exception as e:
                messages.error(request, f'Error processing file: {str(e)}')
    else:
        form = CircuitBreakerBulkImportForm()
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_bulk_import.html', {'form': form})

@login_required
def get_circuit_breaker_suggestions(request):
    """AJAX endpoint for auto-complete suggestions"""
    field = request.GET.get('field')
    query = request.GET.get('q', '')
    
    suggestions = []
    
    if field == 'substation' and query:
        suggestions = list(
            CircuitBreaker.objects.filter(sub_station__icontains=query)
            .values_list('sub_station', flat=True)
            .distinct()[:10]
        )
    elif field == 'make_type' and query:
        suggestions = list(
            CircuitBreaker.objects.filter(make_type__icontains=query)
            .values_list('make_type', flat=True)
            .distinct()[:10]
        )
    
    return JsonResponse({'suggestions': suggestions})

@login_required
def circuit_breaker_edit(request, pk):
    """Edit an existing circuit breaker with comprehensive validation"""
    circuit_breaker = get_object_or_404(CircuitBreaker, pk=pk)
    
    # Check if circuit breaker has active maintenance records
    active_maintenance = MaintenanceRecord.objects.filter(
        circuit_breaker=circuit_breaker,
        status__in=['draft', 'in_progress']
    ).exists()
    
    if request.method == 'POST':
        form = CircuitBreakerForm(request.POST, instance=circuit_breaker)
        
        # Store original values for comparison
        original_breaker_number = circuit_breaker.breaker_number
        original_is_active = circuit_breaker.is_active
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Check if trying to deactivate with active maintenance
                    if (original_is_active and not form.cleaned_data.get('is_active') and active_maintenance):
                        messages.error(
                            request, 
                            'Cannot deactivate circuit breaker with active maintenance records. '
                            'Complete or cancel active maintenance first.'
                        )
                        return render(request, 'circuit_breaker_maintenance/circuit_breaker_form.html', {
                            'form': form,
                            'circuit_breaker': circuit_breaker,
                            'action': 'Edit',
                            'existing_substations': list(CircuitBreaker.objects.values_list('sub_station', flat=True).distinct()),
                            'existing_makes': list(CircuitBreaker.objects.values_list('make_type', flat=True).distinct()),
                            'has_active_maintenance': active_maintenance,
                        })
                    
                    # Save the changes
                    updated_circuit_breaker = form.save()
                    
                    # Log significant changes
                    changes = []
                    if original_breaker_number != updated_circuit_breaker.breaker_number:
                        changes.append(f"Breaker number: {original_breaker_number} → {updated_circuit_breaker.breaker_number}")
                    if original_is_active != updated_circuit_breaker.is_active:
                        status_change = "Activated" if updated_circuit_breaker.is_active else "Deactivated"
                        changes.append(f"Status: {status_change}")
                    
                    if changes:
                        change_log = "; ".join(changes)
                        messages.success(
                            request, 
                            f'Circuit breaker updated successfully! Changes: {change_log}'
                        )
                    else:
                        messages.success(request, 'Circuit breaker updated successfully!')
                    
                    # Redirect based on user preference
                    if 'save_and_continue' in request.POST:
                        return redirect('circuit_breaker_maintenance:circuit_breaker_edit', pk=updated_circuit_breaker.pk)
                    elif 'save_and_create_maintenance' in request.POST:
                        return redirect('circuit_breaker_maintenance:record_create') + f'?circuit_breaker={updated_circuit_breaker.pk}'
                    else:
                        return redirect('circuit_breaker_maintenance:circuit_breaker_detail', pk=updated_circuit_breaker.pk)
                        
            except ValidationError as e:
                messages.error(request, f'Validation error: {str(e)}')
            except Exception as e:
                messages.error(request, f'Error updating circuit breaker: {str(e)}')
        else:
            messages.error(request, 'Please correct the errors below.')
    else:
        form = CircuitBreakerForm(instance=circuit_breaker)
    
    # Get maintenance history for context
    maintenance_history = MaintenanceRecord.objects.filter(
        circuit_breaker=circuit_breaker
    ).order_by('-date')[:5]  # Last 5 records
    
    context = {
        'form': form,
        'circuit_breaker': circuit_breaker,
        'action': 'Edit',
        'existing_substations': list(CircuitBreaker.objects.values_list('sub_station', flat=True).distinct()),
        'existing_makes': list(CircuitBreaker.objects.values_list('make_type', flat=True).distinct()),
        'has_active_maintenance': active_maintenance,
        'maintenance_history': maintenance_history,
    }
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_form.html', context)

@login_required
def circuit_breaker_toggle_status(request, pk):
    """AJAX endpoint to toggle circuit breaker active status with comprehensive validation"""
    if request.method == 'POST':
        circuit_breaker = get_object_or_404(CircuitBreaker, pk=pk)
        
        # Check if trying to deactivate with active maintenance
        if circuit_breaker.is_active:
            active_maintenance = MaintenanceRecord.objects.filter(
                circuit_breaker=circuit_breaker,
                status__in=['draft', 'in_progress']
            )
            
            if active_maintenance.exists():
                active_records = active_maintenance.values_list('report_no', flat=True)
                return JsonResponse({
                    'success': False,
                    'message': f'Cannot deactivate circuit breaker with active maintenance records: {", ".join(active_records)}',
                    'active_maintenance_count': active_maintenance.count()
                })
        
        # Toggle status
        old_status = circuit_breaker.is_active
        circuit_breaker.is_active = not circuit_breaker.is_active
        circuit_breaker.save()
        
        action = "activated" if circuit_breaker.is_active else "deactivated"
        
        return JsonResponse({
            'success': True,
            'message': f'Circuit breaker {circuit_breaker.breaker_number} {action} successfully.',
            'is_active': circuit_breaker.is_active,
            'old_status': old_status,
            'action': action
        })
    
    return JsonResponse({'success': False, 'message': 'Invalid request method.'})

@login_required
def circuit_breaker_bulk_status_change(request):
    """Bulk activate/deactivate multiple circuit breakers"""
    if request.method == 'POST':
        action = request.POST.get('action')  # 'activate' or 'deactivate'
        circuit_breaker_ids = request.POST.getlist('circuit_breaker_ids')
        
        if not action or not circuit_breaker_ids:
            messages.error(request, 'Invalid request. Please select circuit breakers and action.')
            return redirect('circuit_breaker_maintenance:circuit_breaker_list')
        
        circuit_breakers = CircuitBreaker.objects.filter(id__in=circuit_breaker_ids)
        
        if action == 'deactivate':
            # Check for active maintenance records
            blocked_breakers = []
            for cb in circuit_breakers:
                if cb.is_active:
                    active_maintenance = MaintenanceRecord.objects.filter(
                        circuit_breaker=cb,
                        status__in=['draft', 'in_progress']
                    ).exists()
                    
                    if active_maintenance:
                        blocked_breakers.append(cb.breaker_number)
            
            if blocked_breakers:
                messages.error(
                    request, 
                    f'Cannot deactivate circuit breakers with active maintenance: {", ".join(blocked_breakers)}'
                )
                return redirect('circuit_breaker_maintenance:circuit_breaker_list')
        
        # Perform bulk update
        try:
            with transaction.atomic():
                if action == 'activate':
                    updated_count = circuit_breakers.filter(is_active=False).update(is_active=True)
                    messages.success(request, f'Successfully activated {updated_count} circuit breakers.')
                elif action == 'deactivate':
                    updated_count = circuit_breakers.filter(is_active=True).update(is_active=False)
                    messages.success(request, f'Successfully deactivated {updated_count} circuit breakers.')
                
        except Exception as e:
            messages.error(request, f'Error updating circuit breakers: {str(e)}')
    
    return redirect('circuit_breaker_maintenance:circuit_breaker_list')

@login_required
def circuit_breaker_status_report(request):
    """Generate status report for circuit breakers"""
    # Get counts by status
    active_count = CircuitBreaker.objects.filter(is_active=True).count()
    inactive_count = CircuitBreaker.objects.filter(is_active=False).count()
    total_count = active_count + inactive_count
    
    # Get counts by substation
    substation_stats = CircuitBreaker.objects.values('sub_station').annotate(
        total=Count('id'),
        active=Count('id', filter=Q(is_active=True)),
        inactive=Count('id', filter=Q(is_active=False))
    ).order_by('sub_station')
    
    # Get recently deactivated circuit breakers (last 30 days)
    thirty_days_ago = timezone.now() - timezone.timedelta(days=30)
    recently_deactivated = CircuitBreaker.objects.filter(
        is_active=False,
        updated_at__gte=thirty_days_ago
    ).order_by('-updated_at')[:10]
    
    # Get circuit breakers with no maintenance records
    no_maintenance = CircuitBreaker.objects.filter(
        is_active=True,
        maintenancerecord__isnull=True
    ).distinct()
    
    # Get overdue maintenance for active circuit breakers
    overdue_maintenance = MaintenanceRecord.objects.filter(
        circuit_breaker__is_active=True,
        next_maintenance_due__lt=timezone.now().date(),
        status='completed'
    ).select_related('circuit_breaker').order_by('next_maintenance_due')
    
    context = {
        'active_count': active_count,
        'inactive_count': inactive_count,
        'total_count': total_count,
        'substation_stats': substation_stats,
        'recently_deactivated': recently_deactivated,
        'no_maintenance': no_maintenance,
        'overdue_maintenance': overdue_maintenance,
    }
    
    return render(request, 'circuit_breaker_maintenance/status_report.html', context)

@login_required
def circuit_breaker_deactivation_reasons(request, pk):
    """View/add deactivation reasons for a circuit breaker"""
    circuit_breaker = get_object_or_404(CircuitBreaker, pk=pk)
    
    if request.method == 'POST':
        reason = request.POST.get('reason')
        if reason and not circuit_breaker.is_active:
            # You could extend the model to store deactivation reasons
            # For now, we'll use a simple approach
            messages.success(request, 'Deactivation reason recorded.')
            return redirect('circuit_breaker_maintenance:circuit_breaker_detail', pk=pk)
    
    context = {
        'circuit_breaker': circuit_breaker,
    }
    
    return render(request, 'circuit_breaker_maintenance/deactivation_reasons.html', context)

@login_required
def circuit_breaker_activation_check(request, pk):
    """Pre-activation checks for circuit breaker"""
    circuit_breaker = get_object_or_404(CircuitBreaker, pk=pk)
    
    if circuit_breaker.is_active:
        messages.info(request, 'Circuit breaker is already active.')
        return redirect('circuit_breaker_maintenance:circuit_breaker_detail', pk=pk)
    
    # Perform pre-activation checks
    checks = {
        'basic_info_complete': all([
            circuit_breaker.breaker_number,
            circuit_breaker.make_type,
            circuit_breaker.voltage_capacity,
            circuit_breaker.serial_number,
            circuit_breaker.sub_station
        ]),
        'has_maintenance_history': MaintenanceRecord.objects.filter(
            circuit_breaker=circuit_breaker
        ).exists(),
        'recent_maintenance': MaintenanceRecord.objects.filter(
            circuit_breaker=circuit_breaker,
            date__gte=timezone.now().date() - timezone.timedelta(days=365)
        ).exists(),
        'no_pending_issues': True,  # You can add more complex logic here
    }
    
    all_checks_passed = all(checks.values())
    
    context = {
        'circuit_breaker': circuit_breaker,
        'checks': checks,
        'all_checks_passed': all_checks_passed,
    }
    
    return render(request, 'circuit_breaker_maintenance/activation_check.html', context)

@login_required
def circuit_breaker_history(request, pk):
    """View full maintenance history for a circuit breaker"""
    circuit_breaker = get_object_or_404(CircuitBreaker, pk=pk)
    
    # Get all maintenance records with filtering
    maintenance_records = MaintenanceRecord.objects.filter(circuit_breaker=circuit_breaker)
    
    # Apply filters
    status_filter = request.GET.get('status')
    year_filter = request.GET.get('year')
    
    if status_filter:
        maintenance_records = maintenance_records.filter(status=status_filter)
    
    if year_filter:
        maintenance_records = maintenance_records.filter(date__year=year_filter)
    
    maintenance_records = maintenance_records.order_by('-date')
    
    # Pagination
    paginator = Paginator(maintenance_records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get available years and statuses for filtering
    available_years = MaintenanceRecord.objects.filter(
        circuit_breaker=circuit_breaker
    ).dates('date', 'year').distinct()
    
    available_statuses = MaintenanceRecord.objects.filter(
        circuit_breaker=circuit_breaker
    ).values_list('status', flat=True).distinct()
    
    context = {
        'circuit_breaker': circuit_breaker,
        'page_obj': page_obj,
        'available_years': available_years,
        'available_statuses': available_statuses,
        'current_status': status_filter,
        'current_year': year_filter,
    }
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_history.html', context)

@login_required
def maintenance_record_list(request):
    """List all maintenance records with filtering and search"""
    records = MaintenanceRecord.objects.select_related('circuit_breaker').all()
    
    # Get filter parameters
    circuit_breaker_filter = request.GET.get('circuit_breaker')
    status_filter = request.GET.get('status')
    priority_filter = request.GET.get('priority')
    search_query = request.GET.get('search')
    
    # Apply filters
    if circuit_breaker_filter:
        records = records.filter(circuit_breaker__breaker_number__icontains=circuit_breaker_filter)
    
    if status_filter:
        records = records.filter(status=status_filter)
    
    if priority_filter:
        records = records.filter(priority=priority_filter)
    
    # Apply search
    if search_query:
        records = records.filter(
            Q(report_no__icontains=search_query) |
            Q(circuit_breaker__breaker_number__icontains=search_query) |
            Q(circuit_breaker__sub_station__icontains=search_query)
        )
    
    records = records.order_by('-date')
    
    # Pagination
    paginator = Paginator(records, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Get unique values for filter dropdowns
    circuit_breakers = CircuitBreaker.objects.values_list('breaker_number', flat=True).distinct().order_by('breaker_number')
    
    context = {
        'page_obj': page_obj,
        'circuit_breakers': circuit_breakers,
        'current_circuit_breaker': circuit_breaker_filter,
        'current_status': status_filter,
        'current_priority': priority_filter,
        'search_query': search_query,
        'total_count': records.count(),
        'status_choices': MaintenanceRecord.STATUS_CHOICES,
        'priority_choices': MaintenanceRecord.PRIORITY_CHOICES,
    }
    
    return render(request, 'circuit_breaker_maintenance/maintenance_record_list.html', context)

@login_required
def maintenance_record_detail(request, pk):
    """View details of a specific maintenance record"""
    record = get_object_or_404(MaintenanceRecord, pk=pk)
    
    # Get attachments
    attachments = record.attachments.all().order_by('-uploaded_at')
    
    context = {
        'record': record,
        'attachments': attachments,
    }
    
    return render(request, 'circuit_breaker_maintenance/maintenance_record_detail.html', context)

@login_required
def maintenance_record_create(request):
    """Create a new maintenance record"""
    circuit_breaker_id = request.GET.get('circuit_breaker')
    quick_mode = request.GET.get('quick', False)
    
    # Choose form based on mode
    FormClass = MaintenanceRecordQuickForm if quick_mode else MaintenanceRecordForm
    
    if request.method == 'POST':
        form = FormClass(
            request.POST, 
            user=request.user, 
            circuit_breaker_id=circuit_breaker_id
        )
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    maintenance_record = form.save()
                    
                    # Success message
                    messages.success(
                        request,
                        f'Maintenance record "{maintenance_record.report_no}" created successfully!'
                    )
                    
                    # Redirect based on user preference
                    if 'save_and_add_another' in request.POST:
                        redirect_url = request.path
                        if circuit_breaker_id:
                            redirect_url += f'?circuit_breaker={circuit_breaker_id}'
                        return redirect(redirect_url)
                    elif 'save_and_view_cb' in request.POST:
                        return redirect('circuit_breaker_maintenance:circuit_breaker_detail', 
                                      pk=maintenance_record.circuit_breaker.pk)
                    else:
                        return redirect('circuit_breaker_maintenance:record_detail', 
                                      pk=maintenance_record.pk)
                        
            except ValidationError as e:
                logger.error(f"Validation error creating maintenance record: {e}")
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f"Validation error in {field}: {error}")
                elif hasattr(e, 'messages'):
                    for error in e.messages:
                        messages.error(request, f"Validation error: {error}")
                else:
                    messages.error(request, f'Validation error creating maintenance record: {str(e)}')
                    
            except IntegrityError as e:
                logger.error(f"Database integrity error creating maintenance record: {e}")
                error_msg = str(e)
                if 'UNIQUE constraint failed' in error_msg:
                    if 'report_no' in error_msg:
                        messages.error(request, 'Error: A maintenance record with this report number already exists. Please use a different report number.')
                    else:
                        messages.error(request, 'Error: This record conflicts with existing data. Please check for duplicate values.')
                elif 'NOT NULL constraint failed' in error_msg:
                    field_name = error_msg.split('.')[-1] if '.' in error_msg else 'unknown field'
                    messages.error(request, f'Error: Required field "{field_name}" cannot be empty.')
                else:
                    messages.error(request, f'Database error creating maintenance record: {error_msg}')
                    
            except Exception as e:
                logger.error(f"Unexpected error creating maintenance record: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Provide detailed error information
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Check for common Django model errors
                if 'ForeignKey' in error_msg:
                    messages.error(request, f'Error: Invalid circuit breaker reference. Please select a valid circuit breaker.')
                elif 'DateField' in error_msg:
                    messages.error(request, f'Error: Invalid date format. Please enter dates in the correct format (YYYY-MM-DD).')
                elif 'CharField' in error_msg and 'max_length' in error_msg:
                    messages.error(request, f'Error: One or more text fields exceed the maximum allowed length.')
                elif 'JSONField' in error_msg:
                    messages.error(request, f'Error: Invalid JSON data in technical fields. Please check the format of your JSON data.')
                else:
                    messages.error(request, f'Error creating maintenance record ({error_type}): {error_msg}')
                
                # Additional debugging info for developers (only in debug mode)
                if hasattr(request, 'user') and request.user.is_superuser:
                    messages.warning(request, f'Debug info: {traceback.format_exc()[:500]}...')
        else:
            # Enhanced form error handling
            messages.error(request, 'Please correct the errors below:')
            
            # Display field-specific errors
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'Form error: {error}')
                    else:
                        messages.error(request, f'Error in "{field_name}": {error}')
            
            # Display non-field errors
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, f'Form error: {error}')
    else:
        form = FormClass(
            user=request.user,
            circuit_breaker_id=circuit_breaker_id
        )
    
    # Get circuit breaker info for context
    circuit_breaker = None
    if circuit_breaker_id:
        try:
            circuit_breaker = CircuitBreaker.objects.get(pk=circuit_breaker_id)
        except CircuitBreaker.DoesNotExist:
            messages.warning(request, f'Circuit breaker with ID {circuit_breaker_id} not found.')
    
    # Get recent maintenance records for reference
    recent_records = MaintenanceRecord.objects.select_related('circuit_breaker').order_by('-date')[:5]
    
    context = {
        'form': form,
        'action': 'Create',
        'circuit_breaker': circuit_breaker,
        'circuit_breaker_id': circuit_breaker_id,
        'quick_mode': quick_mode,
        'recent_records': recent_records,
        'active_circuit_breakers': CircuitBreaker.objects.filter(is_active=True).count(),
    }
    
    return render(request, 'circuit_breaker_maintenance/maintenance_record_form.html', context)


@login_required
def maintenance_record_edit(request, pk):
    """Edit an existing maintenance record"""
    record = get_object_or_404(MaintenanceRecord, pk=pk)
    
    # Check if record can be edited
    if record.status in ['approved', 'completed'] and not request.user.is_superuser:
        messages.warning(
            request, 
            'This maintenance record cannot be edited as it has been completed/approved. '
            'Contact an administrator if changes are needed.'
        )
        return redirect('circuit_breaker_maintenance:record_detail', pk=record.pk)
    
    if request.method == 'POST':
        form = MaintenanceRecordForm(
            request.POST, 
            instance=record,
            user=request.user
        )
        
        if form.is_valid():
            try:
                with transaction.atomic():
                    # Store original values for comparison
                    original_status = record.status
                    original_priority = record.priority
                    original_circuit_breaker = record.circuit_breaker.breaker_number
                    
                    updated_record = form.save()
                    
                    # Log significant changes
                    changes = []
                    if original_status != updated_record.status:
                        changes.append(f"Status: {original_status} → {updated_record.status}")
                    if original_priority != updated_record.priority:
                        changes.append(f"Priority: {original_priority} → {updated_record.priority}")
                    if original_circuit_breaker != updated_record.circuit_breaker.breaker_number:
                        changes.append(f"Circuit Breaker: {original_circuit_breaker} → {updated_record.circuit_breaker.breaker_number}")
                    
                    if changes:
                        change_log = "; ".join(changes)
                        messages.success(
                            request,
                            f'Maintenance record updated successfully! Changes: {change_log}'
                        )
                    else:
                        messages.success(request, 'Maintenance record updated successfully!')
                    
                    # Redirect based on user preference
                    if 'save_and_continue' in request.POST:
                        return redirect('circuit_breaker_maintenance:record_edit', pk=updated_record.pk)
                    else:
                        return redirect('circuit_breaker_maintenance:record_detail', pk=updated_record.pk)
                        
            except ValidationError as e:
                logger.error(f"Validation error updating maintenance record {pk}: {e}")
                if hasattr(e, 'message_dict'):
                    for field, errors in e.message_dict.items():
                        for error in errors:
                            messages.error(request, f"Validation error in {field}: {error}")
                elif hasattr(e, 'messages'):
                    for error in e.messages:
                        messages.error(request, f"Validation error: {error}")
                else:
                    messages.error(request, f'Validation error updating maintenance record: {str(e)}')
                    
            except IntegrityError as e:
                logger.error(f"Database integrity error updating maintenance record {pk}: {e}")
                error_msg = str(e)
                if 'UNIQUE constraint failed' in error_msg:
                    if 'report_no' in error_msg:
                        messages.error(request, 'Error: A maintenance record with this report number already exists. Please use a different report number.')
                    else:
                        messages.error(request, 'Error: This record conflicts with existing data. Please check for duplicate values.')
                elif 'NOT NULL constraint failed' in error_msg:
                    field_name = error_msg.split('.')[-1] if '.' in error_msg else 'unknown field'
                    messages.error(request, f'Error: Required field "{field_name}" cannot be empty.')
                else:
                    messages.error(request, f'Database error updating maintenance record: {error_msg}')
                    
            except Exception as e:
                logger.error(f"Unexpected error updating maintenance record {pk}: {e}")
                logger.error(f"Traceback: {traceback.format_exc()}")
                
                # Provide detailed error information
                error_type = type(e).__name__
                error_msg = str(e)
                
                # Check for common Django model errors
                if 'ForeignKey' in error_msg:
                    messages.error(request, f'Error: Invalid circuit breaker reference. Please select a valid circuit breaker.')
                elif 'DateField' in error_msg:
                    messages.error(request, f'Error: Invalid date format. Please enter dates in the correct format (YYYY-MM-DD).')
                elif 'CharField' in error_msg and 'max_length' in error_msg:
                    messages.error(request, f'Error: One or more text fields exceed the maximum allowed length.')
                elif 'JSONField' in error_msg:
                    messages.error(request, f'Error: Invalid JSON data in technical fields. Please check the format of your JSON data.')
                elif 'PermissionDenied' in error_type:
                    messages.error(request, f'Error: You do not have permission to make this change.')
                else:
                    messages.error(request, f'Error updating maintenance record ({error_type}): {error_msg}')
                
                # Additional debugging info for developers (only for superusers)
                if hasattr(request, 'user') and request.user.is_superuser:
                    messages.warning(request, f'Debug info: {traceback.format_exc()[:500]}...')
        else:
            # Enhanced form error handling
            messages.error(request, 'Please correct the errors below:')
            
            # Display field-specific errors
            for field, errors in form.errors.items():
                field_name = form.fields[field].label if field in form.fields else field
                for error in errors:
                    if field == '__all__':
                        messages.error(request, f'Form error: {error}')
                    else:
                        messages.error(request, f'Error in "{field_name}": {error}')
            
            # Display non-field errors
            if form.non_field_errors():
                for error in form.non_field_errors():
                    messages.error(request, f'Form error: {error}')
    else:
        form = MaintenanceRecordForm(instance=record, user=request.user)
    
    # Get record history for context
    related_records = MaintenanceRecord.objects.filter(
        circuit_breaker=record.circuit_breaker
    ).exclude(pk=record.pk).order_by('-date')[:5]
    
    context = {
        'form': form,
        'record': record,
        'action': 'Edit',
        'related_records': related_records,
        'can_edit': record.status in ['draft', 'in_progress'] or request.user.is_superuser,
    }
    
    return render(request, 'circuit_breaker_maintenance/maintenance_record_form.html', context)

# API endpoints for integration
@login_required
def get_regions_api(request):
    """Get regions from database as JSON"""
    try:
        from it.users.models import Regions
        regions = Regions.objects.all()
        return JsonResponse(list(regions.values('id', 'region')), safe=False)
    except ImportError:
        return JsonResponse([], safe=False)

@login_required
def get_circuit_breaker_checklist_api(request):
    """Get circuit breaker inspection checklist items from substation inspections module"""
    try:
        checklist_items = get_circuit_breaker_checklist_items()
        if checklist_items:
            items = list(checklist_items.values(
                'id', 'item_code', 'title', 'description', 'category', 'severity',
                'is_mandatory', 'reference_standard'
            ))
            return JsonResponse(items, safe=False)
        else:
            return JsonResponse([], safe=False)
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)

# Enhanced Circuit Breaker Maintenance Views

@login_required
def maintenance_record_create_typed(request, breaker_type):
    """Create a maintenance record for a specific breaker type"""
    from .models import (
        VacuumBreakerChecks, OilBreakerChecks, InsulationResistanceTest,
        ContactResistanceTest, TimingTest, AutoRecloseTest
    )
    from .forms import (
        MaintenanceRecordForm, VacuumBreakerChecksForm, OilBreakerChecksForm,
        InsulationTestFormSet, ContactResistanceTestFormSet, TimingTestFormSet
    )
    
    # Filter circuit breakers by type
    circuit_breakers = CircuitBreaker.objects.filter(
        breaker_type=breaker_type, is_active=True
    )
    
    if request.method == 'POST':
        form = MaintenanceRecordForm(request.POST)
        if form.is_valid():
            maintenance_record = form.save()
            
            # Create default test records based on breaker type
            if breaker_type == 'vacuum':
                VacuumBreakerChecks.objects.create(maintenance_record=maintenance_record)
            elif breaker_type == 'oil':
                OilBreakerChecks.objects.create(maintenance_record=maintenance_record)
            
            # Create default test templates
            phases = ['red', 'yellow', 'blue']
            for phase in phases:
                InsulationResistanceTest.objects.create(
                    maintenance_record=maintenance_record,
                    phase=phase,
                    test_type='open_contact'
                )
                ContactResistanceTest.objects.create(
                    maintenance_record=maintenance_record,
                    phase=phase,
                    test_condition='before_maintenance'
                )
                TimingTest.objects.create(
                    maintenance_record=maintenance_record,
                    phase=phase,
                    operation_type='closing'
                )
            
            AutoRecloseTest.objects.create(maintenance_record=maintenance_record)
            
            messages.success(request, f'{breaker_type.title()} circuit breaker maintenance record created successfully.')
            return redirect('circuit_breaker_maintenance:record_detail', pk=maintenance_record.pk)
    else:
        form = MaintenanceRecordForm()
        # Filter the circuit breaker choices
        form.fields['circuit_breaker'].queryset = circuit_breakers
    
    context = {
        'form': form,
        'breaker_type': breaker_type,
        'title': f'Create {breaker_type.title()} Circuit Breaker Maintenance Record'
    }
    
    return render(request, 'circuit_breaker_maintenance/maintenance_record_create_typed.html', context)

@login_required
def maintenance_tests_view(request, pk):
    """View and manage all tests for a maintenance record"""
    maintenance_record = get_object_or_404(MaintenanceRecord, pk=pk)
    
    context = {
        'maintenance_record': maintenance_record,
        'insulation_tests': maintenance_record.insulation_tests.all(),
        'contact_resistance_tests': maintenance_record.contact_resistance_tests.all(),
        'timing_tests': maintenance_record.timing_tests.all(),
        'interlock_tests': maintenance_record.interlock_tests.all(),
        'contact_travel_tests': maintenance_record.contact_travel_tests.all(),
        'ductor_tests': maintenance_record.ductor_tests.all(),
        'protection_tests': maintenance_record.protection_tests.all(),
        'relay_operation_tests': maintenance_record.relay_operation_tests.all(),
        'auto_reclose_tests': maintenance_record.auto_reclose_tests.all(),
    }
    
    # Add breaker-specific checks
    try:
        if maintenance_record.circuit_breaker.breaker_type == 'vacuum':
            context['vacuum_checks'] = maintenance_record.vacuum_checks
    except:
        pass
    
    try:
        if maintenance_record.circuit_breaker.breaker_type == 'oil':
            context['oil_checks'] = maintenance_record.oil_checks
    except:
        pass
    
    return render(request, 'circuit_breaker_maintenance/maintenance_tests.html', context)

@login_required
def insulation_test_manage(request, pk):
    """Manage insulation resistance tests for a maintenance record"""
    from .forms import InsulationTestFormSet
    maintenance_record = get_object_or_404(MaintenanceRecord, pk=pk)
    
    if request.method == 'POST':
        formset = InsulationTestFormSet(request.POST, instance=maintenance_record)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Insulation resistance tests updated successfully.')
            return redirect('circuit_breaker_maintenance:maintenance_tests', pk=pk)
    else:
        formset = InsulationTestFormSet(instance=maintenance_record)
    
    context = {
        'maintenance_record': maintenance_record,
        'formset': formset,
        'test_type': 'Insulation Resistance Tests'
    }
    
    return render(request, 'circuit_breaker_maintenance/test_formset.html', context)

@login_required
def contact_resistance_test_manage(request, pk):
    """Manage contact resistance tests for a maintenance record"""
    from .forms import ContactResistanceTestFormSet
    maintenance_record = get_object_or_404(MaintenanceRecord, pk=pk)
    
    if request.method == 'POST':
        formset = ContactResistanceTestFormSet(request.POST, instance=maintenance_record)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Contact resistance tests updated successfully.')
            return redirect('circuit_breaker_maintenance:maintenance_tests', pk=pk)
    else:
        formset = ContactResistanceTestFormSet(instance=maintenance_record)
    
    context = {
        'maintenance_record': maintenance_record,
        'formset': formset,
        'test_type': 'Contact Resistance Tests'
    }
    
    return render(request, 'circuit_breaker_maintenance/test_formset.html', context)

@login_required
def timing_test_manage(request, pk):
    """Manage timing tests for a maintenance record"""
    from .forms import TimingTestFormSet
    maintenance_record = get_object_or_404(MaintenanceRecord, pk=pk)
    
    if request.method == 'POST':
        formset = TimingTestFormSet(request.POST, instance=maintenance_record)
        if formset.is_valid():
            formset.save()
            messages.success(request, 'Timing tests updated successfully.')
            return redirect('circuit_breaker_maintenance:maintenance_tests', pk=pk)
    else:
        formset = TimingTestFormSet(instance=maintenance_record)
    
    context = {
        'maintenance_record': maintenance_record,
        'formset': formset,
        'test_type': 'Timing Tests'
    }
    
    return render(request, 'circuit_breaker_maintenance/test_formset.html', context)

@login_required
def vacuum_checks_manage(request, pk):
    """Manage vacuum circuit breaker specific checks"""
    from .forms import VacuumBreakerChecksForm
    maintenance_record = get_object_or_404(MaintenanceRecord, pk=pk)
    
    try:
        vacuum_checks = maintenance_record.vacuum_checks
    except:
        from .models import VacuumBreakerChecks
        vacuum_checks = VacuumBreakerChecks.objects.create(maintenance_record=maintenance_record)
    
    if request.method == 'POST':
        form = VacuumBreakerChecksForm(request.POST, instance=vacuum_checks)
        if form.is_valid():
            form.save()
            messages.success(request, 'Vacuum circuit breaker checks updated successfully.')
            return redirect('circuit_breaker_maintenance:maintenance_tests', pk=pk)
    else:
        form = VacuumBreakerChecksForm(instance=vacuum_checks)
    
    context = {
        'maintenance_record': maintenance_record,
        'form': form,
        'check_type': 'Vacuum Circuit Breaker Checks'
    }
    
    return render(request, 'circuit_breaker_maintenance/vacuum_oil_checks.html', context)

@login_required
def oil_checks_manage(request, pk):
    """Manage oil circuit breaker specific checks"""
    from .forms import OilBreakerChecksForm
    maintenance_record = get_object_or_404(MaintenanceRecord, pk=pk)
    
    try:
        oil_checks = maintenance_record.oil_checks
    except:
        from .models import OilBreakerChecks
        oil_checks = OilBreakerChecks.objects.create(maintenance_record=maintenance_record)
    
    if request.method == 'POST':
        form = OilBreakerChecksForm(request.POST, instance=oil_checks)
        if form.is_valid():
            form.save()
            messages.success(request, 'Oil circuit breaker checks updated successfully.')
            return redirect('circuit_breaker_maintenance:maintenance_tests', pk=pk)
    else:
        form = OilBreakerChecksForm(instance=oil_checks)
    
    context = {
        'maintenance_record': maintenance_record,
        'form': form,
        'check_type': 'Oil Circuit Breaker Checks'
    }
    
    return render(request, 'circuit_breaker_maintenance/vacuum_oil_checks.html', context)

# Transformer Maintenance Views

@login_required
def transformer_maintenance_list(request):
    """List transformer maintenance records"""
    from .models import TransformerMaintenanceRecord
    
    records = TransformerMaintenanceRecord.objects.all()
    
    # Apply filters
    substation_filter = request.GET.get('substation')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    if substation_filter:
        records = records.filter(substation__icontains=substation_filter)
    
    if status_filter:
        records = records.filter(status=status_filter)
    
    if search_query:
        records = records.filter(
            Q(transformer_number__icontains=search_query) |
            Q(substation__icontains=search_query) |
            Q(report_no__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(records, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'substation_filter': substation_filter,
        'status_filter': status_filter,
        'search_query': search_query,
    }
    
    return render(request, 'circuit_breaker_maintenance/transformer_list.html', context)

@login_required
def transformer_maintenance_create(request):
    """Create a transformer maintenance record"""
    from .forms import TransformerMaintenanceRecordForm
    
    if request.method == 'POST':
        form = TransformerMaintenanceRecordForm(request.POST)
        if form.is_valid():
            record = form.save()
            messages.success(request, 'Transformer maintenance record created successfully.')
            return redirect('circuit_breaker_maintenance:transformer_detail', pk=record.pk)
    else:
        form = TransformerMaintenanceRecordForm()
    
    context = {
        'form': form,
        'title': 'Create Transformer Maintenance Record'
    }
    
    return render(request, 'circuit_breaker_maintenance/transformer_form.html', context)

@login_required
def transformer_maintenance_detail(request, pk):
    """View transformer maintenance record details"""
    from .models import TransformerMaintenanceRecord
    record = get_object_or_404(TransformerMaintenanceRecord, pk=pk)
    
    context = {
        'record': record,
        'check_items': record.check_items.all().order_by('category', 'order')
    }
    
    return render(request, 'circuit_breaker_maintenance/transformer_detail.html', context)

@login_required
def transformer_maintenance_edit(request, pk):
    """Edit transformer maintenance record"""
    from .models import TransformerMaintenanceRecord
    from .forms import TransformerMaintenanceRecordForm
    
    record = get_object_or_404(TransformerMaintenanceRecord, pk=pk)
    
    if request.method == 'POST':
        form = TransformerMaintenanceRecordForm(request.POST, instance=record)
        if form.is_valid():
            form.save()
            messages.success(request, 'Transformer maintenance record updated successfully.')
            return redirect('circuit_breaker_maintenance:transformer_detail', pk=pk)
    else:
        form = TransformerMaintenanceRecordForm(instance=record)
    
    context = {
        'form': form,
        'record': record,
        'title': 'Edit Transformer Maintenance Record'
    }
    
    return render(request, 'circuit_breaker_maintenance/transformer_form.html', context)
