from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import TargetScore
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
            
            
