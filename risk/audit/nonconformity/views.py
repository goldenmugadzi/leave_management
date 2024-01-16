
from django.shortcuts import render, redirect,reverse,get_object_or_404,HttpResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
import json
from .models import Nonconformity
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
    response_form = NonconformityResponseForm()

    if request.method == 'POST':
        response_form = NonconformityResponseForm(request.POST, instance=nonconformity)
        if response_form.is_valid():
            response = response_form.save(commit=False)
            response.auditee = request.user
            response.response = f"Description: {response_form.cleaned_data['description'] if response_form.cleaned_data['description'] else ' '}\nExpected Completion Date: {response_form.cleaned_data['expected_completion_date'] if response_form.cleaned_data['expected_completion_date'] else ' '}"
            response.save()
            messages.success(request, 'Nonconformity saved successfully!')

            # Find the matching notification and mark it as read
           
            return redirect('/', messages.SUCCESS)
    matching_notification = Notification.objects.filter(user=request.user, url=request.path, is_read=False).first()
    if matching_notification:
        matching_notification.is_read = True
        matching_notification.save()
        
    return render(request, 'risk/nonconformity/nonconformity_details.html', {'nonconformity': nonconformity,'form': response_form, })

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