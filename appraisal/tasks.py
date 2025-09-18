
try:  # noqa: SIM105
    from apscheduler.schedulers.background import BackgroundScheduler  # type: ignore
    from apscheduler.triggers.cron import CronTrigger  # type: ignore
    from apscheduler.events import EVENT_JOB_ERROR  # type: ignore
    _APSCHEDULER_AVAILABLE = True
except ImportError:  # pragma: no cover - defensive guard
    _APSCHEDULER_AVAILABLE = False

from django.db import IntegrityError
from loguru import logger
from .models.helpers import YearQuarter, QuarterChoices
from datetime import datetime
import time

# Idempotent guard to prevent multiple scheduler startups (e.g., Django autoreload)
_SCHEDULER_STARTED = False

def run_back_ground_tasks():
    global _SCHEDULER_STARTED
    if _SCHEDULER_STARTED:
        logger.debug("Background scheduler already started; skipping duplicate initialization.")
        return

    if not _APSCHEDULER_AVAILABLE:
        logger.warning("APScheduler is not installed; background tasks will not run. Install APScheduler to enable.")
        return

    try:
        tasks = BackgroundScheduler()
        # TODO: Adjust CronTrigger schedule to production needs. Currently placeholder.
        trigger = CronTrigger(month="1", day="17", hour="15", minute="56")
        tasks.add_job(
            func=create_year_quarter_obj,
            trigger=trigger,
            max_instances=1,
            coalesce=True,
            misfire_grace_time=30,
            replace_existing=True
        )
        tasks.add_listener(lambda event: handle_failure(event, tasks), EVENT_JOB_ERROR)
        tasks.start()
        _SCHEDULER_STARTED = True
        logger.success("Background scheduler started successfully.")
    except Exception as e:  # pragma: no cover
        logger.error(f"Failed to start background scheduler: {e}")


def handle_failure(event, scheduler):
    """Handle task failures by retrying the task."""
    job_id = event.job_id
    for retry in range(0, 5):
        logger.warning(f"Job {job_id} with retry: {retry} failed. Retrying in 5 seconds...")
        time.sleep(5)
        try:
            job = scheduler.get_job(job_id)
            if job:
                job.func()  # Retry the job manually
                return
        except IntegrityError as e:
            logger.error(f"Non-recoverable error for job {job_id}: {e}")
            break
        except Exception as e:
            logger.error(f"Retry failed for job {job_id}: {e}")  
            
def create_year_quarter_obj():
    logger.info("Initializing YearQuarter creation handler ...")
    for quarter_choice in QuarterChoices.choices:
        current_year = datetime.now().year
        quarter_number = quarter_choice[0]
        try:
            YearQuarter.objects.get_or_create(
                year=current_year,
                quarter=quarter_number
            )
            logger.success(f"YearnQuarte for year {current_year} - Q {quarter_number} created.")
        except IntegrityError:
            logger.warning(f"Duplicate entry prevented for year {current_year}, quarter {quarter_number}")