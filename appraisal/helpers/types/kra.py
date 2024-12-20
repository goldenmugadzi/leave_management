from pydantic import BaseModel, Field, field_validator
from typing import Literal
from ...models.kra import METRIC_TYPES

class KRAType(BaseModel):
    name: str = Field(..., description="The name of the KRA.")
    description: str = Field(..., description="The description of KRA.")
    weight: float = Field(...,description="The weight of KRA.")

    @field_validator('weight')
    @classmethod
    def check_weight_range(cls, value: float) -> float:
        if not 0 <= value <= 100:
            raise ValueError("Weight must be between 0 and 100.")
        return value

MetricTypeValues = Literal[tuple(metric[1] for metric in METRIC_TYPES)]

class TargetType(BaseModel):
    name: str = Field(..., description="The name of the the Target.")
    metric_type: MetricTypeValues = Field(..., description="The metric type of the Target.")
    weight: float = Field(...,description="The weight of the Target.")
    allowance_variance: float = Field(...,description="The allowance variance of the Target.")
    target_value: float = Field(...,description="The target value of the Target.")
