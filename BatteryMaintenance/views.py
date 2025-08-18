# views.py

from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import DetailView, ListView
from .models import BatteryInstallation
from .forms import BatteryInstallationForm, CellFormSet
class InstallBattery(View):
    template_name = 'battery/install_battery.html'
    def get(self, request):
        form = BatteryInstallationForm(initial={'cost_center': request.user.cost_center})
        formset = CellFormSet()
        return render(request, self.template_name, {
            'form': form,
            'formset': formset
        })
    def post(self, request):
        form = BatteryInstallationForm(request.POST)
        formset = CellFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            battery = form.save()
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

