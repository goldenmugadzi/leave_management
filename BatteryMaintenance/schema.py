import graphene
from graphene import ObjectType, Field, List, ID, Int, InputObjectType, String, Mutation, Float
from graphql_jwt.decorators import login_required
from approve.views import gql_initiate_approval_process, gql_send_notification
from .models import Substation, BatteryInstallation, Cell, BatteryMaintenance, CellReading
from .types import SubstationType, BatteryInstallationType, CellType, BatteryMaintenanceType, CellReadingType
from django.db.models import Q

class CellReadingInput(graphene.InputObjectType):
    cell_id = graphene.ID(required=True)
    specific_gravity = graphene.Float()
    voltage = graphene.Float()

class Query(graphene.ObjectType):
    all_substations = List(SubstationType)
    substations_by_region = List(SubstationType, region=String(required=True))
    substations_by_district = List(SubstationType, district=String(required=True))
    substations_by_depot = List(SubstationType, depot=String(required=True))
    battery_installation = Field(BatteryInstallationType, id=ID(required=True))
    battery_installation_for_substation = List(BatteryInstallationType, substation_id=ID(required=True))
    substations_by_name_or_code = List(SubstationType, search=String(required=True))
    all_battery_installations = List(BatteryInstallationType)
    cells_by_installation = List(CellType, installation_id=ID(required=True))
    battery_maintenance = Field(BatteryMaintenanceType, id=ID(required=True))
    maintenances_by_battery = List(BatteryMaintenanceType, battery_id=ID(required=True))
    cell_readings_by_maintenance = List(CellReadingType, maintenance_id=ID(required=True))

    def resolve_all_substations(self, info):
        return Substation.objects.all()

    def resolve_substations_by_region(self, info, region):
        print("Region")  # Debugging line
        substations = Substation.objects.filter(region__id=region).order_by('name')
        print(substations)
        return Substation.objects.filter(region__id=region).order_by('name')

    def resolve_substations_by_district(self, info, district):
        return Substation.objects.filter(district__district__icontains=district)

    def resolve_substations_by_depot(self, info, depot):
        return Substation.objects.filter(depot__depot__icontains=depot).order_by('name')

    def resolve_battery_installation(self, info, id):
        return BatteryInstallation.objects.get(pk=id)

    def resolve_all_battery_installations(self, info):
        return BatteryInstallation.objects.all()

    def resolve_cells_by_installation(self, info, installation_id):
        return Cell.objects.filter(installation_id=installation_id)

    def resolve_battery_maintenance(self, info, id):
        return BatteryMaintenance.objects.get(pk=id)

    def resolve_maintenances_by_battery(self, info, battery_id):
        return BatteryMaintenance.objects.filter(battery_id=battery_id)

    def resolve_cell_readings_by_maintenance(self, info, maintenance_id):
        return CellReading.objects.filter(battery_maintenance_id=maintenance_id)
    def resolve_substations_by_name_or_code(self, info, search):
        return Substation.objects.filter(
            Q(name__icontains=search) | Q(code__icontains=search)
        )
    def resolve_battery_installation_for_substation(self, info, substation_id):
        return BatteryInstallation.objects.filter(substation_id=substation_id)
class MaintainBattery(Mutation):
    class Arguments:
        battery_id = ID(required=True)
        volts_high = Float()
        volts_low = Float()
        volts_avg = Float()
        sg_high = Float()
        sg_low = Float()
        sg_avg = Float()
        reading_type = String()
        water_used = Float()
        cell_readings = List(CellReadingInput)  # <-- Use the input type class here

    battery_maintenance = Field(BatteryMaintenanceType)
    message = String()

    @login_required
    def mutate(self, info, battery_id, volts_high=None, volts_low=None, volts_avg=None,
                sg_high=None, sg_low=None, sg_avg=None, reading_type="monthly",
                water_used=None, cell_readings=None):
        user = info.context.user
        try:
            battery = BatteryInstallation.objects.get(pk=battery_id)
        except BatteryInstallation.DoesNotExist:
            return MaintainBattery(message="Battery installation not found.")

        maintenance = BatteryMaintenance.objects.create(
            battery=battery,
            volts_high=volts_high,
            volts_low=volts_low,
            volts_avg=volts_avg,
            sg_high=sg_high,
            sg_low=sg_low,
            sg_avg=sg_avg,
            reading_type=reading_type,
            water_used=water_used
        )

        if cell_readings:
            for cr in cell_readings:
                try:
                    cell = Cell.objects.get(pk=cr.cell_id, installation=battery)
                    CellReading.objects.create(
                        battery_maintenance=maintenance,
                        cell=cell,
                        specific_gravity=cr.specific_gravity,
                        voltage=cr.voltage
                    )
                except Cell.DoesNotExist:
                    continue

        return MaintainBattery(battery_maintenance=maintenance, message="Battery maintenance recorded successfully.")

class CreateSubstation(graphene.Mutation):
    class Arguments:
        name = graphene.String(required=True)
        code = graphene.String(required=True)
        region_id = graphene.ID(required=True)
        district_id = graphene.ID(required=True)
        depot_id = graphene.ID(required=True)

    substation = Field(SubstationType)
    message = String()

    @login_required
    def mutate(self, info, name, code, region_id, district_id, depot_id):
        from .models import Regions, Districts, Depots  # Import here to avoid circular import
        try:
            region = Regions.objects.get(pk=region_id)
            district = Districts.objects.get(pk=district_id)
            depot = Depots.objects.get(pk=depot_id)
        except Exception as e:
            return CreateSubstation(message=f"Invalid foreign key: {e}")

        substation = Substation.objects.create(
            name=name,
            code=code,
            region=region,
            district=district,
            depot=depot
        )
        return CreateSubstation(substation=substation, message="Substation created successfully.")

class Mutation(ObjectType):
    maintain_battery = MaintainBattery.Field()
    create_substation = CreateSubstation.Field()