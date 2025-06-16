from django.db.models.signals import post_save, pre_save
from django.urls import reverse
from django.dispatch import receiver
from ..models.kra import Activity, PERFORMANCE_INDICATOR
from ..helpers.types.kra import PerformanceDimensionType
from ..services.kra import PerformanceDimensionService
from ..repository.kra import PerformanceDimensionRepository
from ..helpers.types import PerformanceReviewType
from ..helpers.types.kra import KraRolesType
from ..helpers.notifications import send_appraisal_notifications
from ..helpers.setters import set_approval_process
from ..models.helpers import YearQuarter
from ..helpers.data.approval_stage import ApprovalStageData
from loguru import logger
from decouple import config
from datetime import datetime
from it.users.models import Roles

@receiver(post_save, sender=Activity, dispatch_uid="activity-uid")
def create_performance_dimension_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            logger.info(f"[PerformanceDimension]: creating performance dimensions for Activity pk: {instance.id}, signal handler init ....")

            for perf_dimension in PERFORMANCE_INDICATOR:
                perf_dimension_type = PerformanceDimensionType(
                    description="",
                    performance_indicator=perf_dimension[1],
                    allowable_variance=0.0,
                    agreed_target=0.0,
                    weight=0
                )
                
                service_handler = PerformanceDimensionService(repo=PerformanceDimensionRepository())
                service_handler.create_use_case(activity_obj=instance, data=perf_dimension_type)
            
            logger.success(f"[PerformanceDimension]: creating performance dimensions for Activity pk: {instance.id}, successfully created")
        except Exception as e:
            logger.error(f"[PerformanceDimension]: creating performance dimensions for Activity pk: {instance.id}, signal handler failed with err: {e}")