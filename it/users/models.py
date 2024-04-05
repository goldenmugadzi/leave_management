from django.db import models
from datetime import date
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin, BaseUserManager


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)

class Regions(models.Model):
    region = models.CharField(max_length=100)
    code = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.region

    class Meta:
        app_label = 'users'
class Districts(models.Model):
    district = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    region_id = models.CharField(max_length=100)

    def __str__(self):
        return self.district

    class Meta:
        app_label = 'users'


class Sections(models.Model):
    section = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    district_id = models.CharField(max_length=100)
    region_id = models.CharField(max_length=100)

    def __str__(self):
        return self.section

    class Meta:
        app_label = 'users'


class Depots(models.Model):
    depot = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)

    def __str__(self):
        return self.depot

    class Meta:
        app_label = 'users'


class Roles(models.Model):
    role = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    application = models.CharField(max_length=100)

    def __str__(self):
        return self.role

    class Meta:
        app_label = 'users'


class Designations(models.Model):
    identifier = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=100, blank=True)
    chk = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.identifier

    class Meta:
        app_label = 'users'


class UserProfile(AbstractUser):
    username = models.CharField(max_length=15, unique=True, verbose_name='EC Number')
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    depot = models.ForeignKey(Depots, on_delete=models.DO_NOTHING, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.DO_NOTHING, blank=True, null=True)
    roles = models.ManyToManyField(Roles, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=30, blank=True)
    last_reset = models.DateField(default=date.today())

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.first_name} {self.last_name}"
        else:
            return self.username
   
class Notification(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    is_read = models.BooleanField(default=False)
    url = models.CharField(max_length=250)

    def __str__(self):
        return self.message

    class Meta:
        app_label = 'users'
