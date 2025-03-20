from django.apps import AppConfig
from django.db.models.signals import post_migrate
from loguru import logger

def load_strength_weakness_handler(sender, **kwargs):
    from appraisal.models import PerformanceProgressStrength, PerformanceProgressWeakness
    from appraisal.helpers.data.strenght_weakness import STRENGTHS, WEAKNESSES

    try:
        logger.info("loading performance strength ...")

        strength_objects = [PerformanceProgressStrength(name=item["name"]) for item in STRENGTHS]
        PerformanceProgressStrength.objects.bulk_create(strength_objects, ignore_conflicts=True)

        logger.success("performance strength loaded")
    except Exception as e:
        logger.error(f"loading performance strength failed with error: {e}")

    try:
        logger.info("loading performance weaknesses ...")

        weaknesses_objects = [PerformanceProgressWeakness(name=item["name"]) for item in WEAKNESSES]
        PerformanceProgressWeakness.objects.bulk_create(weaknesses_objects, ignore_conflicts=True)

        logger.success("performance weaknesses loaded")
    except Exception as e:
        logger.error(f"loading performance weaknesses failed with error: {e}")

class AppraisalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appraisal'

    def ready(self) -> None:
        post_migrate.connect(load_strength_weakness_handler, sender=self)
        from .signals.kra import create_kra_roles_handler
        post_migrate.connect(create_kra_roles_handler, sender=self)
        
        from .signals.kra import create_target_score_post_save_handler, create_appraisal_kra_reviewer_status_handler
        from .signals.appraisal import (create_performance_review_post_save_handler, 
                                                 create_training_development_post_save_handler, 
                                                 assign_appraisee_role_post_save_handler,
                                                 set_appraisal_acceptance_stage_completed
                                                 )
        from .signals.target import set_appraisal_scoring_stage_completed
        from .signals.performance_review import set_performance_progress_review_stage_completed, set_training_development_stage_completed
        from .tasks import run_back_ground_tasks
        from .signals.reviewer_status import appraisal_reviewer_workflow_handler
        
        # Run tasks
        run_back_ground_tasks()