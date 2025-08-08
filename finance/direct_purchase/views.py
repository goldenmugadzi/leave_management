import base64
import copy
import csv
import os
from django.http import HttpResponse, JsonResponse
from django.shortcuts import redirect, render
import json
from datetime import datetime
from django.db.models import Sum, Q, Exists, OuterRef, Count, F, Prefetch
from django.core.files.storage import FileSystemStorage
from django.conf import settings
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger
from django.views.decorators.http import require_http_methods
from django.db import transaction

# Add proper logging
import logging
logger = logging.getLogger(__name__)

# Memory monitoring for performance optimization
import psutil
import os

# Import pagination config for Stage 2 optimization
from .pagination_config import get_safe_page_size, get_pagination_info, DATATABLE_MAX_SIZE, DATATABLE_DEFAULT_SIZE

from finance.comparative_schedules.models import Currency, ProcPlan
from finance.comparative_schedules.views import notification_update, notify_user
from .models import *
from it.users.models import *
from finance.purchase_request.models import PurchaseRequest, PrItem, Attachment, UnitOfMeasurement
from ACE2.models import Ace2
from finance.direct_purchase.models import *
import pandas as pd
from django.utils.timezone import now
from django.contrib.auth.decorators import login_required

from django.utils import timezone
from django.contrib import messages
APP_NAME = "direct_purchases"

# Cache timeout in seconds (5 minutes)
CACHE_TIMEOUT = 300

# Enhanced file handling function
def _save_file_optimized(uploaded_file, file_type='bid'):
    """Optimized file upload with validation and error handling"""
    try:
        # File size validation (10MB limit)
        if uploaded_file.size > 10 * 1024 * 1024:
            return {
                'success': False,
                'message': 'File too large. Maximum size is 10MB.',
                'file_path': None
            }
        
        # File type validation
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.zip', '.rar']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return {
                'success': False,
                'message': f'File type {file_extension} not allowed.',
                'file_path': None
            }
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{file_type}_{timestamp}_{uploaded_file.name}"
        
        # Save file
        fs = FileSystemStorage()
        file_path = fs.save(filename, uploaded_file)
        
        return {
            'success': True,
            'message': 'File uploaded successfully.',
            'file_path': file_path,
            'original_name': uploaded_file.name,
            'size': uploaded_file.size
        }
        
    except Exception as ex:
        logger.error(f"File upload error: {str(ex)}")
        return {
            'success': False,
            'message': f'File upload failed: {str(ex)}',
            'file_path': None
        }

# Enhanced bulk operations helper
def _bulk_create_items(cs_query, items_data):
    """Bulk create CS items with optimized performance"""
    items_to_create = []
    
    for item_data in items_data:
        item_id = f"Item{datetime.now().strftime('%Y%m%d%H%M%S')}{len(items_to_create)}"
        
        dp_item = DPItems(
            cs_id=cs_query,
            item_id=item_id,
            item_name=item_data.get('item_required', ''),
            quantity=item_data.get('quantity', 0),
            unit_of_measurement=item_data.get('unit_of_measurement', ''),
        )
        items_to_create.append(dp_item)
    
    # Bulk create for better performance
    created_items = DPItems.objects.bulk_create(items_to_create)
    return created_items

# Enhanced bulk bid operations
def _bulk_create_bids(cs_query, supplier, bid_no, items, bid_doc_path=""):
    """Bulk create bids with optimized performance"""
    bids_to_create = []
    
    for item in items:
        bid = DPBids(
            cs_id=cs_query,
            sup_id=supplier,
            bid_no=bid_no,
            item_id=item,
            unit_price=item.get('unit_price', 0),
            vat=item.get('vat', 0),
            total=item.get('total_price', 0),
            quote_date=datetime.now(),
            bid_document=bid_doc_path
        )
        bids_to_create.append(bid)
    
    # Bulk create for better performance
    created_bids = DPBids.objects.bulk_create(bids_to_create)
    return created_bids

def import_old_dp(request):
    
    dp = pd.read_csv('direct_purchases.csv')
    dp_update = pd.read_csv('direct_purchases_update.csv')

    # # save comperative schedules
    # cs_df = pd.DataFrame(columns=['document_id', 'pr_number', 'status', 'message'])
    # try:
    #     # initialize dataframe that records all failied and successfull comperative schedules
    #     for index, dp_row in dp.iterrows():
    #         adjid = dp_row['adjid']
    #         section_code = dp_row['section_code']
    #         pr_number = dp_row['pr_number']
    #         print("pr_number: ", pr_number)
    #         if pr_number:
    #             pr = PurchaseRequest.objects.filter(pr_no=pr_number).first()

    #             _proc_plan = dp_row['proc_ref']
    #             proc_plan = DPProcPlan.objects.filter(proc_ref=_proc_plan).first()
    #             dp_update_data = dp_update[dp_update['adjid'] == adjid]
    #             if not dp_update_data.empty:
    #                 dp_update_row = dp_update_data.iloc[0]
    #             else:
    #                 dp_update_row = None
    #             if dp_update_row is not None:
    #                 created_by = UserProfile.objects.filter(username=dp_update_row['update_user3']).first()
    #                 if created_by == None: 
    #                     created_by = UserProfile.objects.filter(username='ze123').first()
    #                 print("dp_row: ", dp_row['region'])
    #                 region = None
    #                 if dp_row['region']:
    #                     region_name = str(dp_row['region']).upper()
    #                     region = Regions.objects.filter(region=region_name).first()
    #                 else:
    #                     region = Regions.objects.filter(id=1).first()
                    
    #                 cost_center = CostCenter.objects.filter(Q(id=section_code) | Q(id="CC"+str(section_code))).first()
    #                 try:
    #                     currency = Currency.objects.filter(currency='ZWL').first()
    #                     dc = timezone.make_aware(datetime.strptime(dp_row['date_created'], "%Y-%m-%d %H:%M:%S")) if (dp_row['date_created'] != '0000-00-00 00:00:00' or dp_row['date_created'] != "") else None
    #                     cs_query = DirectPurchase(
    #                         cs_id = adjid,
    #                         pr_id = pr,
    #                         proc_plan = proc_plan,
    #                         scope_of_work = dp_row['description'],
    #                         currency = currency,
    #                         advert = dp_row['specifications'],
    #                         pr_number = pr_number,
    #                         created_by = created_by,
    #                         cost_center = cost_center,
    #                         region = region,
    #                         created_at = dc,
    #                     )
    #                     cs_query.save()
    #                     cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [adjid], 'pr_number': [pr_number], 'status': ['Success'], 'message': ['Success']})], ignore_index=True)
    #                 except Exception as ex:
    #                     print("Error: ", ex)
    #                     cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [adjid], 'pr_number': [pr_number], 'status': ['Failed'], 'message': [ex]})], ignore_index=True)
    #             else:
    #                 cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [adjid], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['PR Object not found']})], ignore_index=True)
    #         else:
    #             cs_df = pd.concat([cs_df, pd.DataFrame({'document_id': [adjid], 'pr_number': [pr_number], 'status': ['Failed'], 'message': ['PR Number not found']})], ignore_index=True)
    #     cs_df.to_csv('dp_df.csv')
    #     print("cs_df: ", cs_df)
    
    # except Exception as ex:
    #     print("Error: ", ex)
        
    # # save bids
    # try:
    #     item_df = pd.DataFrame(columns=['document_id', 'item_id', 'sup_id', 'status', 'message'])
    #     for index, row in dp.iterrows():
    #         adjid = row['adjid']
    #         item1 = row['item1']
    #         quantity1 = row['quantity1']
    #         item1_unitprice = row['item1_unitprice']
    #         item1_total = row['item1_total']
    #         description = row['description']
    #         specifications = row['specifications']
    #         award1 = row['award1']
    #         pr_number = row['pr_number']
    #         date_created = row['date_created']
    #         section_code = row['section_code']
    #         remarks = row['remarks']
    #         service_type = row['service_type']
    #         proc_ref = row['proc_ref']
    #         region = row['region']
    #         print("adjid: ", adjid)
    #         cs_query = DirectPurchase.objects.filter(cs_id=adjid).first()
    #         print("cs_query: ", cs_query)
    #         item_id = "Item" + str(datetime.now().strftime("%Y%m%d%I%M%S%p"))
    #         if cs_query:
    #             item_query = DPItems(
    #                 cs_id = cs_query,
    #                 item_id = item_id,
    #                 item_name = item1,
    #                 quantity = quantity1,
    #                 unit_of_measurement = "",
    #             )
    #             item_query.save()    

    #             for i in range(1,3):
    #                 supplier_quotation_date = row['supplier'+ str(i) +'_quotation_date']
    #                 supplier_quotation = row['supplier'+ str(i) +'_quotation']
    #                 supplier_name = row['supplier'+ str(i)]
    #                 direct_purchase_quote = row['direct_purchase'+ str(i)]

    #                 supplier = None
    #                 if supplier_name and supplier_name != "None" and supplier_name != "nan" and supplier_name != "N/A":
    #                     supplier, created = Supplier.objects.get_or_create(name=supplier_name)
    #                 else:
    #                     item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_query.cs_id], 'item_id': [item1], 'sup_id': [supplier_name], 'status': ['FAILED'], 'message': ['Supplier Not Found']})], ignore_index=True)
    #                 quote_dc = timezone.now()
    #                 if supplier_quotation_date != '0000-00-00':
    #                     quote_dc = timezone.make_aware(datetime.strptime(supplier_quotation_date, "%Y-%m-%d")) if (date_created != '0000-00-00 00:00:00' or date_created != "") else None
    #                 if supplier:
    #                     # print("bid_no", supplier)
    #                     bid = DPBids(
    #                         cs_id = cs_query,
    #                         item_id = item_query,
    #                         sup_id = supplier,
    #                         unit_price = item1_unitprice,
    #                         vat = "",
    #                         quoted_qty = quantity1,
    #                         bid_no = "1",
    #                         quote_date = quote_dc,
    #                         total = item1_total,
    #                         bid_document = direct_purchase_quote,
    #                     )
    #                     bid.save()
    #                     item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_query.cs_id], 'item_id': [""], 'sup_id': [""], 'status': ['SUCCESS'], 'message': ['SUCCESS']})], ignore_index=True)
    #                 else:
    #                     item_df = pd.concat([item_df, pd.DataFrame({'document_id': [cs_query.cs_id], 'item_id': [""], 'sup_id': [""], 'status': ['FAILED'], 'message': ['DB Supplier Not Found']})], ignore_index=True)
                                    
    #         else:
    #             item_df = pd.concat([item_df, pd.DataFrame({'document_id': [""], 'item_id': [""], 'sup_id': [""], 'status': ['FAILED'], 'message': ['Schedule Not Found']})], ignore_index=True)
    # except Exception as ex:
    #     print("Error: ", ex)          
    
    # item_df.to_csv('dp_item_df.csv')
    
    # save bid update
    other_df = pd.DataFrame(columns=['document_id', 'sup_id', 'model', 'status', 'message'])
    try:
        for index, row in dp_update.iterrows():
            cs_id = row['adjid']
            cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
            if cs_query:
                
                # save ranking
                try:
                    for i in range(1, 6):
                        rank_supplier = row[f'ranking{i}'] if f'ranking{i}' in row else ""
                        if rank_supplier and rank_supplier != "None" and rank_supplier != "nan" and rank_supplier != "N/A":
                            supplier = Supplier.objects.filter(name=rank_supplier).first()
                            
                            bids = DPBids.objects.filter(cs_id=cs_query).values('sup_id').annotate(total_sum=Sum('total')).order_by('total_sum')
                            
                            for bid in bids:
                                decision = "Awarded " + bid.sup_id.name + " being the lowest bidder having complied with all the requirements is recommended to provide the goods/service at a total cost of " + cs_query.currency.currency + " " + str(total) + " excluding VAT."

                                ranking_query = DPRanking(
                                    cs_id = cs_query,
                                    supplier_id = supplier,
                                    rank = bid.bid_no,
                                    remarks = "",
                                    decision = decision,
                                    total = bid.total,
                                )
                                ranking_query.save()
                                print("ranking_query: ", ranking_query)
                        else:
                            print("Ranking Supplier not found")
                    
                except Exception as ex:
                    print("Error: ", ex)        
                # save committee
                for i in range(1,3):
                    username = row[f'update_user{i}'] if f'update_user{i}' in row else None
                    status = row[f'status{i}'] if f'status{i}' in row else None
                    approved_at = row[f'update_date{i}'] if f'update_date{i}' in row else None
                    position = ""
                    if i == 1:
                        position = "Chairman"
                    elif i == 2:
                        position = 'Finance'
                    elif i == 3:
                        position = 'Procurement'
                    elif i == 4:
                        position = 'User'
                    else:
                        position = 'Other'
                        
                    if status == 1 and i == 1:
                        status = "Approved"
                    elif status == 2 and i == 2:
                        status = "Approved"
                    elif status == 3 and i == 3:
                        status = "Approved"
                    elif status == 0:
                        status = ""
                    else:
                        status = "Rejected"
                    
                    # check if committee exists
                    if username:
                        # check if member exists
                        # get member user profile
                        member_profile = UserProfile.objects.filter(username=username).first()
                        if member_profile:
                            committee_query = DPCommittee(
                                cs_id = cs_query,
                                user = member_profile,
                                committee_name = username,
                                committee_position = position,
                                committee_approval = status,
                                committee_date = timezone.make_aware(datetime.strptime(approved_at, "%Y-%m-%d %H:%M:%S")) if approved_at != '0000-00-00 00:00:00' else None
                            )
                            committee_query.save()
                            other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [username], 'model': ["Committee"], 'status': ['Success'], 'message': ['SUCCESS']})], ignore_index=True)
                        else:
                            other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [username], 'model': ["Committee"], 'status': ['Failed'], 'message': ['member profile empty']})], ignore_index=True)
                    else:
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [""], 'model': ["Committee"], 'status': ['Failed'], 'message': ['username empty']})], ignore_index=True) 
                
                finance_user = row['update_user4']
                finance_date = row['update_date4']
                finance_status = row['status4']
      
                if finance_status == 4:
                    finance_status = "Approved"
                elif finance_status == 0:
                    finance_status = ""
                else:
                    finance_status = "Rejected"
                
                if finance_user:
                    finance_profile = UserProfile.objects.filter(username=finance_user).first()
                    if finance_profile:
                        finance_query = DPApproval(
                            cs_id = cs_query,
                            user = finance_profile,
                            approver_role = "finance_manager",
                            approval = finance_status,
                            justification = "",
                            approval_date = timezone.make_aware(datetime.strptime(finance_date, "%Y-%m-%d %H:%M:%S")) if finance_date != '0000-00-00 00:00:00' else None,
                        )
                        finance_query.save()
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["DPApproval"], 'status': ['Success'], 'message': ['SUCCESS']})], ignore_index=True)
                    else:
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["DPApproval"], 'status': ['Failed'], 'message': ['DB finance_user empty']})], ignore_index=True)
                else:
                    other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [finance_user], 'model': ["DPApproval"], 'status': ['Failed'], 'message': ['finance_user empty']})], ignore_index=True)
                
                gm_user = row['update_user4']
                gm_date = row['update_date4']
                gm_status = row['status4']
      
                if gm_status == 5:
                    gm_status = "Approved"
                elif gm_status == 0:
                    gm_status = ""
                else:
                    gm_status = "Rejected"
                
                if gm_user:
                    gm_profile = UserProfile.objects.filter(username=gm_user).first()
                    if gm_profile:
                        gm_query = DPApproval(
                            cs_id = cs_query,
                            user = gm_profile,
                            approver_role = "general_manager",
                            approval = gm_status,
                            justification = "",
                            approval_date = timezone.make_aware(datetime.strptime(gm_date, "%Y-%m-%d %H:%M:%S")) if gm_date != '0000-00-00 00:00:00' else None,
                        )
                        gm_query.save()
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["DPApproval"], 'status': ['Success'], 'message': ['SUCCESS GM']})], ignore_index=True)
                    else:
                        other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["DPApproval"], 'status': ['Failed'], 'message': ['GM DB finance_user empty']})], ignore_index=True)
                else:
                    other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [gm_user], 'model': ["DPApproval"], 'status': ['Failed'], 'message': ['GM finance_user empty']})], ignore_index=True)
            else:
                print("cs not found")
                other_df = pd.concat([other_df, pd.DataFrame({'document_id': [cs_id], 'sup_id': [""], 'model': ["Direct Purchase"], 'status': ['Failed'], 'message': ['Schedule not found']})], ignore_index=True)

    except Exception as ex:
        print("Error: ", ex)   
    
    other_df.to_csv('dp_other_df.csv')    
      
    return JsonResponse({
        "success": True,
        "message": "Data imported successfully",
        # "data": other_df.to_json()
        # "data": cs_df.to_json()
        # "data": item_df.to_json()
        }, safe=False)

@transaction.atomic
def clear_approvals(cs_id):
    """Enhanced clear approvals function with transaction management"""
    try:
        cs_query = DirectPurchase.objects.select_for_update().get(cs_id=cs_id)
    except DirectPurchase.DoesNotExist:
        logger.warning(f"Direct Purchase {cs_id} not found for clearing approvals")
        return JsonResponse({
            "message": "Direct Purchase Schedule not found",
            "success": False,
        }, safe=False)

    try:
        # Use bulk update for better performance with transaction safety
        committee_updated = DPCommittee.objects.filter(cs_id=cs_query).update(
            committee_approval="",
            committee_status=""
        )
        
        approval_updated = DPApproval.objects.filter(cs_id=cs_query).update(
            approval="",
            justification=""
        )
        
        # Clear all related caches comprehensively
        cache_keys_to_delete = [
            f'dp_cs_data_{cs_id}',
            f'dp_cs_list_user_{cs_query.created_by_id}',
            f'dp_data_{cs_id}',
            f'dp_list_user_{cs_query.created_by_id}',
            f'dp_committee_{cs_id}',
            f'dp_approvals_{cs_id}',
            f'dp_bids_{cs_id}',
            f'dp_compliance_{cs_id}',
            f'dp_rankings_{cs_id}'
        ]
        
        for key in cache_keys_to_delete:
            cache.delete(key)
        
        logger.info(f"Cleared approvals for DP {cs_id} - Committee: {committee_updated}, Approvals: {approval_updated}")
        return True
        
    except Exception as ex:
        logger.error(f"Error clearing approvals for DP {cs_id}: {str(ex)}")
        raise  # Re-raise to trigger transaction rollback

def getUserFMGMRoles(user):
    """Optimized role checking with caching"""
    cache_key = f'dp_user_roles_{user.id}_{APP_NAME}'
    roles = cache.get(cache_key)
    
    if roles is None:
        fm_role, gm_role, procurement_role = False, False, False

        try:
            user_direct_purchase_role = user.roles.filter(application=APP_NAME).first()

            if user_direct_purchase_role and user_direct_purchase_role.application == APP_NAME:
                if user_direct_purchase_role.role == "check":
                    fm_role = True
                if user_direct_purchase_role.role == "approve":
                    gm_role = True
                if user_direct_purchase_role.role == "procurement":
                    procurement_role = True
        except Exception as ex:
            logger.error(f"Error getting user roles: {ex}")

        roles = (fm_role, gm_role, procurement_role)
        cache.set(cache_key, roles, CACHE_TIMEOUT)
    
    return roles
 
@login_required
def get_comperative_schedules(request):
    
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user)

    if fm_role == True:
        return redirect('/direct_purchase/pending_fm_approval')
    elif gm_role == True:
        return redirect('/direct_purchase/pending_gm_approval')
    elif procurement_role == True:
        return redirect('/direct_purchase/your_schedules')
    else:
        return redirect('/direct_purchase/pending_commitee')
    
@login_required
def your_comperative_schedules(request):
    user_id = request.user.id
    user = UserProfile.objects.filter(id=user_id).first()
    
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user)

    user_page = 'finance/direct_purchase/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, { 
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role,
            "page_title": "Direct Purchases"})

@login_required
def get_all_schedules(request):
    
    user_id = request.user.id
    print("user name: ", request.user.username, request.user.id)
    user_profile = UserProfile.objects.filter(id=user_id).first()
    print("user: ", user_profile.username, user_profile.id)
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    
    print("roles: ", fm_role, gm_role)
    user_page = 'finance/direct_purchase/cs_schedules.html'
    return render(request, user_page, {"fm_role": fm_role, "gm_role": gm_role, "procurement_role": procurement_role,
            "page_title": "Direct Purchases"})


@login_required
def reports_all_schedules(request):
    
    user_id = request.user.id
    print("user name: ", request.user.username, request.user.id)
    user_profile = UserProfile.objects.filter(id=user_id).first()
    print("user: ", user_profile.username, user_profile.id)
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    
    print("roles: ", fm_role, gm_role)
    user_page = 'finance/direct_purchase/cs_reports.html'
    return render(request, user_page, {"fm_role": fm_role, "gm_role": gm_role, "procurement_role": procurement_role,
            "page_title": "Direct Purchases"})


@login_required
def get_pending_committee(request):
    
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
        
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)   
        
    print("roles: ", fm_role, gm_role)
    user_page = 'finance/direct_purchase/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, { 
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role,
            "page_title": "Direct Purchases"})

@login_required
def get_pending_gm_approval(request):
    
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    user_page = 'finance/direct_purchase/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, { 
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role,
            "page_title": "Direct Purchases"})

@login_required
def get_pending_fm_approval(request):
    
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    fm_role, gm_role = False, False
    fm_role, gm_role, procurement_role = getUserFMGMRoles(user_profile)
    user_page = 'finance/direct_purchase/cs_schedules.html'
    print("roles: ", fm_role, gm_role)
    return render(request, user_page, { 
            "fm_role": fm_role,
            "gm_role": gm_role,
            "procurement_role": procurement_role,
            "page_title": "Direct Purchases"})

def get_your_schedules(user_id, search_value=None, column_name=None, region=None):
    """Optimized query for user's schedules"""
    try:   
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'currency', 'pr_id'
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
        logger.error(f"Error in get_your_schedules: {ex}")
        return DirectPurchase.objects.none()

def get_pending_committee_table(user_id, search_value=None, column_name=None, region=None):
    """Optimized committee pending query"""
    try:
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'currency'
        ).prefetch_related(
            Prefetch('dpcommittee_set', 
                    queryset=DPCommittee.objects.select_related('user'))
        ).filter(
            Q(dpcommittee__committee_approval=None) | Q(dpcommittee__committee_approval=""),
            Q(dpcommittee__user_id=user_id),
            cancelled=False,
            region=region,
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
    except Exception as ex:
        logger.error(f"Error in get_pending_committee_table: {ex}")
        return DirectPurchase.objects.none()

def get_finance_manager(user_id, search_value=None, column_name=None, region=None):
    """Optimized finance manager query"""
    try:
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'currency'
        ).prefetch_related('dpcommittee_set', 'dpapproval_set').annotate(
            approved_count=Count('dpcommittee', filter=Q(dpcommittee__committee_approval="Approved")),
            not_approved_count=Count('dpcommittee', filter=Q(dpcommittee__committee_approval="")),
            rejected_count=Count('dpcommittee', filter=Q(dpcommittee__committee_approval="Rejected")),
            committee_count=Count('dpcommittee')
        ).filter(
            approved_count=F('committee_count'),
            committee_count__gt=2,
            not_approved_count=0,
            rejected_count=0,
            dpapproval__approval=None,
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
    except Exception as ex:
        logger.error(f"Error in get_finance_manager: {ex}")
        return DirectPurchase.objects.none()

def get_general_manager(user_id, search_value=None, column_name=None, region=None):
    """Optimized general manager query"""
    try:
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'currency'
        ).prefetch_related('dpcommittee_set', 'dpapproval_set').annotate(
            all_approved=Exists(
                DPCommittee.objects.filter(
                    cs_id=OuterRef('pk'),
                    committee_approval="Approved"
                )
            ),
            any_not_approved=Exists(
                DPCommittee.objects.filter(
                    cs_id=OuterRef('pk'),
                    committee_approval="Approved"
                )
            ),
            gm_approved=Exists(
                DPApproval.objects.filter(
                    cs_id=OuterRef('pk'),
                    approver_role="general_manager",
                    approval="Approved"
                )
            ),
            any_reject=Exists(
                DPApproval.objects.filter(
                    cs_id=OuterRef('pk'),
                    approval="Rejected"
                )
            ),
        ).filter(
            all_approved=True,
            any_not_approved=True,
            gm_approved=False,
            dpapproval__approver_role="finance_manager",
            dpapproval__approval="Approved",
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
    except Exception as ex:
        logger.error(f"Error in get_general_manager: {ex}")
        return DirectPurchase.objects.none()

def get_all_schedules_table(user_id, search_value=None, column_name=None, region=None):
    """Optimized all schedules query"""
    try:
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'currency'
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
    except Exception as ex:
        logger.error(f"Error in get_all_schedules_table: {ex}")
        return DirectPurchase.objects.none()


def get_filtered_schedules(user_id, search_value, column_name, user_region, status, station, pickStation, start_date, end_date):
    """Optimized filtered schedules query"""
    try:
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'currency', 'section', 'cost_center'
        ).prefetch_related('dpcommittee_set', 'dpapproval_set').filter(
            region=user_region,
        )

        if status:
            if status == "Pending Committee":
                cs = cs.filter(
                    Q(dpcommittee__committee_approval=None) | Q(dpcommittee__committee_approval="")).exclude(
                    Q(dpcommittee__committee_approval="Rejected"))
            elif status == "Pending Finance":
                cs = cs.filter(Q(dpapproval__approval="") | Q(dpapproval__approval=None)).exclude(
                    Q(dpcommittee__committee_approval=None) | Q(dpcommittee__committee_approval="") | Q(
                        dpcommittee__committee_approval="Rejected")
                )
            elif status == "Pending General Manager":
                cs = cs.filter(Q(dpapproval__approval="Approved"),
                               Q(dpapproval__approver_role="finance_manager")
                               ).exclude(
                    Q(dpapproval__approval="Rejected") | Q(dpapproval__approver_role="general_manager")
                )
            elif status == "Complete":
                cs = cs.filter(Q(dpapproval__approval="Approved"),
                               Q(dpapproval__approver_role="general_manager")).exclude(
                    Q(dpapproval__approval="Rejected") | Q(dpapproval__approval="") | Q(dpapproval__approval=None)
                )
            elif status == "Rejected":
                cs = cs.filter(
                    Q(dpapproval__approval="Rejected") | Q(dpcommittee__committee_approval="Rejected")
                )
            elif status == "Cancelled":
                cs = cs.filter(cancelled=True)

        if station and pickStation:
            if station == "Sections":
                section = Sections.objects.filter(id=pickStation).first()
                if section:
                    cs = cs.filter(section=section)
            elif station == "Cost Centre":
                cost_center = CostCenter.objects.filter(id=pickStation).first()
                if cost_center:
                    cs = cs.filter(cost_center=cost_center)
            elif station == "Region":
                region_ = Regions.objects.filter(id=pickStation).first()
                if region_:
                    cs = cs.filter(region=region_)

        # Enhanced multi-criteria search
        if search_value:
            cs = cs.filter(
                Q(cs_id__icontains=search_value) |
                Q(scope_of_work__icontains=search_value) |
                Q(pr_number__icontains=search_value) |
                Q(advert__icontains=search_value) |
                Q(created_by__username__icontains=search_value) |
                Q(created_by__first_name__icontains=search_value) |
                Q(created_by__last_name__icontains=search_value) |
                Q(dpbids__sup_id__name__icontains=search_value)
            )

        # Enhanced date filtering with multiple options
        if start_date and end_date:
            try:
                from datetime import datetime
                start_dt = datetime.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else start_date
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else end_date
                cs = cs.filter(created_at__date__range=[start_dt.date(), end_dt.date()])
            except ValueError:
                # Fallback to original filtering if date parsing fails
                cs = cs.filter(created_at__range=[start_date, end_date])

        if column_name:
            cs = cs.order_by(column_name)
            
        return cs.distinct()
    except Exception as ex:
        logger.error(f"Error in get_filtered_schedules: {ex}")
        return DirectPurchase.objects.none()

@cache_page(60 * 5)  # Cache for 5 minutes
def get_csv_export(request):
    """Optimized CSV export with caching"""
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="direct_purchase.csv"'
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


def add_details(cs_queryset):
    """Optimized add_details with proper prefetching"""
    cs_list = []
    
    # Don't re-prefetch if the queryset already has prefetched data
    # This prevents the 'dpcommittee_set' lookup conflict
    if hasattr(cs_queryset, '_prefetch_related_lookups'):
        # Use the queryset as-is if it already has prefetched data
        cs_data = cs_queryset
    else:
        # Only prefetch if not already done
        cs_data = cs_queryset.select_related(
            'created_by', 'region', 'section'
        ).prefetch_related(
            Prefetch('dpcommittee_set', queryset=DPCommittee.objects.select_related('user')),
            Prefetch('dpapproval_set', queryset=DPApproval.objects.select_related('user'))
        )
    
    for c in cs_data:
        committee_approval = ""
        gm_approval = None
        fm_approval = None
        committee_reject_reason = ""
        
        # Process committee approvals
        committee_members = list(c.dpcommittee_set.all())
        if committee_members:
            committee_approved = all([member.committee_approval == "Approved" for member in committee_members])
            if committee_approved:
                committee_approval = "Approval Complete"
                # Get approvals
                approvals = {approval.approver_role: approval for approval in c.dpapproval_set.all()}
                fm_approval = approvals.get("finance_manager")
                gm_approval = approvals.get("general_manager")
            else:
                committee_approval = "Pending"
                fm_approval = None
                gm_approval = None

                committee_pending = any([
                    member.committee_approval in ["", None] for member in committee_members
                ])

                if committee_pending:
                    committee_approval = "Pending"

                committee_rejected = next((
                    member for member in committee_members 
                    if member.committee_approval == "Rejected"
                ), None)

                if committee_rejected:
                    committee_reject_reason = committee_rejected.justification or ""
                    committee_approval = "Rejected"
        else:
            committee_approval = "Pending"
            fm_approval = None
            gm_approval = None

        try:
            cs_list.append({
                "cs_id": c.cs_id,
                "pr_id": c.pr_id_id or "",
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
                "created_by": c.created_by.username if c.created_by else "",
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
            logger.error(f"Error processing CS {c.cs_id}: {ex}")

    return cs_list

@require_http_methods(["GET"])
def datatable_data(request, view):
    """Optimized datatable data with caching and memory monitoring"""
    user_id = request.user.id
    
    # Cache key for user region
    region_cache_key = f'dp_user_region_{user_id}'
    user_region = cache.get(region_cache_key)
    
    if user_region is None:
        try:
            user_region = Regions.objects.filter(region=request.user.region).first()
            cache.set(region_cache_key, user_region, CACHE_TIMEOUT)
        except Exception as ex:
            user_region = None
            logger.error(f"Error getting user region: {ex}")
    
    draw = int(request.GET.get('draw', default=1))
    start = int(request.GET.get('start', default=0))
    requested_length = int(request.GET.get('length', default=DATATABLE_DEFAULT_SIZE))
    search_value = request.GET.get('search[value]', default='')
    
    # Apply safe pagination limits with memory monitoring
    process = psutil.Process(os.getpid())
    memory_usage = process.memory_info().rss / 1024 / 1024  # MB
    
    # Adjust page size based on memory usage
    if memory_usage > 500:  # 500MB threshold
        logger.warning(f"High memory usage: {memory_usage:.1f}MB - reducing page size")
        requested_length = min(requested_length, 10)
    
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

    # Cache key for the query
    cache_key = f'dp_datatable_{view}_{user_id}_{start}_{length}_{search_value}_{column_name}'
    cached_result = cache.get(cache_key)
    
    if cached_result is None:
        data = DirectPurchase.objects.none()
        
        if view == "your_schedules":
            data = get_your_schedules(user_id, search_value, column_name, user_region)
        elif view == "pending_committee":
            data = get_pending_committee_table(user_id, search_value, column_name, user_region)
        elif view == "pending_fm":
            data = get_finance_manager(user_id, search_value, column_name, user_region)
        elif view == "pending_gm":
            data = get_general_manager(user_id, search_value, column_name, user_region)
        elif view == "all_schedules":
            data = get_all_schedules_table(user_id, search_value, column_name, user_region)
        elif view == "filter":
            status = request.GET.get('status')
            station = request.GET.get('station')
            pickStation = request.GET.get('pick_station')
            start_date = request.GET.get('start_date')
            end_date = request.GET.get('end_date')
            data = get_filtered_schedules(user_id, search_value, column_name, user_region, status, station, pickStation, start_date, end_date)
        elif view == "advanced_search":
            # Extract advanced search parameters
            filters = {
                'search_value': search_value,
                'status': request.GET.get('status'),
                'min_amount': request.GET.get('min_amount'),
                'max_amount': request.GET.get('max_amount'),
                'date_field': request.GET.get('date_field', 'created_at'),
                'start_date': request.GET.get('start_date'),
                'end_date': request.GET.get('end_date'),
                'supplier_ids': request.GET.getlist('supplier_ids[]'),
                'section_ids': request.GET.getlist('section_ids[]'),
                'cost_center_ids': request.GET.getlist('cost_center_ids[]'),
                'user_ids': request.GET.getlist('user_ids[]'),
                'currency_ids': request.GET.getlist('currency_ids[]'),
                'min_bids': request.GET.get('min_bids'),
                'max_bids': request.GET.get('max_bids'),
                'sort_field': column_name.lstrip('-') if column_name else 'created_at',
                'sort_direction': 'desc' if column_name.startswith('-') else 'asc'
            }
            # Remove empty values
            filters = {k: v for k, v in filters.items() if v not in [None, '', []]}
            data = get_advanced_filtered_schedules(user_id, filters, user_region)

        # Total number of records before filtering
        total = data.count()
        
        # Pagination
        paginator = Paginator(data, length)
        page_number = start // length + 1
        
        try:
            page_obj = paginator.get_page(page_number)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.get_page(1)

        # Prepare response
        detailed_data = add_details(page_obj.object_list)
        
        cached_result = {
            'draw': draw,
            'recordsTotal': total,
            'recordsFiltered': total,
            'data': detailed_data,
            'performance_info': {
                'memory_usage_mb': round(memory_usage, 1),
                'requested_length': requested_length,
                'actual_length': length,
                'memory_optimized': requested_length != length,
                'cache_hit': False
            }
        }
        
        # Cache for 2 minutes
        cache.set(cache_key, cached_result, 120)
    else:
        cached_result['draw'] = draw  # Update draw number
        cached_result['performance_info']['cache_hit'] = True
    
    return JsonResponse(cached_result)


@login_required
def get_comperative_schedule(request, cs_id):
    
    username = request.user.username
    return render(request, 'finance/direct_purchase/dp_create.html', {
        "cs_id": cs_id,
        "username": username,
    })

@login_required
def create_comperative_schedule(request):

    username = request.user.username
    return render(request, 'finance/direct_purchase/dp_create.html', {
        "username": username,
    })

@login_required
def get_comperative_schedule_data(request, cs_id):
    """Optimized CS data retrieval with caching and prefetching - excluding PR items for main load"""
    
    # Check cache first
    cache_key = f'dp_cs_data_{cs_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return JsonResponse(cached_data, safe=False)
    
    try:
        request_user = request.user
        request_user_profile = UserProfile.objects.filter(id=request_user.id).first()
        user_comparative_schedule_role = request_user_profile.get_user_role_for_application(APP_NAME) if request_user_profile else None           

        # Optimized query with all necessary prefetching
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'section', 'currency', 'proc_plan'
        ).prefetch_related(
            Prefetch('dpitems_set', queryset=DPItems.objects.all()),
            Prefetch('dprequireditems_set', queryset=DPRequiredItems.objects.all()),
            Prefetch('dpbids_set', queryset=DPBids.objects.select_related('sup_id', 'item_id')),
            Prefetch('dpcompliance_set', queryset=DPCompliance.objects.select_related('supplier_id')),
            Prefetch('dpcomplianceremarks_set', queryset=DPComplianceRemarks.objects.select_related('supplier_id')),
            Prefetch('dpranking_set', queryset=DPRanking.objects.select_related('supplier_id')),
            Prefetch('dpcommittee_set', queryset=DPCommittee.objects.select_related('user')),
            Prefetch('dpapproval_set', queryset=DPApproval.objects.select_related('user'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({
                "message": "Comparative Schedule not found",
                "success": False,
            }, status=404, safe=False)
        
        # Get related data efficiently - exclude PR data for main load
        pr = None
        if cs.pr_id_id:
            pr = PurchaseRequest.objects.select_related().filter(id=cs.pr_id_id).first()
        
        # Build context without PR items - they'll be loaded separately
        context = _build_dp_cs_context_without_pr_items(cs, pr, user_comparative_schedule_role)
        
        # Cache for 5 minutes
        cache.set(cache_key, context, CACHE_TIMEOUT)
        
        return JsonResponse(context, safe=False)
        
    except Exception as ex:
        print("Error: ", ex)
        return JsonResponse({
            "message": "Error retrieving Comparative Schedule data",
            "error": str(ex),
            "success": False,
        }, safe=False)

def _build_dp_cs_context_without_pr_items(cs, pr, user_role):
    """Build DP CS context excluding PR items for main load"""
    # Get all related objects from prefetched data
    items = list(cs.dpitems_set.all())
    cs_items = list(cs.dprequireditems_set.all())
    bids = list(cs.dpbids_set.all())
    compliance = list(cs.dpcompliance_set.all())
    compliance_remarks = list(cs.dpcomplianceremarks_set.all())
    rankings = list(cs.dpranking_set.all())
    committee = list(cs.dpcommittee_set.all())
    approvals = {approval.approver_role: approval for approval in cs.dpapproval_set.all()}
    
    # Build items list
    items_list = [
        {
            "item_id": item.item_id,
            "item_required": item.item_name,
            "quantity": item.quantity,
            "unit_of_measurement": item.unit_of_measurement,
            "created_at": item.created_at,
        } for item in items
    ]
            
    # Build grouped bids data efficiently
    grouped_data = {}
    for bid in bids:
        bid_no = bid.bid_no
        if bid_no not in grouped_data:
            # Handle file encoding efficiently
            encoded_file_data = ""
            if bid.bid_document:
                encoded_file_data = _encode_file_safely(bid.bid_document)
            
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
            'item_required': bid.item_id.item_name,
            'quantity': bid.item_id.quantity,
            'unit_of_measurement': bid.item_id.unit_of_measurement,
            'unit_price': bid.unit_price,
            'vat': bid.vat,
            'total_price': bid.total,
        })
    
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
    
    # Build other lists efficiently
    compliance_remarks_list = [
        {
            "supplier": remark.supplier_id.id,
            "supplier_name": remark.supplier_id.name,
            "remarks": remark.remarks,
        } for remark in compliance_remarks if remark.supplier_id
    ]
    
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
    
    # Build final context
    gm_approval = approvals.get("general_manager")
    fm_approval = approvals.get("finance_manager")

    # Determine if PR items tab should be enabled
    pr_items_tab_enabled = bool(cs.cs_id)  # Enable if CS has been saved (has cs_id)
    has_pr_items_configured = bool(cs_items)  # Check if PR items have been configured

    context = {
        "requester_role": user_role.role if user_role else "",
        "cs_id": cs.cs_id,
        "cs_owner": cs.created_by.username if cs.created_by else "",
        "creator": f"{cs.created_by.first_name} {cs.created_by.last_name}" if cs.created_by else "",
        "created_at": cs.created_at.isoformat() if cs.created_at else "",
        "pr_id": pr.id if pr else None,
        "pr_number": cs.pr_number,
        "pr_date": cs.pr_date,
        "additional_notes": cs.additional_notes,        
        "scope_of_work": cs.scope_of_work,
        "closing_date": cs.closing_date,
        "closing_time": cs.closing_time,
        "advert": _encode_file_safely(cs.advert) if cs.advert else "",
        "ref_date": cs.ref_date,
        "cs_opened": cs.cs_opened,
        "tac_date": cs.tac_date,
        "show_site_visit": cs.show_site_visit,
        "show_samples_required": cs.show_sample_required,
        "created_by": cs.created_by.username if cs.created_by else "",
        "section": cs.section.section if cs.section else "",
        "region": cs.region.region if cs.region else "",
        "created_at": cs.created_at,
        
        # Tab management
        "pr_items_tab_enabled": pr_items_tab_enabled,
        "has_pr_items_configured": has_pr_items_configured,
        
        # Related objects
        "proc_plan": {
            "id": cs.proc_plan.id,
            "proc_ref": cs.proc_plan.proc_ref,
            "description": cs.proc_plan.description,
        } if cs.proc_plan else {},
        
        "currency": {
            "id": cs.currency.id,
            "currency": cs.currency.currency,
        } if cs.currency else {},
        
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
            
        # Data lists (excluding PR items)
        "cs_items": [
            {
                "id": cs_item.id,
                "item_required": cs_item.item_name,
                "quantity": cs_item.quantity,
                "unit_of_measurement": cs_item.unit_of_measurement,
                "ordered": True,
            } for cs_item in cs_items
        ],
        "items": items_list,
        "bids": list(grouped_data.values()),
        "compliance": compliance_list,
        "complianceRemarks": compliance_remarks_list,
        "rankings": rankings_list,
        "committee": committee_list,
        "proc_ref": cs.proc_plan.proc_ref if cs.proc_plan else "",
        
        # Cached lookup data
        "proc_plans": _get_cached_dp_proc_plans(),
        "suppliers": _get_cached_dp_suppliers(),
        "users": _get_cached_dp_users(cs.region_id if cs.region else None),
        "currencies": _get_cached_dp_currencies(),
    }
    
    return context


def _encode_file_safely(file_path):
    """Safely encode file to base64"""
    try:
        if not file_path or not os.path.exists(file_path):
            return ""
        
        with open(file_path, 'rb') as f:
            file_data = f.read()
        return base64.b64encode(file_data).decode('utf-8')
    except Exception as ex:
        print(f"Error encoding file {file_path}: {ex}")
        return ""


def _get_cached_dp_proc_plans():
    """Get cached procurement plans"""
    cache_key = 'dp_proc_plans_all'
    data = cache.get(cache_key)
    
    if data is None:
        data = list(DPProcPlan.objects.values('id', 'proc_ref', 'description'))
        cache.set(cache_key, data, CACHE_TIMEOUT * 2)  # Cache for 10 minutes
    
    return data


def _get_cached_dp_suppliers():
    """Get cached suppliers"""
    cache_key = 'dp_suppliers_all'
    data = cache.get(cache_key)
    
    if data is None:
        data = list(Supplier.objects.values('id', 'name'))
        cache.set(cache_key, data, CACHE_TIMEOUT * 2)  # Cache for 10 minutes
    
    return data


def _get_cached_dp_users(region_id=None):
    """Get cached users for region"""
    cache_key = f'dp_users_region_{region_id}' if region_id else 'dp_users_all'
    data = cache.get(cache_key)
    
    if data is None:
        users_query = UserProfile.objects.select_related()
        if region_id:
            users_query = users_query.filter(region_id=region_id)
        
        data = list(users_query.values('id', 'username', 'first_name', 'last_name'))
        cache.set(cache_key, data, CACHE_TIMEOUT)  # Cache for 5 minutes
    
    return data


def _get_cached_dp_currencies():
    """Get cached currencies"""
    cache_key = 'dp_currencies_all'
    data = cache.get(cache_key)
    
    if data is None:
        data = list(Currency.objects.values('id', 'currency'))
        cache.set(cache_key, data, CACHE_TIMEOUT * 2)  # Cache for 10 minutes
    
    return data


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
        proc_plans = DPProcPlan.objects.all()
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
                "message": "PR details retrieved successfully",
                "pr_id": pr_id,
                "scope_of_work": purchase_request.scope_of_work,
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
    proc_plans = DPProcPlan.objects.all()
    username = request.user.username
    
    return render(request, 'finance/direct_purchase/dp_create.html', {
        "proc_plans": proc_plans,
        "username": username,
        "pr_id": pr_id,
    })

@login_required
def create(request):

    if request.method == "POST":
        tender_id = "CS" + datetime.now().strftime("%Y%m%d%I%M%S")
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
                root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'finance', 'cs', 'adverts')
                fs = FileSystemStorage(location=root_dir)
                filename_ = fs.save(advert_file.name, advert_file)
                advert_path = "uploads" + os.path.sep + "finance" + os.path.sep + "cs" + os.path.sep + "adverts" + os.path.sep + filename_
                # save_file(advert_file, advert_path)
                
            if 'bid_document' in request.FILES:
                bid_document_file = request.FILES['bid_document']
                root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'finance', 'cs', 'bids')
                fs = FileSystemStorage(location=root_dir)
                filename_ = fs.save(bid_document_file.name, bid_document_file)
                bid_document_path = "uploads" + os.path.sep + "finance" + os.path.sep + "cs" + os.path.sep + "bids" + os.path.sep + filename_
                # save_file(bid_document_file, bid_document_path)
        
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
            
            item = DPItems(
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
        
        cs_query = DirectPurchase(
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
            
        return render(request, 'finance/direct_purchase/dp_create.html', {
            "proc_plans": None,
        })
        
@login_required
def save_comparative_schedule(request):

    try:
        
        cs_id = "DP" + datetime.now().strftime("%Y%m%d%I%M%S")
        cs_exists = DirectPurchase.objects.filter(cs_id=cs_id).first()
        # @TODO try random number if cs_id exists or return error
        if cs_exists:
            cs_id = "DP" + datetime.now().strftime("%Y%m%d%I%M%S")
        advert_files = request.FILES.getlist("advert", None)
        proc_plan_id = request.POST.get("proc_plan_id", "")
        print("proc plan: ", proc_plan_id)
        # # check if proc ref has 'acc' prefix
        # if not proc_plan_id.startswith("acc"):
        #     temp_proc_ref = "acc" + proc_plan_id
        #     proc_plan_ref = temp_proc_ref
        # else:
        #     proc_plan_ref = proc_plan_id
            
        proc_plan = DPProcPlan.objects.filter(id=proc_plan_id).first()
        print("proc_plan: ", proc_plan)
        scope_of_work = request.POST.get("scope_of_work", "")
        pr_number = request.POST.get("pr_number", "")
        pr_date = request.POST.get("pr_date", "")
        ref_date = request.POST.get("ref_date", "")
        currency = request.POST.get("currency", "")
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
        cs_query = DirectPurchase(
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
        cs_id = request.POST.get("cs_id", "")
        proc_plan_id = request.POST.get("proc_plan_id", "")
        # proc_plan = data['proc_plan']
        # check if proc ref has 'acc' prefix
        # if not proc_plan_id.startswith("acc"):
        #     temp_proc_ref = "acc" + proc_plan_id
        #     proc_plan_ref = temp_proc_ref
        # else:
        #     proc_plan_ref = proc_plan_id
            
        proc_plan_ = DPProcPlan.objects.filter(id=proc_plan_id).first()
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
                root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'comparative', 'adverts')
                fs = FileSystemStorage(location=root_dir)
                filename_ = fs.save(advert_file.name, advert_file)
                advert_path = "uploads" + os.path.sep + "comparative" + os.path.sep + "adverts" + os.path.sep + filename_
        except Exception as ex:
            print("Error: ", ex)

        # fetch user
        currency = Currency.objects.filter(id=currency).first() if currency else None
        # region_ = Regions.objects.filter(region=pr.region).first() if 'region' in pr else None
        # section = Sections.objects.filter(section=pr.section).first() if 'section' in pr else None
        cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()

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
    cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
    
    if cs_query:
        pr_item_id = request.POST.get("pr_id", "")
        DPitems_data = json.loads(request.POST.get("json_data", "{}"))
        print("DPitems_data: ", DPitems_data)
        items = DPitems_data.get("cs_items", [])
        print("items ", items, type(items))
        print("pr_item_id: ", pr_item_id)
        purchase_request = PurchaseRequest.objects.filter(id=pr_item_id).first()
        print("purchase request: ", purchase_request)
        existing_items = DPRequiredItems.objects.filter(cs_id=cs_query).all()
        
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
                cs_required_items = DPRequiredItems(
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
                DPRequiredItems.objects.filter(item_name=item, cs_id=cs_query).delete()        


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
    
    bid_docs = request.FILES.get("bid_document", None)
    bid_date = request.POST.get("bid_date", "")
    supplier_name = request.POST.get("supplier_name", "")
    # get items json
    json_data = json.loads(request.POST.get("json_data", "{}"))
    items = json_data.get("items", [])
    
    cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
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
    bid_query = DPBids.objects.filter(cs_id=cs_query, sup_id=supplier, bid_no=bid_no).all()
    if bid_query:
        clear_approvals(cs_id)
        for bid in bid_query:
            # delete item
            item = DPItems.objects.filter(item_id=bid.item_id).first()
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
        item_query = DPItems(
            cs_id = cs_query,
            item_id = item_id,
            item_name = item['item_required'],
            quantity = item['quantity'],
            unit_of_measurement = item['unit_of_measurement'],
        )
        item_query.save()    
        
        bid = DPBids(
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
    cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
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
    bid_query = DPBids.objects.filter(cs_id=cs_query, sup_id=supplier).all()
    if bid_query:
        clear_approvals(cs_id)
        for bid in bid_query:
            # delete item
            item = bid.item_id if bid.item_id else None
            print("items: ", item) 
            if item:
                item.delete()
                
            compliance = DPCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier)
            if compliance:
                compliance.delete()
                
            complianceRemark = DPComplianceRemarks.objects.filter(cs_id=cs_query, supplier_id=supplier)
            if complianceRemark:
                complianceRemark.delete()
            
            bid.delete()
        
        # update bid numbers after all bids are deleted
        # Get unique suppliers and their current bid numbers
        from django.db.models import Min
        supplier_bid_numbers = DPBids.objects.filter(cs_id=cs_query).values('sup_id').annotate(
            min_bid_no=Min('bid_no')
        ).order_by('min_bid_no')
        
        # Reorder bid numbers for each supplier
        for index, supplier_bid in enumerate(supplier_bid_numbers, 1):
            new_bid_no = str(index)
            # Update all bid records for this supplier to have the new bid number
            DPBids.objects.filter(cs_id=cs_query, sup_id=supplier_bid['sup_id']).update(bid_no=new_bid_no)
            
    return JsonResponse({
        "message": "Bid deleted successfully",
        "success": True,
    })

@login_required
def save_cs_compliance(request):

    cs_id = request.POST.get("cs_id", "")
    show_site_visit = request.POST.get("show_site_visit", "")
    show_sample_required = request.POST.get("show_sample_required", "")
    json_data = json.loads(request.POST.get("compliance", "{}"))

    compliances = json_data.get("compliance", [])

    json_data_ = json.loads(request.POST.get("complianceRemarks", "{}"))

    compliance_remarks = json_data_.get("complianceRemarks", [])
    
    cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    cs_query.show_site_visit = True if show_site_visit == "yes" else False
    cs_query.show_sample_required = True if show_sample_required == "yes" else False
    cs_query.save()
    # check if compliance exists
    compliance_query = DPCompliance.objects.filter(cs_id=cs_query).all()
    if compliance_query:
        clear_approval = clear_approvals(cs_id)
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
        compliance_query = DPCompliance(
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
    compliance_remarks_query = DPComplianceRemarks.objects.filter(cs_id=cs_query).all()
    if compliance_remarks_query:
        for remark in compliance_remarks_query:
            remark.delete()
            
    for remark in compliance_remarks:
        if 'remarks' in remark and remark['remarks']:
            supplier_name = remark['supplier_name'] if 'supplier_name' in remark else ""
            print("supplier_name: ", supplier_name, cs_query)
            supplier = Supplier.objects.filter(name=supplier_name).first()
            print("supplier: ", supplier)
            _remark = DPComplianceRemarks(
                cs_id = cs_query,
                supplier_id = supplier,
                remarks = remark['remarks'] if 'remarks' in remark else ""
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
        
    return JsonResponse({
        "message": "Supplier saved successfully",
        "success": True,
    })
    
@login_required
def save_cs_ranking(request):
    cs_id = request.POST.get("cs_id", "")
    cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    # check if rankings exists
    ranking_query = DPRanking.objects.filter(cs_id=cs_query).all()
    if ranking_query:
        clear_approval = clear_approvals(cs_id)
        for ranking in ranking_query:
            ranking.delete()
    # get bids
    bids = DPBids.objects.filter(cs_id=cs_query).values('sup_id').annotate(total_sum=Sum('total'))
    compliant_bids = []
    for bid in bids:
        supplier = Supplier.objects.filter(id=bid['sup_id']).first()
        _compliance = DPCompliance.objects.filter(cs_id=cs_query, supplier_id=supplier, decision=True).first()
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
            decision = "Awarded " + supplier.name + " being the lowest bidder having complied with all the requirements is recommended to provide the goods/service at a total cost of " + cs_query.currency.currency + " " + str(total) + " excluding VAT."
        ranking_query = DPRanking(
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
    rankings = DPRanking.objects.filter(cs_id=cs_query).all()
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

    try:
        cs_id = request.POST.get("cs_id", "")
        json_data = json.loads(request.POST.get("committee", "{}"))
        committee = json_data.get("committee", [])
        cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
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
                committee_query = DPCommittee.objects.filter(cs_id=cs_query, user=member_profile).first()
                if not committee_query:
                    committee_query = DPCommittee(
                        cs_id = cs_query,
                        user = member_profile,
                        committee_name = member['memberUserName'],
                        committee_position = member['memberPosition']
                    )
                    msg = "You have been added to the committee for Direct Purchase " + cs_query.cs_id
                    url = "/direct_purchase/comperative_schedule/" + cs_query.cs_id
                    notify_user(member_profile, msg, "Direct Purchase", url, cs_query.cs_id, request)
                committee_query.save()
            
        return JsonResponse({
            "message": "Committee saved successfully",
            "success": True,
        })
    except Exception as ex:
        print("Error: ", ex)
        return JsonResponse({
            "message": "Committee saved successfully",
            "success": False,
        })

@login_required
def delete_cs_committee_member(request):
    cs_id = request.POST.get("cs_id", "")
    username = request.POST.get("username", "")
    print("username: ", username)
    cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    member_profile = UserProfile.objects.filter(username=username).first()
    if member_profile:
        committee_query = DPCommittee.objects.filter(cs_id=cs_query, user=member_profile).first()
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
    try:
        cs_id = request.POST.get("cs_id", "")
        username = request.POST.get("username", "")
        print("username: ", username)
        approval = request.POST.get("approval", "")
        justification = request.POST.get("justification", "")
        
        logger.info(f"Processing committee approval for CS: {cs_id}, User: {username}, Approval: {approval}")
        
        cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
        if not cs_query:
            logger.warning(f"Comparative Schedule not found for CS ID: {cs_id}")
            return JsonResponse({
                "message": "Comparative Schedule not found",
                "success": False,
                }, safe=False)
    
        member_profile = UserProfile.objects.filter(username=username).first()
        if member_profile:
            committee_query = DPCommittee.objects.filter(cs_id=cs_query, user=member_profile).first()
            if committee_query:
                committee_query.committee_approval = approval
                committee_query.justification = justification
                committee_query.committee_date = now()
                committee_query.save()
                notification_update(member_profile, cs_query.cs_id)
            
            committees = DPCommittee.objects.filter(cs_id=cs_query).all()
            committee_approved = all([c.committee_approval == "Approved" for c in committees])
            if committee_approved:
                fm_role = Roles.objects.filter(name="Finance Manager", application=APP_NAME).first()
                print("fm role: ", fm_role)
                fm_user = UserProfile.objects.filter(region=cs_query.region, roles=fm_role).first()
                if fm_user:
                    print("fm user: ", fm_user.username, fm_user.id)
                    msg = cs_query.cs_id + " Direct Purchase is ready for your approval "
                    url = "/direct_purchase/comperative_schedule/" + cs_query.cs_id
                    notify_user(fm_user, msg, "Direct Purchase", url, cs_query.cs_id, request)
                else:
                    print("No Finance Manager found for region: ", cs_query.region)

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
            logger.warning(f"Committee member not found: {username}")
            return JsonResponse({
                "message": "Committee member not found",
                "success": False,
            })
        
    except Exception as e:
        logger.error(f"Error in approve_cs_committee function: {str(e)}", exc_info=True)
        return JsonResponse({
            "message": f"An error occurred while processing the committee approval: {str(e)}",
            "success": False,
        }, status=500)

@login_required
def approve_cs(request):
    try:
        cs_id = request.POST.get("cs_id", "")
        username = request.POST.get("username", "")
        approval = request.POST.get("approval", "")
        justification = request.POST.get("justification", "")
        role = request.POST.get("role", "")
        
        logger.info(f"Processing approval for CS: {cs_id}, User: {username}, Role: {role}, Approval: {approval}")
        
        cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
        if not cs_query:
            logger.warning(f"Comparative Schedule not found for CS ID: {cs_id}")
            return JsonResponse({
                "message": "Comparative Schedule not found",
                "success": False,
                }, safe=False)
    
        committees = DPCommittee.objects.filter(cs_id=cs_query)
        user = UserProfile.objects.filter(region=cs_query.region, username=username).first()
        if user:
            if role == "general_manager":
                gm_approval = DPApproval(
                    cs_id = cs_query,
                    user = user,
                    approver_role = role,
                    approval = approval,
                    justification = justification,
                    approval_date = now(),
                    created_at = now(),
                )
                gm_approval.save()
                notification_update(user, cs_query.cs_id)
                
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
                fm_approval = DPApproval(
                    cs_id = cs_query,
                    user = user,
                    approver_role = role,
                    approval = approval,
                    justification = justification,
                    approval_date = now(),
                    created_at = now(),
                )
                fm_approval.save()
                
                print("user: ", user, cs_query.id)
                flag = notification_update(user, cs_query.cs_id)
                print("flag: ", flag)
                notification = Notification.objects.filter(user=user, notification_id=cs_query.id).first()
                if notification:
                    print("notification: ", notification.is_read, notification.notification_type, notification.message)
                    notification.is_read = True
                    notification.save()
                    
                committee_approved = all([c.committee_approval == "Approved" for c in committees])
                if committee_approved and approval == "Approved":
                    gm_role = Roles.objects.filter(name="General Manager", application=APP_NAME).first()
                    print("gm role: ", gm_role)
                    gm_user = UserProfile.objects.filter(region=cs_query.region, roles=gm_role).first()
                    if gm_user:
                        print("gm user: ", gm_user.username, gm_user.id)
                        notify_user(gm_user, "Direct Purchase is ready for your approval " + cs_query.cs_id, "Direct Purchase", "/direct_purchase/comperative_schedule/" + cs_query.cs_id, cs_query.cs_id, request)
                    else:
                        print("No General Manager found for region: ", cs_query.region)
            
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
    except Exception as e:
        logger.error(f"Error in approve_cs function: {str(e)}", exc_info=True)
        return JsonResponse({
            "message": f"An error occurred while processing the approval: {str(e)}",
            "success": False,
        }, status=500)

@login_required
def save_cs_decision(request):
    cs_id = request.POST.get("cs_id", "")
    committee_id = request.POST.get("committee_id", "")
    committee_decision = request.POST.get("committee_decision", "")
    cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
    if not cs_query:
        return JsonResponse({
            "message": "Comparative Schedule not found",
            "success": False,
            }, safe=False)
    
    committee_query = DPCommittee.objects.filter(cs_id=cs_query, id=committee_id).first()
    if committee_query:
        if committee_decision == "approve":
            committee_query.committee_status = True
            committee_query.committee_date = datetime.now()
            committee_query.save()
        elif committee_decision == "reject":
            committee_query.committee_status = False
            committee_query.committee_date = datetime.now()
            committee_query.save() 
            
    return JsonResponse({
        "message": "Committee decision saved successfully",
        "success": True,
    })   
        
@login_required
def cs_add_supplier(request, cs_id):
    
    if request.method == 'GET':
        
        # tender_id = request.GET['tender_id']
        # get tender bids supplier items
        tender = DirectPurchase.objects.filter(document_id=tender_id).first()
        proc_plan = DPProcPlan.objects.filter(proc_ref=tender.pr_number).first()
        bids = DPBids.objects.filter(document_id=tender_id).order_by('bid_no').all()

        bids_dict = {}
        for bid in bids:
            bids_dict.update({bid.bid_no: []})
            
        for i in range(0, len(bids_dict)):
            i = i + 1
            for bid in bids:
                if int(bid.bid_no) == i:
                    supplier = Supplier.objects.filter(sup_id=bid.sup_id).first()
                    item = DPItems.objects.filter(item_id=bid.item_id).first()

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
        proc_plans = DPProcPlan.objects.all()
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
                                  datetime.now().strftime("%Y%m%d%I%M%S") + bid_document_file.name
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
            
            item = DPItems(
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
                supplier_id = "SUP" + datetime.now().strftime("%Y%m%d%I%M%S")
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
        tender = DirectPurchase.objects.filter(document_id=tender_id).first()
        bids = DPBids.objects.filter(document_id=tender_id).order_by('bid_no').all()

        bids_dict = {}
        for bid in bids:
            bids_dict.update({bid.bid_no: []})
            
        for i in range(0, len(bids_dict)):
            i = i + 1
            for bid in bids:
                if int(bid.bid_no) == i:
                    supplier = Suppliers.objects.filter(sup_id=bid.sup_id).first()
                    item = DPItems.objects.filter(item_id=bid.item_id).first()
                    
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
            tender_compliance = DPCompliance(
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


    return render(request, 'finance/direct_purchase/cs_compliance_table.html', {"bids_items": bids_dict})

def save_additional_notes(request):
    cs_id = request.POST.get("cs_id", "")
    additional_notes = request.POST.get("additional_notes", "")
    cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
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

def save_buyers_notes(request):
    cs_id = request.POST.get("cs_id", "")
    buyers_notes = request.POST.get("buyers_notes", "")
    print("buyers_notes: ", buyers_notes)
    cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
    if cs_query:
        ranking = DPRanking.objects.filter(cs_id=cs_query, rank=1).first()
        ranking.remarks = buyers_notes if buyers_notes else "Supplier has been awarded being the lowest bidder having complied with all the requirements is recommended to provide the goods/service"
        ranking.save()
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
        cs_query = DirectPurchase.objects.filter(cs_id=cs_id).first()
        if cs_query:
            cs_query.cancelled = True
            cs_query.scope_of_work = "Cancelled Schedule: " + cs_query.scope_of_work
            cs_query.save()
            print("cs_query: ", cs_query, cs_query.cancelled, "scope: ", cs_query.scope_of_work, cs_query.pr_number)
            required_items = DPRequiredItems.objects.filter(cs_id=cs_query).all()
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
    return redirect('/direct_purchase/comperative_schedules')

# API Functions - Duplicated from comparative_schedules with DP model references

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
    user_direct_purchase_role = request_user_profile.get_user_role_for_application(APP_NAME)
    
    return JsonResponse({
        "success": True,
        "requester_role": user_direct_purchase_role.role if user_direct_purchase_role else "",
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
    """Get PR attachments"""
    if not pr_id.startswith("PR"):
        pr_id = "PR" + pr_id
        
    try:
        purchase_request = PurchaseRequest.objects.prefetch_related('attachment_set').get(id=pr_id)
    except PurchaseRequest.DoesNotExist:
        return JsonResponse({
            "success": False,
            "message": "PR not found",
        })

    pr_at_list = []
    for at in purchase_request.attachment_set.all():
        try:
            if at.file and os.path.exists(at.file.path) and at.file.size < 5 * 1024 * 1024:  # 5MB limit
                file_data = at.file.read()
                encoded_file_data = base64.b64encode(file_data).decode('utf-8')
                pr_at_list.append({
                    "id": at.id,
                    "file": encoded_file_data,
                    "name": os.path.basename(at.file.name),
                })
        except Exception as ex:
            print(f"Error processing attachment {at.id}: {ex}")
            continue

    return JsonResponse({
        "success": True,
        "pr_attachments": pr_at_list,
    })


@login_required
@require_http_methods(["GET"])
def api_get_reference_data(request):
    """Get reference data (suppliers, currencies, etc.)"""
    # Get cached reference data
    proc_plans_cache_key = 'all_dp_proc_plans'
    proc_plans = cache.get(proc_plans_cache_key)
    if proc_plans is None:
        proc_plans = list(DPProcPlan.objects.values('id', 'proc_ref', 'description'))
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
        cache.set(users_cache_key, users, CACHE_TIMEOUT * 2)

    return JsonResponse({
        "success": True,
        "proc_plans": proc_plans,
        "currencies": currencies,
        "suppliers": suppliers,
        "users": users,
    })


@login_required 
@require_http_methods(["GET"])
def api_get_users(request):
    """Get users for dropdowns with search support"""
    try:
        # Get search parameters
        search_query = request.GET.get('search', '').strip()
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        include_inactive = request.GET.get('include_inactive', 'true').lower() == 'true'
        region_id = request.GET.get('region_id')
        
        # Log search request for debugging
        logger.info(f"User search request - query: '{search_query}', limit: {limit}, offset: {offset}, include_inactive: {include_inactive}")
        
        # Base query
        users_query = UserProfile.objects.all()
        
        # Apply region filter if provided
        if region_id:
            users_query = users_query.filter(region_id=region_id)
            logger.info(f"Applied region filter: {region_id}")
        
        # Apply active status filter
        if not include_inactive:
            users_query = users_query.filter(is_active=True)
            logger.info("Filtered to active users only")
        
        # Apply search filter if provided
        if search_query and len(search_query) >= 2:
            users_query = users_query.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
            logger.info(f"Applied search filter for query: '{search_query}'")
        
        # Apply pagination
        total_count = users_query.count()
        users = users_query[offset:offset + limit]
        
        logger.info(f"Found {total_count} users, returning {len(users)} from offset {offset}")
        
        # Format response
        users_data = []
        for user in users:
            users_data.append({
                'id': user.id,
                'username': user.username,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'email': getattr(user, 'email', ''),
                'is_active': getattr(user, 'is_active', True),
            })
        
        response_data = {
            "success": True,
            "users": users_data,
            "total": total_count,
            "has_more": (offset + limit) < total_count,
            "search_query": search_query,
            "limit": limit,
            "offset": offset,
            "include_inactive": include_inactive
        }
        
        logger.info(f"Returning {len(users_data)} users for search query: '{search_query}'")
        return JsonResponse(response_data)
        
    except Exception as ex:
        logger.error(f"Error getting users: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error retrieving users: {str(ex)}",
            "users": []
        }, status=500)


@login_required 
@require_http_methods(["GET"])
def api_get_suppliers(request):
    """Get suppliers for dropdowns with search support"""
    try:
        # Get search parameters
        search_query = request.GET.get('search', '').strip()
        limit = int(request.GET.get('limit', 100))
        offset = int(request.GET.get('offset', 0))
        
        # Log search request for debugging
        logger.info(f"Supplier search request - query: '{search_query}', limit: {limit}, offset: {offset}")
        
        # Base query
        suppliers_query = Supplier.objects.all()
        
        # Apply search filter if provided
        if search_query and len(search_query) >= 2:
            suppliers_query = suppliers_query.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(address__icontains=search_query)
            )
            logger.info(f"Applied search filter for query: '{search_query}'")
        
        # Apply pagination
        total_count = suppliers_query.count()
        suppliers = suppliers_query[offset:offset + limit]
        
        logger.info(f"Found {total_count} suppliers, returning {len(suppliers)} from offset {offset}")
        
        # Format response
        suppliers_data = []
        for supplier in suppliers:
            suppliers_data.append({
                'id': supplier.id,
                'name': supplier.name,
                'email': getattr(supplier, 'email', ''),
                'phone': getattr(supplier, 'phone', ''),
                'address': getattr(supplier, 'address', ''),
            })
        
        response_data = {
            "success": True,
            "suppliers": suppliers_data,
            "total": total_count,
            "has_more": (offset + limit) < total_count,
            "search_query": search_query,
            "limit": limit,
            "offset": offset
        }
        
        logger.info(f"Returning {len(suppliers_data)} suppliers for search query: '{search_query}'")
        return JsonResponse(response_data)
        
    except Exception as ex:
        logger.error(f"Error getting suppliers: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error retrieving suppliers: {str(ex)}",
            "suppliers": []
        }, status=500)


@login_required 
@require_http_methods(["GET"])
def api_get_currencies(request):
    """Get currencies for dropdowns"""
    currencies = list(Currency.objects.values('id', 'currency'))
    
    return JsonResponse({
        "success": True,
        "currencies": currencies,
    })


@login_required 
@require_http_methods(["GET"])
def api_get_proc_plans(request):
    """Get procurement plans for dropdowns"""
    proc_plans = list(DPProcPlan.objects.values('id', 'proc_ref', 'description'))
    
    return JsonResponse({
        "success": True,
        "proc_plans": proc_plans,
    })


@login_required 
@require_http_methods(["GET"])
def api_get_users_with_roles(request):
    """Get users with their roles for the application"""
    users_with_roles = []
    
    for user in UserProfile.objects.all():
        user_role = user.get_user_role_for_application(APP_NAME)
        users_with_roles.append({
            "id": user.id,
            "username": user.username,
            "first_name": user.first_name,
            "last_name": user.last_name,
            "role": user_role.role if user_role else "",
        })
    
    return JsonResponse({
        "success": True,
        "users_with_roles": users_with_roles,
    })


@login_required 
@require_http_methods(["GET"])
def api_get_uom(request):
    """Get units of measurement for dropdowns"""
    uom_list = list(UnitOfMeasurement.objects.values('id', 'name'))
    
    return JsonResponse({
        "success": True,
        "uom": uom_list,
    })

@login_required
@require_http_methods(["GET"])
def api_get_cs_bids_optimized(request, cs_id):
    """Get bids data for a specific CS - optimized"""
    try:
        cs = DirectPurchase.objects.prefetch_related(
            Prefetch('dpbids_set', queryset=DPBids.objects.select_related('sup_id', 'item_id'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        # Build grouped bids data efficiently
        bids = list(cs.dpbids_set.all())
        grouped_data = {}
        
        for bid in bids:
            bid_no = bid.bid_no
            if bid_no not in grouped_data:
                encoded_file_data = ""
                if bid.bid_document:
                    encoded_file_data = _encode_file_safely(bid.bid_document)
                
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
        cs = DirectPurchase.objects.prefetch_related(
            Prefetch('dpcompliance_set', queryset=DPCompliance.objects.select_related('supplier_id')),
            Prefetch('dpcomplianceremarks_set', queryset=DPComplianceRemarks.objects.select_related('supplier_id'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        compliance = list(cs.dpcompliance_set.all())
        compliance_remarks = list(cs.dpcomplianceremarks_set.all())
        
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
        cs = DirectPurchase.objects.prefetch_related(
            Prefetch('dpcommittee_set', queryset=DPCommittee.objects.select_related('user'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        committee = list(cs.dpcommittee_set.all())
        
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
        cs = DirectPurchase.objects.prefetch_related(
            Prefetch('dpapproval_set', queryset=DPApproval.objects.select_related('user')),
            Prefetch('dpranking_set', queryset=DPRanking.objects.select_related('supplier_id'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        approvals = {approval.approver_role: approval for approval in cs.dpapproval_set.all()}
        rankings = list(cs.dpranking_set.all())
        
        # Build approval data
        gm_approval = approvals.get("general_manager")
        fm_approval = approvals.get("finance_manager")
        
        # Get current user's roles for direct_purchase application
        current_user = request.user
        fm_role, gm_role, procurement_role = getUserFMGMRoles(current_user)
        
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
            "current_user_roles": {
                "fm_role": fm_role,
                "gm_role": gm_role,
                "procurement_role": procurement_role
            }
        })
        
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
        cs = DirectPurchase.objects.prefetch_related(
            Prefetch('dpranking_set', queryset=DPRanking.objects.select_related('supplier_id'))
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({"success": False, "message": "CS not found"})
        
        rankings = list(cs.dpranking_set.all())
        
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
    cache_key = f'dp_cs_pr_items_{cs_id}'
    cached_data = cache.get(cache_key)
    
    if cached_data is not None:
        return JsonResponse(cached_data, safe=False)
    
    try:
        # Get CS with related data
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'section', 'currency', 'proc_plan'
        ).prefetch_related(
            Prefetch('dprequireditems_set', queryset=DPRequiredItems.objects.all())
        ).filter(cs_id=cs_id).first()
        
        if not cs:
            return JsonResponse({
                "success": False,
                "message": "Direct Purchase Schedule not found"
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
                cs_items = list(cs.dprequireditems_set.all())
                
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
    """Update PR items for a specific CS"""
    try:
        cs = DirectPurchase.objects.filter(cs_id=cs_id).first()
        if not cs:
            return JsonResponse({
                "success": False,
                "message": "Direct Purchase Schedule not found"
            }, status=404)
        
        # Get items from request
        items_data = json.loads(request.POST.get('items', '[]'))
        
        # Clear existing items
        DPRequiredItems.objects.filter(cs_id=cs).delete()
        
        # Add new items
        for item_data in items_data:
            if item_data.get('included', False):
                DPRequiredItems.objects.create(
                    cs_id=cs,
                    item_id=item_data['id'],
                    item_name=item_data['item_required'],
                    quantity=item_data['quantity'],
                    unit_of_measurement=item_data.get('unit_of_measurement', '')
                )
        
        # Clear cache
        cache_key = f'dp_cs_pr_items_{cs_id}'
        cache.delete(cache_key)
        
        return JsonResponse({
            "success": True,
            "message": "PR items updated successfully"
        })
        
    except Exception as ex:
        return JsonResponse({
            "success": False,
            "message": f"Error updating PR items: {str(ex)}"
        }, status=500)


# Helper function for file encoding
def _encode_file_safely(file_path):
    """Safely encode file to base64"""
    try:
        if file_path and os.path.exists(file_path):
            with open(file_path, 'rb') as file:
                file_data = file.read()
                return base64.b64encode(file_data).decode('utf-8')
    except Exception as ex:
        print(f"Error encoding file {file_path}: {ex}")
    return ""


# File upload/download functions
@login_required
@require_http_methods(["POST"])
def api_upload_file(request):
    """Upload file for CS bid"""
    try:
        file = request.FILES.get('file')
        if not file:
            return JsonResponse({
                "success": False,
                "message": "No file provided"
            })
        
        # Save file
        file_path = _save_file_optimized(file, 'bid_document')
        
        return JsonResponse({
            "success": True,
            "file_path": file_path,
            "message": "File uploaded successfully"
        })
        
    except Exception as ex:
        return JsonResponse({
            "success": False,
            "message": f"Error uploading file: {str(ex)}"
        })


@login_required
@require_http_methods(["GET"])
def api_download_file(request, file_id):
    """Enhanced file download with proper security and validation"""
    try:
        # Try to find the file in various bid documents
        bid_with_file = DPBids.objects.filter(
            Q(bid_document__icontains=file_id) |
            Q(id=file_id)
        ).select_related('cs_id').first()
        
        if not bid_with_file or not bid_with_file.bid_document:
            return JsonResponse({
                "success": False,
                "message": "File not found"
            }, status=404)
        
        # Security check - ensure user has access to this CS
        cs = bid_with_file.cs_id
        user = request.user
        
        # Check if user is the creator or has appropriate role
        has_access = (
            cs.created_by == user or
            user.roles.filter(application=APP_NAME).exists()
        )
        
        if not has_access:
            return JsonResponse({
                "success": False,
                "message": "Access denied"
            }, status=403)
        
        # Construct file path
        file_path = os.path.join(settings.BASE_DIR, bid_with_file.bid_document)
        
        if not os.path.exists(file_path):
            return JsonResponse({
                "success": False,
                "message": "File not found on disk"
            }, status=404)
        
        # Return file info for download
        return JsonResponse({
            "success": True,
            "file_path": bid_with_file.bid_document,
            "file_name": os.path.basename(file_path),
            "cs_id": cs.cs_id,
            "supplier": bid_with_file.sup_id.name if bid_with_file.sup_id else "Unknown"
        })
        
    except Exception as ex:
        logger.error(f"Error downloading file {file_id}: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error downloading file: {str(ex)}"
        }, status=500)


@login_required
@require_http_methods(["POST"])
@transaction.atomic
def api_save_cs_bid_optimized(request):
    """Enhanced bid saving with transaction management and bulk operations"""
    try:
        # Parse request data with better error handling
        cs_id = request.POST.get('cs_id')
        supplier_name = request.POST.get('supplier_name')
        bid_no = request.POST.get('bid_no')
        bid_docs = request.FILES.get('bid_docs')
        
        # Validate required fields
        if not all([cs_id, supplier_name, bid_no]):
            return JsonResponse({
                "message": "Missing required fields: cs_id, supplier_name, bid_no",
                "success": False,
            }, status=400)
        
        # Get items json with better error handling
        try:
            json_data = json.loads(request.POST.get("json_data", "{}"))
            items = json_data.get("items", [])
        except json.JSONDecodeError:
            return JsonResponse({
                "message": "Invalid JSON data in items",
                "success": False,
            }, status=400)
        
        if not items:
            return JsonResponse({
                "message": "No items provided",
                "success": False,
            }, status=400)
        
        # Use select_for_update to prevent race conditions
        cs_query = DirectPurchase.objects.select_for_update().filter(cs_id=cs_id).first()
        if not cs_query:
            return JsonResponse({
                "message": "Direct Purchase Schedule not found",
                "success": False,
            }, status=404)
        
        # Use get_or_create for thread safety
        supplier, created = Supplier.objects.get_or_create(
            name=supplier_name,
            defaults={'name': supplier_name}
        )
        
        # Clear existing bids for this supplier and bid number
        existing_bids = DPBids.objects.filter(cs_id=cs_query, sup_id=supplier, bid_no=bid_no)
        if existing_bids.exists():
            clear_approvals(cs_id)
            # Bulk delete related items first
            item_ids = [bid.item_id.id for bid in existing_bids if bid.item_id]
            if item_ids:
                DPItems.objects.filter(id__in=item_ids).delete()
            existing_bids.delete()
        
        # Handle file upload with enhanced validation
        bid_doc_path = ""
        if bid_docs:
            # Use the enhanced file handling function
            upload_result = _save_file_optimized_enhanced(bid_docs, 'bid_document')
            if upload_result['success']:
                bid_doc_path = upload_result['file_path']
            else:
                return JsonResponse({
                    "message": upload_result['message'],
                    "success": False,
                }, status=400)
        
        # Bulk create items for better performance
        items_to_create = []
        for i, item_data in enumerate(items):
            item_id = item_data.get('item_id', f"Item{datetime.now().strftime('%Y%m%d%H%M%S')}{i}")
            
            dp_item = DPItems(
                cs_id=cs_query,
                item_id=item_id,
                item_name=item_data.get('item_required', ''),
                quantity=item_data.get('quantity', 0),
                unit_of_measurement=item_data.get('unit_of_measurement', ''),
            )
            items_to_create.append(dp_item)
        
        # Bulk create items
        created_items = DPItems.objects.bulk_create(items_to_create)
        
        # Bulk create bids
        bids_to_create = []
        for i, item_data in enumerate(items):
            if i < len(created_items):
                bid = DPBids(
                    cs_id=cs_query,
                    item_id=created_items[i],
                    sup_id=supplier,
                    unit_price=item_data.get('unit_price', 0),
                    vat=item_data.get('vat', 0),
                    quoted_qty=item_data.get('quantity', 0),
                    bid_no=bid_no,
                    quote_date=datetime.now().date(),
                    total=item_data.get('total_price', 0),
                    bid_document=bid_doc_path
                )
                bids_to_create.append(bid)
        
        # Bulk create bids
        DPBids.objects.bulk_create(bids_to_create)
        
        # Clear relevant caches
        cache.delete(f'dp_bids_{cs_id}')
        cache.delete(f'dp_data_{cs_id}')
        cache.delete(f'dp_list_user_{cs_query.created_by_id}')
        
        logger.info(f"Bid saved successfully for DP {cs_id}, supplier {supplier_name}, bid_no {bid_no}")
        
        return JsonResponse({
            "message": "Bid saved successfully",
            "success": True,
            "bid_id": bid_no,
            "items_created": len(created_items),
            "file_uploaded": bool(bid_doc_path),
            "supplier_created": created
        })
        
    except Exception as ex:
        logger.error(f"Error saving bid: {str(ex)}")
        return JsonResponse({
            "message": f"Error saving bid: {str(ex)}",
            "success": False,
        }, status=500)


def _save_file_optimized_enhanced(uploaded_file, file_type='bid'):
    """Enhanced file upload with validation and error handling"""
    try:
        # File size validation (10MB limit)
        if uploaded_file.size > 10 * 1024 * 1024:
            return {
                'success': False,
                'message': 'File too large. Maximum size is 10MB.',
                'file_path': None
            }
        
        # File type validation
        allowed_extensions = ['.pdf', '.doc', '.docx', '.jpg', '.jpeg', '.png', '.zip', '.rar']
        file_extension = os.path.splitext(uploaded_file.name)[1].lower()
        
        if file_extension not in allowed_extensions:
            return {
                'success': False,
                'message': f'File type {file_extension} not allowed.',
                'file_path': None
            }
        
        # Generate unique filename
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f"{file_type}_{timestamp}_{uploaded_file.name}"
        
        # Create directory if it doesn't exist
        root_dir = os.path.join(settings.BASE_DIR, 'uploads', 'direct_purchase', file_type)
        os.makedirs(root_dir, exist_ok=True)
        
        # Save file
        fs = FileSystemStorage(location=root_dir)
        saved_filename = fs.save(filename, uploaded_file)
        file_path = os.path.join('uploads', 'direct_purchase', file_type, saved_filename)
        
        return {
            'success': True,
            'message': 'File uploaded successfully.',
            'file_path': file_path,
            'original_name': uploaded_file.name,
            'size': uploaded_file.size
        }
        
    except Exception as ex:
        logger.error(f"File upload error: {str(ex)}")
        return {
            'success': False,
            'message': f'File upload failed: {str(ex)}',
            'file_path': None
        }

# Keep the old function for backward compatibility
def _save_file_optimized(file, file_type):
    """Save file with optimized handling - Legacy version"""
    result = _save_file_optimized_enhanced(file, file_type)
    return result['file_path'] if result['success'] else ""

# Advanced Search & Filtering Functions

def get_advanced_filtered_schedules(user_id, filters=None, user_region=None):
    """Advanced filtering with multiple criteria and complex queries"""
    if filters is None:
        filters = {}
    
    try:
        # Base query with optimized relations
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'currency', 'section', 'cost_center'
        ).prefetch_related(
            'dpcommittee_set__user', 
            'dpapproval_set__approver',
            'dpbids_set__sup_id'
        ).filter(region=user_region)
        
        # Multi-field search with weighted relevance
        search_value = filters.get('search_value')
        if search_value:
            search_terms = search_value.split()
            search_q = Q()
            
            for term in search_terms:
                search_q |= (
                    Q(cs_id__icontains=term) |
                    Q(scope_of_work__icontains=term) |
                    Q(pr_number__icontains=term) |
                    Q(advert__icontains=term) |
                    Q(created_by__username__icontains=term) |
                    Q(created_by__first_name__icontains=term) |
                    Q(created_by__last_name__icontains=term) |
                    Q(dpbids__sup_id__name__icontains=term)
                )
            
            cs = cs.filter(search_q)
        
        # Advanced status filtering with sub-statuses
        status = filters.get('status')
        if status:
            if status == "draft":
                cs = cs.filter(dpcommittee__isnull=True)
            elif status == "pending_committee":
                cs = cs.filter(
                    Q(dpcommittee__committee_approval=None) | 
                    Q(dpcommittee__committee_approval="")
                ).exclude(Q(dpcommittee__committee_approval="Rejected"))
            elif status == "committee_partial":
                # Some committee members approved, others pending
                cs = cs.annotate(
                    approved_count=Count('dpcommittee', filter=Q(dpcommittee__committee_approval="Approved")),
                    total_count=Count('dpcommittee'),
                    pending_count=Count('dpcommittee', filter=Q(dpcommittee__committee_approval="") | Q(dpcommittee__committee_approval=None))
                ).filter(approved_count__gt=0, pending_count__gt=0)
            elif status == "pending_finance":
                cs = cs.filter(
                    Q(dpapproval__approval="") | Q(dpapproval__approval=None),
                    dpapproval__approver_role="finance_manager"
                ).exclude(
                    Q(dpcommittee__committee_approval=None) | 
                    Q(dpcommittee__committee_approval="") | 
                    Q(dpcommittee__committee_approval="Rejected")
                )
            elif status == "pending_gm":
                cs = cs.filter(
                    Q(dpapproval__approval="Approved"),
                    Q(dpapproval__approver_role="finance_manager")
                ).exclude(
                    Q(dpapproval__approval="Rejected") | 
                    Q(dpapproval__approver_role="general_manager")
                )
            elif status == "complete":
                cs = cs.filter(
                    Q(dpapproval__approval="Approved"),
                    Q(dpapproval__approver_role="general_manager")
                ).exclude(
                    Q(dpapproval__approval="Rejected") | 
                    Q(dpapproval__approval="") | 
                    Q(dpapproval__approval=None)
                )
            elif status == "rejected":
                cs = cs.filter(
                    Q(dpapproval__approval="Rejected") | 
                    Q(dpcommittee__committee_approval="Rejected")
                )
            elif status == "cancelled":
                cs = cs.filter(cancelled=True)
        
        # Amount range filtering
        min_amount = filters.get('min_amount')
        max_amount = filters.get('max_amount')
        if min_amount or max_amount:
            if min_amount:
                cs = cs.filter(dpbids__total__gte=min_amount)
            if max_amount:
                cs = cs.filter(dpbids__total__lte=max_amount)
        
        # Date range filtering with multiple date fields
        date_field = filters.get('date_field', 'created_at')
        start_date = filters.get('start_date')
        end_date = filters.get('end_date')
        
        if start_date and end_date:
            try:
                from datetime import datetime
                start_dt = datetime.strptime(start_date, '%Y-%m-%d') if isinstance(start_date, str) else start_date
                end_dt = datetime.strptime(end_date, '%Y-%m-%d') if isinstance(end_date, str) else end_date
                
                if date_field == 'created_at':
                    cs = cs.filter(created_at__date__range=[start_dt.date(), end_dt.date()])
                elif date_field == 'closing_date':
                    cs = cs.filter(closing_date__range=[start_dt.date(), end_dt.date()])
                elif date_field == 'tac_date':
                    cs = cs.filter(tac_date__range=[start_dt.date(), end_dt.date()])
                    
            except ValueError:
                logger.warning(f"Invalid date format in advanced filter: {start_date}, {end_date}")
        
        # Supplier filtering
        supplier_ids = filters.get('supplier_ids', [])
        if supplier_ids:
            cs = cs.filter(dpbids__sup_id__id__in=supplier_ids)
        
        # Section/Department filtering
        section_ids = filters.get('section_ids', [])
        if section_ids:
            cs = cs.filter(section__id__in=section_ids)
        
        # Cost center filtering
        cost_center_ids = filters.get('cost_center_ids', [])
        if cost_center_ids:
            cs = cs.filter(cost_center__id__in=cost_center_ids)
        
        # User filtering (created by)
        user_ids = filters.get('user_ids', [])
        if user_ids:
            cs = cs.filter(created_by__id__in=user_ids)
        
        # Currency filtering
        currency_ids = filters.get('currency_ids', [])
        if currency_ids:
            cs = cs.filter(currency__id__in=currency_ids)
        
        # Bid count filtering
        min_bids = filters.get('min_bids')
        max_bids = filters.get('max_bids')
        if min_bids or max_bids:
            cs = cs.annotate(bid_count=Count('dpbids__sup_id', distinct=True))
            if min_bids:
                cs = cs.filter(bid_count__gte=min_bids)
            if max_bids:
                cs = cs.filter(bid_count__lte=max_bids)
        
        # Custom sorting
        sort_field = filters.get('sort_field', 'created_at')
        sort_direction = filters.get('sort_direction', 'desc')
        
        if sort_direction == 'desc':
            sort_field = f'-{sort_field}'
        
        cs = cs.order_by(sort_field)
        
        return cs.distinct()
        
    except Exception as ex:
        logger.error(f"Error in advanced filtering: {str(ex)}")
        return DirectPurchase.objects.none()

def fuzzy_search_schedules(search_query, user_region=None, limit=50):
    """Fuzzy search with similarity scoring"""
    try:
        # Split search query into terms
        search_terms = search_query.split() if search_query else []
        
        if not search_terms:
            return DirectPurchase.objects.none()
        
        cs = DirectPurchase.objects.select_related(
            'created_by', 'region', 'currency'
        ).filter(region=user_region, cancelled=False)
        
        # Build fuzzy search using icontains for multiple terms
        search_q = Q()
        for term in search_terms:
            search_q |= (
                Q(cs_id__icontains=term) |
                Q(scope_of_work__icontains=term) |
                Q(pr_number__icontains=term) |
                Q(advert__icontains=term) |
                Q(created_by__username__icontains=term) |
                Q(created_by__first_name__icontains=term) |
                Q(created_by__last_name__icontains=term) |
                Q(dpbids__sup_id__name__icontains=term)
            )
        
        cs = cs.filter(search_q).distinct()
        return cs[:limit]
        
    except Exception as ex:
        logger.error(f"Error in fuzzy search: {str(ex)}")
        return DirectPurchase.objects.none()

# New Enhanced API Endpoints

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def api_bulk_update_items(request):
    """Bulk update multiple CS items with transaction management"""
    try:
        json_data = json.loads(request.body)
        cs_id = json_data.get('cs_id')
        items_updates = json_data.get('items', [])
        
        if not cs_id or not items_updates:
            return JsonResponse({
                "success": False,
                "message": "Missing cs_id or items data"
            }, status=400)
        
        # Verify CS exists and user has access
        cs_query = DirectPurchase.objects.select_for_update().filter(cs_id=cs_id).first()
        if not cs_query:
            return JsonResponse({
                "success": False,
                "message": "Direct Purchase not found"
            }, status=404)
        
        # Check user permissions
        user = request.user
        has_access = (
            cs_query.created_by == user or
            user.roles.filter(application=APP_NAME).exists()
        )
        
        if not has_access:
            return JsonResponse({
                "success": False,
                "message": "Access denied"
            }, status=403)
        
        # Prepare bulk updates
        items_to_update = []
        updated_count = 0
        
        for item_update in items_updates:
            item_id = item_update.get('item_id')
            if not item_id:
                continue
                
            try:
                item = DPItems.objects.get(cs_id=cs_query, item_id=item_id)
                
                # Update fields if provided
                if 'item_name' in item_update:
                    item.item_name = item_update['item_name']
                if 'quantity' in item_update:
                    item.quantity = item_update['quantity']
                if 'unit_of_measurement' in item_update:
                    item.unit_of_measurement = item_update['unit_of_measurement']
                
                items_to_update.append(item)
                updated_count += 1
                
            except DPItems.DoesNotExist:
                logger.warning(f"Item {item_id} not found for CS {cs_id}")
                continue
        
        # Bulk update items
        if items_to_update:
            DPItems.objects.bulk_update(items_to_update, 
                ['item_name', 'quantity', 'unit_of_measurement'])
        
        # Clear related caches
        cache.delete(f'dp_data_{cs_id}')
        cache.delete(f'dp_items_{cs_id}')
        
        logger.info(f"Bulk updated {updated_count} items for CS {cs_id}")
        
        return JsonResponse({
            "success": True,
            "message": f"Successfully updated {updated_count} items",
            "updated_count": updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as ex:
        logger.error(f"Error in bulk update items: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error updating items: {str(ex)}"
        }, status=500)

@login_required
@require_http_methods(["POST"])
@transaction.atomic
def api_bulk_approve_committee(request):
    """Bulk approve multiple committee members with transaction management"""
    try:
        json_data = json.loads(request.body)
        cs_id = json_data.get('cs_id')
        approvals = json_data.get('approvals', [])
        
        if not cs_id or not approvals:
            return JsonResponse({
                "success": False,
                "message": "Missing cs_id or approvals data"
            }, status=400)
        
        # Verify CS exists
        cs_query = DirectPurchase.objects.select_for_update().filter(cs_id=cs_id).first()
        if not cs_query:
            return JsonResponse({
                "success": False,
                "message": "Direct Purchase not found"
            }, status=404)
        
        # Process bulk approvals
        updated_count = 0
        
        for approval_data in approvals:
            user_id = approval_data.get('user_id')
            approval_status = approval_data.get('approval', 'Approved')
            justification = approval_data.get('justification', '')
            
            if not user_id:
                continue
            
            try:
                committee_member = DPCommittee.objects.get(
                    cs_id=cs_query, 
                    user_id=user_id
                )
                
                committee_member.committee_approval = approval_status
                committee_member.committee_justification = justification
                committee_member.committee_date = datetime.now()
                committee_member.save()
                
                updated_count += 1
                
            except DPCommittee.DoesNotExist:
                logger.warning(f"Committee member {user_id} not found for CS {cs_id}")
                continue
        
        # Clear related caches
        cache.delete(f'dp_committee_{cs_id}')
        cache.delete(f'dp_data_{cs_id}')
        
        logger.info(f"Bulk approved {updated_count} committee members for CS {cs_id}")
        
        return JsonResponse({
            "success": True,
            "message": f"Successfully processed {updated_count} approvals",
            "updated_count": updated_count
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as ex:
        logger.error(f"Error in bulk committee approval: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error processing approvals: {str(ex)}"
        }, status=500)

@login_required
@require_http_methods(["POST"])
def api_advanced_search(request):
    """Advanced search API with multiple criteria"""
    try:
        json_data = json.loads(request.body)
        user_id = request.user.id
        
        # Get user region
        try:
            user_region = Regions.objects.filter(region=request.user.region).first()
        except Exception:
            user_region = None
        
        # Extract search filters
        filters = {
            'search_value': json_data.get('search_value', ''),
            'status': json_data.get('status'),
            'min_amount': json_data.get('min_amount'),
            'max_amount': json_data.get('max_amount'),
            'date_field': json_data.get('date_field', 'created_at'),
            'start_date': json_data.get('start_date'),
            'end_date': json_data.get('end_date'),
            'supplier_ids': json_data.get('supplier_ids', []),
            'section_ids': json_data.get('section_ids', []),
            'cost_center_ids': json_data.get('cost_center_ids', []),
            'user_ids': json_data.get('user_ids', []),
            'currency_ids': json_data.get('currency_ids', []),
            'min_bids': json_data.get('min_bids'),
            'max_bids': json_data.get('max_bids'),
            'sort_field': json_data.get('sort_field', 'created_at'),
            'sort_direction': json_data.get('sort_direction', 'desc')
        }
        
        # Pagination
        page = json_data.get('page', 1)
        page_size = json_data.get('page_size', 10)
        
        # Get filtered results
        results = get_advanced_filtered_schedules(user_id, filters, user_region)
        
        # Apply pagination
        paginator = Paginator(results, page_size)
        
        try:
            page_obj = paginator.get_page(page)
        except (EmptyPage, PageNotAnInteger):
            page_obj = paginator.get_page(1)
        
        # Add details to results
        detailed_data = add_details(page_obj.object_list)
        
        # Calculate statistics
        total_results = results.count()
        total_amount = results.aggregate(
            total=Sum('dpbids__total')
        )['total'] or 0
        
        unique_suppliers = results.aggregate(
            suppliers=Count('dpbids__sup_id', distinct=True)
        )['suppliers'] or 0
        
        return JsonResponse({
            "success": True,
            "data": detailed_data,
            "pagination": {
                "page": page_obj.number,
                "pages": paginator.num_pages,
                "per_page": page_size,
                "total": total_results,
                "has_previous": page_obj.has_previous(),
                "has_next": page_obj.has_next()
            },
            "statistics": {
                "total_amount": float(total_amount),
                "unique_suppliers": unique_suppliers,
                "average_amount": float(total_amount / total_results) if total_results > 0 else 0
            },
            "filters_applied": {k: v for k, v in filters.items() if v}
        })
        
    except json.JSONDecodeError:
        return JsonResponse({
            "success": False,
            "message": "Invalid JSON data"
        }, status=400)
    except Exception as ex:
        logger.error(f"Error in advanced search API: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error performing advanced search: {str(ex)}"
        }, status=500)

@login_required
@require_http_methods(["GET"])
def api_fuzzy_search(request):
    """Fuzzy search API endpoint"""
    try:
        search_query = request.GET.get('q', '')
        limit = int(request.GET.get('limit', 20))
        
        # Get user region
        try:
            user_region = Regions.objects.filter(region=request.user.region).first()
        except Exception:
            user_region = None
        
        if not search_query.strip():
            return JsonResponse({
                "success": False,
                "message": "Search query is required"
            }, status=400)
        
        # Perform fuzzy search
        results = fuzzy_search_schedules(search_query, user_region, limit)
        
        # Convert to simple data format for quick results
        search_results = []
        for cs in results:
            search_results.append({
                'cs_id': cs.cs_id,
                'scope_of_work': cs.scope_of_work,
                'pr_number': cs.pr_number,
                'created_by': cs.created_by.get_full_name() if cs.created_by else '',
                'created_at': cs.created_at.strftime('%Y-%m-%d') if cs.created_at else '',
                'status': 'Active' if not cs.cancelled else 'Cancelled'
            })
        
        return JsonResponse({
            "success": True,
            "results": search_results,
            "total": len(search_results),
            "query": search_query,
            "limit": limit
        })
        
    except Exception as ex:
        logger.error(f"Error in fuzzy search API: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error performing fuzzy search: {str(ex)}"
        }, status=500)

@login_required
@require_http_methods(["GET"])
def api_search_suggestions(request):
    """Get search suggestions based on partial input"""
    try:
        partial_query = request.GET.get('q', '').strip()
        suggestion_type = request.GET.get('type', 'all')  # all, suppliers, users, cs_ids
        limit = int(request.GET.get('limit', 10))
        
        if len(partial_query) < 2:
            return JsonResponse({
                "success": True,
                "suggestions": []
            })
        
        suggestions = []
        
        # Get user region
        try:
            user_region = Regions.objects.filter(region=request.user.region).first()
        except Exception:
            user_region = None
        
        if suggestion_type in ['all', 'cs_ids']:
            # CS ID suggestions
            cs_suggestions = DirectPurchase.objects.filter(
                cs_id__icontains=partial_query,
                region=user_region,
                cancelled=False
            ).values_list('cs_id', flat=True)[:limit//4]
            
            for cs_id in cs_suggestions:
                suggestions.append({
                    'type': 'cs_id',
                    'value': cs_id,
                    'label': f"CS: {cs_id}"
                })
        
        if suggestion_type in ['all', 'suppliers']:
            # Supplier suggestions - search across all suppliers, not just those with bids
            supplier_suggestions = Supplier.objects.filter(
                name__icontains=partial_query
            ).values_list('name', flat=True)[:limit//4]
            
            for supplier in supplier_suggestions:
                suggestions.append({
                    'type': 'supplier',
                    'value': supplier,
                    'label': f"Supplier: {supplier}"
                })
        
        if suggestion_type in ['all', 'users']:
            # User suggestions
            user_suggestions = UserProfile.objects.filter(
                Q(username__icontains=partial_query) |
                Q(first_name__icontains=partial_query) |
                Q(last_name__icontains=partial_query)
            ).values_list('username', 'first_name', 'last_name')[:limit//4]
            
            for username, first_name, last_name in user_suggestions:
                full_name = f"{first_name} {last_name}".strip()
                suggestions.append({
                    'type': 'user',
                    'value': username,
                    'label': f"User: {full_name or username}"
                })
        
        # Limit total suggestions
        suggestions = suggestions[:limit]
        
        return JsonResponse({
            "success": True,
            "suggestions": suggestions,
            "query": partial_query,
            "type": suggestion_type
        })
        
    except Exception as ex:
        logger.error(f"Error getting search suggestions: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error getting suggestions: {str(ex)}"
                 }, status=500)

@login_required
@require_http_methods(["GET"])
def api_test_user_search(request):
    """Test endpoint for user search debugging"""
    try:
        search_query = request.GET.get('search', '').strip()
        include_inactive = request.GET.get('include_inactive', 'true').lower() == 'true'
        region_id = request.GET.get('region_id')
        
        # Get all users for comparison
        all_users = UserProfile.objects.all()
        total_users = all_users.count()
        
        # Apply filters
        if region_id:
            all_users = all_users.filter(region_id=region_id)
        
        if not include_inactive:
            all_users = all_users.filter(is_active=True)
        
        # Get users matching search
        if search_query:
            matching_users = all_users.filter(
                Q(username__icontains=search_query) |
                Q(first_name__icontains=search_query) |
                Q(last_name__icontains=search_query) |
                Q(email__icontains=search_query)
            )
            matching_count = matching_users.count()
        else:
            matching_users = all_users
            matching_count = total_users
        
        # Sample of matching users
        sample_users = list(matching_users[:10].values('id', 'username', 'first_name', 'last_name', 'email', 'is_active'))
        
        return JsonResponse({
            "success": True,
            "debug_info": {
                "search_query": search_query,
                "total_users": total_users,
                "matching_users": matching_count,
                "include_inactive": include_inactive,
                "region_id": region_id,
                "sample_users": sample_users,
                "search_applied": bool(search_query)
            }
        })
        
    except Exception as ex:
        logger.error(f"Error in test user search: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error in test search: {str(ex)}"
        }, status=500)

@login_required
@require_http_methods(["GET"])
def api_test_supplier_search(request):
    """Test endpoint for supplier search debugging"""
    try:
        search_query = request.GET.get('search', '').strip()
        
        # Get all suppliers for comparison
        all_suppliers = Supplier.objects.all()
        total_suppliers = all_suppliers.count()
        
        # Get suppliers matching search
        if search_query:
            matching_suppliers = all_suppliers.filter(
                Q(name__icontains=search_query) |
                Q(email__icontains=search_query) |
                Q(phone__icontains=search_query) |
                Q(address__icontains=search_query)
            )
            matching_count = matching_suppliers.count()
        else:
            matching_suppliers = all_suppliers
            matching_count = total_suppliers
        
        # Sample of matching suppliers
        sample_suppliers = list(matching_suppliers[:10].values('id', 'name', 'email', 'phone', 'address'))
        
        return JsonResponse({
            "success": True,
            "debug_info": {
                "search_query": search_query,
                "total_suppliers": total_suppliers,
                "matching_suppliers": matching_count,
                "sample_suppliers": sample_suppliers,
                "search_applied": bool(search_query)
            }
        })
        
    except Exception as ex:
        logger.error(f"Error in test supplier search: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error in test search: {str(ex)}"
        }, status=500)

@login_required
@require_http_methods(["GET"])
def api_search_filters_data(request):
    """Get data for search filter dropdowns"""
    try:
        # Get user region
        try:
            user_region = Regions.objects.filter(region=request.user.region).first()
        except Exception:
            user_region = None
        
        # Get available filter options
        suppliers = Supplier.objects.all().values('id', 'name').order_by('name')
        
        sections = Sections.objects.all().values('id', 'name').order_by('name')
        
        cost_centers = CostCenter.objects.all().values('id', 'name').order_by('name')
        
        currencies = Currency.objects.all().values('id', 'currency').order_by('currency')
        
        users = UserProfile.objects.filter(
            directpurchase__region=user_region
        ).distinct().values('id', 'username', 'first_name', 'last_name').order_by('username')
        
        # Status options
        status_options = [
            {'value': 'draft', 'label': 'Draft'},
            {'value': 'pending_committee', 'label': 'Pending Committee'},
            {'value': 'committee_partial', 'label': 'Committee Partial'},
            {'value': 'pending_finance', 'label': 'Pending Finance'},
            {'value': 'pending_gm', 'label': 'Pending General Manager'},
            {'value': 'complete', 'label': 'Complete'},
            {'value': 'rejected', 'label': 'Rejected'},
            {'value': 'cancelled', 'label': 'Cancelled'}
        ]
        
        # Date field options
        date_field_options = [
            {'value': 'created_at', 'label': 'Created Date'},
            {'value': 'closing_date', 'label': 'Closing Date'},
            {'value': 'tac_date', 'label': 'TAC Date'}
        ]
        
        return JsonResponse({
            "success": True,
            "filters": {
                "suppliers": list(suppliers),
                "sections": list(sections),
                "cost_centers": list(cost_centers),
                "currencies": list(currencies),
                "users": [
                    {
                        'id': user['id'],
                        'username': user['username'],
                        'full_name': f"{user['first_name']} {user['last_name']}".strip() or user['username']
                    } for user in users
                ],
                "status_options": status_options,
                "date_field_options": date_field_options
            }
        })
        
    except Exception as ex:
        logger.error(f"Error getting filter data: {str(ex)}")
        return JsonResponse({
            "success": False,
            "message": f"Error getting filter data: {str(ex)}"
        }, status=500)