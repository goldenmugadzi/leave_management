from django import forms
from django.core.exceptions import ValidationError

class DashboardDataBulkImportForm(forms.Form):
    """Form for bulk importing dashboard data from CSV/Excel"""
    
    DATA_TYPE_CHOICES = [
        ('weekly_collections', 'Weekly Collections'),
        ('weekly_revenue_lost', 'Weekly Revenue Lost'),
        ('debtor_categories', 'Debtor Categories'),
    ]
    
    data_type = forms.ChoiceField(
        choices=DATA_TYPE_CHOICES,
        label="Data Type",
        help_text="Select the type of data to import"
    )
    
    file = forms.FileField(
        label="Upload File",
        help_text="Upload a CSV or Excel file. See template for required columns.",
        widget=forms.FileInput(attrs={
            'class': 'form-control',
            'accept': '.csv,.xlsx,.xls'
        })
    )
    
    year = forms.IntegerField(
        label="Year",
        help_text="Year for the data being imported",
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    month = forms.IntegerField(
        label="Month (for debtor categories)",
        help_text="Month for debtor category data (1-12)",
        required=False,
        widget=forms.NumberInput(attrs={'class': 'form-control'})
    )
    
    location_type = forms.ChoiceField(
        choices=[
            ('region', 'Region Only'),
            ('district', 'District Level'),
            ('depot', 'Depot Level'),
        ],
        label="Location Level",
        help_text="Select the location level for your data"
    )
    
    skip_duplicates = forms.BooleanField(
        label="Skip Duplicates",
        help_text="Skip existing records instead of showing errors",
        required=False
    )
    
    def clean_file(self):
        file = self.cleaned_data.get('file')
        if file:
            if file.size > 10 * 1024 * 1024:  # 10MB limit
                raise ValidationError("File size cannot exceed 10MB.")
            
            allowed_extensions = ['.csv', '.xlsx', '.xls']
            file_extension = f".{file.name.split('.')[-1].lower()}"
            
            if file_extension not in allowed_extensions:
                raise ValidationError("Only CSV and Excel files are allowed.")
        
        return file
