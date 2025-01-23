from django.db.models.signals import post_save
from django.urls import reverse
from django.dispatch import receiver
from django.db import transaction
from ..models import Appraisal
from ..services import PerformanceReviewService, TrainingAndDevelopmentService
from ..repository import PerformanceReviewRepository, TrainingAndDevelopmentRepository
from ..helpers.types import PerformanceReviewType
from ..helpers.notifications import send_appraisal_notifications
from loguru import logger
from decouple import config
from datetime import datetime
from it.users.views import email_notification

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
                performance_review_payloads = [
                    PerformanceReviewType(quarter=1),
                    PerformanceReviewType(quarter=2),
                    PerformanceReviewType(quarter=3),
                    PerformanceReviewType(quarter=4),
                ]

                for performance_review_payload in performance_review_payloads:
                    performance_review_service = PerformanceReviewService(
                        performance_repo=PerformanceReviewRepository()
                    )
                    logger.info(f"[ PerformanceReview ]: create instance {performance_review_payload.quarter} quart signal for {instance.user} appraisal ....")

                    performance_review_service.create_use_case(
                        appraisal_object=instance,
                        data=performance_review_payload
                    )

                    logger.success(f"[ PerformanceReview ]: instance {performance_review_payload.quarter} quart for {instance.user} appraisal created :) ")

        except Exception as e:
            logger.error(f"[PerformanceReview]: creating performance review instances failed for {instance.user} appraisal, with error: {e} ")


@receiver(post_save, sender=Appraisal, dispatch_uid="training-dev-uid")
def create_training_development_post_save_handler(sender, instance, created, **kwargs):
    if created:
        try:

            with transaction.atomic():
                training_development_repo_handler = TrainingAndDevelopmentRepository()
                training_development_service_handler = TrainingAndDevelopmentService(training_dev_repo=training_development_repo_handler)

                for quarter in range(1,5):
                    logger.info(f"[ TrainingAndDevelopment ]: create instance {quarter} quart signal for {instance.user} appraisal ....")
                    training_development_service_handler.create_use_case(
                        appraisal_object=instance,
                        quarter=quarter
                    )
                    logger.success(f"[ TrainingAndDevelopment ]: instance {quarter} quarter for {instance.user} appraisal created :) ")

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