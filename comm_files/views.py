from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import HttpResponse, JsonResponse
from django.core.paginator import Paginator
from django.db.models import Q
from django.db import transaction
from .models import Customer, DocumentType, CustomerDocument, OnboardingProcess, ActivityLog
from .forms import CustomerForm, DocumentTypeForm
import pandas as pd
import io
from django.utils import timezone
import uuid

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

# Excel Import Views
@login_required
def import_customers_excel(request):
    """Import customers from Excel file"""
    if request.method == 'POST':
        if 'excel_file' not in request.FILES:
            messages.error(request, "No file was uploaded. Please select an Excel file.")
            return render(request, 'comm_files/import_customers.html')
            
        excel_file = request.FILES['excel_file']
        
        # Validate file type
        if not excel_file.name.endswith(('.xlsx', '.xls')):
            messages.error(request, "Please upload a valid Excel file (.xlsx or .xls)")
            return render(request, 'comm_files/import_customers.html')
        
        try:
            # Read Excel file
            df = pd.read_excel(excel_file)
            
            # Clean column names (remove extra spaces, convert to lowercase)
            df.columns = df.columns.str.strip().str.lower().str.replace(' ', '_')
            
            # Define column mapping from Excel to model fields
            column_mapping = {
                'account_number': 'account_number',
                'region': 'region', 
                'district': 'district',
                'depot': 'depot',
                'customer_name': 'name',
                'address': 'address',
                'suburb': 'suburb',
                'tariff_description': 'tariff_description',
                'supply_point_number': 'supply_point_number',
                'status': 'status',
                'meter_number': 'meter_number',
                'customer_id': 'customer_id',
                'contact': 'contact_number',
                'email_address': 'email',
                'pjob': 'pjob'
            }
            
            # Process import statistics
            total_rows = len(df)
            successful_imports = 0
            failed_imports = 0
            updated_records = 0
            errors = []
            
            with transaction.atomic():
                for index, row in df.iterrows():
                    try:
                        # Extract customer data from row
                        customer_data = {}
                        
                        # Map Excel columns to model fields
                        for excel_col, model_field in column_mapping.items():
                            if excel_col in df.columns:
                                value = row[excel_col]
                                # Convert NaN to None
                                if pd.isna(value):
                                    value = None
                                elif isinstance(value, str):
                                    value = value.strip()
                                    if value == '':
                                        value = None
                                customer_data[model_field] = value
                        
                        # Generate a unique customer_id if missing
                        if not customer_data.get('customer_id'):
                            # Generate a unique code: CUST-<8char_random>
                            unique_code = f"CUST-{uuid.uuid4().hex[:8].upper()}"
                            customer_data['customer_id'] = unique_code
                        
                        if not customer_data.get('name'):
                            errors.append(f"Row {index + 2}: Missing customer name") 
                            failed_imports += 1
                            continue
                        
                        # Handle status mapping
                        status_value = customer_data.get('status', '').upper() if customer_data.get('status') else 'ACTIVE'
                        if status_value not in [choice[0] for choice in Customer.STATUS_CHOICES]:
                            customer_data['status'] = 'ACTIVE'  # Default to active if invalid
                        else:
                            customer_data['status'] = status_value
                        
                        # Set is_active based on status
                        customer_data['is_active'] = customer_data['status'] == 'ACTIVE'
                        
                        # Check if customer already exists (only if customer_id was provided in the file)
                        existing_customer = None
                        if 'customer_id' in row and row['customer_id'] and not pd.isna(row['customer_id']):
                            existing_customer = Customer.objects.filter(
                                customer_id=row['customer_id']
                            ).first()
                        
                        if existing_customer:
                            # Update existing customer
                            for field, value in customer_data.items():
                                if value is not None:  # Only update non-null values
                                    setattr(existing_customer, field, value)
                            existing_customer.save()
                            
                            # Log activity
                            ActivityLog.objects.create(
                                customer=existing_customer,
                                user=request.user,
                                action="Updated customer via Excel import",
                                details=f"Customer {existing_customer.name} updated from Excel import."
                            )
                            
                            updated_records += 1
                        else:
                            # Create new customer
                            new_customer = Customer.objects.create(**customer_data)
                            
                            # Log activity
                            ActivityLog.objects.create(
                                customer=new_customer,
                                user=request.user,
                                action="Created customer via Excel import",
                                details=f"New customer {new_customer.name} created from Excel import."
                            )
                            
                            successful_imports += 1
                            
                    except Exception as e:
                        errors.append(f"Row {index + 2}: {str(e)}")
                        failed_imports += 1
                        continue
            
            # Prepare success message
            messages.success(request, 
                f"Import completed! Created: {successful_imports}, Updated: {updated_records}, Failed: {failed_imports} out of {total_rows} total rows.")
            
            # Show errors if any
            if errors:
                error_message = "Errors encountered:\n" + "\n".join(errors[:10])  # Show first 10 errors
                if len(errors) > 10:
                    error_message += f"\n... and {len(errors) - 10} more errors."
                messages.warning(request, error_message)
            
            return redirect('comm_files:customer_list')
            
        except Exception as e:
            messages.error(request, f"Error processing Excel file: {str(e)}")
            return render(request, 'comm_files/import_customers.html')
    
    # Show expected columns for reference
    expected_columns = [
        'ACCOUNT NUMBER', 'REGION', 'DISTRICT', 'DEPOT', 'CUSTOMER NAME',
        'ADDRESS', 'SUBURB', 'TARIFF DESCRIPTION', 'SUPPLY POINT NUMBER',
        'STATUS', 'METER NUMBER', 'CUSTOMER ID', 'CONTACT', 'EMAIL ADDRESS', 'PJOB'
    ]
    
    context = {
        'expected_columns': expected_columns
    }
    
    return render(request, 'comm_files/import_customers.html', context)

@login_required
def download_sample_excel(request):
    """Download a sample Excel template for customer import"""
    # Create sample data
    sample_data = {
        'ACCOUNT NUMBER': ['1268810', '1130373'],
        'REGION': ['HARARE', 'HARARE'],
        'DISTRICT': ['SOUTH', 'SOUTH'],
        'DEPOT': ['GLENVIEW DEPOT', 'GLENVIEW DEPOT'],
        'CUSTOMER NAME': ['Client Name', 'Client Two'],
        'ADDRESS': ['99999 B54 UNKNOWN', '99999 B1576 UNKNOWN'],
        'SUBURB': ['UNKNOWN', 'UNKNOWN'],
        'TARIFF DESCRIPTION': ['AGRICULTURAL', 'AGRICULTURAL'],
        'SUPPLY POINT NUMBER': ['1269077', '1130389'],
        'STATUS': ['ACTIVE', 'ACTIVE'],
        'METER NUMBER': ['101316', '303230'],
        'CUSTOMER ID': ['CUST001', 'CUST002'],
        'CONTACT': ['263123456789', '263987654321'],
        'EMAIL ADDRESS': ['client@email.com', 'client2@email.com'],
        'PJOB': ['PROJECT001', 'PROJECT002']
    }
    
    # Create DataFrame
    df = pd.DataFrame(sample_data)
    
    # Create Excel file in memory
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = 'attachment; filename="customer_import_template.xlsx"'
    
    # Write to Excel
    with pd.ExcelWriter(response, engine='openpyxl') as writer:
        df.to_excel(writer, sheet_name='Customer Data', index=False)
        
        # Get the workbook and worksheet
        workbook = writer.book
        worksheet = writer.sheets['Customer Data']
        
        # Auto-adjust column widths
        for column in worksheet.columns:
            max_length = 0
            column_letter = column[0].column_letter
            for cell in column:
                try:
                    if len(str(cell.value)) > max_length:
                        max_length = len(str(cell.value))
                except:
                    pass
            adjusted_width = (max_length + 2)
            worksheet.column_dimensions[column_letter].width = adjusted_width
    
    return response

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
