from typing import Any
from django.forms import inlineformset_factory, modelformset_factory, formset_factory
from .appraisal import AppraisalExperienceForm, UserQualificationForm
from .training import InterventionStrategyForm, CompetencyForm
from ..models import AppraisalExperience, Appraisal, InterventionStrategy
from it.users.models import UserQualification

AppraisalExperienceFormset = inlineformset_factory(
    parent_model=Appraisal,
    model=AppraisalExperience,
    form=AppraisalExperienceForm,
    extra=1 # Number of blank forms to include in the formset
)

    
UserQualificationFormset = modelformset_factory(
    model=UserQualification,
    form=UserQualificationForm,
    extra=1
)

CompetencyFormSet = formset_factory(
    form=CompetencyForm,
    extra=1
)

InterventionStrategyFormSet = modelformset_factory(
    model=InterventionStrategy,
    form=InterventionStrategyForm,
    extra=1
)