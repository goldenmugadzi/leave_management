from graphene_django.types import DjangoObjectType
from .models import  ToolOrEquipment, ToolsAndEquipmentRegister, Remarks, ToolsAndEquipmentRegisterItem   
class ToolOrEquipmentType(DjangoObjectType):
    class Meta:
        model = ToolOrEquipment
class ToolsAndEquipmentRegisterType(DjangoObjectType):
    class Meta:
        model = ToolsAndEquipmentRegister
class ToolsAndEquipmentRegisterItemType(DjangoObjectType):
    class Meta:
        model = ToolsAndEquipmentRegisterItem
class RemarksType(DjangoObjectType):
    class Meta:
        model = Remarks
        
