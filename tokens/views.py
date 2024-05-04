from django.shortcuts import render, redirect
from .forms import *
from .models import *
from django.contrib import messages
from approve.views import intiate
from approve.models import Step
from approve.forms import ApprovalForm
from django.contrib.auth.decorators import login_required

@login_required
def create_token(request):
    if request.method == "POST":
        # meter details from the database if the meter number already exists and use its instance to upldate the meter details
        try:
            meter = Meter.objects.get(number=request.POST["number"])
            meter_form = MeterForm(request.POST, instance=meter)
        except Meter.DoesNotExist:meter_form = MeterForm(request.POST)

        #         customer details from the database if the customer already exists and use its instance to upldate the customer details
        try:
            customer = Customer.objects.get( contact_number=request.POST["contact_number"] )
            customer_form = CustomerForm(request.POST, instance=customer)
        except Customer.DoesNotExist:customer_form = CustomerForm(request.POST)
        print('number=',request.POST["number"])
        token_form = TokenForm(request.POST, request.FILES)
        reimbursement_form = ReimbursementForm(request.POST, request.FILES)
        clear_credit_form = ClearCreditForm(request.POST, request.FILES)
        tamper_token_form = TamperTokenForm(request.POST, request.FILES)
        old_token_form = OldTokenForm(request.POST, request.FILES)
        faulty_meter_form = FaultMeterForm(request.POST, request.FILES)
        recovered_meter_form = RecoveredMeterForm(request.POST, request.FILES)
        fault_maintanance_form = FaultMaintananceForm(request.POST, request.FILES)
        reconnection_form = ReconnectionForm(request.POST, request.FILES)
        forms = {
                "meter_form": meter_form,
                "customer_form": customer_form,
                "token_form": token_form,
                "reimbursement_form": reimbursement_form,
                "clear_credit_form": clear_credit_form,
                "tamper_token_form": tamper_token_form,
                "old_token_form": old_token_form,
                "faulty_meter_form": faulty_meter_form,
                "recovered_meter_form": recovered_meter_form,
                "fault_maintanance_form": fault_maintanance_form,
                "reconnection_form": reconnection_form,
            }
        
        if meter_form.is_valid() and customer_form.is_valid() and token_form.is_valid():
            process = intiate(request, "tokens")
            meter = meter_form.save()
            customer = customer_form.save()
            token = token_form.save(commit=False)
            token.meter = meter
            token.customer = customer
            token.process = process
            token.created_by = request.user
            token.save()
            type=token.type
            if type == 'TEMPER' and tamper_token_form.is_valid:
                tamper_token=tamper_token_form.save(commit=False)
                tamper_token.token = token
                tamper_token.save()
                if tamper_token.is_for == 'Fauty Maintanance' and fault_maintanance_form.is_valid():
                    fault_maintanance = fault_maintanance_form.save(commit=False)
                    fault_maintanance.token = token
                    fault_maintanance.save()
                    messages.info(request,"token request saved successfully")
                elif tamper_token.is_for == 'Recovered Meter' and recovered_meter_form.is_valid():
                    recovered_meter = recovered_meter_form.save(commit=False)
                    recovered_meter.token = token
                    recovered_meter.save()
                    messages.info(request,"token request saved successfully")
                elif tamper_token.is_for == 'Reconnection' and reconnection_form.is_valid():
                    reconnection = reconnection_form.save(commit=False)
                    reconnection.token = token
                    reconnection.save()
                    messages.info(request,"token request saved successfully")
                else:return render(request, "tokens/create_token.html", forms)
            elif type == 'REIMBURSEMENT' and reimbursement_form.is_valid:
                reimbursement = reimbursement_form.save(commit=False)
                reimbursement.token = token
                reimbursement.save()
                if reimbursement.purpose == 'Faulty Meter' and faulty_meter_form.is_valid():
                    faulty_meter = faulty_meter_form.save(commit=False)
                    faulty_meter.token = token
                    faulty_meter.save()
                    messages.info(request,"token request saved successfully")
                elif reimbursement.purpose == 'Recovered Meter' and recovered_meter_form.is_valid():
                    recovered_meter = recovered_meter_form.save(commit=False)
                    recovered_meter.token = token
                    recovered_meter.save()
                    messages.info(request,"token request saved successfully")
                elif reimbursement.purpose == 'Old Token' and old_token_form.is_valid() and request.FILES.get("old_token") :
                    old_token = old_token_form.save(commit=False)
                    old_token.token = token
                    old_token.save()
                    messages.info(request,"token request saved successfully")
                else:return render(request, "tokens/create_token.html", forms)

            elif type == 'CLEAR CREDIT' and clear_credit_form.is_valid:
                clear_credit = clear_credit_form.save(commit=False)
                clear_credit.token=token
                clear_credit.save()
                messages.info(request,"token request saved successfully")
            else:return render(request, "tokens/create_token.html", forms)

            return redirect('tokens:tokens')
           
        else:
           
            return render(request, "tokens/create_token.html", forms)


    forms = {
        "meter_form": MeterForm(),
        "customer_form": CustomerForm(),
        "token_form": TokenForm(),
        "reimbursement_form": ReimbursementForm(),
        "clear_credit_form": ClearCreditForm(),
        "tamper_token_form": TamperTokenForm(),
        "old_token_form": OldTokenForm(),
        "faulty_meter_form": FaultMeterForm(),
        "recovered_meter_form": RecoveredMeterForm(),
        "fault_maintanance_form": FaultMaintananceForm(),
        "reconnection_form": ReconnectionForm(),
    }
    return render(request, "tokens/create_token.html", forms)


@login_required
def token_details(request, token_id):
    token = Token.objects.get(id=token_id)
    approvalForm = None
    to = None
    completed = False
    user_roles = request.user.roles.all()
    try:
        last_approved = token.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    next_step = last_approved + 1
    try:
        newStep = Step.objects.get(
            step=next_step, workflow=token.process.workflow, approver__in=user_roles
        )
        if newStep:
            approvalForm = ApprovalForm
            to = newStep.to
    except Step.DoesNotExist:
        pass
    # if the last approved step is the final step, then the token is approved and a new token form is created
    if token.process.workflow.step_set.last().step == last_approved:
        completed = True
    approved_steps = token.process.approval_set.all().values_list(
        "step__step", flat=True
    )
    return render(
        request,
        "tokens/token_detail.html",
        {
            "token": token,
            "completed": completed,
            "approved_steps": approved_steps,
            "approvalForm": approvalForm,
            "to": to,
        },
    )


def view_all_tokens(request):
    return render(request, "tokens/tokens.html", {"tokens": Token.objects.all()})
