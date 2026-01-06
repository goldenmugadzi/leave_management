import graphene
import graphql_jwt
from tokens.schema import Query as TokenQuery, Mutation as TokenMutation
from pretask_risk_assessment.schema import Query as RiskQuery, Mutation as RiskMutation
from it.users.schema import Query as UserQuery
from BatteryMaintenance.schema import Query as BatteryMaintenanceQuery, Mutation as BatteryMaintenanceMutation
from toolsandequipment.schema import Query as ToolsAndEquipmentQuery, Mutation as ToolsAndEquipmentMutation
from Docusign.schema import DocumentQuery, DocumentMutation
from it.beii_auth.mutations import TokenAuth

class Query(UserQuery, TokenQuery, BatteryMaintenanceQuery, ToolsAndEquipmentQuery, RiskQuery, DocumentQuery, graphene.ObjectType):
    pass

class Mutation(TokenMutation, BatteryMaintenanceMutation, ToolsAndEquipmentMutation, RiskMutation, DocumentMutation, graphene.ObjectType):
    token_auth = TokenAuth.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)