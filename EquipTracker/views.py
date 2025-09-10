# views.py

import os
from django.shortcuts import render, redirect
from django.views import View
from django.views.generic import DetailView, ListView
from .models import TrackEquipment
from .forms import TrackEquipmentForm, EquipmentChangeForm
from django.contrib.auth.mixins import LoginRequiredMixin

class EquipmentListView(LoginRequiredMixin, ListView):
    model = TrackEquipment
    template_name = 'equipment/equipment_list.html'
    context_object_name = 'equipments'
    paginate_by = 10
    ordering = ['-date']
    def get_queryset(self):
        user_region_id = self.request.user.region.id
        return TrackEquipment.objects.filter(equipmentchange__substation__region_id=user_region_id).order_by('-id').distinct()
        
class TrackEquipmentView(LoginRequiredMixin, View):
    template_name = 'equipment/equipment_tracker.html'

    def get(self, request):
        form = TrackEquipmentForm()
        return render(request, self.template_name, {'form': form})

    def post(self, request):
        form = TrackEquipmentForm(request.POST)
        if form.is_valid():
            form.save()
            return redirect('EquipTracker:equipment_list')
        return render(request, self.template_name, {'form': form})
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