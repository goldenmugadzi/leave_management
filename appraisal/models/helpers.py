from django.db import models

class QuarterChoices(models.IntegerChoices):
    Q1 = 1, "1st"
    Q2 = 2, "2nd"
    Q3 = 3, "3rd"
    Q4 = 4, "4th"