from django.contrib.auth.decorators import login_required
from .forms import RFQForm, QuotationFormSet,aceRFQForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from finance.Ace.models import Ace
from it.users.models import *
from approve.views import intiate
from approve.models import Step
from approve.forms import ApprovalForm
from django.shortcuts import render, redirect
from django.urls import reverse

from approve.forms import ApprovalForm
from approve.models import Step
from approve.views import intiate
from finance.Ace.models import Ace
from .forms import RFQForm, QuotationFormSet, aceRFQForm
from .models import Procurement


@login_required
def rfq_detail(request, rfq_id):
    procurement = Procurement.objects.get(id=rfq_id)
    approvalForm=None
    to=None
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute
    
    try:
        last_approved = procurement.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    
    next_step = last_approved + 1
    
    try:
        newStep= Step.objects.get(step=next_step, workflow=procurement.process.workflow, approver__in=user_roles)
        if newStep and request.user.section==procurement.section and next_step==1:
            approvalForm = ApprovalForm 
            to=newStep.to
        elif newStep:
            approvalForm = ApprovalForm
            to=newStep.to
    except Step.DoesNotExist:
        pass
    approved_steps = procurement.process.approval_set.all().values_list('step__step', flat=True)
    return render(request, 'finance/procurement/rfq_detail.html', {'procurement': procurement, 'approved_steps':approved_steps,'approvalForm': approvalForm,'to':to})
    
@login_required
def create_rfq(request):
    if request.method == 'POST':
        form = RFQForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            procurement = form.save(commit=False)
            procurement.process = intiate(request, 'procurement')
            procurement.requested_by = request.user
            procurement.save()

            for quotation_form in formset:
                quotation = quotation_form.save(commit=False)
                quotation.procurement = procurement
                quotation.save()

            url = reverse('procurement:rfq_detail', args=[procurement.id])
            return redirect(url)
    else:
        form = RFQForm()
        formset = QuotationFormSet()

    return render(request, 'finance/procurement/create_rfq.html', {'form': form, 'formset': formset})

class CreateRFQView(CreateView):
    model = Procurement
    fields = '__all__'
    template_name = 'finance/procurement/create_rfq.html'
    success_url = reverse_lazy('rfqs')

@login_required    
def create_ace_rfq(request,ace_id):
    ace = Ace.objects.get(Ace_id=ace_id)
    form = aceRFQForm()
    
    if request.method == 'POST':
        form = aceRFQForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            procurement = form.save(commit=False)
            procurement.process = intiate(request, 'procurement')
            procurement.requested_by = request.user
            procurement.ace = ace
            procurement.save()
            for quotation_form in formset:
                quotation = quotation_form.save(commit=False)
                quotation.procurement = procurement
                quotation.save()

            url = reverse('procurement:rfq_detail', args=[procurement.id])
            return redirect(url)
    else:
        formset = QuotationFormSet()

    return render(request, 'finance/procurement/create_rfq.html', {'form': form, 'formset': formset,'ace':ace})
@login_required
def rfqs_awaiting_my_action(request):
    """
    for each procurement.process in the rfqs,  let curent_step = the last procurement.process.approval if any else 0 and let next_step =curent_step+1
    then check if  next_step=step.step for procurement.process.workflow.step_set filtered by approcer = user.roles.all.
    """
    rfqs_to_process = []
    user_roles = request.user.roles.all()
    for procurement in Procurement.objects.all():
        process = procurement.process

        if process.approval_set.exists():
            last_approval = process.approval_set.last()
            current_step = last_approval.step.step
        else:
            current_step = 0

        next_step = current_step + 1

        workflow = process.workflow
        step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()
        
        if step:
            rfqs_to_process.append(procurement)

    return render(request, 'finance/procurement/view_all_rfqs.html', {'rfqs': rfqs_to_process})
@login_required
def view_all_rfqs(request):
    rfqs = Procurement.objects.all()
    return render(request, 'finance/procurement/view_all_rfqs.html', {'rfqs': rfqs})
