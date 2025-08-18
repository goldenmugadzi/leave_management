from django.db.models.signals import post_save, pre_save
from django.dispatch import receiver
from .models import SanctionForTestForm, SanctionFormAuditLog
from it.users.models import Notification
from approve.models import Approval


@receiver(pre_save, sender=SanctionForTestForm)
def capture_status_change(sender, instance, **kwargs):
    """Capture status changes for audit logging"""
    if instance.pk:
        try:
            old_instance = sender.objects.get(pk=instance.pk)
            instance._old_status = old_instance.status
        except sender.DoesNotExist:
            instance._old_status = None
    else:
        instance._old_status = None


@receiver(post_save, sender=SanctionForTestForm)
def log_sanction_form_changes(sender, instance, created, **kwargs):
    """Automatically log all changes to sanction forms"""
    
    # Determine the action
    if created:
        action = 'created'
        description = f"Sanction form {instance.form_no} created"
    else:
        old_status = getattr(instance, '_old_status', None)
        if old_status and old_status != instance.status:
            action = instance.status
            description = f"Status changed from {old_status} to {instance.status}"
        else:
            action = 'modified'
            description = f"Sanction form {instance.form_no} modified"
    
    # Create audit log entry
    SanctionFormAuditLog.objects.create(
        form=instance,
        user=instance.created_by,  # This could be improved to track actual modifier
        action=action,
        description=description,
        previous_status=getattr(instance, '_old_status', None),
        new_status=instance.status,
    )
    
    # Send notifications for status changes
    if not created and hasattr(instance, '_old_status') and instance._old_status != instance.status:
        notify_users = instance.get_notification_users()
        for user in notify_users:
            try:
                Notification.objects.create(
                    user=user,
                    message=f"Sanction Form {instance.form_no} status changed to {instance.get_status_display()}",
                    url=f"/sanction_for_test/detail/{instance.pk}/",
                    notification_type="sanction_status_change",
                    notification_id=str(instance.pk)
                )
            except Exception as e:
                # Log the error but don't fail the save operation
                print(f"Failed to create notification for user {user}: {e}")


@receiver(post_save, sender=Approval)
def handle_approval_completed(sender, instance, created, **kwargs):
    """Handle when an approval is completed in the workflow"""
    if not created or not instance.approved:
        return
    
    # Check if this approval is for a sanction form
    try:
        # First check if the process has the right workflow type
        if not instance.process or not instance.process.workflow:
            return
            
        # Only handle sanction workflows
        if instance.process.workflow.application.name != 'sanction_for_test':
            return
            
        sanction_form = SanctionForTestForm.objects.get(approval_process=instance.process)
        
        # Update form status based on the approval step
        step_status_mapping = {
            1: 'issued',    # Declaration by Responsible Official
            2: 'received',  # Receipt
            3: 'cleared',   # Clearance
            4: 'cancelled', # Cancellation
        }
        
        new_status = step_status_mapping.get(instance.step.step)
        if new_status and sanction_form.status != new_status:
            old_status = sanction_form.status
            sanction_form.status = new_status
            sanction_form.save()
            
            # Log the approval action
            SanctionFormAuditLog.objects.create(
                form=sanction_form,
                user=instance.user,
                action='approved',
                description=f"Step {instance.step.step} approved by {instance.user}",
                previous_status=old_status,
                new_status=new_status,
                approval_step=instance.step.step
            )
            
    except SanctionForTestForm.DoesNotExist:
        # This approval is not for a sanction form - this is normal for ACE approvals
        pass
    except Exception as e:
        # Handle database errors (like missing table) gracefully
        print(f"Sanction signal handler error: {e}")
        pass


def create_workflow_for_sanction(form, workflow_name="Sanction For Test Approval"):
    """
    Create an approval workflow process for a sanction form
    """
    try:
        from approve.models import Workflow, Process, Application
        
        # Get or create the application
        app, created = Application.objects.get_or_create(
            name='sanction_for_test',
            defaults={'fullname': 'Sanction For Test'}
        )
        
        # Get or create the workflow
        workflow, created = Workflow.objects.get_or_create(
            name=workflow_name,
            defaults={'application': app}
        )
        
        # Create a process instance
        process = Process.objects.create(workflow=workflow)
        
        # Link the process to the form
        form.approval_process = process
        form.save(update_fields=['approval_process'])
        
        return process
        
    except Exception as e:
        print(f"Failed to create workflow for sanction form {form.form_no}: {e}")
        return None
