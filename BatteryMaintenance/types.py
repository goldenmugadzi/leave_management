from graphene_django.types import DjangoObjectType
from graphene import ObjectType, List, Field, ID, Int, String , Mutation, Boolean
from .models import Substation, BatteryInstallation, Cell, BatteryMaintenance, CellReading
from graphene_django.filter import DjangoFilterConnectionField

class SubstationType(DjangoObjectType):
    class Meta:
        model = Substation

class BatteryInstallationType(DjangoObjectType):
    class Meta:
        model = BatteryInstallation

class CellType(DjangoObjectType):
    class Meta:
        model = Cell
class BatteryMaintenanceType(DjangoObjectType):
    class Meta:
        model = BatteryMaintenance
class CellReadingType(DjangoObjectType):
    class Meta:
        model = CellReading