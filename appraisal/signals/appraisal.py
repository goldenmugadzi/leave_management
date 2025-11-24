from django.db.models.signals import post_save, pre_save
from django.urls import reverse
from django.dispatch import receiver
from ..models import Appraisal
from ..services.kra import AppraisalDependanciesInitialisationService
from ..repository import AppraisalRepository
from ..repository.kra import AppraisalDepartmentOutputRepository, AppraisalOutPutPerformanceDimensionScoreRepository, YearQuarterRepository
from ..repository.departmental_workplan import OutPutPerformanceDimensionRepository, DepartmentalOutRepository
from ..helpers.types.kra import KraRolesType
from ..helpers.notifications import send_appraisal_notifications

from loguru import logger

from it.users.models import Roles

@receiver(post_save, sender=Appraisal, dispatch_uid="send-appraiser-email")
def send_appraiser_email_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            logger.info("Appraisal emails handler init ....")
            
            url = reverse("update_appraisal", kwargs={"pk": instance.id})
            notification_type="Appraisal"
            notification_id=instance.id
            
            response_status_code = send_appraisal_notifications(user_object=instance.appraiser,
                                                                notification_type=notification_type,
                                                                notification_id=notification_id,
                                                                url=url
                                                                )
            if response_status_code == 200:
                logger.success(f"Appraisal Email sent successfully. Appraiser: {instance.appraiser}, Appraisee: {instance.user}")
            else:
                logger.error(f"Appraisal Email failed with status code {response_status_code}. Appraiser: {instance.appraiser}, Appraisee: {instance.user}")
        except Exception as e:
            logger.error(f"Appraisal emails signal handler with error: {e}")
            
@receiver(post_save, sender=Appraisal, dispatch_uid="assign_appraisee_role")
def assign_appraisee_role_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            
            
            logger.info(f"Assigning Appraisee role for {instance.user} handler init ....")
            
            if not instance.user.roles.filter(role=KraRolesType.appraisee.value).values("id").exists():
                appraisee_role = Roles.objects.filter(role=KraRolesType.appraisee.value).first()
                
                if appraisee_role:
                    instance.user.roles.add(appraisee_role)
                    instance.user.save()
                    logger.success(f"Appraisee role assigned to {instance.user}.")
                else:
                    logger.warning(f"'Appraisee' role not found in the Roles table.")
                
        except Exception as e:
            logger.error(f"Assigning Appraisee role to {instance.user} signal handler failed with error: {e}")
 
@receiver(post_save, sender=Appraisal, dispatch_uid="appraisal_dependencies")
def set_appraisal_dependencies(sender, instance, created, **kwargs):
    if created:
        try:
            logger.info(f"[AppraisalSignal] set_appraisal_dependencies - Setting Appraisal Dependencies for appraisal pk:{instance.id} initialized ...")
            service_handler = AppraisalDependanciesInitialisationService(
                appraisal_department_output_repo=AppraisalDepartmentOutputRepository(),
                appraisal_output_perf_dimension_repo=AppraisalOutPutPerformanceDimensionScoreRepository(),
                appraisal_repo=AppraisalRepository(),
                year_quarter_repo=YearQuarterRepository(),
                performance_dimension_repo=OutPutPerformanceDimensionRepository(),
                department_output_repo=DepartmentalOutRepository()
            )
            
            appraisal_created_year = instance.created_date.year
            
            if service_handler.create_all_dependencies(appraisal_id=instance.id, year=appraisal_created_year): 
                logger.success(f"[AppraisalSignal] set_appraisal_dependencies - Setting Appraisal Dependencies for appraisal pk:{instance.id} successfully completed")
            else:
                logger.warning(f"[AppraisalSignal] set_appraisal_dependencies - Setting Appraisal Dependencies for appraisal pk:{instance.id} not set")
        except Exception as e:
            logger.error(f"[AppraisalSignal] set_appraisal_dependencies - Setting Appraisal Dependencies for appraisal pk:{instance.id}, failed with error: {e}")
            return None
