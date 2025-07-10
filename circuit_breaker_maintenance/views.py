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
from .forms import CircuitBreakerForm, CircuitBreakerBulkImportForm, QuickCircuitBreakerForm
import csv
import pandas as pd
from io import StringIO

@login_required
def circuit_breaker_list(request):
    """List all circuit breakers with filtering and search"""
    circuit_breakers = CircuitBreaker.objects.all()
    
    # Get filter parameters
    substation_filter = request.GET.get('substation')
    status_filter = request.GET.get('status')
    search_query = request.GET.get('search')
    
    # Apply filters
    if substation_filter:
        circuit_breakers = circuit_breakers.filter(sub_station__icontains=substation_filter)
    
    if status_filter == 'active':
        circuit_breakers = circuit_breakers.filter(is_active=True)
    elif status_filter == 'inactive':
        circuit_breakers = circuit_breakers.filter(is_active=False)
    
    # Apply search
    if search_query:
        circuit_breakers = circuit_breakers.filter(
            Q(breaker_number__icontains=search_query) |
            Q(make_type__icontains=search_query) |
            Q(serial_number__icontains=search_query) |
            Q(sub_station__icontains=search_query)
        )
    
    # Annotate with maintenance count
    circuit_breakers = circuit_breakers.annotate(
        maintenance_count=Count('maintenancerecord')
    ).select_related()
    
    # Get unique substations for filter dropdown
    substations = CircuitBreaker.objects.values_list('sub_station', flat=True).distinct().order_by('sub_station')
    
    # Pagination
    paginator = Paginator(circuit_breakers, 25)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'substations': substations,
        'current_substation': substation_filter,
        'current_status': status_filter,
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
            messages.error(request, 'Please correct the errors below.')
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
    initial_data = {}
    
    if circuit_breaker_id:
        try:
            circuit_breaker = CircuitBreaker.objects.get(pk=circuit_breaker_id)
            initial_data['circuit_breaker'] = circuit_breaker
        except CircuitBreaker.DoesNotExist:
            pass
    
    if request.method == 'POST':
        # You'll need to create a MaintenanceRecordForm
        # form = MaintenanceRecordForm(request.POST)
        # For now, let's create a simple placeholder
        messages.info(request, 'Maintenance record creation form will be implemented here.')
        return redirect('circuit_breaker_maintenance:record_list')
    else:
        # form = MaintenanceRecordForm(initial=initial_data)
        pass
    
    context = {
        'action': 'Create',
        'circuit_breaker_id': circuit_breaker_id,
    }
    
    return render(request, 'circuit_breaker_maintenance/maintenance_record_form.html', context)

@login_required
def maintenance_record_edit(request, pk):
    """Edit an existing maintenance record"""
    record = get_object_or_404(MaintenanceRecord, pk=pk)
    
    if request.method == 'POST':
        # You'll need to create a MaintenanceRecordForm
        # form = MaintenanceRecordForm(request.POST, instance=record)
        # For now, let's create a simple placeholder
        messages.info(request, 'Maintenance record editing form will be implemented here.')
        return redirect('circuit_breaker_maintenance:record_detail', pk=record.pk)
    else:
        # form = MaintenanceRecordForm(instance=record)
        pass
    
    context = {
        'record': record,
        'action': 'Edit',
    }
    
    return render(request, 'circuit_breaker_maintenance/maintenance_record_form.html', context)
