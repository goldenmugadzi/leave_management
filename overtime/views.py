from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import OvertimeEntry
from .forms import OvertimeEntryForm
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.timezone import localtime
from datetime import datetime, timedelta

def create_overtime_entry(request):
    from datetime import datetime, timedelta
    from django.utils.crypto import get_random_string
    period_fields = [
        "month", "period_from", "period_to",
        "district_station", "designation", "ec_number"
    ]

    username = None
    if request.user.is_authenticated:
        username = request.user.username

    if request.method == "POST":
        form = OvertimeEntryForm(request.POST, user=request.user)
        if form.is_valid():
            entry = form.save(commit=False)

            entry.created_by = request.user

            #TAKE EC NUMBER FROM THE CURRENTLY LOGGED IN PERSON IN THE SYSTEM 
            if username and not entry.ec_number:
                entry.ec_number = username

            # generation of JOB NUMBER
            now = datetime.now()
            random_part = get_random_string(3).upper()
            entry.job_vote_number = f"OVT-{now.strftime('%Y%m%d-%H%M%S')}"

            #time frame to calculate hours on the table 
            time_in = entry.time_in
            time_out = entry.time_out
            dt_in = datetime.combine(entry.period_from, time_in)
            dt_out = datetime.combine(entry.period_from, time_out)
            if dt_out < dt_in:
                dt_out += timedelta(days=1)
            duration = dt_out - dt_in
            entry.hours = round(duration.total_seconds() / 3600, 2)

            entry.save()
            return redirect("/table")
    else:
        form = OvertimeEntryForm(user=request.user)

    return render(request, "overtime/overtime_entry_form.html", {
        "form": form,
        "period_fields": period_fields,
    })


def overtime_list (request):
    return render(request, 'overtime/overtime_table.html')



def overtime_datatable(request):
    draw = int(request.GET.get("draw", 1))
    start = int(request.GET.get("start", 0))
    length = int(request.GET.get("length", 10))

    qs =OvertimeEntry.objects.select_related(
        "designation",
        "name_of_employee",
        "created_by"
    )

    total = qs.count()
    paginator = Paginator(qs, length)
    page = paginator.get_page(start // length + 1)

    data = []
    for o in page:
        data.append({
            "id": o.id,
            "job_vote_number": o.job_vote_number,
            "month": o.month,
            "employee": str(o.name_of_employee) if o.name_of_employee else "-",
            "ec_number": o.ec_number,
            "designation": str(o.designation) if o.designation else "-",
            "district_station": o.district_station,
            "period_from": o.period_from.strftime("%Y-%m-%d"),
            "period_to": o.period_to.strftime("%Y-%m-%d"),
            "time_in": o.time_in.strftime("%H:%M"),
            "time_out": o.time_out.strftime("%H:%M"),
            "hours": str(o.hours) if o.hours else "0.00",
            "nature_of_work": o.nature_of_work,
            "created_by": str(o.created_by) if o.created_by else "-",
            "created_at": localtime(o.created_at).strftime("%Y-%m-%d %H:%M"),
            
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })
