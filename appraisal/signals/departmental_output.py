from django.db.models.signals import post_save
from django.dispatch import receiver

from ..helpers.types.kra import TargetScoreType
from ..models import DepartmentOutput
from ..repository.departmental_workplan import OutPutPerformanceDimensionRepository
from loguru import logger
from django.db import transaction
from it.users.models import Application


@receiver(post_save, sender=DepartmentOutput, dispatch_uid="create_output_performance_dimensions")
def create_output_performance_dimensions(sender, instance, created, **kwargs):
    
    if created:
        try:
            logger.info(f"[DepartmentalOutputSignal] create_output_performance_dimensions for departmental output pk: {instance.id}, init....")
            
            repo = OutPutPerformanceDimensionRepository()
            if repo.create_in_bulk(department_output_obj=instance):
                logger.success(f"[DepartmentalOutputSignal] create_output_performance_dimensions for departmental output pk: {instance.id}, created successfully ")
            else:
                logger.warning(f"[DepartmentalOutputSignal] create_output_performance_dimensions for departmental output pk: {instance.id}, not created")

        except Exception as e:
                logger.error(f"[DepartmentalOutputSignal] create_output_performance_dimensions for departmental output pk: {instance.id}, failed with error: {e} ")
