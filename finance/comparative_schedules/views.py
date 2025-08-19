import base64
import csv
import os
from django.core.files.storage import FileSystemStorage
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import datetime
from django.db.models import Sum

from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str
from django.template.loader import render_to_string

# Add proper logging
import logging
logger = logging.getLogger(__name__)

# Import pagination config for Stage 2 optimization
from .pagination_config import get_safe_page_size, get_pagination_info, DATATABLE_MAX_SIZE, DATATABLE_DEFAULT_SIZE

# Import optimized file handlers
from .optimized_file_handlers import OptimizedFileHandler, OptimizedAttachmentHandler

from it.users.views import ms_exhange_reset_password_html, ms_exhange_send, ms_exhange_send_html
from .models import *
from it.users.models import *
from finance.purchase_request.models import PurchaseRequest, PrItem, Attachment, \
    UnitOfMeasurement
from ACE2.models import Ace2
from finance.comparative_schedules.models import *
from django.db.models import Q, Exists, OuterRef, Count, F, Prefetch
import pandas as pd
from django.core.paginator import Paginator
from django.utils import timezone
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_http_methods
import copy
from django.conf import settings
# FileSystemStorage no longer needed - file uploads handled by dedicated APIs
from django.core.cache import cache

from django.contrib import messages

APP_NAME = "comparative_schedule"
CACHE_TIMEOUT = 300  # 5 minutes

# Helper functions for optimized file handling
def get_optimized_file_handler(user):
    """Get optimized file handler instance"""
    return OptimizedFileHandler(user)

def get_optimized_attachment_handler(user):
    """Get optimized attachment handler instance"""
    return OptimizedAttachmentHandler(user)

def save_file_optimized(file, file_type='general', description=None, user=None):
    """Save file using optimized handler"""
    if not user:
        return None
    
    file_handler = get_optimized_file_handler(user)
    try:
        result = file_handler.save_file_optimized(file, file_type, description)
        return result
    except Exception as e:
        logger.error(f"Error saving file optimized: {e}")
        return None

def get_attachments_metadata_optimized(attachments, user=None, include_preview=False):
    """Get attachment metadata without Base64 encoding"""
    if not user:
        return []
    
    attachment_handler = get_optimized_attachment_handler(user)
    try:
        return attachment_handler.get_attachments_metadata(attachments, include_preview)
    except Exception as e:
        logger.error(f"Error getting attachments metadata: {e}")
        return []

def get_cs_file_metadata_optimized(cs_instance, file_field_name, user=None):
    """Get file metadata for ComparativeSchedules file fields"""
    if not user:
        return None
    
    attachment_handler = get_optimized_attachment_handler(user)
    try:
        return attachment_handler.get_cs_file_metadata(cs_instance, file_field_name)
    except Exception as e:
        logger.error(f"Error getting CS file metadata: {e}")
        return None

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
    #             print("No User: ", row['created_by'])M
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
            item_id = row['item_id']
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
                            cs_id=cs_query,
                            item_id=item_id,
                            item_name=item_name,
                            quantity=quantity,
                            unit_of_measurement=unit_of_measurement,
                        )
                        item_query.save()

                        print("bid_no", bid_no)
                        bid = Bids(
                            cs_id=cs_query,
                            item_id=item_query,
                            sup_id=supplier,
                            unit_price=unit_price,
                            vat=vat,
                            quoted_qty=quoted_qty,
                            bid_no=bid_no,
                            quote_date=quote_date,
                            total=total,
                            bid_document=bid_document,
                        )
                        bid.save()
                        item_df = pd.concat([item_df, pd.DataFrame(
                            {'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['SUCCESS'],
                             'message': ['SUCCESS']})], ignore_index=True)
                    else:
                        item_df = pd.concat([item_df, pd.DataFrame(
                            {'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'],
                             'message': ['Item Not Found']})], ignore_index=True)
                else:
                    item_df = pd.concat([item_df, pd.DataFrame(
                        {'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'],
                         'message': ['DB Supplier Not Found']})], ignore_index=True)
            else:
                item_df = pd.concat([item_df, pd.DataFrame(
                    {'document_id': [cs_id], 'item_id': [item_id], 'sup_id': [sup_id], 'status': ['FAILED'],
                     'message': ['Schedule Not Found']})], ignore_index=True)
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
                        item_required=row['item_required'],
                        quantity=row['qty'],
                        unit_of_measurement=uom,
                        purchase_request=pr,
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
    print("user: ", user.username, user.id)
    fm_role, gm_role, procurement_role = False, False, False

    try:
        user_comparative_schedule_role = user.roles.filter(application=APP_NAME).first()
        print(f"🔍 User roles for {APP_NAME}:", user_comparative_schedule_role)

        if user_comparative_schedule_role and user_comparative_schedule_role.application == APP_NAME:
            print(f"🔍 User role: {user_comparative_schedule_role.role}")
            if user_comparative_schedule_role.role == "check":
                fm_role = True
                print("✅ FM role detected")
            if user_comparative_schedule_role.role == "approve":
                gm_role = True
                print("✅ GM role detected")
            if user_comparative_schedule_role.role == "procurement":
                procurement_role = True
                print("✅ Procurement role detected")
        else:
            print(f"❌ No {APP_NAME} role found for user")
            # Debug: show all user roles
            all_roles = user.roles.all()
            print(f"🔍 All user roles: {[f'{r.application}:{r.role}' for r in all_roles]}")

    except Exception as ex:
        # messages.error(request, "Warning: Please not that you do not have the required roles to access this page.")
        print("Error: ", ex)

    print(f"🔍 Final roles - FM: {fm_role}, GM: {gm_role}, Procurement: {procurement_role}")
    return fm_role, gm_role, procurement_role


def notify_user(user_, msg, notification_type, url, id, request):
    try:
        Notification.objects.create(
            user=user_,
            message=msg,
            notification_type=notification_type,
            notification_id=id,
            url=url,
            created_at=datetime.now(),
        )
        print("notification ","email ", user_.email, "msg ", msg, "notification_type ", notification_type, "url ", url, "id ", id)
        
        if "direct_purchase" in url:
            app_base = "direct_purchase/comperative_schedule/"+id
        elif "comperative_schedule" in url:
            app_base = "comperative_schedule/comperative_schedule/"+id
        else:
            app_base = url
        
        email_template_name = 'registration/email.html'
        # {urlsafe_base64_encode(force_bytes(user.pk))}/{default_token_generator.make_token(user)}
        c = {
            "email": user_.email if user_.email else "",
            "message": msg,
            "type": notification_type,
            "redirect_app_base": app_base,
            "id": id,
            "domain": request.META['HTTP_HOST'],
            "site_name": "Zetdc Business Excellence",
            "uid": urlsafe_base64_encode(force_bytes(user_.pk)),
            "user": user_,
            "token": default_token_generator.make_token(user_),
            "protocol": 'https' if request.is_secure() else 'http',
        }
        email = render_to_string(email_template_name, c, request=request)
        ms_exhange_reset_password_html(subject=notification_type,to_recipients=[user_.email], cc_recipients=[],template=email,
                                        kwargs={"kwargs": c})
        return True
    except Exception as e:
        print("error: ", str(e))
        return False

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
        "page_title": "RFQ Comparative Schedules", })


@login_required
def get_all_schedules(request):
    user_id = request.user.id
    print("user name: ", request.user.username, request.user.id)
    user_profile = UserProfile.objects.filter(id=user_id).first()
    print("user: ", user_profile.username, user_profile.id)
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)

    user_page = 'finance/comparative_schedules/cs_schedules.html'
    return render(request, user_page, {"fm_role": fm_role, "gm_role": gm_role, "procurement_role": procurement_role,
                                       "page_title": "RFQ Comparative Schedules"})


@login_required
def reports_all_schedules(request):
    user_id = request.user.id
    print("user name: ", request.user.username, request.user.id)
    user_profile = UserProfile.objects.filter(id=user_id).first()
    print("user: ", user_profile.username, user_profile.id)
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)

    user_page = 'finance/comparative_schedules/cs_reports.html'
    return render(request, user_page, {"fm_role": fm_role, "gm_role": gm_role, "procurement_role": procurement_role,
                                       "page_title": "RFQ Comparative Schedules"})


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
    
    try:   
        cs = ComparativeSchedules.objects.select_related(
            'created_by', 'region', 'section', 'pr_id'
        ).prefetch_related(
            Prefetch('committee_set', queryset=Committee.objects.select_related('user')),
            Prefetch('csapproval_set', queryset=CSApproval.objects.select_related('user'))
        ).filter(
            region=region,
            created_by_id=user_id,
            cancelled=False
        )

        # Filter based on search value
        if search_value:
            cs = cs.filter(
                Q(cs_id__icontains=search_value) |
                Q(scope_of_work__icontains=search_value)
            )
        if column_name:
            cs = cs.order_by(column_name)

        return cs
    except Exception as ex:
        print("Error: ", ex)
        return []


def get_pending_committee_table(user_id, search_value=None, column_name=None, region=None):
    print("user id: ", user_id)
    # fetch schedules if user exists in the committee and has not yet approved
    cs = ComparativeSchedules.objects.select_related(
        'created_by', 'region', 'section', 'pr_id'
    ).prefetch_related(
        Prefetch('committee_set', queryset=Committee.objects.select_related('user')),
        Prefetch('csapproval_set', queryset=CSApproval.objects.select_related('user'))
    ).filter(
        Q(committee__committee_approval=None) | Q(committee__committee_approval=""),
        Q(committee__user_id=user_id),
        cancelled=False,
        region=region,
    )

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
        cancelled=False,
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
    cs = ComparativeSchedules.objects.select_related(
        'created_by', 'region', 'section', 'pr_id'
    ).prefetch_related(
        Prefetch('committee_set', queryset=Committee.objects.select_related('user')),
        Prefetch('csapproval_set', queryset=CSApproval.objects.select_related('user'))
    ).filter(region=region, cancelled=False)

    # Filter based on search value
    if search_value:
        cs = cs.filter(
            Q(cs_id__icontains=search_value) |
            Q(scope_of_work__icontains=search_value)
        )

    if column_name:
        cs = cs.order_by(column_name)

    return cs


def get_filtered_schedules(user_id, search_value, column_name, user_region, status, station, pickStation, start_date,
                           end_date):
    print("user id: ", user_id, "search_value: ", search_value, "column_name: ", column_name, "user_region: ",
          user_region, "status: ", status, "station: ", station, "pickStation: ", pickStation, "start_date: ",
          start_date, "end_date: ", end_date)
    cs = ComparativeSchedules.objects.select_related(
        'created_by', 'region', 'section', 'pr_id'
    ).prefetch_related(
        Prefetch('committee_set', queryset=Committee.objects.select_related('user')),
        Prefetch('csapproval_set', queryset=CSApproval.objects.select_related('user'))
    ).filter(
        region=user_region,
    )

    try:

        if status:
            if status == "Pending Committee":
                cs = cs.filter(
                    Q(committee__committee_approval=None) | Q(committee__committee_approval="")).exclude(
                    Q(committee__committee_approval="Rejected"))
            if status == "Pending Finance":
                cs = cs.filter(Q(csapproval__approval="") | Q(csapproval__approval=None)).exclude(
                    Q(committee__committee_approval=None) | Q(committee__committee_approval="") | Q(
                        committee__committee_approval="Rejected")
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
            print("error: ", ex)
        status = request.GET.get('status')
        station = request.GET.get('station')
        pickStation = request.GET.get('pick_station')
        start_date = request.GET.get('start_date')
        end_date = request.GET.get('end_date')
        data = get_filtered_schedules(user_id=user_id, search_value="", column_name="", user_region=user_region,
                                      status=status, station=station, pickStation=pickStation, start_date=start_date,
                                      end_date=end_date)
        custom_data = add_details(data)
        # build csv file and return as response
        try:
            writer = csv.writer(response)
            writer.writerow(
                ['CS ID', 'PR ID', 'PR Number', 'PR Date', 'Scope of Work', 'Closing Date', 'Closing Time', 'Advert',
                 'PR Number', 'PR Date', 'CS Opened', 'TAC Date', 'Created By', 'Committee Approval', 'GM Approval',
                 'FM Approval', 'Section', 'Region', 'Created At'])
            for item in custom_data:
                try:
                    writer.writerow(
                        [item['cs_id'], item['pr_id'], item['pr_number'], item['pr_date'], item['scope_of_work'],
                         item['closing_date'], item['closing_time'], item['advert'], item['pr_number'], item['pr_date'],
                         item['cs_opened'], item['tac_date'], item['created_by'], item['committee_approval'],
                         item['gm_approval'], item['fm_approval'], item['section'], item['region'], item['created_at']])

                except Exception as ex:
                    print("For Writting to CSV: ", ex)
        except Exception as ex:
            print("Error Writting to CSV: ", ex)
    except Exception as ex:
        print("Error: ", ex)

    return response


def add_details(cs_queryset):
    cs_list = []
    
    for c in cs_queryset:
        committee_approval = ""
        gm_approval = None
        fm_approval = None
        committee_reject_reason = ""
        
        # Use prefetched committee data instead of new queries
        committee_list = list(c.committee_set.all())
        
        if len(committee_list) > 0:
            committee_approved = all([comm.committee_approval == "Approved" for comm in committee_list])
            if committee_approved:
                committee_approval = "Approval Complete"
                # Use prefetched approval data
                fm_approval = next((app for app in c.csapproval_set.all() 
                                  if app.approver_role == "finance_manager"), None)
                gm_approval = next((app for app in c.csapproval_set.all() 
                                  if app.approver_role == "general_manager"), None)
            else:
                committee_approval = "Pending"
                fm_approval = None
                gm_approval = None

                committee_pending = any(comm.committee_approval in ["", None] for comm in committee_list)
                if committee_pending:
                    committee_approval = "Pending"

                committee_rejected = next((comm for comm in committee_list 
                                        if comm.committee_approval == "Rejected"), None)
                if committee_rejected:
                    committee_reject_reason = committee_rejected.justification
                    committee_approval = "Rejected"
        else:
            committee_approval = "Pending"
            fm_approval = None
            gm_approval = None

        try:
            cs_list.append({
                "cs_id": c.cs_id,
                "pr_id": c.pr_id.id if c.pr_id else "",
                "pr_number": c.pr_number,
                "pr_date": c.pr_date,
                "scope_of_work": c.scope_of_work,
                "closing_date": c.closing_date,
                "closing_time": c.closing_time,
                "advert": c.advert,
                "cs_opened": c.cs_opened,
                "tac_date": c.tac_date,
                "created_by": c.created_by.username if c.created_by else None,
                "committee_approval": committee_approval,
                "committee_reject_reason": committee_reject_reason,
                "gm_approval": gm_approval.approval if gm_approval else "Pending",
                "gm_reject_reason": gm_approval.justification if gm_approval else "",
                "fm_approval": fm_approval.approval if fm_approval else "Pending",
                "fm_reject_reason": fm_approval.justification if fm_approval else "",
                "section": c.section.section if c.section else "",
                "region": c.region.region if c.region else "",
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
        print("error: ", ex)
    draw = int(request.GET.get('draw', default=1))
    start = int(request.GET.get('start', default=0))
    requested_length = int(request.GET.get('length', default=DATATABLE_DEFAULT_SIZE))
    search_value = request.GET.get('search[value]', default='')
    
    # Apply safe pagination limits for datatable (Stage 2 optimization)
    length = get_safe_page_size(requested_length, 'schedules')
    
    # Log warning if user requested too large page size
    if requested_length > length:
        logger.warning(f"DataTable requested length {requested_length} reduced to {length} for memory protection")

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
        data = get_filtered_schedules(user_id, search_value, column_name, user_region, status, station, pickStation,
                                      start_date, end_date)

    # Total number of records before filtering
    total = len(data)
    # Pagination
    paginator = Paginator(data, length)
    page_number = start // length + 1
    page_obj = paginator.get_page(page_number)

    # Prepare response
    print("adding details: ", page_obj.object_list)
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
    
    try:
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
        # user = UserProfile.objects.filter(id=cs.created_by_id).first()  # Redundant - using cs_owner instead
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
        users = UserProfile.objects.filter(region=cs.region).all() if cs and cs.region else UserProfile.objects.all()
        
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
                # Construct the correct file path
                if cs.advert.startswith('uploads/'):
                    # File is stored in root directory (BASE_DIR)
                    file_path = os.path.join(settings.BASE_DIR, cs.advert)
                else:
                    # File is stored with absolute path
                    file_path = cs.advert
                
                print(f"🔍 Attempting to read advert file: {file_path}")
                print(f"🔍 File exists: {os.path.exists(file_path)}")
                
                if os.path.exists(file_path):
                    with open(file_path, 'rb') as f:
                        file_data = f.read()
                    encoded_advert_file = base64.b64encode(file_data).decode('utf-8')
                    print(f"✅ Successfully encoded advert file: {len(encoded_advert_file)} characters")
                else:
                    print(f"❌ Advert file not found at path: {file_path}")
                    # Try alternative locations
                    alt_paths = [
                        os.path.join(settings.BASE_DIR, cs.advert),
                        os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts', os.path.basename(cs.advert)),
                        os.path.join(settings.MEDIA_ROOT, 'uploads', 'comparative', 'adverts', os.path.basename(cs.advert)),
                        os.path.join(settings.MEDIA_ROOT, 'uploads', 'purchase_request', os.path.basename(cs.advert))
                    ]
                    
                    for alt_path in alt_paths:
                        if os.path.exists(alt_path):
                            print(f"✅ Found file at alternative path: {alt_path}")
                            with open(alt_path, 'rb') as f:
                                file_data = f.read()
                            encoded_advert_file = base64.b64encode(file_data).decode('utf-8')
                            break
                    else:
                        print(f"❌ File not found at any alternative location")
                        
        except Exception as ex:
            print(f"Error reading advert file: {ex}")
            print(f"Advert field value: {cs.advert}")
            print(f"MEDIA_ROOT: {settings.MEDIA_ROOT}")
            print(f"BASE_DIR: {settings.BASE_DIR}")
            
        cs_owner = UserProfile.objects.filter(id=cs.created_by_id).first() if cs and cs.created_by_id else None
        if not cs_owner and cs:
            print(f"CS Owner not found for CS {cs.cs_id}, created_by_id: {cs.created_by_id}")
        elif not cs:
            print(f"CS not found for cs_id: {cs_id}")  
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
            "created_by": cs_owner.username if cs_owner else "",
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
        
        return JsonResponse(context, safe=False)
    except Exception as ex:
        print("Wholesome Error: ", ex)
        return JsonResponse({
            "message": "Error retrieving Comparative Schedule data",
            "error": str(ex),
            "success": False,
        }, safe=False)


def save_file(f, file_path):
    if f:
        try:
            # Ensure the directory exists
            directory = os.path.dirname(file_path)
            if directory and not os.path.exists(directory):
                os.makedirs(directory, exist_ok=True)
                print(f"✅ Created directory: {directory}")
            
            # Save the file
            with open(file_path, 'wb+') as destination:
                for chunk in f.chunks():
                    destination.write(chunk)
            print(f"✅ File saved successfully: {file_path}")
            return True
        except Exception as ex:
            print(f"❌ Error saving file {file_path}: {ex}")
            return False
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

        # Use optimized file handling instead of Base64 encoding
        pr_at_list = get_attachments_metadata_optimized(pr_attachments, request_user)

        pr_item_list = []
        for pr_item in pr_items:
            pr_item_list.append({
                "id": pr_item.id,
                "item_required": pr_item.item_required,
                "quantity": pr_item.quantity,
                "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
                "ordered": pr_item.ordered,
            })

        # get proc plan for PR
        try:
            if purchase_request.procurement_plan_reference:
                proc_ref = "acc" + str(purchase_request.procurement_plan_reference.id)
            else:
                proc_ref = ""
            pr_proc_plan = ProcPlan.objects.filter(proc_ref=proc_ref).first()
        except Exception as ex:
            logger.error(f"Error getting DP proc plan: {ex}")
            pr_proc_plan = None

        return JsonResponse({
            "success": True,
            "requester_role": user_comparative_schedule_role.role if user_comparative_schedule_role else "",
            "message": "PR details retrieved successfully",
            "pr_id": pr_id,
            "scope_of_work": purchase_request.scope_of_work if purchase_request.scope_of_work else "",
            "proc_ref": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
            "proc_plan": {
                "id": pr_proc_plan.id if pr_proc_plan else "",
                "proc_ref": pr_proc_plan.proc_ref if pr_proc_plan else "",
                "description": pr_proc_plan.description if pr_proc_plan else "",
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
                # Use proper media path construction
                timestamp = timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S%p")
                filename = f"{timestamp}_{advert_file.name}"
                advert_path = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts', filename)
                save_file(advert_file, advert_path)
                # Store relative path in database for consistency
                advert_path_db = os.path.join('uploads', 'comparative', 'adverts', filename)

            if 'bid_document' in request.FILES:
                bid_document_file = request.FILES['bid_document']
                # Use proper media path construction
                timestamp = datetime.now().strftime("%Y%m%d%I%M%S%p")
                filename = f"{timestamp}_{bid_document_file.name}"
                bid_document_path = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts', filename)
                save_file(bid_document_file, bid_document_path)
                # Store relative path in database for consistency
                bid_document_path_db = os.path.join('uploads', 'comparative', 'adverts', filename)

        except Exception as ex:
            print("Error: ", ex)

        for i in range(0, int(item_count)):
            item_id = "Item" + datetime.now().strftime("%Y%m%d%I%M%S%p")
            description = request.POST['supplier[item_name][' + str(i) + ']']
            quantity = request.POST['supplier[quantity][' + str(i) + ']']
            unit_of_measurement = request.POST['supplier[unit_of_measurement][' + str(i) + ']']
            vat = request.POST['supplier[vat][' + str(i) + ']']
            unit_price = request.POST['supplier[unit_price][' + str(i) + ']']
            total_price = request.POST['supplier[total_price][' + str(i) + ']']

            item = CSItems(
                cd_id=tender_id,
                item_id=item_id,
                item=description,
                required_qty=quantity,
                unit_of_measurement=unit_of_measurement,
            )
            item.save()

            supplier_id = ""
            if supplier_key:
                supplier_id = supplier_key
            else:
                supplier_id = "SUP" + datetime.now().strftime("%Y%m%d%I%M%S")
            supplier_query = Supplier(
                sup_id=supplier_id,
                supplier=supplier_name
            )
            supplier_query.save()

            bid = Bids(
                document_id=tender_id,
                item_id=item_id,
                sup_id=supplier_id,
                unit_price=unit_price,
                vat=vat,
                quoted_qty=quantity,
                bid_no=bid_no,
                quote_date=bid_date,
                rfq_no=rfq_no,
                total=total_price,
                bid_document=bid_document_path_db if 'bid_document_path_db' in locals() else bid_document_path,
            )
            bid.save()

        cs_query = ComparativeSchedules(
            document_id=tender_id,
            rfq_date=rfq_date,
            scope_of_work=scope,
            closing_date=closing_date,
            closing_time=closing_time,
            rfq_no=rfq,
            advert=advert_path_db if 'advert_path_db' in locals() else advert_path,
            date_created=date_tender_opened,
            pr_number=pr_number,
            pr_date=pr_date,
            tender_opened=date_tender_opened,
            tac_date=tender_adjudication_committee_date,
            region="",
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
    """
    Save a new comparative schedule.
    
    The advert field should be a file path (string) from a previous file upload API call.
    File uploads are handled separately by dedicated file upload APIs.
    """
    try:
        print("save_comparative_schedule request: ", request.POST)
        cs_id = "CS" + datetime.now().strftime("%Y%m%d%I%M%S")
        cs_exists = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
        # @TODO try random number if cs_id exists or return error
        if cs_exists:
            cs_id = "CS" + datetime.now().strftime("%Y%m%d%I%M%S")

        # Get advert file path from POST data (file uploads handled separately)
        advert_path = request.POST.get("advert", "").strip()
        scope_of_work = request.POST.get("scope_of_work", "")
        pr_number = request.POST.get("pr_number", "")
        pr_date = request.POST.get("pr_date", "")
        ref_date = request.POST.get("ref_date", "")
        currency = request.POST.get("currency", "")

        closing_date = request.POST.get("closing_date", "")
        closing_time = request.POST.get("closing_time", "")
        date_tender_opened = request.POST.get("date_tender_opened", "")
        tender_adjudication_committee_date = request.POST.get("tender_adjudication_committee_date", "")
        username = request.POST.get("username", "")

        # Validate advert file path if provided
        if advert_path:
            print(f"🔍 Validating advert file path: {advert_path}")
            print(f"🔍 Settings - BASE_DIR: {settings.BASE_DIR}")
            print(f"🔍 Settings - MEDIA_ROOT: {settings.MEDIA_ROOT}")
            
            # Basic path validation
            if not advert_path.startswith('uploads/'):
                print(f"Warning: Invalid file path format. Expected 'uploads/...', got: {advert_path}")
                advert_path = ""
            else:
                # Check if the file path exists and is valid
                # Files are stored in media/uploads/, so we need to check both possible locations
                base_path = os.path.join(settings.BASE_DIR, advert_path)
                media_path = os.path.join(settings.MEDIA_ROOT, advert_path)
                
                print(f"🔍 Checking file existence:")
                print(f"  - Base path: {base_path}")
                print(f"  - Media path: {media_path}")
                
                if os.path.exists(base_path):
                    print(f"✅ File found at base path: {advert_path}")
                    # Note: File exists in BASE_DIR/uploads/ but should be in MEDIA_ROOT/uploads/
                    print(f"⚠️  WARNING: File exists in BASE_DIR/uploads/ but should be in MEDIA_ROOT/uploads/")
                    print(f"⚠️  This indicates a file upload configuration issue")
                elif os.path.exists(media_path):
                    print(f"✅ File found at media path: {advert_path}")
                else:
                    print(f"❌ File not found at either location")
                    print(f"  - Base path exists: {os.path.exists(base_path)}")
                    print(f"  - Media path exists: {os.path.exists(media_path)}")
                    print(f"⚠️  SUGGESTION: Check if file upload system is saving to correct location")
                    # Reset to empty if file doesn't exist
                    advert_path = ""
        else:
            print("No advert file path provided")

        # save cs details
        # fetch purchase request
        print("pr number: ", pr_number)
        pr = PurchaseRequest.objects.get(id=pr_number)
        # Handle both proc_ref and proc_plan_id fields from frontend
        proc_ref = request.POST.get("proc_ref", "").strip()
        proc_plan_id = request.POST.get("proc_plan", "").strip()  # Frontend sends this as 'proc_plan'
        
        # Debug: Log all POST data to see what's actually being sent
        print(f"Direct Purchase - All POST data keys: {list(request.POST.keys())}")
        print(f"Direct Purchase - proc_ref: '{proc_ref}', proc_plan_id: '{proc_plan_id}'")
        
        # Determine which field to use for finding the procurement plan
        proc_plan = None
        
        if proc_plan_id and proc_plan_id.strip():
            # Frontend sent proc_plan_id, try to find by ID first
            try:
                if proc_plan_id.startswith('"'):
                    # Clean the string and convert to integer for ID lookup
                    cleaned_proc_plan_id = proc_plan_id.strip().replace('"', '').replace("'", "")
                    print(f"Direct Purchase - Cleaned proc_plan_id: '{cleaned_proc_plan_id}'")
                    proc_plan_ref = "acc" + cleaned_proc_plan_id
                    proc_plan = ProcPlan.objects.filter(proc_ref=proc_plan_ref).first()
                    print(f"Direct Purchase - Found proc_plan by ID: {proc_plan}")
                else:
                    proc_plan = ProcPlan.objects.filter(id=proc_plan_id).first()
                    print(f"Direct Purchase - Found proc_plan by ID: {proc_plan}")
            except (ValueError, TypeError) as e:
                print(f"Direct Purchase - Invalid proc_plan_id format: '{proc_plan_id}', error: {e}")
                # If ID lookup fails, try proc_ref as fallback
                if proc_ref and proc_ref.strip():
                    if not proc_ref.startswith("acc"):
                        temp_proc_ref = "acc" + proc_ref
                        proc_ref = temp_proc_ref
                    proc_plan = ProcPlan.objects.filter(proc_ref=proc_ref).first()
                    print(f"Direct Purchase - Found proc_plan by proc_ref fallback: {proc_plan}")
        elif proc_ref and proc_ref.strip():
            # Frontend sent proc_ref, use the original logic
            if not proc_ref.startswith("acc"):
                temp_proc_ref = "acc" + proc_ref
                proc_ref = temp_proc_ref
            proc_plan = ProcPlan.objects.filter(proc_ref=proc_ref).first()
            print(f"Direct Purchase - Found proc_plan by proc_ref: {proc_plan}")
        else:
            print("Direct Purchase - No procurement plan reference provided")
        
        # fetch user
        user = UserProfile.objects.filter(username=username).first()
        currency = Currency.objects.filter(id=currency).first() if currency else None
        # region_ = Regions.objects.filter(region=pr.region).first() if 'region' in pr else None
        # section = Sections.objects.filter(section=pr.section).first() if 'section' in pr else None
        cs_query = ComparativeSchedules(
            cs_id=cs_id,
            pr_id_id=pr.id,
            scope_of_work=scope_of_work,
            currency=currency,
            closing_date=closing_date,
            closing_time=closing_time,
            advert=advert_path,
            pr_number=pr_number,
            pr_date=pr_date,
            ref_date=ref_date,
            proc_plan=proc_plan,
            cs_opened=date_tender_opened,
            tac_date=tender_adjudication_committee_date,
            created_by_id=user.id,
            cost_center=user.cost_center if user.cost_center else None,
            region_id=user.region_id if user.region_id else None,
        )
        cs_query.save()
        
        print(f"✅ Comparative Schedule saved successfully:")
        print(f"   - CS ID: {cs_id}")
        print(f"   - Advert path: {advert_path}")
        print(f"   - Owner: {user.username if user else 'Unknown'}")

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
    """
    Update an existing comparative schedule.
    
    The advert field should be a file path (string) from a previous file upload API call.
    File uploads are handled separately by dedicated file upload APIs.
    If no advert path is provided, the existing advert remains unchanged.
    """
    try:

        # Get advert file path from POST data (file uploads handled separately)
        advert_path = request.POST.get("advert", "").strip()
        print("advert_path from POST: ", advert_path)
        
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

        # Validate advert file path if provided
        if advert_path:
            print(f"🔍 Validating advert file path: {advert_path}")
            print(f"🔍 Settings - BASE_DIR: {settings.BASE_DIR}")
            print(f"🔍 Settings - MEDIA_ROOT: {settings.MEDIA_ROOT}")
            
            # Basic path validation
            if not advert_path.startswith('uploads/'):
                print(f"Warning: Invalid file path format. Expected 'uploads/...', got: {advert_path}")
                advert_path = ""
            else:
                # Check if the file path exists and is valid
                # Files are stored in media/uploads/, so we need to check both possible locations
                base_path = os.path.join(settings.BASE_DIR, advert_path)
                media_path = os.path.join(settings.MEDIA_ROOT, advert_path)
                
                print(f"🔍 Checking file existence:")
                print(f"  - Base path: {base_path}")
                print(f"  - Media path: {media_path}")
                
                if os.path.exists(base_path):
                    print(f"✅ File found at base path: {advert_path}")
                    # Note: File exists in BASE_DIR/uploads/ but should be in MEDIA_ROOT/uploads/
                    print(f"⚠️  WARNING: File exists in BASE_DIR/uploads/ but should be in MEDIA_ROOT/uploads/")
                    print(f"⚠️  This indicates a file upload configuration issue")
                elif os.path.exists(media_path):
                    print(f"✅ File found at media path: {advert_path}")
                else:
                    print(f"❌ File not found at either location")
                    print(f"  - Base path exists: {os.path.exists(base_path)}")
                    print(f"  - Media path exists: {os.path.exists(media_path)}")
                    print(f"⚠️  SUGGESTION: Check if file upload system is saving to correct location")
                    # Reset to empty if file doesn't exist
                    advert_path = ""
        else:
            print("No advert file path provided - keeping existing advert unchanged")

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
            # Only update advert if we have a valid file path
            if advert_path and advert_path.strip():
                cs_query.advert = advert_path
                print(f"Updated advert path: {advert_path}")
            # Note: If no advert_path is provided, we keep the existing one unchanged
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
            
            print(f"✅ Comparative Schedule updated successfully:")
            print(f"   - CS ID: {cs_id}")
            print(f"   - Advert path: {advert_path}")
            print(f"   - Updated by: {username}")
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
            pr_item = PrItem.objects.filter(item_required=item['item_required'],
                                            purchase_request=purchase_request).first()
            if pr_item:
                pr_item.ordered = True
                pr_item.save()
                print("item: ", item)
                cs_required_items = CSRequiredItems(
                    cs_id=cs_query,
                    item_id=item['id'],
                    item_name=item['item_required'],
                    quantity=item['quantity'],
                    unit_of_measurement=item['unit_of_measurement'],
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
            name=supplier_name
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
            # Use proper media path construction
            timestamp = datetime.now().strftime("%Y%m%d%I%M%S")
            filename = f"{timestamp}_{bid_doc.name}"
            root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts')
            fs = FileSystemStorage(location=root_dir)
            filename_ = fs.save(filename, bid_doc)
            bid_doc_path = os.path.join('uploads', 'comparative', 'adverts', filename_)
            print(f"✅ Bid document saved: {bid_doc_path}")
    except Exception as ex:
        print(f"❌ Error saving bid document: {ex}")

    for item in items:
        item_id = "Item" + datetime.now().strftime("%Y%m%d%I%M%S%p")
        item_query = CSItems(
            cs_id=cs_query,
            item_id=item_id,
            item_name=item['item_required'],
            quantity=item['quantity'],
            unit_of_measurement=item['unit_of_measurement'],
        )
        item_query.save()

        bid = Bids(
            cs_id=cs_query,
            item_id=item_query,
            sup_id=supplier,
            unit_price=item['unit_price'] if 'unit_price' in item else "",
            vat=item['vat'] if 'vat' in item else "",
            quoted_qty=item['quantity'] if 'quantity' in item else "",
            bid_no=bid_no,
            quote_date=bid_date,
            total=item['total_price'] if 'total_price' in item else "",
            bid_document=bid_doc_path,
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
        
        # update bid numbers after all bids are deleted
        # Get unique suppliers and their current bid numbers
        from django.db.models import Min
        supplier_bid_numbers = Bids.objects.filter(cs_id=cs_query).values('sup_id').annotate(
            min_bid_no=Min('bid_no')
        ).order_by('min_bid_no')
        
        # Reorder bid numbers for each supplier
        for index, supplier_bid in enumerate(supplier_bid_numbers, 1):
            new_bid_no = str(index)
            # Update all bid records for this supplier to have the new bid number
            Bids.objects.filter(cs_id=cs_query, sup_id=supplier_bid['sup_id']).update(bid_no=new_bid_no)

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
            cs_id=cs_query,
            supplier_id=supplier,
            payment_terms=payment_terms,
            bid_validity=bid_validity,
            delivery_period=delivery_period,
            technical_specifications=technical_specifications,
            valid_tax_clearance=valid_tax_clearance,
            registered_with_praz=registered_with_praz,
            site_visit_done=site_visit_done,
            samples_delivered=samples_delivered,
            decision=decision,
            remarks=remarks,
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
            cs_id=cs_query,
            supplier_id=supplier,
            remarks=remark['remarks'] if 'remarks' in remark else "",
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
            name=supplier_name
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
            cs_id=cs_query,
            supplier_id=supplier,
            rank=rank,
            remarks=remarks,
            decision=decision,
            total=total,
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
                        cs_id=cs_query,
                        user=member_profile,
                        committee_name=member['memberUserName'],
                        committee_position=member['memberPosition']
                    )
                    msg = "You have been added to the committee for RFQ " + cs_query.cs_id
                    url = "/comperative_schedule/comperative_schedule/" + cs_query.cs_id
                    notify_user(member_profile, msg, "RFQ", url, cs_query.cs_id, request)
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
                notify_user(user_, msg, "RFQ", url, cs_query.cs_id, request)

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
                cs_id=cs_query,
                user=user,
                approver_role=role,
                approval=approval,
                justification=justification,
                approval_date=timezone.now(),
                created_at=timezone.now(),
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
                cs_id=cs_query,
                user=user,
                approver_role=role,
                approval=approval,
                justification=justification,
                approval_date=timezone.now(),
                created_at=timezone.now(),
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
                    notify_user(user_, "Comperative Schedule is ready for your approval " + cs_query.cs_id, "RFQ",
                                "/comperative_schedule/comperative_schedule/" + cs_query.cs_id, cs_query.cs_id, request)

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
            supplier_list.update({supplier.sup_id: supplier.supplier})

        suppliers_json = json.dumps(supplier_list, default=str)

        return render(request, 'finance/tenders/tenders_add_supplier.html', {
            "proc_plans": proc_plans,
            "suppliers": suppliers_json,
            "tender": tender,
            "bids_items": bids_dict,
            "next_bid": len(bids_dict) + 1,
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
                # Use proper media path construction
                timestamp = timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S")
                filename = f"{timestamp}_{bid_document_file.name}"
                bid_document_path = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts', filename)
                save_file(bid_document_file, bid_document_path)
                # Store relative path in database for consistency
                bid_document_path_db = os.path.join('uploads', 'comparative', 'adverts', filename)

        except Exception as ex:
            print("Error: ", ex)

        for i in range(0, int(item_count)):
            item_id = "Item" + timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S%p")
            description = request.POST['supplier[item_name][' + str(i) + ']']
            quantity = request.POST['supplier[quantity][' + str(i) + ']']
            unit_of_measurement = request.POST['supplier[unit_of_measurement][' + str(i) + ']']
            vat = request.POST['supplier[vat][' + str(i) + ']']
            unit_price = request.POST['supplier[unit_price][' + str(i) + ']']
            total_price = request.POST['supplier[total_price][' + str(i) + ']']

            item = CSItems(
                document_id=tender_id,
                item_id=item_id,
                item=description,
                required_qty=quantity,
                unit_of_measurement=unit_of_measurement,
                rfq_no=rfq_no,
            )
            item.save()

            supplier_id = ""
            if supplier_id:
                supplier_id = supplier_key
            else:
                supplier_id = "SUP" + timezone.astimezone(timezone.get_current_timezone()).strftime("%Y%m%d%I%M%S")
            supplier_query = Suppliers(
                sup_id=supplier_id,
                supplier=supplier_name
            )
            supplier_query.save()

            bid = Bids(
                document_id=tender_id,
                item_id=item_id,
                sup_id=supplier_id,
                unit_price=unit_price,
                vat=vat,
                quoted_qty=quantity,
                bid_no=bid_no,
                quote_date=bid_date,
                rfq_no=rfq_no,
                total=total_price,
                bid_document=bid_document_path_db if 'bid_document_path_db' in locals() else bid_document_path,
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
        for i in range(1, bid_count):
            supplier_id = request.POST['supplier_id' + i + '']
            payment_terms = request.POST['payment_terms' + i + '']
            bid_validity = request.POST['bid_validity' + i + '']
            delivery_period = request.POST['delivery_period' + i + '']
            technical_specifications = request.POST['technical_specifications' + i + '']
            valid_tax_clearance = request.POST['valid_tax_clearance' + i + '']
            registered_with_praz = request.POST['registered_with_praz' + i + '']
            site_visit_done = request.POST['site_visit_done' + i + '']
            samples_delivered = request.POST['samples_delivered' + i + '']
            decision = request.POST['decision' + i + '']
            remarks = request.POST['remarks' + i + '']

            # insert into compliance table
            tender_compliance = CSCompliance(
                document_id=document_id,
                supplier_id=supplier_id,
                rfq_no=rfq_no,
                payment_terms=payment_terms,
                bid_validity=bid_validity,
                delivery_period=delivery_period,
                technical_specifications=technical_specifications,
                valid_tax_clearance=valid_tax_clearance,
                registered_with_praz=registered_with_praz,
                site_visit_done=site_visit_done,
                samples_delivered=samples_delivered,
                decision=decision,
                remarks=remarks,
            )
            tender_compliance.save()

        return redirect('tender_compliance', tender_id=document_id)

    return render(request, 'finance/comparative_schedules/cs_compliance_table.html', {"bids_items": bids_dict})


# New optimized API endpoints

@login_required
@require_http_methods(["GET"])
def api_cs_bids(request, cs_id):
    """Optimized API endpoint for CS bids only"""
    cache_key = f'cs_bids_{cs_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return JsonResponse(cached_data, safe=False)
    
    try:
        cs = ComparativeSchedules.objects.select_related().filter(cs_id=cs_id).first()
        if not cs:
            return JsonResponse({"error": "CS not found"}, status=404)
        
        # Get bids with minimal related data
        bids = Bids.objects.select_related('sup_id', 'item_id').filter(cs_id=cs).order_by('bid_no')
        
        grouped_data = {}
        for bid in bids:
            bid_no = bid.bid_no
            if bid_no not in grouped_data:
                grouped_data[bid_no] = {
                    'bid_count': bid.bid_no,
                    'supplier_name': bid.sup_id.name,
                    'bid_date': bid.quote_date,
                    'has_document': bool(bid.bid_document),
                    'items': []
                }
            
            grouped_data[bid_no]['items'].append({
                'item_id': bid.item_id.item_id,
                'item_required': bid.item_id.item_name,
                'quantity': bid.item_id.quantity,
                'unit_of_measurement': bid.item_id.unit_of_measurement,
                'unit_price': float(bid.unit_price) if bid.unit_price else 0,
                'vat': float(bid.vat) if bid.vat else 0,
                'total_price': float(bid.total) if bid.total else 0,
            })
        
        result = list(grouped_data.values())
        cache.set(cache_key, result, 300)  # Cache for 5 minutes
        
        return JsonResponse({"bids": result}, safe=False)
        
    except Exception as ex:
        return JsonResponse({"error": str(ex)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_cs_compliance(request, cs_id):
    """Optimized API endpoint for CS compliance only"""
    cache_key = f'cs_compliance_{cs_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return JsonResponse(cached_data, safe=False)
    
    try:
        cs = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
        if not cs:
            return JsonResponse({"error": "CS not found"}, status=404)
        
        compliance = CSCompliance.objects.select_related('supplier_id').filter(cs_id=cs)
        compliance_remarks = CSComplianceRemarks.objects.select_related('supplier_id').filter(cs_id=cs)
        
        compliance_list = [
            {
                "supplier_name": comp.supplier_id.name if comp.supplier_id else "",
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
            } for comp in compliance if comp.supplier_id
        ]
        
        remarks_list = [
            {
                "supplier": remark.supplier_id.id,
                "supplier_name": remark.supplier_id.name,
                "remarks": remark.remarks,
            } for remark in compliance_remarks if remark.supplier_id
        ]
        
        result = {
            "compliance": compliance_list,
            "complianceRemarks": remarks_list,
            "show_site_visit": cs.show_site_visit,
            "show_samples_required": cs.show_sample_required
        }
        
        cache.set(cache_key, result, 300)
        return JsonResponse(result, safe=False)
        
    except Exception as ex:
        return JsonResponse({"error": str(ex)}, status=500)


@login_required
@require_http_methods(["GET"])
def api_cs_committee(request, cs_id):
    """Optimized API endpoint for CS committee only"""
    cache_key = f'cs_committee_{cs_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return JsonResponse(cached_data, safe=False)
    
    try:
        cs = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
        if not cs:
            return JsonResponse({"error": "CS not found"}, status=404)
        
        committee = Committee.objects.select_related('user').filter(cs_id=cs)
        
        committee_list = [
            {
                "memberUserName": member.user.username if member.user else "",
                "memberName": f"{member.user.first_name} {member.user.last_name}" if member.user else "",
                "memberPosition": member.committee_position,
                "committeeStatus": member.committee_status,
                "memberApproval": member.committee_approval if member.committee_approval else "",
                "committeeJustification": member.justification,
                "committeeDate": member.committee_date,
            } for member in committee if member.user
        ]
        
        result = {"committee": committee_list}
        cache.set(cache_key, result, 180)  # Cache for 3 minutes
        
        return JsonResponse(result, safe=False)
        
    except Exception as ex:
        return JsonResponse({"error": str(ex)}, status=500)


@login_required
@require_http_methods(["POST"])
def api_upload_file(request):
    """Optimized file upload endpoint with validation - uses optimized handler"""
    try:
        if 'file' not in request.FILES:
            return JsonResponse({"error": "No file provided"}, status=400)
        
        file = request.FILES['file']
        file_type = request.POST.get('file_type', 'general')
        description = request.POST.get('description', '')
        
        # Use optimized file handler
        result = save_file_optimized(file, file_type, description, request.user)
        
        if result:
            return JsonResponse({
                "success": True,
                "file_path": result['file_path'],
                "metadata": result['metadata'],
                "download_url": result['download_url'],
                "preview_url": result['preview_url']
            })
        else:
            return JsonResponse({"error": "File upload failed"}, status=500)
        
    except Exception as ex:
        logger.error(f"File upload error: {ex}")
        return JsonResponse({"error": "File upload failed"}, status=500)


@login_required
@require_http_methods(["GET"])
def api_download_file(request, file_id):
    """Optimized file download with caching headers"""
    try:
        # This could be enhanced based on your file tracking model
        file_path = request.GET.get('path')
        
        if not file_path or not os.path.exists(file_path):
            return JsonResponse({"error": "File not found"}, status=404)
        
        # Security check - ensure file is in allowed directory
        allowed_dirs = ['uploads/comparative/', 'uploads/finance/']
        if not any(file_path.startswith(dir) for dir in allowed_dirs):
            return JsonResponse({"error": "Access denied"}, status=403)
        
        # Get file info
        file_size = os.path.getsize(file_path)
        filename = os.path.basename(file_path)
        
        # For small files, encode to base64
        if file_size < 5 * 1024 * 1024:  # 5MB
            encoded_data = _encode_file_safely(file_path)
            return JsonResponse({
                "filename": filename,
                "data": encoded_data,
                "size": file_size
            })
        else:
            # For large files, provide download URL
            return JsonResponse({
                "filename": filename,
                "download_url": f"/uploads/{file_path.replace('uploads/', '')}",
                "size": file_size
            })
            
    except Exception as ex:
        return JsonResponse({"error": str(ex)}, status=500)


# Optimized save operations with better error handling

@login_required
@require_http_methods(["POST"])
def api_save_cs_bid_optimized(request):
    """Optimized bid saving with transaction management"""
    from django.db import transaction
    
    try:
        cs_id = request.POST.get("cs_id", "")
        bid_no = request.POST.get("bid_count", "")
        bid_date = request.POST.get("bid_date", "")
        supplier_name = request.POST.get("supplier_name", "")
        
        # Parse JSON data
        json_data = json.loads(request.POST.get("json_data", "{}"))
        items = json_data.get("items", [])
        
        if not cs_id or not supplier_name or not items:
            return JsonResponse({
                "message": "Missing required data",
                "success": False,
            }, status=400)
        
        with transaction.atomic():
            cs_query = ComparativeSchedules.objects.select_for_update().filter(cs_id=cs_id).first()
            if not cs_query:
                return JsonResponse({
                    "message": "Comparative Schedule not found",
                    "success": False,
                }, status=404)

            # Get or create supplier
            supplier, created = Supplier.objects.get_or_create(name=supplier_name)
            
            # Clear existing bids for this supplier and bid number
            existing_bids = Bids.objects.filter(cs_id=cs_query, sup_id=supplier, bid_no=bid_no)
            if existing_bids.exists():
                clear_approvals(cs_id)
                # Delete related items first
                CSItems.objects.filter(id__in=[bid.item_id_id for bid in existing_bids if bid.item_id_id]).delete()
                existing_bids.delete()

            # Handle file upload
            bid_doc_path = ""
            bid_docs = request.FILES.get("bid_document", None)
            if bid_docs:
                upload_result = _save_file_optimized(bid_docs, 'bid')
                if upload_result['success']:
                    bid_doc_path = upload_result['file_path']

            # Bulk create items and bids
            items_to_create = []
            bids_to_create = []
            
            for item in items:
                item_id = f"Item{datetime.now().strftime('%Y%m%d%H%M%S')}{len(items_to_create)}"
                
                cs_item = CSItems(
                    cs_id=cs_query,
                    item_id=item_id,
                    item_name=item['item_required'],
                    quantity=item['quantity'],
                    unit_of_measurement=item['unit_of_measurement'],
                )
                items_to_create.append(cs_item)
            
            # Bulk create items
            created_items = CSItems.objects.bulk_create(items_to_create)
            
            # Create bids with references to created items
            for i, item in enumerate(items):
                bid = Bids(
                    cs_id=cs_query,
                    item_id=created_items[i],
                    sup_id=supplier,
                    unit_price=item.get('unit_price', 0),
                    vat=item.get('vat', 0),
                    quoted_qty=item.get('quantity', 0),
                    bid_no=bid_no,
                    quote_date=bid_date,
                    total=item.get('total_price', 0),
                    bid_document=bid_doc_path,
                )
                bids_to_create.append(bid)
            
            Bids.objects.bulk_create(bids_to_create)
            
            # Clear related caches
            cache.delete(f'cs_data_{cs_id}')
            cache.delete(f'cs_bids_{cs_id}')
            
            return JsonResponse({
                "message": "Bids saved successfully",
                "success": True,
            })
            
    except Exception as ex:
        print(f"Error saving bid: {ex}")
        return JsonResponse({
            "message": "Error saving bid",
            "error": str(ex),
            "success": False,
        }, status=500)


def _save_file_optimized(file, file_type):
    """Optimized file saving helper"""
    try:
        # Validate file
        if file.size > 10 * 1024 * 1024:  # 10MB limit
            return {"success": False, "error": "File too large"}
        
        allowed_extensions = ['.pdf', '.doc', '.docx', '.xls', '.xlsx', '.jpg', '.jpeg', '.png']
        file_extension = os.path.splitext(file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return {"success": False, "error": "File type not allowed"}
        
        # Create directory
        root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', file_type)
        os.makedirs(root_dir, exist_ok=True)
        
        # Generate unique filename
        timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
        filename = f"{timestamp}_{file.name}"
        
        # Save file
        fs = FileSystemStorage(location=root_dir)
        saved_filename = fs.save(filename, file)
        
        # Return relative path
        relative_path = os.path.join('uploads', 'comparative', file_type, saved_filename)
        
        return {
            "success": True,
            "file_path": relative_path,
            "filename": saved_filename
        }
        
    except Exception as ex:
        return {"success": False, "error": str(ex)}


# New focused API endpoints
@login_required
@require_http_methods(["GET"])
def api_get_pr_basic(request, pr_id):
    """Get basic PR information only"""
    if not pr_id.startswith("PR"):
        pr_id = "PR" + pr_id
        
    try:
        purchase_request = PurchaseRequest.objects.select_related(
            'procurement_plan_reference', 'section', 'cost_center', 'requested_by'
        ).get(id=pr_id)
    except PurchaseRequest.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "PR not found",
        })

    request_user = request.user
    request_user_profile = UserProfile.objects.select_related().get(id=request_user.id)
    user_comparative_schedule_role = request_user_profile.get_user_role_for_application(APP_NAME)
    
    return JsonResponse({
        "success": True,
        "requester_role": user_comparative_schedule_role.role if user_comparative_schedule_role else "",
        "message": "PR details retrieved successfully",
        "pr_id": pr_id,
        "scope_of_work": purchase_request.scope_of_work or "",
        "proc_ref": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
        "proc_plan": {
            "id": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
            "proc_ref": purchase_request.procurement_plan_reference.id if purchase_request.procurement_plan_reference else "",
            "description": purchase_request.procurement_plan_reference.name if purchase_request.procurement_plan_reference else "",
        } if purchase_request.procurement_plan_reference else {},
        "pr_date": purchase_request.created_at.strftime("%Y-%m-%d") if purchase_request.created_at else "",
    })


@login_required
@require_http_methods(["GET"])
def api_get_pr_items(request, pr_id):
    """Get PR items with pagination - shows all items with status"""
    if not pr_id.startswith("PR"):
        pr_id = "PR" + pr_id
        
    try:
        purchase_request = PurchaseRequest.objects.get(id=pr_id)
    except PurchaseRequest.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "PR not found",
        })

    # Get pagination parameters with safety limits (Stage 2 optimization)
    page = int(request.GET.get('page', 1))
    requested_page_size = int(request.GET.get('page_size', 0))
    show_all = request.GET.get('show_all', 'true').lower() == 'true'  # Show all items by default
    
    # Get total items count for safe page size calculation
    if show_all:
        pr_items_query = purchase_request.pritem_set.select_related('unit_of_measurement').all()
    else:
        pr_items_query = purchase_request.pritem_set.select_related('unit_of_measurement').filter(ordered=False)
    
    total_items = pr_items_query.count()
    
    # Apply safe page size limits
    page_size = get_safe_page_size(requested_page_size, 'pr_items', total_items)
    
    # Log warning if user requested too large page size
    if requested_page_size > page_size:
        logger.warning(f"User requested page_size {requested_page_size} reduced to {page_size} for memory protection")
    
    from django.core.paginator import Paginator
    
    # Use the already optimized query from above
    paginator = Paginator(pr_items_query, page_size)
    page_obj = paginator.get_page(page)
    
    pr_item_list = []
    for pr_item in page_obj:
        # Determine the status and availability
        status = "available"
        included = True
        
        if pr_item.ordered:
            status = "used_in_other_schedule"
            included = False  # Don't include by default if already used
        
        pr_item_list.append({
            "id": pr_item.id,
            "item_required": pr_item.item_required,
            "quantity": pr_item.quantity,
            "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
            "ordered": pr_item.ordered,
            "status": status,
            "included": included,  # Whether to include in this CS by default
        })

    # Get enhanced pagination info with warnings
    pagination_info = get_pagination_info(page, page_size, total_items)
    
    return JsonResponse({
        "success": True,
        "pr_items": pr_item_list,
        "pagination": pagination_info,
        "performance_info": {
            "requested_page_size": requested_page_size,
            "actual_page_size": page_size,
            "memory_optimized": requested_page_size != page_size,
            "total_items": total_items
        }
    })


@login_required
@require_http_methods(["GET"])
def api_get_pr_attachments(request, pr_id):
    """Get PR attachments - optimized version without Base64 encoding"""
    if not pr_id.startswith("PR"):
        pr_id = "PR" + pr_id
        
    try:
        purchase_request = PurchaseRequest.objects.prefetch_related('attachment_set').get(id=pr_id)
    except PurchaseRequest.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "PR not found",
        })

    # Use optimized file handling instead of Base64 encoding
    include_preview = request.GET.get('include_preview', 'false').lower() == 'true'
    pr_at_list = get_attachments_metadata_optimized(
        purchase_request.attachment_set.all(), 
        request.user, 
        include_preview
    )

    return JsonResponse({
        "success": True,
        "pr_attachments": pr_at_list,
        "total_count": len(pr_at_list)
    })


@login_required
@require_http_methods(["GET"])
def api_get_reference_data(request):
    """Get reference data (suppliers, currencies, etc.)"""
    try:
        # Get cached reference data
        proc_plans_cache_key = 'all_proc_plans'
        proc_plans = cache.get(proc_plans_cache_key)
        if proc_plans is None:
            proc_plans = list(ProcPlan.objects.values('id', 'proc_ref', 'description'))
            cache.set(proc_plans_cache_key, proc_plans, CACHE_TIMEOUT * 4)

        currencies_cache_key = 'all_currencies'
        currencies = cache.get(currencies_cache_key)
        if currencies is None:
            currencies = list(Currency.objects.values('id', 'currency'))
            cache.set(currencies_cache_key, currencies, CACHE_TIMEOUT * 4)

        suppliers_cache_key = 'all_suppliers'
        suppliers = cache.get(suppliers_cache_key)
        if suppliers is None:
            suppliers = list(Supplier.objects.values('id', 'name'))
            cache.set(suppliers_cache_key, suppliers, CACHE_TIMEOUT * 2)

        users_cache_key = 'all_users'
        users = cache.get(users_cache_key)
        if users is None:
            users = list(UserProfile.objects.values('id', 'username', 'first_name', 'last_name'))
            cache.set(users_cache_key, users, CACHE_TIMEOUT)

        uom_cache_key = 'all_uom'
        uom = cache.get(uom_cache_key)
        if uom is None:
            uom = list(UnitOfMeasurement.objects.values('unit', 'name'))
            cache.set(uom_cache_key, uom, CACHE_TIMEOUT * 4)

        return JsonResponse({
            "success": True,
            "proc_plans": proc_plans,
            "uom": uom,
            "currencies": currencies,
            "suppliers": suppliers,
            "users": users,
        })
    except Exception as ex:
        print(f"Error in api_get_reference_data: {ex}")
        return JsonResponse({
            "success": False,
            "error": str(ex)
        }, status=500)

@login_required 
@require_http_methods(["GET"])
def api_get_users(request):
    """API endpoint to get users for React app with server-side search support"""
    try:
        # Get search parameters
        search_query = request.GET.get('search', '').strip()
        limit = int(request.GET.get('limit', 100))  # Increased default limit
        offset = int(request.GET.get('offset', 0))  # For pagination
        include_inactive = request.GET.get('include_inactive', 'true').lower() == 'true'
        
        # Base query - include ALL users like the original API
        users_query = UserProfile.objects.all()
        
        # Optionally filter by active status (default: include all)
        if not include_inactive:
            users_query = users_query.filter(is_active=True)
        
        # Apply search filter if provided
        if search_query and len(search_query) >= 2:
            from django.db.models import Q
            users_query = users_query.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
        elif not search_query:
            # If no search query, still apply reasonable limit but higher than before
            users_query = users_query[:limit]
        
        # Apply pagination
        total_count = users_query.count()
        users = users_query[offset:offset + limit]
        
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'email': getattr(user, 'email', ''),
                'is_active': getattr(user, 'is_active', True),
            })
        
        return JsonResponse({
            'users': users_data,
            'total_count': total_count,
            'has_more': (offset + limit) < total_count,
            'search_query': search_query,
            'include_inactive': include_inactive
        }, safe=False)
    except Exception as ex:
        print("Error fetching users:", ex)
        return JsonResponse({'error': str(ex)}, status=500)

@login_required 
@require_http_methods(["GET"])
def api_get_suppliers(request):
    """API endpoint to get suppliers for React app"""
    try:
        search_query = request.GET.get('search', '').strip()
        limit = int(request.GET.get('limit', 100))
        
        suppliers = Supplier.objects.all()
        
        # Apply search filter if provided
        if search_query:
            suppliers = suppliers.filter(
                Q(name__icontains=search_query)
            )
        
        # Apply limit
        suppliers = suppliers[:limit]
        
        suppliers_data = []
        for supplier in suppliers:
            suppliers_data.append({
                'id': supplier.id,
                'name': supplier.name,
                'supplier_name': supplier.name,  # For compatibility
            })
        
        # Return in the format expected by the frontend
        return JsonResponse({
            'suppliers': suppliers_data,
            'count': len(suppliers_data)
        })
    except Exception as ex:
        print("Error fetching suppliers:", ex)
        return JsonResponse({'error': str(ex)}, status=500)

@login_required 
@require_http_methods(["GET"])
def api_get_currencies(request):
    """API endpoint to get currencies for React app"""
    try:
        currencies = Currency.objects.all()
        currencies_data = []
        for currency in currencies:
            currencies_data.append({
                'id': currency.id,
                'currency': currency.currency,
            })
        return JsonResponse(currencies_data, safe=False)
    except Exception as ex:
        print("Error fetching currencies:", ex)
        return JsonResponse({'error': str(ex)}, status=500)

@login_required 
@require_http_methods(["GET"])
def api_get_proc_plans(request):
    """API endpoint to get procurement plans for React app"""
    try:
        proc_plans = ProcPlan.objects.all()
        proc_plans_data = []
        for proc_plan in proc_plans:
            proc_plans_data.append({
                'id': proc_plan.id,
                'proc_ref': proc_plan.proc_ref,
                'description': proc_plan.description,
            })
        return JsonResponse(proc_plans_data, safe=False)
    except Exception as ex:
        print("Error fetching procurement plans:", ex)
        return JsonResponse({'error': str(ex)}, status=500)

@login_required
@require_http_methods(["GET"])
def api_get_cs_bids_optimized(request, cs_id):
    """Get bids data for a specific CS - optimized with proper file handling"""
    try:
        cs = ComparativeSchedules.objects.prefetch_related(
            Prefetch('bids_set', queryset=Bids.objects.select_related('sup_id', 'item_id'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        # Build grouped bids data efficiently
        bids = list(cs.bids_set.all())
        grouped_data = {}
        
        for bid in bids:
            bid_no = bid.bid_no
            if bid_no not in grouped_data:
                # Use optimized file handling instead of Base64 encoding
                bid_document_info = None
                if bid.bid_document:
                    # Check if file exists and provide metadata
                    file_path = bid.bid_document
                    if file_path.startswith('uploads/'):
                        # File is stored in root directory (BASE_DIR)
                        full_path = os.path.join(settings.BASE_DIR, file_path)
                    else:
                        # File is stored with absolute path
                        full_path = file_path
                    
                    if os.path.exists(full_path):
                        try:
                            file_size = os.path.getsize(full_path)
                            filename = os.path.basename(file_path)
                            
                            bid_document_info = {
                                'file_path': file_path,
                                'filename': filename,
                                'size': file_size,
                                'download_url': f"/uploads/{file_path.replace('uploads/', '')}",
                                'preview_url': f"/api/files/preview/{file_path}/"
                            }
                        except Exception as ex:
                            print(f"Error getting file info for {file_path}: {ex}")
                            bid_document_info = {
                                'file_path': file_path,
                                'filename': os.path.basename(file_path),
                                'size': 0,
                                'download_url': f"/uploads/{file_path.replace('uploads/', '')}",
                                'preview_url': f"/api/files/preview/{file_path}/"
                            }
                    else:
                        # File not found, but provide path for debugging
                        bid_document_info = {
                            'file_path': file_path,
                            'filename': os.path.basename(file_path),
                            'size': 0,
                            'download_url': f"/media/{file_path}",
                            'preview_url': f"/api/files/preview/{file_path}/",
                            'error': 'File not found'
                        }
                
                grouped_data[bid_no] = {
                    'bid_count': bid.bid_no,
                    'supplier_name': bid.sup_id.name,
                    'bid_date': bid.quote_date,
                    'bid_document_info': bid_document_info,
                    'items': []
                }
            
            grouped_data[bid_no]['items'].append({
                'item_id': bid.item_id.item_id,
                'item_required': bid.item_id.item_name,
                'quantity': bid.item_id.quantity,
                'unit_of_measurement': bid.item_id.unit_of_measurement,
                'unit_price': bid.unit_price,
                'vat': bid.vat,
                'total_price': bid.total,
            })
        
        return JsonResponse({
            "success": True,
            "bids": list(grouped_data.values())
        })
        
    except Exception as ex:
        return JsonResponse({
            "success": False,
            "message": f"Error loading bids: {str(ex)}"
        })


@login_required
@require_http_methods(["GET"])
def api_get_cs_compliance_optimized(request, cs_id):
    """Get compliance data for a specific CS - optimized"""
    try:
        cs = ComparativeSchedules.objects.prefetch_related(
            Prefetch('cscompliance_set', queryset=CSCompliance.objects.select_related('supplier_id')),
            Prefetch('cscomplianceremarks_set', queryset=CSComplianceRemarks.objects.select_related('supplier_id'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        compliance = list(cs.cscompliance_set.all())
        compliance_remarks = list(cs.cscomplianceremarks_set.all())
        
        # Build compliance list
        compliance_list = [
            {
                "supplier_name": comp.supplier_id.name if comp.supplier_id else "",
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
            } for comp in compliance if comp.supplier_id
        ]
        
        compliance_remarks_list = [
            {
                "supplier": remark.supplier_id.id,
                "supplier_name": remark.supplier_id.name,
                "remarks": remark.remarks,
            } for remark in compliance_remarks if remark.supplier_id
        ]
        
        return JsonResponse({
            "success": True,
            "compliance": compliance_list,
            "complianceRemarks": compliance_remarks_list
        })
        
    except Exception as ex:
        return JsonResponse({
            "success": False,
            "message": f"Error loading compliance: {str(ex)}"
        })


@login_required
@require_http_methods(["GET"])
def api_get_cs_committee_optimized(request, cs_id):
    """Get committee data for a specific CS - optimized"""
    try:
        cs = ComparativeSchedules.objects.prefetch_related(
            Prefetch('committee_set', queryset=Committee.objects.select_related('user'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        committee = list(cs.committee_set.all())
        
        committee_list = [
            {
                "memberUserName": member.user.username if member.user else "",
                "memberName": f"{member.user.first_name} {member.user.last_name}" if member.user else "",
                "memberPosition": member.committee_position,
                "committeeStatus": member.committee_status,
                "memberApproval": member.committee_approval if member.committee_approval else "",
                "committeeJustification": member.justification,
                "committeeDate": member.committee_date,
            } for member in committee if member.user
        ]
        
        return JsonResponse({
            "success": True,
            "committee": committee_list
        })
        
    except Exception as ex:
        return JsonResponse({
            "success": False,
            "message": f"Error loading committee: {str(ex)}"
        })


@login_required
@require_http_methods(["GET"])
def api_get_cs_approvals_optimized(request, cs_id):
    """Get approval data for a specific CS - optimized"""
    try:
        cs = ComparativeSchedules.objects.prefetch_related(
            Prefetch('csapproval_set', queryset=CSApproval.objects.select_related('user')),
            Prefetch('ranking_set', queryset=Ranking.objects.select_related('supplier_id'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        approvals = {approval.approver_role: approval for approval in cs.csapproval_set.all()}
        rankings = list(cs.ranking_set.all())
        
        # Build approval data
        gm_approval = approvals.get("general_manager")
        fm_approval = approvals.get("finance_manager")
        
        # Get current user's roles for comparative_schedule application
        current_user = request.user
        fm_role, gm_role, procurement_role = getUserFMGMRoles(current_user)
        
        # Debug logging
        print(f"🔍 API Debug - User: {current_user.username}, CS: {cs_id}")
        print(f"🔍 API Debug - Roles: FM={fm_role}, GM={gm_role}, Procurement={procurement_role}")
        
        # Additional debugging for the response
        current_user_roles = {
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role
        }
        print(f"🔍 API Debug - current_user_roles dict: {current_user_roles}")
        print(f"🔍 API Debug - fm_role type: {type(fm_role)}, value: {fm_role}")
        
        rankings_list = [
            {
                "supplier_name": rank.supplier_id.name if rank.supplier_id else "",
                "rank": rank.rank,
                "remarks": rank.remarks,
                "decision": rank.decision,
                "total": rank.total,
                "created_at": rank.created_at,
            } for rank in rankings
        ]
        
        response_data = {
            "success": True,
            "gm_approval": {
                "id": gm_approval.id,
                "approver": gm_approval.user.username if gm_approval.user else "",
                "approver_name": f"{gm_approval.user.first_name} {gm_approval.user.last_name}" if gm_approval.user else "",
                "approver_role": gm_approval.approver_role,
                "approval": gm_approval.approval,
                "justification": gm_approval.justification,
                "approval_date": gm_approval.approval_date,
            } if gm_approval else {},
            "fm_approval": {
                "id": fm_approval.id,
                "approver": fm_approval.user.username if fm_approval.user else "",
                "approver_name": f"{fm_approval.user.first_name} {fm_approval.user.last_name}" if fm_approval.user else "",
                "approver_role": fm_approval.approver_role,
                "approval": fm_approval.approval,
                "justification": fm_approval.justification,
                "approval_date": fm_approval.approval_date,
            } if fm_approval else {},
            "rankings": rankings_list,
            "current_user_roles": current_user_roles
        }
        
        print(f"🔍 API Debug - Response current_user_roles: {response_data['current_user_roles']}")
        
        return JsonResponse(response_data)
        
    except Exception as ex:
        return JsonResponse({
            "success": False,
            "message": f"Error loading approvals: {str(ex)}"
        })


@login_required
@require_http_methods(["GET"])
def api_get_cs_rankings_optimized(request, cs_id):
    """Get rankings data for a specific CS - optimized"""
    try:
        cs = ComparativeSchedules.objects.prefetch_related(
            Prefetch('ranking_set', queryset=Ranking.objects.select_related('supplier_id'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        rankings = list(cs.ranking_set.all())
        
        rankings_list = [
            {
                "supplier_name": rank.supplier_id.name if rank.supplier_id else "",
                "rank": rank.rank,
                "remarks": rank.remarks,
                "decision": rank.decision,
                "total": rank.total,
                "created_at": rank.created_at,
            } for rank in rankings
        ]
        
        return JsonResponse({
            "success": True,
            "rankings": rankings_list
        })
        
    except Exception as ex:
        return JsonResponse({
            "success": False,
            "message": f"Error loading rankings: {str(ex)}"
        })


@login_required
@require_http_methods(["GET"])
def api_get_cs_pr_items_management(request, cs_id):
    """Get PR items data for management tab - only accessible after CS details are saved"""
    cache_key = f'cs_pr_items_{cs_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return JsonResponse(cached_data, safe=False)
    
    try:
        # Get CS with related data
        cs = ComparativeSchedules.objects.select_related(
            'created_by', 'region', 'section', 'currency', 'proc_plan'
        ).prefetch_related(
            Prefetch('csrequireditems_set', queryset=CSRequiredItems.objects.all())
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({
                "success": False,
                "message": "Comparative Schedule not found"
            }, status=404)
        
        # Check if CS details have been saved (required for PR items tab access)
        if not cs.cs_id:
            return JsonResponse({
                "success": False,
                "message": "CS details must be saved before managing PR items"
            }, status=400)
        
        # Get PR data
        pr = None
        pr_items_list = []
        pr_attachments_list = []
        
        if cs.pr_id_id:
            pr = PurchaseRequest.objects.select_related().prefetch_related(
                Prefetch('pritem_set', 
                        queryset=PrItem.objects.select_related('unit_of_measurement')),
                Prefetch('attachment_set', 
                        queryset=Attachment.objects.all())
            ).filter(id=cs.pr_id_id).first()
            
            if pr:
                # Get existing CS items (already ordered)
                cs_items = list(cs.csrequireditems_set.all())
                
                # Add CS items first (already selected for this CS)
                pr_items_list.extend([
                    {
                        "id": cs_item.id,
                        "item_required": cs_item.item_name,
                        "quantity": cs_item.quantity,
                        "unit_of_measurement": cs_item.unit_of_measurement,
                        "ordered": True,
                        "status": "selected_for_this_cs",
                        "included": True,
                        "source": "cs_required_items"
                    } for cs_item in cs_items
                ])
                
                # Add available PR items (not ordered or not in any CS)
                available_items = pr.pritem_set.filter(ordered=False)
                pr_items_list.extend([
                    {
                        "id": pr_item.id,
                        "item_required": pr_item.item_required,
                        "quantity": pr_item.quantity,
                        "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
                        "ordered": pr_item.ordered,
                        "status": "available",
                        "included": False,
                        "source": "pr_items"
                    } for pr_item in available_items
                ])
                
                # Add items used in other CSs (for reference)
                used_items = pr.pritem_set.filter(ordered=True).exclude(
                    id__in=[cs_item.item_id for cs_item in cs_items if cs_item.item_id]
                )
                pr_items_list.extend([
                    {
                        "id": pr_item.id,
                        "item_required": pr_item.item_required,
                        "quantity": pr_item.quantity,
                        "unit_of_measurement": pr_item.unit_of_measurement.name if pr_item.unit_of_measurement else "",
                        "ordered": pr_item.ordered,
                        "status": "used_in_other_schedule",
                        "included": False,
                        "source": "pr_items"
                    } for pr_item in used_items
                ])
                
                # Process attachments
                for attachment in pr.attachment_set.all():
                    if attachment.file:
                        try:
                            if os.path.exists(attachment.file.path) and attachment.file.size < 5 * 1024 * 1024:  # 5MB limit
                                file_data = attachment.file.read()
                                encoded_file_data = base64.b64encode(file_data).decode('utf-8')
                                pr_attachments_list.append({
                                    "id": attachment.id,
                                    "file": encoded_file_data,
                                    "name": os.path.basename(attachment.file.name),
                                })
                        except Exception as ex:
                            print(f"Error processing attachment {attachment.id}: {ex}")
                            continue

        # Get unit of measurement options
        uom_cache_key = 'all_uom'
        uom = cache.get(uom_cache_key)
        if uom is None:
            uom = list(UnitOfMeasurement.objects.values('unit', 'name'))
            cache.set(uom_cache_key, uom, CACHE_TIMEOUT * 4)

        result_data = {
            "success": True,
            "cs_id": cs.cs_id,
            "pr_id": pr.id if pr else None,
            "pr_number": cs.pr_number,
            "scope_of_work": pr.scope_of_work if pr else cs.scope_of_work,
            "pr_items": pr_items_list,
            "pr_attachments": pr_attachments_list,
            "uom": uom,
            "can_modify": True,  # Add logic here based on user permissions and CS status
            "total_items": len(pr_items_list),
            "selected_items": len([item for item in pr_items_list if item['status'] == 'selected_for_this_cs']),
            "available_items": len([item for item in pr_items_list if item['status'] == 'available']),
        }
        
        # Cache for 5 minutes
        cache.set(cache_key, result_data, CACHE_TIMEOUT)
        
        return JsonResponse(result_data, safe=False)
        
    except Exception as ex:
        print(f"Error loading PR items management data: {ex}")
        return JsonResponse({
            "success": False,
            "message": f"Error loading PR items data: {str(ex)}"
        }, status=500)


@login_required
@require_http_methods(["POST"])
def api_update_cs_pr_items(request, cs_id):
    """Update CS PR items - optimized version for separate tab"""
    from django.db import transaction
    
    try:
        cs_query = ComparativeSchedules.objects.filter(cs_id=cs_id).first()
        if not cs_query:
            return JsonResponse({
                "success": False,
                "message": f"Comparative Schedule with ID {cs_id} not found"
            }, status=404)

        # Parse the data
        try:
            json_data = json.loads(request.body)
            items = json_data.get("cs_items", [])
            pr_id = json_data.get("pr_id")
        except json.JSONDecodeError:
            return JsonResponse({
                "success": False,
                "message": "Invalid JSON data"
            }, status=400)
        
        if not pr_id:
            return JsonResponse({
                "success": False,
                "message": "PR ID is required"
            }, status=400)

        purchase_request = PurchaseRequest.objects.filter(id=pr_id).first()
        if not purchase_request:
            return JsonResponse({
                "success": False,
                "message": f"Purchase Request with ID {pr_id} not found"
            }, status=404)
            
        with transaction.atomic():
            # Get existing CS items to compare
            existing_items = CSRequiredItems.objects.filter(cs_id=cs_query).all()
            existing_items_map = {item.item_name: item for item in existing_items}
            
            # Get items that should be included (from frontend selection)
            items_to_include = {item['item_required'] for item in items if item.get('included', False)}
            
            # Items to add (in items_to_include but not in existing)
            items_to_add = []
            for item in items:
                if item.get('included', False) and item['item_required'] not in existing_items_map:
                    items_to_add.append(item)
            
            # Items to remove (in existing but not in items_to_include)
            items_to_remove = []
            for item_name, cs_item in existing_items_map.items():
                if item_name not in items_to_include:
                    items_to_remove.append(cs_item)

            # Add new items
            for item in items_to_add:
                pr_item = PrItem.objects.filter(
                    item_required=item['item_required'],
                    purchase_request=purchase_request
                ).first()
                
                if pr_item:
                    pr_item.ordered = True
                    pr_item.save()
                    
                    cs_required_items = CSRequiredItems(
                        cs_id=cs_query,
                        item_id=item.get('id'),
                        item_name=item['item_required'],
                        quantity=item['quantity'],
                        unit_of_measurement=item['unit_of_measurement'],
                    )
                    cs_required_items.save()

            # Remove items
            for cs_item in items_to_remove:
                pr_item = PrItem.objects.filter(
                    item_required=cs_item.item_name, 
                    purchase_request=purchase_request
                ).first()
                
                if pr_item:
                    pr_item.ordered = False
                    pr_item.save()
                
                cs_item.delete()

            # Clear approvals if items were modified
            if items_to_add or items_to_remove:
                clear_approvals(cs_id)
                
                # Clear related caches
                cache.delete(f'cs_data_{cs_id}')
                cache.delete(f'cs_pr_items_{cs_id}')

            return JsonResponse({
                "message": "PR Items updated successfully",
                "success": True,
                "stats": {
                    "added_items": len(items_to_add),
                    "removed_items": len(items_to_remove),
                    "total_selected": len(items_to_include)
                }
            })
            
    except Exception as ex:
        print(f"Error updating CS PR items: {ex}")
        return JsonResponse({
            "message": f"Error updating PR items: {str(ex)}",
            "success": False,
        }, status=500)

@login_required 
@require_http_methods(["GET"])
def api_get_users_with_roles(request):
    """API endpoint to get users with their roles for approval table"""
    try:
        users = UserProfile.objects.prefetch_related('roles').all()
        users_data = []
        
        for user in users:
            # Get user's roles for comparative_schedule application
            user_roles = []
            for role in user.roles.all():
                if role.application == 'comparative_schedule':
                    user_roles.append({
                        'role': role.role,
                        'name': role.name,
                        'description': role.description
                    })
            
            users_data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'name': f"{user.first_name} {user.last_name}".strip(),
                'roles': user_roles,
                'region': user.region.name if user.region else None,
                'section': user.section.name if user.section else None
            })
        
        return JsonResponse(users_data, safe=False)
    except Exception as ex:
        print("Error fetching users with roles:", ex)
        return JsonResponse({'error': str(ex)}, status=500)

@login_required 
@require_http_methods(["GET"])
def api_get_uom(request):
    """API endpoint to get UOM for React app with server-side search support"""
    try:
        # Get search parameters
        search_query = request.GET.get('search', '').strip()
        limit = int(request.GET.get('limit', 100))  # Default limit
        offset = int(request.GET.get('offset', 0))  # For pagination
        
        # Base query
        uom_query = UnitOfMeasurement.objects.all()
        
        # Apply search filter if provided
        if search_query and len(search_query) >= 2:
            from django.db.models import Q
            uom_query = uom_query.filter(
                Q(name__icontains=search_query) |
                Q(unit__icontains=search_query)
            )
        elif not search_query:
            # If no search query, apply reasonable limit
            uom_query = uom_query[:limit]
        
        # Apply pagination
        total_count = uom_query.count()
        uom_list = uom_query[offset:offset + limit]
        
        uom_data = []
        for uom_item in uom_list:
            uom_data.append({
                'id': uom_item.unit,  # Use unit as ID for consistency
                'unit': uom_item.unit,
                'name': uom_item.name,
            })
        
        return JsonResponse({
            'uom': uom_data,
            'total_count': total_count,
            'has_more': (offset + limit) < total_count,
            'search_query': search_query
        }, safe=False)
    except Exception as ex:
        print("Error fetching UOM:", ex)
        return JsonResponse({'error': str(ex)}, status=500)
