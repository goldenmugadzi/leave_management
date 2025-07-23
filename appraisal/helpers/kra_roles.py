from typing import Protocol
from it.users.models import Application
from .types.kra import KraRolesCreateType, KraModulesType
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

