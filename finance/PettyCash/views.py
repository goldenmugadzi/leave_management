from datetime import datetime, timezone
from mimetypes import guess_type
from random import randrange
import csv

import sweetify
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponseNotFound, FileResponse, HttpResponse
from django.shortcuts import render, redirect, get_object_or_404
from django.urls import reverse
from openpyxl.workbook import Workbook

from ACE2.utils import find_ace_section_head, find_pettycash_section_head
from approve.forms import ApprovalForm
from approve.views import intiate
from it.users.models import UserProfile, Roles, Sections, Regions, Notification
from approve.models import Process, Step, Approval
from .forms import PettycashForm, QuotationFormSet, PettycashReportForm
from .models import Pettycash, Quotation, PettycashReport

from ..comparative_schedules.views import notify_user


@login_required
def pettyCash_detail(request, petty_id):
    global payment_mode
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    user_groups = user_profile.groups.values_list('name', flat=True)

    custom_user_roles = {
        "pettycash": {},
    }

    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()

        if role.application == "pettycash":
            custom_user_roles["pettycash"] = role.role
    pettycash_role = str(custom_user_roles["pettycash"])
    # print(pettycash_role)

    pettycash_item = Pettycash.objects.get(petty_id=petty_id)

    # return validation to clear validation = pettycash_item.process.approval_set.filter(approved='Approved',
    # step__approver__in=user_profile.roles.all()).exists()) print(validation)

    quotations = Quotation.objects.filter(pettycash=pettycash_item).all()
    # print(quotations.count())

    if pettycash_role == "disburse" and request.method == 'POST':
        payment_mode = request.POST.get('payment_mode')
        amount_disbursed = request.POST.get('amount_disbursed')
        payee = request.POST.get('payee')
        print(payment_mode)
        if payment_mode and payment_mode != '':
            pettycash_item.payment_mode = payment_mode
            pettycash_item.amount_disbursed = amount_disbursed
            pettycash_item.payee = payee
            pettycash_item.save()
            user = pettycash_item.requested_by
            userp = UserProfile.objects.filter(id=user).first()

            msg = "Your Pettycash " + pettycash_item.petty_id + " has a payment method added by Cashier"
            url = "/pettycash/pettycash_detail/" + pettycash_item.petty_id
            notify_user(userp, msg, "Pettycash", url, pettycash_item.petty_id, request)

    approvalForm = None
    to = None
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute
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
    if approval_status != "Rejected":
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

    try:
        print(pettycash_role, clear, requestor, clear_minus, cashier_approved)
        notification_obj = Notification.objects.filter(notification_id=petty_id).first()
        section_created = pettycash_item.section
        section_heads = find_pettycash_section_head(section_created)
        if section_heads:
            print('doing')
            print("user prof ", user_profile, ' sect head ', section_heads)

            if user_profile.username == section_heads:
                print('notification', notification_obj)
                notification_obj.is_read = True
                notification_obj.save()
                print(notification_obj, ' now set to read')
    except Exception as e:
        print(e)

    return render(request, 'finance/pettycash/pettycash_detail.html',
                  {'pettycash': pettycash_item, 'approved_steps': approved_steps, 'approvalForm': approvalForm,
                   'to': to, 'pettycash_role': pettycash_role, 'user_groups': user_groups, 'quotations': quotations
                      , 'clear': clear, "clear_minus": clear_minus, 'requestor': requestor, 'cashier': cashier,
                   'cashier_approved': cashier_approved})


@login_required
def create_pettycash(request):
    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()
    if request.method == 'POST':
        print("post")
        form = PettycashForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
        user_id = request.user.id
        user_profile = UserProfile.objects.filter(id=user_id).first()

        user_groups = user_profile.groups.values_list('name', flat=True)

        custom_user_roles = {
            "pettycash": {},
        }

        roles_ = user_profile.roles.all()
        for _role in roles_:
            role = Roles.objects.filter(id=_role.id).first()

            if role.application == "pettycash":
                custom_user_roles["pettycash"] = role.role
        pettycash_role = str(custom_user_roles["pettycash"])
        print(pettycash_role)
        if pettycash_role == "create":
            if form.is_valid() and formset.is_valid():
                pettycash = form.save(commit=False)
                pettycash.process = intiate(request, 'pettycash')
                pettycash.requested_by = request.user

                rand = randrange(1, 1000)
                rand2 = str(rand)
                date = datetime.now()
                date = date.strftime("%Y%m%d")

                petty_id = "PC" + date + rand2
                pettycash.petty_id = petty_id
                pettycash.save()
                print(pettycash, 'pettycash created')

                for quotation_form in formset:
                    quotation = quotation_form.save(commit=False)
                    quotation.pettycash = pettycash
                    quotation.save()
                    print(quotation, 'quotation created')

                requester = pettycash.requested_by
                use = UserProfile.objects.filter(id=requester.id).first()
                section_created = use.section

                # notify sh

                section_heads = find_pettycash_section_head(section_created)
                try:
                    print(section_heads, "section_heads")
                    if section_heads:
                        print(section_heads, " section_heads")
                        # budget name
                        # bdg = AssetBudget.objects.filter(budget_id=ace.budget_id).first()
                        # budget_name = bdg.budget_name
                        msg = "Your subordinate " + str(use) + " created " + pettycash.petty_id + " for section " + str(
                            pettycash.section)
                        url = "/pettycash/pettycash_detail/" + pettycash.petty_id
                        section_heads = UserProfile.objects.filter(username=section_heads).first()
                        notify_user(section_heads, msg, "Pettycash", url, pettycash.petty_id, request)
                        print("notified", section_heads)
                        sweetify.success(request, "Pettycash created successfully")
                        messages.success(request, "Pettycash created successfully")
                        print("notified", section_heads)

                    else:
                        print("no section head")
                        sweetify.error(request, "No section head found")
                        messages.error(request, "No section head found")

                    # for quotation_form in formset:
                    #     quotation = quotation_form.save(commit=False)
                    #     quotation.pettycash2 = pettycash
                    #     quotation.save()

                    pettycash_section = pettycash.section
                    pettycash_sh = find_pettycash_section_head(pettycash_section)


                except:

                    if pettycash_sh:
                        print(pettycash_sh, "pettycash_sh")
                        # bdg = AssetBudget.objects.filter(budget_id=ace.budget_id).first()
                        # budget_name = bdg.budget_name
                        msg = "user  " + str(use) + " created " + pettycash.petty_id + " for section " + str(
                            pettycash.section)
                        url = "/pettycash/pettycash_detail/" + pettycash.petty_id

                        pettycash_sh = UserProfile.objects.filter(username=pettycash_sh).first()
                        notify_user(pettycash_sh, msg, "Pettycash", url, pettycash.petty_id, request)
                        print("notified", pettycash_sh)

                    else:
                        print("no section head")
                        sweetify.error(request, "No section head found")
                        messages.error(request, "No section head found")

                url = reverse('pettycash:pettycash_detail', args=[pettycash.petty_id])
                return redirect(url)
            else:
                form = PettycashForm(user=user_profile)
                formset = QuotationFormSet()
        else:
            sweetify.error(request, "You are not authorized to create a new pettycash")
            messages.error(request, "You are not authorized to create a new pettycash")
            return redirect('/pettycash/pettycashs')

    else:
        form = PettycashForm(user=user_profile)
        formset = QuotationFormSet()
        print("not post")

    return render(request, 'finance/pettycash/create_pettycash.html', {'form': form, 'formset': formset})


@login_required
def pettycash_awaiting_my_action(request):
    """
    for each pettycash.Process in the rfqs,  let current_step = the last pettycash.process.approval if any else 0 and
    let next_step =current_step+1 then check if  next_step=step.step for rfq.process.workflow.step_set filtered by
    approver = user.roles.all.
    """
    pettycashs_to_process = []
    user_roles = request.user.roles.all()

    user_id = request.user.id
    user_profile = UserProfile.objects.filter(id=user_id).first()

    user_groups = user_profile.groups.values_list('name', flat=True)

    custom_user_roles = {
        "pettycash": {},
    }

    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()

        if role.application == "pettycash":
            custom_user_roles["pettycash"] = role.role
    pettycash_role = str(custom_user_roles["pettycash"])
    print(pettycash_role)
    requester = 'create'
    current_year = datetime.now(timezone.utc).year
    region = Regions.objects.filter(id=user_profile.region.id).first()

    # Calculate the starting year
    starting_year = current_year

    if pettycash_role == "approve":
        for pettycash in Pettycash.objects.filter(region=region, section=request.user.section,
                                                  date_created__year__gte=starting_year).only('petty_id',
                                                                                              'date_created').order_by(
            'old_version', '-date_created', 'petty_id')[:800]:
            process = pettycash.process

            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
            else:
                current_step = 0

            next_step = current_step + 1

            workflow = process.workflow
            step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

            if step:
                pettycashs_to_process.append(pettycash)
    elif pettycash_role == requester:
        for pettycash in Pettycash.objects.filter(section=request.user.section, region=region,
                                                  date_created__year__gte=starting_year).only('petty_id',
                                                                                              'date_created').order_by(
            'old_version', '-date_created', 'petty_id')[:800]:
            process = pettycash.process

            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
            else:
                current_step = 0

            next_step = current_step + 1

            workflow = process.workflow
            step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

            if step:
                pettycashs_to_process.append(pettycash)

    else:
        print(user_profile.region.id, 'region')
        print(user_profile.designation.id, 'designation')
        if user_profile.region.id == 4 and user_profile.designation.id == 300:
            sections_to_filter = [416, 415, 414, 413, 412, 411, 410, 407]
            for pettycash in Pettycash.objects.filter(section__id__in=sections_to_filter).order_by(
                    '-date_created', 'petty_id')[:1600]:
                process = pettycash.process

                if process.approval_set.exists():
                    last_approval = process.approval_set.last()
                    current_step = last_approval.step.step
                else:
                    current_step = 0

                next_step = current_step + 1

                workflow = process.workflow
                step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

                if step:
                    pettycashs_to_process.append(pettycash)
                print('phakathi')
        else:
            for pettycash in Pettycash.objects.filter(region=region).order_by('-date_created', 'petty_id')[:1600]:
                process = pettycash.process

                if process.approval_set.exists():
                    last_approval = process.approval_set.last()
                    current_step = last_approval.step.step
                else:
                    current_step = 0

                next_step = current_step + 1

                workflow = process.workflow
                step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

                if step:
                    pettycashs_to_process.append(pettycash)
                print('outside')

    return render(request, 'finance/pettycash/view_all_pettycashs.html', {'pettycashs': pettycashs_to_process,
                                                                          'pettycash_role': pettycash_role,
                                                                          'user_groups': user_groups,
                                                                          'requester': requester})


@login_required
def view_all_pettycashs(request):
    user_roles = request.user.roles.all()

    user_id = request.user.id
    user_profile = UserProfile.objects.prefetch_related('roles').filter(id=user_id).first()
    region = Regions.objects.filter(id=user_profile.region.id).first()

    user_groups = user_profile.groups.values_list('name', flat=True)

    custom_user_roles = {
        "pettycash": {},
    }

    roles_ = user_profile.roles.all()
    for _role in roles_:
        role = Roles.objects.filter(id=_role.id).first()

        if role.application == "pettycash":
            custom_user_roles["pettycash"] = role.role
            print("tr ", role.role)
    pettycash_role = str(custom_user_roles["pettycash"])
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


def receipt(request):
    if request.method == 'POST':
        receipt_file = request.FILES['file-input']
        print(receipt_file)
        used = request.POST['disbursed']
        pettycash = request.POST['petty_id']
        pettycash = Pettycash.objects.filter(petty_id=pettycash).first()
        pettycash.receipt_file = receipt_file
        pettycash.amount_used = used
        pettycash.save()
        messages.success(request, 'Receipt uploaded successfully')
        return redirect('pettycash:pettycash_detail', petty_id=pettycash.petty_id)
    else:
        return redirect('/pettycash/pettycashs')


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
