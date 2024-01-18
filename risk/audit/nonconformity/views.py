
from django.shortcuts import render, redirect,reverse,get_object_or_404,HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
from .models import Nonconformity,Response
from .forms import NonconformityForm, NonconformityResponseForm
from django.contrib.auth.models import User
# from it.users.models import Notification
from django.apps import apps
Notification = apps.get_model(app_label='users', model_name='Notification')


from django.contrib import messages



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
def nonconformity_details(request, nonconformity_id):
    nonconformity = get_object_or_404(Nonconformity, id=nonconformity_id)
    response = Response.objects.filter(nonconformity=nonconformity, user=request.user).first()

    if request.method == 'POST':
        if request.user == nonconformity.recipient:
            response_form = NonconformityResponseForm(request.POST, instance=response)
            if response_form.is_valid():
                response = response_form.save(commit=False)
                response.user = request.user
                response.nonconformity = nonconformity
                response.save()
                
                # Notify the user who created the nonconformity
                Notification.objects.create(
                    user=nonconformity.created_by,
                    message=f"Response from {request.user.username} on nonconformity: {nonconformity.description}",
                    url=nonconformity.get_absolute_url()
                )

                messages.success(request, 'Response added successfully!')
                return redirect('/nonconformities', nonconformity_id=nonconformity.id)

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
        if request.user == nonconformity.recipient:
           
            form = NonconformityResponseForm(instance=response)
        elif request.user == nonconformity.created_by:
            form = NonconformityForm(instance=nonconformity)
        else:
            form = None
    # Update the old notification to mark it as read
    old_notifications = Notification.objects.filter( user=request.user,url=nonconformity.get_absolute_url())
    for old_notification in old_notifications:
        old_notification.is_read = True
        old_notification.save()
        
    return render(request, 'risk/nonconformity/nonconformity_details.html', {'nonconformity': nonconformity, 'form': form})

@login_required
def view_notifications(request):
    user = request.user  # Assuming you have authentication enabled
    notifications = Notification.objects.filter(user=user).order_by('is_read', '-created_at')
    return render(request, 'risk/nonconformity/inbox.html', {'notifications': notifications})
@login_required
def view_nonconformities(request):
    # Get the current user
    user = request.user

    # Check if the current user belongs to the section head group
    if user.groups.filter(name='Section Head').exists():
        # Get the users with the same designation and region as the section head
        users_with_same_designation = User.objects.filter(section=user.section)

        # Get the nonconformities created by the users with the same designation and region,
        # as well as nonconformities created for or by the section head
        nonconformities = Nonconformity.objects.filter(
            Q(created_by__in=users_with_same_designation) |  Q(recipient__in=users_with_same_designation) | Q(recipient=request.user)
        )
    else:
        # If the user is not a section head, show all nonconformities created for or by the user
        nonconformities = Nonconformity.objects.filter(
            Q(created_by=user) | Q(recipient=user)
        )

    return render(request, 'risk/nonconformity/nonconformities.html', {'nonconformities': nonconformities})