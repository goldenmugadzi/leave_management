import graphene
from .types import (
    UserProfileType, RegionsType, DistrictsType, SectionsType, DepotsType,
    ApplicationType, RolesType, DesignationsType, CostCenterType,
    NotificationType, SupplierType, ResponsibilitiesType
)
from .models import (
    UserProfile, Regions, Districts, Sections, Depots, Application, Roles,
    Designations, CostCenter, Notification, Supplier, Responsibilities
)

class Query(graphene.ObjectType):
    me = graphene.Field(UserProfileType)
    users = graphene.List(UserProfileType)
    user = graphene.Field(UserProfileType, id=graphene.ID(required=True))
    application = graphene.Field(ApplicationType, id=graphene.ID(required=True))
    role = graphene.Field(RolesType, id=graphene.ID(required=True))
    designation = graphene.Field(DesignationsType, id=graphene.ID(required=True))
    cost_center = graphene.Field(CostCenterType, id=graphene.ID(required=True))
    notification = graphene.Field(NotificationType, id=graphene.ID(required=True))
    supplier = graphene.Field(SupplierType, id=graphene.ID(required=True))
    responsibility = graphene.Field(ResponsibilitiesType, id=graphene.ID(required=True))
    my_cost_centers = graphene.List(CostCenterType)
    all_regions = graphene.List(RegionsType)
    all_districts = graphene.List(DistrictsType)
    all_sections = graphene.List(SectionsType)
    all_depots = graphene.List(DepotsType)
    all_applications = graphene.List(ApplicationType)
    all_roles = graphene.List(RolesType)
    all_designations = graphene.List(DesignationsType)
    all_cost_centers = graphene.List(CostCenterType)
    all_notifications = graphene.List(NotificationType)
    all_suppliers = graphene.List(SupplierType)
    all_responsibilities = graphene.List(ResponsibilitiesType)

    def resolve_users(self, info):
        return UserProfile.objects.all()

    def resolve_user(self, info, id):
        return UserProfile.objects.get(pk=id)

    def resolve_me(self, info):
        user = info.context.user
        return UserProfile.objects.get(pk=user.id) if user.is_authenticated else None
   
    def resolve_region(self, info, id):
        return Regions.objects.get(pk=id)

    def resolve_district(self, info, id):
        return Districts.objects.get(pk=id)

    def resolve_section(self, info, id):
        return Sections.objects.get(pk=id)

    def resolve_depot(self, info, id):
        return Depots.objects.get(pk=id)

    def resolve_application(self, info, id):
        return Application.objects.get(pk=id)

    def resolve_role(self, info, id):
        return Roles.objects.get(pk=id)

    def resolve_designation(self, info, id):
        return Designations.objects.get(pk=id) 

    def resolve_cost_center(self, info, id):
        return CostCenter.objects.get(pk=id)
    
    def resolve_my_cost_centers(self, info):
        user = info.context.user
        if user.is_authenticated:
            application_names = ["temper", "reimbursement", "clear credit"]
            return user.cost_centers_for(application_names)
        return CostCenter.objects.none()

    def resolve_notification(self, info, id):
        return Notification.objects.get(pk=id)

    def resolve_supplier(self, info, id):
        return Supplier.objects.get(pk=id)

    def resolve_responsibility(self, info, id):
        return Responsibilities.objects.get(pk=id)

    def resolve_all_regions(self, info):
        return Regions.objects.all()

    def resolve_all_districts(self, info):
        return Districts.objects.all()

    def resolve_all_sections(self, info):
        return Sections.objects.all()

    def resolve_all_depots(self, info):
        return Depots.objects.all()

    def resolve_all_applications(self, info):
        return Application.objects.all()

    def resolve_all_roles(self, info):
        return Roles.objects.all()

    def resolve_all_designations(self, info):
        return Designations.objects.all()

    def resolve_all_cost_centers(self, info):
        return CostCenter.objects.all()

    def resolve_all_notifications(self, info):
        return Notification.objects.all()

    def resolve_all_suppliers(self, info):
        return Supplier.objects.all()

    def resolve_all_responsibilities(self, info):
        return Responsibilities.objects.all()

