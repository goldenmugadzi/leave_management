# views.py

from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import DetailView, ListView
from .models import BatteryInstallation,Substation
from .forms import BatteryInstallationForm, CellFormSet
from django.contrib.auth.mixins import LoginRequiredMixin
import csv
from django.http import HttpResponse
from .models import Regions, Districts, Depots, Substation

def import_substations_from_csv(request):
    csv_path = r'./SUBSTATIONS_PERCY.csv'  # Update path if needed
    created = 0
    skipped = 0
    
    with open(csv_path, newline='', encoding='utf-8') as csvfile:
        reader = csv.DictReader(csvfile)
        
        for row in reader:
            name = row['name'].strip()
            region_name = row['region_name'].strip() if row['region_name'] else None
            district_name = row['district_name'].strip() if row['district_name'] else None
            depot_name = row['depot_name'].strip() if row['depot_name'] else None

            # Only create if all required fields are present
            if not (name and region_name and district_name and depot_name):
                skipped += 1
                missing_fields = []
                if not name:
                    missing_fields.append('name')
                if not region_name:
                    missing_fields.append('region_name')
                if not district_name:
                    missing_fields.append('district_name')
                if not depot_name:
                    missing_fields.append('depot_name')
                
                print(f"Skipped row due to missing fields: {', '.join(missing_fields)}")
                continue

            # Use icontains for case-insensitive filtering
            region = Regions.objects.filter(region__icontains=region_name).first()
            district = Districts.objects.filter(district__icontains=district_name).first()
            depot = Depots.objects.filter(depot__icontains=depot_name).first()

            if region and district and depot:
                sub, was_created = Substation.objects.get_or_create(
                    name=name,
                    region=region,
                    district=district,
                    depot=depot
                )
                if was_created:
                    created += 1
            else:
                skipped += 1
                missing_entities = []
                if not region:
                    missing_entities.append(f"region '{name}{region_name}'")
                if not district:
                    missing_entities.append(f"district '{name}{district_name}'")
                if not depot:
                    missing_entities.append(f"depot '{name}{depot_name}'")
                
                print(f"Skipped row because could not find: {', '.join(missing_entities)}")

    return HttpResponse(f"Imported {created} substations. Skipped {skipped} rows.")
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.shortcuts import render, redirect
from .forms import BatteryInstallationForm, CellFormSet, SubstationForm
from .models import Substation

class InstallBattery(LoginRequiredMixin, View):
    template_name = 'battery/install_battery.html'
    
    def get(self, request):
        form = BatteryInstallationForm(user=request.user)
        formset = CellFormSet()
        substationForm = SubstationForm(user=request.user)
        
        return render(request, self.template_name, {
            'form': form,
            'formset': formset,
            'substationForm': substationForm,
        })
    
    def post(self, request):
        form = BatteryInstallationForm(request.POST, user=request.user)
        formset = CellFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            battery = form.save()
            new_substation_name = form.cleaned_data.get('new_substation')
            if new_substation_name:
                substation = Substation.objects.create(name=new_substation_name, region=request.user.region)
            else:
                substation = form.cleaned_data['substation']
            cells = formset.save(commit=False)
            for cell in cells:
                cell.installation = battery
                cell.save()

            return redirect('BatteryMaintenance:install_battery')  
        
        return render(request, self.template_name, {
            'form': form,
            'formset': formset
        })
    
class BatteryInstallationListView(ListView):
    model = BatteryInstallation
    template_name = 'battery/battery_installation_list.html'
    context_object_name = 'installations'
    paginate_by = 20  # optional

class BatteryInstallationDetailView(DetailView):
    model = BatteryInstallation
    template_name = "battery/battery_installation_detail.html"
    context_object_name = "installation"

