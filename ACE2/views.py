from datetime import datetime, date
from os.path import basename
from random import randrange

import sweetify
import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound, FileResponse, HttpResponseForbidden
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from django.template import loader
from openpyxl import Workbook
from weasyprint import HTML
from django.db import transaction
from django.utils.dateparse import parse_date

from ACE2.forms import *
from ACE2.utils import find_pettycash_section_head
from approve.forms import ApprovalForm
from approve.models import Step
from approve.views import intiate
from it.users.models import UserProfile, Roles, Designations, Districts, Depots, Notification
from finance.PettyCash.views import approve_step
from finance.comparative_schedules.views import notification_update, notify_user
from .models import AceReport as Report


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
            transaction = Transactions.objects.filter(Ace_id2=str(ace_item.Ace_id2)).first()
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
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute

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
        transaction = Transactions.objects.filter(Ace_id2=str(ace_item.Ace_id)).first()
        # print('transaction: ', transaction)
        # print("transaction: ", transaction)
        print("transaction: ", str(transaction.approval_status))

        if transaction.approval_status != "approved by General Manager":
            budget.balance = budget.balance - ace_item.amount
            budget.to_be_withdrawn = budget.to_be_withdrawn - ace_item.amount
            budget.withdrawal_date = date.today()
            budget.withdrawn = budget.withdrawn + ace_item.amount
            budget.save()

            # transaction

            transaction.approval_status = "approved by General Manager"
            transaction.save()
            print("transaction: ", str(transaction.approval_status))
            user = ace_item.requested_by
            userp = UserProfile.objects.filter(id=user.id).first()

            msg = "Your ACE " + ace_item.Ace_id2 + "has been approved by the General Manager"
            url = "/ace/ace_detail/" + ace_item.Ace_id2
            notify_user(userp, msg, "ACE", url, ace_item.Ace_id2, request)

    ace_quantity = range(ace_item.quantity)
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


def generate_unique_ace_id2():
    """Generate a unique Ace_id2."""
    max_attempts = 10
    for _ in range(max_attempts):
        rand = randrange(1, 1000)
        rand2 = str(rand)
        date_str = datetime.now().strftime("%Y%m%d")
        ace_id2 = "ACE" + date_str + rand2
        if not Ace2.objects.filter(Ace_id2=ace_id2).exists():
            return ace_id2
    raise Exception("Could not generate a unique Ace_id2 after multiple attempts.")

@login_required
def create_Ace(request):
    print('create ace')
    global ace_role
    QuotationFormSet()
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    form = AceForm(user=user_profile)
    formset = QuotationFormSet()
    if request.method == 'POST':
        form = AceForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
        user_id = request.user.id
        user_profile = UserProfile.objects.filter(id=user_id).first()

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
                print(ace_role)

        if ace_role == "create":
            if form.is_valid():
                ace = form.save(commit=False)
                # print(ace.budget_id)
                budget = AssetBudget.objects.filter(budget_name=ace.budget_id, period=2025).first()
                # print(budget)
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
                    ace.process = intiate(request, 'ace')
                    ace.requested_by = request.user

                    user_id = request.user.id
                    user_profile = UserProfile.objects.filter(id=user_id).first()

                    user_designation = Designations.objects.filter(id=user_profile.designation.id).first()
                    user_region = Regions.objects.filter(id=user_profile.region.id).first()
                    designation = user_designation
                    # print(designation)
                    region = user_region

                    # Generate a unique Ace_id2
                    try:
                        ace.Ace_id2 = generate_unique_ace_id2()
                    except Exception as e:
                        sweetify.error(request, "Could not generate a unique ACE ID. Please try again.")
                        messages.error(request, "Could not generate a unique ACE ID. Please try again.")
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})

                    # Final check before saving (should never trigger, but for safety)
                    if Ace2.objects.filter(Ace_id2=ace.Ace_id2).exists():
                        sweetify.error(request, "Duplicate ACE ID detected. Please try again.")
                        messages.error(request, "Duplicate ACE ID detected. Please try again.")
                        return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})

                    rand = randrange(1, 1000)
                    rand2 = str(rand)
                    date = datetime.now()
                    date = date.strftime("%Y%m%d")

                    ace_id2 = "ACE" + date + rand2
                    ace.Ace_id2 = ace_id2

                    # check if ace_id2 exists
                    ace_id2_exists = Ace2.objects.filter(Ace_id2=ace_id2).exists()
                    # i want ths to loop till ace_id2 is unique
                    while ace_id2_exists:
                        rand = randrange(1, 1000)
                        rand2 = str(rand)
                        date = datetime.now()
                        date = date.strftime("%Y%m%d")
                        ace_id2 = "ACE" + date + rand2
                        ace.Ace_id2 = ace_id2
                        print("now trying ", ace_id2)
                        ace_id2_exists = Ace2.objects.filter(Ace_id2=ace_id2).exists()

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
                    ace.date_created = date
                    ace.save()

                    ace_code = ace.section
                    print(ace_code)
                    section = Sections.objects.filter(section=ace_code).first()
                    print(section)
                    # print(ace_code)
                    # code = section.code
                    # ace.allocation_code_of_expenditure = code
                    ace.save()
                    attachments = request.FILES.getlist('attachments')
                    for attachment in attachments:
                        attachment = Quotation(quotation_file=attachment,
                                               ace2=ace)
                        attachment.save()

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

                    if str(ace.classification) == "Project":
                        # the idea is that if its ace of type project there need to be added other project details
                        url = reverse('Ace:ace_detail_project', args=[ace.Ace_id2])
                        return redirect(url)
                    else:
                        url = reverse('Ace:ace_detail', args=[ace.Ace_id2])
                        return redirect(url)
                else:
                    messages.error(request, "ace not created")
                    sweetify.error(request, "not created")
                    if balance_after_ace < 0:
                        messages.error(request, "the ace requires more than the current budget resulting in a "
                                                "negative balance")
                        sweetify.error(request, "the ace requires more than the current budget resulting in a "
                                                "negative balance")
                    return render(request, 'finance/ace2/create_ace.html',
                                  {'form': form, 'formset': formset, 'error_message': "Insufficient Balance"})
            else:
                form = AceForm(user=user_profile)
                formset = QuotationFormSet()
        else:
            sweetify.error(request, "You are not allowed to create Ace")
            messages.error(request, "You are not allowed to create")
            # url = reverse('/acee/aces')
            return redirect('/ace/aces')

    return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})


@login_required
def ace_awaiting_my_action(request):
    """
    Show ACEs awaiting the user's action, and ACEs created by the user (with demarcation).
    """
    aces_to_process = []
    user_roles = request.user.roles.all()

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
            # Skip if any approval is "Rejected"
            if process and process.approval_set.filter(approved="Rejected").exists():
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
            # Skip if any approval is "Rejected"
            if process and process.approval_set.filter(approved="Rejected").exists():
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
    user_roles = request.user.roles.all()

    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    region = Regions.objects.filter(id=user_profile.region.id).first()
    section = Sections.objects.filter(section=user_profile.section).first()
    print(section, " section")

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
    requester = "create"

    if ace_role == "create":
        aces = Ace2.objects.filter(requested_by=request.user)
    elif ace_role == "pass":
        aces = Ace2.objects.filter(section=section, region=region)
    else:
        print('kings')
        aces = Ace2.objects.filter(region=region)
        print(aces)

    return render(request, 'finance/ace2/view_all_aces.html', {'aces': aces,
                                                               'requester': requester, 'ace_role': ace_role})


def add_project_details(request, Ace_id2):
    if request.method == 'POST':
        form = ProjectDetailForm(request.POST, request.FILES)
        if form.is_valid():
            project_details = form.save(commit=False)
            # add items from form to already existing ace object and convert to float before saving
            total_connection_fee = (float(project_details.present_tariff) + float(project_details.present_fmc) +
                                    float(project_details.capital_contribution) + float(project_details.materials) +
                                    float(project_details.labour) + float(project_details.transport))

            ace = Ace2.objects.filter(Ace_id2=Ace_id2).first()
            ace.present_tariff = project_details.present_tariff
            ace.present_fmc = project_details.present_fmc
            ace.capital_contribution = project_details.capital_contribution
            ace.materials = project_details.materials
            ace.labour = project_details.labour
            ace.transport = project_details.transport
            ace.total_connection_fee = total_connection_fee
            ace.save()
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
    except Budget.DoesNotExist:
        return JsonResponse({'error': 'Budget not found'}, status=404)


def download_attachment(request, attachment_id):
    try:
        attachment = Quotation.objects.get(pk=attachment_id)
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

    # new_user = {
    #     "id": user_profile.pk,
    #     "username": user_profile.username,
    #     "firstname": user_profile.first_name,
    #     "lastname": user_profile.last_name,
    #     "email": user_profile.email,
    #     "section": section_used,
    #     "depot": depot,
    #     "district": district,
    #     "region": region,
    #     "roles": custom_user_roles,
    #     "designation": user_designation,
    # }
    user_title = request.user.get_full_name()
    print(section_used)
    section_budget = AssetBudget.objects.filter(region=region)
    # print(section_budget)
    user_title = request.user.get_full_name()
    l = request.user.groups.values_list('name', flat=True)

    # QuerySet Object

    user_page = 'ace/budgets_index.html'
    print(section_budget)

    return render(request, user_page, {"title": "All Records",
                                       "context": section_budget,
                                       "user_title": user_title,
                                       "user_groups": user_groups})


@login_required
def add_asset_number(request):
    if request.method == 'POST':
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
                # create assetbudget object using this information if asset budget doesn't exist
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
def create_virament(request):
    # Creates new virament
    # 1. Initializes workflow process
    # 2. Records transaction
    # 3. Handles attachments
    # 4. Links to source/target budgets
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    form = ViramentForm(user=user_profile)
    formset = QuotationFormSet()
    if request.method == 'POST':
        form = ViramentForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
        if form.is_valid():
            virament = form.save(commit=False)
            virament.process = intiate(request, 'virement')
            virament.requested_by = request.user
            virament.region = request.user.region
            virament.save()
            #add attachments
            attachments = request.FILES.getlist('attachments')
            for attachment in attachments:
                attachment = Quotation(quotation_file=attachment,
                                       virament=virament)
                attachment.save()

            #create transaction
            transaction = Transactions.objects.create(
                virament=virament,
                details_of_expenditure="virement of " + str(virament.from_budget) + " to " + str(virament.to_budget),
                approval_status="created",
                region=request.user.region,
                amount=virament.amount,
                budget=virament.from_budget,
                section=virament.section
            )
            transaction.section = virament.section
            transaction.save()
            url = reverse('Ace:virament_detail', args=[virament.virament_id])
            return redirect(url)
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
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute

    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    clear = False
    clear_minus = False
    approve_now = False

    user_groups = user_profile.groups.values_list('name', flat=True)

    custom_user_roles = {
        "virement": {},
    }

    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()

        if role.application == "virement":
            custom_user_roles["virement"] = role
    virement_role = str(custom_user_roles["virement"])

    try:
        last_approved = virament_item.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0
    if virement_role == "create" or virement_role == "order":
        if len(virament_item.process.approval_set.all()) == len(virament_item.process.workflow.step_set.all()):
            clear = True

    approval_status = virament_item.process.approval_set.last().approved if virament_item.process.approval_set.last() else ""
    if approval_status != "Rejected":

        next_step = last_approved + 1
        if len(virament_item.process.approval_set.all()) == len(virament_item.process.workflow.step_set.all()):
            approve_now = True

        try:
            newStep = Step.objects.get(step=next_step, workflow=virament_item.process.workflow,
                                       approver__in=user_roles)

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

    print(approve_now)
    if approve_now:

        balance_before_from = "Actioned"
        balance_before_to = "Actioned"
        balance_after_from = "Actioned"
        balance_after_to = "Actioned"

        # budget calculations
        fbudget = virament_item.from_budget
        tbudget = virament_item.to_budget

        fbudget = AssetBudget.objects.get(budget_id=fbudget.budget_id)
        tbudget = AssetBudget.objects.get(budget_id=tbudget.budget_id)
        print("virament: ", virament_item.virament_id)
        transaction = Transactions.objects.filter(virament_id=str(virament_item.virament_id)).first()
        # print("transaction: ", transaction)
        print("transaction: ", str(transaction.approval_status))

        if transaction.approval_status != "approved by General Manager" and virement_role == "approve":
            fbudget.balance = fbudget.balance - virament_item.amount
            # budget.to_be_withdrawn = budget.to_be_withdrawn - virament_item.amount
            fbudget.withdrawal_date = date.today()
            fbudget.withdrawn = fbudget.withdrawn + virament_item.amount
            # fbudget.balance = fbudget.balance - virament_item.amount
            fbudget.save()

            # budget viremented to
            tbudget.balance = tbudget.balance + virament_item.amount
            tbudget.allocated = tbudget.allocated + virament_item.amount
            tbudget.save()

            # transaction

            transaction.approval_status = "approved by General Manager"
            transaction.save()
            print("transaction: ", str(transaction.approval_status))

    # ace_quantity = range(virament_item.quantity)
    approved_steps = virament_item.process.approval_set.all().values_list('step__step', flat=True)

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
    for each ace2.Process ,  let current_step = the last pettycash.process.approval if any else 0 and
    let next_step =current_step+1 then check if  next_step=step.step for rfq.process.workflow.step_set filtered by
    approver = user.roles.all.
    """
    viraments_to_process = []
    user_roles = request.user.roles.all()

    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    user_groups = user_profile.groups.values_list('name', flat=True)

    custom_user_roles = {
        "virement": {},
    }

    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()

        if role.application == "virement":
            custom_user_roles["virement"] = role
    virement_role = str(custom_user_roles["virement"])
    requester = "create"

    print(virement_role)

    if virement_role == "pass":
        # Only show viraments in the user's section and region
        viraments_qs = Asset_budget_Virament.objects.filter(
            section=request.user.section,
            region=request.user.region
        )
    else:
        # Only show viraments in the user's region
        viraments_qs = Asset_budget_Virament.objects.filter(
            region=request.user.region
        )

    for virement in viraments_qs:
        process = virement.process

        # Only show if the user is the correct approver for the next step
        if process.approval_set.exists():
            last_approval = process.approval_set.last()
            current_step = last_approval.step.step
        else:
            current_step = 0

        next_step = current_step + 1
        workflow = process.workflow
        step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

        # Only add if the user is the approver for this step
        if step:
            # Optionally, check if the user is in the approver list for this step
            if step.approver.filter(id__in=request.user.roles.values_list('id', flat=True)).exists():
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
    region = Regions.objects.filter(id=user_profile.region.id).first()
    transactions = Transactions.objects.filter(budget_id=budget_id)
    return render(request, 'finance/ace2/view_all_transactions.html', {'transactions': transactions})


@login_required
def ace_reports(request):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    ace_report_form = AceReportForm(user=user_profile)

    if request.method == 'POST':
        ace_report_form = AceReportForm(request.POST)
        if ace_report_form.is_valid():
            start_date = ace_report_form.cleaned_data['start_date']
            end_date = ace_report_form.cleaned_data['end_date']
            region = ace_report_form.cleaned_data['region']
            budget = ace_report_form.cleaned_data['budget_id']

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
                return render(request, 'finance/ace2/ace_reports.html', {'aces': aces, 'report': report})
            else:  # All Budgets selected
                # Do NOT save the report, just filter ACEs for all budgets
                aces = Ace2.objects.filter(
                    date_created__range=[start_date, end_date],
                    region=region
                )
                return render(request, 'finance/ace2/ace_reports.html', {'aces': aces, 'report': None})

    return render(request, 'finance/ace2/ace_create_reports.html', {'ace_report_form': ace_report_form})


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
        region = get_object_or_404(Regions, id=region_id)
        aces = Ace2.objects.filter(
            date_created__range=[start_date, end_date],
            region=region
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
    print("report budget", budget.budget_id)
    if budget and region_obj:

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

# @login_required
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
    Show ACE items the current user has actioned (approved/rejected).
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
            print("ace role",ace_role)
            break
    
    # Get all ACEs where the current user has an approval in the process
    actioned_aces = []
    
    # Find all ACEs
    all_aces = Ace2.objects.filter(region=region)
    
    # Check each ACE for this user's approvals
    for ace in all_aces:
        process = ace.process
        if process and process.approval_set.exists():
            approvals = process.approval_set.all()
            for approval in approvals:
                if approval.user == request.user:
                    actioned_aces.append(ace)
                    break

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
                total_steps = process.workflow.step_set.count()
                
                # If we're at the step before the last step, item is pending GM approval
                if current_step == total_steps - 1:
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
    aces = Ace2.objects.filter(budget_id=budget)
    # Total amount used by ACEs
    total_used = aces.aggregate(total=models.Sum('amount'))['total'] or 0
    # Other features
    context = {
        'budget': budget,
        'aces': aces,
        'total_used': total_used,
    }
    return render(request, 'finance/ace2/asset_budget_report.html', context)
