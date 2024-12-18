from django.forms import BaseModelForm
from django.contrib import messages
from ...helpers.types.kra import KRAType
from pydantic import ValidationError

def build_payload(request, form: BaseModelForm) -> KRAType:
    """
        Constructs and returns a KRAType payload from the cleaned data of the given form.

        Args:
            form (BaseModelForm): A Django form instance with cleaned data.

        Returns:
            KRAType: An instance of KRAType populated with data from the form.

        Raises:
            ValidationError: If the data provided cannot be used to construct a valid KRAType instance.
                The first error message is displayed to the user via Django messages framework.
    """
    try:
        data = {
            "name": form.cleaned_data.get("name"),
            "description": form.cleaned_data.get("description"),
            "weight": form.cleaned_data.get("weight"),
        }
        return KRAType(**data)
    except ValidationError as e:
        error_message = e.errors()[0]["msg"]
        messages.error(request, error_message)
        raise