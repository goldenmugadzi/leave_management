from django.db import models
from it.users.models import UserProfile,Regions,Sections,CostCenter
from approve.models import Process,Step,Workflow,Approval
from django.core.validators import RegexValidator
import random
import time


class Meter(models.Model):
    number = models.CharField(max_length=11)
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
    reason = models.TextField(max_length=400,blank=True, null=True,help_text="Description")
    customer = models.ForeignKey(Customer, on_delete=models.CASCADE, blank=True, null=True)
    created_by = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    process=models.ForeignKey(Process, on_delete=models.CASCADE, blank=True, null=True)
    cost_center=models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
     
    token_photo = models.FileField(upload_to='uploads/Tokens/generatedtoken',help_text="photo of generated token " , blank=True, null=True)
    type = models.CharField(max_length=100,help_text="Type of Token",  choices=[('REIMBURSEMENT', 'REIMBURSEMENT') , ('CLEAR CREDIT', 'CLEAR CREDIT'), ('TEMPER', 'TEMPER')])
    def __str__(self):
        return str(self.id)
    
    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "TKN" + timestamp + random_number
        super().save(*args, **kwargs)

class REIMBURSEMENT(models.Model):
    purpose = models.CharField(max_length=15,help_text="Why?", blank=True, null=True,choices=[ ('Faulty Meter', 'Faulty Meter'), ('Recovered Meter', 'Recovered Meter'), ('Old Token', 'Old Token') ])
    units = models.DecimalField(max_digits=10, decimal_places=2, help_text="kilowatt hours to be reimbursed", default=0)
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    def __str__(self):
        return str(self.token.meter.number)
class CLEARCREDIT(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    amount = models.DecimalField(max_digits=10,help_text="amount paid to clear credit", decimal_places=2, null=True, blank=True)
    receipt = models.FileField(upload_to='uploads/Tokens/Token/receipt',help_text="a photo of the receipt as proof of payment", blank=True, null=True)
    def __str__(self):
        return str(self.token.meter.number)

class TAMPERTOKEN(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    is_for = models.CharField(max_length=25,blank=True,null=True,help_text="Why?",choices=[('Fault Maintenance', 'Fault Maintenance'),('Recovered Meter', 'Recovered Meter'),('Reconnection', 'Reconnection'),])
    def __str__(self):
        token = getattr(self, 'token', None)
        meter = getattr(token, 'meter', None) if token else None
        meter_number = getattr(meter, 'number', 'N/A') if meter else 'N/A'
        return f"{meter_number} - {self.is_for}"

class OldToken(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    old_token = models.FileField(upload_to='uploads/Tokens/oldToken',help_text="photo of old token" , blank=True, null=True)
    def __str__(self):
        return str(self.id)
class FaultMeter(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    units = models.DecimalField(max_digits=10, decimal_places=2, help_text="kilowatt hours remaining", default=0)
    photo= models.FileField(upload_to='uploads/Tokens/faultMeter',help_text="Meter photo showing showing units ", blank=True, null=True)
    def __str__(self):
        return str(self.token)
    
class RecoveredMeter(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    picture= models.FileField(upload_to='uploads/Tokens/RecoveredMeter',help_text="Meter photo showing nill credit", blank=True, null=True)
    def __str__(self):
        return str(self.token.meter.number)
class FaultMaintanance(models.Model): 
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    photo= models.FileField(upload_to='uploads/Tokens/FaultMaintanance',help_text="Evidence of fault ", blank=True, null=True)
    def __str__(self):
        return str(self.token.meter.number)

class Reconnection(models.Model):
    token = models.ForeignKey(Token, on_delete=models.CASCADE)
    invoice = models.FileField(upload_to='uploads/Tokens/Reconnection/Invoice',help_text="invoice is issued to request payment", blank=True, null=True)
    proof_of_payment = models.FileField(upload_to='uploads/Tokens/Reconnection/ProofOfPayment',help_text="proof_of_payment serves as proof of payment", blank=True, null=True)
    def __str__(self):
        return str(self.token.meter.number)
