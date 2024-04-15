from django.shortcuts import render, redirect
from .forms import  MeterForm, CustomerForm,ReasonForm,PernaltForm
from .models import *
from approve.views import intiate
from approve.models import Step
from approve.forms import ApprovalForm
from django.contrib.auth.decorators import login_required

def create_tempertoken(request):
    if request.method == 'POST':
        #meter details from the database if the meter number already exists and use its instance to upldate the meter details
        try: meter = Meter.objects.get(number=request.POST['number'])
        except Meter.DoesNotExist: meter = None 
        meter_form = MeterForm(request.POST, instance=meter)
        pernalt_form = PernaltForm(request.POST,request.FILES )
#         customer details from the database if the customer already exists and use its instance to upldate the customer details
        try: customer = Customer.objects.get(contact_number=request.POST['contact_number'])
        except Customer.DoesNotExist: customer = None
        customer_form = CustomerForm(request.POST, instance=customer)
        if meter_form.is_valid() and customer_form.is_valid():
            meter = meter_form.save()
            customer = customer_form.save()
            process = intiate(request, 'tokens')
            temper_token = TemperToken.objects.create(**{'meter': meter,'customer': customer,'process':process,'created_by': request.user,})
            if request.POST['reason']=='fault': Fault.objects.create(**{'temper_token': temper_token,'description': request.POST['description'],})
            elif request.POST['reason']=='recover': Recover.objects.create(**{'temper_token': temper_token,'description': request.POST['description'],})
            elif request.POST['reason']=='reconnection': Reconnection.objects.create(**{'temper_token': temper_token,'description': request.POST['description'],})
            # else: add a validation error
            if pernalt_form.is_valid(): 
                pernalt= pernalt_form.save(commit=False)
                pernalt.temper_token=temper_token
                pernalt.save()
            return redirect('/tempertokens/')
        else: return render(request, 'temper_token/create_tempertoken.html', {'Customer': customer_form ,'reason':ReasonForm(request.POST) ,'Meter': meter_form,'Pernalt':pernalt_form })

    return render(request, 'temper_token/create_tempertoken.html', {'Customer': CustomerForm, 'reason':ReasonForm ,'Meter': MeterForm ,'Pernalt':PernaltForm})

@login_required
def tempertoken_details(request, tempertoken_id):
    tempertoken = TemperToken.objects.get(id=tempertoken_id)
    approvalForm=None
    to=None
    completed=False
    user_roles = request.user.roles.all()
    try:
        last_approved = tempertoken.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    next_step = last_approved + 1
    try:
        newStep= Step.objects.get(step=next_step, workflow=tempertoken.process.workflow, approver__in=user_roles)
        if  newStep:
            approvalForm = ApprovalForm
            to=newStep.to
    except Step.DoesNotExist:
        pass
    #if the last approved step is the final step, then the token is approved and a new token form is created
    if tempertoken.process.workflow.step_set.last().step==last_approved:
        completed=True
    approved_steps = tempertoken.process.approval_set.all().values_list('step__step', flat=True)
    return render(request, 'temper_token/tempertoken_detail.html', {'tempertoken': tempertoken,'completed':completed ,'approved_steps':approved_steps,'approvalForm': approvalForm,'to':to})

def view_all_tempertokens(request):return render(request, 'temper_token/tempertokens.html', {'tempertokens': TemperToken.objects.all()})    