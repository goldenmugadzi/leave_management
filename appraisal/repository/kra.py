from ..models import KeyResultArea, YearQuarter
from ..helpers.types.kra import KRAType


class KRARepository:
    def create(self, quarter_obj: YearQuarter, creator_obj, data: KRAType)->KeyResultArea:
        try:
            return KeyResultArea.objects.create(quarter=quarter_obj, created_by=creator_obj, name=data.name, description=data.description, weight=data.weight)
        except Exception as e:
            raise Exception(f"KRA Create Repo failed with error: {e}")
        
