# views.py

from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import DetailView, ListView
from .models import BatteryInstallation, Substation,BatteryMaintenance
from .forms import BatteryInstallationForm, CellFormSet1,  CellFormSet, SubstationForm
from django.contrib.auth.mixins import LoginRequiredMixin
import csv
from django.http import HttpResponse
from it.users.models import Notification, Regions, Districts, Depots
from django.contrib import messages
import os
from django.contrib.auth.decorators import login_required
# from EquipTracker.models import addEquipment ,addEquipmentChange

@login_required
def clear_notifications(request):
    if request.method == "POST":
        # Example: Assuming you have a Notification model
        Notification.objects.filter(user=request.user).delete()
        print("got here")
        messages.success(request, "Notifications cleared successfully.")
    
    return redirect("/")  
    
def import_substations_from_csv(request):
    csv_path = os.path.join(os.path.dirname(__file__), 'SUBSTATIONS_PERCY.csv')  
    created = 0
    skipped = 0

    with open(csv_path, newline="", encoding="utf-8") as csvfile:
        reader = csv.DictReader(csvfile)

        for row in reader:
            name = row["name"].strip()
            region_name = row["region_name"].strip() if row["region_name"] else None
            code = row["code"].strip() if row["code"] else None
            district_name = (
                row["district_name"].strip() if row["district_name"] else None
            )
            depot_name = row["depot_name"].strip() if row["depot_name"] else None

            # Only create if all required fields are present
            if not (name and region_name and district_name and depot_name):
                skipped += 1
                missing_fields = []
                if not name:
                    missing_fields.append("name")
                if not region_name:
                    missing_fields.append("region_name")
                if not district_name:
                    missing_fields.append("district_name")
                if not depot_name:
                    missing_fields.append("depot_name")

                print(f"Skipped row due to missing fields: {', '.join(missing_fields)}")
                continue

            # Use icontains for case-insensitive filtering
            region = Regions.objects.filter(region__icontains=region_name).first()
            district = Districts.objects.filter(
                district__icontains=district_name
            ).first()
            depot = Depots.objects.filter(depot__icontains=depot_name).first()

            # if region and district and depot:
            sub, was_created = Substation.objects.get_or_create(
                name=name, region=region, district=district, depot=depot, code=code
            )
            if was_created:
                created += 1
            # else:
            #     skipped += 1
            #     missing_entities = []
            #     if not region:
            #         missing_entities.append(f"region '{name}{region_name}'")
            #     if not district:
            #         missing_entities.append(f"district '{name}{district_name}'")
            #     if not depot:
            #         missing_entities.append(f"depot '{name}{depot_name}'")

            #     print(
            #         f"Skipped row because could not find: {', '.join(missing_entities)}"
            #     )

    return HttpResponse(f"Imported {created} substations. Skipped {skipped} rows.")



class InstallBattery(LoginRequiredMixin, View):
    template_name = "battery/install_battery.html"

    def get(self, request):
        form = BatteryInstallationForm(user=request.user)
        formset = CellFormSet()
        substationForm = SubstationForm(user=request.user)

        return render(
            request,
            self.template_name,
            {
                "form": form,
                "formset": formset,
                "substationForm": substationForm,
            },
        )
    def post(self, request):
        form = BatteryInstallationForm(request.POST, user=request.user)
        formset = CellFormSet(request.POST)
        substationForm = SubstationForm(request.POST, user=request.user)

        if form.is_valid() and formset.is_valid():
            existing_sub = form.cleaned_data.get("substation")
            if existing_sub:
                substation = existing_sub
            elif substationForm.is_valid():
                substation = substationForm.save()
            else:
                return render(request, self.template_name, {
                    "form": form,
                    "formset": formset,
                    "substationForm": substationForm,
                })
            # equipment_id = addEquipment("Battery")
            battery = form.save(commit=False)
            # battery.equipment_tracker = equipment_id
            battery.substation = substation
            battery.save()
            # addEquipmentChange(
            #     district=substation.district.district,
            #     substation=substation,
            #     equipment_tracker=equipment_id,
            #     action_taken="Insalation",
            #     date=battery.date,
            #     reason="Insalation of new battery",
            #     signed_by=request.user,
            # )
            cells = formset.save(commit=False)
            for cell in cells:
                cell.installation = battery
                if cell.voltage is not None:
                    cell.save()

            # Calculate summary fields after all cells are saved
            all_cells = battery.cells.all()
            voltages = [cell.voltage for cell in all_cells if cell.voltage is not None]
            sgs = [cell.specific_gravity for cell in all_cells if cell.specific_gravity is not None]
            if voltages:
                battery.volts_high = max(voltages)
                battery.volts_low = min(voltages)
                battery.volts_avg = sum(voltages) / len(voltages)
            if sgs:
                battery.sg_high = max(sgs)
                battery.sg_low = min(sgs)
                battery.sg_avg = sum(sgs) / len(sgs)
            battery.save()

            messages.success(request, "Battery installation submitted successfully.")
            return redirect("BatteryMaintenance:install_battery")

        return render(request, self.template_name, {
            "form": form,
            "formset": formset,
            "substationForm": substationForm,
        })


class InspectBattery(LoginRequiredMixin, DetailView):
    model = BatteryInstallation
    template_name = "battery/inspect_battery.html"
    context_object_name = "installation"

    def get(self, request, *args, **kwargs):
        # Get the BatteryInstallation instance (DetailView normally does this)
        installation = self.get_object()

        # Create a formset for related cells, bound to this installation
        formset = CellFormSet1(instance=installation)

        context = {
            "installation": installation,
            "formset": formset,
        }
        return render(request, self.template_name, context)

class BatteryInstallationListView(ListView):
    model = BatteryInstallation
    template_name = "battery/battery_installation_list.html"
    context_object_name = "installations"
    paginate_by = 20
    ordering = ['-date']  # or any field you want to order by


class BatteryInstallationDetailView(DetailView):
    model = BatteryInstallation
    template_name = "battery/battery_installation_detail.html"
    context_object_name = "installation"

class DetailedBatteryInfo(LoginRequiredMixin, DetailView):
    model = BatteryMaintenance
    template_name = "battery/detailed_battery_info.html"
    context_object_name = "battery"

