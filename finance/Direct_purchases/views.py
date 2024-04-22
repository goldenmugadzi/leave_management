from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from approve.forms import ApprovalForm
from approve.models import Step
from approve.views import intiate
from it.users.models import Roles
from .forms import *
from .models import *
from it.users.models import UserProfile, Regions, Sections, Supplier


@login_required
def Direct_Purchase_detail(request, DP_id):
    DP_item = Direct_purchase.objects.get(id=DP_id)
    approvalForm = None
    to = None
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute

    try:
        last_approved = DP_item.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0

    next_step = last_approved + 1

    try:
        newStep = Step.objects.get(step=next_step, workflow=DP_item.process.workflow,
                                   approver__in=user_roles)
        if newStep and request.user.section == DP_item.section and next_step == 1:
            approvalForm = ApprovalForm
            to = newStep.to
        elif newStep:
            approvalForm = ApprovalForm
            to = newStep.to
    except Step.DoesNotExist:
        pass
    approved_steps = DP_item.process.approval_set.all().values_list('step__step', flat=True)
    return render(request, 'finance/pettycash/pettycash_detail.html',
                  {'pettycash': DP_item, 'approved_steps': approved_steps, 'approvalForm': approvalForm,
                   'to': to})


@login_required
def create_supplier(request):
    if request.method == 'POST':
        form = SupplierForm(request.POST, request.FILES)
        if form.is_valid():
            supplier = form.save(commit=False)
            supplier.created_by = request.user
            supplier.save()

            url = reverse('direct_purchase:supplier_detail', args=[supplier.id])
            return redirect(url)
    else:
        form = SupplierForm()

    return render(request, 'finance/direct_purchases/create_supplier.html', {'form': form})


@login_required
def create_direct_purchase(request):
    if request.method == 'POST':
        form = DirectPurchaseForm(request.POST, request.FILES)
        # formset = ItemForm(request.POST, request.FILES)
        if form.is_valid():
            # and formset.is_valid()):
            direct_purchase = form.save(commit=False)
            direct_purchase.requested_by = request.user
            direct_purchase.save()

            # for item_form in formset:
            #     item = item_form.save(commit=False)
            #     item.direct_purchase = direct_purchase
            #     item.save()

            url = reverse('direct_purchase:direct_purchase_detail', args=[direct_purchase.id])
            return redirect(url)
    else:
        form = DirectPurchaseForm()
        # formset = ItemForm()

    return render(request, 'finance/direct_purchases/create_direct_purchase.html',
                  {'form': form})


@login_required
def direct_purchases_awaiting_my_action(request):
    """
    for each direct purchase.Process in the rfqs,  let current_step = the last direct purchase.process.approval if
    any else 0 and let next_step =current_step+1 then check if  next_step=step.step for direct
    purchase.process.workflow.step_set filtered by approver = user.roles.all.
    """
    DPs_to_process = []
    user_roles = request.user.roles.all()
    for DP in Direct_purchase.objects.all():
        process = DP.process

        if process.approval_set.exists():
            last_approval = process.approval_set.last()
            current_step = last_approval.step.step
        else:
            current_step = 0

        next_step = current_step + 1

        workflow = process.workflow
        step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

        if step:
            DPs_to_process.append(DP)

    return render(request, 'finance/pettycash/view_all_direct_purchases.html', {'Direct_purchases': DPs_to_process})


@login_required
def view_all_DPs(request):
    DPs = Direct_purchase.objects.all()
    return render(request, 'finance/rfq/view_all_DPs.html', {'DPs': DPs})


