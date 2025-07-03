from django.db.models.signals import post_save
from django.dispatch import receiver
from .models import AccidentReport, SafetyMonthlyReport

@receiver(post_save, sender=AccidentReport)
def accumulate_accident_types(sender, instance, created, **kwargs):
    if not created:
        return

    smr = SafetyMonthlyReport.objects.filter(
        year=instance.date.year,
        month=instance.date.month,
        department=instance.department,
        regions=instance.regions
    ).first()
    if not smr:
        return

    # Increment the correct field
    if instance.type_of_accident == 'first aid case':
        smr.first_aid_cases = (smr.first_aid_cases or 0) + 1
    elif instance.type_of_accident == 'medical treatment':
        smr.medical_treatment_cases = (smr.medical_treatment_cases or 0) + 1
    elif instance.type_of_accident == 'non lost time injury':
        smr.non_lost_time_injuries = (smr.non_lost_time_injuries or 0) + 1
    elif instance.type_of_accident == 'lost time injury':
        smr.lost_time_injuries = (smr.lost_time_injuries or 0) + 1
    elif instance.type_of_accident == 'fatality':
        smr.fatalities = (smr.fatalities or 0) + 1

    # Always increment work_related_accidents as a total
    smr.work_related_accidents = (
        (smr.first_aid_cases or 0) +
        (smr.medical_treatment_cases or 0) +
        (smr.non_lost_time_injuries or 0) +
        (smr.lost_time_injuries or 0) +
        (smr.fatalities or 0)
    )

    smr.save(update_fields=[
        'first_aid_cases', 'medical_treatment_cases', 'non_lost_time_injuries',
        'lost_time_injuries', 'fatalities', 'work_related_accidents'
    ])
