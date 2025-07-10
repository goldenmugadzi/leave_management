from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core.paginator import Paginator
from django.db.models import Q, Count
from django.http import JsonResponse
from .models import CircuitBreaker, MaintenanceRecord
from .forms import CircuitBreakerForm

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
    """View details of a specific circuit breaker"""
    circuit_breaker = get_object_or_404(CircuitBreaker, pk=pk)
    
    # Get maintenance records for this circuit breaker
    maintenance_records = MaintenanceRecord.objects.filter(
        circuit_breaker=circuit_breaker
    ).order_by('-date')[:10]  # Last 10 records
    
    # Get next maintenance due
    next_maintenance = MaintenanceRecord.objects.filter(
        circuit_breaker=circuit_breaker,
        next_maintenance_due__gte=timezone.now().date()
    ).order_by('next_maintenance_due').first()
    
    context = {
        'circuit_breaker': circuit_breaker,
        'maintenance_records': maintenance_records,
        'next_maintenance': next_maintenance,
    }
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_detail.html', context)

@login_required
def circuit_breaker_create(request):
    """Create a new circuit breaker"""
    if request.method == 'POST':
        form = CircuitBreakerForm(request.POST)
        if form.is_valid():
            circuit_breaker = form.save()
            messages.success(request, f'Circuit breaker {circuit_breaker.breaker_number} created successfully!')
            return redirect('circuit_breaker_maintenance:circuit_breaker_detail', pk=circuit_breaker.pk)
    else:
        form = CircuitBreakerForm()
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_form.html', {
        'form': form, 
        'action': 'Create'
    })

@login_required
def circuit_breaker_edit(request, pk):
    """Edit an existing circuit breaker"""
    circuit_breaker = get_object_or_404(CircuitBreaker, pk=pk)
    
    if request.method == 'POST':
        form = CircuitBreakerForm(request.POST, instance=circuit_breaker)
        if form.is_valid():
            form.save()
            messages.success(request, f'Circuit breaker {circuit_breaker.breaker_number} updated successfully!')
            return redirect('circuit_breaker_maintenance:circuit_breaker_detail', pk=circuit_breaker.pk)
    else:
        form = CircuitBreakerForm(instance=circuit_breaker)
    
    return render(request, 'circuit_breaker_maintenance/circuit_breaker_form.html', {
        'form': form, 
        'circuit_breaker': circuit_breaker,
        'action': 'Edit'
    })

@login_required
def get_substations_ajax(request):
    """AJAX endpoint to get substations for filtering"""
    substations = list(CircuitBreaker.objects.values_list('sub_station', flat=True).distinct().order_by('sub_station'))
    return JsonResponse({'substations': substations})
