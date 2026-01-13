from django import forms
from .models import *
from it.users.models import UserProfile
import json

FIELD_CSS_CLASSES = "block w-full rounded-md border-0 py-1.5 text-gray-900 shadow-sm ring-1 ring-inset ring-gray-300 placeholder:text-gray-400 focus:ring-2 focus:ring-inset focus:ring-indigo-600 sm:text-sm sm:leading-6"


class SignatureRequestForm(forms.Form):
    title = forms.CharField(max_length=255)
    file = forms.FileField()
    signers = forms.MultipleChoiceField(
        choices=[],
        required=True,
        widget=forms.SelectMultiple(attrs={
            'class': 'w-full docusign-user-select hidden',
            'style': 'display:None;'
        })
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        # Populate choices for the signers field from UserProfile queryset
        try:
            users = UserProfile.objects.all()
            self.fields['signers'].choices = [(str(u.pk), u.get_full_name() or getattr(u, 'username', str(u.pk))) for u in users]
        except Exception:
            # If models are not available at import time (rare), leave choices empty
            self.fields['signers'].choices = []

        for field_name, field in self.fields.items():
            # apply base classes for consistent styling
            classes = FIELD_CSS_CLASSES
            # For select multiple, keep existing class but append spacing
            if isinstance(field.widget, forms.SelectMultiple):
                field.widget.attrs.setdefault('class', '')
                field.widget.attrs['class'] = (field.widget.attrs['class'] + ' ' + 'py-2 rounded').strip()
            else:
                field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
class DocumentUploadForm(forms.ModelForm):
    class Meta:
        model = Document
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            # apply base classes for consistent styling
            classes = FIELD_CSS_CLASSES
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
class SignerForm(forms.ModelForm):
    class Meta:
        model = Sign
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
class RequestForm(forms.ModelForm):
    class Meta:
        model = Request
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
class SignatureForm(forms.ModelForm):
    class Meta:
        model = Signature
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})
class PossibleSignerForm(forms.ModelForm):
    class Meta:
        model = PossibleSigner
        fields = "__all__"

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        for field_name, field in self.fields.items():
            classes = FIELD_CSS_CLASSES
            field.widget.attrs.update({'class': classes})
            if isinstance(field.widget, forms.Textarea):
                field.widget.attrs.update({'rows': '3'})

