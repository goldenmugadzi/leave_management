from django import forms
from django.core.exceptions import ValidationError
from .models import (
    Customer, Contractor, ApplicationAttachment, ClientApplication, 
    InspectionReport, E6Certificate, E1DefectReport, InspectionWorkflow, 
    ApplicationAssignment
)


class CustomerForm(forms.ModelForm):
    """Form for creating and editing customers"""
    
    class Meta:
        model = Customer
        fields = [
            'full_name', 'phone', 'email', 'stand_plot_number', 
            'farm_street_name', 'suburb_township', 'district'
        ]
        
        widgets = {
            'full_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'Enter full name'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': '+263 xxx xxx xxx'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'customer@example.com'
            }),
            'stand_plot_number': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'Stand/Plot Number'
            }),
            'farm_street_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'Farm/Street Name'
            }),
            'suburb_township': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'Suburb/Township'
            }),
            'district': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'District'
            }),
        }


class ContractorForm(forms.ModelForm):
    """Form for creating and editing contractors"""
    
    class Meta:
        model = Contractor
        fields = [
            'business_name', 'contact_person', 'phone', 'email', 
            'address', 'city', 'district', 'license_number', 'business_registration'
        ]
        
        widgets = {
            'business_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'Business Name'
            }),
            'contact_person': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'Contact Person'
            }),
            'phone': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': '+263 xxx xxx xxx'
            }),
            'email': forms.EmailInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'contractor@example.com'
            }),
            'address': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'placeholder': 'Business Address'
            }),
            'city': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'City'
            }),
            'district': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'District'
            }),
            'license_number': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'License Number'
            }),
            'business_registration': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'Business Registration Number'
            }),
        }


class ApplicationAttachmentForm(forms.ModelForm):
    """Form for uploading application attachments"""
    
    class Meta:
        model = ApplicationAttachment
        fields = ['file', 'file_type', 'description']
        
        widgets = {
            'file': forms.FileInput(attrs={
                'class': 'block w-full text-sm text-gray-500 file:mr-4 file:py-2 file:px-4 file:rounded-full file:border-0 file:text-sm file:font-semibold file:bg-gulf-blue-50 file:text-gulf-blue-700 hover:file:bg-gulf-blue-100'
            }),
            'file_type': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'description': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'Brief description of the document'
            }),
        }


class ClientApplicationForm(forms.ModelForm):
    """Enhanced form for creating and editing client applications"""
    
    class Meta:
        model = ClientApplication
        fields = [
            'application_type', 'customer', 'owner_name', 'owner_address',
            'contractor', 'purpose', 'supply_type', 
            'single_phase_required', 'single_phase_count', 'three_phase_required', 
            'three_phase_count', 'service_feed_type', 'main_switch_size_amperes', 
            'main_switch_size_kva', 'notes'
        ]
        
        widgets = {
            'application_type': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'priority': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'customer': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'owner_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'placeholder': 'Property owner name (if different from applicant)'
            }),
            'owner_address': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'placeholder': 'Property owner address'
            }),
            'contractor': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'purpose': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'supply_type': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'roof_covering': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'single_phase_required': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-gulf-blue-600 focus:ring-gulf-blue-500 border-gray-300 rounded'
            }),
            'single_phase_count': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'min': '0'
            }),
            'three_phase_required': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-gulf-blue-600 focus:ring-gulf-blue-500 border-gray-300 rounded'
            }),
            'three_phase_count': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'min': '0'
            }),
            'service_feed_type': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'main_switch_size_amperes': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'min': '0', 'placeholder': 'Amperes'
            }),
            'main_switch_size_kva': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'min': '0', 'step': '0.01', 'placeholder': 'KVA'
            }),
            'notes': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'placeholder': 'Additional notes'
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Set empty choices for customer and contractor if they don't exist
        if not Customer.objects.exists():
            self.fields['customer'].choices = [('', 'No customers available')]
        if not Contractor.objects.exists():
            self.fields['contractor'].choices = [('', 'No contractors available')]


class InspectionReportForm(forms.ModelForm):
    """Form for viewing inspection reports (read-only for web interface)"""
    
    class Meta:
        model = InspectionReport
        fields = '__all__'
        
        widgets = {
            'inspection_date': forms.DateInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'type': 'date', 'readonly': 'readonly'
            }),
            'service_no': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'reason_for_inspection': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'consumer_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'property_supplied': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 2, 'readonly': 'readonly'
            }),
            'property_owner_name': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'property_owner_address': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'contractor': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'contractor_address': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'size_of_mains': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'size_of_mains_conduit': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'consumer_main_switch_type': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'consumer_main_switch_capacity': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'consumer_main_switch_setting': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'neutrals_fused': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'neutral_block_fitted': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'earth_electrode_installed': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'earth_electrode_type': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'all_equipment_bonded_earthed': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'insulation_resistance_between': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'insulation_resistance_to_earth': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'earth_continuity_resistance': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'polarity_switches_plugs': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'socket_outlets_earthed': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'socket_outlet_type': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'wiring_type': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'circuit_conductors_correct_size': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'wiring_condition': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'flexible_cord_prohibited_positions': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'bathroom_switch_accessible': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'unearthed_metal_switches': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'conduits_bushed': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'conduits_bonded_earth': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'conduits_correct_size': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'conduits_adequately_supported': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'conduits_suitable_type': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'max_lighting_points_per_circuit': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'max_plug_points_per_circuit': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'total_lighting_points': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'total_plug_points': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'appliances_wattages': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'motors_plant_details': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'overhead_lines_height': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'overhead_lines_conductor_size': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'overhead_lines_support': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'overhead_lines_general': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'overhead_earthwires_fitted': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'overhead_lines_protected': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'outbuildings_protected': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'motor_installations_protected': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'commission_switch_details': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'supply_connected_disconnected': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'contractor_notified_defects': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'other_features_attention': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'status': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'client_application': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'inspector': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
        }


class E6CertificateForm(forms.ModelForm):
    """Form for viewing E6 certificates (read-only for web interface)"""
    
    class Meta:
        model = E6Certificate
        fields = '__all__'
        
        widgets = {
            'certificate_number': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'service_no': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'installation_description': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 4, 'readonly': 'readonly'
            }),
            'property_address': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'property_owner_occupant': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'minor_defects': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 4, 'readonly': 'readonly'
            }),
            'defects_rectification_period': forms.NumberInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'sent_to_client': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-gulf-blue-600 focus:ring-gulf-blue-500 border-gray-300 rounded', 
                'disabled': 'disabled'
            }),
            'sent_date': forms.DateTimeInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'type': 'datetime-local', 'readonly': 'readonly'
            }),
            'delivery_method': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'inspection_report': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'client_application': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'installation_inspector': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
        }


class E1DefectReportForm(forms.ModelForm):
    """Form for viewing E1 defect reports (read-only for web interface)"""
    
    class Meta:
        model = E1DefectReport
        fields = '__all__'
        
        widgets = {
            'report_number': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'service_no': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'property_address': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 3, 'readonly': 'readonly'
            }),
            'sub_division_number': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'defects_list': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 6, 'readonly': 'readonly'
            }),
            'defects_requiring_attention': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 6, 'readonly': 'readonly'
            }),
            'sent_to_consumer': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-gulf-blue-600 focus:ring-gulf-blue-500 border-gray-300 rounded', 
                'disabled': 'disabled'
            }),
            'sent_to_contractor': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-gulf-blue-600 focus:ring-gulf-blue-500 border-gray-300 rounded', 
                'disabled': 'disabled'
            }),
            'sent_to_district_manager': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-gulf-blue-600 focus:ring-gulf-blue-500 border-gray-300 rounded', 
                'disabled': 'disabled'
            }),
            'sent_to_depot_official': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-gulf-blue-600 focus:ring-gulf-blue-500 border-gray-300 rounded', 
                'disabled': 'disabled'
            }),
            'sent_date': forms.DateTimeInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'type': 'datetime-local', 'readonly': 'readonly'
            }),
            'delivery_method': forms.TextInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'readonly': 'readonly'
            }),
            'is_reinspection': forms.CheckboxInput(attrs={
                'class': 'h-4 w-4 text-gulf-blue-600 focus:ring-gulf-blue-500 border-gray-300 rounded', 
                'disabled': 'disabled'
            }),
            'original_report': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'inspection_report': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'client_application': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
            'installation_inspector': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2', 
                'disabled': 'disabled'
            }),
        }


class ApplicationAssignmentForm(forms.ModelForm):
    """Form for assigning applications to field officers"""
    
    class Meta:
        model = ApplicationAssignment
        fields = ['application', 'assigned_to', 'due_date', 'assignment_notes']
        
        widgets = {
            'application': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'assigned_to': forms.Select(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
            }),
            'due_date': forms.DateTimeInput(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'type': 'datetime-local'
            }),
            'assignment_notes': forms.Textarea(attrs={
                'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
                'rows': 4
            }),
        }

    def __init__(self, *args, **kwargs):
        application_id = kwargs.pop('application_id', None)
        super().__init__(*args, **kwargs)
        # Filter applications to only show submitted ones
        self.fields['application'].queryset = ClientApplication.objects.filter(status='submitted')
        
        # Pre-populate application if provided
        if application_id:
            self.fields['application'].initial = application_id
        
        # Filter users to show only active ones
        from django.contrib.auth import get_user_model
        User = get_user_model()
        self.fields['assigned_to'].queryset = User.objects.filter(is_active=True)


class InspectionSearchForm(forms.Form):
    """Form for searching and filtering inspections"""
    
    search_query = forms.CharField(
        required=False,
        widget=forms.TextInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
            'placeholder': 'Search applications, customers, service numbers...'
        })
    )
    
    application_type = forms.ChoiceField(
        choices=[('', 'All Types')] + ClientApplication.APPLICATION_TYPE_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
        })
    )
    
    status = forms.ChoiceField(
        choices=[('', 'All Statuses')] + ClientApplication.STATUS_CHOICES,
        required=False,
        widget=forms.Select(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm p-2'
        })
    )
    
    date_from = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
            'type': 'date'
        })
    )
    
    date_to = forms.DateField(
        required=False,
        widget=forms.DateInput(attrs={
            'class': 'block w-full rounded-md border-gray-300 shadow-sm focus:border-gulf-blue-500 focus:ring-gulf-blue-500 sm:text-sm', 
            'type': 'date'
        })
    ) 