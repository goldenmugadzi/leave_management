import graphene
from graphene_django import DjangoObjectType
from .models import Job, Teammember, PretaskRiskAssessment

class JobType(DjangoObjectType):
    class Meta:
        model = Job
        fields = '__all__'

class TeammemberType(DjangoObjectType):
    class Meta:
        model = Teammember
        fields = '__all__'

class PretaskRiskAssessmentType(DjangoObjectType):
    class Meta:
        model = PretaskRiskAssessment
        fields = '__all__'
