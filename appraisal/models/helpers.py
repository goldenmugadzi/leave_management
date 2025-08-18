from django.db import models
from helpers.models.timestamp import TimeStamp

class QuarterChoices(models.IntegerChoices):
    Q1 = 1, "1st"
    Q2 = 2, "2nd"
    Q3 = 3, "3rd"
    Q4 = 4, "4th"

def get_year_choices():
    return [(year, str(year)) for year in range(2000, 2050)]

class YearQuarter(TimeStamp):
    """
    Represents a quarter within a specific year.

    This model stores information about a single quarter in a given year, 
    providing the quarter number (1st to 4th) and the year itself. The `quarter` 
    field is constrained to values 1, 2, 3, or 4, representing the four quarters 
    in a year.

    Attributes:
        year (int): The year for which the quarter is defined.
        quarter (int): The quarter of the year (1, 2, 3, or 4).

    """
    year = models.PositiveIntegerField(choices=get_year_choices()) 
    quarter = models.PositiveIntegerField(choices=QuarterChoices.choices)

    def __str__(self):
        return f"Year {self.year} - Q{self.quarter}"

    class Meta:
        unique_together = ('year', 'quarter')