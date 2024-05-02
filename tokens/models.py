from django.db import models
from it.users.models import UserProfile
from approve.models import Process
from django.core.validators import RegexValidator
import random
import time


class Meter(models.Model):
    number = models.CharField(primary_key=True, max_length=11)
    kilowatt_hours = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    type_choices = [('Single phase', 'Single phase'), ('Three phase', 'Three phase')]
    type = models.CharField(max_length=100, blank=True, null=True, choices=type_choices, default='Single phase')

    def __str__(self):
        return str(self.number)

class Customer(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200)
    contact_number = models.CharField(max_length=10, validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')])

    def __str__(self):
        return self.name

class Token(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, blank=True, null=True)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    process=models.ForeignKey(Process, on_delete=models.CASCADE, blank=True, null=True)
    choices = [('REIMBURSEMENT', 'REIMBURSEMENT'), ('CLEAR CREDIT', 'CLEAR CREDIT'), ('TAMPER TOKEN', 'TAMPER TOKEN')]
    kind = models.CharField(max_length=100, blank=True, null=True, choices=choices)
    def __str__(self):
        return str(self.meter.meter_number)
    def save(self, *args, **kwargs):
        timestamp = str(int(time.time()))
        random_number = str(random.randint(10000, 99999))
        self.id = "TKN" + timestamp + random_number
        super().save(*args, **kwargs)

class Fault(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return f"Fault: {self.temper_token}"
class Pernalt(models.Model):
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receipt = models.FileField(upload_to='uploads/Tokens/Token/receipt', blank=True, null=True)
    
    def __str__(self):
        return str(self.amount)

class Reconnection(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return f"Re-Imbursement: {self.temper_token}"

class Recover(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE, blank=True, null=True)
    description = models.TextField(max_length=400)

    def __str__(self):
        return f"Recovered: {self.temper_token}"
