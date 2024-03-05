from django.shortcuts import render, redirect, get_object_or_404
from .models import RFQ, Quotation,Process,Application
from django.contrib.auth.decorators import login_required
from .forms import RFQForm, QuotationFormSet

from it.users.models import *
from approve.views import intiate
from approve.models import Step
from approve.forms import ApprovalForm
from django.urls import reverse

@login_required
def rfq_detail(request, rfq_id):
    rfq = RFQ.objects.get(id=rfq_id)
    approvalForm=None
    to=None
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute
    
    try:
        last_approved = rfq.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    
    next_step = last_approved + 1
    
    try:
        newStep= Step.objects.get(step=next_step, workflow=rfq.process.workflow, approver__in=user_roles)
        if newStep:
            approvalForm = ApprovalForm 
            to=newStep.to
    except Step.DoesNotExist:
        pass
    
    return render(request, 'finance/rfq/rfq_detail.html', {'rfq': rfq, 'approvalForm': approvalForm,'to':to})
@login_required
def create_rfq(request):
    if request.method == 'POST':
        form = RFQForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
        app= Application.objects.get(name='rfq')
        if form.is_valid() and formset.is_valid():
            rfq = form.save(commit=False)
            rfq.process = intiate(request, 'rfq')
            rfq.requested_by = request.user
            rfq.save()

            for quotation_form in formset:
                quotation = quotation_form.save(commit=False)
                quotation.rfq = rfq
                quotation.save()

            url = reverse('rfq:rfq_detail', args=[rfq.id])
            return redirect(url)
    else:
        form = RFQForm()
        formset = QuotationFormSet()

    return render(request, 'finance/rfq/create_rfq.html', {'form': form, 'formset': formset})
@login_required
def rfqs_awaiting_my_action(request):
    rfqs_awaiting_my_action = []
    user_role = request.user.roles
    for process in Process.objects.filter(workflow__name='rfq'):
        last_approval = process.approval_set.last()
        if last_approval and last_approval.step:
            last_approval_step = last_approval.step
            next_step = Step.objects.get(step=last_approval_step + 1, workflow=process.workflow, approver=user_role)
            if next_step:
                rfqs_awaiting_my_action.append(process.rfq)

    return render(request, 'finance/rfq/view_all_rfqs.html', {'rfqs': rfqs_awaiting_my_action})

@login_required
def view_all_rfqs(request):
    rfqs = RFQ.objects.all()
    return render(request, 'finance/rfq/view_all_rfqs.html', {'rfqs': rfqs})