from graphene_django.types import DjangoObjectType
from .models import  ToolOrEquipment, ToolsAndEquipmentRegister, ToolsAndEquipmentRegisterItem, Comment   
class ToolOrEquipmentType(DjangoObjectType):
    class Meta:
        model = ToolOrEquipment
class ToolsAndEquipmentFormType(DjangoObjectType):
    class Meta:
        model = ToolsAndEquipmentRegister
class AssignedToolOrEquipmentType(DjangoObjectType):
    class Meta:
        model = ToolsAndEquipmentRegisterItem
class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        
