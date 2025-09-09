from typing import List
from .types.performance import StrengthAndWeaknessTypes
from approve.models import Approval, Step
from it.users.models import UserProfile
from ..models.performance_review import PerformanceProgressStrength, PerformanceProgressWeakness

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

def map_performance_weaknesses(weaknesses: List[StrengthAndWeaknessTypes])->List[PerformanceProgressWeakness]:
    """
        Maps a list of weaknesses from `StrengthAndWeaknessTypes` objects to a list of `PerformanceProgressWeakness` objects.

        This function is used to transform domain-specific types into model objects suitable for database operations
        or further processing. Each `StrengthAndWeaknessTypes` object in the input list is converted into a
        `PerformanceProgressWeakness` object with its `name` attribute copied.

        Args:
            weaknesses (List[StrengthAndWeaknessTypes]):
                A list of weaknesses represented as `StrengthAndWeaknessTypes` objects.

        Returns:
            List[PerformanceProgressWeakness]:
                A list of `PerformanceProgressStrength` objects corresponding to the input weaknesses.

        Example:
            >>> from .types.performance import StrengthAndWeaknessTypes
            >>> from ..models.performance_review import PerformanceProgressStrength
            >>> weaknesses = [StrengthAndWeaknessTypes(name="Problem Solver"), StrengthAndWeaknessTypes(name="Team Player")]
            >>> mapped_weaknesses = map_performance_weaknesses(weaknesses)
            >>> for strength in mapped_weaknesses:
            ...     print(strength.name)
            Problem Solver
            Team Player
    """

    weaknesses_objects = []
    for weakness in weaknesses:
        weakness_object = PerformanceProgressWeakness(name=weakness.name)
        weaknesses_objects.append(weakness_object)
    return weaknesses_objects


def set_approval_process(process_object: Approval, user_object: UserProfile, approved=True):
    latest_approval = process_object.approval_set.last()
    if latest_approval is not None:
        next_step = latest_approval.step.step + 1
    else:
        next_step = 1
    step_object = Step.objects.filter(workflow=process_object.workflow,step=next_step)

    approved_str = ""
    if approved:
        approved_str = "Approved"
    else:
        approved_str = "Rejected"
    
    Approval.objects.get_or_create(
        step=step_object.first(),
        user=user_object,
        process=process_object,
        defaults={
        "approved": approved_str
        }
    )