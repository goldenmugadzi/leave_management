
from django.contrib.auth.decorators import login_required

from ACE2.models import Ace2
from .forms import PurchaseRequestForm, acePurchaseRequestForm
from django.views.generic import CreateView
from django.urls import reverse_lazy
from finance.Ace.models import Ace
from it.users.models import *
from approve.views import intiate
from approve.models import Step
from approve.forms import ApprovalForm
from django.shortcuts import render, redirect
from django.urls import reverse
from django.db.models import Q
from approve.forms import ApprovalForm
from django.contrib import messages
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
    # approved_steps, approvalForm, to = ApprovalDetails(request, purchase_request)
    can_cs= False
    for role in request.user.roles.all():
        if role.name=="Requester" and role.app_id.name == 'comparative_schedules':
            can_cs = True
    return render(request, 'finance/purchase_request/purchase_request_detail.html', {'purchase_request': purchase_request, 'can_cs':can_cs })#, 'approved_steps':approved_steps,'approvalForm': approvalForm,'to':to})
    
@login_required
def create_purchase_request(request):
    itemFormset = inlineformset_factory(PurchaseRequest, PrItem, form=PrItemForm, extra=int(request.POST.get('items') or 1), can_delete=False)
    if request.method == 'POST':
        try:prexist=PurchaseRequest.objects.get(pr_no = request.POST.get('pr_no'))
        except:prexist=None
        form = PurchaseRequestForm(request.POST)
        action = request.POST.get("action")
        formset = itemFormset(request.POST)
        if not prexist :
            if  form.is_valid():
                purchase_request = form.save(commit=False)
                # purchase_request.process = intiate(request, 'purchase request')
                purchase_request.requested_by = request.user
                purchase_request.region = request.user.region
                purchase_request.save()
                attachments = request.FILES.getlist('attachments')
                for attachment in attachments:
                    attachment = Attachment(file=attachment, purchase_request=purchase_request)
                    attachment.save()
                try:
                    items_from_sap = pd.ExcelFile(request.FILES.get('upload'))
                    if items_from_sap:
                        df = items_from_sap.parse('Sheet1')
                        data_dict = df.to_dict('records')
                        for data in data_dict:
                            item = PrItem(item_required=data['Short Text'],purchase_request=purchase_request,quantity=data['Quantity requested'],unit_of_measurement=UnitOfMeasurement.objects.get(unit=data['Unit of Measure']) )
                            item.save()
                except:pass
                formset = itemFormset(request.POST,instance=purchase_request)
                if formset.is_valid():
                    for it in formset:
                        try:
                            item = it.save(commit=False)
                            item.purchase_request = purchase_request
                            item.save() 
                        except:
                            pass
                    if action:
                        messages.success(request, 'Purchase request saved successfully.')
                        return render(request, 'finance/purchase_request/create_purchase_request.html', {"attachments":purchase_request.attachment_set.all(),'formset': itemFormset(instance=purchase_request), 'form': form})
                    else:
                        return redirect(reverse('purchase_request:purchase_request_detail', args=[purchase_request.id]))
        
                else:
                    return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset, 'form': form})
                
            return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset, 'form': form})
        else: 
            messages.error(request, 'A Purchase request for this PR Number already exist.')
            return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': formset, 'form': form})
    else:
        form = PurchaseRequestForm(initial={'section':request.user.section})
        return render(request, 'finance/purchase_request/create_purchase_request.html',
                      {'formset': itemFormset(), 'form': form})


@login_required
def create_ace_purchase_request(request, ace_id):
    ace = Ace2.objects.get(Ace_id2=ace_id)
    itemFormset = inlineformset_factory(PurchaseRequest, PrItem, form=PrItemForm, extra=int(request.POST.get('items') or 1), can_delete=False)
    if request.method == 'POST':
        try:prexist=PurchaseRequest.objects.get(pr_no = request.POST.get('pr_no'))
        except:prexist=None
        form = acePurchaseRequestForm(request.POST,instance=ace)
        action = request.POST.get("action")
        formset = itemFormset(request.POST)
        if not prexist :
            if  form.is_valid():
                purchase_request = form.save(commit=False)
                # purchase_request.process = intiate(request, 'purchase request')
                purchase_request.requested_by = request.user
                purchase_request.region = request.user.region
                purchase_request.save()
                attachments = request.FILES.getlist('attachments')
                for attachment in attachments:
                    attachment = Attachment(file=attachment, purchase_request=purchase_request)
                    attachment.save()
                try:
                    items_from_sap = pd.ExcelFile(request.FILES.get('upload'))
                    if items_from_sap:
                        df = items_from_sap.parse('Sheet1')
                        data_dict = df.to_dict('records')
                        for data in data_dict:
                            item = PrItem(item_required=data['Short Text'],purchase_request=purchase_request,quantity=data['Quantity requested'],unit_of_measurement=UnitOfMeasurement.objects.get(unit=data['Unit of Measure']) )
                            item.save()
                except:pass
                formset = itemFormset(request.POST,instance=purchase_request)

                if formset.is_valid():
                    for it in formset:
                        try:
                            item = it.save(commit=False)
                            item.purchase_request = purchase_request
                            item.save()
                        except:
                            pass
                    if action:
                        messages.success(request, 'Purchase request saved successfully.')
                        return render(request, 'finance/purchase_request/create_purchase_request.html', {"attachments":purchase_request.attachment_set.all(),'formset': itemFormset(instance=purchase_request), 'form': form})
                    else:
                        return redirect(reverse('purchase_request:purchase_request_detail', args=[purchase_request.id]))
        
                else:
                    return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset, 'form': form})
                
            return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset, 'form': form})
        else: 
            messages.error(request, 'A Purchase request for this PR Number already exist.')
            return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': formset, 'form': form})
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
        form = acePurchaseRequestForm(initial=ace_data,instance=ace)
        return render(request, 'finance/purchase_request/create_purchase_request.html', {'formset': itemFormset(), 'form': form})
@login_required
def purchase_request_update(request, purchase_request_id):
    purchase_request = PurchaseRequest.objects.get(id=purchase_request_id)
    itemFormset = inlineformset_factory(PurchaseRequest, PrItem, form=PrItemForm, extra=0 , can_delete=False)
    ordered_items = purchase_request.pritem_set.filter(ordered=True)
    if ordered_items:
        form = PurchaseRequestForm(instance=purchase_request)
        messages.error(request, 'You cannot update a purchase request with ordered items.')
        return redirect(reverse('purchase_request:purchase_request_detail', args=[purchase_request.id]))
    elif request.method == 'POST' and purchase_request.requested_by == request.user:
        form = PurchaseRequestUpdateForm(request.POST, instance=PurchaseRequest(id=purchase_request_id))
        attachments = request.FILES.getlist('attachments')
        
        action = request.POST.get("action")
        if form.is_valid():
            purchase_request_form = form.save(commit=False)
            # purchase_request_form.process = purchase_request.process
            purchase_request_form.id = purchase_request.id
            purchase_request_form.created_at = purchase_request.created_at
            purchase_request_form.requested_by = purchase_request.requested_by
            purchase_request_form.save()
            formset = itemFormset(request.POST, instance=purchase_request)
            """ remove all approvals for the purchase request"""
            # purchase_request.process.approval_set.all().delete()
            try:
                items_from_sap = pd.ExcelFile(request.FILES.get('upload'))
                if items_from_sap:
                    df = items_from_sap.parse('Sheet1')
                    data_dict = df.to_dict('records')
                    for data in data_dict:
                        item = PrItem(item_required=data['Short Text'],purchase_request=purchase_request,quantity=data['Quantity requested'],unit_of_measurement=UnitOfMeasurement.objects.get(unit=data['Unit of Measure']) )
                        item.save()
            except:pass
            for attachment in attachments:
                attachment = Attachment(file=attachment, purchase_request=purchase_request)
                attachment.save()

            if formset.is_valid():
                for it in formset:
                    try:
                        item = it.save(commit=False)
                        item.purchase_request = purchase_request
                        item.save()
                    except:
                        pass
                messages.success(request, 'Purchase request saved successfully.')
                if action:
                    return redirect(reverse('purchase_request:purchase_request_update', args=[purchase_request.id]))
                else:
                    return redirect(reverse('purchase_request:purchase_request_detail', args=[purchase_request.id]))
            else:
                messages.error(request, 'An error occurred while updating the purchase request.1')
                return render(request, 'finance/purchase_request/create_purchase_request.html',
                            {'formset': formset, 'form': form})
        else:
            messages.error(request, 'An error occurred while updating the purchase request.2')
            return render(request, 'finance/purchase_request/create_purchase_request.html', {"attachments":purchase_request.attachment_set.all(),'formset': itemFormset(instance=purchase_request), 'form': form})
    elif purchase_request.requested_by == request.user:
        form = PurchaseRequestUpdateForm(instance=purchase_request)
        return render(request, 'finance/purchase_request/create_purchase_request.html', {"attachments":purchase_request.attachment_set.all(),'formset': itemFormset(instance=purchase_request), 'form': form})
    else:
        messages.error(request, 'You are not authorized to update this purchase request.')
        return redirect(reverse('purchase_request:purchase_request_detail', args=[purchase_request.id]))

@login_required
def view_all_purchase_requests(request):
    search_term = request.POST.get('search_term')
    if request.method == 'POST' and search_term :
        purchase_requests = PurchaseRequest.objects.filter(Q(cost_center__name__icontains=search_term) | Q(section__section__icontains=search_term) | Q(requested_by__last_name__icontains=search_term) | Q(scope_of_work__icontains=search_term) | Q(id=search_term) | Q(pr_no__icontains=search_term)| Q(created_at__icontains=search_term)  )
        return render(request, 'finance/purchase_request/view_all_purchase_requests.html', {'purchase_requests': purchase_requests.order_by('-id')[:10]})
    purchase_requests = PurchaseRequest.objects.order_by('-id')[:10]
    return render(request, 'finance/purchase_request/view_all_purchase_requests.html', {'purchase_requests': purchase_requests})

@login_required
def uploaduuom(request):
    """upload unit of measurement data to the database"""
    xl = pd.ExcelFile('finance/purchase_request/uom.xlsx')
    df = xl.parse('units')
    data_dict = df.to_dict('records')
    for data in data_dict:
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
    """upload rfq data to the database"""
    import mysql.connector 

    # Connect to the MySQL database
    # cnx = mysql.connector.connect(
    #     host="172.16.8.10",
    #     user="root",
    #     password="",
    #     database="dms"
    # )

    # Create a cursor object
    # cursor = cnx.cursor()

    # Execute the SQL query
    # sql_query = """
    #     SELECT rfq.rfq_number, rfq.rfq_date, rfq.scope_of_work, 
    #         rfq.date_created, rfq.specifications, rfq.created_by, rfq.section_code, 
    #         rfq.ace, rfq.ace_spec, rfq.proc_ref, rfq.region, required_items.*
    #     FROM required_items
    #     JOIN rfq ON required_items.document_id = rfq.document_id
    #     ORDER BY rfq.id ASC
    # """
    # cursor.execute(sql_query)

    # Fetch all the results
    # results = cursor.fetchall()
    # for item_dict in results:
    #     item = dict(zip(cursor.column_names, item_dict))
    #     try:
    #         created_by = UserProfile.objects.get(username=item['created_by'])
    #     except :
    #         created_by= request.user

    #     section_code = item.get('section_code')
    #     if section_code:
    #         defaults = {
    #             # 'section': Sections.objects.get(code=section_code) or Sections.objects.get(id=1),
    #             'procurement_plan_reference': ProcurementPlanReference.objects.get(id=item['proc_ref'][3:]),
    #             'requested_by': created_by,
    #             # 'created_at': item['date_created'] if "#" not in item['date_created'] else None,
    #             # 'ace': item['ace'],
    #             'scope_of_work': item['scope_of_work'],
    #         }
    #     purchase_request, created = PurchaseRequest.objects.get_or_create(pr_no=item['rfq_number'], defaults=defaults)
    #     try:
    #         pritem = PrItem(item_required=item['item_required'],
    #                     unit_of_measurement = UnitOfMeasurement.objects.get(Q(unit__iexact=item['uom']) | Q(name__iexact=item['uom'])),
    #                     quantity=item['qty'],
    #                     purchase_request=purchase_request,
    #                     ) 
    #     except: print(item['uom'],"failed")
    # Close the cursor and database connection
    # cursor.close()
    # cnx.close()

    return render(request, 'finance/purchase_request/add_uom.html')
@login_required
def del_file(request, id):
    attachment = Attachment.objects.get(id=id)
    purchase_request = attachment.purchase_request
    attachment.delete()
    return redirect('purchase_request:purchase_request_update', purchase_request.id)
class AddUOM(CreateView):
    model = UnitOfMeasurement
    form_class = UnitOfMeasurementForm
    template_name = 'finance/purchase_request/add_uom.html'
    success_url = reverse_lazy('purchase_request:create_purchase_request')

    def form_valid(self, form):
        form.instance.created_by = self.request.user
        return super().form_valid(form)


