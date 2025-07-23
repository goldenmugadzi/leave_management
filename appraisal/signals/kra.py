from django.db.models.signals import post_save
from django.dispatch import receiver

from ..helpers.types.kra import TargetScoreType
from ..models.kra import APPRAISAL_KRA_REVIEWER_STATUS_CHOICES
from loguru import logger
from django.db import transaction
from it.users.models import Application


def create_kra_roles_handler(sender, **kwargs):
    try:
        logger.success('KRA roles successfully created for all modules.')
    except Exception as e:
        logger.error(f"Creating Kra Roles handler failed with error: {e}")
        return
