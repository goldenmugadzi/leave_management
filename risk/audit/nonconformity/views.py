from django.shortcuts import render, redirect, reverse, get_object_or_404, HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import datetime
from django.utils import timezone
from .models import *
from .forms import *

# from it.users.models import Notification
from it.users.models import Notification
from django.contrib import messages

# from django.core.mail import send_mail
# from django.conf import settings
from approve.decorators import checklist_roles


@login_required
def create_nonconformity(request):
    if request.method == "POST":
        form = NonconformityForm(request.POST, request.FILES)
        if form.is_valid():
            nonconformity = form.save(commit=False)
            nonconformity.created_by = request.user
            if nonconformity.recipient != request.user:
                nonconformity.save()
                auditee = nonconformity.recipient
                attachments = request.FILES.getlist("attachments")
                for attachment in attachments:
                    Attachment.objects.create(
                        nonconformity=nonconformity, attachment=attachment
                    )
                Notification.objects.create(
                    user=auditee,
                    message=f"{nonconformity.id}",
                    url=reverse("nonconformity:nonconformity", args=[nonconformity.id]),
                )
                messages.success(request, "Nonconformity created successfully!")
                return redirect("nonconformity:nonconformity", nonconformity.id)
            else:
                messages.error(
                    request, "You cannot create a nonconformity for yourself."
                )
                return render(
                    request,
                    "risk/nonconformity/create_nonconformity.html",
                    {"form": form},
                )
    else:
        form = NonconformityForm()
    return render(
        request, "risk/nonconformity/create_nonconformity.html", {"form": form}
    )


@login_required
def create_nonconformity_from_checklist(request, clause):
    clause = Question.objects.get(id=clause)
    if request.method == "POST":
        form = NonconformityForm(request.POST, request.FILES)
        if form.is_valid():
            nonconformity = form.save(commit=False)
            nonconformity.created_by = request.user
            # Check if the recipient is the same as the current user
            if nonconformity.recipient != request.user:
                # Save the nonconformity
                nonconformity.save()
                # Create a notification for the auditee
                auditee = nonconformity.recipient
                notification = Notification.objects.create(
                    user=auditee,
                    message=f"nc: {nonconformity.description}",
                    url=reverse("nonconformity:nonconformity", args=[nonconformity.id]),
                )
                # Display a success message
                messages.success(request, "Nonconformity created successfully!")
                return redirect("nonconformity:nonconformity", nonconformity.id)
            else:
                return HttpResponse("You cannot create a nonconformity for yourself.")
    else:
        form = NonconformityForm(
            instance=clause, initial={"violation_standard_reference": clause}
        )
    return render(
        request, "risk/nonconformity/create_nonconformity.html", {"form": form}
    )


@login_required
def nonconformity_details(request, nonconformity_id):
    # Retrieve the nonconformity object or return 404 if not found
    nonconformity = get_object_or_404(Nonconformity, id=nonconformity_id)
    # Initialize forms as None
    acceptanceForm = None
    rejectionForm = None
    form = None
    resolve_form = None
    closeform = None
    editform = None

    # If the request method is POST, process form data
    if request.method == "POST":
        # If the current user is the recipient and the nonconformity is accepted
        if request.user == nonconformity.recipient and nonconformity.accepted == True:
            # Process resolve form
            resolve_form = ResolveNcForm(request.POST, request.FILES)
            if resolve_form.is_valid():
                resolveform =resolve_form.save(commit=False)
                resolveform.user = request.user
                resolveform.nonconformity = nonconformity
                resolveform.save()
                nonconformity.resolved = True
                nonconformity.save()
                messages.success(request, "You have successfully resolved this nonconformity.")
                return redirect("nonconformity:nonconformity", nonconformity.id)
            else:
                messages.error(request, "Sorry, something went wrong. Please try again.")
                return redirect("nonconformity:nonconformities")

        # If the current user is the recipient and the nonconformity is not accepted
        elif request.user == nonconformity.recipient and nonconformity.accepted != True:
            accepeted = request.POST.get("accepted")
            rejectionForm = RejectionForm(request.POST)
            acceptanceForm = AcceptanceForm(request.POST)
            if accepeted == "True":
                if acceptanceForm.is_valid():
                    acceptance = acceptanceForm.save(commit=False)
                    acceptance.nonconformity = nonconformity
                    acceptance.user = request.user
                    acceptance.save()
                    nonconformity.accepted = True
                    nonconformity.save()
                    # Process attachments for acceptance
                    attachments = request.FILES.getlist("attachments")
                    for attachment in attachments:
                        AcceptanceAttachment.objects.create(acceptance=acceptance, attachment=attachment)
                    messages.success(request, "You have successfully accepted the nonconformity.")
                    return redirect("nonconformity:nonconformities")
                else:
                    messages.error(request, "Sorry, something went wrong. Please fill in the required details and try again. Be sure to pick a date!")
                    return render(request, "risk/nonconformity/nonconformity_details.html", {"nonconformity": nonconformity, "acceptanceForm": acceptanceForm, "rejectionForm": rejectionForm, "form": form})
            elif accepeted == "False":
                if rejectionForm.is_valid():
                    rejection = rejectionForm.save(commit=False)
                    rejection.nonconformity = nonconformity
                    rejection.user = request.user
                    rejection.save()
                    nonconformity.accepted = False
                    nonconformity.save()
                    # Process attachments for rejection
                    attachments = request.FILES.getlist("attachments")
                    for attachment in attachments:
                        RejectionAttachment.objects.create(rejection=rejection, attachment=attachment)
                    messages.success(request, "You have successfully rejected the nonconformity.")
                    return redirect("nonconformity:nonconformities")
                else:
                    messages.error(request, "Sorry, something went wrong. Please fill in the required details and try again.")
                    return render(request, "risk/nonconformity/nonconformity_details.html", {"nonconformity": nonconformity, "acceptanceForm": acceptanceForm, "rejectionForm": rejectionForm, "form": form})

        # If the current user is the creator of the nonconformity
        elif request.user == nonconformity.created_by:
            # Different conditions for closing or updating the nonconformity
            act = request.POST.get("rejected")
            if  ((act == "close") or request.POST.get("closed") != None) and ( nonconformity.accepted != None and nonconformity.resolved != None or nonconformity.closed == None and nonconformity.accepted == False or nonconformity.resolved == None and nonconformity.accepted == False):
                print(act, "act")
                form = CloseNcForm(request.POST, instance=nonconformity)
                if form.is_valid():
                    form.save()
                    messages.success(request, "Nonconformity closed successfully!")
                    return redirect(reverse("nonconformity:nonconformity", args=[nonconformity.id]))
            elif act == "edit" and nonconformity.accepted != True:
                form = NonconformityForm(request.POST, instance=nonconformity)
                if form.is_valid():
                    nc = form.save(commit=False)
                    nc.accepted = None
                    nc.save()
                    # Process attachments
                    attachments = request.FILES.getlist("attachments")
                    for attachment in attachments:
                        Attachment.objects.create(acceptance=nc, attachment=attachment)
                    messages.success(request, "Nonconformity updated successfully!")
                    return redirect(reverse("nonconformity:nonconformity", args=[nonconformity.id]))

            messages.error(request, "Sorry, something went wrong. Please try again.")
            return redirect(reverse("nonconformity:nonconformity", args=[nonconformity.id]))

    # If the request method is GET, prepare forms for display
    else:
        # Determine which forms to display based on the user and nonconformity status
        if request.user == nonconformity.recipient and nonconformity.accepted == None:
            rejectionForm = RejectionForm()
            acceptanceForm = AcceptanceForm(instance=nonconformity)
        
        elif request.user == nonconformity.recipient and nonconformity.accepted == True and nonconformity.resolved != True:
            corective_action = nonconformity.acceptance_set.last().corrective_action
            resolve_form = ResolveNcForm(instance=nonconformity, initial={'corrective_action_taken': corective_action})
      
        elif request.user == nonconformity.created_by and nonconformity.created_by is not None and nonconformity.resolved != None and nonconformity.accepted == True and nonconformity.closed != True:
            closeform = CloseNcForm(instance=nonconformity)
        
        elif request.user == nonconformity.created_by and nonconformity.created_by is not None and not nonconformity.closed and nonconformity.accepted != True:
            editform = NonconformityForm(instance=nonconformity)
            if  nonconformity.accepted == False : closeform = CloseNcForm(instance=nonconformity)

        old_notifications = Notification.objects.filter(user=request.user, url=nonconformity.get_absolute_url())
        old_notifications.update(is_read=True)
        return render(request, "risk/nonconformity/nonconformity_details.html", {"nonconformity": nonconformity, 'editform':editform, "acceptanceForm": acceptanceForm, "rejectionForm": rejectionForm,"resolve_form":resolve_form ,"closeform": closeform, "form": form})
@login_required
def view_notifications(request):
    user = request.user  # Assuming you have authentication enabled
    notifications = Notification.objects.filter(user=user).order_by( "-id" )
    return render(
        request, "risk/nonconformity/inbox.html", {"notifications": notifications}
    )


@login_required
def view_nonconformities(request):
    nonconformities = Nonconformity.objects.all()
    """Get all nonconformities and oder them by  date created in descending order"""
    nonconformities = Nonconformity.objects.all().order_by("-created_at")

    count = nonconformities.count()
    return render(request,"risk/nonconformity/nonconformities.html", {"nonconformities": nonconformities.order_by("-created_at"), "count": count})

@login_required
def Icreated_nonconformities(request):
    # Get the current user
    user = request.user
    nonconformities = Nonconformity.objects.filter(created_by=user)
    count = nonconformities.count()
    return render(
        request,
        "risk/nonconformity/mynonconformities.html",
        {"nonconformities": nonconformities.order_by("-created_at"), "count": count},
    )
@login_required
def assigned_to_me(request):
    # Get the current user
    user = request.user
    nonconformities = Nonconformity.objects.filter(recipient=user)
    count = nonconformities.count()
    return render(
        request,
        "risk/nonconformity/mynonconformities.html",
        {"nonconformities": nonconformities.order_by("-created_at"), "count": count},
    )

# create clause and its questions using generic view it must redirect to the checklist view
def check_roles(request):
    """to edit checklist user must have a role with application= non_conformity and role=supervisor"""
    user = request.user
    return any(
        role.application == "non_conformity" and role.role == "supervisor"
        for role in user.roles.all()
    )


"""checklist functions to create, edit and view checklist"""


@login_required
def awaiting_my_action(request):
    user = request.user
    nonconformities = Nonconformity.objects.filter(
        Q(recipient=user) & Q(accepted=None)
        or Q(recipient=user) & Q(accepted=True) & Q(resolved=False)
        or Q(created_by=user) & Q(accepted=True) & Q(resolved=True) & Q(closed=False)
        or Q(created_by=user) & Q(accepted=False)
    )
    return render(
        request,
        "risk/nonconformity/nonconformities.html",
        {"nonconformities": nonconformities.order_by("-id")},
    )


@login_required
@checklist_roles
def create_clause(request):
    if request.method == "POST":
        form = ClauseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect("nonconformity:editable_checklist")
    else:
        form = ClauseForm()
    return render(
        request, "risk/nonconformity/create_edit_checklist.html", {"form": form}
    )


@login_required
@checklist_roles
def create_topic(request, clause):
    clause = Clause.objects.get(id=clause)
    if request.method == "POST":
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.clause = clause
            topic.save()
            return redirect("nonconformity:editable_checklist")
    else:
        form = TopicForm()
    return render(
        request, "risk/nonconformity/create_edit_checklist.html", {"form": form}
    )


@login_required
@checklist_roles
def create_iso_req(request, topic):
    topic = Topic.objects.get(id=topic)
    if request.method == "POST":
        form = QuestionForm(request.POST)
        if form.is_valid():
            iso_req = form.save(commit=False)
            iso_req.topic = topic
            iso_req.save()
            return redirect("nonconformity:editable_checklist")
    else:
        form = QuestionForm()
    return render(
        request, "risk/nonconformity/create_edit_checklist.html", {"form": form}
    )


@login_required
def checklist(request):
    return render(
        request, "risk/nonconformity/checklist.html", {"clauses": Clause.objects.all()}
    )


@login_required
@checklist_roles
def editable_checklist(request):
    return render(
        request,
        "risk/nonconformity/editable_checklist.html",
        {"clauses": Clause.objects.all()},
    )


@login_required
@checklist_roles
def edit_clause(request, clause):
    clause = Clause.objects.get(id=clause)
    if request.method == "POST":
        form = ClauseForm(request.POST, instance=clause)
        if form.is_valid():
            form.save()
            return redirect("nonconformity:editable_checklist")
    else:
        form = ClauseForm(instance=clause)
    return render(
        request, "risk/nonconformity/create_edit_checklist.html", {"form": form}
    )


@login_required
@checklist_roles
def edit_topic(request, topic):
    topic = Topic.objects.get(id=topic)
    if request.method == "POST":
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            return redirect("nonconformity:editable_checklist")
    else:
        form = TopicForm(instance=topic)
    return render(
        request, "risk/nonconformity/create_edit_checklist.html", {"form": form}
    )


@login_required
@checklist_roles
def edit_iso_req(request, iso_req):
    iso_req = Question.objects.get(id=iso_req)
    if request.method == "POST":
        form = QuestionForm(request.POST, instance=iso_req)
        if form.is_valid():
            form.save()
            return redirect("nonconformity:editable_checklist")
    else:
        form = QuestionForm(instance=iso_req)
    return render(
        request, "risk/nonconformity/create_edit_checklist.html", {"form": form}
    )


def notify(request):
    send_mail(
        subject="Hello from Django qwertyuio",
        message="This is a test email.",
        from_email="perseychinaka@gmail.com",
        recipient_list=["perseychinaka1@gmail.com", "pchinaka@zetdc.co.zw"],
        fail_silently=False,
    )
    return HttpResponse("Email sent successfully!")
    # ['ruvheneko@zetdc.co.zw'],  # recipient list


def migrate_nonconformities(request):
    import mysql.connector

    # Connect to the MySQL database
    cnx = mysql.connector.connect(
        host="172.16.8.10", user="root", password="", database="nca"
    )
    cursor = cnx.cursor()
    sql_query = """SELECT  * FROM non_conformity AS nc JOIN nc_update AS nu ON nu.document_number = nc.document_number"""
    ncs = []
    try:
        cursor.execute(sql_query)
        ncs = cursor.fetchall()
    except mysql.connector.Error as err:
        print("Error executing SQL query:", err)
    nonconformity = {}
    Nonconformity._meta.get_field("created_at").auto_now_add = False
    # print("Error executing SQL query:", ncs)

    for nc_dict in ncs:
        recipient = None
        created_by = None
        nc = dict(zip(cursor.column_names, nc_dict))
        try:
            recipient = UserProfile.objects.get(username=nc["recipient_name"])
        except:
            pass
        try:
            created_by = UserProfile.objects.get(username=nc["originator"])
        except:
            pass
        print(created_by, "Error executing SQL query:", nc["originator"])

        # created_by = None
        if not nc["originator"].startswith("ze") and not nc["originator"].startswith(
            "ZE"
        ):
            print(nc["originator"], "originator")
            try:
                created_by = UserProfile.objects.get(username="ze" + nc["originator"])
            except Exception as e:
                print(created_by, e, "Error executing SQL query:", nc["originator"])

        create_date = timezone.make_aware(nc["originator_date"])
        recipt_date = (
            timezone.make_aware(nc["recipient_date"]) if nc["recipient_date"] else None
        )
        nonconformity["id"] = nc["document_number"]
        nonconformity["recipient"] = recipient
        nonconformity["created_by"] = created_by
        nonconformity["description"] = (
            nc["description"] + ". Violated standard: " + nc["violated_standard"]
        )
        nonconformity["created_at"] = create_date
        nonconformity["recommended_corrective_action"] = nc["recommended_action"]
        nonconformity["resolved"] = True if nc["supervisor_action"] == 5 else False
        nonconformity["closed"] = True if nc["supervisor_action"] == 5 else False
        nonconformity["accepted"] = (
            True
            if nc["recipient_action"] == 2
            else False if nc["recipient_action"] == 4 else None
        )

        try:
            nc_id, created = Nonconformity.objects.get_or_create(**nonconformity)
        except Exception as e:
            print(e)
            nc_id = None
        response = nc["recipient_action"]
        if nc_id:
            if response == 2:
                try:
                    print("Acceptance", recipt_date)
                    Acceptance._meta.get_field("dated").auto_now_add = False
                    Acceptance.objects.create(
                        nonconformity=nc_id, user=recipient, dated=recipt_date
                    )
                    Acceptance._meta.get_field("dated").auto_now_add = True

                except Exception as err:
                    print(err)
            elif response == 4:
                try:
                    print(nc["recipient_reason"], "recipient_reason")
                    Rejection._meta.get_field("dated").auto_now_add = False
                    Rejection.objects.create(
                        nonconformity=nc_id,
                        user=recipient,
                        dated=recipt_date,
                        rejection_reason=nc["recipient_reason"],
                    )
                    Rejection._meta.get_field("dated").auto_now_add = True
                except Exception as err:
                    print(err)

    Nonconformity._meta.get_field("created_at").auto_now_add = True
    cursor.close()
    cnx.close()
    return HttpResponse(ncs)
