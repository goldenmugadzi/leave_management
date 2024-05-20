
from django.shortcuts import render, redirect,reverse,get_object_or_404,HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q

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
    if request.method == 'POST':
        form = NonconformityForm(request.POST, request.FILES)
        if form.is_valid():
            nonconformity = form.save(commit=False)
            nonconformity.created_by = request.user
            if nonconformity.recipient != request.user:
                nonconformity.save()
                auditee = nonconformity.recipient
                attachments = request.FILES.getlist('attachments')
                for attachment in attachments:
                    Attachment.objects.create(nonconformity=nonconformity, attachment=attachment)
                Notification.objects.create( user=auditee,message=f"{nonconformity.id}",url = reverse('nonconformity:nonconformity', args=[nonconformity.id]))
                messages.success(request, 'Nonconformity created successfully!')
                return redirect('/')
            else:
                messages.error(request,"You cannot create a nonconformity for yourself.")
                return render(request, 'risk/nonconformity/create_nonconformity.html', {'form': form})
    else:
        form = NonconformityForm()
    return render(request, 'risk/nonconformity/create_nonconformity.html', {'form': form})

@login_required
def create_nonconformity_from_checklist(request, clause):
    clause = Question.objects.get(id=clause)
    if request.method == 'POST':
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
                    url = reverse('nonconformity:nonconformity', args=[nonconformity.id])
                )
                # Display a success message
                messages.success(request, 'Nonconformity created successfully!')
                return redirect('nonconformity:nonconformities')
            else:
                return HttpResponse("You cannot create a nonconformity for yourself.")
    else:
        form = NonconformityForm(instance=clause, initial={'violation_standard_reference': clause})
    return render(request, 'risk/nonconformity/create_nonconformity.html', {'form': form})

@login_required
def nonconformity_details(request, nonconformity_id):
    nonconformity = get_object_or_404(Nonconformity, id=nonconformity_id)
    if request.method == 'POST':
        
        if request.user == nonconformity.recipient and nonconformity.accepted == True:
            resolve_form = ResolveNcForm(request.POST, instance=nonconformity)
            if resolve_form.is_valid():
                resolve_form.save()
                messages.success(request, 'You have successfully resolved this nonconformity.')
                return redirect('nonconformity:nonconformities')
            else:
                messages.error(request, 'Sorry, something went wrong. Please try again.')
                return redirect('nonconformity:nonconformities')
        elif request.user == nonconformity.recipient and nonconformity.accepted != True:
            accepeted = request.POST.get('accepted')
            rejectionForm = RejectionForm(request.POST)
            form = None
            print(request.POST.get('accepted'),'rejectionForm is valid1',str(accepeted))
            acceptanceForm = AcceptanceForm(request.POST)
            if accepeted == "True":
                if acceptanceForm.is_valid():
                    acceptance = acceptanceForm.save(commit=False)
                    acceptance.nonconformity = nonconformity
                    acceptance.user = request.user
                    acceptance.save()
                    nonconformity.accepted = True
                    nonconformity.save()
                    attachments = request.FILES.getlist('attachments')
                    for attachment in attachments:
                        AcceptanceAttachment.objects.create(acceptance=acceptance, attachment=attachment)
                    messages.success(request, 'You have successfully accepted the nonconformity.')
                    return redirect('nonconformity:nonconformities')
            elif accepeted == "False":
                if rejectionForm.is_valid():
                    rejection = rejectionForm.save(commit=False)
                    rejection.nonconformity = nonconformity
                    rejection.user = request.user
                    rejection.save()
                    nonconformity.accepted = False
                    nonconformity.save()
                    attachments = request.FILES.getlist('attachments')
                    for attachment in attachments:
                        RejectionAttachment.objects.create(rejection=rejection, attachment=attachment)
                    messages.success(request, 'You have successfully rejected the nonconformity.')
                    return redirect('nonconformity:nonconformities')
            else:
                messages.error(request, 'Sorry, something went wrong. Please try again.')
                return render(request, 'risk/nonconformity/nonconformity_details.html',{'nonconformity': nonconformity, 'acceptanceForm': acceptanceForm,'rejectionForm':rejectionForm, 'form': form, 'attachments': attachments })
        elif request.user == nonconformity.created_by:
            if nonconformity.accepted != True:
                form = NonconformityForm(request.POST, instance=nonconformity)
                if form.is_valid():
                    nc = form.save(commit=False)
                    nc.accepted = None
                    nc.save()
                    attachments = request.FILES.getlist('attachments')
                    print('attachments',attachments)
                    for attachment in attachments:
                        Attachment.objects.create(acceptance=nc, attachment=attachment)
                    messages.success(request, 'Nonconformity updated successfully!')
                    return redirect('nonconformity:nonconformities')
            elif nonconformity.accepted == True and nonconformity.resolved == True:
                form = CloseNcForm(request.POST, instance=nonconformity)
                if form.is_valid():
                    form.save()
                    return redirect('nonconformity:nonconformities')
            else: 
                messages.error(request, 'You cannot make changes on this nonconformity at the moment.')
                return redirect('nonconformity:nonconformities')
    else:
        acceptanceForm = None
        rejectionForm = None
        form = None
        if request.user == nonconformity.recipient and nonconformity.accepted ==None :
            rejectionForm = RejectionForm()
            acceptanceForm = AcceptanceForm(instance=nonconformity)
        elif request.user == nonconformity.recipient and nonconformity.accepted == True and nonconformity.resolved != True:
            form = ResolveNcForm(instance=nonconformity)
        elif request.user == nonconformity.created_by and nonconformity.resolved == True and nonconformity.accepted == True and nonconformity.closed != True:
            form = CloseNcForm(instance=nonconformity)
        elif request.user == nonconformity.created_by and nonconformity.accepted != True:
            form = NonconformityForm(instance=nonconformity)
        old_notifications = Notification.objects.filter(user=request.user, url=nonconformity.get_absolute_url())
        old_notifications.update(is_read=True)
        return render(request, 'risk/nonconformity/nonconformity_details.html', {'nonconformity': nonconformity, 'acceptanceForm': acceptanceForm,'rejectionForm':rejectionForm, 'form': form})
@login_required
def view_notifications(request):
    user = request.user  # Assuming you have authentication enabled
    notifications = Notification.objects.filter(user=user).order_by('is_read', '-created_at')
    return render(request, 'risk/nonconformity/inbox.html', {'notifications': notifications})
@login_required
def view_nonconformities(request):
    return render(request, 'risk/nonconformity/nonconformities.html', {'nonconformities': Nonconformity.objects.all()})

@login_required
def my_nonconformities(request):
    # Get the current user
    user = request.user
    nonconformities = Nonconformity.objects.filter(
            Q(created_by=user) | Q(recipient=user)
        )
    return render(request, 'risk/nonconformity/mynonconformities.html', {'nonconformities': nonconformities})
#create clause and its questions using generic view it must redirect to the checklist view
def check_roles(request):
    """to edit checklist user must have a role with application= non_conformity and role=supervisor """
    user = request.user
    return any(role.application == 'non_conformity' and role.role == 'supervisor' for role in user.roles.all())

"""checklist functions to create, edit and view checklist"""

@login_required
@checklist_roles
def create_clause(request):
    if request.method == 'POST':
        form = ClauseForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('nonconformity:editable_checklist')
    else:
        form = ClauseForm()
    return render(request, 'risk/nonconformity/create_edit_checklist.html', {'form': form})
@login_required
@checklist_roles
def create_topic(request, clause):
    clause = Clause.objects.get(id=clause)
    if request.method == 'POST':
        form = TopicForm(request.POST)
        if form.is_valid():
            topic = form.save(commit=False)
            topic.clause = clause
            topic.save()
            return redirect('nonconformity:editable_checklist')
    else:
        form = TopicForm()
    return render(request, 'risk/nonconformity/create_edit_checklist.html', {'form': form})
@login_required
@checklist_roles
def create_iso_req(request, topic):
    topic = Topic.objects.get(id=topic)
    if request.method == 'POST':
        form = QuestionForm(request.POST)
        if form.is_valid():
            iso_req = form.save(commit=False)
            iso_req.topic = topic
            iso_req.save()
            return redirect('nonconformity:editable_checklist')
    else:
        form = QuestionForm()
    return render(request, 'risk/nonconformity/create_edit_checklist.html', {'form': form})
@login_required
def checklist(request):
    return render(request, 'risk/nonconformity/checklist.html',{'clauses':Clause.objects.all()}) 
@login_required
@checklist_roles
def editable_checklist(request):
    return render(request, 'risk/nonconformity/editable_checklist.html',{'clauses':Clause.objects.all()})
@login_required
@checklist_roles
def edit_clause(request, clause):
    clause = Clause.objects.get(id=clause)
    if request.method == 'POST':
        form = ClauseForm(request.POST, instance=clause)
        if form.is_valid():
            form.save()
            return redirect('nonconformity:editable_checklist')
    else:
        form = ClauseForm(instance=clause)
    return render(request, 'risk/nonconformity/create_edit_checklist.html', {'form': form})

@login_required
@checklist_roles
def edit_topic(request, topic):
    topic = Topic.objects.get(id=topic)
    if request.method == 'POST':
        form = TopicForm(request.POST, instance=topic)
        if form.is_valid():
            form.save()
            return redirect('nonconformity:editable_checklist')
    else:
        form = TopicForm(instance=topic)
    return render(request, 'risk/nonconformity/create_edit_checklist.html', {'form': form})
@login_required
@checklist_roles
def edit_iso_req(request, iso_req):
    iso_req = Question.objects.get(id=iso_req)
    if request.method == 'POST':
        form = QuestionForm(request.POST, instance=iso_req)
        if form.is_valid():
            form.save()
            return redirect('nonconformity:editable_checklist')
    else:
        form = QuestionForm(instance=iso_req)
    return render(request, 'risk/nonconformity/create_edit_checklist.html', {'form': form})

def notify(request):
    send_mail(
        subject='Hello from Django qwertyuio',
        message='This is a test email.',
        from_email='perseychinaka@gmail.com',
        recipient_list=['perseychinaka1@gmail.com','pchinaka@zetdc.co.zw'],
        fail_silently=False
    )
    return HttpResponse('Email sent successfully!')
    # ['ruvheneko@zetdc.co.zw'],  # recipient list
