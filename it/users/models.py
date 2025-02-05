from django.db import models
from datetime import date
import random
import time
from django.contrib.auth.models import AbstractUser
from django.contrib.auth.models import BaseUserManager
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError


class UserManager(BaseUserManager):
    def create_user(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', False)
        extra_fields.setdefault('is_superuser', False)
        user = self.model(username=username, **extra_fields)
        try:
            validate_password(password, user=user)
            user.set_password(password)
            user.save(using=self._db)
            return user
            # Password is valid
        except ValidationError as e:
            # Password is not valid
            print(e.messages)
            return None

    def create_superuser(self, username, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        return self.create_user(username, password, **extra_fields)


class Regions(models.Model):
    region = models.CharField(max_length=100)
    code = models.CharField(max_length=100, blank=True)

    def __str__(self):
        return self.region


class Districts(models.Model):
    district = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    region_id = models.CharField(max_length=100)

    def __str__(self):
        return self.district


class Sections(models.Model):
    section = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    district_id = models.CharField(max_length=100)
    region_id = models.CharField(max_length=100)

    def __str__(self):
        return self.section


class Depots(models.Model):
    depot = models.CharField(max_length=100)
    code = models.CharField(max_length=100)
    district = models.ForeignKey(Districts, on_delete=models.CASCADE)
    region = models.ForeignKey(Regions, on_delete=models.CASCADE)

    def __str__(self):
        return self.depot


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
        return f"{self.name}"


class Designations(models.Model):
    identifier = models.CharField(max_length=100, blank=True)
    description = models.CharField(max_length=100, blank=True)
    chk = models.CharField(max_length=100, blank=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)

    def __str__(self):
        return self.identifier


class CostCenter(models.Model):
    id = models.CharField(primary_key=True, max_length=20, editable=False)
    code = models.CharField(max_length=30)
    name = models.CharField(max_length=100, blank=True, null=True)
    parent = models.ForeignKey('self', on_delete=models.CASCADE, blank=True, null=True, related_name='children')

    class Meta:
        ordering = ['parent__id']

    def get_all_children(self):
        children = list(self.children.all())
        return children

    def get_decendance(self):
        def _get_all_descendants(node):
            descendants = node.children.all()
            for child in descendants:
                descendants |= _get_all_descendants(child)
            return descendants

        descendants = _get_all_descendants(self)
        return descendants | self.__class__.objects.filter(pk=self.pk)

    def get_all_ancestors(self):
        ancestors = []
        current = self
        while current.parent:
            ancestors.append(current.parent)
            current = current.parent
        return ancestors[::-1]

    def get_region(self):
        cc = self
        ancestors = cc.get_all_ancestors()

        return ancestors[2]

    def get_all_ancestors_and_their_children(self):
        ancestors = CostCenter.objects.none()
        if self.parent:
            ancestors.append(self.parent)
            ancestors += self.parent.get_all_ancestors_and_their_children()
        children = self.get_all_children()
        return ancestors + children

    def get_view(self):
        """ return a list of cost centers involving children, grand children, brothers ,parent , parent brothers, grand parent"""
        cost_centers = []
        i = 0
        while self.parent and i < 2:
            cost_centers.append(self)
            cost_centers += self.get_all_children()
            self = self.parent
            i += 1
        return cost_centers
    def get_view_1(self):
        """ return a list of cost centers involving children, grand children, brothers ,parent , parent brothers, grand parent"""
        cost_centers = []
        i = 0
        while self.parent and i < 4:
            cost_centers.append(self)
            cost_centers += self.get_all_children()
            self = self.parent
            i += 1
        return cost_centers

    def __str__(self):

        return f"{self.name} ({self.code})"


class UserProfile(AbstractUser):
    username = models.CharField(max_length=15, unique=True, verbose_name='EC Number', db_index=True)
    designation = models.ForeignKey(Designations, on_delete=models.DO_NOTHING, blank=True, null=True)
    section = models.ForeignKey(Sections, on_delete=models.DO_NOTHING, blank=True, null=True)
    cost_center = models.ForeignKey(CostCenter, on_delete=models.DO_NOTHING, blank=True, null=True)
    depot = models.ForeignKey(Depots, on_delete=models.DO_NOTHING, blank=True, null=True)
    district = models.ForeignKey(Districts, on_delete=models.DO_NOTHING, blank=True, null=True)
    roles = models.ManyToManyField(Roles, blank=True, null=True)
    region = models.ForeignKey(Regions, on_delete=models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=30, blank=True)
    email = models.CharField(max_length=50, blank=True)
    last_reset = models.DateField(default=date.today())
    password_expiry_date = models.DateField(null=True, blank=True)
    password_expiry_days = models.IntegerField(default=90)
    change_password = models.BooleanField(default=False, null=True, blank=True)

    class Meta:
        ordering = ['last_name', 'first_name', 'username']

    def __str__(self):
        if self.first_name and self.last_name:
            return f"{self.last_name} {self.first_name}"
        else:
            return f"{self.username}"

    def add_role(self, role, app_id):
        existing_role = self.roles.filter(app_id__fullname=app_id).first()
        if existing_role:
            self.roles.remove(existing_role)
        try:
            self.roles.add(role)
        except:
            pass
        self.save()

    def get_user_roles_for_application(self, application_name):
        # Filter the user's roles for the specific application
        application = Application.objects.filter(name=application_name).first()
        print("application: ", application)
        if application:
            user_roles = self.roles.filter(app_id=application.id)
            print("user_roles: ", user_roles)
            # Return the roles if any exist
            if user_roles.exists():
                return user_roles[0].role
        else:
            return None

    def get_user_role_for_application(self, application_name):
        # Filter the user's roles for the specific application
        application = Application.objects.filter(name=application_name).first()
        print("application: ", application)
        if application:
            user_roles = self.roles.filter(app_id=application.id)
            print("user_roles: ", user_roles)
            # Return the roles if any exist
            if user_roles.exists():
                return user_roles[0]
        else:
            return None

    def cost_centers_for(self, app_names):
        responsibilities = self.responsibilities.filter(role__app_id__name__in=app_names)
        if responsibilities.exists():
            cost_centers = set()
            for responsibility in responsibilities:
                cost_centers.update(responsibility.cost_centers.all())
            return cost_centers
        return None

    def cost_center_and_decendace(self):
        CostCenters = CostCenter.objects.filter(pk=self.cost_center.pk)
        CostCenters |= self.cost_center.get_decendance()
        return CostCenters


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


class Responsibilities(models.Model):
    user = models.ForeignKey(UserProfile, on_delete=models.CASCADE, blank=True, null=True,
                             related_name='responsibilities')
    role = models.ForeignKey(Roles, on_delete=models.CASCADE, blank=True, null=True)
    cost_centers = models.ManyToManyField(CostCenter, blank=True)

    def __str__(self):
        return str(self.role.name)
