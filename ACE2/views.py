from datetime import datetime, date
from os.path import basename
from random import randrange
import logging

import sweetify
import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.core.exceptions import ValidationError
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound, FileResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.template import loader
try:
    from openpyxl import Workbook
except Exception:  # Fallback for test environments without openpyxl
    class Workbook:  # minimal stub
        def __init__(self): pass
        def save(self, *args, **kwargs): pass
        @property
        def active(self):
            class _Sheet:
                def append(self, *args, **kwargs): pass
            return _Sheet()

try:
    from weasyprint import HTML
except Exception:
    class HTML:
        def __init__(self, *args, **kwargs): pass
        def write_pdf(self, *args, **kwargs): return b""
from django.db import transaction
from django.utils.dateparse import parse_date
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count
from django.utils import timezone

logger = logging.getLogger(__name__)

from ACE2.forms import *
from ACE2.utils import find_pettycash_section_head, determine_ace_type
from approve.forms import ApprovalForm
from approve.models import Step, Workflow
try:
    from approve.views import intiate
except Exception:
    def intiate(request, application_name):
        """Test-safe fallback to initialize a minimal Process without importing heavy deps."""
        try:
            from approve.models import Workflow, Process
            from it.users.models import Application
            app, _ = Application.objects.get_or_create(name=application_name, defaults={'fullname': application_name})
            wf, _ = Workflow.objects.get_or_create(name=application_name, application=app)
            return Process.objects.create(workflow=wf)
        except Exception:
            return None
from it.users.models import UserProfile, Roles, Designations, Districts, Depots, Notification
try:
    from finance.PettyCash.views import approve_step
except Exception:
    def approve_step(*args, **kwargs):
        return True

try:
    from finance.comparative_schedules.views import notification_update, notify_user
except Exception:
    def notify_user(*args, **kwargs):
        return None
    def notification_update(*args, **kwargs):
        return None
from .models import AceReport as Report
try:
    from finance.PettyCash.models import Pettycash
except Exception:
    class Pettycash:
        pass
try:
    from tokens.models import Token  # Adjust if your model is named differently
except Exception:
    class Token:
        pass
try:
    from finance.comparative_schedules.models import ComparativeSchedules  # Correct import
except Exception:
    class ComparativeSchedules:
        pass
try:
    from finance.direct_purchase.models import DirectPurchase
except Exception:
    class DirectPurchase:
        pass
from django.http import FileResponse, HttpResponseNotFound
from django.db.models.functions import TruncMonth
from django.db.models import Sum, Count

from .utils import notify_head_office_approvers, get_regional_budget_impact_summary

# Safe helper to get a queryset of Roles for the current user without assuming request.user has a direct 'roles' M2M
def get_user_roles_qs(user):
    """Return a queryset of Roles for the given user safely.
    Falls back to looking up UserProfile if needed; returns empty queryset on failure.
    """
    try:
        # If the user model already has roles M2M
        if hasattr(user, 'roles') and callable(getattr(user, 'roles').all):
            return user.roles.all()
        # Fallback via profile lookup
        if hasattr(user, 'id'):
            profile = UserProfile.objects.filter(id=user.id).first()
            if profile and hasattr(profile, 'roles'):
                return profile.roles.all()
    except Exception:
        pass
    return Roles.objects.none()

# Create your views here.
@login_required
def Ace_detail(request, Ace_id2):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    clear = False
    clear_minus = False
    approve_now = False

    user_groups = user_profile.groups.values_list('name', flat=True)

    custom_user_roles = {
        "ace": {},
    }

    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()

        if role.application == "ace":
            custom_user_roles["ace"] = role.role
    ace_role = str(custom_user_roles["ace"])
    # print(ace_role)

    ace_item = Ace2.objects.get(Ace_id2=Ace_id2)
    #clear notification
    notification_obj = Notification.objects.filter(notification_id=ace_item.Ace_id2).first()
    if notification_obj:
        notification_obj.is_read = True
        notification_obj.save()
        print(notification_obj, ' now set to read')

    budget = ace_item.budget_id.budget_id
    budget = AssetBudget.objects.get(budget_id=budget)
    balance_before = budget.balance
    balance_after = balance_before - ace_item.amount

    # Check for rejected ACEs and process budget reversal only once
    if ace_item.process and ace_item.process.approval_set.exists():
        last_approval = ace_item.process.approval_set.last()
        if last_approval and last_approval.approved == "Rejected":
            # Get the transaction to check if it's already been processed
            transaction = Transactions.objects.filter(Ace_id2=ace_item).first()
            # print("Transaction found:", transaction)
            if transaction and transaction.approval_status != "Rejected":
                # Reverse the budget allocation by returning the amount
                budget.to_be_withdrawn = budget.to_be_withdrawn - ace_item.amount
                budget.save()
                
                # Mark transaction as rejected to prevent repeated reversal
                transaction.approval_status = "Rejected"
                transaction.save()
                
                # Notify the requester
                user = ace_item.requested_by
                if user:
                    userp = UserProfile.objects.filter(id=user.id).first()
                    msg = f"Your ACE {ace_item.Ace_id2} has been rejected. Allocated funds have been released."
                    url = f"/ace/ace_detail/{ace_item.Ace_id2}"
                    notify_user(userp, msg, "ACE", url, ace_item.Ace_id2, request)
                    
                # Show a message to the current user
                sweetify.info(request, f"ACE {ace_item.Ace_id2} was rejected. Budget has been adjusted.")

    quotations = Quotation.objects.filter(ace2=ace_item).all()
    print(quotations.count())

    print(ace_item.section, " section")

    # if ace_role == "disburse":
    #     payment_mode = request.POST.get('payment_mode')
    #     # print(payment_mode)
    #     if payment_mode and payment_mode != '':
    #         ace_item.payment_mode = payment_mode
    #         ace_item.save()

    # Add approval notification handling
    if request.method == 'POST' and 'approval_form' in request.POST:
        form = ApprovalForm(request.POST)
        if form.is_valid():
            approved = form.cleaned_data['approved']
            remarks = form.cleaned_data['remarks']
            
            if approved == 'Approved':
                # Notify the requester about this approval step
                user = ace_item.requested_by
                if user:
                    userp = UserProfile.objects.filter(id=user.id).first()
                    
                    # Get step information for the notification message
                    try:
                        latest_approval = ace_item.process.approval_set.last()
                        if latest_approval:
                            current_step = latest_approval.step.step
                            total_steps = ace_item.process.workflow.step_set.count()
                            approver_role = request.user.designation.description if hasattr(request.user, 'designation') else "Approver"
                            
                            msg = f"Your ACE {ace_item.Ace_id2} has been approved by {approver_role} (Step {current_step}/{total_steps})"
                            url = f"/ace/ace_detail/{ace_item.Ace_id2}"
                            notify_user(userp, msg, "ACE", url, ace_item.Ace_id2, request)
                            
                            sweetify.success(request, f"ACE {ace_item.Ace_id2} approved and requester notified")
                    except Exception as e:
                        print(f"Error sending notification: {e}")
    
    approvalForm = None
    to = None
    user_roles = get_user_roles_qs(request.user)

    try:
        last_approved = ace_item.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    if ace_role == "create" or ace_role == "order":
        if len(ace_item.process.approval_set.all()) == len(ace_item.process.workflow.step_set.all()):
            clear = True
    accounting_officer_role = None
    if ace_role == "process":
        accounting_officer_role = ace_role

    approval_status = ace_item.process.approval_set.last().approved if ace_item.process.approval_set.last() else ""
    if approval_status != "Rejected":

        next_step = last_approved + 1
        if len(ace_item.process.approval_set.all()) == len(ace_item.process.workflow.step_set.all()):
            approve_now = True

        try:
            newStep = Step.objects.get(step=next_step, workflow=ace_item.process.workflow,
                                       approver__in=user_roles)

            if ace_role == "pass":
                print(ace_item.section, " section")

                if newStep and request.user.section == ace_item.section and next_step == 1:
                    approvalForm = ApprovalForm
                    to = newStep.to
                    print(ace_role)
                    if newStep.step == len(ace_item.process.workflow.step_set.all()):
                        clear = True
                    if newStep.step == len(ace_item.process.workflow.step_set.all()) - 1:
                        clear_minus = True
                    print(clear)
                elif newStep:
                    approvalForm = ApprovalForm
                    to = newStep.to
            else:
                approvalForm = ApprovalForm
                to = newStep.to
                print(ace_role)
                print(approve_now)
                if approve_now:
                    if newStep.step == len(ace_item.process.workflow.step_set.all()):
                        clear = True
                    if newStep.step == len(ace_item.process.workflow.step_set.all()) - 1:
                        clear_minus = True
                print(clear)
        except Step.DoesNotExist:
            pass

    print(approve_now)
    if approve_now:
        # budget calculations
        budget = ace_item.budget_id.budget_id
        budget = AssetBudget.objects.get(budget_id=budget)
        balance_before = "deducted"
        balance_after = "deducted"

        print("ace: ", ace_item.Ace_id)
        # Guard: ensure we query by the correct relation object, not string id
        transaction = Transactions.objects.filter(Ace_id2=ace_item).first()
        # print('transaction: ', transaction)
        # print("transaction: ", transaction)
        if not transaction:
            # Nothing to update; avoid crash and log info
            logger.warning(f"No transaction found for ACE {ace_item.Ace_id2} during approve_now.")
            transaction_status = None
        else:
            transaction_status = str(transaction.approval_status)
        print("transaction: ", str(transaction_status))

        if transaction and transaction.approval_status != "approved by General Manager":
            budget.balance = budget.balance - ace_item.amount
            budget.to_be_withdrawn = budget.to_be_withdrawn - ace_item.amount
            budget.withdrawal_date = date.today()
            budget.withdrawn = budget.withdrawn + ace_item.amount
            budget.save()

            # transaction

            transaction.approval_status = "approved by General Manager"
            transaction.save()
            print("transaction: ", str(transaction.approval_status))
            # Notification must not crash the flow
            try:
                user = ace_item.requested_by
                if user:
                    userp = UserProfile.objects.filter(id=user.id).first()
                    msg = "Your ACE " + ace_item.Ace_id2 + " has been approved by the General Manager"
                    url = "/ace/ace_detail/" + ace_item.Ace_id2
                    notify_user(userp, msg, "ACE", url, ace_item.Ace_id2, request)
            except Exception as _e:
                logger.warning(f"Failed to send GM approval notification for {ace_item.Ace_id2}: {_e}")

    # Safely handle missing or invalid quantity
    try:
        qty = int(ace_item.quantity or 0)
        if qty < 0:
            qty = 0
    except Exception:
        qty = 0
    ace_quantity = range(qty)
    approved_steps = ace_item.process.approval_set.all().values_list('step__step', flat=True)

    notification_obj = Notification.objects.filter(notification_id=ace_item.Ace_id2).first()
    section_created = ace_item.section
    section_heads = find_pettycash_section_head(section_created)
    if section_heads:
        print('doing')
        print("user prof ", user_profile, ' sect head ', section_heads)

        if user_profile.username == section_heads:
            print('notification', notification_obj)
            if notification_obj:  # Add null check here
                notification_obj.is_read = True
                notification_obj.save()
                print(notification_obj, ' now set to read')

    # if clear minus notify GM
    if clear_minus:
        msg = " ACE " + ace_item.Ace_id2 + "has been added to your tray"
        url = "/ace/ace_detail/" + ace_item.Ace_id2
        general_manager = find_general_manager(request, ace_item.region)
        if general_manager:
            general_manager = UserProfile.objects.filter(username=general_manager).first()
            notify_user(general_manager, msg, "ACE", url, ace_item.Ace_id2, request)

    return render(request, 'finance/ace2/ace_detail.html',
                  {'ace': ace_item, 'approved_steps': approved_steps, 'approvalForm': approvalForm,
                   'to': to, 'ace_role': ace_role, 'user_groups': user_groups, 'qoutations': quotations,
                   'ace_quantity': ace_quantity,
                   'clear': clear, 'clear_minus': clear_minus, 'accounting_officer_role': accounting_officer_role,
                   'balance_before': balance_before, 'balance_after': balance_after})


def generate_unique_ace_id2(prefix='ACE'):
    """Generate a unique Ace_id2 with optional prefix for high-value ACEs."""
    from datetime import datetime
    import random
    
    current_date = datetime.now()
    year = current_date.strftime("%y")
    month = current_date.strftime("%m")
    day = current_date.strftime("%d")
    
    # Try up to 100 times to generate a unique ID
    for attempt in range(100):
        random_number = random.randint(1000, 9999)
        ace_id = f"{prefix}{year}{month}{day}{random_number}"
        
        if not Ace2.objects.filter(Ace_id2=ace_id).exists():
            return ace_id
    
    # If we couldn't generate a unique ID after 100 attempts, raise an exception
    raise ValueError("Could not generate a unique ACE ID after 100 attempts")

@login_required
def create_Ace(request):
    """
    Create a new ACE with comprehensive validation and error handling
    """
    try:
        print('create ace')
        user_id = request.user.id
        user_profile = UserProfile.objects.filter(id=user_id).first()

        # Validate user profile exists
        if not user_profile:
            messages.error(request, "User profile not found. Please contact your administrator to create your profile.")
            sweetify.error(request, "User profile not found.")
            return redirect('/ace2/aces')

        # Check if user has required roles for ACE creation
        user_roles = user_profile.roles.all()
        if not user_roles.exists():
            messages.error(request, "No roles assigned. Please contact your administrator to assign appropriate roles.")
            sweetify.error(request, "No roles assigned.")
            return redirect('/ace2/aces')

        # Determine user's ACE role - THIS IS THE MISSING PART
        custom_user_roles = {"ace": {}}
        roles_ = user_profile.roles.all()
        ace_role = None
        
        for _role in roles_:
            role = Roles.objects.filter(id=_role.id).first()
            if role and role.application == "ace":
                custom_user_roles["ace"] = role.role
                ace_role = role.role
                break
        
        # Convert to string if it's still a dict
        if isinstance(custom_user_roles["ace"], dict):
            ace_role = "none"
        else:
            ace_role = str(custom_user_roles["ace"])

        print(f"User ACE role determined: {ace_role}")

        form = AceForm(user=user_profile)
        formset = QuotationFormSet()
        
        if request.method == 'POST':
            form = AceForm(request.POST, request.FILES, user=user_profile)
            formset = QuotationFormSet(request.POST, request.FILES)
            # user_id = request.user.id
            # user_profile = UserProfile.objects.filter(id=user_id).first()

            # Validate user profile exists
            if not user_profile:
                messages.error(request, "User profile not found during form processing.")
                sweetify.error(request, "User profile error.")
                return redirect('/ace2/aces')

            user_groups = user_profile.groups.values_list('name', flat=True)

            custom_user_roles = {
                "ace": {},
            }

            roles_ = user_profile.roles.all()
            if not roles_.exists():
                messages.error(request, "No roles assigned. Please contact administrator.")
                sweetify.error(request, "No roles assigned.")
                return redirect('/ace2/aces')

            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()
                if role and role.application == "ace":
                    custom_user_roles["ace"] = role.role
                    ace_role = str(custom_user_roles["ace"])
                    print(ace_role)

        if ace_role == "create":
            if form.is_valid():
                ace = form.save(commit=False)
                
                # Validate required fields before processing
                if not ace.details_of_expenditure:
                    sweetify.error(request, "Details of expenditure is required")
                    messages.error(request, 'Details of expenditure is required')
                    return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                
                if not ace.amount or ace.amount <= 0:
                    sweetify.error(request, "Valid amount is required")
                    messages.error(request, 'Valid amount is required')
                    return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                
                if not ace.budget_id:
                    sweetify.error(request, "Budget selection is required")
                    messages.error(request, 'Budget selection is required')
                    return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                
                if not ace.section:
                    sweetify.error(request, "Section is required")
                    messages.error(request, 'Section is required')
                    return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                
                # Determine ACE type and USD equivalent
                ace_type, zwl_amount = determine_ace_type(ace.amount, ace.currency)
                ace.ace_type = ace_type

                # Set workflow based on ACE type with comprehensive exception handling
                if ace_type == 'high_value':
                    try:
                        ace.process = intiate(request, 'ace_em')  # Use high-value ACE_EM workflow
                        messages.success(request, f"High-value ACE created ({zwl_amount:,.2f} ZWL). Extended approval workflow will be used.")
                    except Workflow.DoesNotExist:
                        messages.error(request, "High-value ACE workflow (ace_em) not configured. Please contact IT administrator.")
                        sweetify.error(request, "High-value ACE workflow not configured. Contact IT administrator.")
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                    except Exception as e:
                        messages.warning(request, f"High-value workflow unavailable ({str(e)}). Using standard workflow.")
                        try:
                            ace.process = intiate(request, 'ace')
                            messages.info(request, "Standard ACE workflow applied successfully.")
                        except Exception as std_error:
                            messages.error(request, f"Critical error: No ACE workflow available. Contact IT administrator. Error: {str(std_error)}")
                            sweetify.error(request, "Critical error: No ACE workflow available. Contact IT administrator.")
                            return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                else:
                    try:
                        ace.process = intiate(request, 'ace')
                        messages.success(request, "Standard ACE workflow applied successfully.")
                    except Exception as e:
                        messages.error(request, f"Critical error: ACE workflow unavailable. Contact IT administrator. Error: {str(e)}")
                        sweetify.error(request, "Critical error: ACE workflow unavailable. Contact IT administrator.")
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                
                # Continue with existing budget validation logic...
                budget = AssetBudget.objects.filter(budget_name=ace.budget_id, period=2025).first()
                print(budget, 'budget')
                print(ace.amount, 'amount', budget.balance, 'balance', budget.to_be_withdrawn, 'to be withdrawn')
                balance_after_ace = budget.balance - ace.amount
                #money in tray check
                if budget.to_be_withdrawn:

                    m_in_tray = budget.to_be_withdrawn + ace.amount
                    budget_to_be_withdrawn = budget.to_be_withdrawn
                else:
                    m_in_tray = ace.amount
                    budget_to_be_withdrawn = 0
                print(budget_to_be_withdrawn, 'budget to be withdrawn')
                print(m_in_tray, 'money in tray')
                if ace.amount <= budget.balance and budget_to_be_withdrawn <= budget.balance and balance_after_ace > 0 and m_in_tray <= budget.balance:
                    # user_id = request.user.id
                    # user_profile = UserProfile.objects.filter(id=user_id).first()
                    
                    if not user_profile:
                        sweetify.error(request, "User profile not found. Please contact your administrator.")
                        messages.error(request, 'User profile not found. Please contact your administrator.')
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                    
                    # Set the requested_by field to the UserProfile object, not request.user
                    ace.requested_by = user_profile

                    user_designation = Designations.objects.filter(id=user_profile.designation.id).first() if user_profile.designation else None
                    if not user_designation:
                        sweetify.error(request, "Please get your designation from It")
                        messages.error(request, 'Please get your designation from It')
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                    
                    user_region = Regions.objects.filter(id=user_profile.region.id).first()
                    if not user_region:
                        sweetify.error(request, "Please get region from It")
                        messages.error(request, 'Please get region from It')
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                    designation = user_designation
                    # print(designation)
                    region = user_region

                    # Generate a unique Ace_id2 with type indicator
                    try:
                        if ace_type == 'high_value':
                            ace.Ace_id2 = generate_unique_ace_id2(prefix='HV')  # High Value prefix
                        else:
                            ace.Ace_id2 = generate_unique_ace_id2()
                        
                        print(f"Generated ACE ID: {ace.Ace_id2}")  # Debug logging
                        
                        # Validate that the ACE ID was generated successfully
                        if not ace.Ace_id2:
                            raise ValueError("Failed to generate ACE ID")
                            
                    except Exception as e:
                        print(f"ACE ID Generation Error: {str(e)}")  # Debug logging
                        sweetify.error(request, "Could not generate a unique ACE ID. Please try again.")
                        messages.error(request, "Could not generate a unique ACE ID. Please try again.")
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                    
                    if designation:
                        ace.designation = designation
                    else:
                        sweetify.error(request, "Please get your designation from It")
                        messages.error(request, 'Please get your designation from It')
                    if region:
                        ace.region = region
                    else:
                        sweetify.error(request, "Please get region from It")
                        messages.error(request, 'Please get region from It')
                    ace.date_created = datetime.now().date()
                    
                    # ACE ID validation removed since it's generated programmatically above
                    # The ID generation already has its own error handling
                    
                    if not ace.details_of_expenditure:
                        sweetify.error(request, "Details of expenditure is required")
                        messages.error(request, "Details of expenditure is required")
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                    
                    if not ace.amount:
                        sweetify.error(request, "Amount is required")
                        messages.error(request, "Amount is required")
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                    
                    # Try to save with validation
                    try:
                        print(f"About to save ACE with ID: {ace.Ace_id2}")  # Debug logging
                        print(f"ACE has pk: {hasattr(ace, 'pk')}, pk value: {getattr(ace, 'pk', None)}")  # Debug logging
                        print(f"ACE requested_by: {ace.requested_by}, type: {type(ace.requested_by)}")  # Debug logging
                        ace.full_clean()  # This will call the model's clean() method
                        ace.save()
                        print(f"ACE saved successfully with ID: {ace.Ace_id2}, pk: {ace.pk}")  # Debug logging
                    except ValidationError as ve:
                        error_msg = f"Validation error saving ACE: {str(ve)}"
                        print(error_msg)  # Debug logging
                        sweetify.error(request, f"Validation error: {str(ve)}")
                        messages.error(request, f"Validation error: {str(ve)}")
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                    except AttributeError as ae:
                        error_msg = f"Attribute error during ACE save: {str(ae)}"
                        print(error_msg)  # Debug logging
                        sweetify.error(request, f"System error during ACE creation: {str(ae)}")
                        messages.error(request, f"System error during ACE creation. Please try again or contact support.")
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
                    except Exception as e:
                        error_msg = f"Error saving ACE: {str(e)}"
                        print(error_msg)  # Debug logging
                        sweetify.error(request, f"An unexpected error occurred while creating the ACE: {str(e)}. Please try again or contact support.")
                        messages.error(request, error_msg)
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})

                    ace_code = ace.section
                    print(ace_code)
                    section = Sections.objects.filter(section=ace_code).first()
                    print(section)
                    # print(ace_code)
                    # code = section.code
                    # ace.allocation_code_of_expenditure = code
                    ace.save()
                    
                    # Handle quotation files from formset
                    try:
                        for form in formset:
                            if form.is_valid() and form.cleaned_data.get('quotation_file'):
                                quotation = form.save(commit=False)
                                quotation.ace2 = ace
                                quotation.save()
                    except Exception as e:
                        messages.warning(request, f"ACE created but some attachments failed to save: {str(e)}")
                        print(f"Quotation save error: {str(e)}")
                    
                    # Also handle any additional attachments from direct file upload
                    attachments = request.FILES.getlist('attachments')
                    for attachment in attachments:
                        try:
                            quotation_obj = Quotation(quotation_file=attachment, ace2=ace)
                            quotation_obj.save()
                        except Exception as e:
                            print(f"Additional attachment save error: {str(e)}")

                    # initialise transaction and budget deductions
                    transaction = Transactions.objects.create(
                        Ace_id2=ace,
                        details_of_expenditure=ace.details_of_expenditure,
                        approval_status="created",
                        region=region,
                        amount=ace.amount,
                        budget=ace.budget_id,
                        section=section
                    )
                    transaction.section = section
                    transaction.save()

                    budget = AssetBudget.objects.filter(budget_name=ace.budget_id).first()
                    budget.to_be_withdrawn = budget_to_be_withdrawn + ace.amount
                    budget.withdrawal_date = ace.date_created
                    budget.save()

                    requester = ace.requested_by
                    use = UserProfile.objects.filter(id=requester.id).first()
                    section_created = use.section

                    # notify sh

                    section_heads = find_ace_section_head(request, section_created)
                    if section_heads:
                        print(section_heads, " section_heads")
                        # budget name
                        # bdg = AssetBudget.objects.filter(budget_id=ace.budget_id).first()
                        # budget_name = bdg.budget_name
                        msg = "Your subordinate " + str(use) + "created " + ace.Ace_id2 + " using budget " + str(
                            ace.budget_id)
                        url = "/ace/ace_detail/" + ace.Ace_id2
                        section_heads = UserProfile.objects.filter(username=section_heads).first()
                        notify_user(section_heads, msg, "ACE", url, ace.Ace_id2, request)

                    # for quotation_form in formset:
                    #     quotation = quotation_form.save(commit=False)
                    #     quotation.ace2 = ace
                    #     quotation.save()

                    ace_section = ace.section
                    ace_sh = find_ace_section_head(request, ace_section)

                    if ace_sh:
                        print(ace_sh, "ace_sh")
                        # bdg = AssetBudget.objects.filter(budget_id=ace.budget_id).first()
                        # budget_name = bdg.budget_name
                        msg = "user  " + str(use) + "created " + ace.Ace_id2 + " using budget " + str(ace.budget_id)
                        url = "/ace/ace_detail/" + ace.Ace_id2

                        ace_sh = UserProfile.objects.filter(username=ace_sh).first()
                        notify_user(ace_sh, msg, "ACE", url, ace.Ace_id2, request)

                    else:
                        print("no ace section head found")
                        sweetify.error(request, "No section head found for this section contact It")
                        messages.error(request, "No section head found for this section contact It")


                    if str(ace.classification) == "Project":
                        # the idea is that if its ace of type project there need to be added other project details
                        url = reverse('Ace:add_project_details', args=[ace.Ace_id2])
                        return redirect(url)
                    else:
                        url = reverse('Ace:ace_detail', args=[ace.Ace_id2])
                        return redirect(url)
                else:
                    messages.error(request, "ACE not created due to insufficient budget balance.")
                    sweetify.error(request, "ACE not created - insufficient budget balance.")
                    if balance_after_ace < 0:
                        messages.error(request, "The ACE requires more than the current budget balance, which would result in a negative balance.")
                        sweetify.error(request, "The ACE amount exceeds available budget balance.")
                    return render(request, 'finance/ace2/create_ace.html',
                                  {'form': form, 'formset': formset, 'error_message': "Insufficient Budget Balance"})
            else:
                # Form validation failed
                form_errors = []
                for field, errors in form.errors.items():
                    # Skip Ace_id2 errors since this field is generated programmatically
                    if field == 'Ace_id2':
                        continue
                    for error in errors:
                        field_name = field.replace('_', ' ').title()
                        # Make field names more user-friendly
                        if field == 'budget_id':
                            field_name = 'Budget'
                        elif field == 'details_of_expenditure':
                            field_name = 'Details of Expenditure'
                        form_errors.append(f"{field_name}: {error}")
                
                if form_errors:
                    error_message = "Please correct the following errors: " + "; ".join(form_errors)
                    messages.error(request, error_message)
                    sweetify.error(request, "Please correct the form errors and try again.")
                
                # Improved quotation formset error handling
                formset_errors = []
                if formset.non_form_errors():
                    for error in formset.non_form_errors():
                        if "Please submit 1 or more forms" in str(error):
                            formset_errors.append("At least one quotation file must be uploaded")
                        else:
                            formset_errors.append(str(error))
                
                for i, form_error in enumerate(formset.errors):
                    if form_error:
                        for field, error_list in form_error.items():
                            if field == 'quotation_file':
                                formset_errors.append("Quotation file is required")
                            else:
                                for error in error_list:
                                    formset_errors.append(f"Quotation {i+1}: {error}")
                
                if formset_errors:
                    formset_error_message = "Quotation errors: " + "; ".join(formset_errors)
                    messages.error(request, formset_error_message)
                    sweetify.error(request, "Please correct the quotation errors.")
                
                form = AceForm(user=user_profile)
                formset = QuotationFormSet()
        else:
            sweetify.error(request, "You are not authorized to create ACEs")
            messages.error(request, "You are not authorized to create ACEs")
            return redirect('/ace/aces')

        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})
        
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact your administrator to create your profile.")
        sweetify.error(request, "User profile not found.")
        return redirect('/ace2/aces')
    except Roles.DoesNotExist:
        messages.error(request, "Role configuration error. Please contact your administrator.")
        sweetify.error(request, "Role configuration error.")
        return redirect('/ace2/aces')
    except AssetBudget.DoesNotExist:
        messages.error(request, "Selected budget not found. Please choose a valid budget.")
        sweetify.error(request, "Budget not found.")
        form = AceForm(user=user_profile)
        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': QuotationFormSet()})
    except Sections.DoesNotExist:
        messages.error(request, "Section configuration error. Please contact your administrator.")
        sweetify.error(request, "Section not found.")
        form = AceForm(user=user_profile)
        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': QuotationFormSet()})
    except Exception as e:
        messages.error(request, f"An unexpected error occurred while creating the ACE: {str(e)}. Please try again or contact support.")
        sweetify.error(request, "System error occurred. Please try again.")
        print(f"ACE Creation Error: {str(e)}")  # For debugging
        form = AceForm(user=user_profile)
        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': QuotationFormSet()})


@login_required
def ace_awaiting_my_action(request):
    """
    Show ACEs awaiting the user's action, including head office approvers
    """
    try:
        user_id = request.user.id
        user_profile = UserProfile.objects.filter(id=user_id).first()
        
        if not user_profile:
            messages.error(request, "User profile not found. Please contact administrator.")
            return render(request, 'finance/ace2/view_all_aces.html', {
                'aces': [],
                'created_aces': [],
                'ace_role': 'none',
                'error_message': 'User profile not found'
            })
        
        # Determine user role with proper exception handling
        custom_user_roles = {"ace": {}}
        roles_ = user_profile.roles.all()
        ace_role = None
        
        try:
            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()
                if role and role.application == "ace":
                    custom_user_roles["ace"] = role.role
                    ace_role = str(custom_user_roles["ace"])
                    print("ace role", ace_role)
                    break
            
            if ace_role is None:
                # User has no ACE role assigned
                messages.warning(request, "You don't have an ACE role assigned. Please contact administrator for access.")
                return render(request, 'finance/ace2/view_all_aces.html', {
                    'aces': [],
                    'created_aces': [],
                    'ace_role': 'none',
                    'error_message': 'No ACE role assigned'
                })
                
        except Exception as e:
            messages.error(request, f"Error determining user role: {str(e)}")
            return render(request, 'finance/ace2/view_all_aces.html', {
                'aces': [],
                'created_aces': [],
                'ace_role': 'none',
                'error_message': 'Role determination error'
            })
    
    except Exception as e:
        messages.error(request, f"System error: {str(e)}")
        return render(request, 'finance/ace2/view_all_aces.html', {
            'aces': [],
            'created_aces': [],
            'ace_role': 'none',
            'error_message': 'System error'
        })
    
    if ace_role in ['fd', 'md']:  # Head office roles
        # Head office users see high-value ACEs from ALL regions
        aces_to_process = []
        
        for ace in Ace2.objects.filter(ace_type='high_value').order_by('-date_created'):
            process = ace.process
            
            if process and process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
                
                # Skip if rejected
                if last_approval.approved == "Rejected":
                    continue
            else:
                current_step = 0
            
            next_step = current_step + 1
            workflow = process.workflow
            
            # Check if user should approve this step
            try:
                step = workflow.step_set.get(step=next_step)
                if step.approver.role == ace_role:
                    aces_to_process.append(ace)
            except Step.DoesNotExist:
                continue
        
        # Add summary information for head office view
        context = {
            'aces': aces_to_process,
            'ace_role': ace_role,
            'is_head_office': True,
            'total_pending': len(aces_to_process),
        }
        
        # Add regional breakdown
        from collections import defaultdict
        regional_breakdown = defaultdict(list)
        total_value = 0
        
        for ace in aces_to_process:
            regional_breakdown[ace.region.region].append(ace)
            total_value += ace.amount or 0
        
        context.update({
            'regional_breakdown': dict(regional_breakdown),
            'total_value': total_value,
        })
        
        return render(request, 'finance/ace2/head_office_awaiting_action.html', context)

    elif ace_role in ['em']:  # Engineering Manager - Regional position
        # Engineering Manager sees high-value ACEs from THEIR region only
        aces_to_process = []
        user_region = Regions.objects.filter(id=user_profile.region.id).first()
        
        for ace in Ace2.objects.filter(ace_type='high_value', region=user_region).order_by('-date_created'):
            process = ace.process
            
            if process and process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
                
                # Skip if rejected
                if last_approval.approved == "Rejected":
                    continue
            else:
                current_step = 0
            
            next_step = current_step + 1
            workflow = process.workflow
            
            # Check if user should approve this step
            try:
                step = workflow.step_set.get(step=next_step)
                if step.approver.role == ace_role:
                    aces_to_process.append(ace)
            except Step.DoesNotExist:
                continue
        
        # Add summary information for engineering manager regional view
        context = {
            'aces': aces_to_process,
            'ace_role': ace_role,
            'is_regional': True,
            'user_region': user_region.region if user_region else 'Unknown',
            'total_pending': len(aces_to_process),
            'total_value': sum(ace.amount or 0 for ace in aces_to_process),
        }
        
        return render(request, 'finance/ace2/head_office_awaiting_action.html', context)

    else:
        # Regional logic for other roles
        aces_to_process = []
        user_roles = get_user_roles_qs(request.user)

        user_id = request.user.id
        user_profile = UserProfile.objects.filter(id=user_id).first()
        region = Regions.objects.filter(id=user_profile.region.id).first()
        section = Sections.objects.filter(section=user_profile.section).first()

        custom_user_roles = {"ace": {}}
        roles_ = user_profile.roles.all()
        for _role in roles_:
            role = Roles.objects.filter(id=_role.id).first()
            if role.application == "ace":
                custom_user_roles["ace"] = role.role
        ace_role = str(custom_user_roles["ace"])
        requester = "create"
        cashier = "process"

        # ACEs awaiting user's action (skip rejected)
        if ace_role == "pass":
            for ace in Ace2.objects.filter(section=section, date_created__year__gte=2025, region=region):
                process = ace.process
                # Skip if process is None
                if not process:
                    continue
                # Skip if any approval is "Rejected"
                if process.approval_set.filter(approved="Rejected").exists():
                    continue
                if process.approval_set.exists():
                    last_approval = process.approval_set.last()
                    current_step = last_approval.step.step
                else:
                    current_step = 0
                next_step = current_step + 1
                workflow = process.workflow
                step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()
                if step:
                    aces_to_process.append(ace)
        else:
            for ace in Ace2.objects.filter(date_created__year__gte=2025, region=region):
                process = ace.process
                # Skip if process is None
                if not process:
                    continue
                # Skip if any approval is "Rejected"
                if process.approval_set.filter(approved="Rejected").exists():
                    continue
                
                if process.approval_set.exists():
                    last_approval = process.approval_set.last()
                    current_step = last_approval.step.step
                else:
                    current_step = 0
                next_step = current_step + 1
                workflow = process.workflow
                step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()
                if step:
                    aces_to_process.append(ace)

        # ACEs created by the user (demarcation)
        created_aces = Ace2.objects.filter(requested_by=request.user, date_created__year__gte=2025, region=region)

        return render(request, 'finance/ace2/view_all_aces.html', {
            'aces': aces_to_process,
            'created_aces': created_aces,
            'ace_role': ace_role,
            'requester': requester,
            'cashier': cashier
        })


@login_required
def view_all_aces(request):
    try:
        user_roles = get_user_roles_qs(request.user)
        user_id = request.user.id
        user_profile = UserProfile.objects.filter(id=user_id).first()
        
        if not user_profile:
            messages.error(request, "User profile not found. Please contact administrator.")
            return render(request, 'finance/ace2/view_all_aces.html', {
                'aces': [],
                'ace_role': 'none',
                'requester': 'create',
                'error_message': 'User profile not found'
            })
        
        try:
            region = Regions.objects.filter(id=user_profile.region.id).first()
            section = Sections.objects.filter(section=user_profile.section).first()
        except AttributeError:
            messages.error(request, "User profile is incomplete. Missing region or section information.")
            return render(request, 'finance/ace2/view_all_aces.html', {
                'aces': [],
                'ace_role': 'none',
                'requester': 'create',
                'error_message': 'Incomplete user profile'
            })
        
        print(section, " section")

        user_groups = user_profile.groups.values_list('name', flat=True)

        custom_user_roles = {
            "ace": {},
        }

        roles_ = user_profile.roles.all()
        ace_role = None
        
        try:
            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()
                if role and role.application == "ace":
                    custom_user_roles["ace"] = role.role
                    ace_role = str(custom_user_roles["ace"])
                    break
            
            if ace_role is None:
                messages.warning(request, "You don't have an ACE role assigned. Please contact administrator for access.")
                return render(request, 'finance/ace2/view_all_aces.html', {
                    'aces': [],
                    'ace_role': 'none',
                    'requester': 'create',
                    'error_message': 'No ACE role assigned'
                })
                
        except Exception as e:
            messages.error(request, f"Error determining user role: {str(e)}")
            return render(request, 'finance/ace2/view_all_aces.html', {
                'aces': [],
                'ace_role': 'none',
                'requester': 'create',
                'error_message': 'Role determination error'
            })
            
        requester = "create"

        if ace_role == "create":
            aces = Ace2.objects.filter(region=region).order_by('-date_created')
        elif ace_role == "pass":
            aces = Ace2.objects.filter(region=region).order_by('-date_created')
        else:
            print('kings')
            aces = Ace2.objects.filter(region=region).order_by('-date_created')
            print(aces)

    except Exception as e:
        messages.error(request, f"System error: {str(e)}")
        return render(request, 'finance/ace2/view_all_aces.html', {
            'aces': [],
            'ace_role': 'none',
            'requester': 'create',
            'error_message': f'System error: {str(e)}'
        })

    return render(request, 'finance/ace2/view_all_aces.html', {'aces': aces,
                                                               'requester': requester, 'ace_role': ace_role})


def add_project_details(request, Ace_id2):
    if request.method == 'POST':
        form = ProjectDetailForm(request.POST, request.FILES)
        if form.is_valid():
            project_details = form.save(commit=False)
            # Calculate total connection fee
            total_connection_fee = (
                float(project_details.present_tariff)
                + float(project_details.present_fmc)
                + float(project_details.capital_contribution)
                + float(project_details.materials)
                + float(project_details.labour)
                + float(project_details.transport)
            )

            ace = Ace2.objects.filter(Ace_id2=Ace_id2).first()
            ace.present_tariff = project_details.present_tariff
            ace.present_fmc = project_details.present_fmc
            ace.capital_contribution = project_details.capital_contribution
            ace.materials = project_details.materials
            ace.labour = project_details.labour
            ace.transport = project_details.transport
            ace.total_connection_fee = total_connection_fee
            ace.amount = total_connection_fee + ace.amount  # Update ACE amount

            # Update related transaction amount
            transaction = Transactions.objects.filter(Ace_id2=ace).first()
            if transaction:
                transaction.amount = transaction.amount + total_connection_fee

            # Update floating cost (to_be_withdrawn) in budget
            if ace.budget_id:
                budget = ace.budget_id
                # Optionally, recalculate to_be_withdrawn as sum of all ACEs for this budget
                budget.to_be_withdrawn = budget.to_be_withdrawn + transaction.amount
                budget.withdrawal_date = date.today()  # Update withdrawal date

                if budget.to_be_withdrawn > budget.balance:
                    messages.error(request, "Insufficient budget balance for this ACE.")
                    sweetify.error(request, "Insufficient budget balance for this ACE.")
                    return redirect('Ace:ace_detail', Ace_id2=ace.Ace_id2)
                else:
                    budget.save()
                    ace.save()
                    transaction.save()
                    messages.success(request, "Project details updated successfully.")
                    sweetify.success(request, "Project details updated successfully.")

            url = reverse('Ace:ace_detail', args=[ace.Ace_id2])
            return redirect(url)
    else:
        form = ProjectDetailForm()

    return render(request, 'finance/ace2/add_project_details.html', {'form': form})


def upload_budgets(request):
    user_title = request.user.get_full_name()
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    print("in view upload")

    user_groups = user_profile.groups.values_list('name', flat=True)
    if request.method == 'POST':
        csvfile = request.FILES['file']  # file as key

        decoded_file = csvfile.read().decode('cp1252').splitlines()
        reader = csv.DictReader(decoded_file)

        for row in reader:
            print("row: ", row)
            section_code = row['section_code']
            section = row['section'][:49]
            budget_name = row['budget']
            allocated = row['allocated']
            withdrawn = row['withdrawn']
            balance = row['balance']
            period = row['period']
            awaiting_sanctioning = row['awaiting_sanctioning']
            region = row['region']

            if not allocated:
                allocated = 0  # Provide a default value if allocated is empty
            if not balance:
                balance = 0  # Provide a default value if balance is empty

            if not withdrawn:
                withdrawn = 0  # Provide a default value if withdrawn is empty
            if not period:
                period = 2025

            if not awaiting_sanctioning:
                awaiting_sanctioning = 0

            if not region:
                region='Transmission'

            try:
                allocated = float(allocated)
                balance = float(balance)
                withdrawn = float(withdrawn)
                period = int(period)  # Ensure period is an integer
                awaiting_sanctioning = float(awaiting_sanctioning)
            except ValueError:
                return HttpResponse("Error: Invalid number format in CSV file. Please check your data.")

            awaiting_sanctioning = awaiting_sanctioning
            period = period
            region = region.strip()
            region = Regions.objects.filter(region=region).first()
            print(region)
            created_date = date.today()
            budget_name = section + "  " + budget_name
            # remove whitespace on section code and section
            section_code = section_code.strip()
            section = section.strip()
            print("section code: ", section_code)
            print("section: ", section)

            # withdrawal_date = datetime.strptime(row['withdrawal_date'], "%Y/%m/%d").strftime("%Y-%m-%d")
            # areas = row['area'].split(',')
            check_budget = AssetBudget.objects.filter(budget_name=budget_name, period=period).first()
            budget_note = csvfile

            if check_budget:
                print("duplicate record ....")
            else:
                AssetBudget.objects.create(section_code=section_code,
                                           section=section,
                                           budget_name=budget_name,
                                           allocated=allocated,
                                           withdrawn=withdrawn,
                                           balance=balance,
                                           awaiting_sanctioning=awaiting_sanctioning,
                                           period=period,
                                           region=region,
                                           created_date=created_date,
                                           budget_note=budget_note),
                print("record created")
        return redirect("/ace/budgets")
        try:
            # ... view logic ...
            return HttpResponse("Budget uploaded successfully"), redirect('/ace/budgets')
        except Exception as e:
            return HttpResponse("Error: {}".format(e))
            return redirect("/ace/budgets")

    else:
        return render(request, 'finance/ace2/upload_budget.html',
                      {"title": "Upload budgets",
                       "user_title": user_title,
                       "user_groups": user_groups}
                      )


@login_required
def get_budget_balance(request, budget_id):
    print(f"budget_id: {budget_id}")
    try:
        budget = AssetBudget.objects.get(pk=budget_id)
        return JsonResponse({'balance': budget.balance, 'withdrawn': budget.withdrawn, 'name': budget.budget_name})
    except AssetBudget.DoesNotExist:
        return JsonResponse({'error': 'Budget not found'}, status=404)


def download_attachment(request, attachment_id):
    try:
        attachment = Quotation.objects.get(pk=attachment_id)
        print(attachment.quotation_file, 'attachment file')
    except Quotation.DoesNotExist:
        return HttpResponseNotFound('Attachment not found')

    response = FileResponse(attachment.quotation_file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{attachment.quotation_file}"'
    return response


@login_required(login_url='/accounts/login/')
def list_budgets(request):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    user_groups = user_profile.groups.values_list('name', flat=True)

    custom_user_roles = {
        "non_conformity": {},
        "remittance_advice": {},
        "pettycash": {},
        "adjudication": {},
        "tokens": {},
        "tenders": {},
        "ace": {},
        "users": {},
    }

    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()

        if role.application == "users":
            custom_user_roles["users"] = role

        if role.application == "non_conformity":
            custom_user_roles["non_conformity"] = role

        if role.application == "remittance_advice":
            custom_user_roles["remittance_advice"] = role

        if role.application == "pettycash":
            custom_user_roles["pettycash"] = role

        if role.application == "adjudication":
            custom_user_roles["adjudication"] = role

        if role.application == "tokens":
            custom_user_roles["tokens"] = role

        if role.application == "tenders":
            custom_user_roles["tenders"] = role

        if role.application == "ace":
            custom_user_roles["ace"] = role

    region = Regions.objects.filter(id=user_profile.region.id).first()
    district = Districts.objects.filter(code=user_profile.district).first()
    depot = Depots.objects.filter(code=user_profile.depot).first()
    section_used = Sections.objects.filter(code=user_profile.section).first()
    user_designation = Designations.objects.filter(
        id=user_profile.designation.id).first() if user_profile.designation else None

    user_title = request.user.get_full_name()

    # Limit budgets to current year and balance > 1
    current_year = timezone.now().year
    section_budget = AssetBudget.objects.filter(
        region=region,
        period=current_year,
        balance__gt=1
    )

    user_page = 'ace/budgets_index.html'

    return render(request, user_page, {
        "title": "All Records",
        "context": section_budget,
        "user_title": user_title,
        "user_groups": user_groups
    })


@login_required
def add_asset_number(request):
    if request.method == 'POST':
        print('adding asset numbers')
        print(request.POST)
        ace_id = request.POST['ace_id']
        ace_quantity = request.POST['quantity']
        ace_items = request.POST.getlist('asset_number[]')
        print(ace_items)
        ace = Ace2.objects.filter(Ace_id2=ace_id).first()
        ace.asset_number = ','.join(ace_items)
        ace.save()
        messages.success(request, 'asset numbers added')
        sweetify.success(request, 'asset numbers added')
        messages.success(request, 'asset numbers added')
        return redirect('Ace:ace_detail', Ace_id2=ace.Ace_id2)
    else:
        return redirect('/ace/aces')


@login_required
def upload_aces_csv(request):
    # day_created = None
    if request.method == 'POST':
        csvfile = request.FILES['file']  # file as key
        decoded_file = csvfile.read().decode('utf-8').splitlines()
        reader = csv.DictReader(decoded_file)
        csvfile2 = request.FILES['file2']  # file as key
        decoded_file2 = csvfile2.read().decode('utf-8').splitlines()
        reader2 = csv.DictReader(decoded_file2)
        for row in reader:
            section_code = None
            ace_id2 = row['ace']
            region = row['division']
            sectionbg = row['undertaking']
            section = row['undertaking']
            district = row['district']
            details_of_expenditure = row['description']
            classification = row['classification']
            present_tariff = row['present_tariff']
            present_fmc = row['present_fmc']
            requested_by = row['estimator']
            date_created = row['date_est']
            date_created = date_created.strip().split(" ")[0]
            if date_created != "null":
                date_created = datetime.strptime(date_created, "%Y-%m-%d")
            else:
                date_created = None
            capital_contr = row['capital_contr']
            connection_fee = row['connection_fee']
            total_connection_fee = row['total_connection_fee']
            materials = row['materials']
            labour = row['labour']
            transport = row['transport']
            summary_total = row['summary_total']
            admin_fee = row['admin_fee']
            estimated_cost = row['estimated_cost']

            applicant = row['applicant']
            app_designation = row['app_designation']
            app_date = row['app_date']
            app_date = app_date.strip().split(" ")[0]
            if app_date != "null":
                app_date = datetime.strptime(app_date, "%Y-%m-%d")
            else:
                app_date = None

            passed_by = row['passed_by']
            passed_date = row['app_date']
            passed_date = passed_date.strip().split(" ")[0]
            if passed_date != "null" or passed_date != "" or passed_date != "0000-00-00":
                passed_date = datetime.strptime(passed_date, "%Y-%m-%d")
            else:
                passed_date = None

            specification = row['specification']
            asset_number = row['asset_number']
            item_division = row['item_division']
            year = row['year']
            item_cap_est = row['item_cap_est']
            item_cap_sanc = row['item_cap_sanc']
            item_totcap_req = row['item_totcap_req']
            item_balcap = row['item_balcap']
            gross_division = row['gross_division']
            gross_tot_cap = row['gross_tot_cap']
            gross_cap_sanc = row['gross_cap_sanc']
            gross_balcap = row['gross_balcap']
            ace_amt = row['ace_amt']
            gross_balcap = row['gross_balcap']
            attachment1 = row['attachment1']
            attachment2 = row['attachment2']
            attachment3 = row['attachment3']
            attachment4 = row['attachment4']
            attachment5 = row['attachment5']
            order_number = row['order_number']

            period = row['period']

            if requested_by:
                requested_by = UserProfile.objects.filter(username=requested_by).first()
            else:
                requested_by = None
            #
            # if date_created:
            #     date_created = datetime.strptime(date_created, "%Y-%m-%d")
            # else:
            #     date_created = None
            if app_designation:
                app_designation = Designations.objects.filter(description=app_designation).first()
            else:
                app_designation = None

            if item_division:
                # fetch from remote budgets model
                budget_obj = RemoteBudget.objects.using('remote').filter(budget_id=item_division).first()
                # create assetbudget object using this information if budget doesn't exist
                print('budget', budget_obj)
                if budget_obj:
                    assetbudget = AssetBudget.objects.filter(budget_name=budget_obj.budget,
                                                             period=budget_obj.period).first()
                region = Regions.objects.filter(region='Eastern Region').first()
                if budget_obj:
                    section = Sections.objects.filter(code=str(budget_obj.section_code)).first()
                    print('section', section.section)
                    if section:
                        if section.code is None:
                            section.code = budget_obj.section_code
                            section.save()
                        print('section code', section.code)
                        section_code = section.code
                    else:
                        section_code = None
                if assetbudget:
                    assetbudget = assetbudget
                else:
                    assetbudget = AssetBudget.objects.create(section_code=str(section_code),
                                                             budget_name=budget_obj.budget,
                                                             allocated=budget_obj.allocated,
                                                             withdrawn=budget_obj.withdrawn,
                                                             balance=budget_obj.balance,
                                                             awaiting_sanctioning=budget_obj.awaiting_sanctioning,
                                                             period=budget_obj.period,
                                                             region=region,
                                                             created_date=date.today(),
                                                             section=section.section
                                                             )
                    assetbudget.save()
            else:
                assetbudget = None

            check_ace = Ace2.objects.filter(Ace_id2=ace_id2).first()
            if check_ace:
                print("duplicate record ....")
                # messages.error(request, 'duplicate record')
                # sweetify.error(request, 'duplicate record')
            else:
                if present_tariff == "":
                    present_tariff = 0
                if present_fmc == "":
                    present_fmc = 0
                if capital_contr == "":
                    capital_contr = 0
                if materials == "":
                    materials = 0
                if connection_fee == "":
                    connection_fee = 0
                if labour == "":
                    labour = 0
                if transport == "":
                    transport = 0
                if total_connection_fee == "":
                    total_connection_fee = 0
                section = Sections.objects.filter(section=sectionbg).first()
                if section:
                    section = section
                else:
                    # create new section
                    section = Sections.objects.create(section=sectionbg, code=section_code or sectionbg)
                    section.save()

                requested_by = UserProfile.objects.filter(username=requested_by).first()
                if requested_by:
                    requested_by = requested_by
                else:
                    requested_by = None
                ace = Ace2.objects.create(Ace_id2=ace_id2,
                                          region=region,
                                          section=section,
                                          details_of_expenditure=details_of_expenditure,
                                          requested_by=requested_by if requested_by else None,
                                          date_created=passed_date,
                                          asset_number=asset_number,

                                          classification=classification,
                                          present_tariff=present_tariff if isinstance(present_tariff,
                                                                                      (int, float)) else None,
                                          present_fmc=present_fmc,
                                          capital_contribution=capital_contr,
                                          materials=materials,
                                          connection_fee=connection_fee,
                                          labour=labour,
                                          transport=transport,
                                          total_connection_fee=total_connection_fee,

                                          designation=app_designation,
                                          currency='rtgs',
                                          quantity=1,
                                          budget_id=assetbudget,
                                          amount=ace_amt
                                          )
                ace.process = intiate(request, 'ace')
                transaction = Transactions.objects.create(
                    Ace_id2=ace,
                    details_of_expenditure=details_of_expenditure,
                    approval_status="created",
                    region=region,
                    amount=ace_amt,
                    budget=assetbudget,
                    section=section
                )
                transaction.save()
                ace.save()
                # for approvals in csvfile2:
        for row in reader2:
            ace_id2 = row['ace']
            ace = Ace2.objects.filter(Ace_id2=ace_id2).first()
            if ace:
                process = Ace2.objects.filter(Ace_id2=ace_id2).first().process
            print("process", process)
            print('ace found', ace)

            if ace:
                print('ace found', ace)
                section = row['section_code']
                section = Sections.objects.filter(code=section).first()
                if section:
                    section_code = section.code
                else:
                    section_code = None
                ace.section_code = section_code
                ace.allocation_code_of_expenditure = section_code
                ace.requested_by = UserProfile.objects.filter(username=row['update_user1']).first()
                ace.save()
                print('section code added')
                status_1 = row['status_1']
                status_2 = row['status_2']
                status_3 = row['status_3']
                status_4 = row['status_4']
                status_5 = row['status_5']
                # make int
                status_1 = int(status_1)
                status_2 = int(status_2)
                status_3 = int(status_3)
                status_4 = int(status_4)
                status_5 = int(status_5)
                # Extract the date part from the petty_id
                date_str = ace_id2[3:9]

                # Convert the date string to a datetime object
                # If the year is less than 20, we assume it's 2000s, otherwise it's 1900s
                year = int(date_str[:2])
                print(year, 'year1')
                if year > 20:
                    year += 2000
                else:
                    year += 1900
                print(year, 'year')

                date_str = str(year) + date_str[2:]
                day_created = datetime.strptime(date_str, '%Y%m%d')
                # format into date format not date time
                day_created = day_created.strftime('%Y-%m-%d')
                ace.date_created = day_created
                ace.save()

                print(day_created)  # Outputs: 2022-01-01 00:00:00
                if status_2 == 2:
                    # strip the row
                    user = row['update_user2']
                    # remove whitespaces
                    userp = user.strip()
                    date_approved = row['update_date2']
                    print('user', user)
                    user = UserProfile.objects.filter(username=userp).first()
                    if user:
                        print(process, "ace process")
                        if process:
                            approve_step(process.id, userp, date_approved)
                            print('sent to initial approval')
                        # approve_step(ace.process.id, userp, date_approved)
                        # print('sent to initial approval')
                    if status_3 == 3:
                        user2 = row['update_user3']
                        user2p = user2.strip()
                        date_approved = row['update_date3']
                        user2 = UserProfile.objects.filter(username=user2p).first()
                        if user2:
                            if process:
                                approve_step(ace.process.id, user2p, date_approved)

                        if status_4 == 4:
                            user3 = row['update_user4']
                            user3p = user3.strip()
                            date_approved = row['update_date4']
                            user3 = UserProfile.objects.filter(username=user3p).first()
                            if user3:
                                if process:
                                    approve_step(ace.process.id, user3p, date_approved)
                            if status_5 == 5:
                                user4 = row['update_user5']
                                user4p = user4.strip()
                                date_approved = row['update_date4']
                                user4 = UserProfile.objects.filter(username=user4p).first()
                                if user4:
                                    if process:
                                        approve_step(ace.process.id, user4p, date_approved)
                                        transaction = Transactions.objects.filter(Ace_id2=ace).first()
                                        transaction.approval_status = "approved by General Manager"
                                        transaction.save()
        return redirect("/ace/aces")
    else:
        return render(request, 'finance/ace2/upload_ace.html')

@login_required
@transaction.atomic
def create_virament(request):
    """
    Creates new virament with comprehensive error handling
    1. Validates form and business rules
    2. Initializes workflow process
    3. Records transaction atomically
    4. Handles attachments
    5. Links to source/target budgets
    """
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    
    if not user_profile.roles.filter(application="virement").exists():
        messages.error(request, "You are not authorized to create virements.")
        return HttpResponseForbidden("Access denied: No virement role assigned.")
    
    form = ViramentForm(user=user_profile)
    formset = QuotationFormSet()
    
    if request.method == 'POST':
        try:
            form = ViramentForm(request.POST, request.FILES, user=user_profile)
            formset = QuotationFormSet(request.POST, request.FILES)
            
            if form.is_valid():
                # Additional business validations
                from_budget = form.cleaned_data['from_budget']
                to_budget = form.cleaned_data['to_budget']
                amount = form.cleaned_data['amount']
                
                # Double-check available balance with database lock (considering to_be_withdrawn)
                from_budget.refresh_from_db()
                if amount > from_budget.available_balance:
                    messages.error(request, 
                        f"Insufficient available balance: Available {from_budget.available_balance:,.2f} "
                        f"(Balance: {from_budget.balance:,.2f}, "
                        f"To be withdrawn: {from_budget.to_be_withdrawn or 0:,.2f}), "
                        f"Requested {amount:,.2f}")
                    return render(request, 'finance/ace2/create_virament.html', 
                                {'form': form, 'formset': formset})
                
                # Create virament
                virament = form.save(commit=False)
                virament.process = intiate(request, 'virement')
                virament.requested_by = request.user
                virament.region = request.user.region
                virament.save()
                
                # Reserve amount in source budget's to_be_withdrawn field
                try:
                    from_budget_obj = AssetBudget.objects.select_for_update().get(
                        budget_id=virament.from_budget.budget_id
                    )
                    if from_budget_obj.to_be_withdrawn is None:
                        from_budget_obj.to_be_withdrawn = 0
                    from_budget_obj.to_be_withdrawn += virament.amount
                    from_budget_obj.save()
                    logger.info(f"Reserved {virament.amount} in to_be_withdrawn for budget {from_budget_obj.budget_id}")
                except Exception as e:
                    logger.error(f"Error reserving amount in to_be_withdrawn: {e}")
                    # Note: Transaction will rollback due to @transaction.atomic
                    messages.error(request, "Error reserving budget amount. Please try again.")
                    return render(request, 'finance/ace2/create_virment.html', 
                                {'form': form, 'formset': formset})
                
                # Add attachments
                attachments = request.FILES.getlist('attachments')
                for attachment in attachments:
                    try:
                        attachment_obj = Quotation(
                            quotation_file=attachment,
                            virament=virament
                        )
                        attachment_obj.save()
                    except Exception as e:
                        logger.error(f"Error saving attachment: {e}")
                        # Continue processing other attachments
                        
                # Create transaction
                try:
                    transaction = Transactions.objects.create(
                        virament=virament,
                        details_of_expenditure=f"virement of {virament.from_budget} to {virament.to_budget}",
                        approval_status="created",
                        region=request.user.region,
                        amount=virament.amount,
                        budget=virament.from_budget,
                        section=virament.section
                    )
                    transaction.section = virament.section
                    transaction.save()
                    
                    messages.success(request, f"Virament {virament.virament_id} created successfully.")

                    # Notify virement section head on creation
                    try:
                        v_sh_username = find_virement_section_head(request, virament.section)
                        if v_sh_username:
                            v_sh = UserProfile.objects.filter(username=v_sh_username).first()
                            if v_sh:
                                msg = (
                                    f"New virement {virament.virament_id} created: "
                                    f"{virament.from_budget} → {virament.to_budget} for {virament.amount:,.2f}"
                                )
                                url = reverse('Ace:virament_detail', args=[virament.virament_id])
                                notify_user(v_sh, msg, "VIREMENT", url, str(virament.virament_id), request)
                    except Exception as _e:
                        logger.warning(f"Failed to send virement creation notification for {virament.virament_id}: {_e}")

                    url = reverse('Ace:virament_detail', args=[virament.virament_id])
                    return redirect(url)
                    
                except Exception as e:
                    logger.error(f"Error creating transaction for virament {virament.virament_id}: {e}")
                    messages.error(request, "Error creating transaction record. Please contact support.")
                    # Transaction will rollback due to @transaction.atomic
                    return render(request, 'finance/ace2/create_virament.html', 
                                {'form': form, 'formset': formset})
            else:
                # Form validation errors
                for field, errors in form.errors.items():
                    for error in errors:
                        messages.error(request, f"{field}: {error}")
                        
        except Exception as e:
            logger.error(f"Unexpected error in create_virament: {e}")
            messages.error(request, "An unexpected error occurred. Please try again.")
            return render(request, 'finance/ace2/create_virament.html', 
                        {'form': form, 'formset': formset})
    else:
        form = ViramentForm(user=user_profile)
    
    return render(request, 'finance/ace2/create_virament.html', {'form': form, 'formset': formset})


@transaction.atomic
@login_required
def virament_detail(request, virament_id):
    virament_item = Asset_budget_Virament.objects.get(virament_id=virament_id)
    user_profile = UserProfile.objects.filter(id=request.user.id).first()

    # Enhanced role and region check
    has_virement_role = user_profile.roles.filter(application="virement").exists()
    is_same_region = virament_item.region == user_profile.region

    if not has_virement_role or not is_same_region:
        return HttpResponseForbidden("You are not authorized to view or approve this virament.")

    balance_before_from = virament_item.from_budget.balance
    balance_before_to = virament_item.to_budget.balance
    balance_after_from = virament_item.from_budget.balance - virament_item.amount
    balance_after_to = virament_item.to_budget.balance + virament_item.amount
    statements = Quotation.objects.filter(virament=virament_item)
    approvalForm = None
    print('virament')
    print(virament_item.process)
    to = None
    user_roles = get_user_roles_qs(request.user)

    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    clear = False
    clear_minus = False
    approve_now = False

    user_groups = user_profile.groups.values_list('name', flat=True)

    custom_user_roles = {
        "virement": "",
    }

    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()
        if role and role.application == "virement":
            # Use the string code of the role (e.g., "pass", "approve")
            custom_user_roles["virement"] = role.role
    virement_role = str(custom_user_roles["virement"])  # expected: "pass" | "approve" | "create" | "order"

    try:
        last_approved = virament_item.process.approval_set.last().step.step if virament_item.process.approval_set.exists() else 0
    except (AttributeError, TypeError):
        logger.warning(f"Error getting last approved step for virament {virament_id}")
        last_approved = 0
    if virement_role == "create" or virement_role == "order":
        if len(virament_item.process.approval_set.all()) == len(virament_item.process.workflow.step_set.all()):
            clear = True

    approval_status = virament_item.process.approval_set.last().approved if virament_item.process.approval_set.last() else ""
    # Initialize approved_steps early so it's available in any error paths below
    approved_steps = virament_item.process.approval_set.all().values_list('step__step', flat=True)
    if approval_status != "Rejected":
        next_step = last_approved + 1
        steps_count = virament_item.process.workflow.step_set.count()
        if len(virament_item.process.approval_set.all()) == len(virament_item.process.workflow.step_set.all()):
            approve_now = True

        try:
            newStep = Step.objects.get(
                step=next_step,
                workflow=virament_item.process.workflow,
                approver__in=user_roles
            )

            if virement_role == "pass":

                if newStep and request.user.section == virament_item.section and next_step == 1:
                    approvalForm = ApprovalForm
                    to = newStep.to
                    print(virement_role)
                    if newStep.step == len(virament_item.process.workflow.step_set.all()):
                        clear = True
                    if newStep.step == len(virament_item.process.workflow.step_set.all()) - 1:
                        clear_minus = True
                    print(clear)
                elif newStep:
                    approvalForm = ApprovalForm
                    to = newStep.to
            else:
                approvalForm = ApprovalForm
                to = newStep.to
                print(virement_role)
                print(approve_now)
                if approve_now:
                    if newStep.step == len(virament_item.process.workflow.step_set.all()):
                        clear = True
                    if newStep.step == len(virament_item.process.workflow.step_set.all()) - 1:
                        clear_minus = True
                print(clear)
        except Step.DoesNotExist:
            pass

        # Independent clear_minus computation: if the next required step is the final one,
        # then we are just before GM (or final approver) and should notify them.
        if next_step == steps_count:
            clear_minus = True

    print(approve_now)
    if approve_now:
        balance_before_from = "Actioned"
        balance_before_to = "Actioned"
        balance_after_from = "Actioned"
        balance_after_to = "Actioned"

        # Enhanced budget calculations with proper error handling
        try:
            with transaction.atomic():
                # Lock budgets to prevent concurrent modifications
                fbudget = AssetBudget.objects.select_for_update().get(budget_id=virament_item.from_budget.budget_id)
                tbudget = AssetBudget.objects.select_for_update().get(budget_id=virament_item.to_budget.budget_id)
                
                print("virament: ", virament_item.virament_id)
                transaction_obj = Transactions.objects.filter(virament_id=str(virament_item.virament_id)).first()
                
                if not transaction_obj:
                    logger.error(f"No transaction found for virament {virament_item.virament_id}")
                    messages.error(request, "Transaction record not found.")
                    return render(request, 'finance/ace2/virament_detail.html', {
                        'virament': virament_item,
                        'statements': statements,
                        'approved_steps': approved_steps,
                        'error': 'Transaction record missing'
                    })
                
                print("transaction: ", str(transaction_obj.approval_status))

                # Validate available balance before processing (considering to_be_withdrawn)
                if virament_item.amount > fbudget.available_balance:
                    logger.error(f"Insufficient available balance for virament {virament_item.virament_id}: "
                               f"Required {virament_item.amount}, Available {fbudget.available_balance} "
                               f"(Balance: {fbudget.balance}, To be withdrawn: {fbudget.to_be_withdrawn or 0})")
                    messages.error(request, 
                        f"Insufficient available balance in source budget. "
                        f"Available: {fbudget.available_balance:,.2f} "
                        f"(Balance: {fbudget.balance:,.2f}, "
                        f"To be withdrawn: {fbudget.to_be_withdrawn or 0:,.2f}), "
                        f"Required: {virament_item.amount:,.2f}")
                    return render(request, 'finance/ace2/virament_detail.html', {
                        'virament': virament_item,
                        'statements': statements,
                        'approved_steps': approved_steps,
                        'balance_before_to': balance_before_to,
                        'balance_after_to': balance_after_to,
                        'balance_before_from': balance_before_from,
                        'balance_after_from': balance_after_from,
                        'error': 'Insufficient available balance'
                    })

                if transaction_obj.approval_status != "approved by General Manager" and virement_role == "approve":
                    # Update source budget - remove from to_be_withdrawn and deduct from balance
                    fbudget.balance = fbudget.balance - virament_item.amount
                    fbudget.withdrawal_date = date.today()
                    fbudget.withdrawn = (fbudget.withdrawn or 0) + virament_item.amount
                    
                    # Remove from to_be_withdrawn since it's now actually withdrawn
                    if fbudget.to_be_withdrawn is not None and fbudget.to_be_withdrawn >= virament_item.amount:
                        fbudget.to_be_withdrawn = fbudget.to_be_withdrawn - virament_item.amount
                    else:
                        logger.warning(f"to_be_withdrawn ({fbudget.to_be_withdrawn}) less than virement amount ({virament_item.amount}) for budget {fbudget.budget_id}")
                        fbudget.to_be_withdrawn = max(0, (fbudget.to_be_withdrawn or 0) - virament_item.amount)
                    
                    fbudget.save()

                    # Update destination budget
                    tbudget.balance = tbudget.balance + virament_item.amount
                    tbudget.allocated = (tbudget.allocated or 0) + virament_item.amount
                    tbudget.save()

                    # Update transaction status
                    transaction_obj.approval_status = "approved by General Manager"
                    transaction_obj.save()
                    
                    logger.info(f"Virament {virament_item.virament_id} approved successfully. "
                              f"Transferred {virament_item.amount} from {fbudget.budget_name} to {tbudget.budget_name}")
                    messages.success(request, f"Virament approved successfully. Funds transferred.")
                    
                    print("transaction: ", str(transaction_obj.approval_status))

                    # Notify requester about final approval
                    try:
                        requester = virament_item.requested_by
                        if requester:
                            msg = (
                                f"Your virement {virament_item.virament_id} has been approved by the General Manager"
                            )
                            url = reverse('Ace:virament_detail', args=[virament_item.virament_id])
                            notify_user(requester, msg, "VIREMENT", url, str(virament_item.virament_id), request)
                    except Exception as _e:
                        logger.warning(f"Failed to send virement approval notification for {virament_item.virament_id}: {_e}")
                
        except AssetBudget.DoesNotExist as e:
            logger.error(f"Budget not found for virament {virament_item.virament_id}: {e}")
            messages.error(request, "Budget not found. Please contact support.")
            return render(request, 'finance/ace2/virament_detail.html', {
                'virament': virament_item,
                'statements': statements,
                'approved_steps': approved_steps,
                'error': 'Budget not found'
            })
        except Exception as e:
            logger.error(f"Error processing virament approval {virament_item.virament_id}: {e}")
            messages.error(request, "Error processing approval. Please try again.")
            return render(request, 'finance/ace2/virament_detail.html', {
                'virament': virament_item,
                'statements': statements,
                'approved_steps': approved_steps,
                'error': str(e)
            })

    # ace_quantity = range(virament_item.quantity)
    approved_steps = virament_item.process.approval_set.all().values_list('step__step', flat=True)

    # If item is about to reach GM (clear_minus), notify GM their action is needed next
    if clear_minus:
        try:
            gm_username = find_virement_general_manager(request, virament_item.region)
            if gm_username:
                gm = UserProfile.objects.filter(username=gm_username).first()
                if gm:
                    msg = f"Virement {virament_item.virament_id} requires your final approval"
                    url = reverse('Ace:virament_detail', args=[virament_item.virament_id])
                    notify_user(gm, msg, "VIREMENT", url, str(virament_item.virament_id), request)
        except Exception as _e:
            logger.warning(f"Failed to send GM pending virement notification for {virament_item.virament_id}: {_e}")
    
    # Handle rejected virements - release reserved funds
    if approval_status == "Rejected":
        try:
            # Check if transaction needs to be marked as rejected
            transaction_obj = Transactions.objects.filter(virament_id=str(virament_item.virament_id)).first()
            if transaction_obj and transaction_obj.approval_status != "Rejected":
                transaction_obj.approval_status = "Rejected"
                transaction_obj.save()
                
                # Release reserved amount from to_be_withdrawn
                if virament_item.release_reserved_amount():
                    logger.info(f"Released reserved amount for rejected virement {virament_item.virament_id}")
                    messages.info(request, "Virement rejected. Reserved funds have been released.")
                else:
                    logger.warning(f"Failed to release reserved amount for rejected virement {virament_item.virament_id}")

                # Notify requester about rejection
                try:
                    requester = virament_item.requested_by
                    if requester:
                        msg = f"Your virement {virament_item.virament_id} has been rejected. Reserved funds have been released."
                        url = reverse('Ace:virament_detail', args=[virament_item.virament_id])
                        notify_user(requester, msg, "VIREMENT", url, str(virament_item.virament_id), request)
                except Exception as _e:
                    logger.warning(f"Failed to send virement rejection notification for {virament_item.virament_id}: {_e}")
        except Exception as e:
            logger.error(f"Error handling rejected virement {virament_item.virament_id}: {e}")

    return render(request, 'finance/ace2/virament_detail.html', {'virament': virament_item,
                                                                 'statements': statements,
                                                                 'approved_steps': approved_steps,
                                                                 'approvalForm': approvalForm,
                                                                 'to': to,
                                                                 'balance_before_to': balance_before_to,
                                                                 'balance_after_to': balance_after_to,
                                                                 'balance_before_from': balance_before_from,
                                                                 'balance_after_from': balance_after_from})

@login_required
def view_all_viraments(request):
    user_profile = UserProfile.objects.filter(id=request.user.id).first()
    if not user_profile.roles.filter(application="virement").exists():
        return HttpResponseForbidden("You are not authorized to view viraments.")
    region = user_profile.region
    viraments = Asset_budget_Virament.objects.filter(region=region).order_by('-date_created')
    return render(request,
                  'finance/ace2/view_all_viraments.html',
                  {'aces': viraments})


@login_required
def viraments_awaiting_my_action(request):
    """
    Show virements awaiting the user's action - mirrors ACE awaiting my action logic but uses virement roles
    """
    viraments_to_process = []
    user_roles = get_user_roles_qs(request.user)

    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    
    if not user_profile:
        messages.error(request, "User profile not found. Please contact administrator.")
        return render(request, 'finance/ace2/view_all_viraments.html', {
            'aces': [],
            'virement_role': 'none',
            'requester': 'create',
            'error_message': 'User profile not found'
        })

    # Get user's region and section
    try:
        region = Regions.objects.filter(id=user_profile.region.id).first()
        section = Sections.objects.filter(section=user_profile.section).first()
    except AttributeError:
        messages.error(request, "User profile is incomplete. Missing region or section information.")
        return render(request, 'finance/ace2/view_all_viraments.html', {
            'aces': [],
            'virement_role': 'none', 
            'requester': 'create',
            'error_message': 'Incomplete user profile'
        })

    # Determine user's virement role
    custom_user_roles = {"virement": {}}
    roles_ = user_profile.roles.all()
    virement_role = None
    
    try:
        for _role in roles_:
            role = Roles.objects.filter(id=_role.id).first()
            if role and role.application == "virement":
                custom_user_roles["virement"] = role.role
                virement_role = str(custom_user_roles["virement"])
                break
        
        if virement_role is None:
            messages.warning(request, "You don't have a virement role assigned. Please contact administrator for access.")
            return render(request, 'finance/ace2/view_all_viraments.html', {
                'aces': [],
                'virement_role': 'none',
                'requester': 'create',
                'error_message': 'No virement role assigned'
            })
            
    except Exception as e:
        messages.error(request, f"Error determining user role: {str(e)}")
        return render(request, 'finance/ace2/view_all_viraments.html', {
            'aces': [],
            'virement_role': 'none',
            'requester': 'create',
            'error_message': 'Role determination error'
        })

    requester = "create"
    print("virement role:", virement_role)

    # Apply section filtering logic similar to ACE - "pass" role sees only their section
    if virement_role == "pass":
        # Section heads only see virements from their own section (like ACE logic)
        for virement in Asset_budget_Virament.objects.filter(section=section, region=region).order_by('-date_created'):
            process = virement.process
            
            # Skip if process is None
            if not process:
                continue
            
            # Skip if any approval is "Rejected" (like ACE logic)
            if process.approval_set.filter(approved="Rejected").exists():
                continue

            # Only show if the user is the correct approver for the next step
            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
            else:
                current_step = 0

            next_step = current_step + 1
            workflow = process.workflow
            step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()
            
            if step:
                viraments_to_process.append(virement)
    else:
        # Other roles see region-wide virements (like ACE logic)
        for virement in Asset_budget_Virament.objects.filter(region=region).order_by('-date_created'):
            process = virement.process
            
            # Skip if process is None
            if not process:
                continue
                
            # Skip if any approval is "Rejected" (like ACE logic)
            if process.approval_set.filter(approved="Rejected").exists():
                continue

            # Only show if the user is the correct approver for the next step
            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
            else:
                current_step = 0

            next_step = current_step + 1
            workflow = process.workflow
            step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()
            
            if step:
                viraments_to_process.append(virement)

    return render(request, 'finance/ace2/view_all_viraments.html', {'aces': viraments_to_process,
                                                                    'virement_role': virement_role,
                                                                    'requester': requester})


@login_required
def view_all_transactions(request):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    region = Regions.objects.filter(id=user_profile.region.id).first()
    transactions = Transactions.objects.filter(region=region)
    return render(request, 'finance/ace2/view_all_transactions.html', {'transactions': transactions})


@login_required
def transactions_for_budget(request, budget_id):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    # region = Regions.objects.filter(id=user_profile.region.id).first()
    transactions = Transactions.objects.filter(budget_id=budget_id)
    if not transactions:
        messages.error(request, 'No transactions found for this budget.')
        return redirect('Ace:list_budgets')
    else:
        messages.success(request, 'Transactions found for this budget.')
        print("transactions:", transactions)
    
    return render(request, 'finance/ace2/view_all_transactions.html', {'transactions': transactions})


@login_required
def ace_reports(request):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    ace_report_form = AceReportForm(user=user_profile)
    current_year = timezone.now().year

    if request.method == 'POST':
        ace_report_form = AceReportForm(request.POST)
        if ace_report_form.is_valid():
            start_date = ace_report_form.cleaned_data['start_date']
            end_date = ace_report_form.cleaned_data['end_date']
            region = ace_report_form.cleaned_data['region']
            budget = ace_report_form.cleaned_data['budget_id']

            # Get budget summary data for graphical display
            budget_summary = []
            total_allocated = 0
            total_utilized = 0
            total_pending = 0
            total_available = 0
            
            if budget:  # Specific budget selected
                report = ace_report_form.save(commit=False)
                report.start_date = start_date
                report.end_date = end_date
                report.region = region
                report.budget_id = budget
                report.save()
                
                # Filter ACEs for this budget
                aces = Ace2.objects.filter(
                    date_created__range=[start_date, end_date],
                    region=region,
                    budget_id=budget
                )
                
                # Get ACE count and average amount for this budget
                ace_count = aces.count()
                total_ace_amount = aces.aggregate(total=Sum('amount'))['total'] or 0
                avg_ace_amount = total_ace_amount / ace_count if ace_count > 0 else 0
                
                # Single budget summary
                utilization_percentage = (budget.withdrawn / budget.allocated * 100) if budget.allocated > 0 else 0
                pending_percentage = (budget.to_be_withdrawn / budget.allocated * 100) if budget.allocated > 0 else 0
                available_percentage = (budget.balance / budget.allocated * 100) if budget.allocated > 0 else 0
                total_commitment_percentage = utilization_percentage + pending_percentage
                
                budget_summary.append({
                    'budget': budget,
                    'allocated': budget.allocated,
                    'withdrawn': budget.withdrawn,
                    'to_be_withdrawn': budget.to_be_withdrawn,
                    'balance': budget.balance,
                    'utilization_percentage': utilization_percentage,
                    'pending_percentage': pending_percentage,
                    'available_percentage': available_percentage,
                    'total_commitment_percentage': total_commitment_percentage,
                    'total_committed': budget.withdrawn + budget.to_be_withdrawn,
                    'ace_count': ace_count,
                    'avg_ace_amount': avg_ace_amount,
                    'health_status': 'good' if budget.balance > (budget.allocated * 0.3) else 'warning' if budget.balance > (budget.allocated * 0.1) else 'critical'
                })
                
                # Calculate totals
                total_allocated = budget.allocated or 0
                total_utilized = budget.withdrawn or 0
                total_pending = budget.to_be_withdrawn or 0
                total_available = budget.balance or 0
                
                return render(request, 'finance/ace2/ace_reports.html', {
                    'aces': aces, 
                    'report': report,
                    'budget_summary': budget_summary,
                    'current_year': current_year,
                    'total_allocated': total_allocated,
                    'total_utilized': total_utilized,
                    'total_pending': total_pending,
                    'total_available': total_available,
                })
            else:  # All Budgets selected
                # Do NOT save the report, just filter ACEs for all budgets
                aces = Ace2.objects.filter(
                    date_created__range=[start_date, end_date],
                    region=region
                )
                
                # Multiple budgets summary for current year only
                budgets = AssetBudget.objects.filter(region=region, period=current_year).order_by('-allocated')
                for budget_item in budgets:
                    if budget_item.allocated > 0:  # Only include budgets with allocation
                        # Get ACE count and average amount for this budget
                        budget_aces = aces.filter(budget_id=budget_item)
                        ace_count = budget_aces.count()
                        total_ace_amount = budget_aces.aggregate(total=Sum('amount'))['total'] or 0
                        avg_ace_amount = total_ace_amount / ace_count if ace_count > 0 else 0
                        
                        # Calculate percentages
                        utilization_percentage = (budget_item.withdrawn / budget_item.allocated * 100) if budget_item.allocated > 0 else 0
                        pending_percentage = (budget_item.to_be_withdrawn / budget_item.allocated * 100) if budget_item.allocated > 0 else 0
                        available_percentage = (budget_item.balance / budget_item.allocated * 100) if budget_item.allocated > 0 else 0
                        total_commitment_percentage = utilization_percentage + pending_percentage
                        
                        budget_summary.append({
                            'budget': budget_item,
                            'allocated': budget_item.allocated,
                            'withdrawn': budget_item.withdrawn,
                            'to_be_withdrawn': budget_item.to_be_withdrawn,
                            'balance': budget_item.balance,
                            'utilization_percentage': utilization_percentage,
                            'pending_percentage': pending_percentage,
                            'available_percentage': available_percentage,
                            'total_commitment_percentage': total_commitment_percentage,
                            'total_committed': budget_item.withdrawn + budget_item.to_be_withdrawn,
                            'ace_count': ace_count,
                            'avg_ace_amount': avg_ace_amount,
                            'health_status': 'good' if budget_item.balance > (budget_item.allocated * 0.3) else 'warning' if budget_item.balance > (budget_item.allocated * 0.1) else 'critical'
                        })
                        
                        # Add to totals
                        total_allocated += budget_item.allocated or 0
                        total_utilized += budget_item.withdrawn or 0
                        total_pending += budget_item.to_be_withdrawn or 0
                        total_available += budget_item.balance or 0
                
                return render(request, 'finance/ace2/ace_reports.html', {
                    'aces': aces, 
                    'report': None,
                    'budget_summary': budget_summary,
                    'current_year': current_year,
                    'total_allocated': total_allocated,
                    'total_utilized': total_utilized,
                    'total_pending': total_pending,
                    'total_available': total_available,
                    'start_date': start_date,
                    'end_date': end_date,
                    'region': region
                })
    
    # Default view - show current year budget summary for user's region
    region = user_profile.region
    budgets = AssetBudget.objects.filter(region=region, period=current_year).order_by('-allocated')
    budget_summary = []
    total_allocated = 0
    total_utilized = 0
    total_pending = 0
    total_available = 0
    
    for budget_item in budgets:
        if budget_item.allocated > 0:  # Only include budgets with allocation
            # Get ACE count and average amount for this budget (current year)
            budget_aces = Ace2.objects.filter(
                budget_id=budget_item,
                date_created__year=current_year
            )
            ace_count = budget_aces.count()
            total_ace_amount = budget_aces.aggregate(total=Sum('amount'))['total'] or 0
            avg_ace_amount = total_ace_amount / ace_count if ace_count > 0 else 0
            
            # Calculate percentages
            utilization_percentage = (budget_item.withdrawn / budget_item.allocated * 100) if budget_item.allocated > 0 else 0
            pending_percentage = (budget_item.to_be_withdrawn / budget_item.allocated * 100) if budget_item.allocated > 0 else 0
            available_percentage = (budget_item.balance / budget_item.allocated * 100) if budget_item.allocated > 0 else 0
            total_commitment_percentage = utilization_percentage + pending_percentage
            
            budget_summary.append({
                'budget': budget_item,
                'allocated': budget_item.allocated,
                'withdrawn': budget_item.withdrawn,
                'to_be_withdrawn': budget_item.to_be_withdrawn,
                'balance': budget_item.balance,
                'utilization_percentage': utilization_percentage,
                'pending_percentage': pending_percentage,
                'available_percentage': available_percentage,
                'total_commitment_percentage': total_commitment_percentage,
                'total_committed': budget_item.withdrawn + budget_item.to_be_withdrawn,
                'ace_count': ace_count,
                'avg_ace_amount': avg_ace_amount,
                'health_status': 'good' if budget_item.balance > (budget_item.allocated * 0.3) else 'warning' if budget_item.balance > (budget_item.allocated * 0.1) else 'critical'
            })
            
            # Add to totals
            total_allocated += budget_item.allocated or 0
            total_utilized += budget_item.withdrawn or 0
            total_pending += budget_item.to_be_withdrawn or 0
            total_available += budget_item.balance or 0

    return render(request, 'finance/ace2/ace_create_reports.html', {
        'ace_report_form': ace_report_form,
        'budget_summary': budget_summary,
        'current_year': current_year,
        'total_allocated': total_allocated,
        'total_utilized': total_utilized,
        'total_pending': total_pending,
        'total_available': total_available,
        'default_view': True
    })


@login_required
def ace_report_detail_pdf(request, report_id2=None):
    if report_id2:
        report = get_object_or_404(AceReport, report_id2=report_id2)
        # Only filter by budget if a specific budget is selected
        if report.budget_id:
            aces = Ace2.objects.filter(
                date_created__range=[report.start_date, report.end_date],
                region=report.region,
                budget_id=report.budget_id
            )
        else:
            aces = Ace2.objects.filter(
                date_created__range=[report.start_date, report.end_date],
                region=report.region
            )
        template = loader.get_template('finance/ace2/ace_reports.html')
        context = {
            'aces': aces,
            'report': report,
            'request': request
        }
        html = template.render(context, request)
        pdf = HTML(string=html).write_pdf()
        return HttpResponse(pdf, content_type='application/pdf')
    else:
        # Get parameters from GET
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
        region_id = request.GET.get('region')
        aces = Ace2.objects.filter(
            date_created__range=[start_date, end_date],
            region=region_id
        )
        template = loader.get_template('finance/ace2/ace_reports.html')
        context = {
            'aces': aces,
            'request': request
        }
        html = template.render(context, request)
        pdf = HTML(string=html).write_pdf()
        return HttpResponse(pdf, content_type='application/pdf')


@login_required
def ace_report_detail_excel(request, report_id2):
    report = get_object_or_404(AceReport, report_id2=report_id2)
    region_obj = get_object_or_404(Regions, id=report.region.id)
    # Only filter by budget if a specific budget is selected
    if report.budget_id:
        aces = Ace2.objects.filter(
            region=region_obj,
            budget_id=report.budget_id,
            date_created__range=[report.start_date, report.end_date]
        )
    else:
        aces = Ace2.objects.filter(
            region=region_obj,
            date_created__range=[report.start_date, report.end_date]
        )
    print("report start date", report.start_date)
    print("report end date", report.end_date)
    print("report region", report.region)
    print('region obj', region_obj)
    print("report budget", report.budget_id.budget_id if report.budget_id else 'All budgets')
    if report.budget_id and region_obj:

        response = HttpResponse(content_type='application/ms-excel')
        response['Content-Disposition'] = 'attachment; filename="ace_report.xlsx"'

        wb = Workbook()
        ws = wb.active

        ws.append([
            ace.Ace_id2,
            ace.details_of_expenditure,
            ace.requested_by.get_full_name() if ace.requested_by else '',
            section_name,
            ace.date_created.strftime('%Y-%m-%d') if ace.date_created else '',
            ace.budget_id.budget_name if ace.budget_id else '',
            ace.amount,
            transaction.approval_status if transaction else '',
            approval_status,
            actioned_by
        ])

        ws.append(
            ['Ace_id', 'details_of_expenditure', 'requested_by', 'section', 'Date', 'Budget', 'Amount',
             'transaction_status', 'approval_status', 'actioned_by'
            ])

        for ace in aces:
            transaction = Transactions.objects.filter(Ace_id2=ace).first()
            latest_approval = ace.process.approval_set.last() if ace.process and ace.process.approval_set.exists() else None
            approval_status = latest_approval.approved if latest_approval else ''
            actioned_by = latest_approval.user.get_full_name() if latest_approval and latest_approval.user else ''
            print(approval_status, actioned_by)
            if ace.section:
                try:
                    section_name = ace.section.section
                except AttributeError:
                    section_name = ""
            else:
                section_name = ""

            print(section_name, 'section name')

            ws.append([
                ace.Ace_id2,
                ace.details_of_expenditure,
                ace.requested_by.get_full_name() if ace.requested_by else '',
                section_name,
                ace.date_created.strftime('%Y-%m-%d') if ace.date_created else '',
                ace.budget_id.budget_name if ace.budget_id else '',
                ace.amount,
                transaction.approval_status if transaction else '',
                approval_status,
                actioned_by
            ])
        wb.save(response)
        return response
    else:
        messages.error(request, "error")

# # @login_required
def find_ace_section_head(request, section):
    all_users = UserProfile.objects.filter(section=section).all()
    # section_heads = UserProfile.objects.filter(section=section, role='section_head')
    if all_users:
        for user_profile in all_users:
            user_groups = user_profile.groups.values_list('name', flat=True)

            custom_user_roles = {
                "ace": {},
            }

            roles_ = user_profile.roles.all()
            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()

                if role.application == "ace":
                    custom_user_roles["ace"] = role.role
    ace_role = str(custom_user_roles["ace"])
    if ace_role == "pass":
        userp = 'sh'
        sh = user_profile.username
        if sh:
            return sh

    # Return None if no section head is found
    return None

# @login_required
def find_general_manager(request, region):
    all_users = UserProfile.objects.filter(region=region).all()
    # section_heads = UserProfile.objects.filter(section=section, role='section_head')
    if all_users:

        for user_profile in all_users:
            user_groups = user_profile.groups.values_list('name', flat=True)

            custom_user_roles = {
                "ace": {},
            }

            roles_ = user_profile.roles.all()
            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()

                if role.application == "ace":
                    custom_user_roles["ace"] = role.role
    ace_role = str(custom_user_roles["ace"])
    if ace_role == "approve":
        userp = 'gm'
        gm = user_profile.username
        if gm:
            return gm


        else:
            print("no users found")

# @login_required
def find_virement_section_head(request, section):
    """Find section head for virement application in a section (role 'pass')."""
    all_users = UserProfile.objects.filter(section=section).all()
    if all_users:
        for user_profile in all_users:
            custom_user_roles = {"virement": {}}
            roles_ = user_profile.roles.all()
            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()
                if role.application == "virement":
                    custom_user_roles["virement"] = role.role
            v_role = str(custom_user_roles["virement"])
            if v_role == "pass":
                sh = user_profile.username
                if sh:
                    return sh
    return None

# @login_required
def find_virement_general_manager(request, region):
    """Find GM for virement application in a region (role 'approve')."""
    all_users = UserProfile.objects.filter(region=region).all()
    if all_users:
        for user_profile in all_users:
            custom_user_roles = {"virement": {}}
            roles_ = user_profile.roles.all()
            for _role in roles_:
                role = Roles.objects.filter(id=_role.id).first()
                if role.application == "virement":
                    custom_user_roles["virement"] = role.role
            v_role = str(custom_user_roles["virement"])
            if v_role == "approve":
                gm = user_profile.username
                if gm:
                    return gm
    return None

# transactions on a budget
@login_required
def transactions_view(request, budget):
    transactions = Transactions.objects.filter(budget_id=budget)
    #return an view with an html table of transactions
    return render(request, 'finance/ace2/view_all_transactions.html', {'transactions': transactions})


@login_required
def reports_view(request):
    reports = Report.objects.all()
    return render(request, 'reports/reports_index.html', {'reports': reports})


@login_required
def generate_report(request):
    if request.method == 'POST':
        attribute = request.POST.get('attribute')
        value = request.POST.get('value')
        aces = Ace2.objects.filter(**{attribute: value})
        return render(request, 'reports/generate_report.html', {'aces': aces, 'attribute': attribute, 'value': value})
    return render(request, 'reports/generate_report.html')


@login_required
def download_csv(request):
    attribute = request.GET.get('attribute')
    value = request.GET.get('value')
    aces = Ace2.objects.filter(**{attribute: value})
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="report.csv"'
    writer = csv.writer(response)
    writer.writerow(
        ['Ace_id', 'details_of_expenditure', 'requested_by', 'section', 'Date', 'Budget', 'Amount', 'approval_status'])
    for ace in aces:
        transaction = Transactions.objects.filter(Ace_id2=ace).first()
        writer.writerow([
            ace.Ace_id2,
            ace.details_of_expenditure,
            ace.requested_by.get_full_name() if ace.requested_by else '',
            ace.section.section if ace.section else '',
            ace.date_created.strftime('%Y-%m-%d') if ace.date_created else '',
            ace.budget_id.budget_name if ace.budget_id else '',
            ace.amount,
            transaction.approval_status if transaction else ''
        ])
    return response


@login_required
def my_actioned_items(request):
    """
    Show ACE items the current user has actioned (approved/rejected), sorted by action date (most recent first).
    """
    username = request.user.username
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    region = Regions.objects.filter(id=user_profile.region.id).first()
    
    # Get user role
    custom_user_roles = {"ace": {}}
    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()
        if role.application == "ace":
            custom_user_roles["ace"] = role.role
            ace_role = str(custom_user_roles["ace"])
            print("ace role", ace_role)
            break
    
    # Get all ACEs where the current user has an approval in the process
    actioned_approvals = []
    all_aces = Ace2.objects.filter(region=region)
    for ace in all_aces:
        process = ace.process
        if process and process.approval_set.exists():
            approvals = process.approval_set.filter(user=request.user)
            for approval in approvals:
                actioned_approvals.append((approval, ace))
    
    # Sort by approval date (replace 'date' with your actual field, e.g., 'timestamp', 'date_approved')
    actioned_approvals.sort(key=lambda x: x[0].approved_at, reverse=True)
    actioned_aces = [ace for approval, ace in actioned_approvals]

    requester = "create"  # Used in template for role checks
    
    return render(request, 'finance/ace2/my_actioned_items.html', {
        'aces': actioned_aces,
        'title': 'My Actioned Items',
        'ace_role': ace_role,
        'requester': requester
    })


@login_required
def notify_pending_gm_approvals(request):
    """
    Sends notifications to general managers about ACE items awaiting their approval
    in their specific region only.
    """
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    notification_count = 0
    
    # Get all regions
    regions = Regions.objects.all()
    
    for region in regions:
        # Find general managers for this specific region (users with "approve" role for ACE)
        gm_users = UserProfile.objects.filter(
            region=region,
            roles__application="ace",
            roles__role="approve"
        ).all()
        
        if not gm_users:
            continue
            
        # Find ACE items in THIS REGION ONLY that are at the final approval step
        pending_aces = []
        for ace in Ace2.objects.filter(region=region):
            process = ace.process
            
            # Skip items without process or already rejected
            if not process or process.approval_set.filter(approved="Rejected").exists():
                continue
                
            if process.approval_set.exists():
                latest_approval = process.approval_set.last()
                current_step = latest_approval.step.step
                
                # If we're at the step before the last step, item is pending GM approval
                if current_step == len(process.workflow.step_set.all()) - 1:
                    pending_aces.append(ace)
        
        # Notify each GM about pending items IN THEIR REGION ONLY
        if pending_aces:
            for gm in gm_users:
                count = len(pending_aces)
                notification_count += count
                
                # Send a summary notification
                msg = f"You have {count} ACE items awaiting your approval in {region.region}"
                url = "/ace/awaiting_my_action/"
                notify_user(gm, msg, "ACE", url, f"gm_summary_{region.id}", request)
                
                # Optional: Send individual notifications for each item
                for ace in pending_aces:
                    item_msg = f"ACE {ace.Ace_id2} requires your final approval"
                    item_url = f"/ace/ace_detail/{ace.Ace_id2}"
                    notify_user(gm, item_msg, "ACE", item_url, ace.Ace_id2, request)
    
    if notification_count > 0:
        sweetify.success(request, f"Sent notifications for {notification_count} pending ACE items to general managers")
    else:
        sweetify.info(request, "No pending ACE items requiring general manager approval found")
    
    return redirect('/ace/aces')

@login_required
def asset_budget_report(request, budget_id):
    budget = get_object_or_404(AssetBudget, pk=budget_id)
    # All ACEs that used this budget
    aces = Ace2.objects.filter(budget_id=budget).order_by('-date_created')
    # Total amount used by ACEs
    total_used = aces.aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Calculate budget statistics
    allocated = budget.allocated or 0
    withdrawn = budget.withdrawn or 0
    awaiting_sanctioning = budget.awaiting_sanctioning or 0
    balance = budget.balance or 0
    
    # Calculate utilization rate
    utilization_rate = (withdrawn / allocated * 100) if allocated > 0 else 0
    
    # Get ACE status counts
    approved_count = 0
    pending_count = 0
    rejected_count = 0
    unknown_count = 0
    
    for ace in aces:
        if ace.process and ace.process.approval_set.last():
            status = ace.process.approval_set.last().approved
            if status == "Approved":
                approved_count += 1
            elif status == "Rejected":
                rejected_count += 1
            else:
                pending_count += 1
        else:
            unknown_count += 1
    
    # Get monthly usage data (last 6 months)
    from datetime import datetime, timedelta
    from django.db.models import Sum, Count
    from django.db.models.functions import TruncMonth
    
    end_date = datetime.now()
    start_date = end_date - timedelta(days=180)  # 6 months ago
    
    monthly_usage = aces.filter(
        date_created__gte=start_date,
        date_created__lte=end_date
    ).annotate(
        month=TruncMonth('date_created')
    ).values('month').annotate(
        total_amount=Sum('amount'),
        ace_count=Count('Ace_id')
    ).order_by('month')
    
    # Format monthly data for chart
    monthly_data = {
        'labels': [],
        'amounts': [],
        'counts': []
    }
    
    for item in monthly_usage:
        monthly_data['labels'].append(item['month'].strftime('%b %Y'))
        monthly_data['amounts'].append(float(item['total_amount'] or 0))
        monthly_data['counts'].append(item['ace_count'])
    
    # Calculate additional metrics
    avg_ace_amount = total_used / aces.count() if aces.count() > 0 else 0
    
    context = {
        'budget': budget,
        'aces': aces,
        'total_used': total_used,
        'allocated': allocated,
        'withdrawn': withdrawn,
        'balance': balance,
        'awaiting_sanctioning': awaiting_sanctioning,
        'monthly_data': monthly_data,
        'avg_ace_amount': avg_ace_amount,
        'total_aces': aces.count(),
    }
    return render(request, 'finance/ace2/asset_budget_report.html', context)


@login_required
def asset_budget_report_pdf(request, budget_id):
    """Export asset budget report to PDF"""
    budget = get_object_or_404(AssetBudget, pk=budget_id)
    aces = Ace2.objects.filter(budget_id=budget).order_by('-date_created')
    total_used = aces.aggregate(total=models.Sum('amount'))['total'] or 0
    
    # Calculate utilization rate
    utilization_rate = (budget.withdrawn / budget.allocated * 100) if budget.allocated > 0 else 0
    
    template = loader.get_template('finance/ace2/asset_budget_report_pdf.html')
    context = {
        'budget': budget,
        'aces': aces,
        'total_used': total_used,
        'utilization_rate': round(utilization_rate, 2),
        'request': request
    }
    html = template.render(context, request)
    
    from weasyprint import HTML
    pdf = HTML(string=html).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="asset_budget_report_{budget.budget_id}.pdf"'
    return response


@login_required
def asset_budget_report_excel(request, budget_id):
    """Export asset budget report to Excel"""
    budget = get_object_or_404(AssetBudget, pk=budget_id)
    aces = Ace2.objects.filter(budget_id=budget).order_by('-date_created')
    total_used = aces.aggregate(total=models.Sum('amount'))['total'] or 0
    
    from openpyxl import Workbook
    from openpyxl.styles import Font, Alignment, PatternFill
    from openpyxl.utils import get_column_letter
    
    wb = Workbook()
    ws = wb.active
    ws.title = "Asset Budget Report"
    
    # Header styling
    header_font = Font(bold=True, size=12)
    header_fill = PatternFill(start_color="366092", end_color="366092", fill_type="solid")
    center_alignment = Alignment(horizontal="center", vertical="center")
    
    # Budget Summary Section
    ws.merge_cells('A1:H1')
    ws['A1'] = f"Asset Budget Report - {budget.budget_name}"
    ws['A1'].font = Font(bold=True, size=16)
    ws['A1'].alignment = center_alignment
    
    ws['A3'] = "Budget Summary"
    ws['A3'].font = header_font
    
    ws['A4'] = "Allocated"
    ws['B4'] = float(budget.allocated or 0)
    ws['A5'] = "Withdrawn"
    ws['B5'] = float(budget.withdrawn or 0)
    ws['A6'] = "Balance"
    ws['B6'] = float(budget.balance or 0)
    ws['A7'] = "Awaiting Sanctioning"
    ws['B7'] = float(budget.awaiting_sanctioning or 0)
    ws['A8'] = "Total Used by ACEs"
    ws['B8'] = float(total_used)
    ws['A9'] = "Utilization Rate (%)"
    ws['B9'] = round((budget.withdrawn / budget.allocated * 100) if budget.allocated > 0 else 0, 2)
    
    # ACE Details Section
    ws['A12'] = "ACE Details"
    ws['A12'].font = header_font
    
    # Headers
    headers = ['ACE ID', 'Details', 'Amount', 'Requested By', 'Date Created', 'Status', 'Section', 'Region']
    for col_num, header in enumerate(headers, 1):
        cell = ws.cell(row=13, column=col_num, value=header)
        cell.font = header_font
        cell.fill = header_fill
        cell.alignment = center_alignment
    
    # Data rows
    for row_num, ace in enumerate(aces, 14):
        ws.cell(row=row_num, column=1, value=ace.Ace_id2)
        ws.cell(row=row_num, column=2, value=ace.details_of_expenditure)
        ws.cell(row=row_num, column=3, value=float(ace.amount or 0))
        ws.cell(row=row_num, column=4, value=ace.requested_by.get_full_name())
        ws.cell(row=row_num, column=5, value=ace.date_created.strftime('%Y-%m-%d') if ace.date_created else '')
        
        # Status
        status = "-"
        if ace.process and ace.process.approval_set.last():
            status = ace.process.approval_set.last().approved
        ws.cell(row=row_num, column=6, value=status)
        
        ws.cell(row=row_num, column=7, value=str(ace.section) if ace.section else "")
        ws.cell(row=row_num, column=8, value=str(ace.region) if ace.region else "")
    
    # Auto-adjust column widths
    for col in ws.columns:
        max_length = 0
        column = col[0].column_letter
        for cell in col:
            try:
                if len(str(cell.value)) > max_length:
                    max_length = len(str(cell.value))
            except:
                pass
        adjusted_width = min(max_length + 2, 50)
        ws.column_dimensions[column].width = adjusted_width
    
    response = HttpResponse(content_type='application/vnd.openxmlformats-officedocument.spreadsheetml.sheet')
    response['Content-Disposition'] = f'attachment; filename="asset_budget_report_{budget.budget_id}.xlsx"'
    wb.save(response)
    return response



@login_required
def download_ace_quotation(request, quotation_id):
    try:
        quotation = Quotation.objects.get(pk=quotation_id)
    except Quotation.DoesNotExist:
        return HttpResponseNotFound('Attachment not found')



    response = FileResponse(quotation.quotation_file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{quotation.quotation_file.name}"'
    return response



@login_required
def monthly_usage_dashboard(request):
    
    current_year = timezone.now().year

    ace_monthly = (
        Ace2.objects
        .filter(date_created__year=current_year)
        .annotate(month=TruncMonth('date_created'))
        .values('month')
        .annotate(total_amount=Sum('amount'), count=Count('Ace_id2'))
        .order_by('month')
    )

    pettycash_monthly = (
        Pettycash.objects
        .filter(date_created__year=current_year)
        .annotate(month=TruncMonth('date_created'))
        .values('month')
        .annotate(total_amount=Sum('amount_disbursed'), count=Count('petty_id'))
        .order_by('month')
    )

    token_monthly = (
        Token.objects
        .filter(created_at__year=current_year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total_tokens=Count('id'))
        .order_by('month')
    )

    comparative_monthly = (
        ComparativeSchedules.objects
        .filter(created_at__year=current_year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(total_schedules=Count('id'))
        .order_by('month')
    )

    direct_purchase_monthly = (
        DirectPurchase.objects
        .filter(created_at__year=current_year)
        .annotate(month=TruncMonth('created_at'))
        .values('month')
        .annotate(count=Count('id'))  # Removed total_amount aggregation
        .order_by('month')
    )

    context = {
        'ace_monthly': ace_monthly,
        'pettycash_monthly': pettycash_monthly,
        'token_monthly': token_monthly,
        'comparative_monthly': comparative_monthly,
        'direct_purchase_monthly': direct_purchase_monthly,
        'current_year': current_year,
    }
    return render(request, 'finance/ace2/monthly_usage_dashboard.html', context)

@login_required
def transactions_excel_export(request):
    """Export all transactions in the user's region to Excel (excluding rejected ACEs)"""
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    region = Regions.objects.filter(id=user_profile.region.id).first()
    
    # Use select_related to avoid DoesNotExist errors and exclude rejected transactions
    transactions = Transactions.objects.filter(
        region=region
    ).exclude(
        approval_status__icontains='rejected'
    ).select_related(
        'Ace_id2', 'Ace_id2__requested_by', 'virament', 'section', 'region', 'budget'
    )
    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="transactions_report.xlsx"'
    
    wb = Workbook()
    ws = wb.active
    
    # Add header row
    ws.append([
        'Transaction ID',
        'ACE ID',
        'Virament ID',
        'Details',
        'Amount',
        'Requested By',
        'Date Created',
        'Section',
        'Section Code',
        'Region',
        'Budget',
        'Approval Status'
    ])
    
    # Add data rows
    for transaction in transactions:
        # Skip if ACE is rejected (additional check)
        if transaction.Ace_id2 and transaction.Ace_id2.process:
            if transaction.Ace_id2.process.approval_set.filter(approved="Rejected").exists():
                continue
                
        # Safe access to related objects
        try:
            section_name = transaction.section.section if transaction.section else ''
        except:
            section_name = ''
            
        try:
            section_code = transaction.section.code if transaction.section else ''
        except:
            section_code = ''
            
        try:
            region_name = transaction.region.region if transaction.region else ''
        except:
            region_name = ''
            
        try:
            budget_name = transaction.budget.budget_name if transaction.budget else ''
        except:
            budget_name = ''
            
        try:
            requested_by = transaction.Ace_id2.requested_by.get_full_name() if transaction.Ace_id2 and transaction.Ace_id2.requested_by else ''
        except:
            requested_by = ''
            
        try:
            date_created = transaction.Ace_id2.date_created.strftime('%Y-%m-%d') if transaction.Ace_id2 and transaction.Ace_id2.date_created else ''
        except:
            date_created = ''
        
        ws.append([
            transaction.transaction_id,
            transaction.Ace_id2.Ace_id2 if transaction.Ace_id2 else '',
            transaction.virament.virament_id if transaction.virament else '',
            transaction.details_of_expenditure or '',
            transaction.amount or 0,
            requested_by,
            date_created,
            section_name,
            section_code,
            region_name,
            budget_name,
            transaction.approval_status or ''
        ])
    
    wb.save(response)
    return response


@login_required
def transactions_for_budget_excel_export(request, budget_id):
    """Export transactions for a specific budget to Excel (excluding rejected ACEs)"""
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    
    # Use select_related to avoid DoesNotExist errors and exclude rejected transactions
    transactions = Transactions.objects.filter(
        budget_id=budget_id
    ).exclude(
        approval_status__icontains='rejected'
    ).select_related(
        'Ace_id2', 'Ace_id2__requested_by', 'virament', 'section', 'region', 'budget'
    )
    
    # Get budget name for filename
    budget = get_object_or_404(AssetBudget, pk=budget_id)
    # Clean filename to avoid invalid characters
    clean_budget_name = "".join(c for c in budget.budget_name if c.isalnum() or c in (' ', '-', '_')).rstrip()
    filename = f"transactions_budget_{clean_budget_name.replace(' ', '_')}.xlsx"
    
    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    wb = Workbook()
    ws = wb.active
    
    # Add header row
    ws.append([
        'Transaction ID',
        'ACE ID',
        'Virament ID',
        'Details',
        'Amount',
        'Requested By',
        'Date Created',
        'Section',
        'Section Code',
        'Region',
        'Budget',
        'Approval Status'
    ])
    
    # Add data rows
    for transaction in transactions:
        # Skip if ACE is rejected (additional check)
        if transaction.Ace_id2 and transaction.Ace_id2.process:
            if transaction.Ace_id2.process.approval_set.filter(approved="Rejected").exists():
                continue
                
        # Safe access to related objects
        try:
            section_name = transaction.section.section if transaction.section else ''
        except:
            section_name = ''
            
        try:
            section_code = transaction.section.code if transaction.section else ''
        except:
            section_code = ''
            
        try:
            region_name = transaction.region.region if transaction.region else ''
        except:
            region_name = ''
            
        try:
            budget_name = transaction.budget.budget_name if transaction.budget else ''
        except:
            budget_name = ''
            
        try:
            requested_by = transaction.Ace_id2.requested_by.get_full_name() if transaction.Ace_id2 and transaction.Ace_id2.requested_by else ''
        except:
            requested_by = ''
            
        try:
            date_created = transaction.Ace_id2.date_created.strftime('%Y-%m-%d') if transaction.Ace_id2 and transaction.Ace_id2.date_created else ''
        except:
            date_created = ''
        
        ws.append([
            transaction.transaction_id,
            transaction.Ace_id2.Ace_id2 if transaction.Ace_id2 else '',
            transaction.virament.virament_id if transaction.virament else '',
            transaction.details_of_expenditure or '',
            transaction.amount or 0,
            requested_by,
            date_created,
            section_name,
            section_code,
            region_name,
            budget_name,
            transaction.approval_status or ''
        ])
    
    wb.save(response)
    return response

@login_required
def ace_report_detail_csv(request, report_id2=None):
    """Export ACE report to CSV format"""
    if report_id2:
        report = get_object_or_404(AceReport, report_id2=report_id2)
        # Only filter by budget if a specific budget is selected
        if report.budget_id:
            aces = Ace2.objects.filter(
                region=report.region,
                budget_id=report.budget_id,
                date_created__range=[report.start_date, report.end_date]
            )
        else:
            aces = Ace2.objects.filter(
                region=report.region,
                date_created__range=[report.start_date, report.end_date]
            )
        
        filename = f"ace_report_{report.report_id2}.csv"
    else:
        # Get parameters from GET request for all budgets report
        start_date = parse_date(request.GET.get('start_date'))
        end_date = parse_date(request.GET.get('end_date'))
        region_id = request.GET.get('region')
        budget_id = request.GET.get('budget_id')
        all_budgets = request.GET.get('all_budgets')
        
        # Handle filters - build query based on provided parameters
        ace_filter = {}
        
        # Add date range filter if dates are provided
        if start_date and end_date:
            ace_filter['date_created__range'] = [start_date, end_date]
        elif start_date:
            ace_filter['date_created__gte'] = start_date
        elif end_date:
            ace_filter['date_created__lte'] = end_date
        
        # Add region filter if region is provided and not empty
        if region_id and region_id.strip():
            try:
                region = get_object_or_404(Regions, id=int(region_id))
                ace_filter['region'] = region
            except (ValueError, TypeError):
                pass  # Skip invalid region IDs
        
        # Add budget filter only if a specific budget is provided and all_budgets is not set
        if budget_id and budget_id.strip() and not all_budgets:
            try:
                from .models import AssetBudget
                budget = get_object_or_404(AssetBudget, budget_id=int(budget_id))
                ace_filter['budget_id'] = budget
            except (ValueError, TypeError):
                pass  # Skip invalid budget IDs
        # If all_budgets=1 or no budget_id specified, don't add budget filter (includes all budgets)
        
        aces = Ace2.objects.filter(**ace_filter)
        
        # Generate descriptive filename
        if all_budgets or not budget_id:
            filename = f"ace_report_all_budgets_{start_date or 'all'}_to_{end_date or 'all'}.csv"
        else:
            filename = f"ace_report_budget_{budget_id}_{start_date or 'all'}_to_{end_date or 'all'}.csv"
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="{filename}"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'ACE ID',
        'Details of Expenditure',
        'Requested By',
        'Section',
        'Date Created',
        'Budget',
        'Amount',
        'Transaction Status',
        'Approval Status',
        'Actioned By'
    ])
    
    # Write data rows
    for ace in aces:
        # Get transaction info
        transaction = Transactions.objects.filter(Ace_id2=ace).first()
        
        # Get approval info
        latest_approval = ace.process.approval_set.last() if ace.process and ace.process.approval_set.exists() else None
        approval_status = latest_approval.approved if latest_approval else ''
        actioned_by = latest_approval.user.get_full_name() if latest_approval and latest_approval.user else ''
        
        # Get section name safely
        try:
            section_name = ace.section.section if ace.section else ''
        except:
            section_name = ''
        
        writer.writerow([
            ace.Ace_id2,
            ace.details_of_expenditure,
            ace.requested_by.get_full_name() if ace.requested_by else '',
            section_name,
            ace.date_created.strftime('%Y-%m-%d') if ace.date_created else '',
            ace.budget_id.budget_name if ace.budget_id else '',
            ace.amount,
            transaction.approval_status if transaction else '',
            approval_status,
            actioned_by
        ])
    
    return response

@login_required
def export_current_year_csv(request):
    """Export current year ACE data for user's region to CSV"""
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    current_year = timezone.now().year
    
    # Get user's region
    region = user_profile.region
    
    # Filter ACEs for current year and user's region
    aces = Ace2.objects.filter(
        date_created__year=current_year,
        region=region
    ).order_by('-date_created')
    
    # Create CSV response
    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = f'attachment; filename="ace_report_{current_year}_{region.region}.csv"'
    
    writer = csv.writer(response)
    
    # Write header row
    writer.writerow([
        'ACE ID',
        'Details of Expenditure',
        'Requested By',
        'Section',
        'Date Created',
        'Budget',
        'Amount',
        'Transaction Status',
        'Approval Status',
        'Actioned By'
    ])
    
    # Write data rows
    for ace in aces:
        # Get transaction info
        transaction = Transactions.objects.filter(Ace_id2=ace).first()
        
        # Get approval info
        latest_approval = ace.process.approval_set.last() if ace.process and ace.process.approval_set.exists() else None
        approval_status = latest_approval.approved if latest_approval else ''
        actioned_by = latest_approval.user.get_full_name() if latest_approval and latest_approval.user else ''
        
        # Get section name safely
        try:
            section_name = ace.section.section if ace.section else ''
        except:
            section_name = ''
        
        writer.writerow([
            ace.Ace_id2,
            ace.details_of_expenditure,
            ace.requested_by.get_full_name() if ace.requested_by else '',
            section_name,
            ace.date_created.strftime('%Y-%m-%d') if ace.date_created else '',
            ace.budget_id.budget_name if ace.budget_id else '',
            ace.amount,
            transaction.approval_status if transaction else '',
            approval_status,
            actioned_by
        ])
    
    return response

@login_required
def export_current_year_pdf(request):
    """Export current year ACE data for user's region to PDF"""
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    current_year = timezone.now().year
    
    # Get user's region
    region = user_profile.region
    
    # Filter ACEs for current year and user's region
    aces = Ace2.objects.filter(
        date_created__year=current_year,
        region=region
    ).order_by('-date_created')
    
    # Get budget summary for context
    budgets = AssetBudget.objects.filter(region=region, period=current_year).order_by('-allocated')
    budget_summary = []
    
    for budget_item in budgets:
        if budget_item.allocated > 0:
            budget_aces = aces.filter(budget_id=budget_item)
            ace_count = budget_aces.count()
            total_ace_amount = budget_aces.aggregate(total=Sum('amount'))['total'] or 0
            avg_ace_amount = total_ace_amount / ace_count if ace_count > 0 else 0
            
            utilization_percentage = (budget_item.withdrawn / budget_item.allocated * 100) if budget_item.allocated > 0 else 0
            pending_percentage = (budget_item.to_be_withdrawn / budget_item.allocated * 100) if budget_item.allocated > 0 else 0
            available_percentage = (budget_item.balance / budget_item.allocated * 100) if budget_item.allocated > 0 else 0
            total_commitment_percentage = utilization_percentage + pending_percentage
            
            budget_summary.append({
                'budget': budget_item,
                'allocated': budget_item.allocated,
                'withdrawn': budget_item.withdrawn,
                'to_be_withdrawn': budget_item.to_be_withdrawn,
                'balance': budget_item.balance,
                'utilization_percentage': utilization_percentage,
                'pending_percentage': pending_percentage,
                'available_percentage': available_percentage,
                'total_commitment_percentage': total_commitment_percentage,
                'total_committed': budget_item.withdrawn + budget_item.to_be_withdrawn,
                'ace_count': ace_count,
                'avg_ace_amount': avg_ace_amount,
                'health_status': 'good' if budget_item.balance > (budget_item.allocated * 0.3) else 'warning' if budget_item.balance > (budget_item.allocated * 0.1) else 'critical'
            })
    
    template = loader.get_template('finance/ace2/ace_reports.html')
    context = {
        'aces': aces,
        'budget_summary': budget_summary,
        'current_year': current_year,
        'request': request
    }
    html = template.render(context, request)
    pdf = HTML(string=html).write_pdf()
    
    response = HttpResponse(pdf, content_type='application/pdf')
    response['Content-Disposition'] = f'attachment; filename="ace_report_{current_year}_{region.region}.pdf"'
    return response


@login_required
def enhanced_add_asset_number(request):
    """Enhanced asset number addition - works alongside your existing function"""
    if request.method == 'POST':
        try:
            print('Enhanced asset number addition')
            
            ace_id = request.POST['ace_id']
            ace_items = request.POST.getlist('asset_number[]')
            use_enhanced = request.POST.get('use_enhanced', 'false') == 'true'
            
            ace = Ace2.objects.filter(Ace_id2=ace_id).first()
            if not ace:
                messages.error(request, 'ACE not found')
                return redirect('/ace/aces')
            
            if use_enhanced:
                # Use enhanced system
                added_count = 0
                errors = []
                
                for asset_num in ace_items:
                    asset_num = asset_num.strip()
                    if asset_num:
                        try:
                            # Check if already exists in enhanced system
                            if ace.enhanced_asset_numbers.filter(asset_number=asset_num).exists():
                                errors.append(f"Asset {asset_num} already exists")
                                continue
                                
                            ace_asset = AceAssetNumber.objects.create(
                                ace=ace,
                                asset_number=asset_num,
                                added_by=request.user,
                                notes="Added via enhanced system"
                            )
                            ace_asset.verify_against_register()
                            added_count += 1
                            
                        except Exception as e:
                            errors.append(f"Error adding {asset_num}: {str(e)}")
                
                # Also update your existing field for backward compatibility
                all_assets = ace.get_all_asset_numbers()
                ace.asset_number = ','.join(all_assets)
                ace.save()
                
                if added_count > 0:
                    messages.success(request, f'Added {added_count} asset numbers using enhanced system')
                if errors:
                    for error in errors:
                        messages.warning(request, error)
                        
            else:
                # Fall back to your existing system
                ace.asset_number = ','.join(ace_items)
                ace.save()
                messages.success(request, 'Asset numbers added using existing system')
            
            return redirect('Ace:ace_detail', Ace_id2=ace.Ace_id2)
            
        except Exception as e:
            messages.error(request, f'Error: {str(e)}')
            return redirect('/ace/aces')
    
    return redirect('/ace/aces')


@login_required
def asset_autocomplete_api(request):
    """AJAX API for asset number autocomplete"""
    try:
        query = request.GET.get('q', '').strip()
        if len(query) < 2:
            return JsonResponse({'results': []})
        
        results = []
        
        # Search in Asset Register (if available)
        try:
            from Asset_Register.models import ZetdcAssets
            assets = ZetdcAssets.objects.filter(
                asset_number__icontains=query
            ).select_related('product_type')[:15]
            
            for asset in assets:
                results.append({
                    'id': asset.asset_number,
                    'text': f"{asset.asset_number} - {getattr(asset.product_type, 'product_type', 'Unknown')}",
                    'verified': True,
                    'source': 'Asset Register'
                })
                
        except (ImportError, Exception) as e:
            print(f"Asset Register not available: {e}")
        
        # Search in existing ACE asset numbers for suggestions
        existing_assets = AceAssetNumber.objects.filter(
            asset_number__icontains=query
        ).values_list('asset_number', flat=True).distinct()[:10]
        
        for asset_num in existing_assets:
            if not any(r['id'] == asset_num for r in results):
                results.append({
                    'id': asset_num,
                    'text': f"{asset_num} - Previously Used",
                    'verified': False,
                    'source': 'Previous ACEs'
                })
        
        # Search in legacy asset numbers for additional suggestions
        legacy_aces = Ace2.objects.exclude(
            asset_number__isnull=True
        ).exclude(
            asset_number__exact=''
        ).filter(
            asset_number__icontains=query
        )[:5]
        
        for ace in legacy_aces:
            if ace.asset_number:
                asset_list = [an.strip() for an in ace.asset_number.split(',') if an.strip()]
                for asset_num in asset_list:
                    if query.lower() in asset_num.lower() and not any(r['id'] == asset_num for r in results):
                        results.append({
                            'id': asset_num,
                            'text': f"{asset_num} - From ACE {ace.Ace_id2}",
                            'verified': False,
                            'source': 'Legacy ACE'
                        })
        
        # Allow manual entry
        if query and not any(r['id'] == query for r in results):
            results.insert(0, {
                'id': query,
                'text': f"{query} - New Asset Number",
                'verified': False,
                'source': 'Manual Entry'
            })
        
        return JsonResponse({'results': results})
        
    except Exception as e:
        print(f"Error in asset autocomplete: {e}")
        return JsonResponse({'results': []})


@login_required
def migrate_ace_assets(request, ace_id):
    """Migrate existing asset numbers to enhanced format"""
    try:
        ace = get_object_or_404(Ace2, Ace_id2=ace_id)
        
        # Check permissions (only accounting officers)
        user_roles = get_user_roles_qs(request.user)
        ace_roles = [role.name for role in user_roles if 'accounting_officer' in role.name.lower()]
        
        if not ace_roles:
            messages.error(request, 'Permission denied')
            return redirect('Ace:ace_detail', Ace_id2=ace.Ace_id2)
        
        migrated_count = ace.migrate_to_enhanced_assets(request.user)
        
        if migrated_count > 0:
            messages.success(request, f'Successfully migrated {migrated_count} asset numbers to enhanced format')
        else:
            messages.info(request, 'No asset numbers to migrate or already migrated')
            
        return redirect('Ace:ace_detail', Ace_id2=ace.Ace_id2)
        
    except Exception as e:
        messages.error(request, f'Migration error: {str(e)}')
        return redirect('Ace:ace_detail', Ace_id2=ace.Ace_id2)


@login_required
def remove_enhanced_asset(request, ace_id, asset_id):
    """Remove an asset from enhanced system"""
    try:
        ace = get_object_or_404(Ace2, Ace_id2=ace_id)
        ace_asset = get_object_or_404(AceAssetNumber, id=asset_id, ace=ace)
        
        # Check permissions
        user_roles = get_user_roles_qs(request.user)
        ace_roles = [role.name for role in user_roles if 'accounting_officer' in role.name.lower()]
        
        if not ace_roles:
            messages.error(request, 'Permission denied')
            return redirect('Ace:ace_detail', Ace_id2=ace.Ace_id2)
        
        asset_number = ace_asset.asset_number
        ace_asset.delete()
        
        # Update legacy field
        all_assets = ace.get_all_asset_numbers()
        ace.asset_number = ','.join(all_assets)
        ace.save()
        
        messages.success(request, f'Removed asset number {asset_number}')
        return redirect('Ace:ace_detail', Ace_id2=ace_id)
        
    except Exception as e:
        messages.error(request, f'Error removing asset: {str(e)}')
        return redirect('Ace:ace_detail', Ace_id2=ace_id)


@login_required
def asset_management_dashboard(request):
    """Dashboard for managing asset number migration and overview"""
    # Calculate statistics
    total_aces = Ace2.objects.count()
    aces_with_legacy = Ace2.objects.exclude(asset_number__isnull=True).exclude(asset_number__exact='').count()
    aces_with_enhanced = Ace2.objects.filter(enhanced_asset_numbers__isnull=False).distinct().count()
    ready_to_migrate = Ace2.objects.exclude(
        asset_number__isnull=True
    ).exclude(
        asset_number__exact=''
    ).filter(
        enhanced_asset_numbers__isnull=True
    ).count()
    
    stats = {
        'total_aces': total_aces,
        'legacy_assets': aces_with_legacy,
        'enhanced_assets': aces_with_enhanced,
        'ready_to_migrate': ready_to_migrate,
    }
    
    # Get sample ACEs for display
    sample_aces = Ace2.objects.exclude(
        asset_number__isnull=True
    ).exclude(
        asset_number__exact=''
    ).prefetch_related('enhanced_asset_numbers')[:20]
    
    # Add asset count to each ACE
    for ace in sample_aces:
        if ace.asset_number:
            ace.asset_count = len([an.strip() for an in ace.asset_number.split(',') if an.strip()])
        else:
            ace.asset_count = 0
    
    context = {
        'stats': stats,
        'sample_aces': sample_aces,
    }
    
    return render(request, 'finance/ace2/asset_management_dashboard.html', context)


@login_required
def bulk_migrate_assets(request):
    """Bulk migrate all legacy assets to enhanced system"""
    if request.method != 'POST':
        return JsonResponse({'error': 'POST method required'}, status=405)
    
    try:
        # Check permissions
        user_roles = get_user_roles_qs(request.user)
        ace_roles = [role.name for role in user_roles if 'accounting_officer' in role.name.lower() or request.user.is_superuser]
        
        if not ace_roles and not request.user.is_superuser:
            return JsonResponse({'error': 'Permission denied'}, status=403)
        
        # Get ACEs ready for migration
        aces_to_migrate = Ace2.objects.exclude(
            asset_number__isnull=True
        ).exclude(
            asset_number__exact=''
        ).filter(
            enhanced_asset_numbers__isnull=True
        )
        
        migrated_count = 0
        ace_count = 0
        errors = []
        
        for ace in aces_to_migrate:
            try:
                count = ace.migrate_to_enhanced_assets(request.user)
                if count > 0:
                    migrated_count += count
                    ace_count += 1
            except Exception as e:
                errors.append(f'ACE {ace.Ace_id2}: {str(e)}')
        
        response_data = {
            'migrated_count': migrated_count,
            'ace_count': ace_count,
        }
        
        if errors:
            response_data['errors'] = errors
            
        return JsonResponse(response_data)
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@login_required
def test_migrate_assets(request):
    """Test migration without making changes"""
    try:
        aces_to_migrate = Ace2.objects.exclude(
            asset_number__isnull=True
        ).exclude(
            asset_number__exact=''
        ).filter(
            enhanced_asset_numbers__isnull=True
        )
        
        total_assets = 0
        samples = []
        
        for ace in aces_to_migrate[:10]:  # Sample first 10
            if ace.asset_number:
                asset_list = [an.strip() for an in ace.asset_number.split(',') if an.strip()]
                asset_count = len(asset_list)
                total_assets += asset_count
                
                samples.append({
                    'ace_id': ace.Ace_id2,
                    'asset_count': asset_count,
                    'assets': asset_list
                })
        
        # Count total for all ACEs
        for ace in aces_to_migrate:
            if ace.asset_number:
                asset_list = [an.strip() for an in ace.asset_number.split(',') if an.strip()]
                total_assets += len(asset_list)
        
        return JsonResponse({
            'total_aces': aces_to_migrate.count(),
            'total_assets': total_assets,
            'samples': samples
        })
        
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
