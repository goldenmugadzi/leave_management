from django.db import models
from it.users.models import UserProfile
from approve.models import Process
from django.core.validators import RegexValidator
import random
import time


class Meter(models.Model):
    number = models.CharField(max_length=11, blank=True,null=True , validators=[RegexValidator(r'\d{11}$', 'Enter a valid Meter number.')])
    kilowatt_hours = models.DecimalField(max_digits=11, decimal_places=2, default=0)
    phase = models.CharField(max_length=100, blank=True, null=True, choices= [('Single phase', 'Single phase'), ('Three phase', 'Three phase')], default='Single phase')

    def __stsr__(self):
        return str(self.number)

class Customer(models.Model):
    name = models.CharField(max_length=100)
    address = models.CharField(max_length=200 , blank=True,null=True )
    stand_number = models.CharField(max_length=100 , blank=True,null=True )
    contact_number = models.CharField(max_length=10, blank=True,null=True , validators=[RegexValidator(r'^\+?1?\d{9,15}$', 'Enter a valid phone number.')])

    def __str__(self):
        return self.name

class Token(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    meter = models.ForeignKey(Meter, on_delete=models.CASCADE, blank=True, null=True)
    reason = models.TextField(max_length=400)
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True, blank=True, null=True)
    process=models.ForeignKey(Process, on_delete=models.CASCADE, blank=True, null=True)
    choices = [('REIMBURSEMENT', 'REIMBURSEMENT'), ('CLEAR CREDIT', 'CLEAR CREDIT'), ('TAMPER TOKEN', 'TAMPER TOKEN')]
    type = models.CharField(max_length=100, blank=True, null=True, choices=choices)
    def __str__(self):
        return str(self.meter.meter_number)
    
    def save(self, *args, **kwargs):
        timestamp = str(int(time.time()))
        random_number = str(random.randint(10000, 99999))
        self.id = "TKN" + timestamp + random_number
        super().save(*args, **kwargs)

class REIMBURSEMENT(models.Model):
    purpose = models.CharField(max_length=15, choices=[ ('Faulty Meter', 'Faulty Meter'), ('Recovered Meter', 'Recovered Meter'), ('Old Token', 'Old Token') ])
    token = models.ForeignKey(Token, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return f"Fault: {self.token}"
class CLEARCREDIT(models.Model):
    penalty = models.CharField(max_length=3, default="No", choices=[ ('No', 'No'), ('Yes', 'Yes'), ])
    amount = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    receipt = models.FileField(upload_to='uploads/Tokens/Token/receipt', blank=True, null=True)
    def __str__(self):
        return str(self.amount)

class TAMPERTOKEN(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE, blank=True, null=True)
    purpose = models.CharField(max_length=15, choices=[('Fauty Meter', 'Fauty Meter'),('Recovered Meter', 'Recovered Meter'),("Old Token","Old Token" ),])
    def __str__(self):
        return f"TAMPERTOKEN: {self.token}"

class OldToken(models.Model):
    old_token = models.ImageField(upload_to='uploads/Tokens/oldToken', blank=True, null=True)
    reimbursement = models.ForeignKey(REIMBURSEMENT, on_delete=models.CASCADE, blank=True, null=True)
    def __str__(self):
        return f"OldToken: {self.old_token}"
class FaultMeter(models.Model):
    reimbursement = models.ForeignKey(REIMBURSEMENT, on_delete=models.CASCADE, blank=True, null=True)
    units = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    photo= models.ImageField(upload_to='uploads/Tokens/faultMeter', blank=True, null=True)

class RecoveredMeter(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE, blank=True, null=True)
    photo= models.ImageField(upload_to='uploads/Tokens/RecoveredMeter', blank=True, null=True)
class FaultMaintanance(models.Model):
    photo = models.FileField(upload_to='uploads/Tokens/FaultMaintanance', blank=True, null=True)
    units = models.DecimalField(max_digits=10, decimal_places=2, default=0)
class Reconnection(models.Model):
    invoice = models.FileField(upload_to='uploads/Tokens/Reconnection/Invoice', blank=True, null=True)
    proof_of_payment = models.FileField(upload_to='uploads/Tokens/Reconnection/ProofOfPayment', blank=True, null=True)
