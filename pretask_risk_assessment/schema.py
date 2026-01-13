import graphene
from graphene_django.types import DjangoObjectType
from .models import Job, Teammember, PretaskRiskAssessment
from .types import JobType, TeammemberType, PretaskRiskAssessmentType, ToolOrEquipmentType
from django.contrib.auth import get_user_model

from toolsandequipment.models import ToolOrEquipment
from it.users.models import Substation

class Query(graphene.ObjectType):
    jobs_for_user = graphene.List(JobType)
    equipment_for_substation = graphene.List(
        ToolOrEquipmentType,
        substation_id=graphene.ID(required=True)
    )

    def resolve_jobs_for_user(self, info):
        user = info.context.user
        if user.is_authenticated:
            return Job.objects.filter(competent_person=user)
        return Job.objects.none()

    def resolve_equipment_for_substation(self, info, substation_id):
        # Assuming ToolOrEquipment has a ForeignKey to Substation as 'substation'
        return ToolOrEquipment.objects.filter(substation_id=substation_id)

class CreatePretaskRiskAssessment(graphene.Mutation):
    class Arguments:
        job_id = graphene.ID(required=True)
        equipment_id = graphene.ID(required=True)
        harzard = graphene.String(required=True)
        control_measures = graphene.String(required=True)

    assessment = graphene.Field(PretaskRiskAssessmentType)

    def mutate(self, info, job_id, equipment_id, harzard, control_measures):
        job = Job.objects.get(pk=job_id)
        equipment = None
        # Correct import path already at top of file
        try:
            equipment = ToolOrEquipment.objects.get(pk=equipment_id)
        except ToolOrEquipment.DoesNotExist:
            raise Exception("Equipment not found")
        assessment = PretaskRiskAssessment.objects.create(
            job=job,
            equipment=equipment,
            harzard=harzard,
            control_measures=control_measures
        )
        return CreatePretaskRiskAssessment(assessment=assessment)

class UpdateTeammemberAgreed(graphene.Mutation):
    class Arguments:
        teammember_id = graphene.ID(required=True)
        agreed = graphene.String(required=True)

    teammember = graphene.Field(TeammemberType)

    def mutate(self, info, teammember_id, agreed):
        teammember = Teammember.objects.get(pk=teammember_id)
        teammember.agreed = agreed
        teammember.save()
        return UpdateTeammemberAgreed(teammember=teammember)

class Mutation(graphene.ObjectType):
    create_pretask_risk_assessment = CreatePretaskRiskAssessment.Field()
    update_teammember_agreed = UpdateTeammemberAgreed.Field()

# Schema is created in beii_v1/schema.py - do not create duplicate here
# schema = graphene.Schema(query=Query, mutation=Mutation)
