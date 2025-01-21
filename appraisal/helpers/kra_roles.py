from typing import Protocol
from it.users.models import Application
from .types.kra import KraRolesCreateType, KraModulesType
from ..repository.kra import KraRolesRepository
from .data.kra_data import KRA_ROLES, KRA_ACTIVITY_ROLES, ACTIVITY_TARGETS_ROLES, TARGETS_SCORE_ROLES
from loguru import logger

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
class BaseKraRolesStrategy:
    def set_roles(self, application_object: Application, roles: list, module: str):
        repo = KraRolesRepository()
        for role_data in roles:
            role_input = KraRolesCreateType(
                role=role_data["role"],
                name=role_data["name"],
                description=role_data["description"],
                application=module,
            )
            try:
                repo.create(application_object=application_object, data=role_input)
            except Exception as e:
                logger.error(f"Failed to create role: {role_input}. Error: {e}")


class KraModuleStrategy(BaseKraRolesStrategy):
    def set_roles(self, application_object: Application):
        super().set_roles(application_object, KRA_ROLES, KraModulesType.kra.value)


class ActivityModuleStrategy(BaseKraRolesStrategy):
    def set_roles(self, application_object: Application):
        super().set_roles(application_object, KRA_ACTIVITY_ROLES, KraModulesType.activity.value)


class TargetModuleStrategy(BaseKraRolesStrategy):
    def set_roles(self, application_object: Application):
        super().set_roles(application_object, ACTIVITY_TARGETS_ROLES, KraModulesType.target.value)


class ScoringModuleStrategy(BaseKraRolesStrategy):
    def set_roles(self, application_object: Application):
        super().set_roles(application_object, TARGETS_SCORE_ROLES, KraModulesType.target_score.value)


# ================== Strategy Context ==========================
class KraModulesRolesStrategyContext:
    def __init__(self, strategy: KraModulesRolesStrategyInterface):
        self.strategy = strategy

    def set_kra_module_roles(self, application_object: Application):
        self.strategy.set_roles(application_object=application_object)