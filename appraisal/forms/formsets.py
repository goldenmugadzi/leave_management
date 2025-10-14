from typing import Any
from django.forms import inlineformset_factory, modelformset_factory, formset_factory
from .appraisal import AppraisalExperienceForm, UserQualificationForm, AppraiseePersonalAttributeForm
from .training import InterventionStrategyForm
from .departmental_plan import JobCompetencyForm
from .kra import ScoreDocumentForm
from ..models import AppraisalExperience, Appraisal, InterventionStrategy, ScoreDocument, JobCompetency
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

InterventionStrategyFormSet = modelformset_factory(
    model=InterventionStrategy,
    form=InterventionStrategyForm,
    extra=1
)

ScoreDocumentFormset = modelformset_factory(
    model=ScoreDocument,
    form=ScoreDocumentForm,
    extra=1
)

AppraiseePersonalAttributeFormSet = formset_factory(
    form=AppraiseePersonalAttributeForm,
    extra=0
)

JobCompetencyFormSet = modelformset_factory(
    JobCompetency,
    form=JobCompetencyForm,
    extra=0,        # no extra blank forms by default
    can_delete=True # allow marking forms for deletion
)