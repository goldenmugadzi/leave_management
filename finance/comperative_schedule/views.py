from django.contrib.auth.decorators import login_required
from it.users.models import *
from approve.views import intiate
from approve.models import Step
from approve.forms import ApprovalForm
from django.shortcuts import render, redirect
from django.urls import reverse
from django.contrib import messages

from django.shortcuts import get_object_or_404
from django.db.models import Min

from approve.forms import ApprovalForm
from approve.models import Step
from approve.views import intiate
from django.forms import formset_factory
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
                return render(request, 'finance/comparative_schedule/create_bid.html', {'formset': formset, 'supplier_form': supplier_form, 'bid_form': bid_form})
        else:
            return render(request, 'finance/comparative_schedule/create_bid.html', {'formset': BidItemFormset(initial=initial_data), 'supplier_form': supplier_form, 'bid_form': bid_form})
    else:
        return render(request, 'finance/comparative_schedule/create_bid.html', {'formset': BidItemFormset(initial=initial_data),'supplier_form':SupplierForm(prefix='supplier'), 'bid_form': BidForm()})
    

def getsuggestions(request, purchase_request_id):
    purchase_request = get_object_or_404(PurchaseRequest, id=purchase_request_id)
    bids = purchase_request.bid_set.all().order_by('supplier__name')
    purchase_request_items = purchase_request.pritem_set.all()
    # Calculate the lowest offer for each item and create a dictionary of suppliers and their offers
    suppliers = {}
    for pr_item in purchase_request_items:
        pr_item.lowest_offer = pr_item.biditem_set.all().aggregate(Min('price'))['price__min']
        for bid in bids:
            if bid.biditem_set.filter(price=pr_item.lowest_offer).exists():
                suppliers.setdefault(bid.supplier, []).append(bid.biditem_set.filter(price=pr_item.lowest_offer).first())
    # Sort the suppliers by the number of their offers in descending order and select the offers
    sorted_suppliers = sorted(suppliers.items(), key=lambda x: len(x[1]), reverse=True)
    selected_offers = [offer for supplier, offers in sorted_suppliers for offer in offers]
    # Associate each selected offer with its respective pr_item
    for pr_item in purchase_request_items:
        pr_item.selected_offer = next((offer for offer in selected_offers if offer.pr_item == pr_item), None)
    return   (bids, purchase_request_items)
@login_required
def comperative_schedule(request, purchase_request_id):
    bids, purchase_request_items = getsuggestions(request, purchase_request_id)
    BidItemFormSet = formset_factory(BidItemForm, extra=len(purchase_request_items))
    choices_dict = {}
    
    # for bid in bids:
    #     for offer in bid.biditem_set.all():
    # #         print(offer)
    # #         key = (offer.id, f"{offer.price} {offer.bid.supplier.name} {offer.pr_item}")
    #         choices_dict[offer.id] = bid.biditem_set.all()
    #         print(key)
    print(len(bids))
    choices = list(choices_dict.values())
    print(len(choices))
    formset = BidItemFormSet(form_kwargs={'choices': choices})
    return render(request, 'finance/comparative_schedule/comparative_schedule.html', {'bids': bids, 'formset':formset, 'purchase_request_items': purchase_request_items,'purchase_request_id': purchase_request_id})

@login_required
def order_selected(request, purchase_request_id):
    purchase_request = get_object_or_404(PurchaseRequest, id=purchase_request_id)
    bids = purchase_request.bid_set.all().order_by('supplier__name')
    purchase_request_items = purchase_request.pritem_set.all()
    print(purchase_request_items)
    suppliers = {}
    for pr_item in purchase_request_items:
        pr_item.lowest_offer = pr_item.biditem_set.all().aggregate(Min('price'))['price__min']
        for bid in bids:
            if bid.biditem_set.filter(price=pr_item.lowest_offer).exists():
                suppliers.setdefault(bid.supplier, []).append(bid.biditem_set.filter(price=pr_item.lowest_offer).first())

    sorted_suppliers = sorted(suppliers.items(), key=lambda x: len(x[1]), reverse=True)
    selected_offers = [offer for supplier, offers in sorted_suppliers for offer in offers]

    for pr_item in purchase_request_items:
        pr_item.selected_offer = next((offer for offer in selected_offers if offer.pr_item == pr_item), None)

    return render(request, 'finance/comparative_schedule/order_selected.html', 
                  {'bids': bids, 'purchase_request_items': purchase_request_items})