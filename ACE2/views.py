from datetime import datetime
from random import randrange

from django.contrib.auth.decorators import login_required
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
    if request.method == 'POST':
        form = AceForm(request.POST, request.FILES)
        formset = QuotationFormSet(request.POST, request.FILES)
        if form.is_valid() and formset.is_valid():
            ace = form.save(commit=False)
            ace.process = intiate(request, 'ace')
            ace.requested_by = request.user

            user_id = request.user.id
            user_profile = UserProfile.objects.filter(id=user_id).first()

            user_designation = Designations.objects.filter(id=user_profile.designation.id).first()
            user_region = Regions.objects.filter(id=user_profile.region.id).first()
            designation = user_designation
            print(designation)
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
            section = Sections.objects.filter(section=ace_code).first()
            print(ace_code)
            # code = section.code
            # ace.allocation_code_of_expenditure = code
            ace.save()

            for quotation_form in formset:
                quotation = quotation_form.save(commit=False)
                quotation.ace2 = ace
                quotation.save()
            if str(ace.classification) == "Project":
                # the idea is that if its ace of type project there need to be added other project details
                url = reverse('Ace:ace_detail_project', args=[ace.Ace_id2])
                return redirect(url)
            else:
                url = reverse('Ace:ace_detail', args=[ace.Ace_id2])
                return redirect(url)
    else:
        form = AceForm()
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
    ace_role = str(custom_user_roles["pettycash"])

    if ace_role == "approve":
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
    return render(request, 'finance/pettycash/view_all_pettycashs.html', {'pettycashs': aces})


def add_project_details(request, Ace_id2):
    if request.method == 'POST':
        form = ProjectDetailForm(request.POST, request.FILES)
        if form.is_valid():
            project_details = form.save(commit=False)
            # add items from form to already existing ace object
            total_connection_fee = project_details.present_tariff + project_details.present_fmc + project_details.capital_contribution+ project_details.materials + project_details.labour + project_details.transport


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
