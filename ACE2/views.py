from django.shortcuts import render

# Create your views here.
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
    # print(pettycash_role)

    pettycash_item = Pettycash.objects.get(petty_id=petty_id)

    quotations = Quotation.objects.filter(pettycash=pettycash_item).all()
    print(quotations.count())

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
                   'to': to, 'pettycash_role': pettycash_role, 'user_groups': user_groups, 'qoutations': quotations})


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
