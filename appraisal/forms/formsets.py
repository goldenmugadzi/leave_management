from django.forms import inlineformset_factory
from .appraisal import AppraisalExperienceForm
from ..models import AppraisalExperience, Appraisal

AppraisalExperienceFormset = inlineformset_factory(
    parent_model=Appraisal,
    model=AppraisalExperience,
    form=AppraisalExperienceForm,
    extra=1 # Number of blank forms to include in the formset
)