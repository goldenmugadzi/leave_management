from django.views.generic import View, DetailView
from django.shortcuts import render, redirect
from django.forms import modelform_factory, inlineformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import  ToolsAndEquipmentForm, AssignedToolOrEquipment, ToolOrEquipment
import pandas as pd
from django.core.management.base import BaseCommand

ToolsAndEquipmentFormForm = modelform_factory(ToolsAndEquipmentForm, exclude=["received_by", "issued_by", "issued_at"]) 
class ToolsAndEquipmentFormCreateView(LoginRequiredMixin, View):
    template_name = 'ToolsandEquipment/instruction_form_create.html'
    
    def get(self, request):
        tes = ToolOrEquipment.objects.all()
        extra_forms = len(tes)
        ToolsAndEquipmentFormSet = inlineformset_factory(
            ToolsAndEquipmentForm, AssignedToolOrEquipment,
            fields=['tool_or_equipment', 'quantity', 'remarks'],
            extra=extra_forms, can_delete=False
        )
        form = ToolsAndEquipmentFormForm()
        # Prepare initial data for each form in the formset
        initial_data = [
            {'tool_or_equipment': tool.id,}
            for tool in tes
        ]
        formset = ToolsAndEquipmentFormSet(initial=initial_data)
        for f in formset.forms:
            f.fields['tool_or_equipment'].queryset = tes
            for field in f.fields.values():
                field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
        for name, field in form.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if name in ["artisan"]:
                field.widget.attrs.update({'class': "select2"})
        return render(request, self.template_name, {'form': form, 'formset': formset})


    def post(self, request):
        form = ToolsAndEquipmentFormForm(request.POST)
        extra_forms = int(request.GET.get('extra', 1))
        ToolsAndEquipmentFormSet = inlineformset_factory(
            ToolsAndEquipmentForm, AssignedToolOrEquipment,
            fields=['tool_or_equipment', 'quantity', 'remarks'],  # Only fields on AssignedToolOrEquipment
            extra=extra_forms, can_delete=False
        )   
        formset = ToolsAndEquipmentFormSet(request.POST)
        for field in form.fields.values():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
        for f in formset.forms:
            for field in f.fields.values():
               field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
        if form.is_valid() and formset.is_valid():
            tools_form = form.save(commit=False)
            tools_form.issued_by = request.user 
            tools_form.save()
            formset.instance = tools_form
            formset.save()
            return redirect('tools-and-equipment-list')
        return render(request, self.template_name, {'form': form, 'formset': formset, 'extra': extra_forms})
    
class ToolsAndEquipmentFormListView(LoginRequiredMixin, View):
    template_name = 'ToolsandEquipment/tools_and_equipment_form_list.html'
    
    def get(self, request):
        forms = ToolsAndEquipmentForm.objects.all().order_by('-issued_at')
        return render(request, self.template_name, {'teforms': forms})

class ToolsAndEquipmentDetailView(LoginRequiredMixin, DetailView):
    model = ToolsAndEquipmentForm
    template_name = 'ToolsandEquipment/tools_and_equipment_detail.html'
    context_object_name = 'teform'

class Command(BaseCommand):
    help = 'Upload tools from TOOLS.xls into the ToolOrEquipment model'

    def add_arguments(self, parser):
        parser.add_argument('filepath', type=str, help='Path to TOOLS.xls file')

    def handle(self, *args, **kwargs):
        filepath = kwargs['filepath']
        df = pd.read_excel(filepath)

        for index, row in df.iterrows():
            try:
               
                tool = ToolOrEquipment(
                    id=str(row['id']),
                    name=row['name'],
                    quantity=int(row['quantity']),
                    value=row['value'] if pd.notna(row['value']) else None,
                    asset_number=row['asset_number'] if pd.notna(row['asset_number']) else None
                )
                tool.save()
                self.stdout.write(self.style.SUCCESS(f"Added tool: {tool.name}"))

            except Exception as e:
                self.stderr.write(self.style.ERROR(f"Error adding row {index + 2}: {e}"))
