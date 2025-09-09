from enum import Enum

class VarianceRangeValuesEnum(Enum):
    within_range = "within range"
    above_range = "above range"
    below_range = "below range"
    variance_equal = "variance equal"
    no_variant = "no variant"

class ActivityRatingEnum(Enum):
    nothing_was_done = 1
    no_target_met_below_variance = 2
    no_target_met_within_variance = 3
    target_met_variance_met = 4
    target_met_within_variance = 5
    target_met_above_variance = 6

class RatingCalculation:
    def get_actual_variance(self, actual_score: float, target_score: float) -> float:
        """
        Calculates the actual variance between the target score and the actual score.

        Args:
            actual_score (float): The achieved score.
            target_score (float): The target score.

        Returns:
            float: The variance between the target and actual scores.
        """
        if actual_score == 0:
            return target_score
        actual_variance = target_score - actual_score
        return abs(actual_variance)

    def is_target_met(self, agreed_target: float, actual_target: float) -> bool:
        """
        Determines whether the actual target meets or exceeds the agreed target.

        Args:
            agreed_target (float): The predefined target value.
            actual_target (float): The achieved value.

        Returns:
            bool: True if the actual target is equal to or greater than the agreed target, otherwise False.
        """
        return actual_target >= agreed_target

    def classify_variance_range(self, agreed_target: float, allowable_variance: float, actual_score: float) -> VarianceRangeValuesEnum:
        """
        Classifies `actual_variance` based on `allowable_variance`.

        The acceptable range is [0, 2 * allowable_variance].

        Args:
            allowable_variance: Non-negative value defining the acceptable range.
            actual_variance: Value to classify.

        Returns:
            VarianceRangeValuesEnum: `within_range`, `above_range`, or `below_range`.

        Raises:
            ValueError: If `allowable_variance` is negative.
        """
        if allowable_variance < 0:
            raise ValueError("allowable_variance must be non-negative")

        if allowable_variance > agreed_target:
            raise ValueError("allowable_variance must be less than the agreed_target")


        if actual_score == 0:
            return VarianceRangeValuesEnum.no_variant

        upper_limit = agreed_target + allowable_variance
        lower_limit = agreed_target - allowable_variance

        if lower_limit <= actual_score <= upper_limit:
            if actual_score == agreed_target:
                return VarianceRangeValuesEnum.variance_equal
            return VarianceRangeValuesEnum.within_range
        elif actual_score > upper_limit:
            return VarianceRangeValuesEnum.above_range
        else:  # actual_variance < lower_limit
            return VarianceRangeValuesEnum.below_range

    def calculate_rating(self, is_target_met: bool, variance_range_classify: VarianceRangeValuesEnum) -> int:
        """
        Calculates the activity rating based on whether the target was met and the variance classification.

        Args:
            is_target_met (bool): Whether the target was met.
            variance_range_classify (VarianceRangeValuesEnum): The classification of the variance.

        Returns:
            int: The activity rating as defined by `ActivityRatingEnum`.
        """
        if not is_target_met:
            if variance_range_classify == VarianceRangeValuesEnum.below_range:
                return ActivityRatingEnum.no_target_met_below_variance.value
            elif variance_range_classify == VarianceRangeValuesEnum.within_range:
                return ActivityRatingEnum.no_target_met_within_variance.value
        else:
            if variance_range_classify == VarianceRangeValuesEnum.within_range:
                return ActivityRatingEnum.target_met_within_variance.value
            elif variance_range_classify == VarianceRangeValuesEnum.above_range:
                return ActivityRatingEnum.target_met_above_variance.value
            else:
                return ActivityRatingEnum.target_met_variance_met.value

        return ActivityRatingEnum.nothing_was_done.value
