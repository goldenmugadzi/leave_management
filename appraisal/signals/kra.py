from django.db.models.signals import post_save
from django.dispatch import receiver
from ..repository.kra import TargetScoreRepository, ApprasialKraReviewerStatusRepository
from ..services.kra import TargetScoreService
from ..helpers.types.kra import TargetScoreType
from ..models import AppraisalKra, PerformanceDimension
from ..models.kra import APPRAISAL_KRA_REVIEWER_STATUS_CHOICES
from loguru import logger
from django.db import transaction
from it.users.models import Application
from ..helpers.kra_roles import KraModulesRolesStrategyContext, KraModuleStrategy, ActivityModuleStrategy, TargetModuleStrategy, ScoringModuleStrategy

@receiver(post_save, sender=PerformanceDimension, dispatch_uid="kra-target-uid")
def create_target_score_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            logger.info(f"[TargetScore]: creating target({instance.name}) score target instance")
            
            repo = TargetScoreRepository()
            service_handler = TargetScoreService(target_score_repository=repo)
            default_values = 0.0
            payload = TargetScoreType(score=default_values)
            service_handler.create_use_case(performance_dimension_obj=instance, data=payload, attachments=[])
            
            logger.success(f"[TargetScore]: created score target instance for performance dimension ({instance.performance_dimension})")
        except Exception as e:
            logger.error(f"[TargetScore]: creating target for performance dimension ({instance.performance_dimension}), failed with error: {e} ")
   


def create_kra_roles_handler(sender, **kwargs):
    try:
        with transaction.atomic():
            logger.info('Loading KRA Roles.....')
            appraisal_application_object, _ = Application.objects.get_or_create(name="Appraisal", defaults={"fullname": "Appraisal"})
            
            # Define strategies for each module
            strategies = [
                KraModulesRolesStrategyContext(KraModuleStrategy()),
            ]

            # Apply each strategy to set roles
            for strategy_context in strategies:
                strategy_context.set_kra_module_roles(appraisal_application_object)
            
            logger.success('KRA roles successfully created for all modules.')
    except Exception as e:
        logger.error(f"Creating Kra Roles handler failed with error: {e}")
        return
    

@receiver(post_save, sender=AppraisalKra, dispatch_uid="appraisal-kra_reviewer_status-uid")
def create_appraisal_kra_reviewer_status_handler(sender, instance, created, **kwargs):
    if created:
        try:
            logger.info(f'Creating ApprasialKraReviewerStatus for AppraisalKra pk {instance.id} .....')
            
            repo = ApprasialKraReviewerStatusRepository()
            repo.create(appraisal_kra_obj=instance, status=APPRAISAL_KRA_REVIEWER_STATUS_CHOICES[0][0])
            
            logger.success(f"ApprasialKraReviewerStatus for AppraisalKra pk {instance.id} created successfully.")
        except Exception as e:
            logger.error(f"Creating Appraisal Kra Reviewer signal handler failed with error: {e}")
            return