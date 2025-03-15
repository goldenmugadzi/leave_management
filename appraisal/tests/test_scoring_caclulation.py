from unittest import TestCase
from ..helpers.getters.rating import RatingCalculation, ActivityRatingEnum
from pydantic import BaseModel
from loguru import logger

class RatingCalculationTestModel(BaseModel):
    name: str
    agreed_target: int
    allowable_variance: int
    actual_score: int
    want_rate: int


class TestRatingCalculation(TestCase):
    def test_calculate_rating(self):
        test_cases = [
            RatingCalculationTestModel(name="nothing was done", agreed_target=35, allowable_variance=5, actual_score=0, want_rate=ActivityRatingEnum.nothing_was_done.value),
            RatingCalculationTestModel(name="no target met and below variance", agreed_target=35, allowable_variance=5, actual_score=29, want_rate=ActivityRatingEnum.no_target_met_below_variance.value),
            RatingCalculationTestModel(name="no target met and within variance", agreed_target=35, allowable_variance=5, actual_score=34, want_rate=ActivityRatingEnum.no_target_met_within_variance.value),
            RatingCalculationTestModel(name="target met and variance met", agreed_target=35, allowable_variance=5, actual_score=35, want_rate=ActivityRatingEnum.target_met_variance_met.value),
            RatingCalculationTestModel(name="target met and within variance", agreed_target=35, allowable_variance=5, actual_score=36, want_rate=ActivityRatingEnum.target_met_within_variance.value),
            RatingCalculationTestModel(name="target met and above variance", agreed_target=35, allowable_variance=5, actual_score=41, want_rate=ActivityRatingEnum.target_met_above_variance.value),
        ]

        rating_handler = RatingCalculation()

        for test_case in test_cases:
            variance_range_classify = rating_handler.classify_variance_range(agreed_target=test_case.agreed_target, allowable_variance=test_case.allowable_variance, actual_score=test_case.actual_score)
            is_target_met = rating_handler.is_target_met(agreed_target=test_case.agreed_target, actual_target=test_case.actual_score)

            got_rate = rating_handler.calculate_rating(is_target_met=is_target_met, variance_range_classify=variance_range_classify)
            self.assertEqual(got_rate, test_case.want_rate)
