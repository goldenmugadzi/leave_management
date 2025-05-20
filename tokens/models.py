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

class Attachment(models.Model):
    file = models.FileField(upload_to='uploads/Tokens/attachments',help_text="Add attachments")
    def __str__(self):
        return str(self.token.meter.number)
    
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
    additional_attachments=models.ManyToManyField(Attachment, blank=True, null=True)
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
    is_for = models.CharField(max_length=25, blank=True, null=True,help_text=" Why?" ,choices=[('Fauty Maintanance', 'Fauty Maintanance'),('Recovered Meter', 'Recovered Meter'),("Reconnection","Reconnection" ),])
    def __str__(self):
        return str(self.token.meter.number)

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
        return str(self.token.meter.number)
    
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

from rest_framework.decorators import api_view
from rest_framework.response import Response
from rest_framework import status

@api_view(['POST'])
def create_token_api(request):
    from it.users.models import UserProfile
    from .models import Attachment, CLEARCREDIT, OldToken, FaultMeter, RecoveredMeter, FaultMaintanance, Reconnection

    serializer = TokenSerializer(data=request.data)
    if serializer.is_valid():
        try:
            created_by = UserProfile.objects.get(id=65)
        except UserProfile.DoesNotExist:
            return Response({'error': 'Default user not found.'}, status=status.HTTP_400_BAD_REQUEST)
        token = serializer.save(created_by=created_by)

        # Handle multiple file uploads for additional_attachments
        files = request.FILES.getlist('additional_attachments')
        for file in files:
            attachment = Attachment.objects.create(file=file)
            token.additional_attachments.add(attachment)

        # Handle CLEARCREDIT receipt
        if 'receipt' in request.FILES:
            CLEARCREDIT.objects.create(
                token=token,
                amount=request.data.get('amount'),
                receipt=request.FILES['receipt']
            )

        # Handle OldToken file
        if 'old_token' in request.FILES:
            OldToken.objects.create(
                token=token,
                old_token=request.FILES['old_token']
            )

        # Handle FaultMeter photo
        if 'faultmeter_photo' in request.FILES:
            FaultMeter.objects.create(
                token=token,
                units=request.data.get('units', 0),
                photo=request.FILES['faultmeter_photo']
            )

        # Handle RecoveredMeter picture
        if 'recoveredmeter_picture' in request.FILES:
            RecoveredMeter.objects.create(
                token=token,
                picture=request.FILES['recoveredmeter_picture']
            )

        # Handle FaultMaintanance photo
        if 'faultmaintanance_photo' in request.FILES:
            FaultMaintanance.objects.create(
                token=token,
                photo=request.FILES['faultmaintanance_photo']
            )

        # Handle Reconnection files
        if 'reconnection_invoice' in request.FILES or 'reconnection_proof_of_payment' in request.FILES:
            Reconnection.objects.create(
                token=token,
                invoice=request.FILES.get('reconnection_invoice'),
                proof_of_payment=request.FILES.get('reconnection_proof_of_payment')
            )

        return Response(TokenSerializer(token).data, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
