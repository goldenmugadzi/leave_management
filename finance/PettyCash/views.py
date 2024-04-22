from datetime import datetime
from random import randrange
import csv

from django.contrib.auth.decorators import login_required
from django.shortcuts import render, redirect
from django.urls import reverse

from approve.forms import ApprovalForm
from approve.models import Step
from approve.views import intiate
from it.users.models import UserProfile, Roles, Sections, Regions
from approve.models import Process, Workflow, Step, Approval
from .forms import PettycashForm, QuotationFormSet
from .models import Pettycash, Quotation


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
            custom_user_roles["pettycash"] = role
    pettycash_role = str(custom_user_roles["pettycash"])
    print(pettycash_role)

    pettycash_item = Pettycash.objects.get(petty_id=petty_id)

    if pettycash_role == "disburse":
        payment_mode = request.POST.get('payment_mode')
        # print(payment_mode)
        if payment_mode and payment_mode != '':
            pettycash_item.payment_mode = payment_mode
            pettycash_item.save()

    approvalForm = None
    to = None
    user_roles = request.user.roles.all()  # Accessing the user's roles through the 'roles' attribute

    try:
        last_approved = pettycash_item.process.approval_set.last().step.step
    except AttributeError:
        last_approved = 0

    next_step = last_approved + 1

    try:
        newStep = Step.objects.get(step=next_step, workflow=pettycash_item.process.workflow,
                                   approver__in=user_roles)
        if newStep and request.user.section == pettycash_item.section and next_step == 1:
            approvalForm = ApprovalForm
            to = newStep.to
            print(pettycash_role)
        elif newStep:
            approvalForm = ApprovalForm
            to = newStep.to
    except Step.DoesNotExist:
        pass

    approved_steps = pettycash_item.process.approval_set.all().values_list('step__step', flat=True)
    return render(request, 'finance/pettycash/pettycash_detail.html',
                  {'pettycash': pettycash_item, 'approved_steps': approved_steps, 'approvalForm': approvalForm,
                   'to': to, 'pettycash_role': pettycash_role, 'user_groups': user_groups})


@login_required
def create_pettycash(request):
    if request.method == 'POST':
        form = PettycashForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
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

            for quotation_form in formset:
                quotation = quotation_form.save(commit=False)
                quotation.pettycash = pettycash
                quotation.save()

            url = reverse('pettycash:pettycash_detail', args=[pettycash.petty_id])
            return redirect(url)
    else:
        form = PettycashForm()
        formset = QuotationFormSet()

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
            custom_user_roles["pettycash"] = role
    pettycash_role = str(custom_user_roles["pettycash"])

    if pettycash_role == "approve":
        for pettycash in Pettycash.objects.filter(section=request.user.section):
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
        for pettycash in Pettycash.objects.all():
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

    return render(request, 'finance/pettycash/view_all_pettycashs.html', {'pettycashs': pettycashs_to_process})


@login_required
def view_all_pettycashs(request):
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
            custom_user_roles["pettycash"] = role
    pettycash_role = str(custom_user_roles["pettycash"])

    if pettycash_role == "create":
        pettycashs = Pettycash.objects.filter(requested_by=request.user)
    elif pettycash_role == "approve":
        pettycashs = Pettycash.objects.filter(section=request.user.section)
    else:
        pettycashs = Pettycash.objects.all()
    return render(request, 'finance/pettycash/view_all_pettycashs.html', {'pettycashs': pettycashs})


@login_required
def import_pettycash(request):
    if request.method == 'POST':
        file = request.FILES['file']
        # file2 = request.FILES['file2']
        # if file there filter based on file type
        if file:
            file_name = file.name
            # file_name2 = file2.name
            if file_name.endswith('.csv'):
                # if file_name.endswith('.csv') or file_name2.endswith('.csv'):
                # read the csv file
                print('csv file')

                decoded_file = file.read().decode('cp1252').splitlines()
                # decoded_file2 = file2.read().decode('cp1252').splitlines()
                reader = csv.DictReader(decoded_file)
                # reader2 = csv.DictReader(decoded_file2)
                for row in reader:
                    petty_id = row['voucher_id']
                    department = row['department']
                    location = row['location']
                    section = row['section']
                    allocation_code1 = row['allocation_code1']
                    description = row['description']
                    quotation_1 = row['quotation_1']
                    quotation_2 = row['quotation_2']
                    quotation_3 = row['quotation_3']
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

                    # if date created is earlier than 2024 then the currency is ZWL,but if its after 2024 its is ZIG
                    # create pettycash if it does not exist
                    PC = Pettycash.objects.filter(petty_id=petty_id).first()
                    if not PC:
                        pettycash = Pettycash.objects.create(
                            petty_id=petty_id,
                            section=Section,
                            details_of_expenditure=description,
                            amount=amount,
                            payment_mode=payment_mode,
                            requested_by=Requester,
                            old_version=True,
                            region=Region,

                        )
                        pettycash.process = intiate(request, 'pettycash')
                        pettycash.save()
                        qoutation_1 = Quotation.objects.create(
                            pettycash=pettycash,
                            quotation_file=quotation_1,
                        )
                        qoutation_1.save()
                        qoutation_2 = Quotation.objects.create(
                            pettycash=pettycash,
                            quotation_file=quotation_2,
                        )
                        qoutation_2.save()
                        qoutation_3 = Quotation.objects.create(
                            pettycash=pettycash,
                            quotation_file=quotation_3,
                        )
                        qoutation_3.save()
                        print(petty_id, 'created')
                    else:
                        print(petty_id, 'already exists')
                for row1 in reader2:
                    voucher_id = row1['voucher_id']
                    section = row1['section']
                    status_1 = row1['status_1']
                    status_2 = row1['status_2']
                    status_3 = row1['status_3']
                    status_4 = row1['status_4']
                    status_5 = row1['status_5']
                    status_6 = row1['status_6']
                    status_7 = row1['status_7']
                    update_user1 = row1['update_user1']
                    update_user2 = row1['update_user2']
                    update_user3 = row1['update_user3']
                    update_user4 = row1['update_user4']
                    update_user5 = row1['update_user5']
                    update_date1 = row1['update_date1']
                    update_date2 = row1['update_date2']
                    update_date3 = row1['update_date3']
                    update_date4 = row1['update_date4']
                    reason_1 = row1['reason_1']
                    reason_2 = row1['reason_2']
                    auth_signature = row1['auth_signature']
                    received_by = row1['received_by']
                    ecno = row1['ecno']
                    date_received = row1['date_received']
                    payment_method = row1['payment_method']
                    ecocash_charge = row1['ecocash_charge']
                    total_disbursed = row1['total_disbursed']
                    actual_amount = row1['actual_amount']
                    ecocash_confirmation = row1['ecocash_confirmation']
                    allocation_code = row1['allocation_code']
                    receipt = row1['receipt']
                    receipt_date = row1['receipt_date']
                    acquittal_date = row1['acquittal_date']
                    checked_by = row1['checked_by']
                    checked_on = row1['checked_on']
                    checked_status = row1['checked_status']
                    reason_3 = row1['reason_3']
                    reason_4 = row1['reason_4']
                    reason_5 = row1['reason_5']
                    requestor_cleared_by = row1['requestor_cleared_by']
                    cashier_cleared_by = row1['cashier_cleared_by']
                    disbursement_remarks = row1['disbursement_remarks']
                    acquittal_remarks = row1['acquittal_remarks']
                    requestor_remarks = row1['requestor_remarks']
                    returned_by = row1['returned_by']
                    date_returned = row1['date_returned']
                    return_remarks = row1['return_remarks']
                    imt_tax = row1['imt_tax']
                    print("now dealing with approvals")
                    # add the date created to the pettycash process
                    pettycash = Pettycash.objects.filter(petty_id=voucher_id).first()
                    pettycash.date_created = update_date1

                    process = Pettycash.objects.filter(petty_id=voucher_id).first().process
                    approval = Approval.objects.filter(process=process).first()
                    # this is the first step of the approval

                    if update_user2 != '':
                        approval.created_at = update_date1
                        step = Step.objects.filter(workflow=process.workflow).first()
                        step.to = "Approve"
                        Role = Role.objects.filter(id=8).first()
                        step.approver = UserProfile.objects.filter(username=update_user2).first()
                        step.step = 1
                        approval.step = step
                        step.save()
                        approval.save()
                        user = UserProfile.objects.filter(username=update_user2).first()


                    approval.user = user
                    approval.process = process
                    approval.step = step

                    approval.save()
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
