from django.db import models

# Create your models here.
class ControllerInstruction(models.Model):
    
    cif_id = models.CharField(max_length=50)
    district_or_station = models.CharField(max_length=100, blank=True)
    instruction_by = models.CharField(max_length=100, blank=True)
    instruction_to = models.CharField(max_length=100, blank=True)
    received_at = models.DateField()
    related_equipment = models.CharField(max_length=200)
    time_at = models.TimeField(blank=True, null=True)
    created_at = models.DateField()
    
class Instruction(models.Model):
    
    cif_id = models.CharField(max_length=50)
    description = models.CharField(max_length=200)
    completed_status = models.BooleanField()
    completed_by = models.CharField(max_length=100)
    completed_at = models.DateField(blank=True)
    created_at = models.DateField()
    
class PermitToWork(models.Model):
    
    cif_id = models.CharField(blank=True,max_length=50)
    ptw_id = models.CharField(blank=True,max_length=50)
    hr_number = models.CharField(blank=True,max_length=50)
    local_number = models.CharField(blank=True,max_length=50)
    ncc_number = models.CharField(blank=True,max_length=50)
    
    comments = models.CharField(blank=True,max_length=300)
    
    serial_number = models.CharField(blank=True,max_length=100)
    issue_to = models.CharField(blank=True,max_length=100)
    employ_of = models.CharField(blank=True,max_length=100)
    work_done = models.CharField(blank=True,max_length=300)
    plant_equipment = models.CharField(blank=True,max_length=100)
    points_of_isolation = models.CharField(blank=True,max_length=300)
    nearest_points_live = models.CharField(blank=True,max_length=100)
    circuit_main_earths = models.CharField(blank=True,max_length=100)
    danger_notices = models.CharField(blank=True,max_length=100)
    caution_notices = models.CharField(blank=True,max_length=100)
    special_keys = models.CharField(blank=True,max_length=100)
    other_precautions = models.CharField(blank=True,max_length=100)
    additional_earths = models.CharField(blank=True,max_length=100)
    circuit_identity_wristlets = models.CharField(blank=True,max_length=100)
    workers = models.CharField(blank=True,max_length=200)
    
    responsible_official = models.CharField(blank=True,max_length=100)
    official_signature = models.BooleanField(blank=True, null=True)
    official_time = models.TimeField(blank=True, null=True)
    official_date = models.DateField(blank=True, null=True)
    
    recipt_person = models.CharField(blank=True,max_length=100)
    recipt_person_signature = models.BooleanField(blank=True, null=True)
    recipt_person_time = models.TimeField(blank=True, null=True)
    recipt_person_date = models.DateField(blank=True, null=True)
    
    clearance_person = models.CharField(blank=True,max_length=100)
    clearance_signature = models.BooleanField(blank=True, null=True)
    clearance_time = models.TimeField(blank=True, null=True)
    clearance_date = models.DateField(blank=True, null=True)
    
    snr_cancellation_person = models.CharField(blank=True,max_length=100)
    snr_cancellation_signature = models.BooleanField(blank=True, null=True)
    snr_cancellation_time = models.TimeField(blank=True, null=True)
    snr_cancellation_date = models.DateField(blank=True, null=True)
    
    official_cancellation_person = models.CharField(blank=True,max_length=100)
    official_cancellation_signature = models.BooleanField(blank=True, null=True)
    official_cancellation_time = models.TimeField(blank=True, null=True)
    official_cancellation_date = models.DateField(blank=True, null=True)
    
    indirect_issue = models.BooleanField(blank=True, null=True)
    indirect_competent = models.CharField(blank=True,max_length=100)
    indirect_senior = models.CharField(blank=True,max_length=100)
    indirect_signature = models.BooleanField(blank=True, null=True)
    indirect_time = models.TimeField(blank=True, null=True)
    indirect_date = models.DateField(blank=True, null=True)
    
    indirect_clearance = models.BooleanField(blank=True, null=True)
    indirect_clr_competent = models.CharField(blank=True,max_length=100)
    indirect_clr_senior = models.CharField(blank=True,max_length=100)
    indirect_clr_signature = models.BooleanField(blank=True, null=True)
    indirect_clr_time = models.TimeField(blank=True, null=True)
    indirect_clr_date = models.DateField(blank=True, null=True)   
    
    created_by = models.CharField(blank=True,max_length=50)
    time_at = models.TimeField(blank=True, null=True)
    created_at = models.DateField(blank=True,)
    
class WorkerDeclaration(models.Model):
    worker_username = models.CharField(max_length=50)    
    ptw_id = models.CharField(max_length=50)
    signature_safe = models.BooleanField(blank=True, null=True)
    signature_safe_path = models.CharField(max_length=400)
    signature_not_safe = models.BooleanField(blank=True, null=True)
    signature_not_safe_path = models.CharField(max_length=400)
    time_safe = models.TimeField(blank=True, null=True)
    date_safe = models.DateField(blank=True, null=True)
    time_not_safe = models.TimeField(blank=True, null=True)
    date_not_safe = models.DateField(blank=True, null=True) 
    created_at = models.DateField(blank=True, null=True)
    
    