from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from .models import Customer, DocumentType, CustomerDocument, OnboardingProcess, ActivityLog
from .forms import CustomerForm, DocumentTypeForm

# Create your views here.
@login_required
def create_customer(request):
    """Create a new customer"""
    if request.method == 'POST':
        form = CustomerForm(request.POST)
        if form.is_valid():
            customer = form.save()
            
            # Log activity
            ActivityLog.objects.create(
                customer=customer,
                user=request.user,
                action="Created customer",
                details=f"New customer {customer.name} ({customer.customer_id}) created in the system."
            )
            
            messages.success(request, f"Customer {customer.name} has been created successfully.")
            return redirect('comm_files:customer_detail', customer_id=customer.customer_id)
    else:
        form = CustomerForm()
    
    return render(request, 'comm_files/create_customer.html', {'form': form})

# Customer views
@login_required
def customer_list(request):
    """Display list of customers with search and filters"""
    search_term = request.GET.get('search', '')
    customer_type = request.GET.get('customer_type', '')
    
    customers = Customer.objects.filter(is_active=True)
    
    # Apply search if provided
    if search_term:
        customers = customers.filter(
            Q(name__icontains=search_term) |
            Q(customer_id__icontains=search_term) |
            Q(account_number__icontains=search_term) |
            Q(meter_number__icontains=search_term)
        )
        
    # Apply customer type filter if provided
    if customer_type:
        customers = customers.filter(customer_type=customer_type)
    
    # Pagination
    paginator = Paginator(customers, 20)  # 20 customers per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search_term': search_term,
        'customer_type': customer_type,
        'customer_types': Customer.CUSTOMER_TYPES,
    }
    
    return render(request, 'comm_files/customer_list.html', context)

@login_required
def customer_detail(request, customer_id):
    """Display customer details with their documents and onboarding status"""
    customer = get_object_or_404(Customer, customer_id=customer_id)
    documents = CustomerDocument.objects.filter(customer=customer)
    onboarding_processes = OnboardingProcess.objects.filter(customer=customer)
    activity_logs = ActivityLog.objects.filter(customer=customer)[:10]  # Get only the 10 most recent logs
    
    context = {
        'customer': customer,
        'documents': documents,
        'onboarding_processes': onboarding_processes,
        'activity_logs': activity_logs,
    }
    
    return render(request, 'comm_files/customer_detail.html', context)

# Document views
@login_required
def document_upload(request, customer_id):
    """Upload a document for a customer"""
    customer = get_object_or_404(Customer, customer_id=customer_id)
    document_types = DocumentType.objects.all()
    
    if request.method == 'POST':
        document_type_id = request.POST.get('document_type')
        document_type = get_object_or_404(DocumentType, id=document_type_id)
        description = request.POST.get('description', '')
        expiry_date = request.POST.get('expiry_date') or None
        
        # Check if file is in request
        if 'document_file' in request.FILES:
            document_file = request.FILES['document_file']
            
            # Check if customer already has this document type
            existing_doc = CustomerDocument.objects.filter(
                customer=customer, 
                document_type=document_type
            ).first()
            
            if existing_doc:
                # Update existing document
                existing_doc.file = document_file
                existing_doc.description = description
                existing_doc.expiry_date = expiry_date
                existing_doc.status = 'PENDING'
                existing_doc.uploaded_by = request.user
                existing_doc.save()
                
                # Log activity
                ActivityLog.objects.create(
                    customer=customer,
                    user=request.user,
                    action=f"Updated document: {document_type.name}",
                    details=f"Document updated and set to pending review."
                )
                
                messages.success(request, f"Document {document_type.name} updated successfully and pending review.")
            else:
                # Create new document
                new_doc = CustomerDocument.objects.create(
                    customer=customer,
                    document_type=document_type,
                    file=document_file,
                    description=description,
                    expiry_date=expiry_date,
                    uploaded_by=request.user
                )
                
                # Log activity
                ActivityLog.objects.create(
                    customer=customer,
                    user=request.user,
                    action=f"Uploaded new document: {document_type.name}",
                    details=f"New document uploaded and pending review."
                )
                
                messages.success(request, f"Document {document_type.name} uploaded successfully and pending review.")
            
            return redirect('comm_files:customer_detail', customer_id=customer.customer_id)
        else:
            messages.error(request, "No file was uploaded. Please select a file.")
    
    context = {
        'customer': customer,
        'document_types': document_types
    }
    
    return render(request, 'comm_files/document_upload.html', context)

@login_required
def document_review(request, document_id):
    """Review a document and approve or reject it"""
    document = get_object_or_404(CustomerDocument, id=document_id)
    
    if request.method == 'POST':
        action = request.POST.get('action')
        
        if action == 'approve':
            document.approve(request.user)
            
            # Log activity
            ActivityLog.objects.create(
                customer=document.customer,
                user=request.user,
                action=f"Approved document: {document.document_type.name}",
                details=f"Document review completed with approval."
            )
            
            messages.success(request, f"Document {document.document_type.name} has been approved.")
        
        elif action == 'reject':
            reason = request.POST.get('rejection_reason', '')
            if not reason:
                messages.error(request, "Please provide a reason for rejection.")
                return redirect('comm_files:document_review', document_id=document.id)
                
            document.reject(request.user, reason)
            
            # Log activity
            ActivityLog.objects.create(
                customer=document.customer,
                user=request.user,
                action=f"Rejected document: {document.document_type.name}",
                details=f"Document rejected. Reason: {reason}"
            )
            
            messages.warning(request, f"Document {document.document_type.name} has been rejected.")
        
        return redirect('comm_files:customer_detail', customer_id=document.customer.customer_id)
    
    context = {
        'document': document
    }
    
    return render(request, 'comm_files/document_review.html', context)

# Onboarding Process views
@login_required
def start_onboarding(request, customer_id):
    """Start or update an onboarding process for a customer"""
    customer = get_object_or_404(Customer, customer_id=customer_id)
    
    # Check if customer already has an ongoing onboarding process
    existing_process = OnboardingProcess.objects.filter(
        customer=customer, 
        status__in=['INITIATED', 'DOCS_SUBMITTED', 'UNDER_REVIEW']
    ).first()
    
    if existing_process:
        messages.info(request, f"Customer already has an ongoing onboarding process in status: {existing_process.get_status_display()}")
        return redirect('comm_files:customer_detail', customer_id=customer.customer_id)
    
    # Create new onboarding process
    new_process = OnboardingProcess.objects.create(
        customer=customer,
        initiated_by=request.user,
        status='INITIATED'
    )
    
    # Log activity
    ActivityLog.objects.create(
        customer=customer,
        user=request.user,
        action="Started onboarding process",
        details="New customer onboarding process initiated."
    )
    
    messages.success(request, f"Onboarding process started for {customer.name}.")
    return redirect('comm_files:customer_detail', customer_id=customer.customer_id)

@login_required
def update_onboarding_status(request, process_id):
    """Update the status of an onboarding process"""
    process = get_object_or_404(OnboardingProcess, id=process_id)
    
    # Get required document types
    required_doc_types = DocumentType.objects.filter(required=True)
    
    if request.method == 'POST':
        new_status = request.POST.get('status')
        notes = request.POST.get('notes', '')
        
        if new_status not in [status[0] for status in OnboardingProcess.STATUS_CHOICES]:
            messages.error(request, "Invalid status selected.")
            return redirect('comm_files:customer_detail', customer_id=process.customer.customer_id)
        
        # Update process status
        process.update_status(new_status, notes)
        
        # Log activity
        ActivityLog.objects.create(
            customer=process.customer,
            user=request.user,
            action=f"Updated onboarding status to: {process.get_status_display()}",
            details=f"Status changed to {process.get_status_display()}. Notes: {notes}"
        )
        
        messages.success(request, f"Onboarding status updated to {process.get_status_display()}.")
        return redirect('comm_files:customer_detail', customer_id=process.customer.customer_id)
    
    context = {
        'process': process,
        'status_choices': OnboardingProcess.STATUS_CHOICES,
        'required_doc_types': required_doc_types
    }
    
    return render(request, 'comm_files/update_onboarding_status.html', context)

@login_required
def edit_customer(request, customer_id):
    """Edit an existing customer"""
    customer = get_object_or_404(Customer, customer_id=customer_id)
    
    if request.method == 'POST':
        form = CustomerForm(request.POST, instance=customer)
        if form.is_valid():
            form.save()
            
            # Log activity
            ActivityLog.objects.create(
                customer=customer,
                user=request.user,
                action="Updated customer",
                details=f"Customer {customer.name} ({customer.customer_id}) information was updated."
            )
            
            messages.success(request, f"Customer {customer.name} has been updated successfully.")
            return redirect('comm_files:customer_detail', customer_id=customer.customer_id)
    else:
        form = CustomerForm(instance=customer)
    
    context = {
        'form': form,
        'customer': customer,
        'is_edit': True
    }
    
    return render(request, 'comm_files/edit_customer.html', context)

# Document Type Management Views
@login_required
def document_type_list(request):
    """List all document types"""
    search = request.GET.get('search', '')
    
    doc_types = DocumentType.objects.all()
    
    # Apply search if provided
    if search:
        doc_types = doc_types.filter(
            Q(name__icontains=search) | 
            Q(description__icontains=search)
        )
    
    # Count documents for each type
    for doc_type in doc_types:
        doc_type.document_count = CustomerDocument.objects.filter(document_type=doc_type).count()
    
    # Pagination
    paginator = Paginator(doc_types, 20)  # 20 per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    context = {
        'page_obj': page_obj,
        'search': search,
    }
    
    return render(request, 'comm_files/document_type_list.html', context)

@login_required
def document_type_create(request):
    """Create a new document type"""
    if request.method == 'POST':
        form = DocumentTypeForm(request.POST)
        if form.is_valid():
            doc_type = form.save()
            messages.success(request, f"Document type '{doc_type.name}' has been created successfully.")
            return redirect('comm_files:document_type_list')
    else:
        form = DocumentTypeForm()
    
    context = {
        'form': form,
        'is_create': True
    }
    
    return render(request, 'comm_files/document_type_form.html', context)

@login_required
def document_type_edit(request, doc_type_id):
    """Edit an existing document type"""
    doc_type = get_object_or_404(DocumentType, id=doc_type_id)
    
    if request.method == 'POST':
        form = DocumentTypeForm(request.POST, instance=doc_type)
        if form.is_valid():
            form.save()
            messages.success(request, f"Document type '{doc_type.name}' has been updated successfully.")
            return redirect('comm_files:document_type_list')
    else:
        form = DocumentTypeForm(instance=doc_type)
    
    # Count how many customers use this document type
    usage_count = CustomerDocument.objects.filter(document_type=doc_type).count()
    
    context = {
        'form': form,
        'doc_type': doc_type,
        'is_edit': True,
        'usage_count': usage_count
    }
    
    return render(request, 'comm_files/document_type_form.html', context)

@login_required
def document_type_delete(request, doc_type_id):
    """Delete a document type"""
    doc_type = get_object_or_404(DocumentType, id=doc_type_id)
    
    # Check if the document type is in use
    usage_count = CustomerDocument.objects.filter(document_type=doc_type).count()
    
    if request.method == 'POST':
        if usage_count > 0:
            messages.error(request, f"Cannot delete '{doc_type.name}'. It is currently used by {usage_count} customer documents.")
        else:
            doc_type_name = doc_type.name
            doc_type.delete()
            messages.success(request, f"Document type '{doc_type_name}' has been deleted successfully.")
        return redirect('comm_files:document_type_list')
    
    context = {
        'doc_type': doc_type,
        'usage_count': usage_count,
    }
    
    return render(request, 'comm_files/document_type_delete.html', context)
