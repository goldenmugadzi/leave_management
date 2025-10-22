from django.db import models
from django.core.validators import RegexValidator
from it.users.models import Regions, Sections, UserProfile

# Validator to prevent XSS at model level
no_script_validator = RegexValidator(
    regex=r'<script|javascript:|on\w+\s*=',
    message='Potentially malicious content detected. Script tags and JavaScript are not allowed.',
    inverse_match=True,
    flags=0
)

# Create your models here.
class OrganisationalCharts(models.Model):
    name = models.CharField(max_length=100)
    image = models.ImageField(upload_to='charts/')
    office = models.CharField(max_length=100)

    def __str__(self):
        return self.name
    

class Category(models.Model):
    name = models.CharField(max_length=100,unique=True)

    class Meta:
        verbose_name_plural = 'categories'

    def __str__(self):
        return self.name

class Subcategory(models.Model):
    category = models.ForeignKey(Category,on_delete=models.CASCADE,related_name='subtype')
    # section = models.ForeignKey(Sections, on_delete=models.CASCADE)
    name = models.CharField(max_length=100, validators=[no_script_validator])

    
    def __str__(self):
        return self.name 

class Document(models.Model):
    category = models.ForeignKey(Category, on_delete=models.CASCADE)
    subcategory = models.ForeignKey(Subcategory, on_delete=models.CASCADE)
    name = models.CharField(
        max_length=100, 
        blank=True, 
        null=True,
        validators=[no_script_validator],
        help_text='Document name (script tags not allowed)'
    )
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    archive = models.BooleanField(default=False)
    file = models.FileField()
    created_by = models.ForeignKey(UserProfile, on_delete = models.DO_NOTHING, blank = True, null = True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class Vacancies(models.Model):
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)
    department = models.ForeignKey(Sections, on_delete=models.CASCADE)
    archive = models.BooleanField(default=False)
    file = models.FileField()
    name = models.CharField(max_length=100, blank = True, null = True, validators=[no_script_validator])
    uploaded_by = models.ForeignKey(UserProfile, on_delete = models.DO_NOTHING, blank = True, null = True)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name