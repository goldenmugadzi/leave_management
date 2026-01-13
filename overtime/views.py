from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import OvertimeEntry
from .forms import OvertimeEntryForm
from django.http import JsonResponse
from django.core.paginator import Paginator
from django.utils.timezone import localtime


def create_overtime_entry(request):
	period_fields = [
		"month", "period_from", "period_to", "district_station", "designation", "ec_number"
	]
	if request.method == "POST":
		form = OvertimeEntryForm(request.POST, user=request.user)
		if form.is_valid():
			entry = form.save(commit=False)
			entry.created_by = request.user
            #entry.created_at = date.now
			entry.save()
			return redirect("overtime:entry_success")
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
            "job_vote_number": o.job_vote_number,
        })

    return JsonResponse({
        "draw": draw,
        "recordsTotal": total,
        "recordsFiltered": total,
        "data": data
    })
