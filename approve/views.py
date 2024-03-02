from django.forms import formset_factory
from .models import Workflow, Step
from django.shortcuts import render, redirect
from .forms import *

StepFormset = formset_factory(StepForm, extra=0)

def create_workflow(request):
    if request.method == 'POST':
        wf_exists = False 
        try:
            wf = Workflow.objects.get(name=request.POST['name'])
            number_of_steps = int(request.POST['number_of_steps'])
            workflow_form = WorkflowUpdateForm(request.POST, instance=wf)
            wf_exists = True 

        except: 
            number_of_steps = int(request.POST['number_of_steps'])
            workflow_form = WorkflowUpdateForm(request.POST)
        
        if workflow_form.is_valid():
            workflow = workflow_form.save(commit=False)
            step_formset = StepFormset(prefix='step')
            i = 1
            if wf_exists:
                existing_steps = Step.objects.filter(workflow=wf)
                for a, existing_step in enumerate(existing_steps, start=1):
                    prefix='step'
                    i += 1
                    step_formset.forms.append(StepForm(instance=existing_step, prefix=prefix))
                    
            step_formset.forms.extend([StepForm(prefix='step') for _ in range(number_of_steps - i + 1)])

            return render(request, 'approve/create_workflow.html', {'workflow_form': workflow_form, 'step_formset': step_formset, 'url': '/create_steps/'})
       
        return render(request, 'approve/create_workflow.html', {'workflow_form': workflow_form})

    workflow_form = WorkflowCreateForm()
    return render(request, 'approve/create_workflow.html', {'workflow_form': workflow_form})

def create_steps(request):
    if request.method == 'POST':
        try:
            wf = Workflow.objects.get(name=request.POST['name'])
            workflow_form = WorkflowUpdateForm(request.POST, instance=wf)
        except: 
            workflow_form = WorkflowUpdateForm(request.POST)
        
        StepFormset = formset_factory(SaveStepForm, extra=0)

        step_formset = StepFormset(request.POST, prefix='step')
        print('got here workflow_form'+request.method)

        if workflow_form.is_valid():
            workflow = workflow_form.save()
            print('got here step_formset'+str(len(step_formset)))
            for k,v in request.POST.items():
                print(k,v)
            i = 1
            for form in step_formset:
                print('got here form'+form)
                if form.is_valid():
                    step = form.save(commit=False)
                    step.workflow = workflow
                    step.step = i
                    step.save()
                    i += 1
                    return redirect('/')
                else:
                    return render(request, 'approve/update_workflow.html', {'workflow_form': form})
        else:
            print('workflow_form.is_valid()'+workflow_form.is_valid())
            return render(request, 'approve/update_workflow.html', {'workflow_form': workflow_form, 'step_formset': step_formset})
    else:
        workflow_form = WorkflowCreateForm()
        step_formset = StepFormset(prefix='step')
        print('got here'+request.method)
    return render(request, 'approve/update_workflow.html', {'workflow_form': workflow_form, 'step_formset': step_formset})