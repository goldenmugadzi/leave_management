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

from .models import (
    Customer, Contractor, ApplicationAttachment, ClientApplication, 
    InspectionReport, E6Certificate, E1DefectReport, InspectionWorkflow, 
    ApplicationAssignment
)
from .forms import (
    CustomerForm, ContractorForm, ApplicationAttachmentForm, ClientApplicationForm, 
    InspectionReportForm, E6CertificateForm, E1DefectReportForm, 
    ApplicationAssignmentForm, InspectionSearchForm
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


# CUSTOMER MANAGEMENT VIEWS
@login_required
def customer_list(request):
    """List all customers with search and filtering"""
    customers = Customer.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        customers = customers.filter(
            Q(customer_id__icontains=search_query) |
            Q(full_name__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(district__icontains=search_query)
        )
    
    customers = customers.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(customers, 20)
    page_number = request.GET.get('page')
    customers = paginator.get_page(page_number)
    
    context = {
        'customers': customers,
        'search_query': search_query,
    }
    return render(request, 'inspections/customer_list.html', context)


@login_required
def customer_create(request):
    """Create a new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.full_name}" created successfully.')
            return redirect('inspections:customer_list')
    else:
        form = CustomerForm()
    
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'inspections/customer_form.html', context)


@login_required
def customer_edit(request, pk):
    """Edit an existing customer"""
    customer = get_object_or_404(Customer, pk=pk)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            customer = form.save()
            messages.success(request, f'Customer "{customer.full_name}" updated successfully.')
            return redirect('inspections:customer_list')
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'is_edit': True,
    }
    return render(request, 'inspections/customer_form.html', context)


@login_required
def customer_detail(request, pk):
    """View customer details"""
    customer = get_object_or_404(Customer, pk=pk)
    applications = customer.applications.all().order_by('-created_at')
    
    context = {
        'customer': customer,
        'applications': applications,
    }
    return render(request, 'inspections/customer_detail.html', context)


# CONTRACTOR MANAGEMENT VIEWS
@login_required
def contractor_list(request):
    """List all contractors with search and filtering"""
    contractors = Contractor.objects.all()
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        contractors = contractors.filter(
            Q(contractor_id__icontains=search_query) |
            Q(business_name__icontains=search_query) |
            Q(contact_person__icontains=search_query) |
            Q(phone__icontains=search_query) |
            Q(email__icontains=search_query) |
            Q(district__icontains=search_query) |
            Q(license_number__icontains=search_query)
        )
    
    contractors = contractors.order_by('-created_at')
    
    # Pagination
    paginator = Paginator(contractors, 20)
    page_number = request.GET.get('page')
    contractors = paginator.get_page(page_number)
    
    context = {
        'contractors': contractors,
        'search_query': search_query,
    }
    return render(request, 'inspections/contractor_list.html', context)


@login_required
def contractor_create(request):
    """Create a new contractor"""
    if request.method == 'POST':
        form = ContractorForm(request.POST)
        if form.is_valid():
            contractor = form.save()
            messages.success(request, f'Contractor "{contractor.business_name}" created successfully.')
            return redirect('inspections:contractor_list')
    else:
        form = ContractorForm()
    
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'inspections/contractor_form.html', context)


@login_required
def contractor_edit(request, pk):
    """Edit an existing contractor"""
    contractor = get_object_or_404(Contractor, pk=pk)
    
    if request.method == 'POST':
        form = ContractorForm(request.POST, instance=contractor)
        if form.is_valid():
            contractor = form.save()
            messages.success(request, f'Contractor "{contractor.business_name}" updated successfully.')
            return redirect('inspections:contractor_list')
    else:
        form = ContractorForm(instance=contractor)
    
    context = {
        'form': form,
        'contractor': contractor,
        'is_edit': True,
    }
    return render(request, 'inspections/contractor_form.html', context)


@login_required
def contractor_detail(request, pk):
    """View contractor details"""
    contractor = get_object_or_404(Contractor, pk=pk)
    applications = contractor.applications.all().order_by('-created_at')
    
    context = {
        'contractor': contractor,
        'applications': applications,
    }
    return render(request, 'inspections/contractor_detail.html', context)


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
                Q(customer__full_name__icontains=search_query) |
                Q(customer__customer_id__icontains=search_query) |
                Q(contractor__business_name__icontains=search_query) |
                Q(contractor__contractor_id__icontains=search_query)
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
    applications = paginator.get_page(page_number)
    
    context = {
        'form': form,
        'applications': applications,
    }
    return render(request, 'inspections/application_list.html', context)


@login_required
def application_detail(request, pk):
    """View details of a client application"""
    application = get_object_or_404(ClientApplication, pk=pk)
    assignments = application.assignments.all().order_by('-created_at')
    inspection_reports = application.inspection_reports.all().order_by('-created_at')
    attachments = application.attachments.all().order_by('-uploaded_at')
    
    # Get related documents
    e6_certificates = application.e6_certificates.all().order_by('-created_at')
    e1_defect_reports = application.e1_defect_reports.all().order_by('-created_at')
    
    context = {
        'application': application,
        'assignments': assignments,
        'inspection_reports': inspection_reports,
        'attachments': attachments,
        'e6_certificates': e6_certificates,
        'e1_defect_reports': e1_defect_reports,
    }

    print("attachments: ", attachments)
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
            
            # Handle file attachments
            files = request.FILES.getlist('attachments[]')
            file_types = request.POST.getlist('file_types[]')
            descriptions = request.POST.getlist('descriptions[]')
            print('file_types: ', file_types)
            print('descriptions: ', descriptions)
            for i, file in enumerate(files):
                if file:  # Only create attachment if a file was actually uploaded
                    file_type = file_types[i] if i < len(file_types) else 'other'
                    description = descriptions[i] if i < len(descriptions) else ''
                    
                    app_attachment = ApplicationAttachment(
                        application=application,
                        file=file,
                        file_type=file_type,
                        description=description
                    )
                    app_attachment.save()

                    print('app_attachment: ', app_attachment)
            
            messages.success(request, f'Application "{application.application_number}" created successfully.')
            return redirect('inspections:application_detail', pk=application.pk)
    else:
        form = ClientApplicationForm()
    
    context = {
        'form': form,
        'is_edit': False,
    }
    return render(request, 'inspections/application_form.html', context)


@login_required
def application_edit(request, pk):
    """Edit an existing client application"""
    application = get_object_or_404(ClientApplication, pk=pk)
    
    if request.method == 'POST':
        form = ClientApplicationForm(request.POST, instance=application)
        if form.is_valid():
            application = form.save()

            # Handle file attachments
            files = request.FILES.getlist('attachments[]')
            file_types = request.POST.getlist('file_types[]')
            descriptions = request.POST.getlist('descriptions[]')
            print('file_types: ', file_types)
            print('descriptions: ', descriptions)
            for i, file in enumerate(files):
                if file:
                    file_type = file_types[i] if i < len(file_types) else 'other'
                    description = descriptions[i] if i < len(descriptions) else ''
                    
                    app_attachment = ApplicationAttachment(
                        application=application,
                        file=file,
                        file_type=file_type,
                        description=description
                    )
                    app_attachment.save()
                    print('app_attachment: ', app_attachment)
            
            # Update application status
            application.status = 'submitted'
            application.save()

            messages.success(request, f'Application "{application.application_number}" updated successfully.')
            return redirect('inspections:application_detail', pk=application.pk)
    else:
        form = ClientApplicationForm(instance=application)
    
    context = {
        'form': form,
        'application': application,
        'is_edit': True,
    }
    return render(request, 'inspections/application_form.html', context)


# INSPECTION REPORT VIEWS
@login_required
def inspection_list(request):
    """List all inspection reports"""
    inspections = InspectionReport.objects.all().order_by('-created_at')
    print("inspections: ", inspections)
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        inspections = inspections.filter(
            Q(service_no__icontains=search_query) |
            Q(consumer_name__icontains=search_query) |
            Q(inspector__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(inspections, 20)
    page_number = request.GET.get('page')
    inspections = paginator.get_page(page_number)
    
    context = {
        'reports': inspections,  # Template expects 'reports' variable
        'search_query': search_query,
    }
    return render(request, 'inspections/inspection_list.html', context)


@login_required
def inspection_detail(request, pk):
    """View inspection report details (E117)"""
    inspection = get_object_or_404(InspectionReport, pk=pk)
    
    context = {
        'inspection': inspection,
    }
    return render(request, 'inspections/e117_view.html', context)


# E6 CERTIFICATE VIEWS
@login_required
def e6_certificate_list(request):
    """List all E6 certificates"""
    certificates = E6Certificate.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        certificates = certificates.filter(
            Q(certificate_number__icontains=search_query) |
            Q(service_no__icontains=search_query) |
            Q(property_owner_occupant__icontains=search_query) |
            Q(installation_inspector__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(certificates, 20)
    page_number = request.GET.get('page')
    certificates = paginator.get_page(page_number)
    
    context = {
        'certificates': certificates,
        'search_query': search_query,
    }
    return render(request, 'inspections/e6_certificate_list.html', context)


@login_required
def e6_certificate_detail(request, pk):
    """View E6 certificate details"""
    certificate = get_object_or_404(E6Certificate, pk=pk)
    
    context = {
        'certificate': certificate,
    }
    return render(request, 'inspections/e6_certificate_view.html', context)


# E1 DEFECT REPORT VIEWS
@login_required
def e1_defect_report_list(request):
    """List all E1 defect reports"""
    reports = E1DefectReport.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        reports = reports.filter(
            Q(report_number__icontains=search_query) |
            Q(service_no__icontains=search_query) |
            Q(property_address__icontains=search_query) |
            Q(installation_inspector__username__icontains=search_query)
        )
    
    # Pagination
    paginator = Paginator(reports, 20)
    page_number = request.GET.get('page')
    reports = paginator.get_page(page_number)
    
    context = {
        'reports': reports,
        'search_query': search_query,
    }
    return render(request, 'inspections/e1_defect_report_list.html', context)


@login_required
def e1_defect_report_detail(request, pk):
    """View E1 defect report details"""
    report = get_object_or_404(E1DefectReport, pk=pk)
    
    context = {
        'report': report,
    }
    return render(request, 'inspections/e1_defect_report_view.html', context)


# WORKFLOW VIEWS
@login_required
def workflow_list(request):
    """List all inspection workflows"""
    workflows = InspectionWorkflow.objects.all().order_by('-created_at')
    
    # Search functionality
    search_query = request.GET.get('search', '')
    if search_query:
        workflows = workflows.filter(
            Q(workflow_number__icontains=search_query) |
            Q(client_application__application_number__icontains=search_query) |
            Q(client_application__customer__full_name__icontains=search_query) |
            Q(status__icontains=search_query)
        )
    
    # Filter by status
    status_filter = request.GET.get('status', '')
    if status_filter:
        workflows = workflows.filter(status=status_filter)
    
    # Pagination
    paginator = Paginator(workflows, 20)
    page_number = request.GET.get('page')
    workflows = paginator.get_page(page_number)
    
    # Get all status choices for filter dropdown
    status_choices = InspectionWorkflow.WORKFLOW_STATUS_CHOICES
    
    context = {
        'workflows': workflows,
        'search_query': search_query,
        'status_filter': status_filter,
        'status_choices': status_choices,
    }
    return render(request, 'inspections/workflow_list.html', context)


@login_required
def workflow_detail(request, pk):
    """View workflow details"""
    workflow = get_object_or_404(InspectionWorkflow, pk=pk)
    
    context = {
        'workflow': workflow,
    }
    return render(request, 'inspections/workflow_detail.html', context)


# ASSIGNMENT VIEWS
@login_required
def assignment_list(request):
    """List all application assignments"""
    assignments = ApplicationAssignment.objects.all().order_by('-created_at')
    
    # Filter by assigned user if specified
    assigned_to = request.GET.get('assigned_to')
    if assigned_to:
        assignments = assignments.filter(assigned_to__username=assigned_to)
    
    # Pagination
    paginator = Paginator(assignments, 20)
    page_number = request.GET.get('page')
    assignments = paginator.get_page(page_number)
    
    context = {
        'assignments': assignments,
    }
    return render(request, 'inspections/assignment_list.html', context)


@login_required
def assignment_create(request):
    """Create a new application assignment"""
    if request.method == 'POST':
        form = ApplicationAssignmentForm(request.POST)
        if form.is_valid():
            assignment = form.save(commit=False)
            assignment.assigned_by = request.user
            assignment.save()
            
            # Update application status
            application = assignment.application
            application.status = 'assigned'
            application.save()
            
            messages.success(request, f'Application assigned to {assignment.assigned_to.get_full_name()} successfully.')
            return redirect('inspections:application_detail', pk=application.pk)
    else:
        # Pre-select application if provided in query parameter
        application_id = request.GET.get('application')
        form = ApplicationAssignmentForm(application_id=application_id)
    
    context = {
        'form': form,
    }
    return render(request, 'inspections/assignment_form.html', context)


@login_required
@require_POST
def assignment_accept(request, pk):
    """Accept an assignment"""
    assignment = get_object_or_404(ApplicationAssignment, pk=pk)
    
    if assignment.assigned_to == request.user:
        assignment.accept_assignment()
        messages.success(request, 'Assignment accepted successfully.')
    else:
        messages.error(request, 'You can only accept assignments assigned to you.')
    
    return redirect('inspections:assignment_list')


@login_required
@require_POST
def assignment_complete(request, pk):
    """Complete an assignment"""
    assignment = get_object_or_404(ApplicationAssignment, pk=pk)
    
    if assignment.assigned_to == request.user:
        notes = request.POST.get('completion_notes', '')
        assignment.complete_assignment(notes)
        messages.success(request, 'Assignment completed successfully.')
    else:
        messages.error(request, 'You can only complete assignments assigned to you.')
    
    return redirect('inspections:assignment_list')


# API VIEWS
@api_view(['GET'])
def api_my_assignments(request):
    """API endpoint for getting current user's assignments"""
    assignments = ApplicationAssignment.objects.filter(
        assigned_to=request.user,
        status__in=['assigned', 'accepted', 'in_progress']
    ).order_by('-created_at')
    
    data = []
    for assignment in assignments:
        data.append({
            'id': str(assignment.id),
            'application_number': assignment.application.application_number,
            'customer_name': assignment.application.customer.full_name,
            'status': assignment.status,
            'due_date': assignment.due_date.isoformat() if assignment.due_date else None,
            'assignment_date': assignment.assignment_date.isoformat(),
        })
    
    return JsonResponse({'assignments': data})


@api_view(['POST'])
def api_accept_assignment(request, pk):
    """API endpoint for accepting an assignment"""
    assignment = get_object_or_404(ApplicationAssignment, pk=pk)
    
    if assignment.assigned_to == request.user:
        assignment.accept_assignment()
        return JsonResponse({'status': 'success', 'message': 'Assignment accepted'})
    else:
        return JsonResponse({'status': 'error', 'message': 'Unauthorized'}, status=403) 