from typing import List
from .types.performance import StrengthAndWeaknessTypes
from ..models.performance_review import PerformanceProgressStrength

def map_performance_strengths(strengths: List[StrengthAndWeaknessTypes])->List[PerformanceProgressStrength]:
    """
        Maps a list of strengths from `StrengthAndWeaknessTypes` objects to a list of `PerformanceProgressStrength` objects.

        This function is used to transform domain-specific types into model objects suitable for database operations 
        or further processing. Each `StrengthAndWeaknessTypes` object in the input list is converted into a 
        `PerformanceProgressStrength` object with its `name` attribute copied.

        Args:
            strengths (List[StrengthAndWeaknessTypes]): 
                A list of strengths represented as `StrengthAndWeaknessTypes` objects.

        Returns:
            List[PerformanceProgressStrength]: 
                A list of `PerformanceProgressStrength` objects corresponding to the input strengths.

        Example:
            >>> from .types.performance import StrengthAndWeaknessTypes
            >>> from ..models.performance_review import PerformanceProgressStrength
            >>> strengths = [StrengthAndWeaknessTypes(name="Problem Solver"), StrengthAndWeaknessTypes(name="Team Player")]
            >>> mapped_strengths = map_performance_strengths(strengths)
            >>> for strength in mapped_strengths:
            ...     print(strength.name)
            Problem Solver
            Team Player
    """
    
    strengths_objects = []
    for strength in strengths:
        strength_object = PerformanceProgressStrength(name=strength.name)
        strengths_objects.append(strength_object)
    return strengths_objects