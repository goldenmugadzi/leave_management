from typing import Any
from django.forms import inlineformset_factory, formset_factory, BaseFormSet
from django.forms.utils import ErrorList
from .appraisal import AppraisalExperienceForm, AppraisalQualificationForm
from ..models import AppraisalExperience, Appraisal

AppraisalExperienceFormset = inlineformset_factory(
    parent_model=Appraisal,
    model=AppraisalExperience,
    form=AppraisalExperienceForm,
    extra=1 # Number of blank forms to include in the formset
)


class AppraisalQualificationBaseFormSet(BaseFormSet):
    """FormSet that overrides BaseFormSet to pass down the user object to each constructed form"""
    def __init__(self, *args, user=None, **kwargs):
        super().__init__(*args, **kwargs)
        self.user = user
    
    def _construct_form(self, i, **kwargs):
        kwargs['user'] = self.user  # Pass the user to each form in the formset
        form = super()._construct_form(i, **kwargs)
        return form
    
    
UserQualificationFormset = formset_factory(
    form=AppraisalQualificationForm,
    formset=AppraisalQualificationBaseFormSet,
    extra=1
)