from django.views.generic import View, DetailView
from django.shortcuts import render, redirect
from django.forms import modelform_factory, inlineformset_factory
from django import forms
from django.db.models import Sum
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import  ToolsAndEquipmentForm, AssignedToolOrEquipment, ToolOrEquipment,DepotToolsAndEquipmentRegister
import pandas as pd
from django.core.management.base import BaseCommand
from .forms import *
import datetime

ToolsAndEquipmentFormForm = modelform_factory(ToolsAndEquipmentForm, exclude=["received_by", "issued_by", "issued_at"]) 
class ToolsAndEquipmentFormCreateView(LoginRequiredMixin, View):
    template_name = 'ToolsandEquipment/T&ERegister.html'
    def get(self, request):
        tes = ToolOrEquipment.objects.all()
        extra_forms = len(tes)
        ToolsAndEquipmentFormSet = inlineformset_factory(
            ToolsAndEquipmentRegister,
            ToolsAndEquipmentRegisterItem,
            form=ToolsAndEquipmentRegisterItemForm,
            fields=['tool_or_equipment', 'quantity', 'value', 'so_or_invoice_no', 'so_or_invoice_date', 'remarks'],
            extra=extra_forms,
            can_delete=False
        )
        form = ToolsAndEquipmentFormForm()
        # Prepare initial data for each form in the formset
        initial_data = [
            {'tool_or_equipment': tool.id,}
            for tool in tes
        ]
        formset = ToolsAndEquipmentFormSet(initial=initial_data)

        # compute issued quantities per tool so we can show remaining stock
        issued_qs = ToolsAndEquipmentRegisterItem.objects.values('tool_or_equipment').annotate(issued=Sum('quantity'))
        issued_map = {i['tool_or_equipment']: (i['issued'] or 0) for i in issued_qs}
        remaining_tools = []
        for tool in tes:
            total = tool.total_quantity or 0
            issued = issued_map.get(tool.pk, 0)
            remaining = total - issued
            if remaining < 0:
                remaining = 0
            remaining_tools.append({'tool': tool, 'remaining': remaining})

        # set per-form 'max' attribute for quantity inputs so browser enforces the limit
        remaining_map = {entry['tool'].pk: entry['remaining'] for entry in remaining_tools}
        for idx, f in enumerate(formset.forms):
            try:
                # try to find the tool id for this form from the initial data (falls back to same index in tes)
                tool_pk = initial_data[idx].get('tool_or_equipment') if idx < len(initial_data) else None
            except Exception:
                tool_pk = None
            if not tool_pk and idx < len(tes):
                tool_pk = tes[idx].pk
            try:
                max_val = remaining_map.get(int(tool_pk), 0)
            except Exception:
                max_val = 0
            if 'quantity' in f.fields:
                f.fields['quantity'].widget.attrs.update({'max': str(max_val), 'min': '0', 'type': 'number'})
            # set the remaining display field if present
            if 'remaining' in f.fields:
                try:
                    rem_val = remaining_map.get(int(tool_pk), 0)
                except Exception:
                    rem_val = 0
                f.fields['remaining'].initial = rem_val
                f.fields['remaining'].widget.attrs.update({'value': str(rem_val)})

        return render(request, self.template_name, {'form': form, 'formset': formset, 'remaining_tools': remaining_tools})


    def post(self, request):
        form = ToolsAndEquipmentFormForm(request.POST)
        extra_forms = int(request.GET.get('extra', 1))
        ToolsAndEquipmentFormSet = inlineformset_factory(
            ToolsAndEquipmentRegister,
            ToolsAndEquipmentRegisterItem,
            form=ToolsAndEquipmentRegisterItemForm,
            fields=['tool_or_equipment', 'quantity', 'value', 'so_or_invoice_no', 'so_or_invoice_date', 'remarks'],
            extra=extra_forms,
            can_delete=False
        )
        formset = ToolsAndEquipmentFormSet(request.POST)

        # recompute remaining_map so we can set max attrs and validate server-side
        issued_qs = ToolsAndEquipmentRegisterItem.objects.values('tool_or_equipment').annotate(issued=Sum('quantity'))
        issued_map = {i['tool_or_equipment']: (i['issued'] or 0) for i in issued_qs}
        remaining_map = {}
        for tool in tes:
            total = tool.total_quantity or 0
            issued = issued_map.get(tool.pk, 0)
            remaining = total - issued
            if remaining < 0:
                remaining = 0
            remaining_map[tool.pk] = remaining

        # set max attrs on bound forms so client sees limits on re-render
        for f in formset.forms:
            # form prefix field name for tool fk
            key = f"{f.prefix}-tool_or_equipment"
            tool_val = request.POST.get(key) or f.initial.get('tool_or_equipment')
            try:
                max_val = remaining_map.get(int(tool_val), 0)
            except Exception:
                max_val = 0
            if 'quantity' in f.fields:
                f.fields['quantity'].widget.attrs.update({'max': str(max_val), 'min': '0', 'type': 'number'})
            # set remaining display value on bound forms
            if 'remaining' in f.fields:
                try:
                    rem_val = remaining_map.get(int(tool_val), 0)
                except Exception:
                    rem_val = 0
                f.fields['remaining'].initial = rem_val
                f.fields['remaining'].widget.attrs.update({'value': str(rem_val)})

        # Validate parent form and formset, then enforce remaining stock limits server-side
        if form.is_valid() and formset.is_valid():
            # extra validation: ensure no form requests more than remaining stock
            exceeded = False
            for f in formset.forms:
                if not f.is_valid():
                    continue
                qty = f.cleaned_data.get('quantity')
                tool_obj = f.cleaned_data.get('tool_or_equipment')
                if tool_obj and qty is not None:
                    rem = remaining_map.get(tool_obj.pk, 0)
                    if qty > rem:
                        f.add_error('quantity', f"Requested quantity ({qty}) exceeds remaining stock ({rem}).")
                        exceeded = True
            if exceeded:
                # re-render with errors visible
                tes = ToolOrEquipment.objects.all()
                issued_qs = ToolsAndEquipmentRegisterItem.objects.values('tool_or_equipment').annotate(issued=Sum('quantity'))
                issued_map = {i['tool_or_equipment']: (i['issued'] or 0) for i in issued_qs}
                remaining_tools = []
                for tool in tes:
                    total = tool.total_quantity or 0
                    issued = issued_map.get(tool.pk, 0)
                    remaining = total - issued
                    if remaining < 0:
                        remaining = 0
                    remaining_tools.append({'tool': tool, 'remaining': remaining})
                return render(request, self.template_name, {'form': form, 'formset': formset, 'extra': extra_forms, 'remaining_tools': remaining_tools})

            tools_form = form.save(commit=False)
            tools_form.issued_by = request.user 
            tools_form.save()
            formset.instance = tools_form
            formset.save()
            return redirect('tools-and-equipment:tools-and-equipment-list')
        print(form.errors)
        print(formset.errors)
        # recompute remaining_tools for re-render so the template can still show them
        tes = ToolOrEquipment.objects.all()
        issued_qs = ToolsAndEquipmentRegisterItem.objects.values('tool_or_equipment').annotate(issued=Sum('quantity'))
        issued_map = {i['tool_or_equipment']: (i['issued'] or 0) for i in issued_qs}
        remaining_tools = []
        for tool in tes:
            total = tool.total_quantity or 0
            issued = issued_map.get(tool.pk, 0)
            remaining = total - issued
            if remaining < 0:
                remaining = 0
            remaining_tools.append({'tool': tool, 'remaining': remaining})

        return render(request, self.template_name, {'form': form, 'formset': formset, 'extra': extra_forms, 'remaining_tools': remaining_tools})

class ToolsAndEquipmentFormListView(LoginRequiredMixin, View):
    template_name = 'ToolsandEquipment/tools_and_equipment_form_list.html'
    
    def get(self, request):
        forms = ToolsAndEquipmentForm.objects.all().order_by('-issued_at')
        return render(request, self.template_name, {'teforms': forms})

class ToolsAndEquipmentDetailView(LoginRequiredMixin, DetailView):
    model = ToolsAndEquipmentForm
    template_name = 'ToolsandEquipment/tools_and_equipment_detail.html'
    context_object_name = 'teform'

    def get_queryset(self):
        return self.model.objects.all()  # Fetch all instances of the model

class DepotToolsAndEquipmentCreateView(LoginRequiredMixin, View):
    template_name = 'ToolsandEquipment/depot_T&ERegister.html'

    def get_depot_queryset(self, cc):
        """Fetch the depot queryset based on the user's cost center."""
        try:
            depots = cc.get_region().get_decendance()
        except Exception:
            try:
                depots = cc.get_decendance()
            except Exception:
                depots = []
        
        if depots:
            try:
                return depots.filter(name__icontains='Depot')
            except Exception:
                pks = [c.pk for c in depots if getattr(c, 'name', None) and 'Depot' in c.name]
                from it.users.models import CostCenter
                return CostCenter.objects.filter(pk__in=pks) if pks else CostCenter.objects.none()

        return CostCenter.objects.filter(name__icontains='Depot')

    def get(self, request):
        DepotForm = modelform_factory(DepotToolsAndEquipmentRegister, fields=['depot'])
        cc = getattr(request.user, 'cost_center', None)
        depot_qs = self.get_depot_queryset(cc)

        form = DepotForm()
        form.fields['depot'] = forms.ModelChoiceField(
            queryset=depot_qs,
            required=False,
            widget=forms.Select(attrs={'class': 'select2'})
        )
        
        DepotToolFormSet = inlineformset_factory(
            DepotToolsAndEquipmentRegister,
            ToolOrEquipment,
            form=ToolOrEquipmentForm,
            fields=['name', 'total_quantity', 'value', 'so_or_invoice_no', 'so_or_invoice_date', 'asset_number'],
            extra=5,
            can_delete=False
        )
        formset = DepotToolFormSet()
        return render(request, self.template_name, {'form': form, 'formset': formset})

    def post(self, request):
        DepotForm = modelform_factory(DepotToolsAndEquipmentRegister, fields=['depot'])
        DepotToolFormSet = inlineformset_factory(
            DepotToolsAndEquipmentRegister,
            ToolOrEquipment,
            form=ToolOrEquipmentForm,
            fields=['name', 'total_quantity', 'value', 'so_or_invoice_no', 'so_or_invoice_date', 'asset_number'],
            extra=5,
            can_delete=False
        )
        form = DepotForm(request.POST)
        cc = getattr(request.user, 'cost_center', None)
        depot_qs = self.get_depot_queryset(cc)
        form.fields['depot'] = forms.ModelChoiceField(queryset=depot_qs, required=False, widget=forms.Select(attrs={'class': 'select2'}))
        formset = DepotToolFormSet(request.POST)

        if form.is_valid():
            depot_register = form.save(commit=False)
            depot_register.created_by = request.user
            depot_register.save()

            # Save valid instances
            for form_instance in formset:
                if form_instance.is_valid() and form_instance.cleaned_data.get('name'):
                    tool_or_equipment_instance = form_instance.save(commit=False)
                    tool_or_equipment_instance.depot_register = depot_register
                    tool_or_equipment_instance.save()

            return redirect('tools-and-equipment:tools-and-equipment-list')

        return render(request, self.template_name, {'form': form, 'formset': formset})

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
