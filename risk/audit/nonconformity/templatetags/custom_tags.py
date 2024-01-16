from django.template import Library
from urllib.parse import urlparse, parse_qs
from ..models import Nonconformity

register = Library()
@register.filter
def extract_id_from_url(url):
    path_parts = url.strip('/').split('/')
    nonconformity_id = path_parts[-1]
    return nonconformity_id

@register.simple_tag
def get_nonconformity(nonconformity_id):
    try:
        nonconformity = Nonconformity.objects.get(id=nonconformity_id)
        return nonconformity
    except Nonconformity.DoesNotExist:
        return None

@register.filter
def split_and_get_last(value, delimiter):
    return value.split(delimiter)[-1]