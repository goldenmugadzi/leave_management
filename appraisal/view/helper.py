from typing import Protocol
from dataclasses import dataclass
from django.forms import BaseModelForm
from django.contrib import messages
from django.http import HttpRequest
from ..helpers.types.kra import KRAType, TargetScoreType, ActivityType, PerformanceDimensionType, KRAOutComeType, AppraiserConfirmationType
from ..helpers.types.dept_workplan import DepartmentalOutTypes, OutputPerformanceDimensionType
from ..helpers.getters.dates import CurrentQuarterDate
from ..models import Appraisal
from ..templatetags.quarter import get_current_quarter
from ..helpers.types.approval import ApprovalStageChoices
from ..repository.kra import YearQuarterRepository
from ..helpers.getters.approval import ApprovalStagesHandler
from ..forms.appraisal import ApprovalStageFilterForm
from pydantic import ValidationError, BaseModel
from loguru import logger

# Payload DeserializationStrategy Interface definition
class PayloadDeserializationStrategyInterface(Protocol):
    
    def deserialize(self, form_object: BaseModelForm)->BaseModel|None:
        pass
    

class KraDeserializationStrategy:
    def deserialize(self, form_object: BaseModelForm)->BaseModel:
        
        data = {
            "key_result_area_description": form_object.cleaned_data.get("key_result_area_description"),
            "goal_description": form_object.cleaned_data.get("goal_description")
        }
        return KRAType(**data)
    
class KraOutComeDeserializationStrategy:
    def deserialize(self, form_object: BaseModelForm)->BaseModel:
        
        data = {
            "outcome_description": form_object.cleaned_data.get("outcome_description")
        }
        return KRAOutComeType(**data)
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
class DepartmentOutputDeserializationStrategy:
    def deserialize(self, form_object: BaseModelForm)->BaseModel:
        data = {
                "output_description": form_object.cleaned_data.get("output_description"),
                "weight": form_object.cleaned_data.get("weight")
                }
        return DepartmentalOutTypes(**data)
class OutputPerformanceDimensionDeserializationStrategy:
    def deserialize(self, form_object: BaseModelForm)->BaseModel:
        data = {
                "performance_indicator": form_object.cleaned_data.get("performance_indicator"),
                "description": form_object.cleaned_data.get("description"),
                "weight": form_object.cleaned_data.get("weight"),
                "allowable_variance": form_object.cleaned_data.get("allowable_variance"),
                "agreed_target": form_object.cleaned_data.get("agreed_target")
                }
        return OutputPerformanceDimensionType(**data)

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
        if is_appraisee:
            data = {
                "score": form.cleaned_data.get("score")
            }
            return TargetScoreType(**data) 
        else:
            data = {
                "appraiser_confirmation": form.cleaned_data.get("appraiser_confirmation"),
                "comments": form.cleaned_data.get("comments"),
            }
            return AppraiserConfirmationType(**data)
    except ValidationError as e:
        error_messages = ""
        for error_message in e.errors():
            msg = f"{error_message['msg']}: '{error_message['loc'][0]}'"
            error_messages.join(msg)
        messages.error(request, error_messages)
        return None
    except Exception as e:
        logger.error(f"[build_payload_score], failed with error: {e}")
        messages.error(request, "something went wrong, please try again.")
        return None
    

def is_within_current_quarter(year: int, quarter: int)->bool:
    current_quarter_date_handler = CurrentQuarterDate(year=year)
    current_quarter_date = current_quarter_date_handler.get_current_quarter()
    
    match quarter:
        case 1:
            if current_quarter_date.is_within_first_quarter:
                return True
        case 2:
            if current_quarter_date.is_within_second_quarter:
                return True
        case 3:
            if current_quarter_date.is_within_third_quarter:
                return True
        case 4:
            if current_quarter_date.is_within_fourth_quarter:
                return True
        case default:
            return False

@dataclass
class ApprovalStagesTemplateHandler:
    appraisal_object: Appraisal
    request_obj: object=None
    
    def get_approval_stage_filter(self)->str:
        approval_stage_filter = None
        if not self.request_obj is None:
            approval_stage_filter = self.request_obj.GET.get('approval_stage_filter', None)
        
        if approval_stage_filter is None:
            current_quarter_name = get_current_quarter(value=None)
            quarters = [q.value for q in ApprovalStageChoices]
            if current_quarter_name not in quarters:
                current_quarter_name = quarters[3]
            approval_stage_filter = current_quarter_name
        return approval_stage_filter
    
    def recursive_approval_stage(self, quarter_name, appraisal_object):
        
        year_quarter_qr = YearQuarterRepository().fetch_by_year(year=appraisal_object.created_date.year)
        
        match quarter_name:
            case ApprovalStageChoices.First_Quarter.value:
                year_quarter_obj = year_quarter_qr.filter(quarter=1).first()
                handler = ApprovalStagesHandler(appraisal_id=appraisal_object.id, year_quarter_id=year_quarter_obj.id)
                approval_stages = handler.get_stages_info()
            case ApprovalStageChoices.Second_Quarter.value:
                year_quarter_obj = year_quarter_qr.filter(quarter=2).first()
                handler = ApprovalStagesHandler(appraisal_id=appraisal_object.id, year_quarter_id=year_quarter_obj.id)
                approval_stages = handler.get_stages_info()
            case ApprovalStageChoices.Third_Quarter.value:
                year_quarter_obj = year_quarter_qr.filter(quarter=3).first()
                handler = ApprovalStagesHandler(appraisal_id=appraisal_object.id, year_quarter_id=year_quarter_obj.id)
                approval_stages = handler.get_stages_info()
            case ApprovalStageChoices.Fourth_Quarter.value:
                year_quarter_obj = year_quarter_qr.filter(quarter=4).first()
                handler = ApprovalStagesHandler(appraisal_id=appraisal_object.id, year_quarter_id=year_quarter_obj.id)
                approval_stages = handler.get_stages_info()
                
        return approval_stages

    
    def get_approval_stages(self):
        try:
            year_quarter_filter = self.get_approval_stage_filter()
            return self.recursive_approval_stage(quarter_name=year_quarter_filter, appraisal_object=self.appraisal_object)
        except Exception as e:
            logger.error(f"[ApprovalStagesTemplateHandler] get_approval_stages for Appraisal pk: {self.appraisal_object.id} failed with error: {e}")
            return None  
        
    def get_approval_stage_filter_form(self):
        """Return the filter form with current selection"""
        current_filter = self.get_approval_stage_filter()
        
        form = ApprovalStageFilterForm(
            initial={"approval_stage_filter": current_filter}
        )
        
        return {
            "approval_stage_filter_form": form,
            "current_approval_filter": current_filter
        }
    
    def get_context_data(self):
        approval_stages_data = self.get_approval_stages()
        approval_stages_form_data = self.get_approval_stage_filter_form()
        return {
            **approval_stages_data,
            **approval_stages_form_data
        }
    
