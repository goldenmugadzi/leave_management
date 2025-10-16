from django import forms
from crispy_forms.helper import FormHelper
from crispy_forms.layout import Layout, Fieldset, Row, Column, Submit, HTML
from crispy_forms.bootstrap import TabHolder, Tab
from .models import (
    E60InspectionReport,
    E60TransformerInspection,
    E60CircuitBreakerInspection,
    E60MeteringInspection,
    E60HousingInspection,
    E60FuseInspection,
    E60SurgeArrestorInspection,
    E60GeneralStateInspection,
    E60SafetyInspection,
    E60ConsumerInstallationInspection,
)


class E60InspectionReportForm(forms.ModelForm):
    """Main form for E60 inspection report header information"""
    
    class Meta:
        model = E60InspectionReport
        fields = [
            'substation_name', 'service_number', 'section', 'construction_type',
            'inspection_date', 'inspection_type', 'general_condition', 'remarks'
        ]
        
        widgets = {
            'inspection_date': forms.DateInput(attrs={
                'class': 'form-control',
                'type': 'date'
            }),
            'general_condition': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 3,
                'placeholder': 'Overall general condition assessment...'
            }),
            'remarks': forms.Textarea(attrs={
                'class': 'form-control',
                'rows': 4,
                'placeholder': 'Additional remarks and observations...'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Header Information',
                Row(
                    Column('substation_name', css_class='form-group col-md-6 mb-0'),
                    Column('service_number', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('section', css_class='form-group col-md-6 mb-0'),
                    Column('construction_type', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('inspection_date', css_class='form-group col-md-6 mb-0'),
                    Column('inspection_type', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            ),
            Fieldset(
                'Overall Assessment',
                'general_condition',
                'remarks',
            ),
        )


class E60TransformerInspectionForm(forms.ModelForm):
    """Form for Section A: TRANSFORMERS inspection data"""
    
    class Meta:
        model = E60TransformerInspection
        fields = [
            'make', 'kva_rating', 'voltage_ratio', 'serial_number', 'security_mounting',
            # 'tank_bonded_to_earth', 
            'lt_neutral_bonded_to_earth', 'bushings_condition',
            'paintwork_condition', 'arcing_horn_gap_setting', 'breather_type',
            'breather_condition', 'oil_condition', 'oil_leaks', 'megger_hv_lv',
            'megger_hv_e', 'megger_lv_e', 'oil_test_results', 'tap_range',
            'tap_position_found', 'tap_position_left'
        ]
        
        widgets = {
            'voltage_ratio': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 11/0.4'
            }),
            'arcing_horn_gap_setting': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 95mm'
            }),
            'tap_range': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 1-5'
            }),
            'oil_test_results': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'Test results details'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Section A: TRANSFORMERS',
                Row(
                    Column('make', css_class='form-group col-md-6 mb-0'),
                    Column('kva_rating', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('voltage_ratio', css_class='form-group col-md-6 mb-0'),
                    Column('serial_number', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('security_mounting', css_class='form-group col-md-6 mb-0'),
                    Column('arcing_horn_gap_setting', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h5 class="mt-3">Bonding and Earthing</h5>'),
                Row(
                    # Column('tank_bonded_to_earth', css_class='form-group col-md-6 mb-0'),
                    Column('lt_neutral_bonded_to_earth', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h5 class="mt-3">Condition Assessment</h5>'),
                Row(
                    Column('bushings_condition', css_class='form-group col-md-6 mb-0'),
                    Column('paintwork_condition', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('breather_type', css_class='form-group col-md-6 mb-0'),
                    Column('breather_condition', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('oil_condition', css_class='form-group col-md-6 mb-0'),
                    Column('oil_leaks', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h5 class="mt-3">Test Results</h5>'),
                Row(
                    Column('megger_hv_lv', css_class='form-group col-md-4 mb-0'),
                    Column('megger_hv_e', css_class='form-group col-md-4 mb-0'),
                    Column('megger_lv_e', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
                'oil_test_results',
                HTML('<h5 class="mt-3">Tap Settings</h5>'),
                Row(
                    Column('tap_range', css_class='form-group col-md-4 mb-0'),
                    Column('tap_position_found', css_class='form-group col-md-4 mb-0'),
                    Column('tap_position_left', css_class='form-group col-md-4 mb-0'),
                    css_class='form-row'
                ),
            )
        )


class E60CircuitBreakerInspectionForm(forms.ModelForm):
    """Form for Section B: A.C.B or O.C.B inspection data"""
    
    class Meta:
        model = E60CircuitBreakerInspection
        fields = [
            'make', 'breaker_type', 'zesa_number', 'current_rating', 'voltage_rating',
            'trip_setting', 'consumer_trip_setting', 'oil_condition', 'contacts_condition',
            'nuts_connections_tight'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Section B: A.C.B or O.C.B',
                Row(
                    Column('make', css_class='form-group col-md-6 mb-0'),
                    Column('breaker_type', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('zesa_number', css_class='form-group col-md-6 mb-0'),
                    Column('current_rating', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('voltage_rating', css_class='form-group col-md-6 mb-0'),
                    Column('trip_setting', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('consumer_trip_setting', css_class='form-group col-md-6 mb-0'),
                    Column('nuts_connections_tight', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h5 class="mt-3">Condition Assessment</h5>'),
                Row(
                    Column('oil_condition', css_class='form-group col-md-6 mb-0'),
                    Column('contacts_condition', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            )
        )


class E60MeteringInspectionForm(forms.ModelForm):
    """Form for Section C: METERING inspection data"""
    
    class Meta:
        model = E60MeteringInspection
        fields = [
            'make', 'current_rating', 'voltage_rating', 'meter_type', 'serial_number',
            'zesa_number', 'vad_number', 'ct_ratio', 'vt_ratio', 'meter_protection_type',
            'meter_case_earthed', 'potential_condition', 'phase_rotation', 'connections_tight',
            'equipment_fully_sealed', 'meter_reading_card_available'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Section C: METERING',
                Row(
                    Column('make', css_class='form-group col-md-6 mb-0'),
                    Column('meter_type', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('current_rating', css_class='form-group col-md-6 mb-0'),
                    Column('voltage_rating', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('serial_number', css_class='form-group col-md-6 mb-0'),
                    Column('zesa_number', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('vad_number', css_class='form-group col-md-6 mb-0'),
                    Column('meter_protection_type', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h5 class="mt-3">Ratios and Settings</h5>'),
                Row(
                    Column('ct_ratio', css_class='form-group col-md-6 mb-0'),
                    Column('vt_ratio', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h5 class="mt-3">Condition and Checks</h5>'),
                Row(
                    Column('meter_case_earthed', css_class='form-group col-md-6 mb-0'),
                    Column('potential_condition', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('phase_rotation', css_class='form-group col-md-6 mb-0'),
                    Column('connections_tight', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('equipment_fully_sealed', css_class='form-group col-md-6 mb-0'),
                    Column('meter_reading_card_available', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            )
        )


class E60HousingInspectionForm(forms.ModelForm):
    """Form for Section D: METER/SWITCHGEAR HOUSING inspection data"""
    
    class Meta:
        model = E60HousingInspection
        fields = [
            'housing_type', 'weatherproof', 'door_fitted', 'paintwork_condition',
            'water_outlet_in_conduit', 'door_fitted_with_lock', 'lock_lubricated'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Section D: METER/SWITCHGEAR HOUSING',
                Row(
                    Column('housing_type', css_class='form-group col-md-6 mb-0'),
                    Column('paintwork_condition', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('weatherproof', css_class='form-group col-md-6 mb-0'),
                    Column('door_fitted', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('water_outlet_in_conduit', css_class='form-group col-md-6 mb-0'),
                    Column('door_fitted_with_lock', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'lock_lubricated',
            )
        )


class E60FuseInspectionForm(forms.ModelForm):
    """Form for Section E: 'D' FUSES inspection data"""
    
    class Meta:
        model = E60FuseInspection
        fields = [
            'rating_and_type', 'gauze_washers_fitted', 'holders_drop_freely',
            'holders_make_good_contact', 'contacts_treated_with_anti_scuffing_paste'
        ]
        
        widgets = {
            'rating_and_type': forms.TextInput(attrs={
                'class': 'form-control',
                'placeholder': 'e.g., 31.5A'
            }),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Section E: \'D\' FUSES',
                'rating_and_type',
                Row(
                    Column('gauze_washers_fitted', css_class='form-group col-md-6 mb-0'),
                    Column('holders_drop_freely', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('holders_make_good_contact', css_class='form-group col-md-6 mb-0'),
                    Column('contacts_treated_with_anti_scuffing_paste', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            )
        )


class E60SurgeArrestorInspectionForm(forms.ModelForm):
    """Form for Sections F & G: HV and LV SURGE ARRESTORS inspection data"""
    
    class Meta:
        model = E60SurgeArrestorInspection
        fields = [
            'arrestor_type', 'make_and_type', 'voltage_rating', 'current_rating', 'capacity_satisfactory'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Sections F & G: SURGE ARRESTORS',
                Row(
                    Column('arrestor_type', css_class='form-group col-md-6 mb-0'),
                    Column('make_and_type', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('voltage_rating', css_class='form-group col-md-6 mb-0'),
                    Column('current_rating', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                'capacity_satisfactory',
            )
        )


class E60GeneralStateInspectionForm(forms.ModelForm):
    """Form for Section J: SUBSTATION GENERAL STATE inspection data"""
    
    class Meta:
        model = E60GeneralStateInspection
        fields = [
            'total_earth_resistance', 'number_of_earth_electrodes', 'structures_bonded_to_earth',
            'lv_cable_sheath_bonded_to_earth', 'lv_mains_condition', 'lv_mains_type_and_length',
            'poles_condition', 'paintwork_condition', 'site_clear_of_undergrowth', 'site_accessible_by_vehicle'
        ]
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Section J: SUBSTATION GENERAL STATE',
                HTML('<h5 class="mt-3">Earth Resistance and Bonding</h5>'),
                Row(
                    Column('total_earth_resistance', css_class='form-group col-md-6 mb-0'),
                    Column('number_of_earth_electrodes', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                Row(
                    Column('structures_bonded_to_earth', css_class='form-group col-md-6 mb-0'),
                    Column('lv_cable_sheath_bonded_to_earth', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h5 class="mt-3">LV Mains and Infrastructure</h5>'),
                Row(
                    Column('lv_mains_condition', css_class='form-group col-md-6 mb-0'),
                    Column('lv_mains_type_and_length', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h5 class="mt-3">Poles and Paintwork</h5>'),
                Row(
                    Column('poles_condition', css_class='form-group col-md-6 mb-0'),
                    Column('paintwork_condition', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
                HTML('<h5 class="mt-3">Site Conditions</h5>'),
                Row(
                    Column('site_clear_of_undergrowth', css_class='form-group col-md-6 mb-0'),
                    Column('site_accessible_by_vehicle', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            )
        )


class E60SafetyInspectionForm(forms.ModelForm):
    """Form for Section K: SAFETY PRECAUTIONS inspection data"""
    
    class Meta:
        model = E60SafetyInspection
        fields = ['danger_plates_fitted', 'anti_climb_fitted']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Section K: SAFETY PRECAUTIONS',
                Row(
                    Column('danger_plates_fitted', css_class='form-group col-md-6 mb-0'),
                    Column('anti_climb_fitted', css_class='form-group col-md-6 mb-0'),
                    css_class='form-row'
                ),
            )
        )


class E60ConsumerInstallationInspectionForm(forms.ModelForm):
    """Form for Section L: CONSUMER'S INSTALLATION inspection data"""
    
    class Meta:
        model = E60ConsumerInstallationInspection
        fields = ['general_condition']
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.helper = FormHelper()
        self.helper.layout = Layout(
            Fieldset(
                'Section L: CONSUMER\'S INSTALLATION',
                'general_condition',
            )
        )
