from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from .models import OvertimeEntry
from .forms import OvertimeEntryForm

@login_required
def create_overtime_entry(request):
	period_fields = [
		"month", "period_from", "period_to", "district_station", "designation", "ec_number"
	]
	if request.method == "POST":
		form = OvertimeEntryForm(request.POST, user=request.user)
		if form.is_valid():
			entry = form.save(commit=False)
			entry.created_by = request.user.userprofile  # adjust if needed
			entry.save()
			return redirect("overtime:entry_success")
	else:
		form = OvertimeEntryForm(user=request.user)
	return render(request, "overtime/overtime_entry_form.html", {
		"form": form,
		"period_fields": period_fields,
	})

@login_required
def entry_success(request):
	return render(request, "overtime/entry_success.html")

