from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import Target
from ..repository.kra import TargetScoreRepository
from ..services.kra import TargetScoreService
from ..helpers.types.kra import TargetScoreType
from loguru import logger
from django.db import transaction
from it.users.models import Application

@receiver(post_save, sender=Target, dispatch_uid="kra-target-uid")
def create_target_score_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            logger.info(f"[TargetScore]: creating target({instance.name}) score target instance")
            
            repo = TargetScoreRepository()
            service_handler = TargetScoreService(target_score_repository=repo)
            default_values = 0.0
            payload = TargetScoreType(score=default_values, actual_variance=default_values)
            service_handler.create_use_case(target_obj=instance, data=payload)
            
            logger.success(f"[TargetScore]: created score target instance for target({instance.name})")
        except Exception as e:
            logger.error(f"[TargetScore]: creating target({instance.name}), failed with error: {e} ")
   


def create_kra_roles_handler(sender, **kwargs):
    try:
        with transaction.atomic():
            appraisal_application_object = Application.objects.get_or_create(name="appraisal")
            
    except Exception as e:
        logger.error(f"Creating Kra Roles handler failed with error: {e}")
        return