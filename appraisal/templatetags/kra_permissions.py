from django import template
from it.users.models import UserProfile
from loguru import logger

register = template.Library()

@register.filter
def has_permissions(user_id: UserProfile, role_name: str):
    print("==================>>>>>>>", role_name)
    try:
        qr = UserProfile.objects.filter(id=user_id, roles__name__iexact=role_name).values("id")
        return qr.exists()
    except Exception as e:
        logger.error(f"Query user roles failed with error: {e}")
        return False