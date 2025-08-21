from django.shortcuts import render, redirect
from .forms import AttendanceRecordForm

def attendance_record_create(request):
    if request.method == 'POST':
        form = AttendanceRecordForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('attendance_list')  
    else:
        form = AttendanceRecordForm()

    return render(request, 'attendance/attendance_form.html', {'form': form})
