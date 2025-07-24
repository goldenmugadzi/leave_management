from django.shortcuts import render, redirect, get_object_or_404
from django.contrib import messages
from django.contrib.auth.decorators import login_required, permission_required
from django.core.paginator import Paginator
from django.db import transaction
from django.http import JsonResponse
from django.utils import timezone
from django.views.decorators.http import require_http_methods
from django.db.models import Q
from .models import (
    SanctionForTestForm, SanctionFormAuditLog, 
    SanctionFormComment, SanctionFormAttachment
)
from .forms import (
    SanctionForTestFormForm, SanctionFormCommentForm, 
    SanctionFormAttachmentForm, SanctionFormStatusUpdateForm,
    ApprovalActionForm
)
from .signals import create_workflow_for_sanction
from it.users.models import UserProfile, Notification


@login_required
def sanction_list(request):
    """
    Display list of all Sanction For Test forms with filtering and pagination
    """
    try:
        # Base queryset with optimized joins
        forms_list = SanctionForTestForm.objects.select_related(
            'created_by', 'region', 'district', 'section', 'depot', 'cost_center'
        ).order_by('-created_at')
        
        # Filter by user's region if not superuser
        if not request.user.is_superuser and hasattr(request.user, 'region') and request.user.region:
            forms_list = forms_list.filter(region=request.user.region)
        
        # Filter by status if provided
        status_filter = request.GET.get('status')
        if status_filter:
            forms_list = forms_list.filter(status=status_filter)
        
        # Filter by priority if provided
        priority_filter = request.GET.get('priority')
        if priority_filter:
            forms_list = forms_list.filter(priority=priority_filter)
        
        # Filter by risk level if provided
        risk_filter = request.GET.get('risk_level')
        if risk_filter:
            forms_list = forms_list.filter(risk_level=risk_filter)
        
        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            forms_list = forms_list.filter(
                Q(form_no__icontains=search_query) |
                Q(work_to_be_carried_out__icontains=search_query) |
                Q(plant_or_equipment_to_be_tested__icontains=search_query) |
                Q(created_by__first_name__icontains=search_query) |
                Q(created_by__last_name__icontains=search_query) |
                Q(created_by__username__icontains=search_query)
            )
        
        # Pagination
        paginator = Paginator(forms_list, 25)  # Show 25 forms per page
        page_number = request.GET.get('page')
        forms = paginator.get_page(page_number)
        
        # Get filter choices
        status_choices = SanctionForTestForm.STATUS_CHOICES
        priority_choices = SanctionForTestForm.PRIORITY_CHOICES
        risk_choices = SanctionForTestForm.RISK_LEVEL_CHOICES
        
        context = {
            'forms': forms,
            'status_choices': status_choices,
            'priority_choices': priority_choices,
            'risk_choices': risk_choices,
            'current_status': status_filter,
            'current_priority': priority_filter,
            'current_risk': risk_filter,
            'search_query': search_query,
        }
        
        return render(request, 'sanction_for_test/list.html', context)
        
    except Exception as e:
        messages.error(request, f"An error occurred while loading forms: {str(e)}")
        return render(request, 'sanction_for_test/list.html', {'forms': []})


@login_required
@permission_required('sanction_for_test.add_sanctionfortestform', raise_exception=True)
def create_sanction_form(request):
    """
    Create a new Sanction For Test form
    """
    if request.method == 'POST':
        form = SanctionForTestFormForm(request.POST, user=request.user)
        try:
            if form.is_valid():
                with transaction.atomic():
                    sanction_form = form.save(commit=False)
                    sanction_form.created_by = request.user
                    sanction_form.save()
                    
                    # Create workflow if enabled
                    try:
                        create_workflow_for_sanction(sanction_form)
                    except Exception as e:
                        print(f"Failed to create workflow: {e}")
                    
                    # Create notification for relevant users
                    try:
                        notify_users = sanction_form.get_notification_users()
                        for user in notify_users:
                            if user != request.user:  # Don't notify creator
                                Notification.objects.create(
                                    user=user,
                                    message=f"New Sanction Form {sanction_form.form_no} created",
                                    url=f"/sanction_for_test/detail/{sanction_form.pk}/",
                                    notification_type="sanction_created",
                                    notification_id=str(sanction_form.pk)
                                )
                    except Exception as e:
                        print(f"Failed to create notifications: {e}")
                    
                    messages.success(request, f"Sanction For Test form {sanction_form.form_no} created successfully!")
                    return redirect('sanction_for_test:detail', pk=sanction_form.pk)
            else:
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                
        except Exception as e:
            messages.error(request, f"An error occurred while creating the form: {str(e)}")
    else:
        form = SanctionForTestFormForm(user=request.user)
    
    return render(request, 'sanction_for_test/create.html', {'form': form})


@login_required
def detail_sanction_form(request, pk):
    """
    Display detailed view of a Sanction For Test form
    """
    try:
        sanction_form = get_object_or_404(
            SanctionForTestForm.objects.select_related(
                'created_by', 'region', 'district', 'section', 'depot', 'cost_center',
                'declaration_responsible_official_signer',
                'receipt_signer', 'clearance_signer', 'cancellation_controller_signer',
                'post_cancellation_responsible_official_signer'
            ).prefetch_related(
                'declaration_responsible_official_entries__signature_entry',
                'receipt_entries__signature_entry',
                'clearance_entries__signature_entry',
                'cancellation_entries__signature_entry',
                'post_cancellation_declaration_entries__signature_entry',
                'comments__user',
                'attachments',
                'audit_logs__user'
            ),
            pk=pk
        )
        
        # Check access permissions based on region/section
        can_view = (
            request.user.is_superuser or
            request.user == sanction_form.created_by or
            request.user.has_perm('sanction_for_test.view_sanctionfortestform') or
            (hasattr(request.user, 'region') and request.user.region == sanction_form.region) or
            (hasattr(request.user, 'section') and request.user.section == sanction_form.section)
        )
        
        if not can_view:
            messages.error(request, "You don't have permission to view this form.")
            return redirect('sanction_for_test:list')
        
        # Initialize quick action form for status changes
        quick_action_form = QuickActionForm()
        
        # Get related entries for display
        declaration_entries = sanction_form.declaration_responsible_official_entries.all()
        next_action = sanction_form.get_next_required_action()
        
        context = {
            'sanction_form': sanction_form,
            'quick_action_form': quick_action_form,
            'declaration_entries': declaration_entries,
            'next_action': next_action,
            'can_edit': sanction_form.is_editable and (
                request.user == sanction_form.created_by or 
                request.user.has_perm('sanction_for_test.change_sanctionfortestform')
            ),
            'can_delete': (
                request.user.has_perm('sanction_for_test.delete_sanctionfortestform') and
                sanction_form.status == 'draft'
            ),
        }
        
        return render(request, 'sanction_for_test/detail.html', context)
        
    except Exception as e:
        messages.error(request, f"An error occurred while loading the form: {str(e)}")
        return redirect('sanction_for_test:list')


@login_required
@permission_required('sanction_for_test.change_sanctionfortestform', raise_exception=True)
def edit_sanction_form(request, pk):
    """
    Edit an existing Sanction For Test form
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        
        # Check if form can be edited
        if not sanction_form.is_editable:
            messages.warning(request, f"Form {sanction_form.form_no} cannot be edited in its current status.")
            return redirect('sanction_for_test:detail', pk=pk)
        
        if request.method == 'POST':
            form = SanctionForTestFormForm(request.POST, instance=sanction_form, user=request.user)
            try:
                if form.is_valid():
                    with transaction.atomic():
                        form.save()
                        messages.success(request, f"Form {sanction_form.form_no} updated successfully!")
                        return redirect('sanction_for_test:detail', pk=pk)
                else:
                    messages.error(request, "Please correct the errors below.")
                    
            except Exception as e:
                messages.error(request, f"An error occurred while updating the form: {str(e)}")
        else:
            form = SanctionForTestFormForm(instance=sanction_form, user=request.user)
        
        context = {
            'form': form,
            'sanction_form': sanction_form,
            'is_edit': True,
        }
        
        return render(request, 'sanction_for_test/create.html', context)
        
    except Exception as e:
        messages.error(request, f"An error occurred while loading the form for editing: {str(e)}")
        return redirect('sanction_for_test:list')


@login_required
@require_http_methods(["POST"])
def quick_action(request, pk):
    """
    Handle quick actions on Sanction For Test forms (issue, receive, clear, cancel, complete)
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        form = QuickActionForm(request.POST)
        
        if form.is_valid():
            action = form.cleaned_data['action']
            comment = form.cleaned_data.get('comment', '')
            signature_name = form.cleaned_data.get('signature_name', '')
            
            with transaction.atomic():
                # Create signature entry if needed
                signature_entry = None
                if signature_name:
                    signature_entry = SignatureEntry.objects.create(
                        user=request.user,
                        name=signature_name,
                        date=timezone.now().date(),
                        time=timezone.now().time()
                    )
                
                # Process the action
                success_message = process_form_action(sanction_form, action, signature_entry, comment)
                
                if success_message:
                    messages.success(request, success_message)
                else:
                    messages.error(request, f"Invalid action '{action}' for current form status.")
                    
        else:
            for field, errors in form.errors.items():
                for error in errors:
                    messages.error(request, f"{field}: {error}")
    
    except Exception as e:
        messages.error(request, f"An error occurred while processing the action: {str(e)}")
    
    return redirect('sanction_for_test:detail', pk=pk)


def process_form_action(sanction_form, action, signature_entry, comment):
    """
    Process form status change actions with proper validation
    """
    status_transitions = {
        'issue': {'from_status': 'draft', 'to_status': 'issued', 'signature_field': 'declaration_responsible_official_signer'},
        'receive': {'from_status': 'issued', 'to_status': 'received', 'signature_field': 'receipt_signer'},
        'clear': {'from_status': 'received', 'to_status': 'cleared', 'signature_field': 'clearance_signer'},
        'cancel': {'from_status': ['issued', 'received'], 'to_status': 'cancelled', 'signature_field': 'cancellation_controller_signer'},
        'complete': {'from_status': 'cleared', 'to_status': 'completed', 'signature_field': None},
    }
    
    if action not in status_transitions:
        return None
    
    transition = status_transitions[action]
    from_status = transition['from_status']
    
    # Check if current status allows this transition
    if isinstance(from_status, list):
        if sanction_form.status not in from_status:
            return None
    else:
        if sanction_form.status != from_status:
            return None
    
    # Update form status
    sanction_form.status = transition['to_status']
    
    # Add signature if required
    if transition['signature_field'] and signature_entry:
        setattr(sanction_form, transition['signature_field'], signature_entry)
    
    # Add comment/reason for cancellation
    if action == 'cancel' and comment:
        sanction_form.cancellation_reason = comment
    
    sanction_form.save()
    
    # Return success message
    action_messages = {
        'issue': f"Form {sanction_form.form_no} issued successfully!",
        'receive': f"Form {sanction_form.form_no} received successfully!",
        'clear': f"Form {sanction_form.form_no} cleared successfully!",
        'cancel': f"Form {sanction_form.form_no} cancelled successfully!",
        'complete': f"Form {sanction_form.form_no} completed successfully!",
    }
    
    return action_messages.get(action)


@login_required
@permission_required('sanction_for_test.delete_sanctionfortestform', raise_exception=True)
def delete_sanction_form(request, pk):
    """
    Delete a Sanction For Test form
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        
        if request.method == 'POST':
            form_no = sanction_form.form_no
            
            # Check if form can be deleted (only drafts should be deletable)
            if sanction_form.status != 'draft':
                messages.warning(request, f"Form {form_no} cannot be deleted as it has been processed.")
                return redirect('sanction_for_test:detail', pk=pk)
            
            with transaction.atomic():
                sanction_form.delete()
                messages.success(request, f"Form {form_no} deleted successfully!")
                return redirect('sanction_for_test:list')
        
        context = {
            'sanction_form': sanction_form,
        }
        
        return render(request, 'sanction_for_test/delete_confirm.html', context)
        
    except Exception as e:
        messages.error(request, f"An error occurred while deleting the form: {str(e)}")
        return redirect('sanction_for_test:list')


@login_required
def ajax_form_status(request, pk):
    """
    AJAX endpoint to get current form status and available actions
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        
        available_actions = []
        if sanction_form.status == 'draft':
            available_actions.append('issue')
        elif sanction_form.status == 'issued':
            available_actions.extend(['receive', 'cancel'])
        elif sanction_form.status == 'received':
            available_actions.extend(['clear', 'cancel'])
        elif sanction_form.status == 'cleared':
            available_actions.append('complete')
        
        data = {
            'status': sanction_form.status,
            'status_display': sanction_form.get_status_display(),
            'next_action': sanction_form.get_next_required_action(),
            'available_actions': available_actions,
            'is_editable': sanction_form.is_editable,
            'can_be_cancelled': sanction_form.can_be_cancelled,
        }
        
        return JsonResponse(data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
