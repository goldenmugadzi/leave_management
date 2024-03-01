from django.shortcuts import render, redirect
from .models import RFQ, Quotation
from .forms import RFQForm, QuotationFormSet
from it.users.models import *

def create_rfq(request):
    if request.method == 'POST':
        form = RFQForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)

        if form.is_valid() and formset.is_valid():
            rfq = form.save()
            for quotation_form in formset:
                quotation = quotation_form.save(commit=False)
                quotation.rfq = rfq
                quotation.save()

            return redirect('/dashboards/overview/', rfq_id=rfq.rfq_id)
    else:
        form = RFQForm()
        formset = QuotationFormSet()

    return render(request, 'finance/rfq/create_rfq.html', {'form': form, 'formset': formset})

