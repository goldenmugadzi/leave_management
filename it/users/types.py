from graphene_django.types import DjangoObjectType
import graphene
from .models import (
    UserProfile, Regions, Districts, Sections, Depots, Application, Roles,
    Designations, CostCenter, Notification, Supplier, Responsibilities
)

class UserProfileType(DjangoObjectType):
    class Meta:
        model = UserProfile

class RegionsType(DjangoObjectType):
    class Meta:
        model = Regions

class DistrictsType(DjangoObjectType):
    class Meta:
        model = Districts

class SectionsType(DjangoObjectType):
    class Meta:
        model = Sections

class DepotsType(DjangoObjectType):
    class Meta:
        model = Depots

class ApplicationType(DjangoObjectType):
    class Meta:
        model = Application

class RolesType(DjangoObjectType):
    class Meta:
        model = Roles

class DesignationsType(DjangoObjectType):
    class Meta:
        model = Designations

class CostCenterType(DjangoObjectType):
    class Meta:
        model = CostCenter

   
class NotificationType(DjangoObjectType):
    class Meta:
        model = Notification

class SupplierType(DjangoObjectType):
    class Meta:
        model = Supplier

class ResponsibilitiesType(DjangoObjectType):
    class Meta:
        model = Responsibilities