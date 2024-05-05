
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
                return redirect('/', messages.SUCCESS)
            else:
                return HttpResponse("You cannot create a nonconformity for yourself.")
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
def additionalInfoForm(request, nonconformity_id):
    nonconformity = get_object_or_404(Nonconformity, id=nonconformity_id)
    if request.method == 'POST':
        form = AdditionalInfoForm(request.POST, instance=nonconformity)
        if form.is_valid():
            nonconformity = form.save(commit=False)
            # Additional processing or validation if needed
            nonconformity.save()
            return redirect('nonconformity:nonconformities')
    else:
        form = AdditionalInfoForm()
    return render(request, 'risk/nonconformity/additional_info.html', {'nonconformity': nonconformity, 'form': form})

@login_required
def nonconformity_details(request, nonconformity_id):
    nonconformity = get_object_or_404(Nonconformity, id=nonconformity_id)
    try:
        response = Response.objects.get(Q(nonconformity=nonconformity), Q(user=request.user))
    except Response.DoesNotExist:
        # No matching response found
        response = None

    if request.method == 'POST':
        if request.user == nonconformity.recipient:
            response_form = NonconformityResponseForm(request.POST, instance=response)
            if response_form.is_valid():
                response = response_form.save(commit=False)
                response.user = request.user
                response.nonconformity = nonconformity
                response.save()

                # Prompt for additional information if status is 'accepted'
                if response.status == 'True':
                    additional_info_form = AdditionalInfoForm(instance=nonconformity)  # Create an instance of the additional info form
                    return render(request, 'risk/nonconformity/additional_info.html', {'nonconformity': nonconformity, 'form': additional_info_form})
                
                # Notify the user who created the nonconformity
                Notification.objects.create(
                    user=nonconformity.created_by,
                    message=f"Response from {request.user.username} on nonconformity: {nonconformity.description}",
                    url=nonconformity.get_absolute_url()
                )

                messages.success(request, 'Response added successfully!')
                return redirect('/nonconformities', nonconformity_id=nonconformity.id)
            else:
                # print(str(response_form))
                return render(request, 'risk/nonconformity/nonconformity_details.html', {'nonconformity': nonconformity, 'form': response_form})
        elif request.user == nonconformity.created_by:
            form = NonconformityForm(request.POST, request.FILES, instance=nonconformity)
            if form.is_valid():
                edited_nonconformity = form.save(commit=False)

                # Check if the recipient is the same as the current user
                if edited_nonconformity.recipient != request.user:
                    # Save the edited nonconformity
                    edited_nonconformity.save()

                    # Create a notification for the auditee
                    auditee = edited_nonconformity.recipient
                    notification = Notification.objects.create(
                        user=auditee,
                        message=f"nc: {edited_nonconformity.description}",
                        url=reverse('nonconformity:nonconformity', args=[edited_nonconformity.id])
                    )

                    # Display a success message
                    messages.success(request, 'Nonconformity edited successfully!')
                    return redirect('/', messages.SUCCESS)
        else:
            return HttpResponse("You are not authorized to edit this nonconformity.")

    else:  # GET request
        nonconformity_accepted = False
        AcceptedForm=None
        if Response.objects.filter(nonconformity=nonconformity).exists():
            if Response.objects.filter(nonconformity=nonconformity).latest('created_at').status == 'false':
                nonconformity_accepted = True
        if request.user == nonconformity.recipient:
            form = NonconformityResponseForm(instance=response)
            AcceptedForm=AdditionalInfoForm(instance=nonconformity)
        elif request.user == nonconformity.created_by and not nonconformity_accepted:
            form = NonconformityForm(instance=nonconformity)
        else:
            form = None
    # Update the old notification to mark it as read
    old_notifications = Notification.objects.filter( user=request.user,url=nonconformity.get_absolute_url())
    for old_notification in old_notifications:
        old_notification.is_read = True
        old_notification.save()
        
    return render(request, 'risk/nonconformity/nonconformity_details.html', {'nonconformity': nonconformity,"AcceptedForm":AcceptedForm, 'form': form})

@login_required
def view_notifications(request):
    user = request.user  # Assuming you have authentication enabled
    notifications = Notification.objects.filter(user=user).order_by('is_read', '-created_at')
    return render(request, 'risk/nonconformity/inbox.html', {'notifications': notifications})
    
@login_required
def view_nonconformities(request):
    user = request.user
    nonconformities = Nonconformity.objects.filter(
        Q(created_by__region=user.region) | Q(recipient__region=user.region)
    )
    #for each nonconformity in nonconformities, get the add a field section with the section name of the recipient
    for nonconformity in nonconformities:
        try:
            response = Response.objects.filter(nonconformity=nonconformity).latest('created_at')
            nonconformity.status = f"{response.user.first_name[0]}. {response.user.last_name} : {response.status}"
        except Response.DoesNotExist:
            nonconformity.status = 'created'

    return render(request, 'risk/nonconformity/nonconformities.html', {'nonconformities': nonconformities})

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
