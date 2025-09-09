from graphene_django.types import DjangoObjectType
from .models import  ToolOrEquipment, ToolsAndEquipmentForm, AssignedToolOrEquipment, Comment   
class ToolOrEquipmentType(DjangoObjectType):
    class Meta:
        model = ToolOrEquipment
class ToolsAndEquipmentFormType(DjangoObjectType):
    class Meta:
        model = ToolsAndEquipmentForm
class AssignedToolOrEquipmentType(DjangoObjectType):
    class Meta:
        model = AssignedToolOrEquipment
class CommentType(DjangoObjectType):
    class Meta:
        model = Comment
        
