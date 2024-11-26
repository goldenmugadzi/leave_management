from django.contrib import admin
from .models import Appraisal, Experience, AppraisalExperience, PerformanceProgressWeakness, PerformanceProgressReview, PerformanceProgressStrength

# Register your models here.

admin.site.register(Appraisal)
admin.site.register(Experience)
admin.site.register(AppraisalExperience)

admin.site.register(PerformanceProgressStrength)
admin.site.register(PerformanceProgressWeakness)
admin.site.register(PerformanceProgressReview)