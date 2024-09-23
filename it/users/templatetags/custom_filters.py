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