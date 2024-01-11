# app/models.py
from django.db import models

class MeterToken(models.Model):
    created_by = models.CharField(max_length=100)
    customer_name = models.CharField(max_length=100)
    customer_address = models.CharField(max_length=200)
    token_number = models.CharField(max_length=50)
    date_purchased = models.DateField()
    reason = models.CharField(max_length=100)

    def __str__(self):
        return self.token_number
