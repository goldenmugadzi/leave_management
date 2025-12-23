from django.forms import inlineformset_factory
from django.views.generic.edit import CreateView, FormView
from django.contrib import messages
from .models import *
from .forms import *
from django.views.generic.detail import DetailView
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from email.mime.text import MIMEText
from it.users.views import ms_exhange_send_html
from django.db.models import Q
from django.core.validators import validate_email
from django.core.exceptions import ValidationError
from decouple import config
from datetime import datetime
from appraisal.helpers.notifications import send_appraisal_notifications
from finance.comparative_schedules.views import notify_user



def is_valid_email(email):
    try:
        validate_email(email)
        return True
    except ValidationError:
        return False

class WorkflowCreateView(CreateView):
    form_class = WorkflowCreateForm
    template_name = "approve/create_workflow.html"
    extra_steps = None

    def form_valid(self, form):
        self.extra_steps = form.cleaned_data["number_of_steps"]
        return super().form_valid(form)

    def get_success_url(self):
        workflow_id = self.object.id
        return f"/workflow/{workflow_id}/add-steps?extra={self.extra_steps}"


def step_formset_view(request, workflow_id):
    workflow = Workflow.objects.get(id=workflow_id)
    extra_steps = int(
        request.GET.get("extra", 5)
    )  # Default value of 5 if no 'extra' parameter is provided
    formset_class = inlineformset_factory(
        Workflow, Step, form=StepForm, extra=extra_steps, can_delete=False
    )
    formset_class.form.base_fields["approver"].queryset = Roles.objects.filter(
        application=workflow.application.name
    )
    existing_steps = Step.objects.filter(workflow_id=workflow_id)

    if request.method == "POST":
        formset = formset_class(request.POST, instance=workflow)
        if existing_steps.exists():
            # Show a pop-up message if there are existing steps
            messages.warning(request, "There are existing steps for this workflow.")
            url = reverse("approve:workflow_detail", args=[workflow_id])
            return redirect(url)
        elif formset.is_valid():
            instances = formset.save(commit=False)
            for index, instance in enumerate(instances):
                if instance.approver:
                    instance.workflow = workflow
                    instance.step = index + 1
                    instance.save()
            url = reverse("approve:workflow_detail", args=[workflow_id])
            return redirect(url)
        else:
            return render(
                request,
                "approve/update_workflow.html",
                {"formset": formset, "workflow": workflow},
            )
    else:
        formset = formset_class(instance=workflow)

    return render(
        request,
        "approve/update_workflow.html",
        {"formset": formset, "workflow": workflow},
    )


class WorkflowDetailView(DetailView):
    model = Workflow
    template_name = "approve/workflow_detail.html"
    context_object_name = "workflow"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflow = self.get_object()
        context["steps"] = workflow.step_set.all()
        return context


def get_my_roles_for_apps(user, app_names):
    roles_dict = []
    for app_name in app_names:
        roles = user.roles.filter(app_id__name=app_name).values_list("name", flat=True)
        if roles:
            for role in roles:
                roles_dict.append(role + " for " + app_name)
    return roles_dict


def intiate(request, app):
    app = Workflow.objects.get(name__iexact=app)
    process = Process.objects.create(workflow=app)
    process.save()
    return process

def gql_initiate_approval_process(app):
    """
    This function is used to initiate a process for a given application.
    It creates a new Process object associated with the specified application.
    """
    app = Workflow.objects.get(name__iexact=app)
    process = Process.objects.create(workflow=app)
    process.save()
    return process

def approve_step(request, process_id):
    """
    This view function is used to approve a step in a process.
    if method is GET, get the last approval with this process id ordered by step and add 1 to its step to get next step.
    use  it to check if user.role == step(with the next step and process.workflow).approver
    else, the step is approved and the user is redirected to the workflow detail page.

    """
    process = Process.objects.get(id=process_id)
    try:
        latest_approval = process.approval_set.last()
        if latest_approval is not None:
            next_step = latest_approval.step.step + 1
        else:
            next_step = 1
    except Step.DoesNotExist:
        next_step = 1
    try:
        step = None
        
        check_step = Step.objects.filter(workflow=process.workflow,step=next_step)   
          
        if process.workflow.name == "Appraisal":
            if check_step.first().approver.name == "appraisee" or check_step.first().approver.name == "appraiser":
                is_appraisee = check_step.filter(
                    approver__name="appraisee"
                ).exists()
                
                is_appraiser = check_step.filter(
                    approver__name="appraiser"
                ).exists()
                if (is_appraisee and process.appraisal_process.last().user == request.user) | (is_appraiser and process.appraisal_process.last().appraiser == request.user):
                    step = check_step.first()
        else:
            step = Step.objects.get(
                workflow=process.workflow,
                step=next_step,
                approver__in=request.user.roles.all(),
            )
    except Step.DoesNotExist:
        messages.info(request, "This process was completed")
        return redirect("approve:workflow_detail", process.workflow.id)
    
    if not process.approval_set.filter(approved="Rejected"):
        if request.method == "POST":
            # Get the approved value from the button click
            approved_value = request.POST.get('approved')
            
            # Create form data with the approved value
            form_data = request.POST.copy()
            form_data['approved'] = approved_value
            
            form = ApprovalForm(form_data)
            if form.is_valid():
                approval = form.save(commit=False)
                approval.user = request.user
                approval.process = process
                approval.step = step
                approval.save()

                # Notify requester for ACE approvals (both standard and high-value)
                if process.workflow.name in ["ace", "ace_value"]:
                    try:
                        ace_item = process.ace2_set.last()
                        if ace_item and ace_item.requested_by:
                            requester = ace_item.requested_by
                            approval_status = approval.approved
                            
                            # Get step information
                            current_step = approval.step.step
                            total_steps = process.workflow.step_set.count()
                            approver_name = request.user.get_full_name() or request.user.username
                            
                            if approval_status == "Approved":
                                msg = f"Your ACE {ace_item.Ace_id2} has been approved by {approver_name} (Step {current_step}/{total_steps})"
                            elif approval_status == "Rejected":
                                msg = f"Your ACE {ace_item.Ace_id2} has been rejected by {approver_name}"
                            else:
                                msg = f"Your ACE {ace_item.Ace_id2} has been actioned by {approver_name} (Step {current_step}/{total_steps})"
                            
                            url = f"/ace/ace_detail/{ace_item.Ace_id2}"
                            notify_user(requester, msg, "ACE", url, ace_item.Ace_id2, request)
                            print(f"Notified requester {requester.username} about ACE {ace_item.Ace_id2} approval")
                    except Exception as e:
                        print(f"Error notifying ACE requester: {e}")

                # Handle different workflow types - check specific workflows first
                if process.workflow.name == "purchase request":
                    return redirect(
                        "purchase_request:purchase_request_detail",
                        process.purchaserequest_set.last().id,
                    )

               
                elif process.workflow.name == "Appraisal":
                    appraisal = process.appraisal_process.last()
                    url = reverse("update_appraisal", kwargs={"pk": appraisal.id})
                    notification_type="Appraisal"
                    notification_id=appraisal.id
                    send_appraisal_notifications(user_object=appraisal.user,
                                                notification_type=notification_type,
                                                notification_id=notification_id,
                                                url=url
                                                )
                    messages.success(request, "approved successfully")
                    
                    return step
                elif process.token_set.exists():
                    token = process.token_set.last()

                    send_notification(request, 'tokens:token', token.type, token, token.id)
                    return redirect('tokens:token', token.id)
                
                elif process.workflow.name == "leave":
                    from django.db import DatabaseError
                    try:
                        # Try to access leave request only if table exists
                        from django.db import connection
                        with connection.cursor() as cursor:
                            cursor.execute("""SELECT COUNT(*) FROM information_schema.tables 
                                          WHERE table_schema = DATABASE() AND 
                                          table_name = 'leave_management_leaverequest'""")
                            if cursor.fetchone()[0] == 1:  # Table exists
                                if process.leaverequest_set.exists():
                                    leaverequest = process.leaverequest_set.last()
                                    return redirect('leave_management:approve_leave', leaverequest.id)
                            else:
                                raise DatabaseError("Leave management tables not found")
                    except (DatabaseError, Exception) as e:
                        messages.error(request, "Leave management system is not properly set up. Please contact the system administrator.")
                        return redirect("approve:workflow_detail", process.workflow.id)
                
                elif process.workflow.name == "pettycash":
                    # Get the approval status to customize the message
                    approval_status = approval.approved
                    if approval_status == "Approved":
                        messages.success(request, "PettyCash approved successfully")
                    elif approval_status == "Rejected":
                        messages.warning(request, "PettyCash rejected successfully")
                    else:
                        messages.success(request, "PettyCash actioned successfully")
                    
                    return redirect(
                        "pettycash:pettycash_detail",
                        process.pettycash_set.last().petty_id,
                    )
                elif process.workflow.name == "virement":
                    # Handle virement workflow with automatic budget transfer on final approval
                    from ACE2.utils import execute_virement_budget_transfer
                    from ACE2.models import Asset_budget_Virament
                    
                    approval_status = approval.approved
                    
                    # Get the virement item
                    try:
                        virement_item = Asset_budget_Virament.objects.filter(process=process).last()
                        if not virement_item:
                            messages.error(request, "Virement item not found")
                            return redirect("approve:workflow_detail", process.workflow.id)
                    except Asset_budget_Virament.DoesNotExist:
                        messages.error(request, "Virement item not found")
                        return redirect("approve:workflow_detail", process.workflow.id)
                    
                    if approval_status == "Approved":
                        # Check if this is the final approval step
                        total_steps = process.workflow.step_set.count()
                        current_step = approval.step.step
                        
                        if current_step == total_steps:
                            # This is the final approval - execute budget transfer automatically
                            transfer_result = execute_virement_budget_transfer(virement_item, request.user)
                            
                            if transfer_result['success']:
                                messages.success(request, f"Virement approved successfully. {transfer_result['message']}")
                            else:
                                messages.error(request, f"Virement approved but budget transfer failed: {transfer_result['error']}")
                        else:
                            messages.success(request, "Virement approved successfully")
                    elif approval_status == "Rejected":
                        messages.warning(request, "Virement rejected successfully")
                    else:
                        messages.success(request, "Virement actioned successfully")
                    
                    return redirect("Ace:virament_detail", virement_item.virament_id)
                # Check for tokens only if no specific workflow matched
                elif process.token_set.exists(): 
                    token = process.token_set.last()
                    send_notification(request, 'tokens:token', token.type, token, token.id)
                    print('------------------------------got here-----------------------------------', str(token.id))
                    return redirect('tokens:token', token.id)
                else:
                    return redirect("approve:workflow_detail", process.workflow.id)
            else:
                messages.error(request, "A comment must be provided for rejection.")
                if process.workflow.name == "purchase request":
                    return redirect(
                        "purchase_request:purchase_request_detail",
                        process.purchaserequest_set.last().id,
                    )
                elif process.workflow.name == "ace":
                    messages.info(request, "Returning to ACE detail page. Please provide a comment for rejection.")
                    return redirect("Ace:ace_detail", process.ace2_set.last().Ace_id2)
                elif process.workflow.name == "ace_value":
                    messages.info(request, "Returning to high-value ACE detail page. Please provide a comment for rejection.")
                    return redirect("Ace:ace_detail", process.ace2_set.last().Ace_id2)
                elif process.workflow.name == "pettycash":
                    messages.info(request, "Returning to PettyCash detail page. Please provide a comment for rejection.")
                    return redirect(
                        "pettycash:pettycash_detail",
                        process.pettycash_set.last().petty_id,
                    )
                elif process.workflow.name == "virement":
                    from ACE2.models import Asset_budget_Virament
                    try:
                        virement_item = Asset_budget_Virament.objects.filter(process=process).last()
                        if virement_item:
                            messages.info(request, "Returning to Virement detail page. Please provide a comment for rejection.")
                            return redirect("Ace:virament_detail", virement_item.virament_id)
                    except Asset_budget_Virament.DoesNotExist:
                        pass
                    return redirect("approve:workflow_detail", process.workflow.id)
                elif process.workflow.name == "tokens":
                    return (
                        False  # redirect('tokens:token', process.token_set.last().id)
                    )
                else:
                    return redirect("approve:workflow_detail", process.workflow.id)

        messages.error(request, "You are not allowed to approve")
        if process.workflow.name == "purchase request":
            return redirect(
                "purchase_request:purchase_request_detail",
                process.purchaserequest_set.last().id,
            )
        elif process.workflow.name == "ace":
            return redirect("Ace:ace_detail", process.ace2_set.last().Ace_id2)
        elif process.workflow.name == "ace_value":
            return redirect("Ace:ace_detail", process.ace2_set.last().Ace_id2)
        elif process.workflow.name == "pettycash":
            return redirect(
                "pettycash:pettycash_detail", process.pettycash_set.last().petty_id
            )
        elif process.workflow.name == "virement":
            from ACE2.models import Asset_budget_Virament
            try:
                virement_item = Asset_budget_Virament.objects.filter(process=process).last()
                if virement_item:
                    return redirect("Ace:virament_detail", virement_item.virament_id)
            except Asset_budget_Virament.DoesNotExist:
                pass
            return redirect("approve:workflow_detail", process.workflow.id)
        elif process.workflow.name == "tokens":
            return redirect("tokens:token", process.token_set.last().id)
        else:
            return redirect("approve:workflow_detail", process.workflow.id)

    messages.error(request, "this process was already rejected")
    if process.workflow.name == "purchase request":
        return redirect(
            "purchase_request:purchase_request_detail",
            process.purchaserequest_set.last().id,
        )
    elif process.workflow.name == "ace":
        return redirect("Ace:ace_detail", process.ace2_set.last().Ace_id2)
    elif process.workflow.name == "ace_value":
        return redirect("Ace:ace_detail", process.ace2_set.last().Ace_id2)
    elif process.workflow.name == "pettycash":
        return redirect(
            "pettycash:pettycash_detail", process.pettycash_set.last().petty_id
        )
    elif process.workflow.name == "virement":
        from ACE2.models import Asset_budget_Virament
        try:
            virement_item = Asset_budget_Virament.objects.filter(process=process).last()
            if virement_item:
                return redirect("Ace:virament_detail", virement_item.virament_id)
        except Asset_budget_Virament.DoesNotExist:
            pass
        return redirect("approve:workflow_detail", process.workflow.id)
    elif process.workflow.name == "tokens":
        return redirect("tokens:token", process.token_set.last().id)
    else:
        return redirect("approve:workflow_detail", process.workflow.id)


def approvers(object):
    print("object.process.workflow  ",object.process.workflow)
    try:
        step = get_object_or_404(Step, workflow=object.process.workflow, step=object.process.approval_set.count())
    except:
        step = get_object_or_404(Step, workflow=object.process.workflow, step=1)
    """check if the step is not the last step in the workflow"""
    if step.step < object.process.workflow.step_set.count():
        next_step = get_object_or_404(Step, workflow=object.process.workflow, step=object.process.approval_set.count()+1)
        """check if there are approvers for the next step"""
        return Responsibilities.objects.filter(Q(role=next_step.approver)& Q(cost_centers=object.cost_center))
    else:
        return None

def allowed_to_approve(user, object):
    responsibilities = approvers(object)
    return user in responsibilities





def send_notification(request, url, app, obj,id):
    responsibilities = approvers(obj)
    if responsibilities == None:
        return messages.info(request, "This process was completed successfully")
    elif not responsibilities:
        messages.error(request, "There are no approvers for the next step")
        messages.info(request, f" Please inform your EXPECTED APPROVER to contact system administrator for approval authorisation of ({app.upper()}) for ({ str(obj.cost_center).upper() })")
        return 0
    domain_name = config('be_url') #"http://127.0.0.1:8000"  # Consider using settings for the domain
    cc_recipients =[]
    recipients =[]
    cc_recipients_names =[]
    redirect_url = f"{domain_name}{reverse(url, args=[id])}"
    message = f"We kindly request that you review and take necessary action regarding this "

    hour = datetime.now().hour
    greetings = {(0, 4): "Good night!",(5, 11): "Good morning!",(12, 16): "Good afternoon!",(17, 20): "Good evening!",(21, 23): "Good night!"}
    subject = next((msg for (start, end), msg in greetings.items() if start <= hour <= end), "Hello!")

    url=reverse(url, args=[id])
    notification_type=app
    notification_id=id

    for responsibility in responsibilities:
        if responsibility.user.email and is_valid_email(responsibility.user.email):  # Validate email
            recipients.append(responsibility.user)
            cc_recipients.append(responsibility.user.email)
            cc_recipients_names.append(responsibility.user.get_full_name())  # Call the method
    try:
        user=recipients[0]

        print(f"Sending to: {user.email}, CC: {cc_recipients}")
        notify(request,subject,user,message,redirect_url,url,notification_type,notification_id,cc_recipients,cc_recipients_names)
        return 1
    except:

        messages.info(request, f" Please inform your EXPECTED APPROVER to contact system administrator for approval authorisation of ({notification_type.upper()}) for ({ str(obj.cost_center).upper() })")
        return 0
# def gql_send_notification(obj):
#     responsibilities = approvers(obj)
#     recipients = []
#     recipient_emails = []
#     if responsibilities is None:
#         return "This process was completed successfully", []
#     elif not responsibilities:
#         return f"No approvers for the next step. Please inform your EXPECTED APPROVER to contact system administrator for approval authorisation of ({str(obj.cost_center).upper()})", []
#     domain_name = config('be_url')
#     cc_recipients = []
#     cc_recipients_names = []
#     redirect_url = f"{domain_name}/graphql"  # Adjust as needed for your frontend
#     message = "We kindly request that you review and take necessary action regarding this"

#     hour = datetime.now().hour
#     greetings = {(0, 4): "Good night!", (5, 11): "Good morning!", (12, 16): "Good afternoon!", (17, 20): "Good evening!", (21, 23): "Good night!"}
#     subject = next((msg for (start, end), msg in greetings.items() if start <= hour <= end), "Hello!")

#     notification_type = obj.__class__.__name__.lower()
#     notification_id = getattr(obj, 'id', None)

#     for responsibility in responsibilities:
#         if responsibility.user.email and is_valid_email(responsibility.user.email):
#             recipients.append(responsibility.user)
#             recipient_emails.append(responsibility.user.email)
#             cc_recipients.append(responsibility.user.email)
#             cc_recipients_names.append(responsibility.user.get_full_name())
#     try:
#         user = recipients[0]
#         Notification.objects.create(
#             user=user,
#             message=message,
#             url=redirect_url,
#             notification_type=notification_type,
#             notification_id=notification_id
#         )
#         response = ms_exhange_send_html(
#             subject=subject,
#             to_recipients=[user.email],
#             cc_recipients=cc_recipients,
#             template='email/email_template.html',
#             kwargs={"kwargs": {"redirect_url": redirect_url, "type": notification_type, "user_fullname": user.get_full_name(), "message": message}}
#         )
#         if response.status_code == 200:
#             return f"Email notification successfully sent to {', '.join(recipient_emails)}"
#         else:
#             return f"Error sending email to {user.get_full_name()}"
#     except Exception as e:
#         return f"Error: {str(e)}. Please inform your EXPECTED APPROVER to contact system administrator for approval authorisation of ({obj.process.workflow.name.upper()}) for ({str(obj.cost_center).upper()})"

def gql_send_notification(obj):
    responsibilities = approvers(obj)
    recipients = []
    recipient_emails = []

    if responsibilities is None:
        return "This process was completed successfully"

    elif not responsibilities:
        return f"No approvers for the next step. Please inform your EXPECTED APPROVER to contact system administrator for approval authorisation of ({str(obj.cost_center).upper()})"

    domain_name = config('be_url')
    cc_recipients = []
    cc_recipients_names = []
    redirect_url = f"{domain_name}/graphql"  # Adjust for your frontend
    message = "We kindly request that you review and take necessary action regarding this"

    hour = datetime.now().hour
    greetings = {
        (0, 4): "Good night!",
        (5, 11): "Good morning!",
        (12, 16): "Good afternoon!",
        (17, 20): "Good evening!",
        (21, 23): "Good night!"
    }
    subject = next((msg for (start, end), msg in greetings.items() if start <= hour <= end), "Hello!")

    notification_type = obj.__class__.__name__.lower()
    notification_id = getattr(obj, 'id', None)

    for responsibility in responsibilities:
        if responsibility.user.email and is_valid_email(responsibility.user.email):
            recipients.append(responsibility.user)
            recipient_emails.append(responsibility.user.email)
            cc_recipients.append(responsibility.user.email)
            cc_recipients_names.append(responsibility.user.get_full_name())

    try:
        user = recipients[0]
        Notification.objects.create(
            user=user,
            message=message,
            url=redirect_url,
            notification_type=notification_type,
            notification_id=notification_id
        )
        response = ms_exhange_send_html(
            subject=subject,
            to_recipients=[user.email],
            cc_recipients=cc_recipients,
            template='email/email_template.html',
            kwargs={
                "kwargs": {
                    "redirect_url": redirect_url,
                    "type": notification_type,
                    "user_fullname": user.get_full_name(),
                    "message": message
                }
            }
        )
        if response.status_code == 200:
            return f"Email notification successfully sent to {', '.join(recipient_emails)}"
        else:
            return f"Error sending email to {user.get_full_name()}"

    except Exception as e:
        return (
            f"Error: {str(e)}. Please inform your EXPECTED APPROVER to contact system administrator "
            f"for approval authorisation of ({obj.process.workflow.name.upper()}) for ({str(obj.cost_center).upper()})"
        )

def notify(request,subject,user,message,redirect_url,url,notification_type,notification_id,cc_recipients,cc_recipients_names):
      # Create the notification
        Notification.objects.create(user=user,message=message,url=url,notification_type=notification_type,notification_id=notification_id)
        # Send the email
        response = ms_exhange_send_html(subject=subject,to_recipients=[user.email],cc_recipients=cc_recipients,template='email/email_template.html',
                                    kwargs={"kwargs":{"redirect_url":redirect_url,"type":notification_type,"user_fullname":user.get_full_name(),"message":message}})
        if response.status_code == 200:
            cc_names_str = ', '.join(cc_recipients_names)  # Convert list to a  ent to  " + cc_names_str)
            return messages.success(request, "Email notification successfully sent to "+ cc_names_str)
        
        else: return messages.error(request, "Error sending email to  "+user.get_full_name())
