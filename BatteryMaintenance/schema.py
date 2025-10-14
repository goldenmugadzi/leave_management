import graphene
from graphene import ObjectType, Field, List, ID, Int, InputObjectType, String, Mutation, Float
from graphql_jwt.decorators import login_required
from approve.views import gql_initiate_approval_process, gql_send_notification
from .models import Substation, BatteryInstallation, Cell, BatteryMaintenance, CellReading
from pretask_risk_assessment.types import ToolOrEquipmentType
# from toolsandequipment.models import ToolOrEquipment
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
    # equipment_for_substation = graphene.List(ToolOrEquipmentType,substation_id=graphene.ID(required=True))

    def resolve_all_substations(self, info):
        return Substation.objects.all()

    def resolve_substations_by_region(self, info, region):
        print("Region")  # Debugging line
        substations = Substation.objects.filter(region__id=region).order_by('name')
        print(substations)
        return Substation.objects.filter(region__id=region).order_by('name') 

    def resolve_substations_by_district(self, info, district):
        return Substation.objects.filter(district__district__icontains=district)
        
    # def resolve_equipment_for_substation(self, info, substation_id):
    #     return ToolOrEquipment.objects.filter(substation__id=substation_id)


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

# Updated mutation to match AddBatteryMaintenance signature and return structure
class AddBatteryMaintenance(Mutation):
    class Arguments:
        battery_id = ID(required=True)
        reading_type = String(required=True)
        water_used = Float()
        cell_readings = List(CellReadingInput, required=True)
        total_volts = Float()
        # volts_high, volts_low, volts_avg, sg_high, sg_low, sg_avg removed from arguments

    id = ID()
    reading_type = String()
    water_used = Float()
    cellreading_set = List(CellReadingType)
    total_volts = Float()
    # volts_high, volts_low, volts_avg, sg_high, sg_low, sg_avg removed from output fields

    @login_required
    def mutate(self, info, battery_id, reading_type, water_used=None, cell_readings=None, total_volts=None,
               volts_high=None, volts_low=None, volts_avg=None, sg_high=None, sg_low=None, sg_avg=None):
        print("[DEBUG] AddBatteryMaintenance called with:")
        print(f"  battery_id={battery_id}")
        print(f"  reading_type={reading_type}")
        print(f"  water_used={water_used}")
        print(f"  total_volts={total_volts}")
        print(f"  cell_readings={cell_readings}")
        user = info.context.user
        try:
            battery = BatteryInstallation.objects.get(pk=battery_id)
        except BatteryInstallation.DoesNotExist:
            print("[ERROR] Battery installation not found.")
            raise Exception("Battery installation not found.")

        maintenance = BatteryMaintenance.objects.create(
            battery=battery,
            reading_type=reading_type,
            water_used=water_used,
            total_volts=total_volts
            # volts_high, volts_low, volts_avg, sg_high, sg_low, sg_avg can still be set in the model if needed, but not returned
        )

        cellreading_objs = []
        for cr in cell_readings or []:
            try:
                print(f"[DEBUG] Processing cell reading: {cr}")
                cell = Cell.objects.get(pk=cr.cell_id, installation=battery)
                cellreading = CellReading.objects.create(
                    battery_maintenance=maintenance,
                    cell=cell,
                    specific_gravity=cr.specific_gravity,
                    voltage=cr.voltage
                )
                cellreading_objs.append(cellreading)
            except Cell.DoesNotExist:
                print(f"[ERROR] Cell with id {cr.cell_id} does not exist for battery {battery_id}")
                continue

        return AddBatteryMaintenance(
            id=maintenance.id,
            reading_type=maintenance.reading_type,
            water_used=maintenance.water_used,
            cellreading_set=cellreading_objs,
            total_volts=maintenance.total_volts
        )
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
    add_battery_maintenance = AddBatteryMaintenance.Field()
    create_substation = CreateSubstation.Field()