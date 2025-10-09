from django import forms
from ..models import InterventionStrategy, TrainingAndDevelopment, JobCompetency
from ..repository.departmental_workplan import JobCompetencyRepository
from loguru import logger
class InterventionStrategyForm(forms.ModelForm):
    class Meta:
        model = InterventionStrategy
        fields = ["description", "category"]
        
class ActionsForm(forms.ModelForm):
    class Meta:
        model = TrainingAndDevelopment
        fields = ["existence_competencies", "action_recommended", "action_taken"]
        widgets = {
            "existence_competencies": forms.SelectMultiple(
                attrs={
                    "class": "w-full rounded-xl border-gray-300 shadow-sm focus:border-indigo-500 focus:ring-2 focus:ring-indigo-500 focus:ring-offset-1 focus:ring-offset-gray-50 transition-all duration-200 text-gray-800",
                }
            ),
        }
        
    def __init__(self, *args, **kwargs):
        
        designation_id = kwargs.pop("designation_id", False)
        year = kwargs.pop("year", False)
        super().__init__(*args, **kwargs)
        
        if designation_id is not None and year is not None:
            self.fields["existence_competencies"].queryset = JobCompetency.objects.none()
            try:
                repo = JobCompetencyRepository()
                self.fields["existence_competencies"].queryset = repo.fetch_by_designation_id_year(designation_id=designation_id, year=year)
            except Exception as e:
                logger.error(f"[ActionsForm] existence_competencies qr with designation_id: {designation_id} and year: {year}, failed with error: {e}")
        else:
            logger.error(f"[ActionsForm] existence_competencies qr with designation_id: {designation_id} and year: {year}, has no designation id or year")
        
        self.fields["existence_competencies"].required = False
            
