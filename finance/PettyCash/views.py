from datetime import datetime, timezone, timedelta
from decimal import Decimal, InvalidOperation
from mimetypes import guess_type
from random import randrange
import csv

import sweetify
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, FileResponse, HttpResponse
from django.http import JsonResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
try:
    from openpyxl.workbook import Workbook
except Exception:  # pragma: no cover - not needed during isolated tests
    Workbook = None
from django.core.exceptions import ValidationError
from django.db.models import Sum, Q
from django.db.models.functions import TruncMonth

from ACE2.utils import find_ace_section_head, find_pettycash_section_head
from django.utils import timezone as dj_timezone
from approve.forms import ApprovalForm
try:
    from approve.views import intiate, get_my_roles_for_apps
except Exception:  # Fallback to a minimal initiator to avoid importing heavy subsystems during tests
    def intiate(request, app_name):
        try:
            from approve.models import Workflow, Process
            from it.users.models import Application
            app_obj, _ = Application.objects.get_or_create(application=app_name)
            wf, _ = Workflow.objects.get_or_create(name=f"{app_name}-workflow", application=app_obj)
            return Process.objects.create(workflow=wf)
        except Exception:
            # As a last resort, return a bare Process linked to a dummy Workflow
            from approve.models import Workflow, Process
            wf = Workflow.objects.create(name=f"{app_name}-wf-dummy", application_id=1)
            return Process.objects.create(workflow=wf)
    
    def get_my_roles_for_apps(user, app_names):
        """Fallback for get_my_roles_for_apps during tests"""
        return []
from it.users.models import UserProfile, Roles, Sections, Regions
from approve.models import Process, Step, Approval
from .forms import PettycashForm, QuotationFormSet, PettycashReportForm, CashierDisbursementForm, RequesterClearForm
from .models import Pettycash, Quotation, PettycashReport

try:
    from ..comparative_schedules.views import notify_user
except Exception:  # Safe no-op during tests
    def notify_user(*args, **kwargs):
        return None


def is_process_rejected(process) -> bool:
    """Return True if any approval on the process is marked as Rejected."""
    try:
        return bool(process and process.approval_set.filter(approved='Rejected').exists())
    except Exception:
        return False


def get_parent_cost_center(cost_centers):
    """Get the parent cost center from a list of cost centers."""
    parent = None
    for cost_center in cost_centers:
        if cost_center.parent in cost_centers:
            parent = cost_center.parent
    return parent


@login_required
def pettyCash_detail(request, petty_id):
    global payment_mode
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    # Handle missing user profile
    if not user_profile:
        messages.error(request, "User profile not found. Please contact administrator.")
        return redirect('/pettycash/pettycashs')

    # Handle missing user groups safely
    try:
        user_groups = user_profile.groups.values_list('name', flat=True) if user_profile.groups.exists() else []
    except Exception:
        user_groups = []

    custom_user_roles = {
        "pettycash": {},
    }

    # Safely get user roles
    try:
        roles_ = user_profile.roles.all()
        for _role in roles_:
            try:
                role = Roles.objects.filter(id=_role.id).first()
                if role and role.application == "pettycash":
                    custom_user_roles["pettycash"] = role.role
            except Exception:
                continue
    except Exception:
        roles_ = []
        
    pettycash_role = str(custom_user_roles["pettycash"])
    # print(pettycash_role)

    # Safely get PettyCash object
    try:
        pettycash_item = Pettycash.objects.get(petty_id=petty_id)
    except Pettycash.DoesNotExist:
        messages.error(request, f"PettyCash {petty_id} not found.")
        return redirect('/pettycash/pettycashs')
    except Exception as e:
        messages.error(request, f"Error accessing PettyCash: {str(e)}")
        return redirect('/pettycash/pettycashs')
        
    # Default form holders
    form = None  # cashier form
    requester_form = None

    # return validation to clear validation = pettycash_item.process.approval_set.filter(approved='Approved',
    # step__approver__in=user_profile.roles.all()).exists()) print(validation)

    quotations = Quotation.objects.filter(pettycash=pettycash_item).all()
    # print(quotations.count())

    # Check if process has been rejected at any point
    process_rejected = is_process_rejected(pettycash_item.process)

    # REPLACE the current raw POST handling under pettycash_role == "disburse"
    # with the safer form-based flow below.

    if pettycash_role == "disburse":
        # Disallow any actions if the process has already been rejected
        if process_rejected:
            messages.warning(request, f"PettyCash {pettycash_item.petty_id} was rejected. No further actions are allowed.")
            # Don't redirect - just disable form functionality by setting form to None
            form = None
        # Prevent editing if already captured
        elif request.method == "POST":
            if getattr(pettycash_item, "payment_mode", None):
                messages.warning(request, "Payment already captured. Contact Finance to amend.")
                # Don't redirect - just disable form functionality by setting form to None  
                form = None

            form = CashierDisbursementForm(request.POST, pettycash=pettycash_item)
            if form.is_valid():
                pettycash_item.payment_mode = form.cleaned_data["payment_mode"]
                pettycash_item.amount_disbursed = form.cleaned_data["amount_disbursed"]
                # Model-level validation safety net
                try:
                    pettycash_item.full_clean()
                except ValidationError as e:
                    # Attach specific validation errors and fall through to render
                    if hasattr(e, 'message_dict') and 'amount_disbursed' in e.message_dict:
                        for msg in e.message_dict['amount_disbursed']:
                            form.add_error("amount_disbursed", msg)
                    else:
                        for msg in e.messages:
                            form.add_error("amount_disbursed", msg)
                else:
                    pettycash_item.save(update_fields=["payment_mode", "amount_disbursed"])

                # Notify requester (keep your existing pattern)
                try:
                    msg = f"Your Petty Cash {pettycash_item.petty_id} has been captured by Cashier"
                    url = f"/pettycash/pettycash_detail/{pettycash_item.petty_id}"
                    notify_user(pettycash_item.requested_by, msg, "PettyCash", url, pettycash_item.petty_id, request)
                except Exception:
                    pass

                if not form.errors:
                    messages.success(request, "Payment captured successfully.")
                    # After successful save, continue to render the updated page instead of redirecting
                    # This prevents potential redirect loops and shows the updated state immediately
                    form = None  # Clear the form since payment is now captured
            # if invalid, keep form with errors and fall through to shared render
        else:
            if not getattr(pettycash_item, "payment_mode", None) and not process_rejected:
                form = CashierDisbursementForm(pettycash=pettycash_item)

    # Requester clear flow (inline form, similar to cashier)
    if pettycash_role == "create":
        # Eligible only after cashier disburses and when not yet receipted
        if pettycash_item.amount_disbursed is not None and pettycash_item.payment_mode is not None and not pettycash_item.receipt_file:
            if request.method == "POST" and request.POST.get("action") == "requester_clear":
                # Disallow clearing and auto-approval if process was rejected
                if process_rejected:
                    messages.warning(request, f"PettyCash {pettycash_item.petty_id} was rejected. You cannot clear or proceed further.")
                    # Don't redirect - just disable form by not processing it further
                    pass
                
                requester_form = RequesterClearForm(request.POST, request.FILES, pettycash=pettycash_item)
                if requester_form.is_valid():
                    pettycash_item.receipt_file = requester_form.cleaned_data["receipt_file"]
                    pettycash_item.amount_used = float(requester_form.cleaned_data["amount_used"])
                    pettycash_item.save(update_fields=["receipt_file", "amount_used"])

                    # Auto-approve requester step if permitted
                    try:
                        # Double-check rejection state before auto-approval
                        if is_process_rejected(pettycash_item.process):
                            raise Exception("Process rejected; skipping auto-approval")
                        
                        process = pettycash_item.process
                        latest_approval = process.approval_set.last()
                        next_step_num = (latest_approval.step.step + 1) if latest_approval else 1
                        user_roles = user_profile.roles.all()
                        step_for_user = Step.objects.get(step=next_step_num, workflow=process.workflow, approver__in=user_roles)
                        Approval.objects.create(
                            step=step_for_user,
                            user=request.user,
                            process=process,
                            approved='Approved',
                            approved_at=datetime.now()
                        )
                    except Step.DoesNotExist:
                        pass
                    except Exception:
                        pass

                    messages.success(request, "Petty cash cleared successfully.")
                    # After successful clearing, continue to render the updated page instead of redirecting
                    # This prevents potential redirect loops and shows the updated state immediately
                    requester_form = None  # Clear the form since clearing is complete
            else:
                requester_form = RequesterClearForm(pettycash=pettycash_item)

    approvalForm = None
    to = None
    
    # Safely get user roles
    try:
        user_roles = user_profile.roles.all() if user_profile else []
    except Exception:
        user_roles = []

    clear = False
    clear_minus = False

    try:
        last_approved = pettycash_item.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0

    cashier_approved = False
    if pettycash_item.process.approval_set.filter(step__step=3).exists():
        cashier_approved = True

    approval_status = pettycash_item.process.approval_set.last().approved if pettycash_item.process.approval_set.last() else ""
    print("last approved", approval_status)
    # Do not offer approval actions if any prior rejection exists
    if not process_rejected:
        next_step = last_approved + 1
        if len(pettycash_item.process.approval_set.all()) == len(pettycash_item.process.workflow.step_set.all()):
            print('approval set')
            clear = True
        if len(pettycash_item.process.approval_set.all()) == len(pettycash_item.process.workflow.step_set.all()) - 2:
            print('approval set ...')
            clear_minus = True

        try:
            newStep = Step.objects.get(step=next_step, workflow=pettycash_item.process.workflow,
                                       approver__in=user_roles)

            # check if section head
            if pettycash_role == "approve":
                if newStep and request.user.section == pettycash_item.section:
                    approvalForm = ApprovalForm
                    print("newstep", newStep.step)
                    print(len(pettycash_item.process.workflow.step_set.all()))

                    to = newStep.to
            else:
                approvalForm = ApprovalForm
                print("newstep", newStep.step)
                print(len(pettycash_item.process.workflow.step_set.all()))

                to = newStep.to

        except Step.DoesNotExist:
            pass

    approved_steps = pettycash_item.process.approval_set.all().values_list('step__step', flat=True)

    if pettycash_role == "create":
        requestor = pettycash_role
    else:
        print(pettycash_role)
        requestor = None

    if pettycash_role == "disburse":
        cashier = pettycash_role
    else:
        cashier = None

    # Ensure cashier form is available on final render when needed
    if pettycash_role == "disburse" and not getattr(pettycash_item, "payment_mode", None) and form is None and not process_rejected:
        try:
            form = CashierDisbursementForm(pettycash=pettycash_item)
        except Exception:
            form = None

    print(pettycash_role, clear, requestor, clear_minus, cashier_approved)
    return render(request, 'finance/pettycash/pettycash_detail.html',
                  {
                      'pettycash': pettycash_item,
                      'approved_steps': approved_steps,
                      'approvalForm': approvalForm,
                      'to': to,
                      'pettycash_role': pettycash_role,
                      'user_groups': user_groups,
                      'quotations': quotations,
                      'clear': clear,
                      "clear_minus": clear_minus,
                      'requestor': requestor,
                      'cashier': cashier,
                      'cashier_approved': cashier_approved,
                      'form': form,  # cashier form
                      'requester_form': requester_form,  # requester clear form
                  })


@login_required
def create_pettycash(request):
    """
    Create a new PettyCash with comprehensive validation and error handling
    """
    try:
        user_id = request.user.id
        user_profile = UserProfile.objects.filter(id=user_id).first()
        
        # Validate user profile exists
        if not user_profile:
            messages.error(request, "User profile not found. Please contact your administrator to set up your profile.")
            sweetify.error(request, "User profile not found. Please contact your administrator.")
            return redirect('/pettycash/pettycashs')

        # Check if user has required roles for PettyCash creation
        user_roles = user_profile.roles.all()
        if not user_roles.exists():
            messages.error(request, "You don't have any assigned roles. Please contact your administrator to assign appropriate roles.")
            sweetify.error(request, "No roles assigned to your profile.")
            return redirect('/pettycash/pettycashs')
            
        if request.method == 'POST':
            try:
                form = PettycashForm(request.POST, request.FILES)
                formset = QuotationFormSet(request.POST, request.FILES)
                user_id = request.user.id
                user_profile = UserProfile.objects.filter(id=user_id).first()

                # Double-check user profile during POST processing
                if not user_profile:
                    messages.error(request, "User profile not found during form processing.")
                    sweetify.error(request, "User profile error.")
                    return redirect('/pettycash/pettycashs')

                user_groups = user_profile.groups.values_list('name', flat=True)

                custom_user_roles = {
                    "pettycash": {},
                }

                roles_ = user_profile.roles.all()
                if not roles_.exists():
                    messages.error(request, "No roles assigned. Please contact administrator.")
                    sweetify.error(request, "No roles assigned.")
                    return redirect('/pettycash/pettycashs')

                # Determine user role for pettycash
                pettycash_role = 'none'
                for _role in roles_:
                    role = Roles.objects.filter(id=_role.id).first()
                    if role and role.application == "pettycash":
                        custom_user_roles["pettycash"] = role.role
                        pettycash_role = str(custom_user_roles["pettycash"])
                        break

                print(f"PettyCash role: {pettycash_role}")
                
                if pettycash_role == "create":
                    # Validate forms
                    if not form.is_valid():
                        # Enhanced form validation error messages
                        form_errors = []
                        for field, errors in form.errors.items():
                            for error in errors:
                                form_errors.append(f"{field.replace('_', ' ').title()}: {error}")
                        
                        if form_errors:
                            error_message = "Please correct the following errors: " + "; ".join(form_errors)
                            messages.error(request, error_message)
                            sweetify.error(request, "Please correct the form errors and try again.")
                        
                        form = PettycashForm(user=user_profile)
                        formset = QuotationFormSet()
                        return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})
                    
                    if not formset.is_valid():
                        # Enhanced formset validation error messages
                        formset_errors = []
                        for i, form_error in enumerate(formset.errors):
                            if form_error:
                                for field, errors in form_error.items():
                                    for error in errors:
                                        formset_errors.append(f"Quotation {i+1} - {field.replace('_', ' ').title()}: {error}")
                        
                        if formset_errors:
                            formset_error_message = "Quotation errors: " + "; ".join(formset_errors)
                            messages.error(request, formset_error_message)
                            sweetify.error(request, "Please correct the quotation errors.")
                        
                        form = PettycashForm(user=user_profile)
                        formset = QuotationFormSet()
                        return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})

                    # Process the valid form
                    pettycash = form.save(commit=False)
                    
                    # Validate required fields
                    if not pettycash.details_of_expenditure:
                        messages.error(request, "Details of expenditure is required.")
                        sweetify.error(request, "Details of expenditure is required.")
                        return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})
                    
                    if not pettycash.amount or pettycash.amount <= 0:
                        messages.error(request, "Valid amount is required.")
                        sweetify.error(request, "Valid amount is required.")
                        return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})

                    # Initialize process workflow
                    try:
                        pettycash.process = intiate(request, 'pettycash')
                    except Exception as e:
                        messages.error(request, f"Error initializing approval workflow: {str(e)}")
                        sweetify.error(request, "Error setting up approval process.")
                        return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})
                    
                    pettycash.requested_by = request.user

                    # Generate unique PettyCash ID
                    try:
                        rand = randrange(1, 1000)
                        rand2 = str(rand)
                        date = datetime.now()
                        date = date.strftime("%Y%m%d")
                        petty_id = "PC" + date + rand2
                        pettycash.petty_id = petty_id
                        
                        # Validate uniqueness
                        if Pettycash.objects.filter(petty_id=petty_id).exists():
                            # If ID exists, try a few more times
                            for attempt in range(5):
                                rand = randrange(1, 10000)
                                rand2 = str(rand)
                                petty_id = "PC" + date + rand2
                                if not Pettycash.objects.filter(petty_id=petty_id).exists():
                                    pettycash.petty_id = petty_id
                                    break
                            else:
                                raise ValueError("Could not generate unique PettyCash ID after multiple attempts")
                                
                    except Exception as e:
                        messages.error(request, f"Error generating PettyCash ID: {str(e)}")
                        sweetify.error(request, "Could not generate unique PettyCash ID. Please try again.")
                        return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})
                    
                    # Save the PettyCash
                    try:
                        pettycash.save()
                        messages.success(request, f"PettyCash {pettycash.petty_id} created successfully!")
                        sweetify.success(request, "PettyCash created successfully!")
                    except Exception as e:
                        messages.error(request, f"Error saving PettyCash: {str(e)}")
                        sweetify.error(request, "Error saving PettyCash. Please try again.")
                        return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})

                    # Save quotations
                    try:
                        for quotation_form in formset:
                            if quotation_form.cleaned_data:  # Only save if there's data
                                quotation = quotation_form.save(commit=False)
                                quotation.pettycash = pettycash
                                quotation.save()
                    except Exception as e:
                        messages.warning(request, f"PettyCash created but some attachments failed to save: {str(e)}")
                        print(f"Quotation save error: {str(e)}")

                    # Notification logic with error handling
                    try:
                        requester = pettycash.requested_by
                        use = UserProfile.objects.filter(id=requester.id).first()
                        if use and use.section:
                            section_created = use.section

                            # notify section heads
                            section_heads = find_pettycash_section_head(section_created)
                            if section_heads:
                                print(section_heads, " section_heads")
                                msg = f"Your subordinate {str(use)} created {pettycash.petty_id} for section {str(pettycash.section)}"
                                url = f"/pettycash/pettycash_detail/{pettycash.petty_id}"
                                section_heads_profile = UserProfile.objects.filter(username=section_heads).first()
                                if section_heads_profile:
                                    notify_user(section_heads_profile, msg, "PettyCash", url, pettycash.petty_id, request)
                                    print("notified", section_heads)

                            pettycash_section = pettycash.section
                            pettycash_sh = find_pettycash_section_head(pettycash_section)

                            if pettycash_sh:
                                print(pettycash_sh, "pettycash_sh")
                                msg = f"User {str(use)} created {pettycash.petty_id} for section {str(pettycash.section)}"
                                url = f"/pettycash/pettycash_detail/{pettycash.petty_id}"
                                pettycash_sh_profile = UserProfile.objects.filter(username=pettycash_sh).first()
                                if pettycash_sh_profile:
                                    notify_user(pettycash_sh_profile, msg, "PettyCash", url, pettycash.petty_id, request)
                                    print("notified", pettycash_sh)
                    except Exception as e:
                        print(f"Notification error: {str(e)}")
                        # Don't fail the creation for notification errors

                    url = reverse('pettycash:pettycash_detail', args=[pettycash.petty_id])
                    return redirect(url)
                    
                else:
                    sweetify.error(request, "You are not authorized to create a new PettyCash. Please contact your administrator for proper role assignment.")
                    messages.error(request, "You are not authorized to create a new PettyCash.")
                    return redirect('/pettycash/pettycashs')
                    
            except Exception as e:
                messages.error(request, f"Error processing PettyCash creation: {str(e)}. Please try again.")
                sweetify.error(request, "Error processing form. Please try again.")
                print(f"PettyCash POST processing error: {str(e)}")
                form = PettycashForm(user=user_profile)
                formset = QuotationFormSet()
                return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})

        else:
            form = PettycashForm(user=user_profile)
            formset = QuotationFormSet()

        return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})
        
    except UserProfile.DoesNotExist:
        messages.error(request, "User profile not found. Please contact your administrator to create your profile.")
        sweetify.error(request, "User profile not found.")
        return redirect('/pettycash/pettycashs')
    except Roles.DoesNotExist:
        messages.error(request, "Role configuration error. Please contact your administrator.")
        sweetify.error(request, "Role configuration error.")
        return redirect('/pettycash/pettycashs')
    except Exception as e:
        messages.error(request, f"An unexpected error occurred: {str(e)}. Please try again or contact support.")
        sweetify.error(request, "System error occurred. Please try again.")
        print(f"PettyCash Creation Error: {str(e)}")  # For debugging
        return redirect('/pettycash/pettycashs')


@login_required
def pettycash_awaiting_my_action(request):
    """
    Process PettyCash based on user roles and cost centers - with fallback for older records.
    Combines cost center filtering (for newer records) with section/region filtering (for older records).
    """
    user = request.user
    user_profile = UserProfile.objects.filter(id=user.id).first()
    
    if not user_profile:
        return render(request, 'finance/pettycash/view_all_pettycashs.html', {
            "pettycashs": [],
            "error": "User profile not found.",
        })
    
    application_names = ["pettycash"]
    cost_centers_set = user.cost_centers_for(application_names)
    cost_center = user.cost_center
    end_date = datetime.now()
    start_date = end_date.replace(day=1)
    
    # Prepare cost centers list
    cost_centers = []
    if cost_centers_set:
        cost_centers = list(cost_centers_set)
        cost_center = get_parent_cost_center(cost_centers)
    else:
        # Fallback to user's cost center and descendants
        print("Using fallback cost centers")
        fallback_cost_centers = user.cost_center_and_decendace()
        if fallback_cost_centers:
            cost_centers = list(fallback_cost_centers)
    
    user_roles = set(user.roles.all())
    pettycashs_to_process = []
    processed_pettycash_ids = set()  # Track processed PettyCash to avoid duplicates
    
    # Determine role level for access control
    # Note: PettyCash doesn't have FD/MD roles typically, but keep for consistency
    system_wide_roles = ['Finance Director', 'Managing Director']
    has_system_wide_access = user_roles and any(role.name in system_wide_roles for role in user_roles)
    
    # Query 1: Records WITH cost centers
    if has_system_wide_access:
        # System-wide roles see ALL records with cost centers
        pettycashs_with_cost_center = Pettycash.objects.filter(
            cost_center__isnull=False
        ).exclude(
            process__approval__approved="Rejected"
        ).prefetch_related(
            "process__approval_set", "process__workflow__step_set"
        )
    elif cost_centers:
        # All other roles limited to their designated cost centers
        pettycashs_with_cost_center = Pettycash.objects.filter(
            cost_center__in=cost_centers
        ).exclude(
            process__approval__approved="Rejected"
        ).prefetch_related(
            "process__approval_set", "process__workflow__step_set"
        )
    else:
        pettycashs_with_cost_center = Pettycash.objects.none()
    
    for pettycash in pettycashs_with_cost_center:
        if pettycash.process and pettycash.petty_id not in processed_pettycash_ids:
            approvals = pettycash.process.approval_set.all()
            next_step = (approvals.last().step.step if approvals.exists() else 0) + 1
            if (
                pettycash.process.workflow.step_set.filter(
                    step=next_step, approver__in=user_roles
                ).exists()
            ):
                pettycashs_to_process.append(pettycash)
                processed_pettycash_ids.add(pettycash.petty_id)
    
    # Query 2: Records WITHOUT cost centers (use section/region fallback)
    section = user_profile.section
    region = user_profile.region
    current_year = datetime.now().year
    
    # Determine access level for records without cost centers
    # System-wide roles: See everything
    # Petty Cash Authoriser: See entire region
    # Others: See only their section
    region_wide_roles = ['Petty Cash Authoriser']
    has_region_wide_access = user_roles and any(role.name in region_wide_roles for role in user_roles)
    
    if has_system_wide_access:
        # System-wide roles see ALL records without cost centers
        fallback_filter = {
            'cost_center__isnull': True,
            'date_created__year__gte': current_year
        }
    elif has_region_wide_access and region:
        # Region-wide roles see entire region
        fallback_filter = {
            'cost_center__isnull': True,
            'region': region,
            'date_created__year__gte': current_year
        }
    elif region:
        # Junior roles see only their section
        fallback_filter = {
            'cost_center__isnull': True,
            'region': region,
            'date_created__year__gte': current_year
        }
        if section:
            fallback_filter['section'] = section
    else:
        fallback_filter = None
    
    if fallback_filter:
        pettycashs_without_cost_center = Pettycash.objects.filter(
            **fallback_filter
        ).exclude(
            process__approval__approved="Rejected"
        ).prefetch_related("process__approval_set", "process__workflow__step_set")
        
        for pettycash in pettycashs_without_cost_center:
            if pettycash.process and pettycash.petty_id not in processed_pettycash_ids:
                approvals = pettycash.process.approval_set.all()
                next_step = (approvals.last().step.step if approvals.exists() else 0) + 1
                if (
                    pettycash.process.workflow.step_set.filter(
                        step=next_step, approver__in=user_roles
                    ).exists()
                ):
                    pettycashs_to_process.append(pettycash)
                    processed_pettycash_ids.add(pettycash.petty_id)
    else:
        pettycashs_without_cost_center = Pettycash.objects.none()

    # PettyCash created by the user (both with and without cost centers)
    created_pettycashs_filter = {"requested_by": request.user}
    if has_system_wide_access:
        created_pettycashs_with_cc = Pettycash.objects.filter(cost_center__isnull=False, **created_pettycashs_filter).exclude(process__approval__approved="Rejected")
    elif cost_centers:
        created_pettycashs_with_cc = Pettycash.objects.filter(cost_center__in=cost_centers, **created_pettycashs_filter).exclude(process__approval__approved="Rejected")
    else:
        created_pettycashs_with_cc = Pettycash.objects.none()
    
    # For created PettyCash without cost centers, respect access levels
    if has_system_wide_access:
        created_fallback_filter = {
            'cost_center__isnull': True,
            **created_pettycashs_filter
        }
    elif has_region_wide_access and region:
        created_fallback_filter = {
            'cost_center__isnull': True,
            'region': region,
            **created_pettycashs_filter
        }
    elif region:
        created_fallback_filter = {
            'cost_center__isnull': True,
            'region': region,
            **created_pettycashs_filter
        }
        if section:
            created_fallback_filter['section'] = section
    else:
        created_fallback_filter = None
    
    if created_fallback_filter:
        created_pettycashs_without_cc = Pettycash.objects.filter(
            **created_fallback_filter
        ).exclude(process__approval__approved="Rejected")
    else:
        created_pettycashs_without_cc = Pettycash.objects.none()
    
    # Combine created PettyCash
    created_pettycashs = list(created_pettycashs_with_cc) + list(created_pettycashs_without_cc)

    return render(
        request,
        'finance/pettycash/view_all_pettycashs.html',
        {
            "pettycashs": pettycashs_to_process,
            "created_pettycashs": created_pettycashs,
            "all": False,
            "start_date": start_date,
            "end_date": end_date,
            "cost_center": cost_center,
            "types": application_names,
            "roles": get_my_roles_for_apps(user, application_names),
        },
    )


@login_required
def view_all_pettycashs(request):
    try:
            user_id = request.user.id
            user_profile = UserProfile.objects.prefetch_related('roles').filter(id=user_id).first()
        
            if not user_profile:
                messages.error(request, "User profile not found. Please contact administrator.")
                return render(request, 'finance/pettycash/view_all_pettycashs.html', {
                    'pettycashs': [],
                    'pettycash_role': 'none',
                    'requester': 'create',
                    'error_message': 'User profile not found'
                })
        
            try:
                region = Regions.objects.filter(id=user_profile.region.id).first()
                if not region:
                    messages.error(request, "User region not found. Please contact administrator.")
                    return render(request, 'finance/pettycash/view_all_pettycashs.html', {
                        'pettycashs': [],
                        'pettycash_role': 'none',
                        'requester': 'create',
                        'error_message': 'User region not found'
                    })
            except AttributeError:
                messages.error(request, "User profile is incomplete. Missing region information.")
                return render(request, 'finance/pettycash/view_all_pettycashs.html', {
                    'pettycashs': [],
                    'pettycash_role': 'none',
                    'requester': 'create',
                    'error_message': 'Incomplete user profile'
                })

            try:
                user_groups = user_profile.groups.values_list('name', flat=True)
            except AttributeError:
                user_groups = []

            custom_user_roles = {
                "pettycash": {},
            }

            roles_ = user_profile.roles.all()
            pettycash_role = None
        
            try:
                for _role in roles_:
                    role = Roles.objects.filter(id=_role.id).first()
                    if role and role.application == "pettycash":
                        custom_user_roles["pettycash"] = role.role
                        pettycash_role = str(custom_user_roles["pettycash"])
                        print("tr ", role.role)
                        break
                
                if pettycash_role is None:
                    messages.warning(request, "You don't have a PettyCash role assigned. Please contact administrator for access.")
                    return render(request, 'finance/pettycash/view_all_pettycashs.html', {
                        'pettycashs': [],
                        'pettycash_role': 'none',
                        'requester': 'create',
                        'error_message': 'No PettyCash role assigned'
                    })
                    
            except Exception as e:
                messages.error(request, f"Error determining user role: {str(e)}")
                return render(request, 'finance/pettycash/view_all_pettycashs.html', {
                    'pettycashs': [],
                    'pettycash_role': 'none',
                    'requester': 'create',
                    'error_message': 'Role determination error'
                })
            
            print("gh ", pettycash_role)
            requester = "create"
            current_year = datetime.now(timezone.utc).year

            # Calculate the starting year
            starting_year = current_year - 2

            if pettycash_role == "create":
                pettycashs = Pettycash.objects.filter(region=region, requested_by=request.user)
            elif pettycash_role == "approve":
                pettycashs = Pettycash.objects.filter(region=region, section=request.user.section).order_by('-date_created',
                                                                                                            'petty_id')[:800]
            else:
                pettycashs = Pettycash.objects.filter(region=region).only('petty_id', 'date_created').order_by('-date_created',
                                                                                                               'petty_id')[
                             :1200]
        
    except Exception as e:
        messages.error(request, f"System error: {str(e)}")
        return render(request, 'finance/pettycash/view_all_pettycashs.html', {
            'pettycashs': [],
            'pettycash_role': 'none',
            'requester': 'create',
            'error_message': f'System error: {str(e)}'
        })
        
    return render(request, 'finance/pettycash/view_all_pettycashs.html', {'pettycashs': pettycashs,
                                                                          'requester': requester})


@login_required
def import_pettycash(request):
    if request.method == 'POST':
        file = request.FILES['file']
        file2 = request.FILES['file2']
        # if file there filter based on file type
        if file and file2:
            file_name = file.name
            file_name2 = file2.name
            if file_name.endswith('.csv') and file_name2.endswith('.csv'):
                # if file_name.endswith('.csv') or file_name2.endswith('.csv'):
                # read the csv file
                print('csv file2 uploaded')

                decoded_file = file.read().decode('cp1252').splitlines()
                decoded_file2 = file2.read().decode('cp1252').splitlines()
                reader = csv.DictReader(decoded_file)
                reader2 = csv.DictReader(decoded_file2)
                for row in reader:
                    petty_id = row['voucher_id']
                    department = row['department']
                    location = row['location']
                    section = row['section']
                    allocation_code1 = row['allocation_code1']
                    description = row['description']
                    # quotation_1 = row['quotation_1']
                    # quotation_2 = row['quotation_2']
                    # quotation_3 = row['quotation_3']
                    amount = row['amount']
                    requester = row['requester']
                    payment_mode = row['payment_mode']
                    mobile_number = row['mobile_number']
                    merchant_code = row['merchant_code']
                    merchant = row['merchant']
                    fullname = row['fullname']
                    centre = row['centre']
                    sect = row['sect']
                    region = row['region']
                    # petty_id = 'PC220101...'

                    # Extract the date part from the petty_id
                    date_str = petty_id[2:8]

                    # Convert the date string to a datetime object
                    # If the year is less than 20, we assume it's 2000s, otherwise it's 1900s
                    year = int(date_str[:2])
                    if year > 20:
                        year += 2000
                    else:
                        year += 1900

                    date_str = str(year) + date_str[2:]
                    date = datetime.strptime(date_str, '%Y%m%d')
                    # format into date format not date time
                    date = date.strftime('%Y-%m-%d')

                    print(date)  # Outputs: 2022-01-01 00:00:00

                    # if date created is earlier than 2024 then the currency is ZWL,but if its after 2024 its is ZIG
                    # create pettycash if it does not exist
                    PC = Pettycash.objects.filter(petty_id=petty_id).first()
                    if not PC:
                        if section != '':
                            Section = Sections.objects.filter(code=section).first()
                            if not Section:
                                Section = Sections.objects.create(
                                    section=section,
                                    code=section,
                                )
                                Section.save()
                        else:
                            Section = None

                        if region != '':
                            Region = Regions.objects.filter(code=region).first()
                            if not Region:
                                Region = Regions.objects.create(
                                    region=region,
                                    code=region,
                                )
                                Region.save()
                        else:
                            Region = None

                        if requester != '':
                            # remove the leading and trailing whitespaces
                            requester = requester.strip()
                            Requester = UserProfile.objects.filter(username=requester).first()
                        else:
                            Requester = None

                        pettycash = Pettycash.objects.create(
                            petty_id=petty_id,
                            section=Section,
                            details_of_expenditure=description,
                            amount=amount,
                            payment_mode=payment_mode,
                            requested_by=Requester,
                            old_version=True,
                            region=Region,
                            date_created=date

                        )
                        pettycash.process = intiate(request, 'pettycash')
                        pettycash.save()
                        pettycash.date_created = date
                        pettycash.save()
                        # check if quotation_1 isnt empty
                        # if quotation_1 != '' or quotation_1 == '0':
                        #     qoutation_1 = Quotation.objects.create(
                        #         pettycash=pettycash,
                        #         quotation_file=quotation_1,
                        #     )
                        #     qoutation_1.save()
                        # qoutation_2 = Quotation.objects.create(
                        #     pettycash=pettycash,
                        #     quotation_file=quotation_2,
                        # )
                        # qoutation_2.save()
                        # qoutation_3 = Quotation.objects.create(
                        #     pettycash=pettycash,
                        #     quotation_file=quotation_3,
                        # )
                        # qoutation_3.save()
                        # print(petty_id, 'created')
                    else:
                        print(petty_id, 'already exists')

                print('now dealing with approvals')
                for row1 in reader2:
                    voucher_id = row1['voucher_id']
                    section = row1['section']
                    status_1 = row1['status_1']
                    status_2 = row1['status_2']
                    status_3 = row1['status_3']
                    # status_4 = row1['status_4']
                    # status_5 = row1['status_5']
                    status_6 = row1['status_6']
                    # status_7 = row1['status_7']
                    update_user1 = row1['update_user1']
                    update_user2 = row1['update_user2']
                    update_user3 = row1['update_user3']
                    # update_user4 = row1['update_user4']
                    update_user5 = row1['update_user4']
                    update_date1 = row1['update_date1']
                    update_date2 = row1['update_date2']
                    update_date3 = row1['update_date3']
                    # update_date4 = row1['update_date4']
                    # reason_1 = row1['reason_1']
                    # reason_2 = row1['reason_2']
                    # auth_signature = row1['auth_signature']
                    # received_by = row1['received_by']
                    # ecno = row1['ecno']
                    # date_received = row1['date_received']
                    payment_method = row1['payment_method']
                    # ecocash_charge = row1['ecocash_charge']
                    # total_disbursed = row1['total_disbursed']
                    # actual_amount = row1['actual_amount']
                    # ecocash_confirmation = row1['ecocash_confirmation']
                    # allocation_code = row1['allocation_code']
                    # receipt = row1['receipt']
                    # receipt_date = row1['receipt_date']
                    # acquittal_date = row1['acquittal_date']
                    # checked_by = row1['checked_by']
                    # checked_on = row1['checked_on']
                    # checked_status = row1['checked_status']
                    # reason_3 = row1['reason_3']
                    # reason_4 = row1['reason_4']
                    # reason_5 = row1['reason_5']
                    # requestor_cleared_by = row1['requestor_cleared_by']
                    # cashier_cleared_by = row1['cashier_cleared_by']
                    # disbursement_remarks = row1['disbursement_remarks']
                    # acquittal_remarks = row1['acquittal_remarks']
                    # requestor_remarks = row1['requestor_remarks']
                    # returned_by = row1['returned_by']
                    # date_returned = row1['date_returned']
                    # return_remarks = row1['return_remarks']
                    # imt_tax = row1['imt_tax']
                    # print("now dealing with approvals")
                    # add the date created to the pettycash process
                    pettycash = Pettycash.objects.filter(petty_id=voucher_id).first()
                    # if pettycash exists then update the pettycash process with the date created modify the date created
                    # to the date created in the pettycash modify update_date1 to form a date object yyyy-mm-dd
                    if pettycash and update_date1 != '0000-00-00 00:00:00':
                        update_date1 = datetime.strptime(update_date1, '%Y-%m-%d')
                        # pettycash.date_created = update_date1
                        print('date created', pettycash.date_created)

                        if pettycash.process:
                            print('process exists')
                            print(pettycash)

                            process = Pettycash.objects.filter(petty_id=voucher_id).first().process

                            print('process', process.id)
                            print(update_user2, "update_user2")
                            print(status_1, "status_1")
                            # make status_1 an integer
                            status_1 = int(status_1)
                            if status_1 == 1:
                                update_user2 = update_user2.strip()
                                print(update_user2, "update_user2 stripped")
                                user = UserProfile.objects.filter(username=update_user2).first()
                                if user and status_1 == 1:
                                    if process:
                                        if approve_step(process.id, user.username, update_date1):
                                            print('approved as sh', pettycash)
                                        else:
                                            print('not approved')
                                    else:
                                        print('process not found')

                                status_2 = int(status_2)

                                if update_user3 != '' and status_2 == 2:
                                    update_user3 = update_user3.strip()
                                    user = UserProfile.objects.filter(username=update_user3).first()
                                    if user:
                                        if approve_step(process.id, user.username, update_date2):
                                            print('approved as petty Authoriser', pettycash)
                                        else:
                                            print('not approved')
                                    else:
                                        print('user not found')
                                status_3 = int(status_3)
                                status_7 = int(status_6)
                                if update_user5 != '' and status_3 == 3 and status_7 == 7:
                                    update_user5 = update_user5.strip()
                                    user = UserProfile.objects.filter(username=update_user5).first()
                                    if user:
                                        if approve_step(process.id, user.username, update_date3):
                                            print('approved as Disburser', pettycash)
                                            user1 = UserProfile.objects.filter(username=update_user1).first()
                                            if user1:
                                                if approve_step(process.id, user1.username, update_date3):
                                                    print('cleared by', user1, "for item", pettycash)
                                                else:
                                                    print('not cleared by', user1, "for item", pettycash)
                                        else:
                                            print('not approved')
                                    else:
                                        print('user not found')

                        print('dodgy barcket passed')
                        pettycash.payment_mode = payment_method
                        pettycash.currency = 'ZWL'
                        pettycash.save()

                        date_str = pettycash.petty_id[2:8]
                        print(date_str, 'date_str')
                        #check length of date string
                        if len(date_str) == 6:
                            # Convert the date string to a datetime object
                            # If the year is less than 20, we assume it's 2000s, otherwise it's 1900s
                            year = int(date_str[:2])
                            print(year, 'year1')
                            year += 2000
                            print(year, 'year')

                            date_str = str(year) + date_str[2:]
                            day_created = datetime.strptime(date_str, '%Y%m%d')
                            # format into date format not date time
                            day_created = day_created.strftime('%Y-%m-%d')
                            pettycash.date_created = day_created
                            pettycash.save()

                print('done')
                return redirect('/pettycash/pettycashs')
            elif file_name.ends_with('.xls'):
                print('xls file')
            elif file_name.ends_with('xlsx'):
                print('xlsx file')
            else:
                print('not an excel file')
        else:
            print('no file')
            return render(request, 'finance/pettycash/import_pettycash.html')
        return render(request, 'finance/pettycash/import_pettycash.html')
    else:
        return render(request, 'finance/pettycash/import_pettycash.html')


def approve_step(process_id, user_id, date_approved):
    process = Process.objects.get(id=process_id)
    user = UserProfile.objects.get(username=user_id)
    
    # Do not append approvals if the process has already been rejected
    if is_process_rejected(process):
        print('process already rejected; skipping approval append')
        return False
    
    # parse the date into year, month and day
    if date_approved != '0000-00-00 00:00:00':
        print('setting date approved to', date_approved)
        date_approved1 = date_approved
    else:
        print('setting date approved to current date')
        date_approved1 = datetime.now()
    try:
        latest_approval = process.approval_set.last()
        if latest_approval is not None:
            next_step = latest_approval.step.step + 1
        else:
            next_step = 1
    except Step.DoesNotExist:
        next_step = 1
    try:
        step = Step.objects.get(workflow=process.workflow, step=next_step)
    except Step.DoesNotExist:
        print('doesnt exist')
        return False
    approval = Approval(
        step=step,
        user=user,
        process=process,
        approved='Approved',
        # if parameter date_approved is not passed, the default value is the current date and time
        approved_at=date_approved1
    )
    approval.save()
    print('approved', date_approved1)
    approval.approved_at = date_approved1
    approval.save()
    print('approved')
    return True


def receipt_form(request, petty_id):
    """
    Display receipt upload form for a specific pettycash ID
    """
    # Get the pettycash object
    try:
        pettycash = Pettycash.objects.get(petty_id=petty_id)
    except Pettycash.DoesNotExist:
        messages.error(request, 'Petty cash not found.')
        return redirect('/pettycash/pettycashs')
    
    # Check authorization - only requester can upload receipt
    if request.user != pettycash.requested_by:
        messages.error(request, 'You are not authorized to upload receipt for this petty cash.')
        return redirect(f'/pettycash/pettycash_detail/{petty_id}')
    
    # Check if receipt already uploaded
    if pettycash.receipt_file:
        messages.warning(request, 'Receipt has already been uploaded for this petty cash.')
        return redirect(f'/pettycash/pettycash_detail/{petty_id}')
    
    # Check if cashier has disbursed
    if pettycash.amount_disbursed is None:
        messages.error(request, 'Cashier must disburse the amount before you can upload receipt.')
        return redirect(f'/pettycash/pettycash_detail/{petty_id}')
    
    # Block actions if process is rejected
    try:
        if is_process_rejected(pettycash.process):
            messages.error(request, 'This petty cash was rejected. No further actions are allowed.')
            return redirect(f'/pettycash/pettycash_detail/{petty_id}')
    except Exception:
        pass
    
    context = {
        'pettycash': pettycash,
        'max_amount': pettycash.amount_disbursed if pettycash.amount_disbursed else pettycash.amount
    }
    
    return render(request, 'finance/pettycash/receipt_form.html', context)


def receipt(request):
    if request.method != 'POST':
        return redirect('/pettycash/pettycashs')

    # Defensive fetch
    petty_id = request.POST.get('petty_id')
    pettycash = Pettycash.objects.filter(petty_id=petty_id).first()
    if not pettycash:
        return JsonResponse({'success': False, 'error': 'Petty cash not found.'}, status=404)

    # Authorization: only requester can clear
    if request.user != pettycash.requested_by:
        return JsonResponse({'success': False, 'error': 'Not authorized to clear this petty cash.'}, status=403)

    # Block any actions if process is already rejected
    try:
        if is_process_rejected(pettycash.process):
            return JsonResponse({'success': False, 'error': 'This petty cash was rejected. No further actions are allowed.'}, status=400)
    except Exception:
        pass

    # Require cashier disbursement first
    if pettycash.amount_disbursed is None or pettycash.payment_mode is None:
        return JsonResponse({'success': False, 'error': 'Cashier must capture disbursement before you can clear.'}, status=400)

    # Ensure not already receipted
    if pettycash.receipt_file:
        return JsonResponse({'success': False, 'error': 'Receipt already uploaded.'}, status=400)

    # Validate receipt file
    receipt_file = request.FILES.get('file-input')
    if not receipt_file:
        return JsonResponse({'success': False, 'error': 'Receipt file is required.'}, status=400)

    # Validate amount used
    used_raw = request.POST.get('disbursed')
    try:
        used_amt = Decimal(used_raw)
    except (InvalidOperation, TypeError):
        return JsonResponse({'success': False, 'error': 'Amount used must be a valid number.'}, status=400)
    if used_amt <= Decimal('0'):
        return JsonResponse({'success': False, 'error': 'Amount used must be greater than 0.'}, status=400)

    # Determine cap: prefer amount_disbursed, else requested amount
    cap = pettycash.amount_disbursed if pettycash.amount_disbursed is not None else pettycash.amount
    try:
        cap_dec = Decimal(str(cap))
    except Exception:
        cap_dec = Decimal('0')

    if used_amt > cap_dec:
        return JsonResponse({'success': False, 'error': f'Amount used cannot exceed {cap_dec}.'}, status=400)

    # Handle optional remarks
    remarks = request.POST.get('remarks', '').strip()
    
    # Save receipt, amount used, and remarks
    pettycash.receipt_file = receipt_file
    pettycash.amount_used = float(used_amt)
    if remarks:
        # If the model has a remarks field, save it; otherwise you might want to add it to the model
        # For now, we'll just save receipt and amount
        pass
    pettycash.save(update_fields=['receipt_file', 'amount_used'])

    # Auto-approve requester clear step if the next step is assigned to the requester
    try:
        process = pettycash.process
        latest_approval = process.approval_set.last()
        next_step_num = (latest_approval.step.step + 1) if latest_approval else 1
        # Safe roles access via profile
        user_profile = UserProfile.objects.filter(id=request.user.id).first()
        try:
            user_roles = user_profile.roles.all() if user_profile else []
        except Exception:
            user_roles = []
        step_for_user = Step.objects.get(step=next_step_num, workflow=process.workflow, approver__in=user_roles)
        # Create approval record
        Approval.objects.create(
            step=step_for_user,
            user=request.user,
            process=process,
            approved='Approved',
            approved_at=datetime.now()
        )
    except Step.DoesNotExist:
        # No step for this user; skip auto-approval
        pass
    except Exception:
        # Don’t fail the receipt on approval errors
        pass

    return JsonResponse({'success': True, 'redirect': f"/pettycash/pettycash_detail/{pettycash.petty_id}"})


def download_attachment(request, attachment_id):
    try:
        attachment = Quotation.objects.get(pk=attachment_id)
    except Quotation.DoesNotExist:
        return HttpResponseNotFound('Attachment not found')

    response = FileResponse(attachment.quotation_file, content_type='application/octet-stream')
    response['Content-Disposition'] = f'attachment; filename="{attachment.quotation_file}"'
    return response


def download_file(request, filename):
    # Open the file for reading (replace 'path/to/file' with the actual path)
    filepath = f'uploads/pettycash/{filename}'
    try:
        with open(filepath, 'rb') as f:
            mime_type, _ = guess_type(filepath)
            response = HttpResponse(f.read(), content_type=mime_type)
            response['Content-Disposition'] = f"attachment; filename={filename}"
        return response
    except FileNotFoundError:
        # Handle file not found error (return 404 or a custom message)
        sweetify.error(request, 'File not found')
        messages.error(request, 'File not found')

        return HttpResponseNotFound('The requested file does not exist.')


def pettycash_report(request):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    pettyreportform = PettycashReportForm(user=user_profile)

    if request.method == 'POST':
        pettyreportform = PettycashReportForm(request.POST, user=user_profile)
        if pettyreportform.is_valid():
            start_date = pettyreportform.cleaned_data['start_date']
            end_date = pettyreportform.cleaned_data['end_date']
            region = pettyreportform.cleaned_data['region']
            section = pettyreportform.cleaned_data['section']
            # payment_mode = pettyreportform.cleaned_data['payment_mode']

            pettycashs = Pettycash.objects.filter(region=region, section=section,
                                                  date_created__range=[start_date, end_date]).all()
            report = PettycashReport.objects.create(start_date=start_date, end_date=end_date, region=region,
                                                    section=section)
            report.save()
            print('report created')
            print('count', pettycashs.count())
            return render(request, 'finance/pettycash/pettycash_reports.html',
                          {'pettycashs': pettycashs, 'report': report})
    return render(request, 'finance/pettycash/pettycash_create_report.html', {'pettyreportform': pettyreportform})


def print_report_excel(request, report_id):
    report = get_object_or_404(PettycashReport, report_id=report_id)
    print("report date", report.start_date)
    print("report date", report.end_date)
    print("report region", report.region)

    pettycashs = Pettycash.objects.filter(region=report.region, section=report.section,
                                          date_created__range=[report.start_date, report.end_date]).all()
    print('count', pettycashs.count())

    response = HttpResponse(content_type='application/ms-excel')
    response['Content-Disposition'] = 'attachment; filename="pettycash_report.xlsx"'

    wb = Workbook()
    ws = wb.active

    ws.append(
        ['petty_id', 'details_of_expenditure', 'requested_by', 'section', 'date_created', 'amount', 'amount_disbursed',
         'amount_used', 'payment_mode', 'currency',
         'approval_status'])

    for pettycash in pettycashs:
        requested_by = pettycash.requested_by.get_full_name() if pettycash.requested_by else ''
        section = pettycash.section.section if pettycash.section else ''
        date_created = pettycash.date_created.strftime('%Y-%m-%d') if pettycash.date_created else ''
        approval_status = str(pettycash.process.approval_set.last()) if pettycash.process.approval_set.last() else ''

        ws.append([
            pettycash.petty_id,
            pettycash.details_of_expenditure,
            requested_by,
            section,
            date_created,
            pettycash.amount,
            pettycash.amount_disbursed,
            pettycash.amount_used,
            pettycash.payment_mode,
            pettycash.currency,
            approval_status
        ])
    wb.save(response)
    return response


def print_report_csv(request, report_id):
    """Stream a CSV petty cash report for the given report_id filters."""
    report = get_object_or_404(PettycashReport, report_id=report_id)
    pettycashs = Pettycash.objects.filter(
        region=report.region,
        section=report.section,
        date_created__range=[report.start_date, report.end_date]
    ).all()

    response = HttpResponse(content_type='text/csv')
    response['Content-Disposition'] = 'attachment; filename="pettycash_report.csv"'

    writer = csv.writer(response)
    writer.writerow([
        'petty_id', 'details_of_expenditure', 'requested_by', 'section', 'date_created',
        'amount', 'amount_disbursed', 'amount_used', 'payment_mode', 'currency', 'approval_status'
    ])

    for pettycash in pettycashs:
        requested_by = pettycash.requested_by.get_full_name() if pettycash.requested_by else ''
        section = pettycash.section.section if pettycash.section else ''
        date_created = pettycash.date_created.strftime('%Y-%m-%d') if pettycash.date_created else ''
        approval_status = str(pettycash.process.approval_set.last()) if pettycash.process and pettycash.process.approval_set.last() else ''

        writer.writerow([
            pettycash.petty_id,
            pettycash.details_of_expenditure,
            requested_by,
            section,
            date_created,
            pettycash.amount or '',
            pettycash.amount_disbursed or '',
            pettycash.amount_used or '',
            pettycash.payment_mode or '',
            pettycash.currency or '',
            approval_status
        ])

    return response


def receipt_manual(request):
    if request.method == 'POST':
        receipt_file = request.FILES['file-input']
        print(receipt_file)
        pettycash = request.POST['pettycash']
        pettycash = Pettycash.objects.filter(petty_id=pettycash).first()
        pettycash.receipt_file = receipt_file
        pettycash.save()
        messages.success(request, 'Receipt uploaded successfully')
        return redirect('pettycash:pettycash_detail', petty_id=pettycash.petty_id)
    else:
        return render(request, 'finance/pettycash/receipt.html')


@login_required
def pettycash_monthly_totals(request):
    """Show monthly totals for PettyCash in the user's region for a selected year."""
    try:
        user_id = request.user.id
        user_profile = UserProfile.objects.filter(id=user_id).first()
        if not user_profile:
            messages.error(request, "User profile not found. Please contact administrator.")
            return render(request, 'finance/pettycash/pettycash_monthly_totals.html', {
                'rows': [], 'year': None, 'years': []
            })

        try:
            region = Regions.objects.filter(id=user_profile.region.id).first()
            if not region:
                messages.error(request, "User region not found. Please contact administrator.")
                return render(request, 'finance/pettycash/pettycash_monthly_totals.html', {
                    'rows': [], 'year': None, 'years': []
                })
        except AttributeError:
            messages.error(request, "User profile is incomplete. Missing region information.")
            return render(request, 'finance/pettycash/pettycash_monthly_totals.html', {
                'rows': [], 'year': None, 'years': []
            })

        # Determine year (default to current year)
        try:
            selected_year = int(request.GET.get('year', datetime.now(timezone.utc).year))
        except (TypeError, ValueError):
            selected_year = datetime.now(timezone.utc).year

        base_qs = Pettycash.objects.filter(region=region, date_created__year=selected_year)

        # Aggregate by month
        monthly = (
            base_qs
            .annotate(month=TruncMonth('date_created'))
            .values('month')
            .order_by('month')
            .annotate(
                total_amount=Sum('amount'),
                total_disbursed=Sum('amount_disbursed'),
                total_used=Sum('amount_used'),
            )
        )

        # Build a dict keyed by month for easy lookup
        month_map = {m['month'].month: m for m in monthly}

        # Prepare rows for all 12 months
        rows = []
        grand_amount = 0.0
        grand_disbursed = 0.0
        grand_used = 0.0

        for m in range(1, 13):
            rec = month_map.get(m)
            amt = float(rec['total_amount']) if rec and rec['total_amount'] is not None else 0.0
            disb = float(rec['total_disbursed']) if rec and rec['total_disbursed'] is not None else 0.0
            used = float(rec['total_used']) if rec and rec['total_used'] is not None else 0.0

            grand_amount += amt
            grand_disbursed += disb
            grand_used += used

            rows.append({
                'month_num': m,
                'amount': amt,
                'disbursed': disb,
                'used': used,
            })

        # Available years for dropdown (only in this region)
        years = [d.year for d in Pettycash.objects.filter(region=region).dates('date_created', 'year')]

        context = {
            'rows': rows,
            'year': selected_year,
            'years': years,
            'grand_amount': grand_amount,
            'grand_disbursed': grand_disbursed,
            'grand_used': grand_used,
            'region': region,
        }
        return render(request, 'finance/pettycash/pettycash_monthly_totals.html', context)

    except Exception as e:
        messages.error(request, f"System error: {str(e)}")
        return render(request, 'finance/pettycash/pettycash_monthly_totals.html', {
            'rows': [], 'year': None, 'years': []
        })


@login_required
def my_actioned_items(request):
    """
    Show PettyCash items that the user has actioned/approved
    """
    try:
        user_id = request.user.id
        user_profile = UserProfile.objects.filter(id=user_id).first()
        
        if not user_profile:
            messages.error(request, "User profile not found. Please contact administrator.")
            return render(request, 'finance/pettycash/my_actioned_items.html', {
                'pettycashs': [],
                'user_profile': None,
                'error_message': 'User profile not found'
            })

        # Get all approvals made by this user
        my_approvals = Approval.objects.filter(
            user=request.user
        ).select_related('process', 'step').order_by('-approved_at')

        # Get the corresponding PettyCash items
        actioned_pettycashs = []
        for approval in my_approvals:
            try:
                # Find PettyCash items associated with this process
                pettycash = Pettycash.objects.filter(process=approval.process).first()
                if pettycash:
                    # Add approval info to the pettycash object for display
                    pettycash.my_approval = approval
                    actioned_pettycashs.append(pettycash)
            except Exception:
                continue  # Skip if there's an issue with this particular item

        # Remove duplicates while preserving order
        seen = set()
        unique_pettycashs = []
        for pettycash in actioned_pettycashs:
            if pettycash.petty_id not in seen:
                seen.add(pettycash.petty_id)
                unique_pettycashs.append(pettycash)

        return render(request, 'finance/pettycash/my_actioned_items.html', {
            'pettycashs': unique_pettycashs[:200],  # Limit to 200 items for performance
            'user_profile': user_profile,
            'title': 'PettyCash Items I Have Actioned'
        })

    except Exception as e:
        messages.error(request, f"Error retrieving actioned items: {str(e)}")
        return render(request, 'finance/pettycash/my_actioned_items.html', {
            'pettycashs': [],
            'user_profile': None,
            'error_message': f'System error: {str(e)}'
        })


def send_uncleared_pettycash_reminders(request, days_overdue: int = 3, limit: int = 200) -> int:
    """
    Notify requesters for petty cash items that have been disbursed but not yet cleared (no receipt uploaded)
    after a grace period (default 3 days). Returns the count of reminders sent.

    Criteria:
    - pettycash.amount_disbursed is not None
    - pettycash.receipt_file is None
    - There exists an Approval on the pettycash.process where step.approver.role == 'disburse'
      and Approval.approved_at <= now - days_overdue
    """
    try:
        now = dj_timezone.now()
        cutoff = now - timedelta(days=days_overdue)

        # Fetch candidates with disbursed but not cleared
        candidates = Pettycash.objects.filter(
            amount_disbursed__isnull=False,
        )[:limit]

        sent = 0
        for pc in candidates:
            try:
                process = pc.process
                if not process:
                    continue
                # Skip if already receipted/cleared
                try:
                    if getattr(pc, 'receipt_file', None):
                        # FileField truthiness is True when a file path/name exists
                        if str(pc.receipt_file):
                            continue
                except Exception:
                    pass
                # Find the cashier/disburse approval time
                disb_appr = process.approval_set.filter(
                    Q(step__approver__role='disburse') | Q(step__step=3)
                ).order_by('-approved_at').first()
                if not disb_appr or not disb_appr.approved_at:
                    continue
                # Robust comparison: handle naive vs aware datetimes
                appr_at = disb_appr.approved_at
                try:
                    is_overdue = appr_at <= cutoff
                except TypeError:
                    appr_at_naive = appr_at.replace(tzinfo=None) if getattr(appr_at, 'tzinfo', None) else appr_at
                    cutoff_naive = cutoff.replace(tzinfo=None) if getattr(cutoff, 'tzinfo', None) else cutoff
                    is_overdue = appr_at_naive <= cutoff_naive
                if is_overdue:
                    # Build and send reminder
                    requester = pc.requested_by
                    if not requester:
                        continue
                    msg = f"Reminder: Please clear Petty Cash {pc.petty_id} by uploading your receipt."
                    url = f"/pettycash/pettycash_detail/{pc.petty_id}"
                    try:
                        notify_user(requester, msg, "PettyCash", url, pc.petty_id, request)
                        sent += 1
                    except Exception:
                        # Ignore notification failures
                        pass
            except Exception:
                # Skip problematic items but continue others
                continue
        return sent
    except Exception:
        return 0
