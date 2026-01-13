from graphene import (ObjectType, List, Field, ID, Int, String, Mutation)
from .models import ToolOrEquipment, ToolsAndEquipmentRegister, ToolsAndEquipmentRegisterItem, Comment
from .typses import ToolOrEquipmentType, ToolsAndEquipmentFormType, AssignedToolOrEquipmentType, CommentType
from it.users.models import UserProfile

class Query(ObjectType):
    all_tools_and_equipment = List(ToolOrEquipmentType)
    tool_or_equipment_by_id = Field(ToolOrEquipmentType, id=ID(required=True))
    tools_and_equipment_forms = List(ToolsAndEquipmentFormType)
    assigned_tools_and_equipment = List(AssignedToolOrEquipmentType)
    assigned_tool_or_equipment_by_id = Field(AssignedToolOrEquipmentType, id=ID(required=True))
    my_tools_and_equipment = List(AssignedToolOrEquipmentType, user_id=ID(required=True))
    comments = List(CommentType)
    comment_by_id = Field(CommentType, id=ID(required=True))

    def resolve_all_tools_and_equipment(root, info):
        return ToolOrEquipment.objects.all()
    def resolve_tool_or_equipment_by_id(root, info, id):
        try:
            return ToolOrEquipment.objects.get(pk=id)
        except ToolOrEquipment.DoesNotExist:
            return None
    def resolve_tools_and_equipment_forms(root, info):
        return ToolsAndEquipmentRegister.objects.all()  
    def resolve_assigned_tools_and_equipment(root, info):
        return ToolsAndEquipmentRegisterItem.objects.all()
    def resolve_assigned_tool_or_equipment_by_id(root, info, id):
        try:
            return ToolsAndEquipmentRegisterItem.objects.get(pk=id)
        except ToolsAndEquipmentRegisterItem.DoesNotExist:
            return None
    def resolve_my_tools_and_equipment(root, info, user_id):
        return ToolsAndEquipmentRegisterItem.objects.filter(assigned_to__id=user_id)
    def resolve_comments(root, info):
        return Comment.objects.all()
    def resolve_comment_by_id(root, info, id):
        try:
            return Comment.objects.get(pk=id)
        except Comment.DoesNotExist:
            return None

class CreateComment(Mutation):
    class Arguments:
        comment = String(required=True)
        assigned_tool_or_equipment_id = ID(required=True)
        author_id = ID(required=True)

    comment_obj = Field(CommentType)
    message = String()

    def mutate(self, info, comment, assigned_tool_or_equipment_id, author_id):
        try:
            assigned_tool = ToolsAndEquipmentRegisterItem.objects.get(pk=assigned_tool_or_equipment_id)
        except ToolsAndEquipmentRegisterItem.DoesNotExist:
            return CreateComment(message="Assigned tool or equipment not found.")

        try:
            author = UserProfile.objects.get(pk=author_id)
        except UserProfile.DoesNotExist:
            return CreateComment(message="Author not found.")

        comment_obj = Comment.objects.create(
            assigned_tool_or_equipment=assigned_tool,
            comment=comment,
            author=author
        )
        return CreateComment(comment_obj=comment_obj, message="Comment added successfully.")

class Mutation(ObjectType):
    create_comment = CreateComment.Field()
