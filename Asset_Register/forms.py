from django import forms
from .models import ZetdcAssets, HumanResource, ProductType, UserProfile, Designations, CostCenter, Sections, Regions

class CombinedAssetForm(forms.Form):
    TYPE_CHOICES = (
        ('asset', 'IT Asset'),
        ('hr', 'HR Asset'),
    )
    asset_type = forms.ChoiceField(choices=TYPE_CHOICES, label="Asset Type")

    # Common fields
    assetnumber = forms.CharField(required=False, label="Asset Number")
    asset_state = forms.CharField(required=False, label="Asset State")
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
    warrant = forms.CharField(required=False)
    created_by = forms.ModelChoiceField(queryset=UserProfile.objects.all(), required=False)
    supplier = forms.CharField(required=False)

    # HumanResource specific
    officenumber = forms.CharField(required=False)
    descriptionofitem = forms.CharField(required=False)
    lastchecked_at = forms.DateField(required=False, widget=forms.DateInput(attrs={'type': 'date'}))

    def save(self):
        cleaned = self.cleaned_data
        if cleaned['asset_type'] == 'asset':
            asset = ZetdcAssets(
                product_type=cleaned['product_type'],
                serial_number=cleaned['serial_number'],
                asset_number=cleaned['assetnumber'],
                asset_state=cleaned['asset_state'],
                user=cleaned['user'],
                regions=cleaned['regions'],
                purchase_cost=cleaned['purchase_cost'] or 0,
                designation=cleaned['designation'],
                department=cleaned['department'],
                date_purchased=cleaned['date_purchased'],
                model=cleaned['model'],
                warrant=cleaned['warrant'],
                cost_center=cleaned['cost_center'],
                created_by=cleaned['created_by'],
                supplier=cleaned['supplier'],
            )
            asset.save()
            return asset
        else:
            hr = HumanResource(
                assetnumber=cleaned['assetnumber'],
                designation=cleaned['designation'],
                cost_center=cleaned['cost_center'],
                department=cleaned['department'],
                officenumber=cleaned['officenumber'],
                assetstate=cleaned['asset_state'],
                regions=cleaned['regions'],
                descriptionofitem=cleaned['descriptionofitem'],
                user=cleaned['user'],
                lastchecked_at=cleaned['lastchecked_at'] or None,
            )
            hr.save()
            return hr
        
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            if isinstance(field, forms.ModelChoiceField):
                field.widget.attrs.update({'class': 'select2 form-control'})