from typing import Dict, Any
from django.db.models import Model

def get_changed_fields(model_object: Model, data: Dict[str, Any]) -> Dict[str, Any]:
    changed_data = {}
    for key, value in data.items():
        current_user_value = getattr(model_object, key, None)
        if value != current_user_value:
            changed_data[key] = value
    return changed_data
