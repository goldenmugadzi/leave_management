from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter
def filter_by_doc_type(documents, doc_type):
    """Filter customer documents by document type"""
    for doc in documents:
        if doc.document_type.id == doc_type.id:
            return doc
    return None 