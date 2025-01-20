from typing import List
from typing import Protocol
from it.users.models import Application
from .types.performance import StrengthAndWeaknessTypes
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


# implement strategy pattern for setting KRA related models roles

# ================= Strategy Interface ==========================
class KraModulesRolesStrategyInterface(Protocol):
    def set_roles(self, application_object: Application):
        """Set roles per each kra module

        Args:
            application_object (Application): instance of Application model
        """
        pass

# =================== Concrete implementations ===================
class KraModuleStrategy:
    def set_roles(self, application_object: Application):
        ...
class ActivityModuleStrategy:
    def set_roles(self, application_object: Application):
        ...
class TargetModuleStrategy:
    def set_roles(self, application_object: Application):
        ...
class ScoringModuleStrategy:
    def set_roles(self, application_object: Application):
        ...
        
# ================== Context ===================
class KraModulesRolesStrategyContext:
    def __init__(self, strategy: KraModulesRolesStrategyInterface):
        self.strategy = strategy
    
    def set_kra_module_roles(self, application_object: Application):
        """
        Delegates the role-setting task to the selected strategy.

        Args:
            application_object (Application): An instance of the Application model.
        """
        return self.strategy.set_roles(application_object)