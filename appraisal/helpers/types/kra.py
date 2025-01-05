from pydantic import BaseModel, Field, field_validator
from decimal import Decimal
from typing import Literal, Annotated, Optional
from ...models.kra import METRIC_TYPES

class KRAType(BaseModel):
    name: str = Field(..., description="The name of the KRA.")
    description: str = Field(..., description="The description of KRA.")
    weight: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="The weight of the KRA."
    )

    @field_validator('weight')
    @classmethod
    def check_weight_range(cls, value: float) -> float:
        if not 0 <= value <= 100:
            raise ValueError("Weight must be between 0 and 100.")
        return value

MetricTypeValues = Literal[tuple(metric[1] for metric in METRIC_TYPES)]

class TargetType(BaseModel):
    metric_type: MetricTypeValues = Field(..., description="The metric type of the Target.")
    name: Annotated[str, Field(max_length=255)] = Field(
        ..., description="The name of the Target."
    )
    weight: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="The weight of the Target."
    )
    allowance_variance: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The allowance variance of the Target."
    )
    unit: Optional[Annotated[str, Field(max_length=30)]] = Field(
        None, description="The unit of the Target."
    )

class TargetScoreType(BaseModel):
    score: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The score of the target."
    )
    actual_variance: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The actual variance of the target."
    )
    comment: Optional[str] = Field(None, description="The comment of the target.")

