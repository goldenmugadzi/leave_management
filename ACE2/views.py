from datetime import datetime, date
from os.path import basename
from random import randrange

import sweetify
import csv
from django.contrib import messages
from django.contrib.auth.decorators import login_required
from django.http import HttpResponse, JsonResponse, HttpResponseNotFound, FileResponse
from django.shortcuts import render, redirect
from django.urls import reverse

from ACE2.forms import *
from approve.forms import ApprovalForm
from approve.models import Step
from approve.views import intiate
from it.users.models import UserProfile, Roles, Designations


# Create your views here.
@login_required
def Ace_detail(request, Ace_id2):
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

    next_step = last_approved + 1

    try:
        newStep = Step.objects.get(step=next_step, workflow=ace_item.process.workflow,
                                   approver__in=user_roles)
        if newStep and request.user.section == ace_item.section and next_step == 1:
            approvalForm = ApprovalForm
            to = newStep.to
            print(ace_role)
            if newStep.step == len(ace_item.process.workflow.step_set.all()):
                clear = True
                # budget calculations
                budget = ace_item.budget
                budget = Budget.objects.get(budget_id=budget)
                budget.balance = budget.balance - ace_item.amount
                budget.to_be_withdrawn = budget.to_be_withdrawn + ace_item.amount
                budget.withdrawal_date = date.today()
                budget.withdrawn = budget.withdrawn + ace_item.amount
                budget.save()

                # transaction
                transaction = Transactions.objects.filter(transaction_id=ace_item.transaction).first()
                transaction.approval_status = "approved by General Manager"
                transaction.save()
        elif newStep:
            approvalForm = ApprovalForm
            to = newStep.to
    except Step.DoesNotExist:
        pass

    approved_steps = ace_item.process.approval_set.all().values_list('step__step', flat=True)
    return render(request, 'finance/ace2/ace_detail.html',
                  {'ace': ace_item, 'approved_steps': approved_steps, 'approvalForm': approvalForm,
                   'to': to, 'ace_role': ace_role, 'user_groups': user_groups, 'qoutations': quotations})


@login_required
def create_Ace(request):
    formset = QuotationFormSet()
    if request.method == 'POST':
        form = AceForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)

        if form.is_valid():
            ace = form.save(commit=False)
            # print(ace.budget_id)
            budget = AssetBudget.objects.filter(budget_name=ace.budget_id).first()
            # print(budget)
            if ace.amount <= budget.balance:
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
                ace.designation = designation
                ace.region = region
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
    print(ace_role)

    if ace_role == "pass":
        for ace in Ace2.objects.filter(section=request.user.section):
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

    else:
        for ace in Ace2.objects.all():
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

    return render(request, 'finance/ace2/view_all_aces.html', {'aces': aces_to_process})


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

    if ace_role == "create":
        aces = Ace2.objects.filter(requested_by=request.user)
    elif ace_role == "approve":
        aces = Ace2.objects.filter(section=request.user.section)
    else:
        aces = Ace2.objects.all()
    return render(request, 'finance/ace2/view_all_aces.html', {'aces': aces})


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

            withdrawal_date = row['withdrawal_date']
            withdrawal_date = withdrawal_date.strip().split(" ")[0]
            if withdrawal_date != "null":

                withdrawal_date = datetime.strptime(withdrawal_date, "%Y-%m-%d")
            else:
                withdrawal_date = None

            awaiting_sanctioning = row['awaiting_sanctioning']
            period = int(row['period'])
            region = row['region']
            created_date = date.today()

            # withdrawal_date = datetime.strptime(row['withdrawal_date'], "%Y/%m/%d").strftime("%Y-%m-%d")
            # areas = row['area'].split(',')
            check_budget = Budget.objects.filter(budget_name=budget_name, period=period).first()
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
                                           withdrawal_date=withdrawal_date,
                                           awaiting_sanctioning=awaiting_sanctioning,
                                           period=period,
                                           region=region,
                                           created_date=created_date,
                                           budget_note=budget_note),
                print("record created")
        redirect("/ace/budgets")
        try:
            # ... view logic ...
            return HttpResponse("Budget uploaded successfully"), redirect('/ace/budgets')
        except Exception as e:
            return HttpResponse("Error: {}".format(e))
            return redirect("/ace/budgets")

    else:
        return render(request, 'ace/upload_budget.html',
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
