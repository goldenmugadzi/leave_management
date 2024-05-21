from django.shortcuts import render, redirect
from .forms import *
from .models import *
from django.contrib import messages
from approve.views import intiate, approve_step,get_my_roles_for_apps
from approve.models import Step
from approve.forms import ApprovalForm
from django.contrib.auth.decorators import login_required
from approve.decorators import allowed_roles
from django.db.models import Q

@login_required
@allowed_roles(['Requester'], ['temper', 'reimbursement','clear credit'])
def create_token(request):
    if request.method == "POST":
        # meter details from the database if the meter number already exists and use its instance to update the meter details
        try:
            meter = Meter.objects.get(number=request.POST["number"])
            meter_form = MeterForm(request.POST, instance=meter)
        except Meter.DoesNotExist:
            meter_form = MeterForm(request.POST)

        # customer details from the database if the customer already exists and use its instance to update the customer details
        try:
            customer = Customer.objects.get(contact_number=request.POST["contact_number"])
            customer_form = CustomerForm(request.POST, instance=customer)
        except Customer.DoesNotExist:
            customer_form = CustomerForm(request.POST)

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
            meter = meter_form.save()
            customer = customer_form.save()
            token = token_form.save(commit=False)
            token_type = token.type
            if token_type == 'TEMPER': process = intiate(request, "temper")
            elif token_type == 'REIMBURSEMENT': process = intiate(request, "reimbursement")
            elif token_type == 'CLEAR CREDIT': process = intiate(request, "clear credit")
            token.meter = meter
            token.customer = customer
            token.process = process
            token.created_by = request.user
            token.region = request.user.region
            token.save()

            if token_type == 'TEMPER' and tamper_token_form.is_valid():
                tamper_token = tamper_token_form.save(commit=False)
                tamper_token.token = token
                tamper_token.save()

                if tamper_token.is_for == 'Fauty Maintanance' and fault_maintanance_form.is_valid():
                    fault_maintanance = fault_maintanance_form.save(commit=False)
                    fault_maintanance.token = token
                    fault_maintanance.save()
                    messages.info(request, "Token request saved successfully")
                elif tamper_token.is_for == 'Recovered Meter' and  request.FILES.get("picture") and recovered_meter_form.is_valid():
                    recovered_meter = recovered_meter_form.save(commit=False)
                    recovered_meter.token = token
                    recovered_meter.save()
                    messages.info(request, "Token request saved successfully")
                elif tamper_token.is_for == 'Reconnection' and reconnection_form.is_valid():
                    reconnection = reconnection_form.save(commit=False)
                    reconnection.token = token
                    reconnection.save()
                    messages.info(request, "Token request saved successfully")
                else:
                    forms.update({
                        'fault_maintanance_form': fault_maintanance_form,
                        'recovered_meter_form': recovered_meter_form,
                        'reconnection_form': reconnection_form
                    })
                    tamper_token.delete()
                    token.delete()
                    messages.error(request, "Token request error")
                    return render(request, "tokens/create_token.html", forms)

            elif token_type == 'REIMBURSEMENT' and reimbursement_form.is_valid():
                reimbursement = reimbursement_form.save(commit=False)
                reimbursement.token = token
                reimbursement.save()
                if reimbursement.purpose == 'Faulty Meter' and faulty_meter_form.is_valid():
                    faulty_meter = faulty_meter_form.save(commit=False)
                    faulty_meter.token = token
                    faulty_meter.save()
                    messages.info(request, "Token request saved successfully")
                elif reimbursement.purpose == 'Recovered Meter' and recovered_meter_form.is_valid():
                    recovered_meter = recovered_meter_form.save(commit=False)
                    recovered_meter.token = token
                    recovered_meter.save()
                    messages.info(request, "Token request saved successfully")
                elif reimbursement.purpose == 'Old Token' and old_token_form.is_valid() and request.FILES.get("old_token"):
                    old_token = old_token_form.save(commit=False)
                    old_token.token = token
                    old_token.save()
                    messages.info(request, "Token request saved successfully")
                else:
                    forms.update({
                        'faulty_meter_form': faulty_meter_form,
                        'recovered_meter_form': recovered_meter_form,
                        'old_token_form': old_token_form
                    })
                    messages.error(request, "Token request error")
                    return render(request, "tokens/create_token.html", forms)

            elif token_type == 'CLEAR CREDIT' and clear_credit_form.is_valid():
                clear_credit = clear_credit_form.save(commit=False)
                clear_credit.token = token
                clear_credit.save()
                messages.info(request, "Token request saved successfully")
            else:
                return render(request, "tokens/create_token.html", forms)

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
    if request.method == "POST":
        generatetokenform = GenerateTokenForm(request.POST, request.FILES, instance=token)
        last_approval = token.process.approval_set.last()
        last_step = last_approval.step if last_approval else None
        if (
            token.process.workflow.step_set.last() is not None
            and last_step is not None
            and token.process.workflow.step_set.last().step == (last_step.step + 1)
        ):
            if generatetokenform.is_valid() and request.FILES.get("token_photo"):
                approve_step(request, token.process.pk)
                generatetokenform.save()
            else:
                messages.error(request, 'Generate token form is invalid. Have you provided a token photo?')
        else:
            approve_step(request, token.process.pk)
    approvalForm = None
    generateTokenForm = None
    to = None
    completed = False
    user_roles = request.user.roles.all()

    try:
        last_approved = token.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    next_step = last_approved + 1
    try:
        newStep = Step.objects.get(step=next_step, workflow=token.process.workflow, approver__in=user_roles)
        approvalForm = ApprovalForm
        to = newStep.to
        if newStep == token.process.workflow.step_set.last():
            generateTokenForm = GenerateTokenForm()

    except Step.DoesNotExist:
        pass

    completed = token.process.workflow.step_set.last().step == last_approved
    approved_steps = token.process.approval_set.all().values_list("step__step", flat=True)

    return render(request, "tokens/token_detail.html", {
        "token": token,
        "completed": completed,
        "approved_steps": approved_steps,
        "approvalForm": approvalForm,
        "generateTokenForm":generateTokenForm,
        "to": to,
    })
def view_all_tokens(request):
    return render(request, "tokens/tokens.html", {"tokens": Token.objects.all(),'all':True,'roles': get_my_roles_for_apps(request.user, ['temper','reimbursement','clear credit'])})
@login_required
def awaiting_my_action(request):
    """
    for each token.process in the tokens,  let curent_step = the last token.process.approval if any else 0 and let next_step =curent_step+1
    then check if  next_step=step.step for token.process.workflow.step_set filtered by approcer = user.roles.all.
    """
    tokens_to_process = []
    user_roles = request.user.roles.all()
    for token in Token.objects.filter(Q(section=request.user.section), Q(region=request.user.region)):
        process = token.process

        if process.approval_set.exists():
            last_approval = process.approval_set.last()
            current_step = last_approval.step.step
        else:
            current_step = 0

        next_step = current_step + 1

        workflow = process.workflow
        step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

        if step:
            tokens_to_process.append(token)

    return render(request, 'tokens/tokens.html',{'tokens': tokens_to_process,'all':False,'roles': get_my_roles_for_apps(request.user, ['temper','tokens','reimbursement','clear credit'])})

def addsection(request):
    for token in Token.objects.all():
        try:
            if not token.section:
                token.section = token.created_by.section
                token.region = token.created_by.region
                token.save() 
            old_process = token.process
            if old_process.workflow.name == 'tokens':
                if token.type == 'TEMPER': process = intiate(request, "temper")
                elif token.type == 'REIMBURSEMENT': process = intiate(request, "reimbursement")
                elif token.type == 'CLEAR CREDIT': process = intiate(request, "clear credit")
                token.process = process
                token.save()
                old_process.delete()
        except: pass
    return redirect('tokens:tokens')
