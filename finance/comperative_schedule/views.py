from django.contrib.auth.decorators import login_required
from it.users.models import *
from approve.views import intiate
from approve.models import Step
from approve.forms import ApprovalForm
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from approve.forms import ApprovalForm
from approve.models import Step
from approve.views import intiate
from django.forms import inlineformset_factory
from .forms import *
from .models import *



@login_required
def bid_on_pr(request, purchase_request_id):
    prq = PurchaseRequest.objects.get(id=purchase_request_id)
    pr_items = prq.pritem_set.all()
    
    supplier_form = SupplierForm(prefix='supplier')
   
    BidItemFormset = inlineformset_factory(Bid, BidItem, form=BidItemForm, extra=len(pr_items), can_delete=False)
    initial_data = [{'pr_item': pr_item, 'quantity': pr_item.quantity} for pr_item in pr_items]

    if request.method == 'POST':
        supplier= None
        if request.POST.get('supplier-name'):
            supplier_form = SupplierForm(request.POST, prefix='supplier')
            if supplier_form.is_valid():
                supplier = supplier_form.save()
            else:
                return render(request, 'finance/comparative_schedule/create_bid.html', {'formset': BidItemFormset(initial=initial_data), 'supplier_form': supplier_form, 'bid_form': BidForm()},)
        
        bid_form = BidForm(request.POST)
        if bid_form.is_valid():
            bid = bid_form.save(commit=False)
            if supplier: bid.supplier = supplier
            elif request.POST.get('supplier'):
                bid.supplier = Supplier.objects.get(id=request.POST.get('supplier'))
            else:
                messages.error(request, 'Please provide a Supplier.')
                return render(request, 'finance/comparative_schedule/create_bid.html', {'formset': BidItemFormset(initial=initial_data), 'supplier_form': supplier_form, 'bid_form': BidForm()})
            bid.purchase_request = prq
            bid.save()

            formset = BidItemFormset(request.POST, instance=bid, initial=initial_data)
            if formset.is_valid():
                formset.save()
                return redirect('purchase_request:purchase_request_detail', purchase_request_id)
            else:
                return render(request, 'finance/comparative_schedule/create_bid.html', {'formset': formset, 'form': form})
        else:
            return render(request, 'finance/comparative_schedule/create_bid.html', {'formset': BidItemFormset(initial=initial_data), 'form': form})
    else:
        return render(request, 'finance/comparative_schedule/create_bid.html', {'formset': BidItemFormset(initial=initial_data),'supplier_form':SupplierForm(prefix='supplier'), 'bid_form': BidForm()})