from graphene import (ObjectType, List, Field, ID, Int, String, Mutation)
from .models import ToolOrEquipment, ToolsAndEquipmentRegister, ToolsAndEquipmentRegisterItem, Remarks
from .typses import ToolOrEquipmentType, ToolsAndEquipmentRegisterType, ToolsAndEquipmentRegisterItemType, RemarksType
from it.users.models import UserProfile

class Query(ObjectType):
    all_tools_and_equipment = List(ToolOrEquipmentType)
    tool_or_equipment_by_id = Field(ToolOrEquipmentType, id=ID(required=True))
    tools_and_equipment_registers = List(ToolsAndEquipmentRegisterType)
    tools_and_equipment_register_items = List(ToolsAndEquipmentRegisterItemType)
    remarks = List(RemarksType)
    remark_by_id = Field(RemarksType, id=ID(required=True))
    my_T_E = List(ToolsAndEquipmentRegisterType)

    def resolve_all_tools_and_equipment(root, info):
        return ToolOrEquipment.objects.all()
    def resolve_tool_or_equipment_by_id(root, info, id):
        try:
            return ToolOrEquipment.objects.get(pk=id)
        except ToolOrEquipment.DoesNotExist:
            return None
    def resolve_tools_and_equipment_registers(root, info):
        return ToolsAndEquipmentRegister.objects.all()
    def resolve_tools_and_equipment_register_items(root, info):
        return ToolsAndEquipmentRegisterItem.objects.all()
    def resolve_remarks(root, info):
        return Remarks.objects.all()
    def resolve_remark_by_id(root, info, id):
        try:
            return Remarks.objects.get(pk=id)
        except Remarks.DoesNotExist:
            return None
    def resolve_my_T_E(self, info):
        user = info.context.user
        if user.is_authenticated:
            return ToolsAndEquipmentRegister.objects.filter(artisan=user)
        return ToolsAndEquipmentRegister.objects.none()

class Mutation(ObjectType):
    pass
