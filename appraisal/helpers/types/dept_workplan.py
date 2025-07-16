from pydantic import BaseModel, Field, field_validator, ValidationError
from decimal import Decimal
from typing import Literal, Annotated, Optional
from ...models.departmental_workplan import PERFORMANCE_INDICATOR

def percentage_validation(percentage_value: int, field_name: str):
    if percentage_value <= 0 or percentage_value > 100:
        raise ValueError(f"{field_name} must be a percentage between 0 and 100")
    return percentage_value

class DepartmentalOutTypes(BaseModel):
    output_description: str = Field(..., description="The description of the DepartmentOutput.")
    weight: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="The weight of the DepartmentOutput."
    )
    
    @field_validator("weight")
    @classmethod
    def validate_weight(cls, value: str):
        return percentage_validation(percentage_value=value, field_name="Weight") 
    
VALID_PERFORMANCE_INDICATORS = {choice[1] for choice in PERFORMANCE_INDICATOR}

    
class OutputPerformanceDimensionType(BaseModel):
    performance_indicator: str = Field(..., description="The performance indicator value of the activity.")
    description: str = Field(..., description="The description of the activity.")
    weight: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="The weight of the activity."
    )
    allowable_variance: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The allowable variance of the Target."
    )
    agreed_target: Annotated[Decimal, Field(max_digits=10, decimal_places=2)] = Field(
        ..., description="The agreed value of the Target."
    )

    @field_validator("performance_indicator")
    @classmethod
    def validate_performance_indicator(cls, value: str):
        if value not in VALID_PERFORMANCE_INDICATORS:
            raise ValueError(f"Invalid performance indicator: {value}")
        return value   
    
    @field_validator("weight")
    @classmethod
    def validate_weight(cls, value: str):
        return percentage_validation(percentage_value=value,  field_name="Weight") 
    
    @field_validator("agreed_target")
    @classmethod
    def validate_agreed_target(cls, value: str):
        return percentage_validation(percentage_value=value,  field_name="Agreed target") 
    
    @field_validator("allowable_variance")
    @classmethod
    def validate_allowable_variance(cls, value: str):
        return percentage_validation(percentage_value=value,  field_name="Allowable variance") 