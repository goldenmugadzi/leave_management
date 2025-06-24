from django.shortcuts import render, redirect
from .forms import LeaveRequestForm
from django.contrib import messages

def leave_create(request):
    if request.method == 'POST':
        form = LeaveRequestForm(request.POST)
        if form.is_valid():
            leave = form.save(commit=False)
            leave.user = request.user 
            leave.save()
            messages.success(request, "Leave request submitted successfully.")
            return redirect('leave_list') 
    else:
        form = LeaveRequestForm()
    return render(request, 'leave_system/create_leave.html', {'form': form})