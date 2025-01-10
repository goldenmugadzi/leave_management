from unittest import TestCase
from ..helpers.getters import get_actual_variance, get_within_condition, get_rating

class TestGetActualVariance(TestCase):
    def test_actual_variance_success(self):
        # Arrange
        actual_score = 90
        target_score = 100
        want = 10

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
    def test_actual_variance_positive_within_condition_within_1(self):
        # Arrange
        actual_variance = 1
        within_condition = 0.8
        want = 5

        # Act
        got = get_rating(actual_variance, within_condition)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_positive_within_condition_above_1(self):
        # Arrange
        actual_variance = 1
        within_condition = 1.5
        want = 6

        # Act
        got = get_rating(actual_variance, within_condition)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_negative_within_condition_within_1(self):
        # Arrange
        actual_variance = -1
        within_condition = 0.5
        want = 4

        # Act
        got = get_rating(actual_variance, within_condition)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_negative_within_condition_between_1_and_2(self):
        # Arrange
        actual_variance = -1
        within_condition = 1.5
        want = 3

        # Act
        got = get_rating(actual_variance, within_condition)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_negative_within_condition_between_2_and_3(self):
        # Arrange
        actual_variance = -1
        within_condition = 2.5
        want = 2

        # Act
        got = get_rating(actual_variance, within_condition)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_negative_within_condition_above_3(self):
        # Arrange
        actual_variance = -1
        within_condition = 3.5
        want = 1

        # Act
        got = get_rating(actual_variance, within_condition)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_zero_within_condition_within_1(self):
        # Arrange
        actual_variance = 0
        within_condition = 1
        want = 5

        # Act
        got = get_rating(actual_variance, within_condition)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_negative_within_condition_exactly_2(self):
        # Arrange
        actual_variance = -1
        within_condition = 2
        want = 3

        # Act
        got = get_rating(actual_variance, within_condition)

        # Assert
        self.assertEqual(want, got)

    def test_actual_variance_negative_within_condition_exactly_3(self):
        # Arrange
        actual_variance = -1
        within_condition = 3
        want = 2

        # Act
        got = get_rating(actual_variance, within_condition)

        # Assert
        self.assertEqual(want, got)
