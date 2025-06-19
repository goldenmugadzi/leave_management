from typing import Protocol
from django.forms import BaseModelForm
from django.contrib import messages
from django.http import HttpRequest
from ...helpers.types.kra import KRAType, TargetScoreType, ActivityType, PerformanceDimensionType
from ...models import TargetScore
from pydantic import ValidationError, BaseModel
from loguru import logger

# Payload DeserializationStrategy Interface definition
class PayloadDeserializationStrategyInterface(Protocol):
    
    def deserialize(self, form_object: BaseModelForm)->BaseModel|None:
        pass
    

class KraDeserializationStrategy:
    def deserialize(self, form_object: BaseModelForm)->BaseModel:
        
        data = {
            "name": form_object.cleaned_data.get("name"),
            "description": form_object.cleaned_data.get("description"),
            "weight": form_object.cleaned_data.get("weight"),
        }
        return KRAType(**data)

class KraActivityDeserializationStrategy:
    def deserialize(self, form_object: BaseModelForm)->BaseModel:
        
        data = {
                "name": form_object.cleaned_data.get("name"),
                "description": form_object.cleaned_data.get("description"),
                "weight": form_object.cleaned_data.get("weight"),
                "performance_indicator": form_object.cleaned_data.get("performance_indicator"),
                "agreed_target": form_object.cleaned_data.get("agreed_target"),
                "allowable_variance": form_object.cleaned_data.get("allowable_variance")
            }
        return ActivityType(**data)
    
class ScoreDeserializationStrategy:
    def deserialize(self, form_object: BaseModelForm)->BaseModel:
        data = {
            "score": form_object.cleaned_data.get("score"),
            "actual_variance": form_object.cleaned_data.get("actual_variance"),
            "comment": form_object.cleaned_data.get("comments"),

        }
        return TargetScoreType(**data)
    
class PerformanceDimensionDeserializationStrategy:
    def deserialize(self, form_object: BaseModelForm)->BaseModel:
        data = {
                "description": form_object.cleaned_data.get("description"),
                "weight": form_object.cleaned_data.get("weight"),
                "performance_indicator": form_object.cleaned_data.get("performance_indicator"),
                "agreed_target": form_object.cleaned_data.get("agreed_target"),
                "allowable_variance": form_object.cleaned_data.get("allowable_variance")
        }
        return PerformanceDimensionType(**data)

class PayloadDeserializationStrategyContext:
    def __init__(self, strategy: PayloadDeserializationStrategyInterface):
        self.strategy = strategy
        
    def deserialize_payload(self, request_object: HttpRequest, form_object: BaseModelForm)->BaseModel|None:
        """            
            Constructs and returns payload from the cleaned data of the given form_object.
            The function make use of django messages function to compose and return response. 

            Args:
                request_object (HttpRequest): Django request object
                form_object (BaseModelForm): A Django form_object instance with cleaned data.

            Returns:
                BaseModel: Pydantic defined base class 
                None: indicates an error
        """
        try:
            return self.strategy.deserialize(form_object=form_object)
        except ValidationError as e:
            # print("========>>>>>>>>>err ", f"{e.errors()[0]}(s): ")
            error_messages = ""
            for error_message in e.errors():
                msg = f"{error_message['msg']}: '{error_message['loc'][0]}'"
                error_messages.join(msg)
            messages.error(request_object, error_messages)
            return None
        except Exception as e:
            logger.error(f"[PayloadDeserializationStrategyContext] of {str(self.strategy)}, failed with error: {e}")
            messages.error(request_object, "something went wrong, please try again.")
            return None


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
    
def build_payload_activity(request, form: BaseModelForm) -> ActivityType:
    """
        Constructs and returns a ActivityType payload from the cleaned data of the given form.

        Args:
            form (BaseModelForm): A Django form instance with cleaned data.

        Returns:
            ActivityType: An instance of ActivityType populated with data from the form.

        Raises:
            ValidationError: If the data provided cannot be used to construct a valid ActivityType instance.
                The first error message is displayed to the user via Django messages framework.
    """
    try:
        data = {
            "name": form.cleaned_data.get("name"),
            "description": form.cleaned_data.get("description"),
            "weight": form.cleaned_data.get("weight"),
            "performance_indicator": form.cleaned_data.get("performance_indicator"),
            "agreed_target": form.cleaned_data.get("agreed_target"),
            "allowable_variance": form.cleaned_data.get("allowable_variance")
        }
        return ActivityType(**data)
    except ValidationError as e:
        error_message = e.errors()[0]["msg"]
        messages.error(request, error_message)
        raise

    
def build_payload_score(request, form: BaseModelForm, is_appraisee: bool) -> TargetScoreType:
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
        if not is_appraisee:
            data = {
                "appraiser_confirmation": form.cleaned_data.get("appraiser_confirmation"),
                "comment": form.cleaned_data.get("comments"),
                "score": form.cleaned_data.get("score")
            }
        else:
            data = {
                "score": form.cleaned_data.get("score"),
                "appraiser_confirmation": form.cleaned_data.get("appraiser_confirmation"),
                "comment": form.cleaned_data.get("comments"),
            }
        return TargetScoreType(**data)
    except ValidationError as e:
        error_message = e.errors()[0]["msg"]
        messages.error(request, error_message)
        raise
    
