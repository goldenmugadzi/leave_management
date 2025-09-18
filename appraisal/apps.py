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

def load_personal_attributes_handler(sender, **kwargs):
    from appraisal.repository.appraisal import PersonalAttributeRepository
    from appraisal.helpers.data.personal_attr import PERSORNAL_ATTRIBUTES
    from appraisal.models.appraisal import PersonalAttribute
    
    try:
        logger.info("loading personal_attributes ...")
        personal_attr_objs = []
        
        for personal_attr_item in PERSORNAL_ATTRIBUTES:
            personal_attr_obj = PersonalAttribute(name=personal_attr_item["name"])
            personal_attr_objs.append(personal_attr_obj)
        
        repo = PersonalAttributeRepository()
        is_loaded = repo.bulk_create(personal_attr_list=personal_attr_objs)
        if is_loaded:
            logger.success("personal_attributes loaded successfully")
        else:
            logger.warning("personal_attributes loaded unsuccessfully")
    except Exception as e:
        logger.error(f"load_personal_attributes_handler failed with error: {e}")


def set_quarter_year(sender, **kwargs):
    from datetime import datetime
    from appraisal.models.helpers import YearQuarter
    from appraisal.tasks import create_year_quarter_obj
    
    current_year = datetime.now().year
    quarter_year_qr = YearQuarter.objects.filter(year=current_year)
    
    if not quarter_year_qr.exists():
        create_year_quarter_obj()

class AppraisalConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'appraisal'

    def ready(self) -> None:
        post_migrate.connect(load_strength_weakness_handler, sender=self)
        post_migrate.connect(load_personal_attributes_handler, sender=self)
        post_migrate.connect(set_quarter_year, sender=self)
        
        from .signals.kra import create_kra_roles_handler
        from .signals.appraisal import set_appraisal_dependencies, create_training_development_post_save_handler, set_appraisal_acceptance_stage_completed
        from .signals.departmental_output import create_output_performance_dimensions
        post_migrate.connect(create_kra_roles_handler, sender=self)        

        from .tasks import run_back_ground_tasks
        
        # Run tasks
        run_back_ground_tasks()