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
            form = ApprovalForm(request.POST)
            if form.is_valid():
                approval = ApprovalForm(request.POST).save(commit=False)
                approval.user = request.user
                approval.process = process
                approval.step = step
                approval.save()

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
                    
                    return redirect("update_appraisal", appraisal.id)
                elif process.token_set.exists() != None:
                    token = process.token_set.last()

                    send_notification(request, 'tokens:token', token.type, token, token.id)
                    return redirect('tokens:token', token.id)
                 
                elif process.workflow.name == "pettycash":
                    return redirect(
                        "pettycash:pettycash_detail",
                        process.pettycash_set.last().petty_id,
                    )
                elif process.workflow.name == "ace":
                    print(process.ace2_set.last().Ace_id2, "Please")
                    messages.success(request, "ace actioned successfully")
                    return redirect("Ace:ace_detail", process.ace2_set.last().Ace_id2)
                else:
                    return redirect("approve:workflow_detail", process.workflow.id)
            else:

                messages.error(request, "A comment must be provided for rejection.")
                if process.workflow.name == "purchase request":
                    return redirect(
                        "purchase_request:purchase_request_detail",
                        process.purchaserequest_set.last().id,
                    )

                if process.workflow.name == "tokens":
                    return (
                        False  # redirect('tokens:token', process.token_set.last().id)
                    )
                elif process.workflow.name == "pettycash":
                    return redirect(
                        "pettycash:pettycash_detail",
                        process.pettycash_set.last().petty_id,
                    )

                else:
                    return redirect("approve:workflow_detail", process.workflow.id)

        messages.error(request, "You are not allowed to approve")
        if process.workflow.name == "purchase request":
            return redirect(
                "purchase_request:purchase_request_detail",
                process.purchaserequest_set.last().id,
            )

        if process.workflow.name == "tokens":
            return redirect("tokens:token", process.token_set.last().id)
        elif process.workflow.name == "pettycash":
            return redirect(
                "pettycash:pettycash_detail", process.pettycash_set.last().petty_id
            )

        else:
            return redirect("approve:workflow_detail", process.workflow.id)

    messages.error(request, "this process was already rejected")
    if process.workflow.name == "purchase request":
        return redirect(
            "purchase_request:purchase_request_detail",
            process.purchaserequest_set.last().id,
        )

    if process.workflow.name == "tokens":
        return redirect("tokens:token", process.token_set.last().id)
    elif process.workflow.name == "pettycash":
        return redirect(
            "pettycash:pettycash_detail", process.pettycash_set.last().petty_id
        )

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
