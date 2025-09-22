from django.views.generic import View
from django.shortcuts import render, redirect
from .models import SafetyMonthlyReport,AccidentReport,VehicleAccidentReport, PropertyLossIncident
from .forms import SafetyMonthlyReportForm,AccidentReportForm, VehicleAccidentReportForm, PropertyLossIncidentForm
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q
from .models import AccidentReport
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
            report.user = request.user  
            report.save()
            messages.success(request, "Safety report submitted successfully.")
            return redirect('safety_table')
    else:
        form = SafetyMonthlyReportForm()
    return render(request, 'safety/safety_form.html', {'form': form})

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
    prev_month = report.month - 1
    prev_year = report.year
    if prev_month == 0:
        prev_month = 12
        prev_year -= 1

    prev_report = SafetyMonthlyReport.objects.filter(
        year=prev_year,
        month=prev_month
    ).first()

    return render(request, 'safety/ytd.html', {
        'report': report,
        'prev_report': prev_report
    })
       
def create_accident(request):
    accident_form = AccidentReportForm()
    vehicle_form = VehicleAccidentReportForm()
    property_loss_form = PropertyLossIncidentForm()

    if request.method == 'POST':
        # Check which form was submitted by submit button name
        if 'submit_vehicle' in request.POST:
            vehicle_form = VehicleAccidentReportForm(request.POST, request.FILES)
            if vehicle_form.is_valid():
                vehicle_report = vehicle_form.save(commit=False)
                # vehicle_report.user = request.user
                vehicle_report.save()
                messages.success(request, "Vehicle accident report submitted successfully.")
                return redirect('accident_report_dashboard')
        elif 'submit_accident' in request.POST:
            accident_form = AccidentReportForm(request.POST)
            if accident_form.is_valid():
                accident = accident_form.save(commit=False)
                # accident.user = request.user
                accident.save()
                messages.success(request, "Human accident report submitted successfully.")
                return redirect('accident_report_dashboard')
        elif 'submit_property_loss' in request.POST:
            property_loss_form = PropertyLossIncidentForm(request.POST, request.FILES)
            if property_loss_form.is_valid():
                incident = property_loss_form.save(commit=False)
                incident.user = request.user
                incident.save()
                messages.success(request, "Property loss incident report submitted successfully.")
                return redirect('accident_report_dashboard') 

    return render(request, 'safety/accident_report.html', {
        'form': accident_form,
        'vehicle_form': vehicle_form,
        'property_loss_form': property_loss_form,
    })


def accident_reports_datatable(request):
    draw = int(request.GET.get('draw', 1))
    start = int(request.GET.get('start', 0))
    length = int(request.GET.get('length', 10))
    search_value = request.GET.get('search[value]', '')

    qs = AccidentReport.objects.all()

    if search_value:
        qs = qs.filter(
            Q(employee_involved__user__username__icontains=search_value) |
            Q(department__section__icontains=search_value) |
            Q(regions__region__icontains=search_value) |
            Q(type_of_accident__icontains=search_value) |
            Q(nature_of_accident__icontains=search_value) |
            Q(nature_of_injury__icontains=search_value) |
            Q(ec_number__icontains=search_value)
        )

    total = qs.count()
    qs = qs.order_by('-date')[start:start+length]

    data = []
    for report in qs:
        data.append({
            "id": report.id,
            "employee_involved": str(report.employee_involved) if report.employee_involved else "",
            "department": str(report.department) if report.department else "",
            "regions": str(report.regions) if report.regions else "",
            "date": report.date.strftime('%Y-%m-%d'),
            "time": report.time.strftime('%H:%M'),
            "cost_center": str(report.cost_center) if report.cost_center else "",
            "ec_number": report.ec_number,
            "type_of_accident": report.type_of_accident,
            "nature_of_accident": report.nature_of_accident,
            "nature_of_injury": report.nature_of_injury,
            "circumstance_leading_to_accident": report.circumstance_leading_to_accident,
            "location_of_accident_giving_line_and_section_number": report.location_of_accident_giving_line_and_section_number,
            "attach_pretask_risk_assessment": report.attach_pretask_risk_assessment.url if report.attach_pretask_risk_assessment else "",
            "operation_of_protective_devices": report.operation_of_protective_devices,
            "attach_photographs": report.attach_photographs.url if report.attach_photographs else "",
            "steps_taken_on_the_short_term": report.steps_taken_on_the_short_term,
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })

def table_accident(request):
    return render(request, 'safety/table_accident.html')

from .models import AccidentReport, VehicleAccidentReport, PropertyLossIncident

def accident_report_dashboard(request):
    # Statistics
    total_accidents = AccidentReport.objects.count() + VehicleAccidentReport.objects.count() + PropertyLossIncident.objects.count()
    property_count = PropertyLossIncident.objects.count()
    staff_count = AccidentReport.objects.count()
    vehicle_count = VehicleAccidentReport.objects.count()

    # Table data: combine all accident types
    accidents = []

    # Property Loss
    for incident in PropertyLossIncident.objects.all():
        accidents.append({
            'id': incident.id,
            'type': 'property',
            'reported_by': incident.reported_by,
            'date': incident.date_of_report,
            'status': 'Pending',  # You can add a status field to your model if needed
        })

    # Human Accident
    for accident in AccidentReport.objects.all():
        accidents.append({
            'id': accident.id,
            'type': 'human',
            #'reported_by': getattr(accident.employee_involved, 'user', accident.employee_involved),
            'date': accident.date_of_accident,
            'status': 'Pending',  # Add status logic if you have it
        })

    # Vehicle Accident
    for vehicle in VehicleAccidentReport.objects.all():
        accidents.append({
            'id': vehicle.id,
            'type': 'vehicle',
            'reported_by': vehicle.driver_name,
            'date': getattr(vehicle, 'datetime_for_accident', vehicle.date_submitted),
            'status': 'Pending',  # Add status logic if you have it
        })

    # Optionally, sort by date descending
    accidents = sorted(accidents, key=lambda x: x['date'], reverse=True)

    return render(request, 'safety/accident_report.html', {
        'total_accidents': total_accidents,
        'property_count': property_count,
        'staff_count': staff_count,
        'vehicle_count': vehicle_count,
        'accidents': accidents,
        'form': AccidentReportForm(),
        'vehicle_form': VehicleAccidentReportForm(),
        'property_loss_form': PropertyLossIncidentForm(),
    })


