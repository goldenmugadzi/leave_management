from django import template

register = template.Library()

@register.filter
def get_item(dictionary, key):
    """Get an item from a dictionary using a key"""
    return dictionary.get(key)


@register.simple_tag
def current_document(process, document_type):
    """
    Return the current document for a process and document type.
    """
    if not process:
        return None
    return process.documents.filter(document_type=document_type, is_current=True).first()