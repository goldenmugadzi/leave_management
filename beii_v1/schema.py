import graphene
import graphql_jwt
from tokens.schema import Query as TokenQuery, Mutation as TokenMutation
from it.users.schema import Query as UserQuery

class Query( UserQuery,TokenQuery , graphene.ObjectType):
    pass

class Mutation( TokenMutation, graphene.ObjectType):
    token_auth = graphql_jwt.ObtainJSONWebToken.Field()
    verify_token = graphql_jwt.Verify.Field()
    refresh_token = graphql_jwt.Refresh.Field()

schema = graphene.Schema(query=Query, mutation=Mutation)