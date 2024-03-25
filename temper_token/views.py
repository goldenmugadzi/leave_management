from django.shortcuts import render, redirect
from .forms import  MeterForm, CustomerForm,ReasonForm
from .models import *
from approve.views import intiate
from approve.forms import ApprovalForm
from django.contrib.auth.decorators import login_required

def create_tempertoken(request):
    if request.method == 'POST':
        meter_form = MeterForm(request.POST)
        customer_form = CustomerForm(request.POST)
        if meter_form.is_valid() and customer_form.is_valid():
            meter = meter_form.save()
            customer = customer_form.save()
            process = intiate(request, 'tempertoken')
            temper_token = TemperToken.objects.create(**{'meter': meter,'customer': customer,'created_by': request.user,})
            if request.POST['reason']=='fault': Fault.objects.create(**{'temper_token': temper_token,'process':process,'description': request.POST['description'],})
            elif request.POST['reason']=='recover': Recover.objects.create(**{'temper_token': temper_token,'description': request.POST['description'],})
            elif request.POST['reason']=='reconnection': Reconnection.objects.create(**{'temper_token': temper_token,'description': request.POST['description'],})
            # else: add a validation error
            return redirect('/tempertokens/')
        else: return render(request, 'temper_token/create_tempertoken.html', {'Customer': customer_form ,'Meter': meter_form })

    return render(request, 'temper_token/create_tempertoken.html', {'Customer': CustomerForm, 'reason':ReasonForm ,'Meter': MeterForm })

@login_required
def tempertoken_details(request, tempertoken_id):
    tempertoken = TemperToken.objects.get(id=tempertoken_id)
    approvalForm=None
    to=None
    user_roles = request.user.roles.all()
    try:
        last_approved = tempertoken.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    next_step = last_approved + 1
    try:
        newStep= Step.objects.get(step=next_step, workflow=tempertoken.process.workflow, approver__in=user_roles)
        if newStep and request.user.section==tempertoken.section and next_step==1:
            approvalForm = ApprovalForm 
            to=newStep.to
        elif newStep:
            approvalForm = ApprovalForm
            to=newStep.to
    except Step.DoesNotExist:
        pass
    approved_steps = tempertoken.process.approval_set.all().values_list('step__step', flat=True)
    return render(request, 'temper_token/tempertoken_detail.html', {'tempertoken': tempertoken, 'approved_steps':approved_steps,'approvalForm': approvalForm,'to':to})

def view_all_tempertokens(request):return render(request, 'temper_token/tempertokens.html', {'tempertokens': TemperToken.objects.all()})    