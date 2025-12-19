from django.db.models.signals import post_save
from django.dispatch import receiver

from ..helpers.types.kra import TargetScoreType
from ..models.kra import APPRAISAL_KRA_REVIEWER_STATUS_CHOICES
from loguru import logger
from django.db import transaction
from it.users.models import Application, Roles
from ..helpers.data.roles import APPRAISAL_ROLES

def create_kra_roles_handler(sender, **kwargs):
    try:
        logger.info(f"Create Appraisal App Roles")
        app_obj, _ = Application.objects.get_or_create(name="Appraisal", defaults={"fullname": "Appraisal"})

        roles = APPRAISAL_ROLES
        for role in roles:
            _, _ = Roles.objects.get_or_create(role=role, 
                                            name=role, 
                                            application=app_obj.name, 
                                            defaults={"app_id": app_obj, "description": role})
        logger.success('KRA roles successfully created for all modules.')
    except Exception as e:
        logger.error(f"Creating Kra Roles handler failed with error: {e}")
        return
