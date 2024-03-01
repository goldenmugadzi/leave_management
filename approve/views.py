from django.forms import formset_factory
from .models import Workflow, Step
from django.shortcuts import render, redirect
from django.db.models import Q
from django.contrib import messages
from .forms import *

StepFormset = formset_factory(StepForm, extra=0)
def create_workflow(request):
    if request.method == 'POST':
        try:
            wf= Workflow.objects.get(name=request.POST['name'])
            number_of_steps =int(request.POST['number_of_steps'])
            workflow_form = WorkflowUpdateForm(request.POST,instance=wf)
        except: 
            number_of_steps = int(request.POST['number_of_steps'])
            workflow_form = WorkflowUpdateForm(request.POST)

        if workflow_form.is_valid():
            workflow = workflow_form.save(commit=False)

            # StepFormset = formset_factory(StepForm, extra=number_of_steps)
            step_formset = StepFormset(prefix='step')
            i=1
            if wf:
                existing_steps = Step.objects.filter(workflow=wf)
                for a,existing_step in enumerate(existing_steps, start=1):
                    prefix = f'step-{i}'
                    i+=1
                    step_formset.forms.append(StepForm(instance=existing_step, prefix=prefix))
            if number_of_steps>i:
                step_formset.extra=number_of_steps-i                   
            if number_of_steps > i:
                for _ in range(number_of_steps - i):
                    i += 1
                    step_formset.forms.append(StepForm(prefix=f'step-{i}'))
            step_formset.forms.append(StepForm(prefix=f'step-{i}'))

            return render(request, 'approve/create_workflow.html', {'workflow_form': workflow_form,'step_formset': step_formset,'url':'/create_steps/'})
       
        return render(request, 'approve/create_workflow.html', {'workflow_form': workflow_form})

    workflow_form = WorkflowCreateForm()

    return render(request, 'approve/create_workflow.html', {
        'workflow_form': workflow_form,
    })

def create_steps(request):
    if request.method == 'POST':
        try:
            wf= Workflow.objects.get(name=request.POST['name'])
            workflow_form = WorkflowUpdateForm(request.POST,instance=wf)
        except: 
            workflow_form = WorkflowCreateForm(request.POST)

        step_formset = StepFormset(request.POST, prefix='step')

        if workflow_form.is_valid() and step_formset.is_valid():
            workflow = workflow_form.save()
            i =1
            for form in step_formset:
                step = form.save(commit=False)
                step.workflow = workflow
                step.step = i
                step.save()
                i+=1
            return redirect('/')
    else:
        workflow_form = WorkflowCreateForm()
        step_formset = StepFormset(prefix='step')

    return render(request, 'approve/create_workflow.html', {
        'workflow_form': workflow_form,
        'step_formset': step_formset,
    })