from django.shortcuts import render, redirect
from .models import SafetyMonthlyReport
from .forms import SafetyMonthlyReportForm  # You need to create this form
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q

def safety_table(request):
    reports = SafetyMonthlyReport.objects.all().order_by('-year', '-month')
    return render(request, 'safety/safety_table.html', {'reports': reports})

def safety_report_create(request):
    if request.method == 'POST':
        form = SafetyMonthlyReportForm(request.POST)
        if form.is_valid():
            form.save()
            messages.success(request, "Safety report submitted successfully.")
            return redirect('safety_table')
    else:
        form = SafetyMonthlyReportForm()
    return render(request, 'safety/report_form.html', {'form': form})

def safety_report_data(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')
    department_filter = request.GET.get('department', '')

    qs = SafetyMonthlyReport.objects.all()

    # Filtering by search
    if search_value:
        qs = qs.filter(
            Q(user__first_name__icontains=search_value) |
            Q(user__last_name__icontains=search_value) |
            Q(department__section__icontains=search_value)
        )

    # Filtering by department
    if department_filter:
        qs = qs.filter(department__section__icontains=department_filter)

    total = qs.count()

    # Pagination
    qs = qs.order_by('-id')[start:start+length]

    data = []
    for report in qs:
        data.append({
            "id": report.id,
            "user": str(report.user) if report.user else "",
            "department": str(report.department) if report.department else "",
            "regions": str(report.regions) if report.regions else "",
            "date": report.date.strftime('%Y-%m-%d') if report.date else "",
            "month": report.month,
            "year": report.year,
            "work_related_accidents": report.work_related_accidents,
            "disabling_accidents": report.disabling_accidents,
            "fatal_accidents": report.fatal_accidents,
            "man_hours_lost": report.man_hours_lost,
            "accident_free_days": report.accident_free_days,
            "motor_vehicle_accidents": report.motor_vehicle_accidents,
            "property_damaged": report.property_damaged,
            "number_of_workers": report.number_of_workers,
            "number_of_days": report.number_of_days,
            "accident_frequency_rate": report.accident_frequency_rate,
            "injury_severity_rate": report.injury_severity_rate,
            "ytd_work_related_accidents": report.ytd_work_related_accidents,
            "ytd_disabling_accidents": report.ytd_disabling_accidents,
            "ytd_fatal_accidents": report.ytd_fatal_accidents,
            "ytd_man_hours_lost": report.ytd_man_hours_lost,
            "ytd_motor_vehicle_accidents": report.ytd_motor_vehicle_accidents,
            "ytd_property_damaged": report.ytd_property_damaged,
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })
