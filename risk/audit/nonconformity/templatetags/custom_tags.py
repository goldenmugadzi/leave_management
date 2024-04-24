from django.template import Library
from urllib.parse import urlparse, parse_qs
from ..models import Nonconformity 
from django.apps import apps
import os
Notification = apps.get_model(app_label='users', model_name='Notification')


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

@register.simple_tag(takes_context=True)
def get_filtered_notifications(context):
     
    user = context['request'].user
    notifications = Notification.objects.filter(user=user).order_by('-created_at')
    filtered_notifications = notifications.filter(is_read=False).order_by('-created_at')#[:10]
    context['filtered_notifications'] = filtered_notifications
    return ""

@register.filter
def total_price(quote_id):
    from finance.purchase_request.models import Quotation  # replace with your actual app and model name

    quote = Quotation.objects.get(id=quote_id)
    
    total = sum(float(item.unit_price) * float(item.quantity) for item in quote.quoteitem_set.all())
    return total if total else 0
@register.filter
def get_extension(file_url):
    return os.path.splitext(file_url)[1]
@register.filter
def order_total_price(id):
    from finance.comperative_schedule.models import Order  # replace with your actual app and model name

    order = Order.objects.get(id=id)
    
    total = sum(float(item.bid_item.price) * float(item.quantity) for item in order.orderitem_set.all())
    return total if total else 0