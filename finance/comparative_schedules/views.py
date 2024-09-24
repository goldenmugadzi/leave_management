import base64
import csv
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import datetime
from django.db.models import Sum

from it.users.views import ms_exhange_send
from .models import *
from it.users.models import *
from finance.purchase_request.models import ProcurementPlanReference, PurchaseRequest, PrItem, Attachment, UnitOfMeasurement
from ACE2.models import Ace2
from finance.comparative_schedules.models import *
from django.db.models import Q, Exists, OuterRef, Count, F
import pandas as pd
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
import copy
from django.conf import settings
from django.core.files.storage import FileSystemStorage

from django.contrib import messages
APP_NAME = "comparative_schedule"

def add_cost_center(request):
    schedules = ComparativeSchedules.objects.all()
    for schedule in schedules:
        cost_center = schedule.created_by.cost_center
        schedule.cost_center = cost_center
        schedule.save()
    
    return HttpResponse("Cost Center added successfully")

def debug_time(request):
    system_time = datetime.now()
    aware_system_time = timezone.make_aware(system_time, timezone.get_default_timezone())
    django_time = timezone.now()
    
    current_timezone = timezone.get_current_timezone_name()
    django_time_utc = timezone.now()
    local_time = django_time_utc.astimezone(timezone.get_current_timezone())
    
    return HttpResponse(f"System Time: {system_time}<br>"
                        f"Aware System Time: {aware_system_time}<br>"
                        f"Django Time: {django_time}<br>"
                        f"Current Timezone: {current_timezone}<br>"
                        f"Django Time UTC: {django_time_utc}<br>"
                        f"Local Time: {local_time}<br>")

@login_required
def import_old_rfq(request):

    tender_csv = 'tender2.csv'
    rfq_csv = 'rfq2.csv'
    bid_update_csv = 'bid_update2.csv'
    bids_csv = 'bids2.csv'
    items_csv = 'items2.csv'
    required_items_csv = 'required_items2.csv'
    suppliers_csv = 'suppliers2.csv'
    
    # Read the tender CSV file using pandas
    tender_data = pd.read_csv(tender_csv)
    print(tender_data.head())
    rfq_data = pd.read_csv(rfq_csv)
    print(rfq_data.head())
    bid_update_data = pd.read_csv(bid_update_csv)
    print(bid_update_data.head())
    bids_data = pd.read_csv(bids_csv)
    print(bids_data.head())
    items_data = pd.read_csv(items_csv)
    print(items_data.head())
    required_items_data = pd.read_csv(required_items_csv)
    print(required_items_data.head())
    suppliers_data = pd.read_csv(suppliers_csv)
    print(suppliers_data.head())
    
    # save suppliers
    # for index, row in suppliers_data.iterrows():
    #     # supplier_id = row['sup_id']
    #     sup_name = row['supplier']
    #     supplier_exists = Supplier.objects.filter(name=sup_name).first()
    #     if not supplier_exists:
    #         supplier = Supplier(
    #             name = row['supplier'],
    #         )
    #         supplier.save()
    
    # save rfq
    
    # print("..............")
    # for index, row in rfq_data.iterrows():
    #     # "id","document_id","rfq_number","rfq_date","scope_of_work","item_required","qty","date_created","specifications","created_by","section_code","ace","ace_spec","proc_ref"
    #     print("pr: ", row)
    #     print("................")
    #     try:
    #         section = Sections.objects.filter(code=row['section_code']).first() if row['section_code'] else None
    #         cost_center = CostCenter.objects.filter(id=row['section_code']).first() if row['section_code'] else None
    #         proc_ref = str(row["proc_ref"])
    #         if proc_ref.startswith("acc"):
    #             proc_ref = proc_ref.lstrip('acc')
    #         procurement_plan = ProcurementPlanReference.objects.filter(id=proc_ref).first() if proc_ref else None
    #         created_by = None
    #         # print("created by: ", row['created_by'])
    #         if row['created_by']:
    #             # print("using User")
    #             created_by = UserProfile.objects.filter(username=row['created_by']).first()
    #         if created_by == None: 
    #             created_by = UserProfile.objects.filter(username='12345').first()
    #             print("No User: ", row['created_by'])
    #             # print("using No User")
    #         # ace = Ace2.objects.filter(ace=row['ace']).first() if row['ace'] else None
    #         print("created by: ", created_by, datetime.strptime(row['date_created'], "%Y-%m-%d %H:%M:%S"))
    #         dc = timezone.make_aware(datetime.strptime(row['date_created'], "%Y-%m-%d %H:%M:%S")) if row['date_created'] != '0000-00-00 00:00:00' else None
    #         region = Regions.objects.filter(region='EASTERN REGION').first()
    #         pr_ = PurchaseRequest.objects.filter(pr_no=row['rfq_number']).first()
    #         if not pr_:   
    #             pr = PurchaseRequest(
    #                 pr_no = row['rfq_number'],
    #                 section = section,
    #                 cost_center = cost_center,
    #                 procurement_plan_reference = procurement_plan,
    #                 requested_by = created_by,
    #                 created_at = dc,
    #                 # ace = ace,
    #                 scope_of_work = row['scope_of_work'],
    #                 region = region,
    #             )
    #             pr.save()
    #         else:
    #             print("PR Exists")
    #         # att_path = 'uploads/finance/pr/attachments/' + row['specifications'].split('/')[-1] if row['specifications'] else ""

    #         attachments = Attachment(
    #             file = row['specifications'] if row['specifications'] else row['ace_spec'],
    #             purchase_request = pr,
    #         )
    #         attachments.save()
            
    #     except Exception as ex:
    #         print("Error: ", ex)  
    #         return JsonResponse({
    #             "success": False,
    #             "message": "Error: " + str(ex),
    #         }) 

        
    # # save required items
    # try:
    #     for index, row in required_items_data.iterrows():
    #         document_id = row['document_id']
    #         filtered_rows = rfq_data[rfq_data['document_id'] == document_id]
    #         if not filtered_rows.empty:
    #             pr_row = filtered_rows.iloc[0]
    #         else:
    #             pr_row = None
            
    #         if pr_row is not None:
    #             pr_no = pr_row['rfq_number']
    #             pr = PurchaseRequest.objects.filter(pr_no=pr_no).first()

    #             uom = None
    #             if row['uom'] == "None":
    #                 print("uom is None")
    #             if row['uom'] is not None:
    #                 _uom = row['uom']
    #                 if row['uom'] == "kgs":
    #                     _uom = "Kilogram"
    #                 elif row['uom'] == "litres":
    #                     _uom = "Liter"
    #                 elif row['uom'] == "metres":
    #                     _uom = "Meter"
    #                 elif row['uom'] == "each":
    #                     _uom = "Each"
    #                 uom = UnitOfMeasurement.objects.filter(name=_uom).first() 

    #             else: 
    #                 uom = UnitOfMeasurement.objects.filter(name='Each').first()
    #             pr_item_ = PrItem.objects.filter(item_required=row['item_required'], purchase_request=pr).first()
    #             if not pr_item_:
    #                 pr_item = PrItem(
    #                     item_required = row['item_required'],
    #                     quantity = row['qty'],
    #                     unit_of_measurement = uom,
    #                     purchase_request = pr,
    #                 )
    #                 pr_item.save()
    #             else:
    #                 print("Item Exists")
    # except Exception as ex:
    #     print("error: ", ex)
        # return JsonResponse({
        #     "success": False,
        #     "message": "Error: " + str(ex),
        # })
    
    # # save comperative schedules
    # cs_df = pd.DataFrame(columns=['document_id', 'pr_number', 'status', 'message'])
    # try:
    #     # initialize dataframe that records all failied and successfull comperative schedules
    #     for index, tender_row in tender_data.iterrows():
    #         cs_id = tender_row['document_id']
    #         pr_number = tender_row['rfq_no']
    #         print("pr_number: ", pr_number)
    #         if pr_number:
    #             pr = None
    #             if pr_number.startswith("RQ"):
    #                pr = PurchaseRequest.objects.filter().first()
    #             if pr_number.startswith("PR"):
    #                 pr = PurchaseRequest.objects.filter(pr_no=pr_number).first()
    #             else:
    #                 pr = PurchaseRequest.objects.filter(pr_no=pr_number).first()
                
    #             # if pr:
    #             print("pr: ", pr)
    #             pr_ref = None
    #             if pr:
    #                 print("pr_ref obj: ", pr.procurement_plan_reference) 
    #                 pr_ref = 'acc'+pr.procurement_plan_reference.id if pr.procurement_plan_reference else None
    #             print("pr_ref: ", pr_ref)   
    #             proc_plan = ProcurementPlanReference.objects.filter(id=pr_ref).first()
    #             tender_update = bid_update_data[bid_update_data['document_id'] == cs_id]
    #             if not tender_update.empty:
    #                 tender_update_row = tender_update.iloc[0]
    #             else:
    #                 tender_update_row = None
    #             if tender_update_row is not None:
    #                 created_by = UserProfile.objects.filter(username=tender_update_row['user3']).first()
    #                 if created_by == None: 
    #                     created_by = UserProfile.objects.filter(username='ze123').first()
    #                 region = Regions.objects.filter(region='EASTERN REGION').first()
    #                 try:
    #                     cs_ = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    #                     if not cs_:
    #                         currency = Currency.objects.filter(currency='ZWL').first()
    #                         cs_query = ComparativeSchedules(
    #                             cs_id = cs_id,
    #                             pr_id = pr,
    #                             proc_plan = proc_plan,
    #                             scope_of_work = tender_row['scope_of_work'],
    #                             currency = currency,
    #                             closing_date = tender_row['closing_date'],
    #                             closing_time = tender_row['closing_time'],
    #                             advert = tender_row['advert'],
    #                             pr_number = pr_number,
    #                             pr_date = tender_row['pr_date'],
    #                             ref_date = tender_row['pr_date'],
    #                             cs_opened = tender_row['tender_opened'],
    #                             tac_date = tender_row['tac_date'],
    #                             created_by = created_by,
    #                             region = region,
    #                             created_at = tender_row['pr_date'],
    #                         )
    #                         cs_query.save()
    #                         cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr.id if pr else None], 'status': ['Success'], 'message': ['Success']})], ignore_index=True)
    #                     else:
    #                         print("CS Exists")
    #                 except Exception as ex:
    #                     print("Error: ", ex)
    #                     cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': [ex]})], ignore_index=True)
    #             # else:
    #             #     cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['Tender Update not found']})], ignore_index=True)
    #             else:
    #                 cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['PR Object not found']})], ignore_index=True)
    #         else:
    #             cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['PR Number not found']})], ignore_index=True)
    #     cs_df.to_csv('cs_df.csv')
    #     print("cs_df: ", cs_df)
    
    # except Exception as ex:
    #     print("Error: ", ex)
    #     return JsonResponse({
    #         "success": False,
    #         "message": "Error: " + str(ex),
    #     })
        
    # # save bids
    
    try:
        item_df = pd.DataFrame(columns=['document_id', 'item_id', 'sup_id', 'status', 'message'])
        for index, row in bids_data.iterrows():
            cs_id = row['document_id']
            sup_id = row['sup_id']
            item_id	= row['item_id']
            unit_price = row['unit_price']	
            vat = row['vat']
            quoted_qty = row['quoted_qty']
            bid_no = row['bid_no']
            quote_date = row['quote_date']
            rfq_no = row['rfq_no']
            total = row['total']
            bid_document = row['bid_document']
            print("cs_id: ", cs_id)
            cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
            print("cs_query: ", cs_query)
            if cs_query:
                supplier = Supplier.objects.filter(id=sup_id).first() if sup_id else None
                
                if supplier:
                    current_item = items_data[items_data['item_id'] == item_id]
                    if not current_item.empty:
                        current_item_row = current_item.iloc[0]
                        item_name = current_item_row['item']
                        quantity = current_item_row['required_qty']
                        unit_of_measurement = current_item_row['unit_of_measurement']
                        item_query = CSItems(
                            cs_id = cs_query,
                            item_id = item_id,
                            item_name = item_name,
                            quantity = quantity,
                            unit_of_measurement = unit_of_measurement,
                        )
                        item_query.save()    
                    
                        print("bid_no", bid_no)
                        bid = Bids(
                            cs_id = cs_query,
                            item_id = item_query,
                            sup_id = supplier,
                            unit_price = unit_price,
                            vat = vat,
                            quoted_qty = quoted_qty,
                            bid_no = bid_no,
                            quote_date = quote_date,
                            total = total,
                            bid_document = bid_document,
                        )
                        bid.save()
                        item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['SUCCESS'], 'message': ['SUCCESS']})], ignore_index=True)
                    else:
                        item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['Item Not Found']})], ignore_index=True)
                else:
                    item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['DB Supplier Not Found']})], ignore_index=True)
            else:
                item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['Schedule Not Found']})], ignore_index=True)
    except Exception as ex:
        print("Error: ", ex)          
    
    item_df.to_csv('item_df.csv')
    
    # save bid update
    # other_df = pd.DataFrame(columns=['document_id', 'sup_id', 'model', 'status', 'message'])
    # try:
    #     for index, row in bid_update_data.iterrows():
    #         cs_id = row['document_id']
    #         cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    #         if cs_query:
    #             # reason1 = row['reason1']
    #             # reason2 = row['reason2']
    #             # reason3 = row['reason3']
    #             for i in range(1, 30):
                    
    #                 supplier_name = row[f'supplier{i}'] if f'supplier{i}' in row else None	
    #                 payment_terms = row[f'payment_terms{i}'] if f'payment_terms{i}' in row else ""
    #                 bid_validity = row[f'bid_validity{i}'] if f'bid_validity{i}' in row else ""
    #                 delivery_period = row[f'delivery_period{i}'] if f'delivery_period{i}' in row else ""	
    #                 technical_specifications = row[f'technical_specifications{i}'] if f'technical_specifications{i}' in row else ""	
    #                 valid_tax_clearance = row[f'valid_tax_clearance{i}'] if f'valid_tax_clearance{i}' in row else ""	
    #                 registered_with_praz = row[f'registered_with_praz{i}'] if f'registered_with_praz{i}' in row else ""	
    #                 tax_status = row[f'tax_status{i}'] if f'tax_status{i}' in row else ""
    #                 site_visit_done = row[f'site_visit_done{i}'] if f'site_visit_done{i}' in row else ""	
    #                 samples_delivered = row[f'samples_delivered{i}'] if f'samples_delivered{i}' in row else ""
    #                 decision = row[f'decision{i}'] if f'decision{i}' in row else ""
    #                 total = row[f'total{i}'] if f'total{i}' in row else ""
    #                 remarks = row[f'remarks{i}'] if f'remarks{i}' in row else ""
                    
    #                 if supplier_name and supplier_name != "None" and supplier_name != "nan" and supplier_name != "N/A" and supplier_name != "N/A":
    #                     supplier = Supplier.objects.filter(name=supplier_name).first()
    #                     if supplier and supplier != "" and supplier != " " and supplier_name != "None" and supplier_name != "nan" and supplier_name != "N/A" and supplier_name != "N/A":
    #                         Supplier.objects.get_or_create(
    #                             name = supplier_name
    #                         )
                        
    #                     if supplier:
    #                         compliance_query = CSCompliance(
    #                             cs_id = cs_query,
    #                             supplier_id = supplier,
    #                             payment_terms = True if payment_terms == "on" else False,
    #                             bid_validity = True if bid_validity == "on" else False,
    #                             delivery_period = True if delivery_period == "on" else False,
    #                             technical_specifications = True if technical_specifications == "on" else False,
    #                             valid_tax_clearance = True if valid_tax_clearance == "on" else False,
    #                             registered_with_praz = True if registered_with_praz == "on" else False,
    #                             site_visit_done = True if site_visit_done == "on" else False,
    #                             samples_delivered = True if samples_delivered == "on" else False,
    #                             decision = True if decision == "on" else False,
    #                             remarks = remarks if remarks and remarks != "nan" else "",
    #                         )
    #                         compliance_query.save()
                            
    #                         _remark = CSComplianceRemarks(
    #                             cs_id = cs_query,
    #                             supplier_id = supplier,
    #                             remarks = remarks if remarks and remarks != "" and remarks != " " and remarks != "None" and remarks != "nan" and remarks != "N/A" and remarks != "N/A" else "",
    #                         )  
    #                         _remark.save()
    #                         other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["CSCompliance"], 'status': ['Successs'], 'message': ['SUCCESS']})], ignore_index=True) 
                            
    #                     else:
    #                         other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["CSCompliance"], 'status': ['Failed'], 'message': ['DB Supplier not found']})], ignore_index=True) 
    #                 else:
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["CSCompliance"], 'status': ['Failed'], 'message': ['Supplier not found']})], ignore_index=True) 
                
    #             # save ranking
    #             try:
    #                 for i in range(1, 6):
    #                     rank_supplier = row[f'ranking{i}'] if f'ranking{i}' in row else ""
    #                     if rank_supplier and rank_supplier != "None" and rank_supplier != "nan" and rank_supplier != "N/A":
    #                         supplier = Supplier.objects.filter(name=rank_supplier).first()
                            
    #                         bids = Bids.objects.filter(cs_id=cs_query).values('sup_id').annotate(total_sum=Sum('total'))
    #                         compliant_bids = []
    #                         for bid in bids:
    #                             supplier = Supplier.objects.filter(id=bid['sup_id']).first()
    #                             _compliance = CSCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier, decision=True).first()
    #                             if _compliance:
    #                                 compliant_bids.append(bid)
    #                         rankings = {bid['sup_id']: bid['total_sum'] for bid in compliant_bids}
    #                         print("rankings: ", rankings)
    #                         sorted_rankings = sorted(rankings.items(), key=lambda x: x[1])
    #                         print("sorted_rankings: ", sorted_rankings)
    #                         rank = 1
    #                         sorted_rankings_dict = dict(sorted_rankings)
    #                         # search dict for supplier and total
    #                         total = 0
    #                         for key, value in sorted_rankings_dict.items():
    #                             if key == supplier.id:
    #                                 total = value
    #                                 break
                            
    #                         if i == 1:
    #                             decision = "Awarded " + supplier.name + " being the lowest bidder having complied with all the requirements is recommended to provide the goods/service at a total cost of " + cs_query.currency.currency + " " + str(total) + " excluding VAT."
    #                         else:
    #                             decision = ""
    #                         ranking_query = Ranking(
    #                             cs_id = cs_query,
    #                             supplier_id = supplier,
    #                             rank = i,
    #                             remarks = "",
    #                             decision = decision,
    #                             total = total,
    #                         )
    #                         ranking_query.save()
    #                         print("ranking_query: ", ranking_query)
    #                     else:
    #                         print("Ranking Supplier not found")
                    
    #             except Exception as ex:
    #                 print("Error: ", ex)        
    #             # save committee
    #             for i in range(1,10):
    #                 username = row[f'user{i}'] if f'user{i}' in row else None
    #                 status = row[f'status_{i}'] if f'status_{i}' in row else None
    #                 approved_at = row[f'date_{i}'] if f'date_{i}' in row else None
    #                 position = ""
    #                 if i == 1:
    #                     position = "Chairman"
    #                 elif i == 2:
    #                     position = 'Finance'
    #                 elif i == 3:
    #                     position = 'Procurement'
    #                 elif i == 4:
    #                     position = 'User'
    #                 else:
    #                     position = 'Other'
                        
    #                 if status == 1:
    #                     status = "Approved"
    #                 elif status == 2:
    #                     status = "Rejected"
    #                 else:
    #                     status = ""
                    
    #                 # check if committee exists
    #                 if username:
    #                     # check if member exists
    #                     # get member user profile
    #                     member_profile = UserProfile.objects.filter(username=username).first()
    #                     if member_profile:
    #                         committee_query = Committee(
    #                             cs_id = cs_query,
    #                             user = member_profile,
    #                             committee_name = username,
    #                             committee_position = position,
    #                             committee_approval = status,
    #                             committee_date = timezone.make_aware(datetime.strptime(approved_at, "%Y-%m-%d %H:%M:%S")) if approved_at != '0000-00-00 00:00:00' else None
    #                         )
    #                         committee_query.save()
    #                         other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [username], 'model': ["Committee"], 'status': ['Success'], 'message': ['SUCCESS']})], ignore_index=True)
    #                     else:
    #                         other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [username], 'model': ["Committee"], 'status': ['Failed'], 'message': ['member profile empty']})], ignore_index=True)
    #                 else:
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["Committee"], 'status': ['Failed'], 'message': ['username empty']})], ignore_index=True) 
                
    #             finance_user = row['finance_user']
    #             finance_date = row['finance_date']
    #             finance_status = row['finance_status']
      
    #             if finance_status == 1:
    #                 finance_status = "Approved"
    #             elif finance_status == 2:
    #                 finance_status = "Rejected"
    #             else:
    #                 finance_status = ""
                
    #             if finance_user:
    #                 finance_profile = UserProfile.objects.filter(username=finance_user).first()
    #                 if finance_profile:
    #                     finance_query = CSApproval(
    #                         cs_id = cs_query,
    #                         user = finance_profile,
    #                         approver_role = "finance_manager",
    #                         approval = finance_status,
    #                         justification = "",
    #                         approval_date = timezone.make_aware(datetime.strptime(finance_date, "%Y-%m-%d %H:%M:%S")) if finance_date != '0000-00-00 00:00:00' else None,
    #                     )
    #                     finance_query.save()
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["CSApproval"], 'status': ['Success'], 'message': ['SUCCESS']})], ignore_index=True)
    #                 else:
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['DB finance_user empty']})], ignore_index=True)
    #             else:
    #                 other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['finance_user empty']})], ignore_index=True)
                
    #             gm_user = row['gm_user']
    #             gm_date = row['gm_date']
    #             gm_status = row['gm_status']
      
    #             if gm_status == 1:
    #                 gm_status = "Approved"
    #             elif gm_status == 2:
    #                 gm_status = "Rejected"
    #             else:
    #                 gm_status = ""
                
    #             if gm_user:
    #                 gm_profile = UserProfile.objects.filter(username=gm_user).first()
    #                 if gm_profile:
    #                     gm_query = CSApproval(
    #                         cs_id = cs_query,
    #                         user = gm_profile,
    #                         approver_role = "general_manager",
    #                         approval = gm_status,
    #                         justification = "",
    #                         approval_date = timezone.make_aware(datetime.strptime(gm_date, "%Y-%m-%d %H:%M:%S")) if gm_date != '0000-00-00 00:00:00' else None,
    #                     )
    #                     gm_query.save()
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["CSApproval"], 'status': ['Success'], 'message': ['SUCCESS GM']})], ignore_index=True)
    #                 else:
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['GM DB finance_user empty']})], ignore_index=True)
    #             else:
    #                 other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['GM finance_user empty']})], ignore_index=True)
    #         else:
    #             print("cs not found")
    #             other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [""], 'model': ["ComparativeSchedules"], 'status': ['Failed'], 'message': ['Schedule not found']})], ignore_index=True)

    # except Exception as ex:
    #     print("Error: ", ex)   
    
    # other_df.to_csv('other_df.csv')    
      
    return JsonResponse({
        "success": True,
        "message": "Data imported successfully",
        # "data": other_df.to_json()
        # "data": cs_df.to_json()
        # "data": item_df.to_json()
        }, safe=False)

@login_required
def import_old_rfqX(request):

    tender_csv = 'tender2.csv'
    rfq_csv = 'rfq2.csv'
    bid_update_csv = 'bid_update2.csv'
    bids_csv = 'bids2.csv'
    items_csv = 'items2.csv'
    required_items_csv = 'required_items2.csv'
    suppliers_csv = 'suppliers2.csv'
    
    # Read the tender CSV file using pandas
    # tender_data = pd.read_csv(tender_csv)
    # print(tender_data.head())
    rfq_data = pd.read_csv(rfq_csv)
    print(rfq_data.head())
    # bid_update_data = pd.read_csv(bid_update_csv)
    # print(bid_update_data.head())
    # bids_data = pd.read_csv(bids_csv)
    # print(bids_data.head())
    # items_data = pd.read_csv(items_csv)
    # print(items_data.head())
    required_items_data = pd.read_csv(required_items_csv)
    print(required_items_data.head())
    # suppliers_data = pd.read_csv(suppliers_csv)
    # print(suppliers_data.head())
    
    # save suppliers
    # for index, row in suppliers_data.iterrows():
    #     # supplier_id = row['sup_id']
    #     sup_name = row['supplier']
    #     supplier_exists = Supplier.objects.filter(name=sup_name).first()
    #     if not supplier_exists:
    #         supplier = Supplier(
    #             name = row['supplier'],
    #         )
    #         supplier.save()
    
    # save rfq
    
    # print("..............")
    # for index, row in rfq_data.iterrows():
    #     # "id","document_id","rfq_number","rfq_date","scope_of_work","item_required","qty","date_created","specifications","created_by","section_code","ace","ace_spec","proc_ref"
    #     print("pr: ", row)
    #     print("................")
    #     try:
    #         section = Sections.objects.filter(code=row['section_code']).first() if row['section_code'] else None
    #         cost_center = CostCenter.objects.filter(id=row['section_code']).first() if row['section_code'] else None
    #         proc_ref = str(row["proc_ref"])
    #         if proc_ref.startswith("acc"):
    #             proc_ref = proc_ref.lstrip('acc')
    #         procurement_plan = ProcurementPlanReference.objects.filter(id=proc_ref).first() if proc_ref else None
    #         created_by = None
    #         # print("created by: ", row['created_by'])
    #         if row['created_by']:
    #             # print("using User")
    #             created_by = UserProfile.objects.filter(username=row['created_by']).first()
    #         if created_by == None: 
    #             created_by = UserProfile.objects.filter(username='12345').first()
    #             print("No User: ", row['created_by'])
    #             # print("using No User")
    #         # ace = Ace2.objects.filter(ace=row['ace']).first() if row['ace'] else None
    #         print("created by: ", created_by, datetime.strptime(row['date_created'], "%Y-%m-%d %H:%M:%S"))
    #         dc = timezone.make_aware(datetime.strptime(row['date_created'], "%Y-%m-%d %H:%M:%S")) if row['date_created'] != '0000-00-00 00:00:00' else None
    #         pr_ = PurchaseRequest.objects.filter(pr_no=row['rfq_number']).first()
    #         if not pr_:   
    #             pr = PurchaseRequest(
    #                 pr_no = row['rfq_number'],
    #                 section = section,
    #                 cost_center = cost_center,
    #                 procurement_plan_reference = procurement_plan,
    #                 requested_by = created_by,
    #                 created_at = dc,
    #                 # ace = ace,
    #                 scope_of_work = row['scope_of_work'],
    #             )
    #             pr.save()
    #         else:
    #             print("PR Exists")
    #         # att_path = 'uploads/finance/pr/attachments/' + row['specifications'].split('/')[-1] if row['specifications'] else ""

    #         attachments = Attachment(
    #             file = row['specifications'] if row['specifications'] else row['ace_spec'],
    #             purchase_request = pr,
    #         )
    #         attachments.save()
            
    #     except Exception as ex:
    #         print("Error: ", ex)  
    #         return JsonResponse({
    #             "success": False,
    #             "message": "Error: " + str(ex),
    #         }) 

        
    # # save required items
    try:
        for index, row in required_items_data.iterrows():
            document_id = row['document_id']
            filtered_rows = rfq_data[rfq_data['document_id'] == document_id]
            if not filtered_rows.empty:
                pr_row = filtered_rows.iloc[0]
            else:
                pr_row = None
            
            if pr_row is not None:
                pr_no = pr_row['rfq_number']
                pr = PurchaseRequest.objects.filter(pr_no=pr_no).first()

                uom = None
                if row['uom'] == "None":
                    print("uom is None")
                if row['uom'] is not None:
                    _uom = row['uom']
                    if row['uom'] == "kgs":
                        _uom = "Kilogram"
                    elif row['uom'] == "litres":
                        _uom = "Liter"
                    elif row['uom'] == "metres":
                        _uom = "Meter"
                    uom = UnitOfMeasurement.objects.filter(name=_uom).first() 

                else: 
                    uom = UnitOfMeasurement.objects.filter(name='each').first()
                pr_item_ = PrItem.objects.filter(item_required=row['item_required'], purchase_request=pr).first()
                if not pr_item_:
                    pr_item = PrItem(
                        item_required = row['item_required'],
                        quantity = row['qty'],
                        unit_of_measurement = uom,
                        purchase_request = pr,
                    )
                    pr_item.save()
                else:
                    print("Item Exists")
    except Exception as ex:
        print("error: ", ex)
        return JsonResponse({
            "success": False,
            "message": "Error: " + str(ex),
        })
    
    # # save comperative schedules
    # cs_df = pd.DataFrame(columns=['document_id', 'pr_number', 'status', 'message'])
    # try:
    #     # initialize dataframe that records all failied and successfull comperative schedules
    #     for index, tender_row in tender_data.iterrows():
    #         cs_id = tender_row['document_id']
    #         pr_number = tender_row['rfq_no']
    #         print("pr_number: ", pr_number)
    #         if pr_number:
    #             pr = PurchaseRequest.objects.filter(pr_no=pr_number).first()
    #             if not pr:
    #                 pr = PurchaseRequest.objects.filter(pr_no="10000000").first()
    #                 print("pr 001: ", pr)
    #             if pr:
    #                 print("pr: ", pr)
    #                 _proc_plan = tender_row['pr_number']
    #                 proc_plan = ProcPlan.objects.filter(proc_ref=_proc_plan).first()
    #                 tender_update = bid_update_data[bid_update_data['document_id'] == cs_id]
    #                 if not tender_update.empty:
    #                     tender_update_row = tender_update.iloc[0]
    #                 else:
    #                     tender_update_row = None
    #                 if tender_update_row is not None:
    #                     created_by = UserProfile.objects.filter(username=tender_update_row['user3']).first()
    #                     if created_by == None: 
    #                         created_by = UserProfile.objects.filter(username='ze123').first()
    #                     print("tender_row: ", tender_row['region'])
    #                     region = None
    #                     if tender_row['region']:
    #                         region_name = str(tender_row['region']).upper()
    #                         region = Regions.objects.filter(region=region_name).first()
    #                     else:
    #                         region = Regions.objects.filter(id=1).first()
    #                     try:
    #                         currency = Currency.objects.filter(currency='ZWL').first()
    #                         cs_query = ComparativeSchedules(
    #                             cs_id = cs_id,
    #                             pr_id = pr,
    #                             proc_plan = proc_plan,
    #                             scope_of_work = tender_row['scope_of_work'],
    #                             currency = currency,
    #                             closing_date = tender_row['closing_date'],
    #                             closing_time = tender_row['closing_time'],
    #                             advert = tender_row['advert'],
    #                             pr_number = pr_number,
    #                             pr_date = tender_row['pr_date'],
    #                             ref_date = tender_row['pr_date'],
    #                             cs_opened = tender_row['tender_opened'],
    #                             tac_date = tender_row['tac_date'],
    #                             created_by = created_by,
    #                             region = region,
    #                             created_at = tender_row['pr_date'],
    #                         )
    #                         cs_query.save()
    #                         cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr.id], 'status': ['Success'], 'message': ['Success']})], ignore_index=True)
    #                     except Exception as ex:
    #                         print("Error: ", ex)
    #                         cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': [ex]})], ignore_index=True)
    #                 else:
    #                     cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['Tender Update not found']})], ignore_index=True)
    #             else:
    #                 cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['PR Object not found']})], ignore_index=True)
    #         else:
    #             cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [cs_id], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['PR Number not found']})], ignore_index=True)
    #     cs_df.to_csv('cs_df.csv')
    #     print("cs_df: ", cs_df)
    
    # except Exception as ex:
    #     print("Error: ", ex)
        
    # # save bids
    
    # try:
    #     item_df = pd.DataFrame(columns=['document_id', 'item_id', 'sup_id', 'status', 'message'])
    #     for index, row in bids_data.iterrows():
    #         cs_id = row['document_id']
    #         sup_id = row['sup_id']
    #         item_id	= row['item_id']
    #         unit_price = row['unit_price']	
    #         vat = row['vat']
    #         quoted_qty = row['quoted_qty']
    #         bid_no = row['bid_no']
    #         quote_date = row['quote_date']
    #         rfq_no = row['rfq_no']
    #         total = row['total']
    #         bid_document = row['bid_document']
    #         print("cs_id: ", cs_id)
    #         cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    #         print("cs_query: ", cs_query)
    #         if cs_query:
    #             current_supplier = suppliers_data[suppliers_data['sup_id'] == sup_id]
    #             supplier = None
    #             if not current_supplier.empty:
    #                 current_supplier_row = current_supplier.iloc[0]
    #                 supplier_name = current_supplier_row['supplier']
    #                 if supplier_name and supplier_name != "None" and supplier_name != "nan" and supplier_name != "N/A":
    #                     supplier = Supplier.objects.get_or_create(name=supplier_name).first()
                    
    #             else:
    #                 item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [""], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['Supplier Not Found']})], ignore_index=True)
                
    #             if supplier:
    #                 current_item = items_data[items_data['item_id'] == item_id]
    #                 if not current_item.empty:
    #                     current_item_row = current_item.iloc[0]
    #                     item_name = current_item_row['item']
    #                     quantity = current_item_row['required_qty']
    #                     unit_of_measurement = current_item_row['unit_of_measurement']
    #                     item_query = CSItems(
    #                         cs_id = cs_query,
    #                         item_id = item_id,
    #                         item_name = item_name,
    #                         quantity = quantity,
    #                         unit_of_measurement = unit_of_measurement,
    #                     )
    #                     item_query.save()    
                    
    #                     print("bid_no", bid_no)
    #                     bid = Bids(
    #                         cs_id = cs_query,
    #                         item_id = item_query,
    #                         sup_id = supplier,
    #                         unit_price = unit_price,
    #                         vat = vat,
    #                         quoted_qty = quoted_qty,
    #                         bid_no = bid_no,
    #                         quote_date = quote_date,
    #                         total = total,
    #                         bid_document = bid_document,
    #                     )
    #                     bid.save()
    #                     item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['SUCCESS'], 'message': ['SUCCESS']})], ignore_index=True)
    #                 else:
    #                     item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['Item Not Found']})], ignore_index=True)
    #             else:
    #                 item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['DB Supplier Not Found']})], ignore_index=True)
    #         else:
    #             item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'], 'message': ['Schedule Not Found']})], ignore_index=True)
    # except Exception as ex:
    #     print("Error: ", ex)          
    
    # item_df.to_csv('item_df.csv')
    
    # save bid update
    # other_df = pd.DataFrame(columns=['document_id', 'sup_id', 'model', 'status', 'message'])
    # try:
    #     for index, row in bid_update_data.iterrows():
    #         cs_id = row['document_id']
    #         cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    #         if cs_query:
    #             # reason1 = row['reason1']
    #             # reason2 = row['reason2']
    #             # reason3 = row['reason3']
    #             for i in range(1, 30):
                    
    #                 supplier_name = row[f'supplier{i}'] if f'supplier{i}' in row else None	
    #                 payment_terms = row[f'payment_terms{i}'] if f'payment_terms{i}' in row else ""
    #                 bid_validity = row[f'bid_validity{i}'] if f'bid_validity{i}' in row else ""
    #                 delivery_period = row[f'delivery_period{i}'] if f'delivery_period{i}' in row else ""	
    #                 technical_specifications = row[f'technical_specifications{i}'] if f'technical_specifications{i}' in row else ""	
    #                 valid_tax_clearance = row[f'valid_tax_clearance{i}'] if f'valid_tax_clearance{i}' in row else ""	
    #                 registered_with_praz = row[f'registered_with_praz{i}'] if f'registered_with_praz{i}' in row else ""	
    #                 tax_status = row[f'tax_status{i}'] if f'tax_status{i}' in row else ""
    #                 site_visit_done = row[f'site_visit_done{i}'] if f'site_visit_done{i}' in row else ""	
    #                 samples_delivered = row[f'samples_delivered{i}'] if f'samples_delivered{i}' in row else ""
    #                 decision = row[f'decision{i}'] if f'decision{i}' in row else ""
    #                 total = row[f'total{i}'] if f'total{i}' in row else ""
    #                 remarks = row[f'remarks{i}'] if f'remarks{i}' in row else ""
                    
    #                 if supplier_name and supplier_name != "None" and supplier_name != "nan" and supplier_name != "N/A" and supplier_name != "N/A":
    #                     supplier = Supplier.objects.filter(name=supplier_name).first()
    #                     if supplier and supplier != "" and supplier != " " and supplier_name != "None" and supplier_name != "nan" and supplier_name != "N/A" and supplier_name != "N/A":
    #                         Supplier.objects.get_or_create(
    #                             name = supplier_name
    #                         )
                        
    #                     if supplier:
    #                         compliance_query = CSCompliance(
    #                             cs_id = cs_query,
    #                             supplier_id = supplier,
    #                             payment_terms = True if payment_terms == "on" else False,
    #                             bid_validity = True if bid_validity == "on" else False,
    #                             delivery_period = True if delivery_period == "on" else False,
    #                             technical_specifications = True if technical_specifications == "on" else False,
    #                             valid_tax_clearance = True if valid_tax_clearance == "on" else False,
    #                             registered_with_praz = True if registered_with_praz == "on" else False,
    #                             site_visit_done = True if site_visit_done == "on" else False,
    #                             samples_delivered = True if samples_delivered == "on" else False,
    #                             decision = True if decision == "on" else False,
    #                             remarks = remarks if remarks and remarks != "nan" else "",
    #                         )
    #                         compliance_query.save()
                            
    #                         _remark = CSComplianceRemarks(
    #                             cs_id = cs_query,
    #                             supplier_id = supplier,
    #                             remarks = remarks if remarks and remarks != "" and remarks != " " and remarks != "None" and remarks != "nan" and remarks != "N/A" and remarks != "N/A" else "",
    #                         )  
    #                         _remark.save()
    #                         other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["CSCompliance"], 'status': ['Successs'], 'message': ['SUCCESS']})], ignore_index=True) 
                            
    #                     else:
    #                         other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["CSCompliance"], 'status': ['Failed'], 'message': ['DB Supplier not found']})], ignore_index=True) 
    #                 else:
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["CSCompliance"], 'status': ['Failed'], 'message': ['Supplier not found']})], ignore_index=True) 
                
    #             # save ranking
    #             try:
    #                 for i in range(1, 6):
    #                     rank_supplier = row[f'ranking{i}'] if f'ranking{i}' in row else ""
    #                     if rank_supplier and rank_supplier != "None" and rank_supplier != "nan" and rank_supplier != "N/A":
    #                         supplier = Supplier.objects.filter(name=rank_supplier).first()
                            
    #                         bids = Bids.objects.filter(cs_id=cs_query).values('sup_id').annotate(total_sum=Sum('total'))
    #                         compliant_bids = []
    #                         for bid in bids:
    #                             supplier = Supplier.objects.filter(id=bid['sup_id']).first()
    #                             _compliance = CSCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier, decision=True).first()
    #                             if _compliance:
    #                                 compliant_bids.append(bid)
    #                         rankings = {bid['sup_id']: bid['total_sum'] for bid in compliant_bids}
    #                         print("rankings: ", rankings)
    #                         sorted_rankings = sorted(rankings.items(), key=lambda x: x[1])
    #                         print("sorted_rankings: ", sorted_rankings)
    #                         rank = 1
    #                         sorted_rankings_dict = dict(sorted_rankings)
    #                         # search dict for supplier and total
    #                         total = 0
    #                         for key, value in sorted_rankings_dict.items():
    #                             if key == supplier.id:
    #                                 total = value
    #                                 break
                            
    #                         if i == 1:
    #                             decision = "Awarded " + supplier.name + " being the lowest bidder having complied with all the requirements is recommended to provide the goods/service at a total cost of " + cs_query.currency.currency + " " + str(total) + " excluding VAT."
    #                         else:
    #                             decision = ""
    #                         ranking_query = Ranking(
    #                             cs_id = cs_query,
    #                             supplier_id = supplier,
    #                             rank = i,
    #                             remarks = "",
    #                             decision = decision,
    #                             total = total,
    #                         )
    #                         ranking_query.save()
    #                         print("ranking_query: ", ranking_query)
    #                     else:
    #                         print("Ranking Supplier not found")
                    
    #             except Exception as ex:
    #                 print("Error: ", ex)        
    #             # save committee
    #             for i in range(1,10):
    #                 username = row[f'user{i}'] if f'user{i}' in row else None
    #                 status = row[f'status_{i}'] if f'status_{i}' in row else None
    #                 approved_at = row[f'date_{i}'] if f'date_{i}' in row else None
    #                 position = ""
    #                 if i == 1:
    #                     position = "Chairman"
    #                 elif i == 2:
    #                     position = 'Finance'
    #                 elif i == 3:
    #                     position = 'Procurement'
    #                 elif i == 4:
    #                     position = 'User'
    #                 else:
    #                     position = 'Other'
                        
    #                 if status == 1:
    #                     status = "Approved"
    #                 elif status == 2:
    #                     status = "Rejected"
    #                 else:
    #                     status = ""
                    
    #                 # check if committee exists
    #                 if username:
    #                     # check if member exists
    #                     # get member user profile
    #                     member_profile = UserProfile.objects.filter(username=username).first()
    #                     if member_profile:
    #                         committee_query = Committee(
    #                             cs_id = cs_query,
    #                             user = member_profile,
    #                             committee_name = username,
    #                             committee_position = position,
    #                             committee_approval = status,
    #                             committee_date = timezone.make_aware(datetime.strptime(approved_at, "%Y-%m-%d %H:%M:%S")) if approved_at != '0000-00-00 00:00:00' else None
    #                         )
    #                         committee_query.save()
    #                         other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [username], 'model': ["Committee"], 'status': ['Success'], 'message': ['SUCCESS']})], ignore_index=True)
    #                     else:
    #                         other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [username], 'model': ["Committee"], 'status': ['Failed'], 'message': ['member profile empty']})], ignore_index=True)
    #                 else:
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [supplier_name], 'model': ["Committee"], 'status': ['Failed'], 'message': ['username empty']})], ignore_index=True) 
                
    #             finance_user = row['finance_user']
    #             finance_date = row['finance_date']
    #             finance_status = row['finance_status']
      
    #             if finance_status == 1:
    #                 finance_status = "Approved"
    #             elif finance_status == 2:
    #                 finance_status = "Rejected"
    #             else:
    #                 finance_status = ""
                
    #             if finance_user:
    #                 finance_profile = UserProfile.objects.filter(username=finance_user).first()
    #                 if finance_profile:
    #                     finance_query = CSApproval(
    #                         cs_id = cs_query,
    #                         user = finance_profile,
    #                         approver_role = "finance_manager",
    #                         approval = finance_status,
    #                         justification = "",
    #                         approval_date = timezone.make_aware(datetime.strptime(finance_date, "%Y-%m-%d %H:%M:%S")) if finance_date != '0000-00-00 00:00:00' else None,
    #                     )
    #                     finance_query.save()
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["CSApproval"], 'status': ['Success'], 'message': ['SUCCESS']})], ignore_index=True)
    #                 else:
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['DB finance_user empty']})], ignore_index=True)
    #             else:
    #                 other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['finance_user empty']})], ignore_index=True)
                
    #             gm_user = row['gm_user']
    #             gm_date = row['gm_date']
    #             gm_status = row['gm_status']
      
    #             if gm_status == 1:
    #                 gm_status = "Approved"
    #             elif gm_status == 2:
    #                 gm_status = "Rejected"
    #             else:
    #                 gm_status = ""
                
    #             if gm_user:
    #                 gm_profile = UserProfile.objects.filter(username=gm_user).first()
    #                 if gm_profile:
    #                     gm_query = CSApproval(
    #                         cs_id = cs_query,
    #                         user = gm_profile,
    #                         approver_role = "general_manager",
    #                         approval = gm_status,
    #                         justification = "",
    #                         approval_date = timezone.make_aware(datetime.strptime(gm_date, "%Y-%m-%d %H:%M:%S")) if gm_date != '0000-00-00 00:00:00' else None,
    #                     )
    #                     gm_query.save()
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["CSApproval"], 'status': ['Success'], 'message': ['SUCCESS GM']})], ignore_index=True)
    #                 else:
    #                     other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['GM DB finance_user empty']})], ignore_index=True)
    #             else:
    #                 other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["CSApproval"], 'status': ['Failed'], 'message': ['GM finance_user empty']})], ignore_index=True)
    #         else:
    #             print("cs not found")
    #             other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [""], 'model': ["ComparativeSchedules"], 'status': ['Failed'], 'message': ['Schedule not found']})], ignore_index=True)

    # except Exception as ex:
    #     print("Error: ", ex)   
    
    # other_df.to_csv('other_df.csv')    
      
    return JsonResponse({
        "success": True,
        "message": "Data imported successfully",
        # "data": other_df.to_json()
        # "data": cs_df.to_json()
        # "data": item_df.to_json()
        }, safe=False)

def clear_approvals(cs_id):

    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
        
    committee = Committee.objects.filter(cs_id=cs_query).all()
    if committee:
        for member in committee:
            member.committee_approval = ""
            member.committee_status = ""
            member.save()
    
    approvals = CSApproval.objects.filter(cs_id=cs_query).all()
    if approvals:
        for approval in approvals:
            approval.approval = ""
            approval.justification = ""
            # approval.approval_date = None
            approval.save()
            
    return True

def getUserFMGMRoles(user):
    print("user: ", user.username, user.id  )
    fm_role, gm_role, procurement_role = False, False, False
    
    try:
        user_comparative_schedule_role = user.roles.filter(application=APP_NAME).first()

        if user_comparative_schedule_role.application == APP_NAME:
            if user_comparative_schedule_role.role == "check":
                fm_role = True
            if user_comparative_schedule_role.role == "approve":
                gm_role = True
            if user_comparative_schedule_role.role == "procurement":
                procurement_role = True
        
    except Exception as ex:
        # messages.error(request, "Warning: Please not that you do not have the required roles to access this page.")
        print("Error: ", ex)
    
    return fm_role, gm_role, procurement_role

def notify_user(user_, msg, notification_type, url, id):
            
        Notification.objects.create(
            user=user_,
            message=msg,
            notification_type=notification_type,
            notification_id=id,
            url=url,
            created_at=datetime.now(),
        )
        
        # ms_exhange_send(subject=notification_type, body=msg, to_recipients=[user_.email], cc_recipients=[])
        return True
 
def notification_update(user, id):
    notification = Notification.objects.filter(user=user, notification_id=id).first()
    if notification:
        notification.is_read = True
        notification.save()
    return True

@login_required    
def get_comperative_schedules(request):
    
    user_id = request.user.id
    print("user name: ", request.user.username, request.user.id)
    user = UserProfile.objects.filter(id=user_id).first()
    print("user: ", user.username, user.id)
    
    fm_role, gm_role, procurement_role = False, False, False
    
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user)
    print("roles ,,,, : ", fm_role, gm_role, procurement_role)

    if fm_role == True:
        return redirect('/comperative_schedule/pending_fm_approval')
    elif gm_role == True:
        return redirect('/comperative_schedule/pending_gm_approval')
    elif procurement_role == True:
        return redirect('/comperative_schedule/your_schedules')
    else:
        return redirect('/comperative_schedule/pending_commitee')

@login_required
def your_comperative_schedules(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user)

    user_page = 'finance/comparative_schedules/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, { 
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role,
            "page_title": "RFQ Comparative Schedules",})

@login_required
def get_all_schedules(request):
    
    user_id = request.user.id
    print("user name: ", request.user.username, request.user.id)
    user_profile = UserProfile.objects.filter(id=user_id).first()
    print("user: ", user_profile.username, user_profile.id)
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    return render(request, user_page, { "fm_role": fm_role, "gm_role": gm_role, "procurement_role": procurement_role, "page_title": "RFQ Comparative Schedules"})

@login_required
def get_pending_committee(request):
    
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
        
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)   
        
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, {
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role,
            "page_title": "RFQ Comparative Schedules"})

@login_required
def get_pending_gm_approval(request):
    
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, {
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role,
            "page_title": "RFQ Comparative Schedules"})

@login_required
def get_pending_fm_approval(request):
    
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    user_page = 'finance/comparative_schedules/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, { 
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role,
            "page_title": "RFQ Comparative Schedules"})

def get_your_schedules(user_id, search_value=None, column_name=None, region=None):
    
    cs = ComparativeSchedules.objects.filter(
        region=region,
        created_by_id=user_id,
        cancelled=False
    ).all()

    # Filter based on search value
    if search_value:
                cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )
    if column_name:    
        cs = cs.order_by(column_name)

    return cs

def get_pending_committee_table(user_id, search_value=None, column_name=None, region=None):

    print("user id: ", user_id)
    # fetch schedules if user exists in the committee and has not yet approved
    cs = ComparativeSchedules.objects.filter(
        Q(committee__committee_approval=None) | Q(committee__committee_approval=""),
        Q(committee__user_id=user_id),
        cancelled = False,
        region=region,
    ).all()

    # Filter based on search value
    if search_value:
        cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )
    
    if column_name:    
        cs = cs.order_by(column_name)

    return cs

def get_finance_manager(user_id, search_value=None, column_name=None, region=None):
    
    cs = ComparativeSchedules.objects.annotate(
        approved_count=Count('committee', filter=Q(committee__committee_approval="Approved")),
        not_approved_count=Count('committee', filter=Q(committee__committee_approval="")),
        rejected_count=Count('committee', filter=Q(committee__committee_approval="Rejected")),
        committee_count=Count('committee')
    ).filter(
        approved_count=F('committee_count'),
        committee_count__gt=2,
        not_approved_count=0,
        rejected_count=0,
        csapproval__approval=None,
        cancelled = False,
        region=region
    ).distinct()

    # Filter based on search value
    if search_value:
                cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )
    
    if column_name:    
        cs = cs.order_by(column_name)

    return cs

def get_general_manager(user_id, search_value=None, column_name=None, region=None):
    # fetch all pending approvals
    cs = ComparativeSchedules.objects.annotate(
        all_approved=Exists(
            Committee.objects.filter(
                cs_id=OuterRef('pk'),
                committee_approval="Approved"
            )
        ),
        any_not_approved=Exists(
            Committee.objects.filter(
                cs_id=OuterRef('pk'),
                committee_approval="Approved"
            )
        ),
        gm_approved=Exists(
            CSApproval.objects.filter(
                cs_id=OuterRef('pk'),
                approver_role="general_manager",
                approval="Approved"
            )
        ),
        any_reject=Exists(
            CSApproval.objects.filter(
                cs_id=OuterRef('pk'),
                approval="Rejected"
            )
        ),
    ).filter(
        all_approved=True,
        any_not_approved=True,
        gm_approved=False,
        csapproval__approver_role="finance_manager",
        csapproval__approval="Approved",
        cancelled=False,
        any_reject=False,
        region=region
    ).distinct()
    
    # Filter based on search value
    if search_value:
                cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )
    
    if column_name:    
        cs = cs.order_by(column_name)

    return cs

def get_all_schedules_table(user_id, search_value=None, column_name=None, region=None):
    
    cs = ComparativeSchedules.objects.filter(region=region, cancelled=False).all()
    
    # Filter based on search value
    if search_value:
        cs = cs.filter(
        Q(cs_id__icontains=search_value) |
        Q(scope_of_work__icontains=search_value) 
        )

    if column_name:
        cs = cs.order_by(column_name)


    return cs

def get_filtered_schedules(user_id, search_value, column_name, user_region, status, station, pickStation, start_date, end_date):
        print("user id: ", user_id, "search_value: ", search_value, "column_name: ", column_name, "user_region: ", user_region, "status: ", status, "station: ", station, "pickStation: ", pickStation, "start_date: ", start_date, "end_date: ", end_date)
        cs = ComparativeSchedules.objects.filter(
            region=user_region,
        ).all()
        
        try:
        
            if status:
                if status == "Pending Committee":
                    cs = cs.filter(
                        Q(committee__committee_approval=None) | Q(committee__committee_approval="")).exclude(
                            Q(committee__committee_approval="Rejected"))
                if status == "Pending Finance":
                    cs = cs.filter(Q(csapproval__approval="") | Q(csapproval__approval=None)).exclude(
                        Q(committee__committee_approval=None) | Q(committee__committee_approval="") | Q(committee__committee_approval="Rejected")
                    )
                    print("cs: ", cs)
                if status == "Pending General Manager":
                    cs = cs.filter(Q(csapproval__approval="Approved"), 
                            Q(csapproval__approver_role="finance_manager")
                        ).exclude(
                        Q(csapproval__approval="Rejected") | Q(csapproval__approver_role="general_manager")
                    )
                if status == "Complete":
                    cs = cs.filter(Q(csapproval__approval="Approved"), 
                            Q(csapproval__approver_role="general_manager")).exclude(
                        Q(csapproval__approval="Rejected") | Q(csapproval__approval="") | Q(csapproval__approval=None)
                    )
                if status == "Rejected":
                    cs = cs.filter(
                        Q(csapproval__approval="Rejected") | Q(committee__committee_approval="Rejected")
                    )
                if status == "Cancelled":
                    cs = cs.filter(cancelled=True)

            if station and pickStation:
                if station == "Sections":
                    section = Sections.objects.filter(id=pickStation).first()
                    if section:
                        cs = cs.filter(section=section)
                    print("cs: ", cs)   
                if station == "Cost Centre":
                    cost_center = CostCenter.objects.filter(id=pickStation).first()
                    if cost_center:
                        cs = cs.filter(cost_center=cost_center)
                    print("cs: ", cs)
                if station == "Region":
                    region_ = Regions.objects.filter(id=pickStation).first()
                    print("region: ", region_)
                    if region_:
                        cs = cs.filter(region=region_)
            
            # Filter based on search value
            if search_value:
                cs = cs.filter(
                Q(cs_id__icontains=search_value) |
                Q(scope_of_work__icontains=search_value) 
                )
                
            if start_date and end_date:
                cs = cs.filter(created_at__range=[start_date, end_date])
            
            if column_name:
                cs = cs.order_by(column_name)
        except Exception as ex:
            print("Error: ", ex)
        
        return cs

def get_csv_export(request):
    
    print("export csv")
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="rfq.csv"'
    try:    
        user_id = request.user.id
        try:
            user_region = Regions.objects.filter(region=request.user.region).first()
        except Exception as ex:
            user_region = None
            print("error: ",  ex)
        status = request.GET.get('status')
        station = request.GET.get('station')
        pickStation = request.GET.get('pick_station')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        data = get_filtered_schedules(user_id=user_id, search_value="", column_name="", user_region=user_region, status=status, station=station, pickStation=pickStation, start_date=start_date, end_date=end_date)
        custom_data = add_details(data)
        # build csv file and return as response
        try:
            writer = csv.writer(response)
            writer.writerow(['CS ID', 'PR ID', 'PR Number', 'PR Date', 'Scope of Work', 'Closing Date', 'Closing Time', 'Advert', 'PR Number', 'PR Date', 'CS Opened', 'TAC Date', 'Created By', 'Committee Approval', 'GM Approval', 'FM Approval', 'Section', 'Region', 'Created At'])
            for item in custom_data:
                try:
                    writer.writerow([item['cs_id'], item['pr_id'], item['pr_number'], item['pr_date'], item['scope_of_work'], item['closing_date'], item['closing_time'], item['advert'], item['pr_number'], item['pr_date'], item['cs_opened'], item['tac_date'], item['created_by'], item['committee_approval'], item['gm_approval'], item['fm_approval'], item['section'], item['region'], item['created_at']])
                    
                except Exception as ex:
                    print("For Writting to CSV: ", ex)
        except Exception as ex:
            print("Error Writting to CSV: ", ex)
    except Exception as ex:
        print("Error: ", ex)
    
    
    return response

def add_details(cs):
    cs_list = []
    committee_reject_reason = ""
    
    for c in cs:
        committee_approval = ""
        gm_approval = None
        fm_approval = None
        committee = Committee.objects.filter(
                cs_id=c.id
        ).all()
        
        if len(committee) > 0:            
            committee_approved = all([c.committee_approval == "Approved" for c in committee])
            if committee_approved:
                committee_approval = "Approval Complete"
                fm_approval = CSApproval.objects.filter(
                    cs_id=c,
                    approver_role="finance_manager",
                ).first()
                    
                gm_approval = CSApproval.objects.filter(
                    cs_id=c,
                    approver_role="general_manager",
                ).first()
            else:
                committee_approval = "Pending"
                fm_approval = None
                gm_approval = None
                
                committee_pending = Committee.objects.filter(
                    cs_id=c,
                    committee_approval__in=["", None]
                ).exists()

                if committee_pending:
                    committee_approval = "Pending"
            
                committee_rejected = Committee.objects.filter(
                cs_id=c,
                    committee_approval="Rejected"
                ).first()

                if committee_rejected:
                    committee_reject_reason = committee_rejected.justification
                    committee_approval = "Rejected"
        else:
            committee_approval = "Pending"
            fm_approval = None
            gm_approval = None
        
        print("c.pr_id_id: ", c.pr_id_id)
        pr = PurchaseRequest.objects.filter(id=c.pr_id_id).first()
        user = UserProfile.objects.filter(id=c.created_by_id).first()
        region = Regions.objects.filter(id=c.region_id).first()
        section = Sections.objects.filter(id=c.section_id).first()
               
        try:
            cs_list.append({
                "cs_id": c.cs_id,
                "pr_id": pr.id if pr else "",
                "pr_number": c.pr_number,
                "pr_date": c.pr_date,
                "scope_of_work": c.scope_of_work,
                "closing_date": c.closing_date,
                "closing_time": c.closing_time,
                "advert": c.advert,
                "pr_number": c.pr_number,
                "pr_date": c.pr_date,
                "cs_opened": c.cs_opened,
                "tac_date": c.tac_date,
                "created_by": user.username if user else None,
                "committee_approval": committee_approval,
                "committee_reject_reason": committee_reject_reason,
                "gm_approval": gm_approval.approval if gm_approval else "Pending",
                "gm_reject_reason": gm_approval.justification if gm_approval else "",
                "fm_approval": fm_approval.approval if fm_approval else "Pending",
                "fm_reject_reason": fm_approval.justification if fm_approval else "",
                "section": section.section if section else "",
                "region": region.region if region else "",
                "created_at": c.created_at.strftime("%Y-%m-%d %H:%M") if c.created_at else ""
            })
        except Exception as ex:
            print("Error: ", ex)
            
    return cs_list

def datatable_data(request, view):
    
    user_id = request.user.id
    try:
        user_region = Regions.objects.filter(region=request.user.region).first()
    except Exception as ex:
        user_region = None
        print("error: ",  ex)
    draw = int(request.GET.get('draw', default=1))
    start = int(request.GET.get('start', default=0))
    length = int(request.GET.get('length', default=10))
    search_value = request.GET.get('search[value]', default='')

    # Sorting
    order_column = request.GET.get('order[0][column]')
    order = request.GET.get('order[0][dir]')
    column_name = ""
    if order_column:
        column_name = request.GET.get(f'columns[{order_column}][data]')
        if order == 'desc':
            column_name = f'-{column_name}'

    data = []
    if view == "your_schedules":
        data = get_your_schedules(user_id, search_value, column_name, user_region)
    elif view == "pending_committee":
        data = get_pending_committee_table(user_id, search_value, column_name, user_region)
    elif view == "pending_fm":
        data = get_finance_manager(user_id, search_value, column_name, user_region)
    elif view == "pending_gm":
        data = get_general_manager(user_id, search_value, column_name, user_region)
    elif view == "all_schedules":
        print("region inside: ", user_region)
        data = get_all_schedules_table(user_id, search_value, column_name, user_region)
    elif view == "filter":
        status = request.GET.get('status')
        station = request.GET.get('station')
        pickStation = request.GET.get('pick_station')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        data = get_filtered_schedules(user_id, search_value, column_name, user_region, status, station, pickStation, start_date, end_date)
    
    # Total number of records before filtering
    total = len(data)
    print("total: ", total)
    # Pagination
    paginator = Paginator(data, length)
    page_number = start // length + 1
    page_obj = paginator.get_page(page_number)

    # Prepare response
    print("adding details")
    data = add_details(page_obj.object_list)
    return JsonResponse({
        'draw': draw,
        'recordsTotal': total,
        'recordsFiltered': total,
        'data': data
    })


@login_required
def get_comperative_schedule(request, cs_id):
    
    username = request.user.username
    return render(request, 'finance/comparative_schedules/cs_create.html', {
        "cs_id": cs_id,
        "username": username,
    })

@login_required
def create_comperative_schedule(request):

    username = request.user.username
    return render(request, 'finance/comparative_schedules/cs_create.html', {
        "username": username,
    })

@login_required
def get_comperative_schedule_data(request, cs_id):
    
    request_user = request.user
    request_user_profile = UserProfile.objects.filter(id=request_user.id).first()
    user_comparative_schedule_role = request_user_profile.get_user_role_for_application(APP_NAME)           

    cs = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    pr = None
    proc_plan = ""
    if cs:
        try:
            pr = PurchaseRequest.objects.filter(id=cs.pr_id_id).first()
            proc_plan = cs.proc_plan if cs.proc_plan else ""
        except Exception as ex:
            print("Error: ", ex)
            
    proc_plans = ProcPlan.objects.all()
    currencies = Currency.objects.all()
    user = UserProfile.objects.filter(id=cs.created_by_id).first()
    region = Regions.objects.filter(id=cs.region_id).first()
    section = Sections.objects.filter(id=cs.section_id).first()
    items = CSItems.objects.filter(cs_id=cs).all()
    cs_items = CSRequiredItems.objects.filter(cs_id=cs).all()
    bids = Bids.objects.filter(cs_id=cs).all()

    compliance = CSCompliance.objects.filter(cs_id=cs).all()
    complianceRemarks = CSComplianceRemarks.objects.filter(cs_id=cs).all()
    
    rankings = Ranking.objects.filter(cs_id=cs).all()
    committee = Committee.objects.filter(cs_id=cs).all()
    gm_approval = CSApproval.objects.filter(cs_id=cs, approver_role="general_manager").first()
    fm_approval = CSApproval.objects.filter(cs_id=cs, approver_role="finance_manager").first()
    
    suppliers = Supplier.objects.all()
    pr_items = PrItem.objects.filter(purchase_request=cs.pr_id_id, ordered=False).all()
    users = UserProfile.objects.filter(region=cs.region).all()
    
    items_list = []
    for item in items:
        items_list.append({
            "item_id": item.item_id,
            "item_required": item.item_name,
            "quantity": item.quantity,
            "unit_of_measurement": item.unit_of_measurement,
            "created_at": item.created_at,
        })
        
    grouped_by_bid = {}
    grouped_data = {}
    for bid in bids:
        print("bid: ", bid.sup_id.name, bid.bid_no)
        try:
            bid_no = bid.bid_no
            if bid_no not in grouped_data:
                encoded_file_data = ""
                if bid.bid_document:
                    try:
                        with open(bid.bid_document, 'rb') as f:
                            file_data = f.read()
                        encoded_file_data = base64.b64encode(file_data).decode('utf-8')
                    except Exception as ex:
                        print("Error: ", ex)
                grouped_data[bid_no] = {
                    'bid_count': bid.bid_no,
                    'supplier_name': bid.sup_id.name,
                    'bid_date': bid.quote_date,
                    'encoded_bid_document': encoded_file_data,
                    'bid_document': None,
                    'items': []
                }
            grouped_data[bid_no]['items'].append({
                'item_id': bid.item_id.item_id,
                'item_required': bid.item_id.item_name,  # assume this is constant
                'quantity': bid.item_id.quantity,
                'unit_of_measurement': bid.item_id.unit_of_measurement,
                'unit_price': bid.unit_price,
                'vat': bid.vat,
                'total_price': bid.total,
            })
        except Exception as ex:
            print("Error: ", ex)
    result = list(grouped_data.values())
        
    compliance_list = []
    for comp in compliance:
        sup_name = ""
        try:
            sup_name = comp.supplier_id.name
        except Exception as ex:
            print("Error: ", ex)
        
        if sup_name:
            compliance_list.append({
                "supplier_name": sup_name,
                "payment_terms": comp.payment_terms,
                "bid_validity": comp.bid_validity,
                "delivery_period": comp.delivery_period,
                "technical_specifications": comp.technical_specifications,
                "valid_tax_clearance": comp.valid_tax_clearance,
                "registered_with_praz": comp.registered_with_praz,
                "site_visit": comp.site_visit_done,
                "samples_required": comp.samples_delivered,
                "decision": comp.decision,
                "remarks": comp.remarks,
                "created_at": comp.created_at,
            })
    
    compliance_remarks = []
    for remark in complianceRemarks:
        try:
            compliance_remarks.append({
            "supplier": remark.supplier_id.id,
            "supplier_name": remark.supplier_id.name,
            "remarks": remark.remarks,
            })
        except Exception as ex:
            print("Error: ", ex)
        
    rankings_list = []
    for rank in rankings:
        try:
            supplier = Supplier.objects.filter(id=rank.supplier_id.id).first()
            rankings_list.append({
                "supplier_name": supplier.name if supplier else "",
                "rank": rank.rank,
                "remarks": rank.remarks,
                "decision": rank.decision,
                "total": rank.total,
                "created_at": rank.created_at,
            })
        except Exception as ex:
            print("Error: ", ex)
        
    committee_list = []
    for member in committee:
        try:
            if member.user:
                committee_list.append({
                    "memberUserName": member.user.username if member.user else "",
                    "memberName": member.user.first_name + " " + member.user.last_name if member.user else "",
                    "memberPosition": member.committee_position,
                    "committeeStatus": member.committee_status,
                    "memberApproval": member.committee_approval if member.committee_approval else "",
                    "committeeJustification": member.justification,
                    "committeeDate": member.committee_date,
                }) 
        except Exception as ex:
            print("commitee_list Error: ", ex) 
    
    encoded_advert_file = ""
    try:
        if cs.advert:
            with open(cs.advert, 'rb') as f:
                file_data = f.read()
            encoded_advert_file = base64.b64encode(file_data).decode('utf-8')
    except Exception as ex:
        print("Error: ", ex)
        
    cs_owner = UserProfile.objects.filter(id=cs.created_by_id).first()  
    pr_attachments = Attachment.objects.filter(purchase_request=pr).all()
    
    pr_at_list = []
    for at in pr_attachments:
        encoded_file_data = ""
        if at.file:
            try:
                file_data = at.file.read()
                encoded_file_data = base64.b64encode(file_data).decode('utf-8')
                pr_at_list.append({
                    "id": at.id,
                    "file": encoded_file_data,
                    "name": os.path.basename(at.file.name),
                })
            except Exception as ex:
                print("Error: ", ex)
      
    cs_item_list = []
    for cs_item in cs_items:
        cs_item_list.append({
            "id": cs_item.id,
            "item_required": cs_item.item_name,
            "quantity": cs_item.quantity,
            "unit_of_measurement": cs_item.unit_of_measurement,
            "ordered": True,
        })
        
    # copy cs_item_list to pr_item_list
    pr_item_list = copy.deepcopy(cs_item_list) if cs_item_list else []
    for pr_item in pr_items:
        pr_item_list.append({
            "id": pr_item.id,
            "item_required": pr_item.item_required,
            "quantity": pr_item.quantity,
            "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
            "ordered": pr_item.ordered,
        })

    context = {
        "requester_role": user_comparative_schedule_role.role if user_comparative_schedule_role else "",
        "cs_id": cs.cs_id,
        "cs_owner": cs_owner.username if cs_owner else "",
        "creator": cs_owner.first_name + " " + cs_owner.last_name if cs_owner else "",
        "pr_id": pr.id,
        "pr_number": cs.pr_number,
        "pr_date": cs.pr_date,
        "additional_notes": cs.additional_notes,        
        "scope_of_work": cs.scope_of_work,
        "closing_date": cs.closing_date,
        "closing_time": cs.closing_time,
        "advert": encoded_advert_file,
        "pr_number": cs.pr_number,
        "pr_date": cs.pr_date,
        "ref_date": cs.ref_date,
        "cs_opened": cs.cs_opened,
        "tac_date": cs.tac_date,
        "show_site_visit": cs.show_site_visit,
        "show_samples_required": cs.show_sample_required,
        "created_by": user.username,
        "section": section.section if section else "",
        "region": region.region if region else "",
        "created_at": cs.created_at,
        "proc_plan": {
            "id": proc_plan.id,
            "proc_ref": proc_plan.proc_ref,
            "description": proc_plan.description,
            } if proc_plan else {},
        "proc_plans": list(proc_plans.values('id', 'proc_ref', 'description')),
        "currencies": list(currencies.values('id', 'currency')),
        "currency": {
            "id": cs.currency.id,
            "currency": cs.currency.currency,
            } if cs.currency else {},
        "gm_approval": {
            "id": gm_approval.id,
            "approver": gm_approval.user.username if gm_approval.user else "",
            "approver_name": gm_approval.user.first_name + " " + gm_approval.user.last_name if gm_approval.user else "",
            "approver_role": gm_approval.approver_role,
            "approval": gm_approval.approval,
            "justification": gm_approval.justification,
            "approval_date": gm_approval.approval_date,
            } if gm_approval else {},
        "fm_approval": {
            "id": fm_approval.id,
            "approver": fm_approval.user.username if fm_approval.user else "",
            "approver_name": fm_approval.user.first_name + " " + fm_approval.user.last_name if fm_approval.user else "",
            "approver_role": fm_approval.approver_role,
            "approval": fm_approval.approval,
            "justification": fm_approval.justification,
            "approval_date": fm_approval.approval_date,
            } if fm_approval else {},
        
        "pr_items": pr_item_list,
        "pr_attachments": pr_at_list,
        "cs_items": cs_item_list,
        "proc_plans": list(proc_plans.values('id', 'proc_ref', 'description')),
        "suppliers": list(suppliers.values('id', 'name')),
        "users": list(users.values('id', 'username', 'first_name', 'last_name')),
        "items": items_list,
        "bids": result,
        "compliance": compliance_list,
        "complianceRemarks": compliance_remarks,
        "rankings": rankings_list,
        "committee": committee_list,
        "proc_ref": cs.proc_plan.proc_ref if cs.proc_plan else "",
    }
    
    context = json.dumps(context, default=str)
    
    return JsonResponse(context, safe=False)

def save_file(f, file_path):
    if f:
        with open(file_path, 'wb+') as destination:
            for chunk in f.chunks():
                destination.write(chunk)
            return True
    else:
        return False

@login_required    
def get_create_data(request, pr_id):

    # check is pr_id started with PR or not
    if not pr_id.startswith("PR"):
        pr_id = "PR" + pr_id
    purchase_request = PurchaseRequest.objects.filter(id=pr_id).first()
    if purchase_request:
        request_user = request.user
        request_user_profile = UserProfile.objects.filter(id=request_user.id).first()
        user_comparative_schedule_role = request_user_profile.get_user_role_for_application(APP_NAME) 
        proc_plans = ProcPlan.objects.all()
        currencies = Currency.objects.all()
        suppliers = Supplier.objects.all()
        users = UserProfile.objects.all()
        uom = UnitOfMeasurement.objects.all()
        pr_items = PrItem.objects.filter(purchase_request=purchase_request, ordered=False).all()
        pr_attachments = Attachment.objects.filter(purchase_request=purchase_request).all()
        
        pr_at_list = []
        for at in pr_attachments:
            encoded_file_data = ""
            if at.file:
                try:
                    file_data = at.file.read()
                    encoded_file_data = base64.b64encode(file_data).decode('utf-8')
                    pr_at_list.append({
                        "id": at.id,
                        "file": encoded_file_data,
                        "name": os.path.basename(at.file.name),
                    })
                except Exception as ex:
                    print("Error: ", ex)

        pr_item_list = []
        for pr_item in pr_items:
            pr_item_list.append({
                "id": pr_item.id,
                "item_required": pr_item.item_required,
                "quantity": pr_item.quantity,
                "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
                "ordered": pr_item.ordered,
            })
        
        return JsonResponse({
                "success": True,
                "requester_role": user_comparative_schedule_role.role if user_comparative_schedule_role else "",
                "message": "PR details retrieved successfully",
                "pr_id": pr_id,
                "scope_of_work": purchase_request.scope_of_work if purchase_request.scope_of_work else "",
                "proc_ref": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
                "proc_plan": {
                    "id": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
                    "proc_ref": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
                    "description": purchase_request.procurement_plan_reference.name if purchase_request.procurement_plan_reference else "",
                } if purchase_request.procurement_plan_reference else {},
                "pr_date": purchase_request.created_at.strftime("%Y-%m-%d") if purchase_request.created_at else "",
                "pr_items": pr_item_list,
                "pr_attachments": pr_at_list,
                "proc_plans": list(proc_plans.values('id', 'proc_ref', 'description')),
                "uom": list(uom.values('unit', 'name')),
                "currencies": list(currencies.values('id', 'currency')),
                "suppliers": list(suppliers.values('id', 'name')),
                "users": list(users.values('id', 'username', 'first_name', 'last_name')),
            }, safe=False)
    else:
        return JsonResponse({
            "success": False,
            "message": "PR not found",
        }, safe=False)

@login_required
def get_create_cs(request, pr_id):

    print("get_create_cs pr_id: ", pr_id)
    # get proc plans
    proc_plans = ProcPlan.objects.all()
    username = request.user.username
    
    return render(request, 'finance/comparative_schedules/cs_create.html', {
        "proc_plans": proc_plans,
        "username": username,
        "pr_id": pr_id,
    })

@login_required
def create(request):

    if request.method == "POST":
        tender_id = "CS" + timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S")
        advert_file = request.FILES['advert']
        bid_document_file = request.FILES['advert']
        item_count = request.POST['item_count']
        rfq_no = request.POST['rfq_id']
        rfq = request.POST['rfq']
        scope = request.POST['scope_of_work']
        quantity = request.POST['quantity']
        rfq_date = request.POST['rfq_date']
        closing_date = request.POST['closing_date']
        closing_time = request.POST['closing_time_hour']
        pr_number = request.POST['pr_number']
        pr_date = request.POST['pr_date']
        date_tender_opened = request.POST['date_tender_opened']
        tender_adjudication_committee_date = request.POST['tender_adjudication_committee_date']
        supplier_name = request.POST['supplier_name']
        supplier_key = request.POST['supplier_key']
        bid_date = request.POST['bid_date']
        bid_no = request.POST['supplier[bid][0]']
        
        # store attachments
        advert_path = ""
        bid_document_path = ""
        try:
            if 'advert' in request.FILES:
                advert_file = request.FILES['advert']
                advert_path = 'uploads/finance/cs/adverts/' + \
                                  timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S%p") + advert_file.name
                save_file(advert_file, advert_path)
                
            if 'bid_document' in request.FILES:
                bid_document_file = request.FILES['bid_document']
                bid_document_path = 'uploads/finance/cs/bids/' + \
                                  datetime.now().strftime("%Y%m%d%I%M%S%p") + bid_document_file.name
                save_file(bid_document_file, bid_document_path)
        
        except Exception as ex:
            print("Error: ", ex)
        
        for i in range(0,int(item_count)):
            item_id = "Item" + datetime.now().strftime("%Y%m%d%I%M%S%p")
            description = request.POST['supplier[item_name]['+str(i)+']']
            quantity = request.POST['supplier[quantity]['+str(i)+']']
            unit_of_measurement = request.POST['supplier[unit_of_measurement]['+str(i)+']']
            vat = request.POST['supplier[vat]['+str(i)+']']
            unit_price = request.POST['supplier[unit_price]['+str(i)+']']
            total_price = request.POST['supplier[total_price]['+str(i)+']']
            
            item = CSItems(
                cd_id = tender_id,
                item_id = item_id,
                item = description,
                required_qty = quantity,
                unit_of_measurement = unit_of_measurement,
            )
            item.save()
            
            supplier_id = ""
            if supplier_key:
                supplier_id = supplier_key
            else:
                supplier_id = "SUP" + datetime.now().strftime("%Y%m%d%I%M%S")
            supplier_query = Supplier(
                sup_id = supplier_id,
                supplier = supplier_name
            )
            supplier_query.save()
            
            bid = Bids(
                document_id = tender_id,
                item_id = item_id,
                sup_id = supplier_id,
                unit_price = unit_price,
                vat = vat,
                quoted_qty = quantity,
                bid_no = bid_no,
                quote_date = bid_date,
                rfq_no = rfq_no,
                total = total_price,
                bid_document = bid_document_path,
            )
            bid.save()
        
        cs_query = ComparativeSchedules(
            document_id = tender_id,
            rfq_date = rfq_date,
            scope_of_work = scope,
            closing_date = closing_date,
            closing_time = closing_time,
            rfq_no = rfq,
            advert = advert_path,
            date_created = date_tender_opened,
            pr_number = pr_number,
            pr_date = pr_date,
            tender_opened = date_tender_opened,
            tac_date = tender_adjudication_committee_date,
            region = "",
        )
        cs_query.save()
        
        # rfq_query = RFQUPDATE.objects.filter(document_id=rfq).first()
        # if rfq_query:
        #     rfq_query.tender_board = 'yes'
        #     rfq_query.save()
        
        if 'add_supplier' in request.POST:
            return redirect('add_supplier', tender_id=tender_id)
            
        return render(request, 'finance/comparative_schedules/cs_create.html', {
            "proc_plans": None,
        })

@login_required        
def save_comparative_schedule(request):

    try:
        
        cs_id = "CS" + datetime.now().strftime("%Y%m%d%I%M%S")
        cs_exists = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
        # @TODO try random number if cs_id exists or return error
        if cs_exists:
            cs_id = "CS" + datetime.now().strftime("%Y%m%d%I%M%S")
            
        advert_files = request.FILES.getlist("advert", None)
        proc_ref = request.POST.get("proc_ref", "")
        print("proc plan: ", proc_ref)
        # check if proc ref has 'acc' prefix
        if not proc_ref.startswith("acc"):
            temp_proc_ref = "acc" + proc_ref
            proc_ref = temp_proc_ref
            
        proc_plan = ProcPlan.objects.filter(proc_ref=proc_ref).first()
        print("proc_plan: ", proc_plan)
        scope_of_work = request.POST.get("scope_of_work", "")
        pr_number = request.POST.get("pr_number", "")
        pr_date = request.POST.get("pr_date", "")
        ref_date = request.POST.get("ref_date", "")
        currency = request.POST.get("currency", "")
        print("currency: ", currency)
        # quantity = data['quantity']
        closing_date = request.POST.get("closing_date", "")
        closing_time = request.POST.get("closing_time", "")
        date_tender_opened = request.POST.get("date_tender_opened", "")
        tender_adjudication_committee_date = request.POST.get("tender_adjudication_committee_date", "")
        username = request.POST.get("username", "")
        
        # save advert file
        advert_path = ""
        try:
            if advert_files:
                advert_file = advert_files[0]
                root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts')
                fs = FileSystemStorage(location=root_dir)
                filename_ = fs.save(advert_file.name, advert_file)
                advert_path = "uploads" + os.path.sep + "comparative" + os.path.sep + "adverts" + os.path.sep + filename_
        except Exception as ex:
            print("Error: ", ex)
        
        # save cs details
        # fetch purchase request
        print("pr number: ", pr_number)
        pr = PurchaseRequest.objects.get(id=pr_number)
        print("PR: ", pr, pr_number, username)
        # fetch user
        user = UserProfile.objects.filter(username=username).first()
        currency = Currency.objects.filter(id=currency).first() if currency else None
        # region_ = Regions.objects.filter(region=pr.region).first() if 'region' in pr else None
        # section = Sections.objects.filter(section=pr.section).first() if 'section' in pr else None
        cs_query = ComparativeSchedules(
            cs_id = cs_id,
            pr_id_id = pr.id,
            scope_of_work = scope_of_work,
            currency = currency,
            closing_date = closing_date,
            closing_time = closing_time,
            advert = advert_path,
            pr_number = pr_number,
            pr_date = pr_date,
            ref_date = ref_date,
            proc_plan = proc_plan,
            cs_opened = date_tender_opened,
            tac_date = tender_adjudication_committee_date,
            created_by_id = user.id,
            cost_center = user.cost_center if user.cost_center else None,
            region_id = user.region_id if user.region_id else None,
        )
        cs_query.save()
        
        return JsonResponse({
            "message": "Comparative Schedule saved successfully",
            "success": True,
            "cs_id": cs_id,
            "cs_owner": user.username if user else "",
            }, safe=False)
    except Exception as ex:
        print("Error: ", ex)
        return JsonResponse({
            "message": "Error saving Comparative Schedule",
            "error": str(ex),
            "success": False,
            }, safe=False)

@login_required   
def update_comparative_schedule(request):

    try:
        
        advert_files = request.FILES.getlist("advert", None)
        print("advert_files: ", advert_files)
        cs_id = request.POST.get("cs_id", "")
        plan_ref = request.POST.get("proc_ref", "")
        # proc_plan = data['proc_plan']
        proc_plan_ = ProcPlan.objects.filter(proc_ref=plan_ref).first()
        scope_of_work = request.POST.get("scope_of_work", "")
        currency = request.POST.get("currency", "")
        pr_number = request.POST.get("pr_number", "")
        pr_date = request.POST.get("pr_date", "")
        ref_date = request.POST.get("ref_date", "")
        # quantity = data['quantity']
        closing_date = request.POST.get("closing_date", "")
        closing_time = request.POST.get("closing_time", "")
        date_tender_opened = request.POST.get("date_tender_opened", "")
        tender_adjudication_committee_date = request.POST.get("tender_adjudication_committee_date", "")
        username = request.POST.get("username", "")
        
        # save advert file
        advert_path = ""
        try:
            if advert_files:
                advert_file = advert_files[0]
                print("advert_file: ", advert_file.name)
                root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts')
                fs = FileSystemStorage(location=root_dir)
                filename_ = fs.save(advert_file.name, advert_file)
                advert_path = "uploads" + os.path.sep + "comparative" + os.path.sep + "adverts" + os.path.sep + filename_
        except Exception as ex:
            print("Error: ", ex)
        
        # fetch user
        print("pr number: ", pr_number)
        print("currency: ", currency)
        currency = Currency.objects.filter(id=currency).first() if currency else None
        # region_ = Regions.objects.filter(region=pr.region).first() if 'region' in pr else None
        # section = Sections.objects.filter(section=pr.section).first() if 'section' in pr else None
        cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()

        if cs_query:
            clear_approvals(cs_id)
            if currency:
                cs_query.currency = currency
            if scope_of_work:
                cs_query.scope_of_work = scope_of_work 
            if closing_date:
                cs_query.closing_date = closing_date
            if closing_time:
                cs_query.closing_time = closing_time
            if advert_path:
                cs_query.advert = advert_path
            if pr_number:
                cs_query.pr_number = pr_number
            if pr_date:
                cs_query.pr_date = pr_date
            if date_tender_opened:
                cs_query.cs_opened = date_tender_opened
            if tender_adjudication_committee_date:
                cs_query.tac_date = tender_adjudication_committee_date
            if proc_plan_:
                cs_query.proc_plan = proc_plan_
            if ref_date:
                cs_query.ref_date = ref_date
            
            cs_query.save()
        else:
            print("ComparativeSchedule record not found with cs_id:", cs_id)
        
        return JsonResponse({
            "message": "Comparative Schedule saved successfully",
            "success": True,
            "cs_id": cs_id,
            }, safe=False)
    except Exception as ex:
        print("Error: ", ex)
        return JsonResponse({
            "message": "Error saving Comparative Schedule",
            "error": str(ex),
            "success": False,
            }, safe=False)

@login_required
def update_pritem_ordered(request):
    
    cs_id = request.POST.get("cs_id", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    
    if cs_query:
        pr_item_id = request.POST.get("pr_id", "")
        csitems_data = json.loads(request.POST.get("json_data", "{}"))
        print("csitems_data: ", csitems_data)
        items = csitems_data.get("cs_items", [])
        print("items ", items, type(items))
        print("pr_item_id: ", pr_item_id)
        purchase_request = PurchaseRequest.objects.filter(id=pr_item_id).first()
        print("purchase request: ", purchase_request)
        existing_items = CSRequiredItems.objects.filter(cs_id=cs_query).all()
        
        # Convert existing items to a list of dictionaries for easier comparison
        existing_items_list = [
            {
                "id": item.id,
                "item_name": item.item_name,
                "quantity": item.quantity,
                "unit_of_measurement": item.unit_of_measurement,
                # Include other fields as necessary
            }
            for item in existing_items
        ]
        print("existing_items_list: ", existing_items_list)

        # Step 2: Identify items to add
        # Convert provided list to a set of IDs for faster lookup
        provided_ids = {item['item_required'] for item in items}
        print("provided_ids: ", provided_ids)

        # Find IDs in the provided list that are not in the existing items
        ids_to_add = provided_ids - {item['item_name'] for item in existing_items_list}
        print("ids_to_add: ", ids_to_add)

        # Filter the provided list to get the items to add
        items_to_add = [item for item in items if item['item_required'] in ids_to_add]
        print("items_to_add: ", items_to_add)

        # Step 3: Identify items to delete
        # Find IDs in the existing items that are not in the provided list
        ids_to_delete = {item['item_name'] for item in existing_items_list} - provided_ids
        print("ids_to_delete: ", ids_to_delete)

        # Step 4: Update the database
        # Add new items
        for item in items_to_add:
            print("item: ", item)
            pr_item = PrItem.objects.filter(item_required=item['item_required'], purchase_request=purchase_request).first()
            if pr_item:
                pr_item.ordered = True
                pr_item.save()
                print("item: ", item)
                cs_required_items = CSRequiredItems(
                    cs_id = cs_query,
                    item_id = item['id'],
                    item_name = item['item_required'],
                    quantity = item['quantity'],
                    unit_of_measurement = item['unit_of_measurement'],
                )
                cs_required_items.save()
                print("added ...")

        # Delete items that no longer exist
        for item in ids_to_delete:
            print("item: ", item)
            pr_item = PrItem.objects.filter(item_required=item, purchase_request=purchase_request).first()
            if pr_item:
                pr_item.ordered = False
                pr_item.save()
                CSRequiredItems.objects.filter(item_name=item, cs_id=cs_query).delete()        

        return JsonResponse({
            "message": "PR Item updated successfully",
            "success": True,
            }, safe=False)
    else:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)

@login_required    
def save_cs_bid(request):

    cs_id = request.POST.get("cs_id", "")
    bid_no = request.POST.get("bid_count", "")
    print("bid_no: ", bid_no)
    
    bid_docs = request.FILES.get("bid_document", None)
    bid_date = request.POST.get("bid_date", "")
    supplier_name = request.POST.get("supplier_name", "")
    # get items json
    json_data = json.loads(request.POST.get("json_data", "{}"))
    items = json_data.get("items", [])
    
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
      
    supplier = Supplier.objects.filter(name=supplier_name).first()
    if not supplier:
        supplier_ = Supplier(
            name = supplier_name
        )
        supplier_.save()
        supplier = supplier_  
        
    # check if bid exists
    bid_query = Bids.objects.filter(cs_id=cs_query, sup_id=supplier, bid_no=bid_no).all()
    if bid_query:
        clear_approvals(cs_id)
        for bid in bid_query:
            # delete item
            item = CSItems.objects.filter(item_id=bid.item_id).first()
            if item:
                item.delete()
            bid.delete()
            
    # save bids
    bid_doc_path = ""
    try:
        if bid_docs:
            bid_doc = bid_docs
            root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts')
            fs = FileSystemStorage(location=root_dir)
            filename_ = fs.save(bid_doc.name, bid_doc)
            bid_doc_path = "uploads" + os.path.sep + "comparative" + os.path.sep + "adverts" + os.path.sep + filename_
    except Exception as ex:
        print("Error: ", ex)
        
    for item in items:
        item_id = "Item" + datetime.now().strftime("%Y%m%d%I%M%S%p")
        item_query = CSItems(
            cs_id = cs_query,
            item_id = item_id,
            item_name = item['item_required'],
            quantity = item['quantity'],
            unit_of_measurement = item['unit_of_measurement'],
        )
        item_query.save()    
        
        bid = Bids(
            cs_id = cs_query,
            item_id = item_query,
            sup_id = supplier,
            unit_price = item['unit_price'] if 'unit_price' in item else "",
            vat = item['vat'] if 'vat' in item else "",
            quoted_qty = item['quantity'] if 'quantity' in item else "",
            bid_no = bid_no,
            quote_date = bid_date,
            total = item['total_price'] if 'total_price' in item else "",
            bid_document = bid_doc_path,
        )
        bid.save()
        
    return JsonResponse({
        "message": "Bids saved successfully",
        "success": True,
    })

@login_required
def delete_cs_bid(request):
    
    cs_id = request.POST.get("cs_id", "")
    supplier_name = request.POST.get("supplier_name", "")
    bid_no = request.POST.get("bid_count", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    supplier = Supplier.objects.filter(name=supplier_name).first()
    if not supplier:
        return JsonResponse({
            "message": "Supplier not found",
            "success": False,
            }, safe=False)
    
    # check if bid exists
    bid_query = Bids.objects.filter(cs_id=cs_query, sup_id=supplier).all()
    if bid_query:
        clear_approvals(cs_id)
        for bid in bid_query:
            # delete item
            item = bid.item_id if bid.item_id else None
            print("items: ", item) 
            if item:
                item.delete()
                
            compliance = CSCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier)
            if compliance:
                compliance.delete()
                
            complianceRemark = CSComplianceRemarks.objects.filter(cs_id=cs_query, supplier_id=supplier)
            if complianceRemark:
                complianceRemark.delete()
            
            bid.delete()

    return JsonResponse({
        "message": "Bid deleted successfully",
        "success": True,
    })

@login_required
def save_cs_compliance(request):

    cs_id = request.POST.get("cs_id", "")
    show_site_visit = request.POST.get("show_site_visit", "")
    show_sample_required = request.POST.get("show_samples_required", "")
    json_data = json.loads(request.POST.get("compliance", "{}"))

    compliances = json_data.get("compliance", [])

    json_data_ = json.loads(request.POST.get("complianceRemarks", "{}"))

    compliance_remarks = json_data_.get("complianceRemarks", [])
    
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    cs_query.show_site_visit = True if show_site_visit == "yes" else False
    cs_query.show_sample_required = True if show_sample_required == "yes" else False
    cs_query.save()
    # check if compliance exists
    compliance_query = CSCompliance.objects.filter(cs_id=cs_query).all()
    if compliance_query:
        clear_approvals(cs_id)
        for compliance in compliance_query:
            compliance.delete()
    
    for comp in compliances:
        print("comp: ", comp)
        supplier_name = comp['supplier_name'] if 'supplier_name' in comp else False
        payment_terms = comp['payment_terms'] if 'payment_terms' in comp else False
        bid_validity = comp['bid_validity'] if 'bid_validity' in comp else False
        delivery_period = comp['delivery_period'] if 'delivery_period' in comp else False
        technical_specifications = comp['technical_specifications'] if 'technical_specifications' in comp else False
        valid_tax_clearance = comp['valid_tax_clearance'] if 'valid_tax_clearance' in comp else False
        registered_with_praz = comp['registered_with_praz'] if 'registered_with_praz' in comp else False
        site_visit_done = comp['site_visit'] if 'site_visit' in comp else False
        samples_delivered = comp['samples_required'] if 'samples_required' in comp else False
        decision = comp['decision'] if 'decision' in comp else False
        remarks = comp['remarks'] if 'remarks' in comp else False
        
        supplier = Supplier.objects.filter(name=supplier_name).first()
        compliance_query = CSCompliance(
            cs_id = cs_query,
            supplier_id = supplier,
            payment_terms = payment_terms,
            bid_validity = bid_validity,
            delivery_period = delivery_period,
            technical_specifications = technical_specifications,
            valid_tax_clearance = valid_tax_clearance,
            registered_with_praz = registered_with_praz,
            site_visit_done = site_visit_done,
            samples_delivered = samples_delivered,
            decision = decision,
            remarks = remarks,
        )
        compliance_query.save()
    
    # check if compliance remarks exists
    compliance_remarks_query = CSComplianceRemarks.objects.filter(cs_id=cs_query).all()
    if compliance_remarks_query:
        for remark in compliance_remarks_query:
            remark.delete()
            
    for remark in compliance_remarks:
        supplier_name = remark['supplier_name'] if 'supplier_name' in remark else ""
        print("supplier_name: ", supplier_name, cs_query)
        supplier = Supplier.objects.filter(name=supplier_name).first()
        print("supplier: ", supplier)
        _remark = CSComplianceRemarks(
            cs_id = cs_query,
            supplier_id = supplier,
            remarks = remark['remarks'] if 'remarks' in remark else "",
        )  
        _remark.save()
        
    return JsonResponse({
        "message": "Compliance saved successfully",
        "success": True,
    })

@login_required    
def save_supplier(request):

    supplier_name = request.POST.get("supplier_name", "")
    
    supplier_query = Supplier.objects.filter(name=supplier_name).first()
    if not supplier_query:
        supplier_query = Supplier(
            name = supplier_name
        )
        supplier_query.save()
    
    suppliers = Supplier.objects.all()
    return JsonResponse({
        "message": "Supplier saved successfully",
        "suppliers": list(suppliers.values('id', 'name')),
        "success": True,
    })

@login_required     
def save_cs_ranking(request):
    cs_id = request.POST.get("cs_id", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    print("cs_query: ", cs_query)
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    # check if rankings exists
    ranking_query = Ranking.objects.filter(cs_id=cs_query).all()
    if ranking_query:
        clear_approvals(cs_id)
        for ranking in ranking_query:
            ranking.delete()
    # get bids
    bids = Bids.objects.filter(cs_id=cs_query).values('sup_id').annotate(total_sum=Sum('total'))
    compliant_bids = []
    for bid in bids:
        supplier = Supplier.objects.filter(id=bid['sup_id']).first()
        _compliance = CSCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier, decision=True).first()
        if _compliance:
            compliant_bids.append(bid)
    rankings = {bid['sup_id']: bid['total_sum'] for bid in compliant_bids}
    print("rankings: ", rankings)
    sorted_rankings = sorted(rankings.items(), key=lambda x: x[1])
    print("sorted_rankings: ", sorted_rankings)
    rank = 1
    sorted_rankings_dict = dict(sorted_rankings)
    for supplier_id, total in sorted_rankings_dict.items():
        supplier = Supplier.objects.filter(id=supplier_id).first()
        remarks = ""
        decision = ""
        if rank == 1:
            decision = "Awarded " + supplier.name + cs_query.currency.currency + " " + str(total)
        ranking_query = Ranking(
            cs_id = cs_query,
            supplier_id = supplier,
            rank = rank,
            remarks = remarks,
            decision = decision,
            total = total,
        )
        ranking_query.save()
        rank += 1
        
    # get rankings
    rankings = Ranking.objects.filter(cs_id=cs_query).all()
    custom_rankings = []
    for ranking in rankings:
        supplier = ranking.supplier_id
        custom_rankings.append({
            "id": ranking.id,
            "supplier_name": supplier.name,
            "rank": ranking.rank,
            "remarks": ranking.remarks,
            "decision": ranking.decision,
            "total": ranking.total,
        })
    
    custom_rankings = sorted(custom_rankings, key=lambda x: x['rank'])
    return JsonResponse({
        "message": "Ranking saved successfully",
        "success": True,
        "rankings": list(custom_rankings),
    })

@login_required    
def save_cs_committee(request):
    cs_id = request.POST.get("cs_id", "")
    json_data = json.loads(request.POST.get("committee", "{}"))
    committee = json_data.get("committee", [])
    try:
        cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
        if not cs_query:
            return JsonResponse({
                "message": "Comparative Schedule not found",
                "success": False,
                }, safe=False)
        
        # check if committee exists
        for member in committee:
            # check if member exists
            # get member user profile
            member_profile = UserProfile.objects.filter(username=member['memberUserName']).first()
            if member_profile:
                committee_query = Committee.objects.filter(cs_id=cs_query, user=member_profile).first()
                if not committee_query:
                    clear_approvals(cs_id)
                    committee_query = Committee(
                        cs_id = cs_query,
                        user = member_profile,
                        committee_name = member['memberUserName'],
                        committee_position = member['memberPosition']
                    )
                    msg = "You have been added to the committee for RFQ " + cs_query.cs_id
                    url = "/comperative_schedule/comperative_schedule/" + cs_query.cs_id
                    notify_user(member_profile, msg, "RFQ", url, cs_query.cs_id)
                    committee_query.save()
                
            
        return JsonResponse({
            "message": "Committee saved successfully",
            "success": True,
        })
    except Exception as ex:
        print("Error: ", ex)
        return JsonResponse({
            "message": "Error saving Committee",
            "error": str(ex),
            "success": False,
            }, safe=False)

@login_required
def delete_cs_committee_member(request):
    cs_id = request.POST.get("cs_id", "")
    username = request.POST.get("username", "")
    print("username: ", username)
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    member_profile = UserProfile.objects.filter(username=username).first()
    if member_profile:
        committee_query = Committee.objects.filter(cs_id=cs_query, user=member_profile).first()
        print("committee_query: ", committee_query)
        if committee_query:
            clear_approvals(cs_id)
            committee_query.delete()
            return JsonResponse({
                "message": "Committee member deleted successfully",
                "success": True,
            })
        else:
            return JsonResponse({
                "message": "Committee member not found",
                "success": False,
            })
    else:
        return JsonResponse({
            "message": "Committee member not found",
            "success": False,
        })

@login_required
def approve_cs_committee(request):
    cs_id = request.POST.get("cs_id", "")
    username = request.POST.get("username", "")
    approval = request.POST.get("approval", "")
    justification = request.POST.get("justification", "")

    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    member_profile = UserProfile.objects.filter(username=username).first()
    if member_profile:
        committee_query = Committee.objects.filter(cs_id=cs_query, user=member_profile).first()

        if committee_query:
            committee_query.committee_approval = approval
            committee_query.justification = justification
            committee_query.committee_date = timezone.now()
            committee_query.save()
            notification_update(member_profile, cs_query.cs_id)
        
        committees = Committee.objects.filter(cs_id=cs_query).all()
        committee_approved = all([c.committee_approval == "Approved" for c in committees])
        if committee_approved:
            fm_role = Roles.objects.filter(name="Finance Manager", application=APP_NAME).first()
            print("fm role: ", fm_role)
            fm_users = UserProfile.objects.filter(roles=fm_role, region=cs_query.region).all()
            print("fm user: ", fm_users)
            msg = "Comperative Schedule is ready for your approval " + cs_query.cs_id
            url = "/comperative_schedule/comperative_schedule/" + cs_query.cs_id
            for user_ in fm_users:  
                notify_user(user_, msg, "RFQ", url, cs_query.cs_id)

        return JsonResponse({
            "message": "Committee member approved successfully",
            "success": True,
            "data": {
                "committee_date": committee_query.committee_date,
                "committee_status": committee_query.committee_status,
                "committee_fullname": member_profile.first_name + " " + member_profile.last_name,
                "committee_approval": approval,
            }
        })
    else:
        return JsonResponse({
            "message": "Committee member not found",
            "success": False,
        })

@login_required
def approve_cs(request):
    cs_id = request.POST.get("cs_id", "")
    username = request.POST.get("username", "")
    approval = request.POST.get("approval", "")
    justification = request.POST.get("justification", "")
    role = request.POST.get("role", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    committees = Committee.objects.filter(cs_id=cs_query).all()
    user = UserProfile.objects.filter(username=username).first()
    if user:
        if role == "general_manager":
            gm_approval = CSApproval(
                cs_id = cs_query,
                user = user,
                approver_role = role,
                approval = approval,
                justification = justification,
                approval_date = timezone.now(),
                created_at = timezone.now(),
            )
            gm_approval.save()
            gm_role = Roles.objects.filter(name="General Manager", application=APP_NAME).first()
            gm_users = UserProfile.objects.filter(roles=gm_role, region=cs_query.region).all()
            for user_ in gm_users:
                notification_update(user_, cs_query.cs_id)
            
            return JsonResponse({
                "message": "GM approval saved successfully",
                "success": True, 
                "role": role,
                "approval": approval,           
                "gm_approval": {
                    "id": gm_approval.id,
                    "approver": gm_approval.user.username if gm_approval.user else "",
                    "approver_name": gm_approval.user.first_name + " " + gm_approval.user.last_name if gm_approval.user else "",
                    "approver_role": gm_approval.approver_role,
                    "approval": gm_approval.approval,
                    "justification": gm_approval.justification,
                    "approval_date": gm_approval.approval_date,
                }
            })
        elif role == "finance_manager":
            fm_approval = CSApproval(
                cs_id = cs_query,
                user = user,
                approver_role = role,
                approval = approval,
                justification = justification,
                approval_date = timezone.now(),
                created_at = timezone.now(),
            )
            fm_approval.save()
            gm_role = Roles.objects.filter(name="Finance Manager", application=APP_NAME).first()
            gm_users = UserProfile.objects.filter(roles=gm_role, region=cs_query.region).all()
            for user_ in gm_users:
                notification_update(user_, cs_query.cs_id)
                
            committee_approved = all([c.committee_approval == "Approved" for c in committees])
            if committee_approved and approval == "Approved":
                gm_role = Roles.objects.filter(name="Finance Manager", application=APP_NAME).first()
                print("gm role: ", gm_role)
                gm_users = UserProfile.objects.filter(roles=gm_role, region=cs_query.region).all()
                for user_ in gm_users:
                    notify_user(user_, "Comperative Schedule is ready for your approval " + cs_query.cs_id, "RFQ", "/comperative_schedule/comperative_schedule/" + cs_query.cs_id, cs_query.cs_id)
        
            return JsonResponse({
                "message": "FM approval saved successfully",
                "success": True, 
                "role": role,
                "approval": approval,          
                "fm_approval": {
                    "id": fm_approval.id,
                    "approver": fm_approval.user.username if fm_approval.user else "",
                    "approver_name": fm_approval.user.first_name + " " + fm_approval.user.last_name if fm_approval.user else "",
                    "approver_role": fm_approval.approver_role,
                    "approval": fm_approval.approval,
                    "justification": fm_approval.justification,
                    "approval_date": fm_approval.approval_date,
                }
            })
        else:
            return JsonResponse({
                "message": "User Role not found",
                "success": False,
            })
    else:
        return JsonResponse({
            "message": "User not found",
            "success": False,
        })

@login_required
def save_cs_decision(request):
    cs_id = request.POST.get("cs_id", "")
    committee_id = request.POST.get("committee_id", "")
    committee_decision = request.POST.get("committee_decision", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    committee_query = Committee.objects.filter(cs_id=cs_query, id=committee_id).first()
    if committee_query:
        if committee_decision == "approve":
            committee_query.committee_status = True
            committee_query.committee_date = timezone.now()
            committee_query.save()
        elif committee_decision == "reject":
            committee_query.committee_status = False
            committee_query.committee_date = timezone.now()
            committee_query.save() 
            
    return JsonResponse({
        "message": "Committee decision saved successfully",
        "success": True,
    })   

@login_required
def save_additional_notes(request):
    cs_id = request.POST.get("cs_id", "")
    additional_notes = request.POST.get("additional_notes", "")
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if cs_query:
        cs_query.additional_notes = additional_notes
        cs_query.save()
        return JsonResponse({
            "message": "Additional notes saved successfully",
            "success": True,
        })
    else:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        })

@login_required
def save_buyers_notes(request):
    cs_id = request.POST.get("cs_id", "")
    buyers_notes = request.POST.get("buyers_notes", "")
    print("buyers_notes: ", buyers_notes)
    cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
    if cs_query:
        ranking = Ranking.objects.filter(cs_id=cs_query, rank=1).first()
        ranking.remarks = buyers_notes if buyers_notes else ""
        ranking.save()
        print("ranking: ", ranking)
        return JsonResponse({
            "message": "Buyers notes saved successfully",
            "success": True,
        })
    else:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
        })

@login_required
def cancel_schedule(request, cs_id):
    print("cs_id: ", cs_id)
    try:
        cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
        if cs_query:
            cs_query.cancelled = True
            cs_query.scope_of_work = "Cancelled Schedule: " + cs_query.scope_of_work
            cs_query.save()
            print("cs_query: ", cs_query, cs_query.cancelled, "scope: ", cs_query.scope_of_work, cs_query.pr_number)
            required_items = CSRequiredItems.objects.filter(cs_id=cs_query).all()
            pr_query = PurchaseRequest.objects.filter(id=cs_query.pr_number).first()
            for item in required_items:
                pr_item = PrItem.objects.filter(id=item.item_id, purchase_request=pr_query).first()
                pr_item.ordered = False
                pr_item.save()
                item.delete()

    except Exception as ex:
        print("Error: ", ex)
        messages.error(request, "Error cancelling Comparative Schedule", str(ex))
    
    messages.success(request, "Comparative Schedule cancelled successfully")
    return redirect('/comperative_schedule/comperative_schedules')

@login_required        
def cs_add_supplier(request, cs_id):
    
    if request.method == 'GET':
        
        # tender_id = request.GET['tender_id']
        # get tender bids supplier items
        tender = ComparativeSchedules.objects.filter(document_id=tender_id).first()
        proc_plan = ProcPlan.objects.filter(proc_ref=tender.pr_number).first()
        bids = Bids.objects.filter(document_id=tender_id).order_by('bid_no').all()

        bids_dict = {}
        for bid in bids:
            bids_dict.update({bid.bid_no: []})
            
        for i in range(0, len(bids_dict)):
            i = i + 1
            for bid in bids:
                if int(bid.bid_no) == i:
                    supplier = Supplier.objects.filter(sup_id=bid.sup_id).first()
                    item = CSItems.objects.filter(item_id=bid.item_id).first()

                    if supplier:
                        print(supplier, supplier.supplier, supplier.sup_id)
                        supplier_id = supplier.sup_id
                        supplier_name = supplier.supplier
                        bids_dict[str(i)].append({
                            "bid_no": int(bid.bid_no),
                            "supplier_name": supplier_name,
                            "supplier_id": supplier_id,
                            "bid": bid,
                            "item": item,
                        })
                
        # get proc plans
        proc_plans = ProcPlan.objects.all()
        suppliers = Suppliers.objects.all()
        supplier_list = {}
        for supplier in suppliers:
            supplier_list.update({supplier.sup_id:supplier.supplier})
            
        suppliers_json = json.dumps(supplier_list, default=str)
        
        return render(request, 'finance/tenders/tenders_add_supplier.html', {
            "proc_plans": proc_plans,
            "suppliers": suppliers_json,
            "tender": tender,
            "bids_items": bids_dict,
            "next_bid": len(bids_dict)+1,
            "proc_plan": proc_plan
        })
    elif request.method == "POST":
        print("request: ", request.POST)
        print(i)
        tender_id = request.POST['tender_id']
        item_count = request.POST['item_count']
        rfq_no = request.POST['rfq_id']
        supplier_name = request.POST['supplier_name']
        supplier_id = request.POST['supplier_key']
        supplier_key = request.POST['supplier_key']
        bid_date = request.POST['bid_date']
        bid_no = request.POST['supplier[bid][0]']
        # store attachments
        bid_document_path = ""
        try:
                
            if 'bid_document' in request.FILES:
                bid_document_file = request.FILES['bid_document']
                bid_document_path = 'uploads/finance/cs/bids/' + \
                                  timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S") + bid_document_file.name
                save_file(bid_document_file, bid_document_path)
        
        except Exception as ex:
            print("Error: ", ex)
        
        for i in range(0,int(item_count)):
            item_id = "Item" + timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S%p")
            description = request.POST['supplier[item_name]['+str(i)+']']
            quantity = request.POST['supplier[quantity]['+str(i)+']']
            unit_of_measurement = request.POST['supplier[unit_of_measurement]['+str(i)+']']
            vat = request.POST['supplier[vat]['+str(i)+']']
            unit_price = request.POST['supplier[unit_price]['+str(i)+']']
            total_price = request.POST['supplier[total_price]['+str(i)+']']
            
            item = CSItems(
                document_id = tender_id,
                item_id = item_id,
                item = description,
                required_qty = quantity,
                unit_of_measurement = unit_of_measurement,
                rfq_no = rfq_no,
            )
            item.save()
            
            supplier_id = ""
            if supplier_id:
                supplier_id = supplier_key
            else:
                supplier_id = "SUP" + timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S")
            supplier_query = Suppliers(
                sup_id = supplier_id,
                supplier = supplier_name
            )
            supplier_query.save()
            
            bid = Bids(
                document_id = tender_id,
                item_id = item_id,
                sup_id = supplier_id,
                unit_price = unit_price,
                vat = vat,
                quoted_qty = quantity,
                bid_no = bid_no,
                quote_date = bid_date,
                rfq_no = rfq_no,
                total = total_price,
                bid_document = bid_document_path,
            )
            bid.save()
        
        if 'add_supplier' in request.POST:
            return redirect('add_supplier', tender_id=tender_id)
            
        return render(request, 'finance/tenders/tenders_create.html', {
            "proc_plans": proc_plans,
            "suppliers": suppliers_json
        })

@login_required      
def cs_compliance_table(request, cs_id):
    
    if request.method == 'GET':
        tender_id = tender_id
        tender = ComparativeSchedules.objects.filter(document_id=tender_id).first()
        bids = Bids.objects.filter(document_id=tender_id).order_by('bid_no').all()

        bids_dict = {}
        for bid in bids:
            bids_dict.update({bid.bid_no: []})
            
        for i in range(0, len(bids_dict)):
            i = i + 1
            for bid in bids:
                if int(bid.bid_no) == i:
                    supplier = Suppliers.objects.filter(sup_id=bid.sup_id).first()
                    item = CSItems.objects.filter(item_id=bid.item_id).first()
                    
                    print(supplier, supplier.supplier, supplier.sup_id)
                    supplier_id = supplier.sup_id
                    supplier_name = supplier.supplier
                    bids_dict[str(i)].append({
                        "bid_no": int(bid.bid_no),
                        "supplier_name": supplier_name,
                        "supplier_id": supplier_id,
                        "bid": bid,
                    })
    elif request.method == 'POST':
        document_id = request.POST['document_id']
        rfq_no = request.POST['rfq_no']
        bid_count = request.POST['bid_count']
        
        # get compliance table values
        for i in range(1,bid_count):
            supplier_id = request.POST['supplier_id'+i+'']
            payment_terms = request.POST['payment_terms'+i+'']
            bid_validity = request.POST['bid_validity'+i+'']
            delivery_period = request.POST['delivery_period'+i+'']
            technical_specifications = request.POST['technical_specifications'+i+'']
            valid_tax_clearance = request.POST['valid_tax_clearance'+i+'']
            registered_with_praz = request.POST['registered_with_praz'+i+'']
            site_visit_done = request.POST['site_visit_done'+i+'']
            samples_delivered = request.POST['samples_delivered'+i+'']
            decision = request.POST['decision'+i+'']
            remarks = request.POST['remarks'+i+'']
            
            # insert into compliance table
            tender_compliance = CSCompliance(
                document_id = document_id,
                supplier_id = supplier_id,
                rfq_no = rfq_no,
                payment_terms = payment_terms,
                bid_validity = bid_validity,
                delivery_period = delivery_period,
                technical_specifications = technical_specifications,
                valid_tax_clearance = valid_tax_clearance,
                registered_with_praz = registered_with_praz,
                site_visit_done = site_visit_done,
                samples_delivered = samples_delivered,
                decision = decision,
                remarks = remarks,
            )
            tender_compliance.save()
            
        return redirect('tender_compliance', tender_id=document_id)


    return render(request, 'finance/comparative_schedules/cs_compliance_table.html', {"bids_items": bids_dict})
