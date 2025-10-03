# views.py

import os
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import DetailView, ListView
from .models import TrackEquipment, EquipmentChange 
from .forms import TrackEquipmentForm, EquipmentChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin

class EquipmentListView(LoginRequiredMixin, ListView):
    model = TrackEquipment
    template_name = 'equipment/equipment_list.html'
    context_object_name = 'equipments'
    paginate_by = 10
    ordering = ['-id']

    def get_queryset(self):
        user_region_id = self.request.user.region.id
        equipment_ids = EquipmentChange.objects.filter(substation__region_id=user_region_id).values_list('equipment_tracker_id', flat=True)
        for a in equipment_ids: print("qqqqqqqqq",a)
        return TrackEquipment.objects.filter(id__in=equipment_ids, type_of_equipment='Battery').order_by('-id')
        

class EquipmentDetailView(LoginRequiredMixin, DetailView):
    model = TrackEquipment
    template_name = 'equipment/equipment_tracker.html'
    context_object_name = 'equipment'

    def get_object(self, queryset=None):
        obj = super().get_object(queryset)
        return obj
class EquipmentChangeView(LoginRequiredMixin, View):
    template_name = 'equipment/equipment_change.html'

    def get(self, request):
        form = EquipmentChangeForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = EquipmentChangeForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('EquipTracker:equipment_list')
        return render(request, self.template_name, {'form': form})