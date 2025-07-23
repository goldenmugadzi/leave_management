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
from approve.models import Approval


@login_required
def list_view(request):
    """
    Display a list of all Sanction For Test forms with filtering and pagination
    """
    try:
        sanction_forms = SanctionForTestForm.objects.all()
        
        # Apply filters based on user permissions and region/district
        if hasattr(request.user, 'userprofile'):
            profile = request.user.userprofile
            if profile.region:
                sanction_forms = sanction_forms.filter(region=profile.region)
            if profile.district:
                sanction_forms = sanction_forms.filter(district=profile.district)
        
        # Search functionality
        search_query = request.GET.get('search')
        if search_query:
            sanction_forms = sanction_forms.filter(
                Q(form_no__icontains=search_query) |
                Q(work_to_be_carried_out__icontains=search_query) |
                Q(created_by__username__icontains=search_query)
            )
        
        # Filter by status
        status_filter = request.GET.get('status')
        if status_filter:
            sanction_forms = sanction_forms.filter(status=status_filter)
        
        # Filter by priority
        priority_filter = request.GET.get('priority')
        if priority_filter:
            sanction_forms = sanction_forms.filter(priority=priority_filter)
        
        # Order by creation date (newest first)
        sanction_forms = sanction_forms.order_by('-created_at')
        
        # Pagination
        paginator = Paginator(sanction_forms, 25)  # Show 25 forms per page
        page_number = request.GET.get('page')
        page_obj = paginator.get_page(page_number)
        
        # Get status choices for filter dropdown
        status_choices = SanctionForTestForm.STATUS_CHOICES
        priority_choices = SanctionForTestForm.PRIORITY_CHOICES
        
        context = {
            'page_obj': page_obj,
            'search_query': search_query,
            'status_filter': status_filter,
            'priority_filter': priority_filter,
            'status_choices': status_choices,
            'priority_choices': priority_choices,
        }
        
        return render(request, 'sanction_for_test/list.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading sanction forms: {str(e)}")
        return render(request, 'sanction_for_test/list.html', {'page_obj': None})


@login_required
def create_view(request):
    """
    Create a new Sanction For Test form
    """
    try:
        if request.method == 'POST':
            form = SanctionForTestFormForm(request.POST, user=request.user)
            if form.is_valid():
                with transaction.atomic():
                    sanction_form = form.save(commit=False)
                    sanction_form.created_by = request.user
                    sanction_form.save()
                    
                    # Create approval workflow for the form
                    create_workflow_for_sanction(sanction_form)
                    
                    # Log the creation
                    SanctionFormAuditLog.objects.create(
                        form=sanction_form,
                        user=request.user,
                        action='created',
                        description=f'Form {sanction_form.form_no} created',
                        new_status=sanction_form.status,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, f'Sanction Form {sanction_form.form_no} created successfully!')
                    return redirect('sanction_for_test:detail', pk=sanction_form.pk)
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = SanctionForTestFormForm(user=request.user)
        
        context = {
            'form': form,
            'title': 'Create New Sanction For Test Form'
        }
        
        return render(request, 'sanction_for_test/create.html', context)
        
    except Exception as e:
        messages.error(request, f"Error creating sanction form: {str(e)}")
        return redirect('sanction_for_test:list')


@login_required
def detail_view(request, pk):
    """
    Display detailed view of a specific Sanction For Test form
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        
        # Check if user has permission to view this form
        can_view = (
            request.user == sanction_form.created_by or
            request.user.has_perm('sanction_for_test.view_sanctionfortestform') or
            (hasattr(request.user, 'userprofile') and request.user.userprofile.region == sanction_form.region)
        )
        
        if not can_view:
            messages.error(request, "You don't have permission to view this form.")
            return redirect('sanction_for_test:list')
        
        # Get approval process status
        approvals = []
        pending_approval = None
        
        if sanction_form.approval_process:
            approvals = Approval.objects.filter(process=sanction_form.approval_process).order_by('step__order')
            pending_approval = approvals.filter(approved__isnull=True).first()
        
        # Get comments and attachments
        comments = sanction_form.comments.all().order_by('-created_at')
        attachments = sanction_form.attachments.all().order_by('-uploaded_at')
        
        # Forms for actions
        comment_form = SanctionFormCommentForm()
        attachment_form = SanctionFormAttachmentForm()
        status_form = SanctionFormStatusUpdateForm(current_status=sanction_form.status)
        approval_form = ApprovalActionForm()
        
        context = {
            'sanction_form': sanction_form,
            'approvals': approvals,
            'pending_approval': pending_approval,
            'comments': comments,
            'attachments': attachments,
            'comment_form': comment_form,
            'attachment_form': attachment_form,
            'status_form': status_form,
            'approval_form': approval_form,
            'can_edit': sanction_form.status in ['draft', 'pending'] and request.user == sanction_form.created_by,
            'can_approve': pending_approval and request.user == pending_approval.step.role.user_set.first(),
        }
        
        return render(request, 'sanction_for_test/detail.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading sanction form: {str(e)}")
        return redirect('sanction_for_test:list')


@login_required
def edit_view(request, pk):
    """
    Edit an existing Sanction For Test form
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        
        # Check if user can edit this form
        can_edit = (
            request.user == sanction_form.created_by and 
            sanction_form.status in ['draft', 'pending']
        )
        
        if not can_edit:
            messages.error(request, "You don't have permission to edit this form.")
            return redirect('sanction_for_test:detail', pk=pk)
        
        if request.method == 'POST':
            form = SanctionForTestFormForm(request.POST, instance=sanction_form, user=request.user)
            if form.is_valid():
                with transaction.atomic():
                    updated_form = form.save()
                    
                    # Log the modification
                    SanctionFormAuditLog.objects.create(
                        form=updated_form,
                        user=request.user,
                        action='modified',
                        description=f'Form {updated_form.form_no} modified',
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
                    
                    messages.success(request, f'Sanction Form {updated_form.form_no} updated successfully!')
                    return redirect('sanction_for_test:detail', pk=updated_form.pk)
            else:
                messages.error(request, 'Please correct the errors below.')
        else:
            form = SanctionForTestFormForm(instance=sanction_form, user=request.user)
        
        context = {
            'form': form,
            'sanction_form': sanction_form,
            'title': f'Edit Sanction Form {sanction_form.form_no}'
        }
        
        return render(request, 'sanction_for_test/create.html', context)
        
    except Exception as e:
        messages.error(request, f"Error editing sanction form: {str(e)}")
        return redirect('sanction_for_test:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def delete_view(request, pk):
    """
    Delete a Sanction For Test form
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        
        # Check if user can delete this form
        can_delete = (
            request.user == sanction_form.created_by and 
            sanction_form.status == 'draft'
        )
        
        if not can_delete:
            messages.error(request, "You can only delete forms in draft status that you created.")
            return redirect('sanction_for_test:detail', pk=pk)
        
        form_no = sanction_form.form_no
        sanction_form.delete()
        
        messages.success(request, f'Sanction Form {form_no} deleted successfully!')
        return redirect('sanction_for_test:list')
        
    except Exception as e:
        messages.error(request, f"Error deleting sanction form: {str(e)}")
        return redirect('sanction_for_test:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def update_status(request, pk):
    """
    Update the status of a Sanction For Test form
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        form = SanctionFormStatusUpdateForm(request.POST, current_status=sanction_form.status)
        
        if form.is_valid():
            old_status = sanction_form.status
            new_status = form.cleaned_data['status']
            comment = form.cleaned_data.get('comment', '')
            
            with transaction.atomic():
                sanction_form.status = new_status
                sanction_form.save()
                
                # Log the status change
                SanctionFormAuditLog.objects.create(
                    form=sanction_form,
                    user=request.user,
                    action='status_changed',
                    description=f'Status changed from {old_status} to {new_status}. {comment}',
                    previous_status=old_status,
                    new_status=new_status,
                    ip_address=request.META.get('REMOTE_ADDR'),
                    user_agent=request.META.get('HTTP_USER_AGENT', '')
                )
                
                messages.success(request, f'Status updated to {new_status}')
        else:
            messages.error(request, 'Invalid status update')
        
        return redirect('sanction_for_test:detail', pk=pk)
        
    except Exception as e:
        messages.error(request, f"Error updating status: {str(e)}")
        return redirect('sanction_for_test:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def add_comment(request, pk):
    """
    Add a comment to a Sanction For Test form
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        form = SanctionFormCommentForm(request.POST)
        
        if form.is_valid():
            comment = form.save(commit=False)
            comment.form = sanction_form
            comment.user = request.user
            comment.save()
            
            # Log the comment addition
            SanctionFormAuditLog.objects.create(
                form=sanction_form,
                user=request.user,
                action='comment_added',
                description=f'Comment added: {comment.comment[:50]}...',
                ip_address=request.META.get('REMOTE_ADDR'),
                user_agent=request.META.get('HTTP_USER_AGENT', '')
            )
            
            messages.success(request, 'Comment added successfully!')
        else:
            messages.error(request, 'Error adding comment')
        
        return redirect('sanction_for_test:detail', pk=pk)
        
    except Exception as e:
        messages.error(request, f"Error adding comment: {str(e)}")
        return redirect('sanction_for_test:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def add_attachment(request, pk):
    """
    Add an attachment to a Sanction For Test form
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        form = SanctionFormAttachmentForm(request.POST, request.FILES)
        
        if form.is_valid():
            attachment = form.save(commit=False)
            attachment.form = sanction_form
            attachment.uploaded_by = request.user
            attachment.save()
            
            messages.success(request, 'Attachment uploaded successfully!')
        else:
            messages.error(request, 'Error uploading attachment')
        
        return redirect('sanction_for_test:detail', pk=pk)
        
    except Exception as e:
        messages.error(request, f"Error uploading attachment: {str(e)}")
        return redirect('sanction_for_test:detail', pk=pk)


@login_required
@require_http_methods(["POST"])
def approve_action(request, pk):
    """
    Handle approval actions (approve, reject, request changes)
    """
    try:
        sanction_form = get_object_or_404(SanctionForTestForm, pk=pk)
        form = ApprovalActionForm(request.POST)
        
        if form.is_valid() and sanction_form.approval_process:
            action = form.cleaned_data['action']
            comment = form.cleaned_data['comment']
            
            # Find the pending approval for this user
            pending_approval = Approval.objects.filter(
                process=sanction_form.approval_process,
                approved__isnull=True,
                step__role__user_set=request.user
            ).first()
            
            if pending_approval:
                with transaction.atomic():
                    if action == 'approve':
                        pending_approval.approved = True
                        pending_approval.comment = comment
                        pending_approval.approved_at = timezone.now()
                        pending_approval.save()
                        
                        # Check if all approvals are complete
                        all_approved = not Approval.objects.filter(
                            process=sanction_form.approval_process,
                            approved__isnull=True
                        ).exists()
                        
                        if all_approved:
                            sanction_form.status = 'approved'
                            sanction_form.save()
                            
                        messages.success(request, 'Form approved successfully!')
                        
                    elif action == 'reject':
                        pending_approval.approved = False
                        pending_approval.comment = comment
                        pending_approval.approved_at = timezone.now()
                        pending_approval.save()
                        
                        sanction_form.status = 'rejected'
                        sanction_form.save()
                        
                        messages.success(request, 'Form rejected.')
                        
                    elif action == 'request_changes':
                        sanction_form.status = 'pending'
                        sanction_form.save()
                        
                        # Add comment about requested changes
                        SanctionFormComment.objects.create(
                            form=sanction_form,
                            user=request.user,
                            comment=f"Changes requested: {comment}",
                            is_private=False
                        )
                        
                        messages.success(request, 'Changes requested.')
                    
                    # Log the approval action
                    SanctionFormAuditLog.objects.create(
                        form=sanction_form,
                        user=request.user,
                        action=f'approval_{action}',
                        description=f'Approval {action}: {comment}',
                        approval_step=pending_approval.step.name if pending_approval else None,
                        ip_address=request.META.get('REMOTE_ADDR'),
                        user_agent=request.META.get('HTTP_USER_AGENT', '')
                    )
            else:
                messages.error(request, 'No pending approval found for you.')
        else:
            messages.error(request, 'Invalid approval action')
        
        return redirect('sanction_for_test:detail', pk=pk)
        
    except Exception as e:
        messages.error(request, f"Error processing approval: {str(e)}")
        return redirect('sanction_for_test:detail', pk=pk)


@login_required
def reports_view(request):
    """
    Display reports and statistics for Sanction For Test forms
    """
    try:
        # Get all forms with optional filtering
        sanction_forms = SanctionForTestForm.objects.all()
        
        # Apply region/district filtering based on user profile
        if hasattr(request.user, 'userprofile'):
            profile = request.user.userprofile
            if profile.region:
                sanction_forms = sanction_forms.filter(region=profile.region)
            if profile.district:
                sanction_forms = sanction_forms.filter(district=profile.district)
        
        # Calculate statistics
        total_forms = sanction_forms.count()
        draft_count = sanction_forms.filter(status='draft').count()
        pending_count = sanction_forms.filter(status='pending').count()
        approved_count = sanction_forms.filter(status='approved').count()
        rejected_count = sanction_forms.filter(status='rejected').count()
        completed_count = sanction_forms.filter(status='completed').count()
        
        # Group by priority
        high_priority = sanction_forms.filter(priority='high').count()
        critical_priority = sanction_forms.filter(priority='critical').count()
        
        # Group by risk level
        high_risk = sanction_forms.filter(risk_level='high').count()
        extreme_risk = sanction_forms.filter(risk_level='extreme').count()
        
        # Recent forms (last 30 days)
        from datetime import timedelta
        thirty_days_ago = timezone.now() - timedelta(days=30)
        recent_forms = sanction_forms.filter(created_at__gte=thirty_days_ago).count()
        
        context = {
            'total_forms': total_forms,
            'draft_count': draft_count,
            'pending_count': pending_count,
            'approved_count': approved_count,
            'rejected_count': rejected_count,
            'completed_count': completed_count,
            'high_priority': high_priority,
            'critical_priority': critical_priority,
            'high_risk': high_risk,
            'extreme_risk': extreme_risk,
            'recent_forms': recent_forms,
            'sanction_forms': sanction_forms[:20],  # Latest 20 forms for table
        }
        
        return render(request, 'sanction_for_test/reports.html', context)
        
    except Exception as e:
        messages.error(request, f"Error loading reports: {str(e)}")
        return render(request, 'sanction_for_test/reports.html', {
            'error': str(e)
        })
