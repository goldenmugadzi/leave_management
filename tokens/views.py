from django.shortcuts import render, redirect
from .forms import  MeterForm, CustomerForm,ReasonForm,PernaltForm,TokenForm
from .models import *
from django.contrib import messages
from approve.views import intiate
from approve.models import Step
from approve.forms import ApprovalForm
from django.contrib.auth.decorators import login_required

def create_token(request):
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
            token = TokenForm(request.POST)
            if token.is_valid():
                token = token.save(commit=False)
                token.meter = meter
                token.customer = customer
                token.process = process
                token.created_by = request.user
                token.save()

                if request.POST['reason']=='fault': Fault.objects.create(**{'token':token,'description': request.POST['description'],})
                elif request.POST['reason']=='recover': Recover.objects.create(**{'token':token,'description': request.POST['description'],})
                elif request.POST['reason']=='reconnection': Reconnection.objects.create(**{'token':token,'description': request.POST['description'],})
                # else: add a validation error
                if pernalt_form.is_valid(): 
                    pernalt= pernalt_form.save(commit=False)
                    pernalt.token=token
                    pernalt.save()
                return redirect('/tokens/')
            else:
                messages.error(request, 'Invalid token details')
                return render(request, 'tokens/create_token.html', {'Customer': customer_form ,'token':TokenForm,'reason':ReasonForm(request.POST) ,'Meter': meter_form,'Pernalt':pernalt_form })
        else: return render(request, 'tokens/create_token.html', {'Customer': customer_form ,'reason':ReasonForm(request.POST) ,'Meter': meter_form,'Pernalt':pernalt_form })

    return render(request, 'tokens/create_token.html', {'Customer': CustomerForm, 'reason':ReasonForm ,'token':TokenForm ,'Meter': MeterForm ,'Pernalt':PernaltForm})

@login_required
def token_details(request, token_id):
    token = Token.objects.get(id=token_id)
    approvalForm=None
    to=None
    completed=False
    user_roles = request.user.roles.all()
    try:
        last_approved = token.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    next_step = last_approved + 1
    try:
        newStep= Step.objects.get(step=next_step, workflow=token.process.workflow, approver__in=user_roles)
        if  newStep:
            approvalForm = ApprovalForm
            to=newStep.to
    except Step.DoesNotExist:
        pass
    #if the last approved step is the final step, then the token is approved and a new token form is created
    if token.process.workflow.step_set.last().step==last_approved:
        completed=True
    approved_steps = token.process.approval_set.all().values_list('step__step', flat=True)
    return render(request, 'tokens/token_detail.html', {'token': token,'completed':completed ,'approved_steps':approved_steps,'approvalForm': approvalForm,'to':to})

def view_all_tokens(request):return render(request, 'tokens/tokens.html', {'tokens': Token.objects.all()})    