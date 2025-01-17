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
        from appraisal.signals.appraisal import create_performance_review_post_save_handler
        from appraisal.signals.appraisal import create_training_development_post_save_handler
        from appraisal.signals.kra import create_target_score_post_save_handler
        from .tasks import run_back_ground_tasks
        
        # Run tasks
        run_back_ground_tasks()