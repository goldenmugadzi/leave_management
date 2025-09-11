from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.views.decorators.http import require_http_methods
from django.utils import timezone
from .models import Equipment, EquipmentOperation, OperationDocument, EquipmentHistory
from .forms import EquipmentForm, EquipmentOperationForm, OperationDocumentForm


@login_required
def dashboard(request):
    """
    Main dashboard for equipment management
    """
    # Get summary statistics
    total_equipment = Equipment.objects.count()
    active_equipment = Equipment.objects.filter(status='active').count()
    pending_operations = EquipmentOperation.objects.filter(status='submitted').count()
    recent_operations = EquipmentOperation.objects.order_by('-created_at')[:5]
    
    # Equipment by status
    equipment_status = {
        'active': Equipment.objects.filter(status='active').count(),
        'faulty': Equipment.objects.filter(status='faulty').count(),
        'maintenance': Equipment.objects.filter(status='maintenance').count(),
        'removed': Equipment.objects.filter(status='removed').count(),
    }
    
    # Operations by status
    operations_status = {
        'draft': EquipmentOperation.objects.filter(status='draft').count(),
        'submitted': EquipmentOperation.objects.filter(status='submitted').count(),
        'approved': EquipmentOperation.objects.filter(status='approved').count(),
        'completed': EquipmentOperation.objects.filter(status='completed').count(),
    }
    
    context = {
        'total_equipment': total_equipment,
        'active_equipment': active_equipment,
        'pending_operations': pending_operations,
        'recent_operations': recent_operations,
        'equipment_status': equipment_status,
        'operations_status': operations_status,
    }
    
    return render(request, 'equipment_management/dashboard.html', context)


@login_required
def equipment_list(request):
    """
    List all equipment with search and filtering
    """
    equipment_list = Equipment.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        equipment_list = equipment_list.filter(
            Q(serial_number__icontains=search_query) |
            Q(make__icontains=search_query) |
            Q(substation_name__icontains=search_query) |
            Q(location_description__icontains=search_query)
        )
    
    # Filter by equipment type
    equipment_type = request.GET.get('equipment_type')
    if equipment_type:
        equipment_list = equipment_list.filter(equipment_type=equipment_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        equipment_list = equipment_list.filter(status=status)
    
    # Filter by district
    district = request.GET.get('district')
    if district:
        equipment_list = equipment_list.filter(district=district)
    
    # Pagination
    paginator = Paginator(equipment_list, 20)  # Show 20 equipment per page
    page_number = request.GET.get('page')
    equipment = paginator.get_page(page_number)
    
    # Get filter options for dropdowns
    equipment_types = Equipment.EQUIPMENT_TYPES
    status_choices = Equipment.STATUS_CHOICES
    districts = Equipment.objects.values_list('district', flat=True).distinct()
    
    context = {
        'equipment': equipment,
        'search_query': search_query,
        'equipment_types': equipment_types,
        'status_choices': status_choices,
        'districts': districts,
        'selected_type': equipment_type,
        'selected_status': status,
        'selected_district': district,
    }
    
    return render(request, 'equipment_management/equipment_list.html', context)


@login_required
def equipment_detail(request, pk):
    """
    Display detailed information about a specific equipment
    """
    equipment = get_object_or_404(Equipment, pk=pk)
    
    # Get related operations
    installation_operations = equipment.installation_operations.all()
    removal_operations = equipment.removal_operations.all()
    
    # Get equipment history
    history = equipment.history.order_by('-performed_at')[:10]
    
    context = {
        'equipment': equipment,
        'installation_operations': installation_operations,
        'removal_operations': removal_operations,
        'history': history,
    }
    
    return render(request, 'equipment_management/equipment_detail.html', context)


@login_required
def equipment_create(request):
    """
    Create new equipment
    """
    if request.method == 'POST':
        form = EquipmentForm(request.POST)
        if form.is_valid():
            equipment = form.save(commit=False)
            equipment.created_by = request.user
            equipment.save()
            
            # Create history record
            EquipmentHistory.objects.create(
                equipment=equipment,
                action_type='created',
                action_description=f'Equipment created by {request.user}',
                performed_by=request.user
            )
            
            messages.success(request, f'Equipment {equipment.serial_number} created successfully.')
            return redirect('equipment_management:equipment_detail', pk=equipment.pk)
    else:
        form = EquipmentForm()
    
    return render(request, 'equipment_management/equipment_form.html', {
        'form': form,
        'title': 'Create New Equipment'
    })


@login_required
def equipment_edit(request, pk):
    """
    Edit existing equipment
    """
    equipment = get_object_or_404(Equipment, pk=pk)
    
    if request.method == 'POST':
        form = EquipmentForm(request.POST, instance=equipment)
        if form.is_valid():
            # Store old values for history
            old_values = {
                'status': equipment.status,
                'location_description': equipment.location_description,
                'substation_name': equipment.substation_name,
            }
            
            updated_equipment = form.save()
            
            # Create history record for changes
            changes = []
            if old_values['status'] != updated_equipment.status:
                changes.append(f"Status changed from {old_values['status']} to {updated_equipment.status}")
            if old_values['location_description'] != updated_equipment.location_description:
                changes.append("Location description updated")
            if old_values['substation_name'] != updated_equipment.substation_name:
                changes.append(f"Substation changed from {old_values['substation_name']} to {updated_equipment.substation_name}")
            
            if changes:
                EquipmentHistory.objects.create(
                    equipment=updated_equipment,
                    action_type='specification_change',
                    action_description='; '.join(changes),
                    old_value=old_values,
                    new_value={
                        'status': updated_equipment.status,
                        'location_description': updated_equipment.location_description,
                        'substation_name': updated_equipment.substation_name,
                    },
                    performed_by=request.user
                )
            
            messages.success(request, f'Equipment {equipment.serial_number} updated successfully.')
            return redirect('equipment_management:equipment_detail', pk=equipment.pk)
    else:
        form = EquipmentForm(instance=equipment)
    
    return render(request, 'equipment_management/equipment_form.html', {
        'form': form,
        'equipment': equipment,
        'title': f'Edit Equipment {equipment.serial_number}'
    })


@login_required
def operation_list(request):
    """
    List all equipment operations
    """
    operations_list = EquipmentOperation.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search')
    if search_query:
        operations_list = operations_list.filter(
            Q(form_number__icontains=search_query) |
            Q(consumer_name__icontains=search_query) |
            Q(substation_name__icontains=search_query) |
            Q(operator_name__icontains=search_query)
        )
    
    # Filter by operation type
    operation_type = request.GET.get('operation_type')
    if operation_type:
        operations_list = operations_list.filter(operation_type=operation_type)
    
    # Filter by status
    status = request.GET.get('status')
    if status:
        operations_list = operations_list.filter(status=status)
    
    # Pagination
    paginator = Paginator(operations_list, 20)
    page_number = request.GET.get('page')
    operations = paginator.get_page(page_number)
    
    # Get filter options
    operation_types = EquipmentOperation.OPERATION_TYPES
    status_choices = EquipmentOperation.STATUS_CHOICES
    
    context = {
        'operations': operations,
        'search_query': search_query,
        'operation_types': operation_types,
        'status_choices': status_choices,
        'selected_type': operation_type,
        'selected_status': status,
    }
    
    return render(request, 'equipment_management/operation_list_tailwind.html', context)


@login_required
def operation_detail(request, pk):
    """
    Display detailed information about a specific operation
    """
    operation = get_object_or_404(EquipmentOperation, pk=pk)
    documents = operation.documents.all()
    
    context = {
        'operation': operation,
        'documents': documents,
    }
    
    return render(request, 'equipment_management/operation_detail_tailwind.html', context)


@login_required
def operation_create(request):
    """
    Create new equipment operation (Form E114)
    """
    if request.method == 'POST':
        form = EquipmentOperationForm(request.POST)
        if form.is_valid():
            operation = form.save(commit=False)
            operation.created_by = request.user
            operation.save()
            
            messages.success(request, f'Operation {operation.form_number} created successfully.')
            return redirect('equipment_management:operation_detail', pk=operation.pk)
    else:
        form = EquipmentOperationForm()
    
    return render(request, 'equipment_management/operation_form_tailwind.html', {
        'form': form,
        'title': 'Create New Operation (Form E114)'
    })


@login_required
def operation_edit(request, pk):
    """
    Edit existing operation
    """
    operation = get_object_or_404(EquipmentOperation, pk=pk)
    
    # Check if operation can be edited
    if operation.status in ['completed', 'cancelled']:
        messages.error(request, 'This operation cannot be edited as it is already completed or cancelled.')
        return redirect('equipment_management:operation_detail', pk=operation.pk)
    
    if request.method == 'POST':
        form = EquipmentOperationForm(request.POST, instance=operation)
        if form.is_valid():
            form.save()
            messages.success(request, f'Operation {operation.form_number} updated successfully.')
            return redirect('equipment_management:operation_detail', pk=operation.pk)
    else:
        form = EquipmentOperationForm(instance=operation)
    
    return render(request, 'equipment_management/operation_form_tailwind.html', {
        'form': form,
        'operation': operation,
        'title': f'Edit Operation {operation.form_number}'
    })


@login_required
@require_http_methods(["GET"])
def equipment_search_api(request):
    """
    API endpoint for equipment search (for autocomplete)
    """
    query = request.GET.get('q', '')
    equipment_type = request.GET.get('type', '')
    
    equipment = Equipment.objects.filter(status='active')
    
    if query:
        equipment = equipment.filter(
            Q(serial_number__icontains=query) |
            Q(make__icontains=query)
        )
    
    if equipment_type:
        equipment = equipment.filter(equipment_type=equipment_type)
    
    equipment = equipment[:10]  # Limit to 10 results
    
    results = []
    for item in equipment:
        results.append({
            'id': item.id,
            'serial_number': item.serial_number,
            'make': item.make,
            'equipment_type': item.get_equipment_type_display(),
            'substation_name': item.substation_name,
            'text': f"{item.serial_number} - {item.make} ({item.substation_name})"
        })
    
    return JsonResponse({'results': results})
