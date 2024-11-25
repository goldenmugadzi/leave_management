from django.contrib import admin
from .models import Appraisal, Experience, AppraisalExperience

# Register your models here.

admin.site.register(Appraisal)
admin.site.register(Experience)
admin.site.register(AppraisalExperience)
