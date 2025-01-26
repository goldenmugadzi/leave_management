from django.db.models.signals import post_save
from django.dispatch import receiver
from ..models import TargetScore
from loguru import logger
from approve.models import Step, Approval
from django.db import transaction

@receiver(post_save, sender=TargetScore, dispatch_uid="target-score-approval")
def target_score_approval_post_save_handler(sender, instance, created, **kwargs):
    if not created and not instance.is_scored:
        try:
            logger.info("Initializing Target Scoring approval ....")
            with transaction.atomic():
                appraisal_object = instance.activity.kra.appraisal
                
                process_object = appraisal_object.process
                latest_approval = process_object.approval_set.last()
                if latest_approval is not None:
                    next_step = latest_approval.step.step + 1
                else:
                    next_step = 1

                step_object = Step.object.filter(workflow=process_object.workflow,step=next_step)
                appraiser_object = appraisal_object.appraiser
                
                Approval.objects.get_or_create(
                    step=step_object,
                    user=appraiser_object,
                    process=process_object,
                    defaults={
                    "approved":'Approved'
                    }
                )
        except Exception as e:
            logger.error(f"Error in Target Score approval(Appraisal: {appraisal_object} | Appraiser: {appraiser_object}) signal handler: {e}")
            
            
