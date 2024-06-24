from datetime import datetime, date
from os.path import basename
from random import randrange

import sweetify
import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.core import serializers
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound, FileResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from ACE2.forms import *
from approve.forms import ApprovalForm
from approve.models import Step
from approve.views import intiate
from it.users.models import UserProfile, Roles, Designations, Districts, Depots
from finance.PettyCash.views import approve_step


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
            custom_user_roles["ace"] = role
    ace_role = str(custom_user_roles["ace"])
    # print(ace_role)

    ace_item = Ace2.objects.get(Ace_id2=Ace_id2)

    quotations = Quotation.objects.filter(ace2=ace_item).all()
    print(quotations.count())

    if ace_role == "disburse":
        payment_mode = request.POST.get('payment_mode')
        # print(payment_mode)
        if payment_mode and payment_mode != '':
            ace_item.payment_mode = payment_mode
            ace_item.save()

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
        print("ace: ", ace_item.Ace_id)
        transaction = Transactions.objects.filter(Ace_id2=str(ace_item.Ace_id)).first()
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

    ace_quantity = range(ace_item.quantity)
    approved_steps = ace_item.process.approval_set.all().values_list('step__step', flat=True)
    return render(request, 'finance/ace2/ace_detail.html',
                  {'ace': ace_item, 'approved_steps': approved_steps, 'approvalForm': approvalForm,
                   'to': to, 'ace_role': ace_role, 'user_groups': user_groups, 'qoutations': quotations,
                   'ace_quantity': ace_quantity,
                   'clear': clear, 'clear_minus': clear_minus, 'accounting_officer_role': accounting_officer_role})


@login_required
def create_Ace(request):
    global ace_role
    QuotationFormSet()
    form = AceForm()
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
                custom_user_roles["ace"] = role
                ace_role = str(custom_user_roles["ace"])
                print(ace_role)

        if ace_role == "create":
            if form.is_valid():
                ace = form.save(commit=False)
                # print(ace.budget_id)
                budget = AssetBudget.objects.filter(budget_name=ace.budget_id).first()
                # print(budget)
                if ace.amount <= budget.balance and budget.to_be_withdrawn <= budget.balance:
                    ace.process = intiate(request, 'ace')
                    ace.requested_by = request.user

                    user_id = request.user.id
                    user_profile = UserProfile.objects.filter(id=user_id).first()

                    user_designation = Designations.objects.filter(id=user_profile.designation.id).first()
                    user_region = Regions.objects.filter(id=user_profile.region.id).first()
                    designation = user_designation
                    # print(designation)
                    region = user_region

                    rand = randrange(1, 1000)
                    rand2 = str(rand)
                    date = datetime.now()
                    date = date.strftime("%Y%m%d")

                    ace_id2 = "ACE" + date + rand2
                    ace.Ace_id2 = ace_id2
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
                    budget.to_be_withdrawn = budget.to_be_withdrawn + ace.amount
                    budget.withdrawal_date = ace.date_created
                    budget.save()

                    # for quotation_form in formset:
                    #     quotation = quotation_form.save(commit=False)
                    #     quotation.ace2 = ace
                    #     quotation.save()

                    if str(ace.classification) == "Project":
                        # the idea is that if its ace of type project there need to be added other project details
                        url = reverse('Ace:ace_detail_project', args=[ace.Ace_id2])
                        return redirect(url)
                    else:
                        url = reverse('Ace:ace_detail', args=[ace.Ace_id2])
                        return redirect(url)
                else:
                    messages.error(request, "the ace requires more than the current budget")
                    sweetify.error(request, "the ace requires more than the current budget")
                    return render(request, 'finance/ace2/create_ace.html',
                                  {'form': form, 'formset': formset, 'error_message': "Insufficient Balance"})
            else:
                form = AceForm()
                formset = QuotationFormSet()
        else:
            sweetify.error(request, "You are not allowed to create Ace")
            messages.error(request, "You are not allowed to create")
            # url = reverse('/acee/aces')
            return redirect('/acee/aces')

    return render(request, 'finance/ace2/create_ace.html', {'form': form, 'formset': formset})


@login_required
def ace_awaiting_my_action(request):
    """
    for each ace2.Process ,  let current_step = the last pettycash.process.approval if any else 0 and
    let next_step =current_step+1 then check if  next_step=step.step for rfq.process.workflow.step_set filtered by
    approver = user.roles.all.
    """
    aces_to_process = []
    user_roles = request.user.roles.all()

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
            custom_user_roles["ace"] = role
    ace_role = str(custom_user_roles["ace"])
    requester = "create"
    cashier = "process"

    print(ace_role)

    if ace_role == "pass":
        # I want objects from 2024 upwards

        for ace in Ace2.objects.filter(section=request.user.section, date_created__year__gte=2024):
            process = ace.process

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
                # remove aces that have been rejected
                if process.approval_set.filter(approved="Rejected").exists():
                    aces_to_process.remove(ace)

    else:
        for ace in Ace2.objects.filter(date_created__year__gte=2024):
            process = ace.process

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
                # remove aces that have been rejected
                if process.approval_set.filter(approved="Rejected").exists():
                    aces_to_process.remove(ace)

    print(aces_to_process)

    return render(request, 'finance/ace2/view_all_aces.html', {'aces': aces_to_process,
                                                               'ace_role': ace_role,
                                                               'requester': requester,
                                                               'cashier':cashier})


@login_required
def view_all_aces(request):
    user_roles = request.user.roles.all()

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
            custom_user_roles["ace"] = role
    ace_role = str(custom_user_roles["ace"])
    requester = "create"

    if ace_role == "create":
        aces = Ace2.objects.filter(requested_by=request.user)
    elif ace_role == "pass":
        aces = Ace2.objects.filter(section=request.user.section)
    else:
        print('kings')
        aces = Ace2.objects.all()
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
            section = row['section']
            budget_name = row['budget']
            allocated = row['allocated']
            withdrawn = row['withdrawn']
            balance = row['balance']

            # withdrawal_date = row['withdrawal_date']
            # withdrawal_date = withdrawal_date.strip().split(" ")[0]
            # if withdrawal_date != "NULL":
            #
            #     withdrawal_date = datetime.strptime(withdrawal_date, "%Y-%m-%d")
            # else:
            #     withdrawal_date = None

            awaiting_sanctioning = row['awaiting_sanctioning']
            period = int(row['period'])
            region = row['region']
            region = Regions.objects.filter(region=region).first()
            print(region)
            created_date = date.today()

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
    context = serializers.serialize('json', section_budget)

    user_page = 'ace/budgets_index.html'
    print(context)

    return render(request, user_page, {"title": "All Records",
                                       "context": context,
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
                assetbudget = AssetBudget.objects.filter(budget_name=budget_obj.budget,
                                                         period=budget_obj.period).first()
                region = Regions.objects.filter(region='Harare Region').first()
                section = Sections.objects.filter(code=str(budget_obj.section_code)).first()
                if section:
                    section_code = section.code
                # else:
                #     section_code = None
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


def create_virament(request):
    form = ViramentForm()
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
        form = ViramentForm()
    return render(request, 'finance/ace2/create_virament.html', {'form': form, 'formset': formset})


def virament_detail(request, virament_id):
    virament_item = Asset_budget_Virament.objects.get(virament_id=virament_id)
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


def view_all_viraments(request):
    viraments = Asset_budget_Virament.objects.all()
    return render(request, 'finance/ace2/view_all_viraments.html', {'viraments': viraments})


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
        for ace in Asset_budget_Virament.objects.filter(section=request.user.section):
            process = ace.process

            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
            else:
                current_step = 0

            next_step = current_step + 1

            workflow = process.workflow
            step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

            if step:
                viraments_to_process.append(ace)

    else:
        for ace in Asset_budget_Virament.objects.all():
            process = ace.process

            if process.approval_set.exists():
                last_approval = process.approval_set.last()
                current_step = last_approval.step.step
            else:
                current_step = 0

            next_step = current_step + 1

            workflow = process.workflow
            step = workflow.step_set.filter(step=next_step, approver__in=user_roles).first()

            if step:
                viraments_to_process.append(ace)

    return render(request, 'finance/ace2/view_all_aces.html', {'aces': viraments_to_process,
                                                               'virement_role': virement_role,
                                                               'requester': requester})
