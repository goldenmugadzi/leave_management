from django.db.models.signals import post_save
from django.dispatch import receiver
from ..repository.kra import TargetScoreRepository
from ..services.kra import TargetScoreService
from ..helpers.types.kra import TargetScoreType
from loguru import logger
from django.db import transaction
from it.users.models import Application
from ..helpers.data.approval_stage import ApprovalStageData
from ..models import Activity, AppraisalWorkflow
from ..helpers.kra_roles import KraModulesRolesStrategyContext, KraModuleStrategy, ActivityModuleStrategy, TargetModuleStrategy, ScoringModuleStrategy

@receiver(post_save, sender=Activity, dispatch_uid="kra-target-uid")
def create_target_score_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            logger.info(f"[TargetScore]: creating target({instance.name}) score target instance")
            
            repo = TargetScoreRepository()
            service_handler = TargetScoreService(target_score_repository=repo)
            default_values = 0.0
            payload = TargetScoreType(score=default_values)
            service_handler.create_use_case(activity_obj=instance, data=payload)
            
            logger.success(f"[TargetScore]: created score target instance for target({instance.name})")
        except Exception as e:
            logger.error(f"[TargetScore]: creating target({instance.name}), failed with error: {e} ")
   


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
    
# def create_approval_stages(sender, **kwargs):
#     try:
#         logger.info(f"Creating Appraisal Approval] initialing ...")
#         for index, stage in enumerate(ApprovalStageData):
#             logger.info(f"[Creating Appraisal Approval] for approval stage: {stage.value}")
            
#             stage_num = index+1
#             AppraisalWorkflow.objects.get_or_create(stage_name=stage.value, stage_num=stage_num, defaults={"stage_name": stage.value, "stage_num": stage_num})
            
#             logger.success(f"[Creating Appraisal Approval] - {stage.value}, created successfully")
        
#         logger.info("Creating Appraisal Approval] completed")
#     except Exception as e:
#         logger.error(f"[Creating Appraisal Approval]-failed with error: {e}")
#         return