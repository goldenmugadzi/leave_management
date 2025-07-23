from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Literal, Annotated, Optional
from enum import Enum
from ...models.kra import APPRAISAL_KRA_REVIEWER_STATUS_CHOICES
class KRAType(BaseModel):
    key_result_area_description: str = Field(..., description="The KRA description.")
    goal_description: str = Field(..., description="The goal description.")

class KRAOutComeType(BaseModel):
    outcome_description: str = Field(..., description="The outcome description.")


APPRAISER_CONFIRMATION_STATUS = {status[1] for status in APPRAISAL_KRA_REVIEWER_STATUS_CHOICES}

class TargetScoreType(BaseModel):
    score: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The score of the target."
    )
    comment: Optional[str] = Field(None, description="The comment of the target.")
    appraiser_confirmation: str = Field(..., description="The appraiser confirmation value.")

    @field_validator("appraiser_confirmation")
    @classmethod
    def validate_performance_indicator(cls, value: str):
        if value not in APPRAISER_CONFIRMATION_STATUS:
            raise ValueError(f"Invalid appraiser confirmation: {value}")
        return value   
    
class KraRolesType(Enum):
    appraisee = "appraisee"
    appraiser = "appraiser"
    reviewer = "reviewer"
    hr = "hr"
    
class KraRolesActionsType(Enum):
    create = "Create"
    update = "Update"
    delete = "Delete"
    read = "Read"
    
class KraRolesCreateType(BaseModel):
    role: str = Field(..., description="The role action of KRA.")
    name: str = Field(..., description="The role name of KRA.")
    description: str = Field(..., description="The role description of KRA.")
    application: str = Field(..., description="The role application of KRA.")

class KraModulesType(Enum):
    kra = "Kra"
    activity = "Activity"
    target = "Target"
    target_score = "TargetScore"
    
    
class RoleFilterChoices(Enum):
    MY_APPRAISAL = "my_appraisal"
    ASSIGNED_APPRAISALS = "assigned_appraisals"
    APPRAISALS_FOR_REVIEW = "appraisals_for_review"
    ALL_APPRAISALS = "all_appraisals"

    @classmethod
    def choices(cls):
        return [(choice.value, choice.name.replace("_", " ").title()) for choice in cls]


class ActivityType(BaseModel):
    name: str = Field(..., description="The name of the activity.")
    description: str = Field(..., description="The description of the activity.")
    weight: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="The weight of the activity."
    )
    


class PerformanceDimensionType(BaseModel):
    description: str = Field(..., description="The description of the activity.")
    weight: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="The weight of the activity."
    )
    performance_indicator: str = Field(..., description="The performance indicator value of the activity.")
    allowable_variance: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The allowable variance of the Target."
    )
    agreed_target: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The agreed value of the Target."
    )

class WeightProgressType(BaseModel):
    covered_weight: float
    remaining_weight: float