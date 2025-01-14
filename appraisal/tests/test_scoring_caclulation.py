from unittest import TestCase
from ..helpers.getters import get_actual_variance, get_within_condition, get_rating

class TestGetActualVariance(TestCase):
    def test_actual_variance_success(self):
        # Arrange
        actual_score = 90
        target_score = 100
        want = -10

        # Act
        got = get_actual_variance(actual_score=actual_score, target_score=target_score)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_zero(self):
        # Arrange
        actual_score = 100
        target_score = 100
        want = 0

        # Act
        got = get_actual_variance(actual_score=actual_score, target_score=target_score)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_both_scores_zero(self):
        # Arrange
        actual_score = 0
        target_score = 0
        want = 0

        # Act
        got = get_actual_variance(actual_score=actual_score, target_score=target_score)

        # Assert
        self.assertEqual(want, got)

class TestGetWithInCondition(TestCase):
    def test_success_calculation(self):
        # Arrange
        actual_variance = 5
        allowed_variance = 10
        want = 0.5
        # Act
        got = get_within_condition(actual_variance=actual_variance, allowable_variance=allowed_variance)

        # Assert
        self.assertEqual(want, got)

    def test_allowance_variance_zero_error(self):
        # Arrange
        actual_variance = 5
        allowed_variance = 0
        expected_err = "Allowance variance cannot be zero"

        # Act & Assert
        with self.assertRaises(ValueError) as context:
            get_within_condition(actual_variance=actual_variance, allowable_variance=allowed_variance)

        self.assertEqual(str(context.exception), expected_err)

class TestGetRating(TestCase):
    def test_rating_5(self):
        self.assertEqual(get_rating(0, 0), 5)
        self.assertEqual(get_rating(-1, 0.5), 5)
        self.assertEqual(get_rating(-1, -0.5), 5)

    def test_rating_6(self):
        self.assertEqual(get_rating(1, 2), 6)
        self.assertEqual(get_rating(5, 3), 6)

    def test_rating_4(self):
        self.assertEqual(get_rating(-1, -0.5), 4)

    def test_rating_3(self):
        self.assertEqual(get_rating(-1, -1.5), 3)

    def test_rating_2(self):
        self.assertEqual(get_rating(-1, -2.5), 2)

    def test_rating_1(self):
        self.assertEqual(get_rating(-1, -5), 1)

    def test_rating_0(self):
        # Case where no condition is met
        self.assertEqual(get_rating(1, 0), 0)
        self.assertEqual(get_rating(0, 2), 0)
