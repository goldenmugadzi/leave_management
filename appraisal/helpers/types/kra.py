from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Literal, Annotated, Optional
from ...models.kra import METRIC_TYPES
from enum import Enum
class KRAType(BaseModel):
    name: str = Field(..., description="The name of the KRA.")
    description: str = Field(..., description="The description of KRA.")
    weight: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="The weight of the KRA."
    )

MetricTypeValues = Literal[tuple(metric[1] for metric in METRIC_TYPES)]

class TargetType(BaseModel):
    metric_type: MetricTypeValues = Field(..., description="The metric type of the Target.")
    name: Annotated[str, Field(max_length=255)] = Field(
        ..., description="The name of the Target."
    )
    weight: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="The weight of the Target."
    )
    allowable_variance: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The allowable variance of the Target."
    )
    agreed_target: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The agreed value of the Target."
    )
    unit: Optional[Annotated[str, Field(max_length=30)]] = Field(
        None, description="The unit of the Target."
    )

class TargetScoreType(BaseModel):
    score: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The score of the target."
    )
    comment: Optional[str] = Field(None, description="The comment of the target.")

class KraRolesType(Enum):
    appraisee = "Appraisee"
    appraiser = "Appraiser"
    hod = "Section Head"
    hr = "HR"
    
class KraRolesActionsType(Enum):
    create = "Create"
    update = "Update"
    delete = "Delete"
    read = "Read"