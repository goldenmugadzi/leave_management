from django import forms
from it.users.models import CostCenter, Designations, UserProfile
from ..models.helpers import get_year_choices
from ..models.departmental_workplan import DepartmentObjective, DepartmentOutput, OutPutPerformanceDimension
from ..models.training import JobCompetency

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
        fields = ["output_description", "weight"]
        
        
class DesignationFilterForm(forms.Form):
    designations = forms.ModelChoiceField(queryset=Designations.objects.none())
    
    def __init__(self, *args, **kwargs):
        cost_center_id = kwargs.pop("cost_center_id", None)
        super().__init__(*args, **kwargs)
        
        if cost_center_id is not None:
            # set a queryset with cost center designations
            cost_center_users = UserProfile.objects.filter(cost_center__id=cost_center_id).select_related("designation")
            cost_center_designations_id = cost_center_users.values_list("designation_id", flat=True).distinct()
            cost_center_designations_qr = Designations.objects.filter(id__in=cost_center_designations_id)
            self.fields['designations'].queryset = cost_center_designations_qr

class OutPutPerformanceDimensionUpdateForm(forms.ModelForm):
    class Meta:
        model = OutPutPerformanceDimension
        fields = ["performance_indicator", "description", "weight", "allowable_variance", "agreed_target"]

    def __init__(self, *args, **kwargs):
        is_quality_indicator = kwargs.pop("is_quality_indicator", False)
        super().__init__(*args, **kwargs)
        
        if is_quality_indicator:
            self.fields["allowable_variance"].widget = forms.HiddenInput()
            self.fields["agreed_target"].widget = forms.HiddenInput()
        
        self.fields['performance_indicator'].disabled = True
        

class JobCompetencyForm(forms.ModelForm):
    class Meta:
        model = JobCompetency
        fields = ["required_competency"]