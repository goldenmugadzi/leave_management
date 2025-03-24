from django import forms
from .models import Employee

class EmployeeForm(forms.ModelForm):
    class Meta:
        model = Employee
        exclude = ['loggedindate']
        fields = [

            'eserialnumber',
            'userprofile', 
            'ephoneextension',
            'efault',
            'erepairstatus',
            'elocation',
            'eupdatedby',
            'comment',
            'regions',
            'department',
        ]

   

