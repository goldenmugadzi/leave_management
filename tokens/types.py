from graphene_django.types import DjangoObjectType
from graphene import ObjectType, List, Field, ID, Int, String
from .models import (
    Meter, Customer, Token, REIMBURSEMENT, CLEARCREDIT, TAMPERTOKEN,
    OldToken, FaultMeter, RecoveredMeter, FaultMaintanance, Reconnection
)
from it.users.models import UserProfile, Regions, Sections, CostCenter
from approve.models import Process, Step, Workflow, Approval

class MeterType(DjangoObjectType):
    class Meta:
        model = Meter

class CustomerType(DjangoObjectType):
    class Meta:
        model = Customer

class TokenType(DjangoObjectType):
    class Meta:
        model = Token
        name = 'MeterToken'  # Custom GraphQL type name to avoid JWT conflicts

class ReimbursementType(DjangoObjectType):
    class Meta:
        model = REIMBURSEMENT

class ClearCreditType(DjangoObjectType):
    class Meta:
        model = CLEARCREDIT

class TamperTokenType(DjangoObjectType):
    class Meta:
        model = TAMPERTOKEN

class OldTokenType(DjangoObjectType):
    class Meta:
        model = OldToken

class FaultMeterType(DjangoObjectType):
    class Meta:
        model = FaultMeter

class RecoveredMeterType(DjangoObjectType):
    class Meta:
        model = RecoveredMeter

class FaultMaintananceType(DjangoObjectType):
    class Meta:
        model = FaultMaintanance

class ReconnectionType(DjangoObjectType):
    class Meta:
        model = Reconnection
        fields = "__all__"

    def resolve_proof_of_payment(self, info):
        request = info.context
        if self.proof_of_payment and hasattr(self.proof_of_payment, 'url'):
            return request.build_absolute_uri(self.proof_of_payment.url)
        return None

class UserProfileType(DjangoObjectType):
    class Meta:
        model = UserProfile

class RegionsType(DjangoObjectType):
    class Meta:
        model = Regions

class SectionsType(DjangoObjectType):
    class Meta:
        model = Sections

class CostCenterType(DjangoObjectType):
    class Meta:
        model = CostCenter

class ProcessType(DjangoObjectType):
    class Meta:
        model = Process

class StepType(DjangoObjectType):
    class Meta:
        model = Step

class WorkflowType(DjangoObjectType):
    class Meta:
        model = Workflow

class ApprovalType(DjangoObjectType):
    class Meta:
        model = Approval