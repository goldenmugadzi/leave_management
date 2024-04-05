from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from approve.forms import ApprovalForm
from approve.models import Step
from approve.views import intiate
from .forms import PettycashForm, QuotationFormSet
from .models import Pettycash


@login_required
def pettyCash_detail(request, petty_id):
    pettycash_item = Pettycash.objects.get(id=petty_id)
    approvalForm = None
    to = None
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute

    try:
        last_approved = pettycash_item.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0

    next_step = last_approved + 1

    try:
        newStep = Step.objects.get(step=next_step, workflow=pettycash_item.process.workflow,
                                   approver__in=user_roles)
        if newStep and request.user.section == pettycash_item.section and next_step == 1:
            approvalForm = ApprovalForm
            to = newStep.to
        elif newStep:
            approvalForm = ApprovalForm
            to = newStep.to
    except Step.DoesNotExist:
        pass
    approved_steps = pettycash_item.process.approval_set.all().values_list('step__step', flat=True)
    return render(request, 'finance/pettycash/pettycash_detail.html',
                  {'pettycash': pettycash_item, 'approved_steps': approved_steps, 'approvalForm': approvalForm, 'to': to})


@login_required
def create_rfq(request):
    if request.method == 'POST':
        form = PettycashForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            pettycash = form.save(commit=False)
            pettycash.process = intiate(request, 'pettycash')
            pettycash.requested_by = request.user
            pettycash.save()

            for quotation_form in formset:
                quotation = quotation_form.save(commit=False)
                quotation.pettycash = pettycash
                quotation.save()

            url = reverse('pettycash:pettycash_detail', args=[pettycash.id])
            return redirect(url)
    else:
        form = PettycashForm()
        formset = QuotationFormSet()

    return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})


@login_required
def pettycash_awaiting_my_action(request):
    """
    for each pettycash.Process in the rfqs,  let current_step = the last pettycash.process.approval if any else 0 and
    let next_step =current_step+1 then check if  next_step=step.step for rfq.process.workflow.step_set filtered by
    approver = user.roles.all.
    """
    pettycashs_to_process = []
    user_roles = request.user.roles.all()
    for pettycash in Pettycash.objects.all():
        process = pettycash.process

        if process.approval_set.exists():
            last_approval = process.approval_set.last()
            current_step = last_approval.step.step
        else:
            current_step = 0

        next_step = current_step + 1

        workflow = process.workflow
        step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

        if step:
            pettycashs_to_process.append(pettycash)

    return render(request, 'finance/pettycash/view_all_pettycashs.html', {'pettycashs': pettycashs_to_process})


@login_required
def view_all_pettycashs(request):
    pettycashs = Pettycash.objects.all()
    return render(request, 'finance/rfq/view_all_pettycashs.html', {'pettycashs': pettycashs})

