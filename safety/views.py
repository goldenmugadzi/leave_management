from django.shortcuts import render, redirect
from .models import SafetyMonthlyReport
from .forms import SafetyMonthlyReportForm 
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from django.shortcuts import get_object_or_404, render, redirect 
from django.db import transaction,IntegrityError
def safety_table(request):
    reports = SafetyMonthlyReport.objects.all().order_by('-year', '-month')
    return render(request, 'safety/safety_table.html', {'reports': reports})

def safety_report_create(request):
    if request.method == 'POST':
        form = SafetyMonthlyReportForm(request.POST)
        if form.is_valid():
            report = form.save(commit=False)
            report.user = request.user  # Set the user to the currently logged-in user
            report.save()
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
            # All YTD fields below
            "ytd_work_related_accidents": report.ytd_work_related_accidents,
            "ytd_disabling_accidents": report.ytd_disabling_accidents,
            "ytd_fatal_accidents": report.ytd_fatal_accidents,
            "ytd_man_hours_lost": report.ytd_man_hours_lost,
            "ytd_accident_free_days": report.ytd_accident_free_days,
            "ytd_motor_vehicle_accidents": report.ytd_motor_vehicle_accidents,
            "ytd_property_damaged": report.ytd_property_damaged,
            "ytd_she_meetings_conducted": report.ytd_she_meetings_conducted,
            "ytd_she_related_trainings": report.ytd_she_related_trainings,
            "ytd_wellness_programmes": report.ytd_wellness_programmes,
            "ytd_clear_up_campaigns": report.ytd_clear_up_campaigns,
            "ytd_she_inspections_conducted": report.ytd_she_inspections_conducted,
            "ytd_mock_drills_conducted": report.ytd_mock_drills_conducted,
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })

def safety_update(request, id):
   safetymonthlyreport = get_object_or_404(SafetyMonthlyReport, id=id)

   if request.method == 'POST':
        form = SafetyMonthlyReportForm (request.POST, instance=safetymonthlyreport)

        if form.is_valid():
            try:
                with transaction.atomic():
                    form.save()
                    
                    messages.success(request, "report updated successfully!")
                    return redirect('/safety_table/')
            except Exception as e:
                messages.error(request, f"Error updating fault: {str(e)}")
        else:
            messages.error(request, "Please correct the errors below.")
   else:
        form = SafetyMonthlyReportForm (instance=safetymonthlyreport)

   return render(request, 'safety/safety_update.html', {'form': form, 'safetymonthlyreport': safetymonthlyreport})

def safety_ytd(request):
    report = SafetyMonthlyReport.objects.latest('year', 'month')
    # Find previous month (handle January)
    prev_month = report.month - 1
    prev_year = report.year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1
    prev_report = SafetyMonthlyReport.objects.filter(
        year=prev_year,
        month=prev_month,
        department=report.department,
        regions=report.regions
    ).first()
    return render(request, 'safety/ytd.html', {
        'report': report,
        'prev_report': prev_report
    })