from django import forms
from .models import AssetTransfer

class AssetTransferForm(forms.ModelForm):
    class Meta:
        model = AssetTransfer
        fields = [
            'date',
            'serial_number',
            'asset_description',
            'asset_number',
            'transfer_from',
            'transfer_to',
            'reason_for_transfer',
            
        ]
        widgets = {
            'date': forms.DateInput(attrs={'type': 'date'}),
            'asset_description': forms.Textarea(attrs={'rows': 3}),
            'reason_for_transfer': forms.Textarea(attrs={'rows': 3}),
        }