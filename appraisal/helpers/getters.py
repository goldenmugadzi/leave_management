from typing import Dict, Any
from django.db.models import Model


def get_changed_fields(model_object: Model, data: Dict[str, Any]) -> Dict[str, Any]:
    changed_data = {}
    for key, value in data.items():
        current_user_value = getattr(model_object, key, None)
        if value != current_user_value:
            changed_data[key] = value
    return changed_data

def get_actual_variance(actual_score: float, target_score: float)->float:
    """Calculates the actual variance between the target score and the actual score.

    Args:
        actual_score (float): The achieved score.
        target_score (float): The target score.

    Returns:
        float: The variance between the target and actual scores.
    """
    actual_variance = actual_score-target_score
    return actual_variance

def get_within_condition(actual_variance: float, allowable_variance: float)->float:
    """
        Calculates the within condition, which is the ratio of actual_variance to allowable_variance.

        Args:
            actual_variance (float): The actual variance.
            allowable_variance (float): The allowable variance.

        Returns:
            float: The calculated within condition.

        Raises:
            ValueError: If allowable_variance is zero.
    """
    if allowable_variance == 0:
        raise ValueError("Allowance variance cannot be zero")
    return float(actual_variance) / float(allowable_variance)

def get_rating(actual_variance, within_condition):
    rating = 0
    if (within_condition > -1 and within_condition < 1):
        rating = 5
    elif actual_variance > 0 and within_condition > 1:
        rating = 6
    elif actual_variance < 0 and within_condition < 0 and within_condition >-1:
        rating = 4
    elif actual_variance < 0 and within_condition <-1 and within_condition >-2:
        rating = 3
    elif actual_variance < 0 and within_condition <-2 and within_condition >-3:
        rating = 2
    elif actual_variance < 0 and within_condition <-4:
        rating = 1
    return rating
