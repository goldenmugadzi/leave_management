from django import forms
from django.core.exceptions import ValidationError
from .models import Document
from .models import Subcategory
import bleach
import re
import logging

logger = logging.getLogger(__name__)

def validate_no_scripts(value):
    """
    Validator to reject input containing script tags or javascript.
    Prevents XSS attacks at the model/form validation level.
    """
    if not value:
        return value
    
    # Check for script tags
    if re.search(r'<script[^>]*>.*?</script>', value, re.IGNORECASE | re.DOTALL):
        logger.warning(f"XSS attempt detected: script tag in input - {value[:100]}")
        raise ValidationError('Script tags are not allowed for security reasons.')
    
    # Check for javascript: protocol
    if re.search(r'javascript:', value, re.IGNORECASE):
        logger.warning(f"XSS attempt detected: javascript protocol in input - {value[:100]}")
        raise ValidationError('JavaScript code is not allowed for security reasons.')
    
    # Check for event handlers
    if re.search(r'on\w+\s*=', value, re.IGNORECASE):
        logger.warning(f"XSS attempt detected: event handler in input - {value[:100]}")
        raise ValidationError('Event handlers are not allowed for security reasons.')
    
    return value

def sanitize_input(value):
    """
    Sanitize input by stripping all HTML tags and potentially dangerous content.
    Uses bleach library for robust HTML sanitization.
    """
    if not value:
        return value
    
    # Strip all HTML tags - no tags allowed in name field
    cleaned = bleach.clean(value, tags=[], strip=True)
    
    # Remove any remaining whitespace artifacts
    cleaned = ' '.join(cleaned.split())
    
    return cleaned

class DocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = "__all__" #['category', 'name', 'region', 'section', 'file', 'created_by']
        exclude=['created_by', 'section']
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })
    
    def clean_name(self):
        """Sanitize the name field to prevent XSS attacks."""
        name = self.cleaned_data.get('name')
        if name:
            # First validate - this will raise ValidationError if malicious content detected
            validate_no_scripts(name)
            # Then sanitize
            name = sanitize_input(name)
            logger.info(f"Document name sanitized: {name}")
        return name

class Subcategory(forms.ModelForm):
  class Meta:
    model = Subcategory
    fields = ['category', 'name']
  
  def clean_name(self):
    """Sanitize the name field to prevent XSS attacks."""
    name = self.cleaned_data.get('name')
    if name:
      # First validate - this will raise ValidationError if malicious content detected
      validate_no_scripts(name)
      # Then sanitize
      name = sanitize_input(name)
      logger.info(f"Subcategory name sanitized: {name}")
    return name

class editDocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = "__all__" #['category', 'name', 'region', 'section', 'file', 'created_by']
        exclude=['created_by','file', 'section', 'archive']
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        for field_name, field in self.fields.items():
            field.widget.attrs.update({
                'class': "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6",
            })
    
    def clean_name(self):
        """Sanitize the name field to prevent XSS attacks."""
        name = self.cleaned_data.get('name')
        if name:
            # First validate - this will raise ValidationError if malicious content detected
            validate_no_scripts(name)
            # Then sanitize
            name = sanitize_input(name)
            logger.info(f"Document name sanitized during edit: {name}")
        return name

class archiveDocumentForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = "__all__" #['category', 'name', 'region', 'section', 'file', 'created_by']
        exclude=['created_by','section']
   
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
