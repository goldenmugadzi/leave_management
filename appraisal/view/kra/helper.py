from django.forms import BaseModelForm
from django.contrib import messages
from ...helpers.types.kra import KRAType, TargetType, TargetScoreType
from pydantic import ValidationError

# TODO: Use Strategy Pattern to encapsulate

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
    
def build_payload_target(request, form: BaseModelForm) -> TargetType:
    """
        Constructs and returns a TargetType payload from the cleaned data of the given form.

        Args:
            form (BaseModelForm): A Django form instance with cleaned data.

        Returns:
            TargetType: An instance of TargetType populated with data from the form.

        Raises:
            ValidationError: If the data provided cannot be used to construct a valid KRAType instance.
                The first error message is displayed to the user via Django messages framework.
    """
    try:
        data = {
            "name": form.cleaned_data.get("name"),
            "metric_type": form.cleaned_data.get("metric_type"),
            "weight": form.cleaned_data.get("weight"),
            "allowance_variance": form.cleaned_data.get("allowance_variance"),
            "target_value": form.cleaned_data.get("target_value"),
            "unit": form.cleaned_data.get("unit"),
        }
        return TargetType(**data)
    except ValidationError as e:
        error_message = e.errors()[0]["msg"]
        messages.error(request, error_message)
        raise
    
    
    
def build_payload_score(request, form: BaseModelForm) -> TargetScoreType:
    """
        Constructs and returns a TargetType payload from the cleaned data of the given form.

        Args:
            form (BaseModelForm): A Django form instance with cleaned data.

        Returns:
            TargetType: An instance of TargetType populated with data from the form.

        Raises:
            ValidationError: If the data provided cannot be used to construct a valid KRAType instance.
                The first error message is displayed to the user via Django messages framework.
    """
    try:
        data = {
            "score": form.cleaned_data.get("score"),
            "actual_variance": form.cleaned_data.get("actual_variance"),
            "comment": form.cleaned_data.get("comments"),

        }
        return TargetScoreType(**data)
    except ValidationError as e:
        error_message = e.errors()[0]["msg"]
        messages.error(request, error_message)
        raise
    
    
    