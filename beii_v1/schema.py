import graphene
import graphql_jwt
from tokens.schema import Query as TokenQuery, Mutation as TokenMutation
from it.users.schema import Query as UserQuery
from BatteryMaintenance.schema import Query as BatteryMaintenanceQuery, Mutation as BatteryMaintenanceMutation
from toolsandequipment.schema import Query as ToolsAndEquipmentQuery, Mutation as ToolsAndEquipmentMutation

class Query( UserQuery,TokenQuery, BatteryMaintenanceQuery ,  ToolsAndEquipmentQuery, graphene.ObjectType):
    pass

class Mutation( TokenMutation, BatteryMaintenanceMutation, ToolsAndEquipmentMutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)