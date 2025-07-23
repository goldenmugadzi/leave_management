from django.views.generic import View
from django.shortcuts import render, redirect
from django.forms import modelform_factory, inlineformset_factory
from django import forms
from django.contrib.auth.mixins import LoginRequiredMixin
from .models import ControllersInstructionForm, Instruction

ControllersInstructionFormForm = modelform_factory(ControllersInstructionForm, exclude=["received_by", "issued_by", "issued_at"])

class ControllersInstructionFormCreateView(LoginRequiredMixin, View):
    template_name = 'safety/instruction_form.html'
    def get(self, request):
        extra_forms = int(request.GET.get('extra', 1))
        InstructionFormSet = inlineformset_factory(
            ControllersInstructionForm, Instruction,
            fields=['instruction',],
            extra=extra_forms, can_delete=False
        )
        form = ControllersInstructionFormForm()
        formset = InstructionFormSet()
        # Add CSS classes to form fields
        for name, field in form.fields.items():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
            if name in ['district_station', 'issued_by', 'received_by']:
                field.widget.attrs.update({'class': "select2"})
        for f in formset.forms:
            for field in f.fields.values():
               field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
               if isinstance(field.widget, forms.Textarea):
                  field.widget.attrs.update({'rows': '3'})
        
        return render(request, self.template_name, {'form': form, 'formset': formset, 'extra': extra_forms})
    def post(self, request):
        extra_forms = int(request.GET.get('extra', 1))
        InstructionFormSet = inlineformset_factory(
            ControllersInstructionForm, Instruction,
            fields=['instruction', 'received', 'completed'],
            extra=extra_forms, can_delete=False
        )
        form = ControllersInstructionFormForm(request.POST)
        formset = InstructionFormSet(request.POST)
        # Add CSS classes to form fields
        for field in form.fields.values():
            field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
        for f in formset.forms:
            for field in f.fields.values():
               field.widget.attrs.update({'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",})
               if isinstance(field.widget, forms.Textarea):
                  field.widget.attrs.update({'rows': '3'})
        if form.is_valid() and formset.is_valid():
            instruction_form = form.save(commit=False)
            instruction_form.issued_by = request.user 
            instruction_form.save() 
            formset.instance = instruction_form
            formset.save()
            return redirect('instruction-form-list')  # Change as needed
        return render(request, self.template_name, {'form': form, 'formset': formset, 'extra': extra_forms})
    
class ControllersInstructionFormListView(LoginRequiredMixin, View):
    template_name = 'safety/instruction_form_list.html'
    
    def get(self, request):
        forms = ControllersInstructionForm.objects.all().order_by('-issued_at')
        return render(request, self.template_name, {'cinstructions': forms})
