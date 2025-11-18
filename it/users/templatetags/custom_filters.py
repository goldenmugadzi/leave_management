from django import template
from ..models import Responsibilities

register = template.Library()

@register.filter
def get_value(dictionary, key):
    return dictionary.get(key, [])
@register.filter
def get_responsibility(user, key):
    try:
        responsibility = user.responsibilities.filter(role__app_id=key.id).first()
    except Exception as ex:
        print("ex: ", ex)
        responsibility = None
    if responsibility is None:
        return None
    return responsibility

@register.filter
def humanize_key(value):
    """
    Convert snake_case or kebab-case keys into human readable labels.
    """
    if value is None:
        return ""
    if not isinstance(value, str):
        value = str(value)
    return value.replace('_', ' ').replace('-', ' ').title()