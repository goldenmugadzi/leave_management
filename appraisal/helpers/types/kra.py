from pydantic import BaseModel, Field, field_validator

class KRAType(BaseModel):
    name: str = Field(..., description="The name of the KRA.")
    description: str = Field(..., description="The description of KRA.")
    weight: float = Field(...,description="The weight of KRA.")

    @field_validator('weight')
    @classmethod
    def check_weight_range(cls, v: float):
        weight = v
        if weight < 0 or weight > 100:
            raise ValueError('Weight must be between 0 and 100.')
        return v
