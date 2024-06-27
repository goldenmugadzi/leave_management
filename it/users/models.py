from django.db import models
from datetime import date
import random
import time
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.hashers import make_password, check_password

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


class Application(models.Model):
    name = models.CharField(max_length=100, unique=True)
    fullname = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.name


class Roles(models.Model):
    role = models.CharField(max_length=100)
    name = models.CharField(max_length=100)
    description = models.CharField(max_length=400)
    application = models.CharField(max_length=100)
    app_id = models.ForeignKey(Application, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.role

    class Meta:
        app_label = 'users'


class Designations(models.Model):
    identifier = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=100, blank=True)
    chk = models.CharField(max_length=100, blank=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.identifier

    class Meta:
        app_label = 'users'

class CostCenter(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True)

    class Meta:
        ordering = ['id']

    def __str__(self):
        return self.id

    def get_all_children(self):
        children = list(self.children.all())
        return children
    
    def get_all_ancestors(self):
        ancestors = []
        if self.parent:
            ancestors.append(self.parent)
            ancestors += self.parent.get_all_ancestors()
        return ancestors
    def get_all_ancestors_and_their_children(self):
            """
            Returns a list of all ancestors and their children for the current instance.

            Ancestors are determined by the parent attribute of each instance.
            Children are determined by calling the get_all_children method.

            Returns:
                list: A list of all ancestors and their children.
            """
            ancestors = []
            if self.parent:
                ancestors.append(self.parent)
                ancestors += self.parent.get_all_ancestors_and_their_children()
            children = self.get_all_children()
            return ancestors  + children

class UserProfile(AbstractUser):
    username = models.CharField(max_length=15, unique=True, verbose_name='EC Number',db_index=True)
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.DO_NOTHING, blank=True, null=True)
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
    
    def get_user_roles_for_application(self, application_name):
        # Filter the user's roles for the specific application
        application = Application.objects.filter(name=application_name).first()

        if application:
            user_roles = self.roles.filter(app_id=application.id)
            
            # Return the roles if any exist
            if user_roles.exists():
                return user_roles[0].role
        else:
            return None
    
    def get_user_role_for_application(self, application_name):
        # Filter the user's roles for the specific application
        application = Application.objects.filter(name=application_name).first()

        if application:
            user_roles = self.roles.filter(app_id=application.id)
            
            # Return the roles if any exist
            if user_roles.exists():
                return user_roles[0]
        else:
            return None


class Notification(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    message = models.TextField()
    is_read = models.BooleanField(default=False)
    url = models.CharField(max_length=250)
    notification_type = models.CharField(max_length=100, blank=True, null=True)
    notification_id = models.CharField(max_length=100, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.message

    class Meta:
        app_label = 'users'


class Supplier(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    name = models.CharField(max_length=100, unique=True, blank=True, null=True)
    email = models.EmailField(blank=True, null=True)
    phone = models.IntegerField(blank=True, null=True)
    address = models.CharField(max_length=100, blank=True, null=True)

    class Meta:
        ordering = ['name'] 

    def __str__(self):
        return self.name

    def save(self, *args, **kwargs):
        if not self.id:
            timestamp = str(int(time.time()))
            random_number = str(random.randint(10000, 99999))
            self.id = "splr" + timestamp + random_number
        super().save(*args, **kwargs)
        
class Question(models.Model):
    question = models.CharField(max_length=255)
    question_name = models.CharField(max_length=255)

    def __str__(self):
        return self.question

    class Meta:
        app_label = 'users'
class SecurityQuestions(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE)
    security_question = models.ForeignKey(Question, on_delete=models.CASCADE)
    security_answer = models.CharField(max_length=255)

    def set_security_answers(self, answer):
        self.security_answer = make_password(answer)

    def check_security_answers(self, answer):
        return check_password(answer, self.security_answer)
