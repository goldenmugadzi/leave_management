from pydantic import BaseModel, Field, field_validator, ValidationError
from decimal import Decimal
from typing import Literal, Annotated, Optional

def percentage_validation(percentage_value: int):
    if percentage_value <= 0 or percentage_value > 100:
        raise ValueError("Weight must be a percentage between 0 and 100")
    return percentage_value

class DepartmentalOutTypes(BaseModel):
    output_description: str = Field(..., description="The description of the DepartmentOutput.")
    weight: Annotated[Decimal, Field(max_digits=5, decimal_places=2)] = Field(
        ..., description="The weight of the DepartmentOutput."
    )
    
    @field_validator("weight")
    @classmethod
    def validate_weight(cls, value: str):
        return percentage_validation(percentage_value=value) 