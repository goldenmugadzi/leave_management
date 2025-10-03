from django.views.generic import View, DetailView
from django.shortcuts import render, redirect
from django.forms import modelform_factory, inlineformset_factory
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import  *
import pandas as pd
from django.core.management.base import BaseCommand
from .forms import *

ToolsAndEquipmentForm= modelform_factory(ToolOrEquipment, exclude=["received_by", "issued_by", "issued_at"]) 
class ToolsAndEquipmentFormCreateView(LoginRequiredMixin, View):
    template_name = 'ToolsandEquipment/T&ERegister.html'
    
    def get(self, request):
        tes = ToolOrEquipment.objects.all()
        extra_forms = len(tes)
        ToolsAndEquipmentFormSet = inlineformset_factory(
            ToolsAndEquipmentRegister,
            ToolsAndEquipmentRegisterItem,
            form=ToolsAndEquipmentRegisterItemForm,
            fields=['tool_or_equipment', 'quantity', 'value', 'so_or_invoice_no', 'so_or_invoice_date', 'initials', 'remarks'],
            extra=extra_forms,
            can_delete=False
        )
        form = ToolsAndEquipmentRegisterForm(user=request.user)
        initial_data = [{'tool_or_equipment': tool.id,} for tool in tes]
        formset = ToolsAndEquipmentFormSet(initial=initial_data)
        return render(request, self.template_name, {'form': form, 'formset': formset})


    def post(self, request):
        form = ToolsAndEquipmentRegisterForm(request.POST)
        tes = ToolOrEquipment.objects.all()
        extra_forms = len(tes)
        ToolsAndEquipmentFormSet = inlineformset_factory(
            ToolsAndEquipmentRegister,
            ToolsAndEquipmentRegisterItem,
            form=ToolsAndEquipmentRegisterItemForm,
            fields=['tool_or_equipment', 'quantity', 'value', 'so_or_invoice_no', 'so_or_invoice_date', 'initials', 'remarks'],
            extra=extra_forms,
            can_delete=False
        )
        formset = ToolsAndEquipmentFormSet(request.POST)
        if form.is_valid() and formset.is_valid():
            tools_form = form.save(commit=False)
            tools_form.issued_by = request.user 
            tools_form.save()
            formset.instance = tools_form
            formset.save()
            return redirect('tools-and-equipment-list')
        print(form.errors)
        print(formset.errors)
        return render(request, self.template_name, {'form': form, 'formset': formset, 'extra': extra_forms})
    
class ToolsAndEquipmentFormListView(LoginRequiredMixin, View):
    template_name = 'ToolsandEquipment/tools_and_equipment_form_list.html'
    def get(self, request):
        forms = ToolsAndEquipmentRegister.objects.all().order_by('-date_issued')
        return render(request, self.template_name, {'teforms': forms})

class ToolsAndEquipmentDetailView(LoginRequiredMixin, DetailView):
    model = ToolsAndEquipmentRegister  # Ensure this is the correct model
    template_name = 'ToolsandEquipment/tools_and_equipment_detail.html'  # Adjust the template path as needed
    context_object_name = 'register'  # This is the name that will be used in the template to refer to the object

    def get_queryset(self):
        return self.model.objects.all()  # Fetch all instances of the model
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
