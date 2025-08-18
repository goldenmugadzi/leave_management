from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.core.paginator import Paginator
from django.db.models import Q
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from rest_framework import viewsets
from rest_framework.decorators import api_view
from django.utils import timezone

from .models import ClientApplication, InspectionReport, ApplicationAssignment
from .forms import (
    ClientApplicationForm, InspectionReportForm, ApplicationAssignmentForm, 
    InspectionSearchForm
)


@login_required
def dashboard(request):
    """Main dashboard for inspections module"""
    # Get statistics
    total_applications = ClientApplication.objects.count()
    pending_applications = ClientApplication.objects.filter(status='submitted').count()
    in_progress = ClientApplication.objects.filter(status='in_progress').count()
    completed = ClientApplication.objects.filter(status='completed').count()
    
    # Recent applications
    recent_applications = ClientApplication.objects.order_by('-created_at')[:5]
    
    # My assignments (if user is field officer)
    my_assignments = ApplicationAssignment.objects.filter(
        assigned_to=request.user,
        status__in=['assigned', 'accepted', 'in_progress']
    ).order_by('-created_at')[:5]
    
    context = {
        'total_applications': total_applications,
        'pending_applications': pending_applications,
        'in_progress': in_progress,
        'completed': completed,
        'recent_applications': recent_applications,
        'my_assignments': my_assignments,
    }
    return render(request, 'inspections/dashboard.html', context)


# CLIENT APPLICATION VIEWS
@login_required
def application_list(request):
    """List all client applications with search and filtering"""
    form = InspectionSearchForm(request.GET)
    applications = ClientApplication.objects.all()
    
    if form.is_valid():
        search_query = form.cleaned_data.get('search_query')
        application_type = form.cleaned_data.get('application_type')
        status = form.cleaned_data.get('status')
        date_from = form.cleaned_data.get('date_from')
        date_to = form.cleaned_data.get('date_to')
        
        if search_query:
            applications = applications.filter(
                Q(application_number__icontains=search_query) |
                Q(customer_name__icontains=search_query) |
                Q(service_number__icontains=search_query)
            )
        
        if application_type:
            applications = applications.filter(application_type=application_type)
        
        if status:
            applications = applications.filter(status=status)
        
        if date_from:
            applications = applications.filter(submission_date__gte=date_from)
        
        if date_to:
            applications = applications.filter(submission_date__lte=date_to)
    
    applications = applications.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(applications, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'page_obj': page_obj,
        'applications': page_obj,
    }
    return render(request, 'inspections/application_list.html', context)


@login_required
def application_detail(request, pk):
    """View details of a client application"""
    application = get_object_or_404(ClientApplication, pk=pk)
    assignments = application.assignments.all().order_by('-created_at')
    inspection_reports = application.inspection_reports.all().order_by('-created_at')
    
    context = {
        'application': application,
        'assignments': assignments,
        'inspection_reports': inspection_reports,
    }
    return render(request, 'inspections/application_detail.html', context)


@login_required
def application_create(request):
    """Create a new client application"""
    if request.method == 'POST':
        form = ClientApplicationForm(request.POST)
        if form.is_valid():
            application = form.save(commit=False)
            application.submitted_by = request.user
            application.save()
            messages.success(request, f'Application {application.application_number} created successfully!')
            return redirect('inspections:application_detail', pk=application.pk)
    else:
        form = ClientApplicationForm()
    
    context = {'form': form}
    return render(request, 'inspections/application_form.html', context)


@login_required
def application_edit(request, pk):
    """Edit an existing client application"""
    application = get_object_or_404(ClientApplication, pk=pk)
    
    if request.method == 'POST':
        form = ClientApplicationForm(request.POST, instance=application)
        if form.is_valid():
            form.save()
            messages.success(request, 'Application updated successfully!')
            return redirect('inspections:application_detail', pk=application.pk)
    else:
        form = ClientApplicationForm(instance=application)
    
    context = {
        'form': form,
        'application': application,
        'is_edit': True
    }
    return render(request, 'inspections/application_form.html', context)


# INSPECTION REPORT VIEWS
@login_required
def inspection_list(request):
    """List all inspection reports"""
    reports = InspectionReport.objects.select_related('inspector', 'client_application').order_by('-created_at')
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'reports': page_obj,
    }
    return render(request, 'inspections/inspection_list.html', context)


@login_required
def inspection_detail(request, pk):
    """View details of an inspection report"""
    report = get_object_or_404(InspectionReport, pk=pk)
    context = {'report': report}
    return render(request, 'inspections/inspection_detail.html', context)


@login_required
def inspection_create(request):
    """Create a new inspection report"""
    if request.method == 'POST':
        form = InspectionReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.inspector = request.user
            report.save()
            messages.success(request, 'Inspection report created successfully!')
            return redirect('inspections:inspection_detail', pk=report.pk)
    else:
        form = InspectionReportForm()
    
    context = {'form': form}
    return render(request, 'inspections/inspection_form.html', context)


@login_required
def inspection_edit(request, pk):
    """Edit an existing inspection report"""
    report = get_object_or_404(InspectionReport, pk=pk)
    
    if request.method == 'POST':
        form = InspectionReportForm(request.POST, instance=report)
        if form.is_valid():
            form.save()
            messages.success(request, 'Inspection report updated successfully!')
            return redirect('inspections:inspection_detail', pk=report.pk)
    else:
        form = InspectionReportForm(instance=report)
    
    context = {
        'form': form,
        'report': report,
        'is_edit': True
    }
    return render(request, 'inspections/inspection_form.html', context)


# APPLICATION ASSIGNMENT VIEWS
@login_required
def assignment_list(request):
    """List all application assignments"""
    assignments = ApplicationAssignment.objects.select_related(
        'application', 'assigned_to', 'assigned_by'
    ).order_by('-created_at')
    
    # Filter by assigned user if not superuser
    if not request.user.is_superuser:
        assignments = assignments.filter(
            Q(assigned_to=request.user) | Q(assigned_by=request.user)
        )
    
    # Pagination
    paginator = Paginator(assignments, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'assignments': page_obj,
    }
    return render(request, 'inspections/assignment_list.html', context)


@login_required
def assignment_create(request):
    """Create a new assignment"""
    if request.method == 'POST':
        form = ApplicationAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            assignment.save()
            
            # Update application status
            assignment.application.status = 'assigned'
            assignment.application.save()
            
            messages.success(request, 'Assignment created successfully!')
            return redirect('inspections:assignment_list')
    else:
        form = ApplicationAssignmentForm()
    
    context = {'form': form}
    return render(request, 'inspections/assignment_form.html', context)


@login_required
@require_POST
def assignment_accept(request, pk):
    """Accept an assignment"""
    assignment = get_object_or_404(ApplicationAssignment, pk=pk, assigned_to=request.user)
    
    if assignment.status == 'assigned':
        assignment.accept_assignment()
        
        # Update application status
        assignment.application.status = 'in_progress'
        assignment.application.save()
        
        messages.success(request, 'Assignment accepted successfully!')
    else:
        messages.error(request, 'Assignment cannot be accepted.')
    
    return redirect('inspections:assignment_list')


@login_required
@require_POST
def assignment_complete(request, pk):
    """Complete an assignment"""
    assignment = get_object_or_404(ApplicationAssignment, pk=pk, assigned_to=request.user)
    
    if assignment.status in ['accepted', 'in_progress']:
        completion_notes = request.POST.get('completion_notes', '')
        assignment.complete_assignment(completion_notes)
        messages.success(request, 'Assignment completed successfully!')
    else:
        messages.error(request, 'Assignment cannot be completed.')
    
    return redirect('inspections:assignment_list')


# API VIEWS FOR MOBILE APP
@api_view(['GET'])
def api_my_assignments(request):
    """API endpoint for mobile app to get user's assignments"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    assignments = ApplicationAssignment.objects.filter(
        assigned_to=request.user,
        status__in=['assigned', 'accepted', 'in_progress']
    ).select_related('application')
    
    data = []
    for assignment in assignments:
        data.append({
            'id': str(assignment.id),
            'application_number': assignment.application.application_number,
            'customer_name': assignment.application.customer_name,
            'property_address': assignment.application.property_address,
            'status': assignment.status,
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
            'assignment_notes': assignment.assignment_notes,
        })
    
    return JsonResponse({'assignments': data})


@api_view(['POST'])
def api_accept_assignment(request, pk):
    """API endpoint for mobile app to accept assignment"""
    if not request.user.is_authenticated:
        return JsonResponse({'error': 'Authentication required'}, status=401)
    
    try:
        assignment = ApplicationAssignment.objects.get(pk=pk, assigned_to=request.user)
        if assignment.status == 'assigned':
            assignment.accept_assignment()
            
            # Update application status
            assignment.application.status = 'in_progress'
            assignment.application.save()
            
            return JsonResponse({'success': True, 'message': 'Assignment accepted'})
        else:
            return JsonResponse({'error': 'Assignment cannot be accepted'}, status=400)
    except ApplicationAssignment.DoesNotExist:
        return JsonResponse({'error': 'Assignment not found'}, status=404) 