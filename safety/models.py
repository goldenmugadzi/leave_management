from django.db import models
import random
import time
from it.users.models import UserProfile, CostCenter

class ControllersInstructionForm(models.Model):
   id = models.CharField(primary_key=True, max_length=20, editable=False)
   district_station = models.ForeignKey(CostCenter, on_delete=models.SET_NULL, null=True, blank=True)
   issued_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='issued_instructions')
   received_by = models.ForeignKey(UserProfile, on_delete=models.SET_NULL, null=True, related_name='received_instructions')
   issued_at = models.DateTimeField(auto_now_add=True)

   class Meta:
      verbose_name = "Controller's Instruction Form"
      verbose_name_plural = "Controller's Instruction Forms"

   def __str__(self):
      return f"Instruction Form #{self.id} - {self.district_station}"
   def save(self, *args, **kwargs):
      if not self.id:
         # Format: SAF + YYYYMMDD + 4 random digits, e.g. SAF202504234343
         date_str = time.strftime("%Y%m%d")
         random_number = str(random.randint(1000, 9999))
         self.id = f"SAF{date_str}{random_number}"
      super().save(*args, **kwargs)


class Instruction(models.Model):
    form = models.ForeignKey(ControllersInstructionForm, on_delete=models.CASCADE, related_name='entries')
    instruction = models.CharField(help_text="Instruction issued",max_length=500)
    received= models.TimeField(help_text="Time when the instruction was received", null=True, blank=True)
    completed = models.TimeField(help_text="Time when the instruction was completed", null=True, blank=True)

    def __str__(self):
        return f"{self.year}-{self.month:02d} Safety Report"

class AccidentReport(models.Model):
    Severity_Of_Accident = [
        ('First aid case', 'First aid case'),
        ('Medical treatment', 'Medical treatment'),
        ('Non lost time injury', 'Non lost time injury'),
        ('Lost time injury', 'Lost time injury'),
        ('Fatal', 'Fatal'),
        #('Non fatal', 'Non fatal'),
    ]
    Nature_of_Accidents = [
        ('Electrical', 'Electrical'),
        ('Non_electrical', 'Non_electrical'),
        #('Road traffic', 'Road traffic'),
    ]
    Nature_of_injury = [
        ('Major', 'Major'),
        ('Minor','Minor'),
    ]
    Voltage = [
        ('11kv', '11kv'),
        ('33kv','33kv'),
    ]
    Risk_Assessment = [
        ('Yes','Yes'),
        ('No' ,'No'),
    ]
    Safety_Preparation = [
         ('Yes','Yes'),
         ('No' ,'No'),
    ]
    Sex = [
         ('Male','Male'),
         ('Female' ,'Female'),
    ]
    
    employee_involved = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,related_name="accident_reports")
    department = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    sex = models.CharField(max_length=300 ,choices=Sex)
    address_of_person_involved = models.CharField(max_length=500)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    age = models.PositiveIntegerField(default=0)
    date_of_accident = models.DateField()
    time_of_accident  = models.TimeField()
    authority_received_datetime = models.DateTimeField( verbose_name="Date and Time Report Was Received by Authority")
    authority_received_from = models.CharField(max_length=255,verbose_name="Name of Person Who Reported to Authority")
    police_received_datetime = models.DateTimeField(verbose_name="Date and Time Report Was Received by Police" )
    police_received_from = models.CharField(max_length=255, verbose_name="Name of Person Who Reported to Police")
    cost_center = models.ForeignKey(CostCenter, on_delete=models.CASCADE, blank=True, null=True)
    ec_number = models.CharField(max_length=500)
    severity_Of_Accident  = models.CharField(max_length=500, choices=Severity_Of_Accident )
    nature_of_accident = models.CharField(max_length=600, choices=Nature_of_Accidents)
    nature_of_injury = models.CharField(max_length=400, choices=Nature_of_injury)
    circumstance_leading_to_accident = models.TextField(max_length=700)
    location_of_accident_giving_line_and_section_number = models.TextField(max_length=800)
    risk_assessment_carried_out = models.CharField(max_length=800 ,choices=Risk_Assessment)
    operation_of_protective_devices = models.TextField(max_length=600)
    attach_photographs = models.ImageField(upload_to='accident_photos/', blank=True, null=True)
    steps_taken_on_the_short_term = models.CharField(max_length=700)
    safety_preparation_carried_out = models.CharField(max_length=900,choices=Safety_Preparation)
    attach_written_statements = models.ImageField(upload_to='accident_photos/', blank=True, null=True)
    other_information_considered_neccesary = models.TextField(max_length=600)
    for_electrical_state_voltage = models.TextField(max_length=600,choices=Voltage)
 
       
    
    
class VehicleAccidentReport(models.Model):
    
    Hired = [
        ('Yes','Yes'),
        ('No' ,'No'),
    ]
    # 1. Driver's Details
    driver_name = models.CharField(max_length=100)
    home_address = models.TextField()
    age = models.PositiveIntegerField()
    drivers_license = models.CharField(max_length=50)
    designation = models.CharField(max_length=100)
    place_of_issue = models.CharField(max_length=100)
    date_of_issue = models.DateField()
    ec_number = models.CharField(max_length=50)
    work_station = models.CharField(max_length=100)

    # 2. Vehicle Details
    make = models.CharField(max_length=100)
    registration_number = models.CharField(max_length=50)
    fleet_number = models.CharField(max_length=50)
    allocation_to_section = models.CharField(max_length=100)
    state_if_hired = models.TextField(max_length=600,choices=Hired)

    # 3. Particulars of Accident
    datetime_for_accident = models.DateTimeField( verbose_name="Date and Time of Accident")
    place_of_accident = models.CharField(max_length=150)
    brief_description = models.TextField()
    datetime_to_police = models.DateTimeField( verbose_name="Date and Time Accident was reported to police")
    speed_at_time_of_accident = models.PositiveIntegerField(default=0)
    gear_used = models.PositiveIntegerField(default=0)
    type_and_state_of_road = models.CharField(max_length=150)
    state_of_weather = models.CharField(max_length=150)
    nature_and_weight_of_load = models.CharField(max_length=150)
    name_and_address_of_passenger = models.TextField()

    # 4. Damaged Property Details
    name_and_address_of_driver= models.CharField(max_length=100)
    other_vehicle_owner_name = models.CharField(max_length=100)
    other_vehicle_owner_address = models.TextField()
    other_vehicle_make_and_type = models.CharField(max_length=100)
    other_vehicle_registration_number = models.CharField(max_length=50)
    approximate_speed_of_other_vehicle = models.CharField(max_length=50, blank=True, help_text="e.g., '60 km/h'")

    # 5. Damage to Property Details
    zesa_vehicle_damage = models.TextField(blank=True)
    other_vehicle_damage = models.TextField(blank=True)
    other_property_damage = models.TextField(blank=True)

    # 6. Reports
    drivers_report = models.TextField()
    section_head_comments = models.TextField()

    date_submitted = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Vehicle Accident Report - {self.driver_name} - {self.date_of_accident}"

class PropertyLossIncident(models.Model):
    # Property/Asset details
    full_description_of_property = models.TextField("Full Description of Property or Asset Damaged")
    address_of_loss = models.CharField("Address Where Loss Occurred", max_length=500)
    date_time_of_loss = models.DateTimeField("Date and Time of Loss")
    
    # Reporting details
    zetdc_report_received_datetime = models.DateTimeField("Date and Time Report Was Received by ZETDC")
    zetdc_report_received_from = models.CharField("Name of Person Who Reported to ZETDC", max_length=255)
    zrp_report_received_datetime = models.DateTimeField("Date and Time Report Was Received by ZRP")
    zrp_report_received_from = models.CharField("Name of Person Who Reported to ZRP", max_length=255, blank=True)
    description_file = models.FileField("Attach File for Full Description of Damaged Property", upload_to='property_loss/', blank=True, null=True)

    # Person injured (optional, can be blank if not applicable)
    person_injured_name = models.CharField("Name of Injured Person", max_length=255, blank=True)
    person_injured_address = models.CharField("Address of Injured Person", max_length=500, blank=True)
    person_injured_age = models.PositiveIntegerField("Age of Injured Person", blank=True, null=True)
    injuries_sustained = models.TextField("Injuries Sustained", blank=True)
    condition_of_victim = models.CharField("Condition of Victim", max_length=255, blank=True)
    location_of_medical_practitioner = models.CharField("Location of Medical Practitioner", max_length=255, blank=True)
    medical_opinion_recovery_period = models.CharField("Medical Practitioner Opinion for Recovery Period", max_length=255, blank=True)

    # Incident details
    circumstances_leading_to_incident = models.TextField("Circumstances Leading to the Incident")
    network_circuit_details = models.TextField(
        "Network Circuit (11kv feeder, 11/0.4kv substation number, MV circuit number, phase)", blank=True
    )
    operation_of_protective_devices = models.TextField("Operation of Any Protective Devices", blank=True)
    site_details = models.TextField(
        "Relevant Details of the Site (height/position of conductor, ground clearance, earth resistance, voltage resistance, illegal connections, security of substation)",
        blank=True
    )

    # Attachments
    written_statements = models.FileField("Attach Written Statements", upload_to='property_loss/statements/', blank=True, null=True)
    photographs = models.ImageField("Attach Photographs", upload_to='property_loss/photos/', blank=True, null=True)

    # Opinions and other info
    opinion_on_cause_and_liability = models.TextField("Opinion on the Cause of the Loss and Liability", blank=True)
    other_information = models.TextField("Any Other Information Considered Necessary", blank=True)

    # Reporting
    reported_by = models.CharField("Reported By", max_length=255)
    date_of_report = models.DateField("Date of the Report", auto_now_add=True)

    def __str__(self):
        return f"Property Loss Incident at {self.address_of_loss} on {self.date_time_of_loss:%Y-%m-%d %H:%M}"




