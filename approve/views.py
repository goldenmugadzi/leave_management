from django.forms import inlineformset_factory
from django.views.generic.edit import CreateView, FormView
from django.contrib import messages
from .models import *
from .forms import *
from django.views.generic.detail import DetailView
from django.shortcuts import render, redirect, HttpResponse
from django.urls import reverse


class WorkflowCreateView(CreateView):
    form_class = WorkflowCreateForm
    template_name = 'approve/create_workflow.html'
    extra_steps = None

    def form_valid(self, form):
        self.extra_steps = form.cleaned_data['number_of_steps']
        return super().form_valid(form)

    def get_success_url(self):
        workflow_id = self.object.id
        return f'/workflow/{workflow_id}/add-steps?extra={self.extra_steps}'


def step_formset_view(request, workflow_id):
    workflow = Workflow.objects.get(id=workflow_id)
    extra_steps = int(request.GET.get('extra', 5))  # Default value of 5 if no 'extra' parameter is provided
    formset_class = inlineformset_factory(Workflow, Step, form=StepForm, extra=extra_steps, can_delete=False)
    formset_class.form.base_fields['approver'].queryset = Roles.objects.filter(application=workflow.application.name)
    existing_steps = Step.objects.filter(workflow_id=workflow_id)

    if request.method == 'POST':
        formset = formset_class(request.POST, instance=workflow)
        if existing_steps.exists():
            # Show a pop-up message if there are existing steps
            messages.warning(request, 'There are existing steps for this workflow.')
            url = reverse('approve:workflow_detail', args=[workflow_id])
            return redirect(url)
        elif formset.is_valid():
            instances = formset.save(commit=False)
            for index, instance in enumerate(instances):
                if instance.approver:
                    instance.workflow = workflow
                    instance.step = index + 1
                    instance.save()
            url = reverse('approve:workflow_detail', args=[workflow_id])
            return redirect(url)
        else:
            return render(request, 'approve/update_workflow.html', {'formset': formset, 'workflow': workflow})
    else:
        formset = formset_class(instance=workflow)

    return render(request, 'approve/update_workflow.html', {'formset': formset, 'workflow': workflow})


class WorkflowDetailView(DetailView):
    model = Workflow
    template_name = 'approve/workflow_detail.html'
    context_object_name = 'workflow'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        workflow = self.get_object()
        context['steps'] = workflow.step_set.all()
        return context


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
        step = Step.objects.get(workflow=process.workflow, step=next_step, approver__in=request.user.roles.all())
    except Step.DoesNotExist:
        message = messages.info(request, 'This process was completed')
        return redirect('approve:workflow_detail', process.workflow.id, message)
    if request.method == 'POST':
        form = ApprovalForm(request.POST)
        if form.is_valid():
            approval = ApprovalForm(request.POST).save(commit=False)
            approval.user = request.user
            approval.process = process
            approval.step = step
            approval.save()
            
            if process.workflow.name == 'purchase request':
                return redirect('purchase_request:purchase_request_detail', process.purchaserequest_set.last().id)
           
            if process.workflow.name == 'tokens':
                return redirect('tokens:token', process.token_set.last().id)
            elif process.workflow.name == 'pettycash':
                return redirect('pettycash:pettycash_detail', process.pettycash_set.last().id)

            else:
                return redirect('approve:workflow_detail', process.workflow.id)
        else:

            return HttpResponse('A comment must be provided for rejection.')
    return HttpResponse('You are not allowed to approve')
