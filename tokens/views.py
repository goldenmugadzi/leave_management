from django.shortcuts import render, redirect, HttpResponse, get_object_or_404
from .forms import *
from .models import *
from django.contrib import messages
from approve.views import (
    intiate,
    approve_step,
    get_my_roles_for_apps,
    send_notification,
    allowed_to_approve,
    approvers
)
from approve.models import Step
from approve.forms import ApprovalForm
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime
from approve.decorators import allowed_roles
from django.db.models import Q
import os, json, re
import mysql.connector


# check update
@login_required
@allowed_roles(["Requester", "Commercial Supervisor"], ["temper", "reimbursement", "clear credit"])
def create_token(request):
    if request.method == "POST":
        # meter details from the database if the meter number already exists and use its instance to update the meter details
        try:
            meter = Meter.objects.get(number=request.POST["number"])
            meter_form = MeterForm(request.POST, instance=meter)
        except Meter.DoesNotExist:
            meter_form = MeterForm(request.POST)

        # customer details from the database if the customer already exists and use its instance to update the customer details
        try:
            customer = Customer.objects.get(
                contact_number=request.POST["contact_number"]
            )
            customer_form = CustomerForm(request.POST, instance=customer)
        except Customer.DoesNotExist:
            customer_form = CustomerForm(request.POST)

        token_form = TokenForm(request.POST, request.FILES)
        reimbursement_form = ReimbursementForm(request.POST, request.FILES)
        clear_credit_form = ClearCreditForm(request.POST, request.FILES)
        tamper_token_form = TamperTokenForm(request.POST, request.FILES)
        old_token_form = OldTokenForm(request.POST, request.FILES)
        faulty_meter_form = FaultMeterForm(request.POST, request.FILES)
        recovered_meter_form = RecoveredMeterForm(request.POST, request.FILES)
        fault_maintanance_form = FaultMaintananceForm(request.POST, request.FILES)
        reconnection_form = ReconnectionForm(request.POST, request.FILES)

        forms = {
            "meter_form": meter_form,
            "customer_form": customer_form,
            "token_form": token_form,
            "reimbursement_form": reimbursement_form,
            "clear_credit_form": clear_credit_form,
            "tamper_token_form": tamper_token_form,
            "old_token_form": old_token_form,
            "faulty_meter_form": faulty_meter_form,
            "recovered_meter_form": recovered_meter_form,
            "fault_maintanance_form": fault_maintanance_form,
            "reconnection_form": reconnection_form,
        }

        if meter_form.is_valid() and customer_form.is_valid() and token_form.is_valid():
            meter = meter_form.save()
            customer = customer_form.save()
            token = token_form.save(commit=False)
            token_type = token.type
            if token_type == "TEMPER":
                process = intiate(request, "temper")
            elif token_type == "REIMBURSEMENT":
                process = intiate(request, "reimbursement")
            elif token_type == "CLEAR CREDIT":
                process = intiate(request, "clear credit")
            token.meter = meter
            token.customer = customer
            token.process = process
            token.created_by = request.user
            token.region = request.user.region
            token.save()
            app = None
            if token_type == "TEMPER" and tamper_token_form.is_valid():
                tamper_token = tamper_token_form.save(commit=False)
                tamper_token.token = token
                tamper_token.save()
                app = "temper"
                if (
                        tamper_token.is_for == "Fauty Maintanance"
                        and fault_maintanance_form.is_valid()
                ):
                    fault_maintanance = fault_maintanance_form.save(commit=False)
                    fault_maintanance.token = token
                    fault_maintanance.save()
                    messages.info(request, "Token request saved successfully")
                elif (
                        tamper_token.is_for == "Recovered Meter"
                        and request.FILES.get("picture")
                        and recovered_meter_form.is_valid()
                ):
                    recovered_meter = recovered_meter_form.save(commit=False)
                    recovered_meter.token = token
                    recovered_meter.save()
                    messages.info(request, "Token request saved successfully")
                elif (
                        tamper_token.is_for == "Reconnection"
                        and reconnection_form.is_valid()
                ):
                    reconnection = reconnection_form.save(commit=False)
                    reconnection.token = token
                    reconnection.save()
                    messages.info(request, "Token request saved successfully")
                else:
                    forms.update(
                        {
                            "fault_maintanance_form": fault_maintanance_form,
                            "recovered_meter_form": recovered_meter_form,
                            "reconnection_form": reconnection_form,
                        }
                    )
                    tamper_token.delete()
                    token.delete()
                    messages.error(request, "Token request error")
                    return render(request, "tokens/create_token.html", forms)

            elif token_type == "REIMBURSEMENT" and reimbursement_form.is_valid():
                app = "reimbursement"
                reimbursement = reimbursement_form.save(commit=False)
                reimbursement.token = token
                reimbursement.save()
                if (
                        reimbursement.purpose == "Faulty Meter"
                        and faulty_meter_form.is_valid()
                ):
                    faulty_meter = faulty_meter_form.save(commit=False)
                    faulty_meter.token = token
                    faulty_meter.save()
                    messages.info(request, "Token request saved successfully")
                elif (
                        reimbursement.purpose == "Recovered Meter"
                        and recovered_meter_form.is_valid()
                ):
                    recovered_meter = recovered_meter_form.save(commit=False)
                    recovered_meter.token = token
                    recovered_meter.save()
                    messages.info(request, "Token request saved successfully")
                elif (
                        reimbursement.purpose == "Old Token"
                        and old_token_form.is_valid()
                        and request.FILES.get("old_token")
                ):
                    old_token = old_token_form.save(commit=False)
                    old_token.token = token
                    old_token.save()
                    messages.info(request, "Token request saved successfully")
                else:
                    forms.update(
                        {
                            "faulty_meter_form": faulty_meter_form,
                            "recovered_meter_form": recovered_meter_form,
                            "old_token_form": old_token_form,
                        }
                    )
                    messages.error(request, "Token request error")
                    return render(request, "tokens/create_token.html", forms)

            elif token_type == "CLEAR CREDIT" and clear_credit_form.is_valid():
                app = "Clear Credit"
                clear_credit = clear_credit_form.save(commit=False)
                clear_credit.token = token
                clear_credit.save()
                messages.success(request, "Token request saved successfully")
            else:
                return render(request, "tokens/create_token.html", forms)

            # send_notification("token", token)
            # send_notification(request, "tokens:token", app, token)

            return redirect("tokens:token", token.id)

        else:
            return render(request, "tokens/create_token.html", forms)

    forms = {
        "meter_form": MeterForm(),
        "customer_form": CustomerForm(),
        "token_form": TokenForm(initial={"cost_center": request.user.cost_center}),
        "reimbursement_form": ReimbursementForm(),
        "clear_credit_form": ClearCreditForm(),
        "tamper_token_form": TamperTokenForm(),
        "old_token_form": OldTokenForm(),
        "faulty_meter_form": FaultMeterForm(),
        "recovered_meter_form": RecoveredMeterForm(),
        "fault_maintanance_form": FaultMaintananceForm(),
        "reconnection_form": ReconnectionForm(),
    }
    return render(request, "tokens/create_token.html", forms)


@login_required
def token_details(request, token_id):
    token = Token.objects.get(id=token_id)
    if request.method == "POST":
        generatetokenform = GenerateTokenForm(request.POST, request.FILES, instance=token)
        last_approval = token.process.approval_set.last()
        last_step = last_approval.step if last_approval else None
        if (
                token.process.workflow.step_set.last() is not None and last_step is not None and token.process.workflow.step_set.last().step == (
                last_step.step + 1)):
            if (generatetokenform.is_valid() and request.FILES.get("token_photo") is not None):
                approve_step(request, token.process.pk)
                generatetokenform.save()
                return redirect("tokens:token", token_id)
            else:
                messages.error(request, "Generate token form is invalid. Have you provided a token photo?", )
        else:
            approve_step(request, token.process.pk)
    approvalForm = None
    generateTokenForm = None
    to = None
    completed = False
    user_roles = request.user.roles.all()
    if not token.process.approval_set.filter(approved="Rejected").exists():  # and allowed:
        try:
            last_approved = token.process.approval_set.last().step.step
        except AttributeError:
            last_approved = 0
        next_step = last_approved + 1
        try:
            newStep = Step.objects.get(
                step=next_step, workflow=token.process.workflow, approver__in=user_roles
            )
            approvalForm = ApprovalForm
            to = newStep.to
            if newStep == token.process.workflow.step_set.last():
                generateTokenForm = GenerateTokenForm()
        except Step.DoesNotExist:
            pass
        completed = token.process.workflow.step_set.last().step == last_approved
    approved_steps = token.process.approval_set.all().values_list(
        "step__step", flat=True
    )

    token = get_object_or_404(Token, id=token_id)
    # _approvers=approvers(token)
    # print("approvers",_approvers)
    # print("approvers",_approvers[0].user.get_full_name())
    return render(
        request,
        "tokens/token_detail.html",
        {
            "token": token,
            "completed": completed,
            "approved_steps": approved_steps,
            "approvalForm": approvalForm,
            "generateTokenForm": generateTokenForm,
            "to": to,
        },
    )


@login_required
def view_all_tokens(request):
    if request.method == "POST":
        tkns = {}
        tockens = Token.objects.none()
        search_term = request.POST.get("search_term", "")
        """for all the words that are in the search term, make all possible combinations of the words and search for them in the database and order them by the number of times they appear in the search term giving && query the highest priority when ranking the results"""
        words = search_term.split()
        field_names = [
            "meter__number",
            "customer__name",
            "customer__stand_number",
            "reason",
            "created_by__username",
            "cost_center__name",
            "cost_center__code",
            "id",
            "created_at",
        ]
        for word in words:
            for field_name in field_names:
                word_tkns = Token.objects.filter(
                    Q(**{field_name + "__icontains": word})
                )
                for tkn in word_tkns:
                    if tkn.id in tkns:
                        tkns[tkn.id]["count"] += 1
                    else:
                        tkns[tkn.id] = {"token": tkn, "count": 1}

        for word in search_term.split():
            print(word)
            word_tkns = Token.objects.filter(
                Q(meter__number__icontains=word)
                | Q(customer__name__icontains=word)
                | Q(customer__stand_number__icontains=word)
                | Q(reason__icontains=word)
                | Q(created_by__username__icontains=word)
                | Q(cost_center__name__icontains=word)
                | Q(cost_center__code__iexact=word)
                | Q(id__iexact=word)
                | Q(created_at__icontains=word)
            )
            for tkn in word_tkns:
                if tkn.id in tkns:
                    tkns[tkn.id]["count"] += 1
                else:
                    tkns[tkn.id] = {"token": tkn, "count": 1}
        user_cost_center = request.user.section.id
        print(user_cost_center)
        print(Token.objects.filter(cost_center=user_cost_center))

        sorted_tokens = sorted(tkns.values(), key=lambda x: x["count"], reverse=True)
        sorted_token_ids = [token["token"].id for token in sorted_tokens]
        if user_cost_center:
            tockens = Token.objects.filter(
                Q(id__in=sorted_token_ids) & Q(cost_center=user_cost_center)
            )
            return render(
                request,
                "tokens/tokens.html",
                {
                    "tokens": tockens.order_by("-created_at")[:100],
                    "roles": get_my_roles_for_apps(
                        request.user, ["temper", "reimbursement", "clear credit"]
                    ),
                    "all": True,
                },
            )
        else:
            messages.error(
                request,
                "You do not have a cost center assigned to you. \n Please contact the administrator.",
            )
            return redirect("tokens:tokens")

    user = request.user
    application_names = ["temper", "reimbursement", "clear credit"]
    cost_centers = user.cost_centers_for(application_names)
    mytokens = Token.objects.none()

    if cost_centers:
        mytokens = Token.objects.filter(cost_center__in=cost_centers)
    else:
        print(user.cost_center_and_decendace())
        mytokens = Token.objects.filter(cost_center__in=user.cost_center_and_decendace())

    return render(request, "tokens/tokens.html", {"tokens": mytokens, "all": True,
                                                  "roles": get_my_roles_for_apps(request.user,
                                                                                 ["temper", "reimbursement",
                                                                                  "clear credit"]), }, )


@login_required
def awaiting_my_action(request):
    """Process tokens based on user roles and cost centers."""
    user = request.user
    application_names = ["temper", "reimbursement", "clear credit"]
    cost_centers = user.cost_centers_for(application_names)
    cost_center = user.cost_center
    end_date = datetime.now()
    start_date = end_date.replace(day=1)
    print(end_date)
    print(start_date)
    if cost_centers:
        cost_center = get_parent(cost_centers)
    if not cost_centers:
        return render(request, "tokens/tokens.html",
                      {"tokens": [], "all": False, "roles": get_my_roles_for_apps(user, application_names),
                       "error": "No cost centers found for the given applications.", }, )
    user_roles = set(user.roles.all())
    tokens_to_process = []
    tokens = Token.objects.filter(cost_center__in=cost_centers).prefetch_related("process__approval_set",
                                                                                 "process__workflow__step_set")
    for token in tokens:
        approvals = token.process.approval_set.all()
        next_step = (approvals.last().step.step if approvals.exists() else 0) + 1
        if token.process.workflow.step_set.filter(step=next_step,
                                                  approver__in=user_roles).exists() and not token.process.approval_set.filter(
                approved="Rejected").exists():
            tokens_to_process.append(token)

    return render(request, "tokens/tokens.html",
                  {"tokens": tokens_to_process, "all": False, "start_date": start_date, "end_date": end_date,
                   "cost_center": cost_center, "types": application_names,
                   "roles": get_my_roles_for_apps(user, application_names), }, )


def get_parent(cost_centers):
    parent = None
    for cost_center in cost_centers:
        if cost_center.parent in cost_centers:
            parent = cost_center.parent
    return parent


def addsection(request):
    for token in Token.objects.all():
        try:
            if not token.section:
                token.section = token.created_by.section
                token.region = token.created_by.region
                token.save()
            old_process = token.process
            if old_process.workflow.name == "tokens":
                if token.type == "TEMPER":
                    process = intiate(request, "temper")
                elif token.type == "REIMBURSEMENT":
                    process = intiate(request, "reimbursement")
                elif token.type == "CLEAR CREDIT":
                    process = intiate(request, "clear credit")
                token.process = process
                token.save()
                old_process.delete()
        except:
            pass
    return redirect("tokens:tokens")


def process_file(file_path):
    if not os.path.isfile(file_path):
        raise FileNotFoundError("File not found!")

    with open(file_path, "r") as file:
        cont = file.readlines()
        roots = []
        p_t = None
        c_t = None
        n_t = None
        p_name = None
        c_name = None
        n_name = None
        root = None
        prev = None
        curent = None
        next = None
        state = None
        tkn = None
        pp = None
        b4 = 0
        after = 0
        for a in range(len(cont)):
            if a > 0:
                prev = cont[a - 1].rstrip()
            curent = cont[a].rstrip()
            if a < (len(cont) - 1):
                next = cont[a + 1].rstrip()

            if prev:
                p_t = len(prev) - len(prev.lstrip("\t"))
            c_t = len(curent) - len(curent.lstrip("\t"))
            if next:
                n_t = len(next) - len(next.lstrip("\t"))

            if prev:
                p_id, *pname = prev.strip().split("\t")
            c_id, *cname = curent.strip().split("\t")
            n_id, *nname = next.strip().split("\t")

            if prev:
                p_name = " ".join(pname).replace("\t", "").replace(" ", "")
            c_name = " ".join(cname).replace("\t", "").replace("   ", "")
            n_name = " ".join(nname).replace("\t", "").replace("   ", "")

            tkn = n_t > c_t
            if a > 0:
                pp = c_t > p_t
                b4 = c_t - p_t
                after = n_t - c_t

            if pp and b4 > 0:
                root = CostCenter.objects.get(code=p_id)
                CostCenter.objects.create(name=c_name, code=c_id, parent=root)
            elif tkn and b4 > 0:
                if a > 0:
                    CostCenter.objects.create(name=c_name, code=c_id, parent=root)
                else:
                    CostCenter.objects.create(name=c_name, code=c_id, parent=root)

            elif not pp and tkn:

                if b4 < 0:
                    b4 = -1 * b4
                    root = root
                    for i in range(b4):
                        root = root.parent
                    CostCenter.objects.create(name=c_name, code=c_id, parent=root)
                if b4 == 0:
                    if a > 0:
                        root = CostCenter.objects.get(code=p_id).parent
                        CostCenter.objects.create(name=c_name, code=c_id, parent=root)
                    else:
                        CostCenter.objects.create(name=c_name, code=c_id, parent=None)

            elif not pp and not tkn:
                if b4 < 0:
                    b4 = -1 * b4
                    root = root
                    for i in range(b4):
                        root = root.parent
                CostCenter.objects.create(name=c_name, code=c_id, parent=root)
            else:
                CostCenter.objects.create(name=c_name, code=c_id, parent=None)

            state = {
                "p_t": p_t,
                "c_t": c_t,
                "n_t": n_t,
                "b4": b4,
                "tkn": tkn,
                "pp": pp,
                "c_name": c_name,
            }
            print(state)
    return "json_data"


def cost_centers(request):
    return render(
        request, "tokens/cost_centers.html", {"cost_centers": CostCenter.objects.all()}
    )


def upload_centers(request):
    CostCenter.objects.all().delete()
    file_path = "tokens/cc.txt"
    try:
        process_file(file_path)
    except FileNotFoundError as e:
        print(e)
    return redirect("tokens:cost_centers")


"""get ancestors of the cost center and all its children and merge them into cost_centers"""


def cost_center(request, cost_center_id):
    cost_center = CostCenter.objects.get(id=cost_center_id)
    return render(
        request,
        "tokens/cost_centers.html",
        {
            "ancestors": cost_center.get_all_ancestors(),
            "cost_centers": cost_center.get_all_ancestors_and_their_children(),
        },
    )


def migrate_tokens(request):
    import mysql.connector

    # Connect to the MySQL database
    # cnx = mysql.connector.connect(
    #     host="172.16.8.10", user="root", password="", database="harare"
    # )
    cnx = mysql.connector.connect(
        host="127.0.0.1", user="root", password="", database="dms1"
    )
    cursor = cnx.cursor()
    sql_query = """SELECT * FROM tamper_token AS tt JOIN centre AS cc on cc.scode = tt.section_code JOIN tamper_token_update AS ttu ON tt.request_id = ttu.request_id where `tt`.`section_code` !="" ORDER BY `tt`.`section_code` ASC
"""
    tkns = []
    try:
        cursor.execute(sql_query)
        tkns = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error executing SQL query:", err)
    token = {}
    # Token.objects.all().delete()
    Token._meta.get_field("created_at").auto_now_add = False

    for nc_dict in tkns:
        created_by = None
        tkn = dict(zip(cursor.column_names, nc_dict))
        if tkn["requester"] is not None:
            try:
                created_by = UserProfile.objects.get(username=tkn["requester"])
            except:
                # print(created_by, "Error executing SQL query:", tkn["requester"])
                if not tkn["requester"].startswith("ze") and not tkn[
                    "requester"
                ].startswith("ZE"):
                    # print(tkn["requester"], "requester")
                    try:
                        created_by = UserProfile.objects.get(
                            username="ze" + tkn["requester"]
                        )
                    except Exception as e:
                        print(
                            created_by,
                            e,
                            "Error executing SQL query:",
                            tkn["requester"],
                        )

            customer = None
            meter, created = Meter.objects.get_or_create(
                number=tkn["meter_number"],
                defaults={"kilowatt_hours": tkn["kilowatts"], "phase": tkn["type"]},
            )
            customer = Customer.objects.filter(
                name=tkn["customer_name"],
                address=tkn["stand_number"],
                stand_number=tkn["stand_number"],
            ).first()
            if customer is None:
                customer, created = Customer.objects.get_or_create(
                    name=tkn["customer_name"],
                    defaults={
                        "address": tkn["stand_number"],
                        "stand_number": tkn["stand_number"],
                    },
                )

            create_date = timezone.make_aware(tkn["requested_date"])
            token["meter"] = meter
            token["created_by"] = created_by
            token["reason"] = tkn["reason"]
            token["created_at"] = create_date
            token["customer"] = customer
            cost_center_query = CostCenter.objects.filter(
                code=tkn["section_code"]
            ).first()
            if not cost_center_query:
                cost_center_query = CostCenter.objects.filter(
                    code=tkn["allocation_code"]
                ).first()

            token["cost_center"] = (
                cost_center_query
                if cost_center_query
                else CostCenter.objects.get(code=tkn["allocation_code"])
            )
            if created_by is not None:
                token["region"] = created_by.region
            else:
                token["region"] = None
            token["type"] = "TEMPER"
            purpose = tkn["purpose"]
            process = intiate(request, "temper")
            token["process"] = process
            crted_token, created = Token.objects.get_or_create(
                id=tkn["request_id"], defaults=token
            )
            if str(purpose) == "fault_maintanance":
                fault_number_str = tkn["fault_number"]
                numbers = re.findall(r"\d+", fault_number_str)
                code = int(numbers[0]) if numbers else None
                FaultMaintanance.objects.create(token=crted_token, code=code)
                TAMPERTOKEN.objects.create(
                    token=crted_token, is_for="Fauty Maintanance"
                )
            elif str(purpose) == "reconnection":
                Reconnection.objects.create(token=crted_token)
                TAMPERTOKEN.objects.create(token=crted_token, is_for="Reconnection")
            elif str(purpose) == "recovered_meter":
                RecoveredMeter.objects.create(token=crted_token)
                TAMPERTOKEN.objects.create(token=crted_token, is_for="Recovered Meter")
            else:
                print("invalid purpose", purpose, token["id"])
            if process.approval_set.exists():
                last_apporoved_step = process.approval_set.last().step
            else:
                last_apporoved_step = 0

            if process.workflow.step_set.last().step != last_apporoved_step:
                next_approval_step = process.workflow.step_set.get(
                    step=last_apporoved_step + 1
                )

            if tkn["update_user2"] is not None:
                try:
                    try:
                        user = UserProfile.objects.get(username=tkn["update_user2"])
                    except Exception as e:
                        user = UserProfile.objects.get(
                            username="ze" + tkn["update_user2"]
                        )
                    next2_approval_step = process.workflow.step_set.get(
                        step=last_apporoved_step + 2
                    )
                    next3_approval_step = process.workflow.step_set.get(
                        step=last_apporoved_step + 3
                    )
                    if tkn["reject_reason"] is not None:
                        Approval.objects.create(
                            step=next2_approval_step,
                            user=user,
                            process=process,
                            comment=tkn["reject_reason"],
                            approved="Rejected",
                            approved_at=timezone.now(),
                        )
                    elif tkn["reject_reason"] is None:
                        Approval.objects.create(
                            step=next2_approval_step,
                            user=user,
                            process=process,
                            approved="Approved",
                            approved_at=timezone.now(),
                        )
                        Approval.objects.create(
                            step=next3_approval_step,
                            user=user,
                            process=process,
                            approved="Approved",
                            approved_at=timezone.now(),
                        )
                except Exception as e:
                    pass
                    # print(tkn["update_user2"], "l2 appproval error", e)
            if tkn["update_user1"] is not None:
                try:
                    try:
                        user = UserProfile.objects.get(
                            username="ze" + tkn["update_user1"]
                        )
                    except Exception as e:
                        user = UserProfile.objects.get(username=tkn["update_user1"])
                    if tkn["reject_reason"] is not None and tkn["update_user2"] is None:
                        Approval.objects.create(
                            step=next_approval_step,
                            user=user,
                            process=process,
                            comment=tkn["reject_reason"],
                            approved="Rejected",
                            approved_at=timezone.now(),
                        )
                    else:
                        Approval.objects.create(
                            step=next_approval_step,
                            user=user,
                            process=process,
                            approved="Approved",
                            approved_at=timezone.now(),
                        )
                except Exception as e:
                    pass
                    # print(tkn["update_user1"], "l1 appproval error", e)
        Token._meta.get_field("created_at").auto_now_add = True
        cursor.close()
        cnx.close()

    return HttpResponse(tkns)


@login_required
def migrate_reimbursement_tokens(request):
    cnx = mysql.connector.connect(
        host="127.0.0.1", user="root", password="", database="dms1"
    )
    cursor = cnx.cursor()
    sql_query = """SELECT * FROM `reimbursement_token` as rt JOIN centre AS cc on cc.scode = rt.section_code JOIN `reimbursement_token_update` as rtu ON rt.request_id = rtu.request_id where `rt`.`section_code` !="" ORDER BY `rt`.`section_code` ASC"""
    tkns = []
    try:
        cursor.execute(sql_query)
        tkns = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error executing SQL query:", err)
    token = {}
    Token._meta.get_field("created_at").auto_now_add = False
    for nc_dict in tkns:
        created_by = None
        tkn = dict(zip(cursor.column_names, nc_dict))
        if tkn["requester"] is not None:
            try:
                created_by = UserProfile.objects.get(username=tkn["requester"])
            except:
                print(created_by, "Error executing SQL query:", tkn["requester"])
                if not tkn["requester"].startswith("ze") and not tkn[
                    "requester"
                ].startswith("ZE"):
                    print(tkn["requester"], "requester")
                    try:
                        created_by = UserProfile.objects.get(
                            username="ze" + tkn["requester"]
                        )
                    except Exception as e:
                        print(
                            created_by,
                            e,
                            "Error executing SQL query:",
                            tkn["requester"],
                        )

            customer = None
            meter, created = Meter.objects.get_or_create(
                number=tkn["meter_number"],
                defaults={"kilowatt_hours": tkn["kilowatts"], "phase": tkn["type"]},
            )
            customer = Customer.objects.filter(
                name=tkn["customer_name"],
                address=tkn["stand_number"],
                stand_number=tkn["stand_number"],
            ).first()
            if customer is None:
                customer, created = Customer.objects.get_or_create(
                    name=tkn["customer_name"],
                    defaults={
                        "address": tkn["stand_number"],
                        "stand_number": tkn["stand_number"],
                    },
                )

            create_date = timezone.make_aware(tkn["requested_date"])
            token["id"] = tkn["request_id"]
            token["meter"] = meter
            token["created_by"] = created_by
            token["reason"] = tkn["reason"]
            token["created_at"] = create_date
            token["customer"] = customer
            cost_center_query = CostCenter.objects.filter(
                code=tkn["section_code"]
            ).first()
            if cost_center_query is None:
                cost_center_query = CostCenter.objects.filter(
                    code=tkn["allocation_code"]
                ).first()

            token["cost_center"] = cost_center_query
            try:
                if created_by is not None:
                    token["region"] = created_by.region
                else:
                    token["region"] = None
                print("token", token)
                token["type"] = "REIMBURSEMENT"
                purpose = tkn["recovered_fault"]
                process = intiate(request, "reimbursement")
                token["process"] = process
                crted_token, created = Token.objects.get_or_create(
                    id=tkn["request_id"], defaults=token
                )
                if str(purpose) == "faulty_meter":
                    fault_number_str = tkn["fault_number"]
                    numbers = re.findall(r"\d+", fault_number_str)
                    code = int(numbers[0]) if numbers else None
                    FaultMeter.objects.create(token=crted_token, code=code)
                    REIMBURSEMENT.objects.create(
                        token=crted_token, purpose="Faulty Meter"
                    )
                elif str(purpose) == "recovered_meter":
                    RecoveredMeter.objects.create(token=crted_token)
                    REIMBURSEMENT.objects.create(
                        token=crted_token, purpose="Recovered Meter"
                    )
                elif str(purpose) == "old_token":
                    OldToken.objects.create(token=crted_token)
                    REIMBURSEMENT.objects.create(token=crted_token, purpose="Old Token")
                else:
                    print("invalid purpose", purpose, token["id"])
                if process.approval_set.exists():
                    last_apporoved_step = process.approval_set.last().step
                else:
                    last_apporoved_step = 0
                if process.workflow.step_set.last().step != last_apporoved_step:
                    next_approval_step = process.workflow.step_set.get(
                        step=last_apporoved_step + 1
                    )
                if tkn["update_user2"] is not None:
                    try:
                        try:
                            user = UserProfile.objects.get(username=tkn["update_user2"])
                        except Exception as e:
                            user = UserProfile.objects.get(
                                username="ze" + tkn["update_user2"]
                            )
                        next2_approval_step = process.workflow.step_set.get(
                            step=last_apporoved_step + 2
                        )
                        next3_approval_step = process.workflow.step_set.get(
                            step=last_apporoved_step + 3
                        )
                        if tkn["reject_reason"] is not None:
                            Approval.objects.create(
                                step=next2_approval_step,
                                user=user,
                                process=process,
                                comment=tkn["reject_reason"],
                                approved="Rejected",
                                approved_at=timezone.now(),
                            )
                        elif tkn["reject_reason"] is None:
                            Approval.objects.create(
                                step=next2_approval_step,
                                user=user,
                                process=process,
                                approved="Approved",
                                approved_at=timezone.now(),
                            )
                            Approval.objects.create(
                                step=next3_approval_step,
                                user=user,
                                process=process,
                                approved="Approved",
                                approved_at=timezone.now(),
                            )
                    except Exception as e:
                        print(tkn["update_user2"], "l2 appproval error", e)
                if tkn["update_user1"] is not None:
                    try:
                        try:
                            user = UserProfile.objects.get(
                                username="ze" + tkn["update_user1"]
                            )
                        except Exception as e:
                            user = UserProfile.objects.get(username=tkn["update_user1"])
                        if (
                                tkn["reject_reason"] is not None
                                and tkn["update_user2"] is None
                        ):
                            Approval.objects.create(
                                step=next_approval_step,
                                user=user,
                                process=process,
                                comment=tkn["reject_reason"],
                                approved="Rejected",
                                approved_at=timezone.now(),
                            )
                        else:
                            Approval.objects.create(
                                step=next_approval_step,
                                user=user,
                                process=process,
                                approved="Approved",
                                approved_at=timezone.now(),
                            )
                    except Exception as e:
                        print(tkn["update_user1"], "l1 appproval error", e)
            except Exception as e:
                print(e, "error")
        Token._meta.get_field("created_at").auto_now_add = True
        cursor.close()
        cnx.close()
    return redirect("tokens:tokens")


@login_required
def migrate_clear_credit_tokens(request):
    cnx = mysql.connector.connect(
        host="127.0.0.1", user="root", password="", database="dms1"
    )
    cursor = cnx.cursor()
    sql_query = """SELECT * FROM `credit_request` as cct JOIN centre AS cc on cc.scode = cct.section_code JOIN `credit_request_update` as cctu ON cct.request_id = cctu.request_id where `cct`.`section_code` !="" ORDER BY `cct`.`section_code` ASC"""
    tkns = []
    try:
        cursor.execute(sql_query)
        tkns = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error executing SQL query:", err)
    token = {}
    Token._meta.get_field("created_at").auto_now_add = False
    for nc_dict in tkns:
        created_by = None
        tkn = dict(zip(cursor.column_names, nc_dict))
        if tkn["requester"] is not None:
            try:
                created_by = UserProfile.objects.get(username=tkn["requester"])
            except:
                print(created_by, "Error executing SQL query:", tkn["requester"])
                if not tkn["requester"].startswith("ze") and not tkn[
                    "requester"
                ].startswith("ZE"):
                    print(tkn["requester"], "requester")
                    try:
                        created_by = UserProfile.objects.get(
                            username="ze" + tkn["requester"]
                        )
                    except Exception as e:
                        print(
                            created_by,
                            e,
                            "Error executing SQL query:",
                            tkn["requester"],
                        )

            customer = None
            meter, created = Meter.objects.get_or_create(
                number=tkn["meter_number"],
                defaults={"kilowatt_hours": tkn["kilowatts"], "phase": tkn["type"]},
            )
            customer = Customer.objects.filter(
                name=tkn["customer_name"],
                address=tkn["stand_number"],
                stand_number=tkn["stand_number"],
            ).first()
            if customer is None:
                customer, created = Customer.objects.get_or_create(
                    name=tkn["customer_name"],
                    defaults={
                        "address": tkn["stand_number"],
                        "stand_number": tkn["stand_number"],
                    },
                )

            create_date = timezone.make_aware(tkn["requested_date"])
            token["id"] = tkn["request_id"]
            token["meter"] = meter
            token["created_by"] = created_by
            token["reason"] = tkn["reason"]
            token["created_at"] = create_date
            token["customer"] = customer
            cost_center_query = CostCenter.objects.filter(
                code=tkn["section_code"]
            ).first()
            if cost_center_query is None:
                cost_center_query = CostCenter.objects.filter(
                    code=tkn["allocation_code"]
                ).first()

            token["cost_center"] = cost_center_query
            try:
                if created_by is not None:
                    token["region"] = created_by.region
                else:
                    token["region"] = None
                print("token", token)
                token["type"] = "CLEAR CREDIT"
                process = intiate(request, "clear credit")
                token["process"] = process
                crted_token, created = Token.objects.get_or_create(
                    id=tkn["request_id"], defaults=token
                )
                clear_credit, crtd = CLEARCREDIT.objects.get_or_create(
                    token=crted_token, amount=tkn["amount"]
                )

                if process.approval_set.exists():
                    last_apporoved_step = process.approval_set.last().step
                else:
                    last_apporoved_step = 0
                if process.workflow.step_set.last().step != last_apporoved_step:
                    next_approval_step = process.workflow.step_set.get(
                        step=last_apporoved_step + 1
                    )
                if tkn["update_user2"] is not None:
                    try:
                        try:
                            user = UserProfile.objects.get(username=tkn["update_user2"])
                        except Exception as e:
                            user = UserProfile.objects.get(
                                username="ze" + tkn["update_user2"]
                            )
                        next2_approval_step = process.workflow.step_set.get(
                            step=last_apporoved_step + 2
                        )
                        next3_approval_step = process.workflow.step_set.get(
                            step=last_apporoved_step + 3
                        )
                        if tkn["reject_reason"] is not None:
                            Approval.objects.create(
                                step=next2_approval_step,
                                user=user,
                                process=process,
                                comment=tkn["reject_reason"],
                                approved="Rejected",
                                approved_at=timezone.now(),
                            )
                        elif tkn["reject_reason"] is None:
                            Approval.objects.create(
                                step=next2_approval_step,
                                user=user,
                                process=process,
                                approved="Approved",
                                approved_at=timezone.now(),
                            )
                            Approval.objects.create(
                                step=next3_approval_step,
                                user=user,
                                process=process,
                                approved="Approved",
                                approved_at=timezone.now(),
                            )
                    except Exception as e:
                        print(tkn["update_user2"], "l2 appproval error", e)
                if tkn["update_user1"] is not None:
                    try:
                        try:
                            user = UserProfile.objects.get(
                                username="ze" + tkn["update_user1"]
                            )
                        except Exception as e:
                            user = UserProfile.objects.get(username=tkn["update_user1"])
                        if (
                                tkn["reject_reason"] is not None
                                and tkn["update_user2"] is None
                        ):
                            Approval.objects.create(
                                step=next_approval_step,
                                user=user,
                                process=process,
                                comment=tkn["reject_reason"],
                                approved="Rejected",
                                approved_at=timezone.now(),
                            )
                        else:
                            Approval.objects.create(
                                step=next_approval_step,
                                user=user,
                                process=process,
                                approved="Approved",
                                approved_at=timezone.now(),
                            )
                    except Exception as e:
                        print(tkn["update_user1"], "l1 appproval error", e)
            except Exception as e:
                print(e, "error")
        Token._meta.get_field("created_at").auto_now_add = True
        cursor.close()
        cnx.close()
    return redirect("tokens:tokens")
