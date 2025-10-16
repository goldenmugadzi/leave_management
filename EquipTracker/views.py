# views.py

import os
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import DetailView, ListView
from .models import * 
from django.contrib.auth.mixins import LoginRequiredMixin
from .forms import *

class EquipmentListView(LoginRequiredMixin, ListView):
    model = Equipment
    template_name = 'equipment/equipment_list.html'
    context_object_name = 'equipments'
    paginate_by = 10
    ordering = ['-id']

    def get_queryset(self):
        user_region_id = self.request.user.region.id
        equipment_ids = EquipmentChange.objects.filter(substation__region_id=user_region_id).values_list('equipment_id', flat=True)
        for a in equipment_ids: print("qqqqqqqqq",a)
        return Equipment.objects.filter(id__in=equipment_ids, type_of_equipment='Battery').order_by('-id')
        

class EquipmentDetailView(LoginRequiredMixin, DetailView):
    model = Equipment
    template_name = 'equipment/equipment_tracker.html'
    context_object_name = 'equipment'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        return obj
 
class EquipmentChangeView(LoginRequiredMixin, View):
    template_name = 'equipment/equipment_change.html'

    def get(self, request):
        form = EquipmentChangeForm( user=request.user)
        equipment = EquipmentForm()

        # Prepopulate the formset with initial data
        initial_data = [
            {'action_taken': 'Installation'},  # First form prepopulated for Installation
            {'action_taken': 'Removal'},       # Second form prepopulated for Removal
        ]
        
        formset = EquipmentParticularsFormSet(queryset=EquipmentParticulars.objects.none(), initial=initial_data)
        
        return render(request, self.template_name, {'equipment':equipment, 'form':form, 'formset': formset})

    def post(self, request):
        form = EquipmentChangeForm(request.POST)
        formset = EquipmentParticularsFormSet(request.POST)

        if form.is_valid() and formset.is_valid():
            equipment_change = form.save()  # Save the main EquipmentChange object

            # Save each EquipmentParticulars instance in the formset
            particulars = formset.save(commit=False)
            for particular in particulars:
                particular.equipment_change = equipment_change  # Associate with the EquipmentChange
                particular.save()

            return redirect('EquipTracker:equipment_list')
        
        return render(request, self.template_name, {'equipment': form, 'formset': formset})

        