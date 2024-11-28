from typing import List
from .types.performance import StrengthAndWeaknessTypes
from ..models.performance_review import PerformanceProgressStrength

def map_performance_strengths(strengths: List[StrengthAndWeaknessTypes])->List[PerformanceProgressStrength]:
    strengths_objects = []
    for strength in strengths:
        strength_object = PerformanceProgressStrength(name=strength.name)
        strengths_objects.append(strength_object)
    return strengths_objects