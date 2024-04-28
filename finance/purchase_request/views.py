from django.contrib.auth.decorators import login_required
from .forms import PurchaseRequestForm,acePurchaseRequestForm
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
from django.forms import inlineformset_factory
from .forms import *
from .models import *
from approve.decorators import ApprovalDetails
import pandas as pd

@login_required
def purchase_request_detail(request, purchase_request_id):
    purchase_request = PurchaseRequest.objects.get(id=purchase_request_id)
    approved_steps, approvalForm, to = ApprovalDetails(request, purchase_request)

    return render(request, 'finance/purchase_request/purchase_request_detail.html', {'purchase_request': purchase_request, 'approved_steps':approved_steps,'approvalForm': approvalForm,'to':to})
    
@login_required
def create_purchase_request(request):
    itemFormset = inlineformset_factory(PurchaseRequest, PrItem, form=PrItemForm, extra=int(request.POST.get('items') or 1) , can_delete=False)
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST)
        attachments = request.FILES.getlist('attachments')
        if form.is_valid():
            print('Form is valid')
            purchase_request = form.save(commit=False)
            purchase_request.process = intiate(request, 'purchase request')
            purchase_request.requested_by = request.user
            purchase_request.save()
            for attachment in attachments:
                attachment = Attachment(file=attachment, purchase_request=purchase_request)
                attachment.save()

            formset = itemFormset(request.POST,instance=purchase_request)
            if formset.is_valid():
                formset.save()
            else:
                return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset, 'form': form})
            
            url = reverse('purchase_request:purchase_request_detail', args=[purchase_request.id])
            return redirect(url)
        return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset, 'form': form})
    else:
        form = PurchaseRequestForm()
        return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset(), 'form': form})
    
@login_required    
def create_ace_purchase_request(request,ace_id):
    ace = Ace.objects.get(Ace_id2=ace_id)
    itemFormset = inlineformset_factory(PurchaseRequest, PrItem, form=PrItemForm, extra=int(request.POST.get('items') or 1) , can_delete=False)
    if request.method == 'POST':
        form = acePurchaseRequestForm(request.POST, request.FILES)
        if form.is_valid():
            purchase_request = form.save(commit=False)
            purchase_request.process = intiate(request, 'purchase request')
            purchase_request.requested_by = request.user
            purchase_request.save()

          
            formset = itemFormset(request.POST, request.FILES)
            for it in formset:
                if it.is_valid():
                    try:
                        item = it.save(commit=False)
                        item.purchase_request = purchase_request
                        item.save()
                    except: 
                        pass
                else:
                    return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': formset, "attachentFormset":attachentFormset, 'form': form})
            
            url = reverse('purchase_request:purchase_request_detail', args=[purchase_request.id])
            return redirect(url)
        return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset, 'form': form})
    else:
        ace_data = {
            'description': ace.details_of_expenditure,
            'ace': ace.Ace_id,
            'allocation_code_of_expenditure': ace.allocation_code_of_expenditure,
            'quantity': int(ace.quantity),
            'section': ace.section,
        }
        if ace.section:
            ace_data['section'] = ace.section
        form = acePurchaseRequestForm(initial=ace_data)
        return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset(), 'form': form})
def purchase_request_update(request, purchase_request_id):
    purchase_request = PurchaseRequest.objects.get(id=purchase_request_id)
    pr_items = purchase_request.pritem_set.all()
    itemFormset = inlineformset_factory(PurchaseRequest, PrItem, form=PrItemForm, extra=0 , can_delete=False)
  
    if request.method == 'POST':
        form = PurchaseRequestForm(request.POST, request.FILES, instance=PurchaseRequest(id=purchase_request_id))
        if form.is_valid():
            purchase_request_form = form.save(commit=False)
            purchase_request_form.process = purchase_request.process
            purchase_request_form.id = purchase_request.id
            purchase_request_form.created_at = purchase_request.created_at  
            purchase_request_form.requested_by = purchase_request.requested_by
            purchase_request_form.save()
            formset = itemFormset(request.POST, request.FILES, instance=purchase_request)
            """ remove all approvals for the purchase request"""
            purchase_request.process.approval_set.all().delete()
            if formset.is_valid():
                for it in formset:
                    try:
                        item = it.save(commit=False)
                        item.purchase_request = purchase_request
                        item.save()
                    except: 
                        pass
                url = reverse('purchase_request:purchase_request_detail', args=[purchase_request.id])
                return redirect(url)
            else:
                return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': formset, 'form': form})
        else:
            return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset(instance=purchase_request), 'form': form})
    else:
        form = PurchaseRequestForm(instance=purchase_request)
        return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset(instance=purchase_request), 'form': form})
        
@login_required
def purchase_requests_awaiting_my_action(request):
    """
    for each purchase_request.process in the purchase_requests,  let curent_step = the last purchase_request.process.approval if any else 0 and let next_step =curent_step+1
    then check if  next_step=step.step for purchase_request.process.workflow.step_set filtered by approcer = user.roles.all.
    """
    purchase_requests_to_process = []
    user_roles = request.user.roles.all()
    for purchase_request in PurchaseRequest.objects.all():
        process = purchase_request.process

        if process.approval_set.exists():
            last_approval = process.approval_set.last()
            current_step = last_approval.step.step
        else:
            current_step = 0

        next_step = current_step + 1

        workflow = process.workflow
        step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()
        
        if step:
            purchase_requests_to_process.append(purchase_request)

    return render(request, 'finance/purchase_request/view_all_purchase_requests.html', {'purchase_requests': purchase_requests_to_process})
@login_required
def view_all_purchase_requests(request):
    purchase_requests = PurchaseRequest.objects.all()
    return render(request, 'finance/purchase_request/view_all_purchase_requests.html', {'purchase_requests': purchase_requests})
def uploaduuom(request):
    """upload unit of measurement data to the database"""
    xl = pd.ExcelFile('finance/purchase_request/uom.xlsx')
    df = xl.parse('units')
    data_dict = df.to_dict('records')
    print(data_dict)
    for data in data_dict:
        print(data)
        unit = UnitOfMeasurement(unit=data['UM'], name=data['MUT'])
        unit.save()
    """upload procurement Plan References data to the database"""
    from .grn import data
    procurementPlanReferences= data 
    for procurementPlanReference in procurementPlanReferences:
        print(procurementPlanReference)
        try:
            unit = ProcurementPlanReference(id=procurementPlanReference['id'], name=procurementPlanReference['name'])
            unit.save()
        except:
            pass
    return render(request, 'finance/purchase_request/add_uom.html')

class AddUOM(CreateView):
    model = UnitOfMeasurement
    form_class = UnitOfMeasurementForm
    template_name = 'finance/purchase_request/add_uom.html'
    success_url = reverse_lazy('purchase_request:create_purchase_request')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)
@login_required
def quote_purchase_request(request, purchase_request_id):
    prq = PurchaseRequest.objects.get(id=purchase_request_id)
    pr_items = prq.pritem_set.all()
    itemFormset = inlineformset_factory(Quotation, QuoteItem , form=QuoteItemForm, extra=len(pr_items) , can_delete=False)
    initial_data = [{'pr_item': pr_item,  'quantity': pr_item.quantity} for pr_item in pr_items]
    if request.method == 'POST'and not request.POST.get('quote'):
        quote = QuotationForm(request.POST, request.FILES, instance=Quotation(purchase_request=prq))
        if quote.is_valid():
            quotation = quote.save(commit=False)
            quotation.purchase_request = prq
            quotation.created_by = request.user
            quotation.save()

            formset = itemFormset(request.POST, request.FILES, instance=quotation, initial=initial_data)
            for form in formset:
                if form.is_valid():
                    try:
                        print(quotation.id)
                        item = form.save(commit=False)
                        item.quotation = quotation
                        item.save()
                    except:
                        pass
                else:
                    return render(request, 'finance/purchase_request/create_quote.html', {'formset': formset, 'quote': quote})
            return redirect('purchase_request:purchase_request_detail', purchase_request_id)
        else:
            return render(request, 'finance/purchase_request/create_quote.html', {'formset': formset, 'quote': quote})
    else:
        quote = QuotationForm()
        return render(request, 'finance/purchase_request/create_quote.html', {'formset': itemFormset(initial=initial_data), 'quote': quote})