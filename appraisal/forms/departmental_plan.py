from django import forms
from it.users.models import CostCenter
from ..models.helpers import get_year_choices
from ..models.departmental_workplan import DepartmentObjective, DepartmentOutput

class CostCenterFilterForm(forms.Form):
    cost_center = forms.ModelChoiceField(queryset=CostCenter.objects.all())
    year = forms.ChoiceField(choices=get_year_choices())
    
class DepartmentObjectiveCreateForm(forms.ModelForm):
    class Meta:
        model = DepartmentObjective
        fields = ["key_result_area", "cost_center", "objective_description"]
    
class DepartmentObjectiveUpdateForm(forms.ModelForm):
    class Meta:
        model = DepartmentObjective
        fields = ["key_result_area", "objective_description"]
    
class DepartmentOutputCreateForm(forms.ModelForm):
    class Meta:
        model = DepartmentOutput
        fields = ["department_objective", "output_description", "weight"]