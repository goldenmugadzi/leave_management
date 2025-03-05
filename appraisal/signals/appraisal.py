from django.db.models.signals import post_save, pre_save
from django.urls import reverse
from django.dispatch import receiver
from django.db import transaction
from ..models import Appraisal, AppraisalWorkflow
from ..services import PerformanceReviewService, TrainingAndDevelopmentService
from ..repository import PerformanceReviewRepository, TrainingAndDevelopmentRepository
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


@receiver(post_save, sender=Appraisal, dispatch_uid="appraisal-uid")
def create_performance_review_post_save_handler(sender, instance, created, **kwargs):
    """
        Signal handler that triggers after an `Appraisal` instance is created.

        This function listens to the `post_save` signal of the `Appraisal` model. When a new `Appraisal`
        instance is created, it automatically generates performance review entries for all four quarters
        (Q1, Q2, Q3, Q4) of the year associated with the created appraisal.

        Implementation Details:
        1. **Atomic Transaction**:
        - All performance review creation operations are wrapped in a `transaction.atomic()` block.
        - Ensures that either all the performance reviews are created successfully, or none are created
            if an error occurs (maintains database integrity).

        2. **Payload Preparation**:
        - A list of `PerformanceReviewType` objects is prepared, representing each quarter (1 through 4).

        3. **Service Layer Usage**:
        - For each quarter's payload, the `PerformanceReviewService` is instantiated with a
            `PerformanceReviewRepository` dependency.
        - The service's `create_use_case` method is called to create the performance review
            for the specified `Appraisal` instance.

        4. **Logging**:
        - Log messages are added at different stages of the process for observability:
            - Before creating a performance review for a specific quarter.
            - After successfully creating the review.
            - If an error occurs during the process.

        Args:
            sender (class): The model class sending the signal (`Appraisal` in this case).
            instance (Appraisal): The specific instance of `Appraisal` that triggered the signal.
            created (bool): A flag indicating whether a new `Appraisal` instance was created.
            **kwargs: Additional arguments provided by the signal (not used here).

        Raises:
            Any exception raised during the process is logged and handled without affecting
            the `Appraisal` creation.

        Dependencies:
            - `PerformanceReviewType`: A payload type for performance review data.
            - `PerformanceReviewService`: A service responsible for creating performance reviews.
            - `PerformanceReviewRepository`: Repository dependency for the service.
            - `loguru.logger`: For logging messages.
    """
    if created:
        try:
            with transaction.atomic():
                year_quarter_qr = YearQuarter.objects.filter(year=datetime.now().year)

                for year_quarter_obj in year_quarter_qr:
                    performance_review_service = PerformanceReviewService(
                        performance_repo=PerformanceReviewRepository()
                    )
                    logger.info(f"[ PerformanceReview ]: create instance {year_quarter_obj} quart signal for {instance.user} appraisal ....")

                    performance_review_service.create_use_case(
                        appraisal_object=instance,
                        year_quarter_object=year_quarter_obj
                    )

                    logger.success(f"[ PerformanceReview ]: instance {year_quarter_obj} quart for {instance.user} appraisal created :) ")

        except Exception as e:
            logger.error(f"[PerformanceReview]: creating performance review instances failed for {instance.user} appraisal, with error: {e} ")


@receiver(post_save, sender=Appraisal, dispatch_uid="training-dev-uid")
def create_training_development_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:
            training_development_repo_handler = TrainingAndDevelopmentRepository()
            training_development_service_handler = TrainingAndDevelopmentService(training_dev_repo=training_development_repo_handler)

            with transaction.atomic():

                year_quarter_qr = YearQuarter.objects.filter(year=datetime.now().year)

                for year_quarter_obj in year_quarter_qr:
                    logger.info(f"[ TrainingAndDevelopment ]: create instance {year_quarter_obj} quart signal for {instance.user} appraisal ....")
                    training_development_service_handler.create_use_case(
                        appraisal_object=instance,
                        quarter_obj=year_quarter_obj
                    )
                    logger.success(f"[ TrainingAndDevelopment ]: instance {year_quarter_obj} quarter for {instance.user} appraisal created :) ")

        except Exception as e:
            logger.error(f"[TrainingAndDevelopment]: creating training and development instances failed for {instance.user} appraisal, with error: {e} ")

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


@receiver(post_save, sender=Appraisal, dispatch_uid="set_appraiser_approval")
def set_appraiser_approval_post_save_handler(sender, instance, created, **kwargs):
    if not created and instance.is_accepted:
        try:
            logger.info(f"Starting Appraiser Confirmation Process for Appraisal: {instance} ....")
            with transaction.atomic():
                set_approval_process(process_object=instance.process, user_object=instance.appraiser)
                
                logger.success(f"Appraiser Confirmation Process for Appraisal: {instance} completed successfully.")
        except Exception as e:
            logger.error(f"Assigning Appraiser Approval to {instance.user} signal handler failed with error: {e}")
            

@receiver(post_save, sender=Appraisal, dispatch_uid="appraisal_approval_workflow")
def set_appraisal_approval_workflow(sender, instance, created, **kwargs):
    if created:
        try:
            logger.info(f"[Creating Appraisal Approval] appraisal: {instance} handler initialized ...")
            
            workflow_entries = [
                AppraisalWorkflow(
                    appraisal=instance,
                    stage_name=stage.value,
                    stage_num=index+1
                )
                for index, stage in enumerate(ApprovalStageData)
            ]
            
            with transaction.atomic():
                AppraisalWorkflow.objects.bulk_create(workflow_entries)
            
            logger.success("[Creating Appraisal Approval] completed")
        except Exception as e:
            logger.error(f"[Creating Appraisal Approval]-failed with error: {e}")
            return

