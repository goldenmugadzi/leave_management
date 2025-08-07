from graphene import ObjectType, Field, List, ID, Int, InputObjectType,String,Mutation
from graphql_jwt.decorators import login_required
from approve.views import gql_initiate_approval_process, gql_send_notification
from .models import (
    Meter, Customer, Token, CostCenter, REIMBURSEMENT, CLEARCREDIT, TAMPERTOKEN,
    FaultMaintanance, RecoveredMeter, Reconnection, OldToken, FaultMeter
)
from .types import (
    MeterType, CustomerType, TokenType, ReimbursementType, ClearCreditType,
    TamperTokenType, OldTokenType, FaultMeterType, RecoveredMeterType,
    FaultMaintananceType, ReconnectionType
)
from graphene_file_upload.scalars import Upload
from .forms import ReimbursementForm, FaultMeterForm, RecoveredMeterForm, OldTokenForm, TamperTokenForm, FaultMaintananceForm, ReconnectionForm

class Query(ObjectType):
    all_tokens = List(TokenType, limit=Int())
    token = Field(TokenType, id=ID(required=True))
    meter_tokens = List(TokenType, meter_number=String(required=True), limit=Int())
    all_meters = List(MeterType)
    all_customers = List(CustomerType)
    all_reimbursements = List(ReimbursementType)
    all_clearcredits = List(ClearCreditType)
    all_tampertokens = List(TamperTokenType)
    all_oldtokens = List(OldTokenType)
    all_faultmeters = List(FaultMeterType)
    all_recoveredmeters = List(RecoveredMeterType)
    all_faultmaintanances = List(FaultMaintananceType)
    all_reconnections = List(ReconnectionType)
    token_types = List(TokenType)

    @login_required
    def resolve_all_tokens(self, info, limit=None):
        user = info.context.user
        application_names = ["temper", "reimbursement", "clear credit"]
        cost_centers = user.cost_centers_for(application_names)
        print("Cost Centers:", cost_centers)
        qs =  Token.objects.filter(cost_center__in=cost_centers)
        if limit:
            qs = qs[:limit]
        return qs

    @login_required
    def resolve_token(self, info, id):
        return Token.objects.get(pk=id)
    # @login_required
    def resolve_token_types(self, info):
        return Token.objects.values_list('token_type', flat=True).distinct()
    
    @login_required
    def resolve_meter_tokens(self, info, meter_number, limit=None):
        qs = Token.objects.filter(meter__number=meter_number)
        if limit:
            qs = qs[:limit]
        return qs

    @login_required
    def resolve_all_meters(self, info):
        return Meter.objects.all()

    @login_required
    def resolve_all_customers(self, info):
        return Customer.objects.all()

    @login_required
    def resolve_all_reimbursements(self, info):
        return REIMBURSEMENT.objects.all()

    @login_required
    def resolve_all_clearcredits(self, info):
        return CLEARCREDIT.objects.all()

    @login_required
    def resolve_all_tampertokens(self, info):
        return TAMPERTOKEN.objects.all()

    @login_required
    def resolve_all_oldtokens(self, info):
        return OldToken.objects.all()

    @login_required
    def resolve_all_faultmeters(self, info):
        return FaultMeter.objects.all()

    @login_required
    def resolve_all_recoveredmeters(self, info):
        return RecoveredMeter.objects.all()

    @login_required
    def resolve_all_faultmaintanances(self, info):
        return FaultMaintanance.objects.all()

    @login_required
    def resolve_all_reconnections(self, info):
        return Reconnection.objects.all()
    
class CreateTokenInput(InputObjectType):
    type = String(required=True)
    reason = String(required=True)
    meterNumber = String(required=True)
    customerName = String(required=True)
    customerContactNumber = String()
    customerAddress = String()
    costCenterName = String()
    selectedCostCenter = ID()
    tokenPhoto = String()
    reimbursementUnits = String()
    reimbursementPurpose = String()
    tamperIsFor = String()
    faultUnits = String()
    clearAmount = String()

class CreateToken(Mutation):
    class Arguments:
        input = CreateTokenInput(required=True)
        faultPhoto = Upload(required=False)
        faultMaintPhoto = Upload(required=False)
        reconnectionInvoice = Upload(required=False)
        reconnectionProof = Upload(required=False)
        oldToken = Upload(required=False)
        clearReceipt = Upload(required=False)
        recoveredMeterPhoto = Upload(required=False)

    token = Field(TokenType)
    message = String()

    @login_required
    def mutate(self, info, input, recoveredMeterPhoto=None, faultPhoto=None, faultMaintPhoto=None, reconnectionInvoice=None, reconnectionProof=None, oldToken=None, clearReceipt=None):
        user = info.context.user
        print("Received input:", input)

        try:
            cost_center = CostCenter.objects.get(pk=int(input.selectedCostCenter))
        except CostCenter.DoesNotExist:
            raise Exception(f"CostCenter with id {input.selectedCostCenter} does not exist")
        meter, _ = Meter.objects.get_or_create(number=input.meterNumber)
        customers = Customer.objects.filter(name=input.customerName)
        if customers.exists():
            customer = customers.first()
        else:
            customer = Customer.objects.create(
                name=input.customerName,
                contact_number=input.customerContactNumber,
                address=input.customerAddress
            )
        process = gql_initiate_approval_process(input.type)
        token = Token.objects.create(
            type=input.type,
            reason=input.reason,
            process=process,
            meter=meter,
            customer=customer,
            cost_center=cost_center,
            created_by=user,
        )
        if input.type.upper() == "TEMPER":
            # Validate tamper token form
            tamper_token_form = TamperTokenForm({
                "is_for": input.tamperIsFor,
            })
            if tamper_token_form.is_valid():
                tamper_token = tamper_token_form.save(commit=False)
                tamper_token.token = token
                tamper_token.save()
                app = "temper"

                # Faulty Maintanance case
                if tamper_token.is_for == "Fault Maintenance":
                    fault_maintanance_form = FaultMaintananceForm(files={"photo": faultMaintPhoto})
                    if fault_maintanance_form.is_valid():
                        fault_maintanance = fault_maintanance_form.save(commit=False)
                        fault_maintanance.token = token
                        fault_maintanance.save()
                    else:
                        tamper_token.delete()
                        token.delete()
                        raise Exception(f"Fault Maintenance form error: {fault_maintanance_form.errors}")

                # Recovered Meter case
                elif tamper_token.is_for == "Recovered Meter":
                    recovered_meter_form = RecoveredMeterForm(files={"picture": recoveredMeterPhoto})
                    if recovered_meter_form.is_valid():
                        recovered_meter = recovered_meter_form.save(commit=False)
                        recovered_meter.token = token
                        recovered_meter.save()
                    else:
                        tamper_token.delete()
                        token.delete()
                        raise Exception(f"Recovered Meter form error: {recovered_meter_form.errors}")

                # Reconnection case
                elif tamper_token.is_for == "Reconnection":
                    reconnection_form = ReconnectionForm(files={
                        "invoice": reconnectionInvoice,
                        "proof_of_payment": reconnectionProof,
                    })
                    if reconnection_form.is_valid():
                        reconnection = reconnection_form.save(commit=False)
                        reconnection.token = token
                        reconnection.save()
                    else:
                        tamper_token.delete()
                        token.delete()
                        raise Exception(f"Reconnection form error: {reconnection_form.errors}")

                else:
                    print(tamper_token.is_for)
                    tamper_token.delete()
                    token.delete()
                    raise Exception(f"Invalid tamper token purpose: {tamper_token.is_for}")
            else:
                token.delete()
                raise Exception(f"Tamper Token form error: {tamper_token_form.errors}")
        elif input.type.upper() == "REIMBURSEMENT":
            # Validate reimbursement form
            reimbursement_form = ReimbursementForm({
                "units": input.reimbursementUnits,
                "purpose": input.reimbursementPurpose,
            })
            if reimbursement_form.is_valid():
                reimbursement = reimbursement_form.save(commit=False)
                reimbursement.token = token
                reimbursement.save()

                # Faulty Meter case
                if reimbursement.purpose == "Faulty Meter":
                    faulty_meter_form = FaultMeterForm(files={"photo": faultPhoto})
                    if faulty_meter_form.is_valid():
                        faulty_meter = faulty_meter_form.save(commit=False)
                        faulty_meter.token = token
                        faulty_meter.save()
                    else:
                        token.delete()
                        raise Exception(f"Faulty Meter form error: {faulty_meter_form.errors}")

                # Recovered Meter case
                elif reimbursement.purpose == "Recovered Meter":
                    recovered_meter_form = RecoveredMeterForm(files={"picture": recoveredMeterPhoto})
                    if recovered_meter_form.is_valid():
                        recovered_meter = recovered_meter_form.save(commit=False)
                        recovered_meter.token = token
                        recovered_meter.save()
                    else:
                        token.delete()
                        raise Exception(f"Recovered Meter form error: {recovered_meter_form.errors}")

                # Old Token case
                elif reimbursement.purpose == "Old Token":
                    old_token_form = OldTokenForm(files={"old_token": oldToken})
                    if old_token_form.is_valid() and oldToken:
                        old_token_instance = old_token_form.save(commit=False)
                        old_token_instance.token = token
                        old_token_instance.save()
                    else:
                        token.delete()
                        raise Exception(f"Old Token form error: {old_token_form.errors}")

            else:
                token.delete()
                raise Exception(f"Reimbursement form error: {reimbursement_form.errors}")
        elif input.type.upper() == "CLEAR CREDIT":
            CLEARCREDIT.objects.create(
                token=token,
                amount=input.clearAmount,
                receipt=clearReceipt
            )
        response_message = gql_send_notification(token)
        return CreateToken(token=token, message=response_message)

class Mutation(ObjectType):
    create_token = CreateToken.Field()