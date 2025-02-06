from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import TargetScore, Target
from ..helpers.setters import set_approval_process
from loguru import logger
from django.db import transaction

@receiver(post_save, sender=TargetScore, dispatch_uid="target-score-approval")
def target_score_approval_post_save_handler(sender, instance, created, **kwargs):
    if not created and not instance.is_scored:
        try:
            logger.info("Initializing Target Scoring approval ....")
            with transaction.atomic():
                appraisal_object = instance.activity.kra.appraisal
                process_object = appraisal_object.process
                set_approval_process(process_object=process_object, user_object=process_object.appraiser)

        except Exception as e:
            logger.error(f"Error in Target Score approval(Appraisal: {appraisal_object} | Appraiser: {appraisal_object.appraiser}) signal handler: {e}")
            
            

@receiver(post_save, sender=Target, dispatch_uid="set_target_approval")
def set_target_approval_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            logger.info(f"Starting KRA Approval for Target: {instance} ....")
            with transaction.atomic():
                appraisal_object = instance.activity.kra.appraisal
                set_approval_process(process_object=appraisal_object.process, user_object=appraisal_object.appraiser)
                
                logger.success(f"KRA Approval for Target: {instance} completed successfully.")
        except Exception as e:
            logger.error(f"KRA Approval for Target: {instance}, signal handler failed with error: {e}")
            
            
