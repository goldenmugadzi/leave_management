from django import forms
from Asset_Register.models import ZetdcAssets, HumanResource, ProductType, UserProfile, Designations, CostCenter, Sections, Regions

class CombinedAssetForm(forms.ModelForm):
    class Meta:
        model = ZetdcAssets
        fields = [
            'product_type', 'asset_state', 'asset_number', 'serial_number', 'user',
            'department', 'regions', 'designation', 'cost_center', 'model',
            'date_purchased', 'supplier', 'warrant'
        ]

    # Common fields
    assetnumber = forms.CharField(required=False, label="Asset Number")
    asset_state = forms.ChoiceField(choices=ZetdcAssets._meta.get_field('asset_state').choices, required=False, label="Asset State")
    user = forms.ModelChoiceField(queryset=UserProfile.objects.all(), required=False)
    department = forms.ModelChoiceField(queryset=Sections.objects.all(), required=False)
    regions = forms.ModelChoiceField(queryset=Regions.objects.all(), required=False)
    designation = forms.ModelChoiceField(queryset=Designations.objects.all(), required=False)
    cost_center = forms.ModelChoiceField(queryset=CostCenter.objects.all(), required=False)

    # ZetdcAssets specific
    product_type = forms.ModelChoiceField(queryset=ProductType.objects.all(), required=False)
    serial_number = forms.CharField(required=False)
    purchase_cost = forms.DecimalField(required=False)
    date_purchased = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))
    model = forms.CharField(required=False)
    supplier = forms.CharField(required=False)

    # HumanResource specific
    officenumber = forms.CharField(required=False)
    descriptionofitem = forms.CharField(required=False)
    lastchecked_at = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                field.widget.attrs.update({'class': 'select2 form-control'})