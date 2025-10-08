from django.test import TestCase, override_settings
from django.urls import reverse
from django.utils import timezone

from it.users.models import (
    UserProfile, Application, Roles, Regions, Districts, Depots
)
from fault_locator.central_roles import FaultLocatorRoleManager
from fault_locator.models import CraneTruck, CraneRequest


@override_settings(ROOT_URLCONF='fault_locator.test_urls')
class CraneWorkflowTests(TestCase):
    @classmethod
    def setUpTestData(cls):
        # Regions/Districts/Depot
        cls.region = Regions.objects.create(region="NORTH", code="NR")
        cls.district = Districts.objects.create(district="D1", code="D1", region_id=str(cls.region.id))
        cls.depot = Depots.objects.create(depot="Main Depot", code="MD1", district=cls.district, region=cls.region)

        # Central roles application and roles
        cls.app = Application.objects.create(name='fault_locator', fullname='Fault Locator System')
        for code, name in [
            (FaultLocatorRoleManager.TRANSPORT_MANAGER, 'Transport Manager'),
            (FaultLocatorRoleManager.CRANE_OPERATOR, 'Crane Operator'),
            (FaultLocatorRoleManager.DEPOT_FOREPERSON, 'Depot Foreperson'),
        ]:
            Roles.objects.get_or_create(
                role=code,
                application='fault_locator',
                app_id=cls.app,
                defaults={
                    'name': name,
                    'description': name
                }
            )

        # Users
        cls.tm = UserProfile.objects.create_user(username='tm1', password='Passw0rd!')
        cls.tm.region = cls.region
        cls.tm.save()
        FaultLocatorRoleManager.assign_role(cls.tm, FaultLocatorRoleManager.TRANSPORT_MANAGER)

        cls.fp = UserProfile.objects.create_user(username='fp1', password='Passw0rd!')
        cls.fp.region = cls.region
        cls.fp.depot = cls.depot
        cls.fp.save()
        FaultLocatorRoleManager.assign_role(cls.fp, FaultLocatorRoleManager.DEPOT_FOREPERSON)

        cls.op = UserProfile.objects.create_user(username='op1', password='Passw0rd!')
        cls.op.region = cls.region
        cls.op.save()
        FaultLocatorRoleManager.assign_role(cls.op, FaultLocatorRoleManager.CRANE_OPERATOR)

    def test_full_crane_job_flow(self):
        # Manager creates a crane truck
        self.client.login(username='tm1', password='Passw0rd!')
        create_truck_url = reverse('fault_locator:crane_truck_create')
        resp = self.client.post(create_truck_url, {
            'fleet_number': 'FLT-001',
            'number_plate': 'ABC-123',
            'mileage_km': 10000,
            'status': 'available',
            'operator': '',
        })
        self.assertEqual(resp.status_code, 302)
        truck = CraneTruck.objects.get(fleet_number='FLT-001')

        # Foreperson submits a crane request
        self.client.logout()
        self.client.login(username='fp1', password='Passw0rd!')
        create_req_url = reverse('fault_locator:crane_request_create')
        today = timezone.now().date().isoformat()
        resp = self.client.post(create_req_url, {
            'depot': self.depot.id,
            'purpose': 'Lift transformer',
            'location': 'Substation A',
            'requested_date': today,
            'time_window': '09:00-12:00',
            'notes': 'Urgent replacement',
        })
        self.assertEqual(resp.status_code, 302)
        req = CraneRequest.objects.first()
        self.assertIsNotNone(req)
        self.assertEqual(req.status, 'pending')
        self.assertEqual(req.requested_by_id, self.fp.id)

        # Manager assigns truck and operator
        self.client.logout()
        self.client.login(username='tm1', password='Passw0rd!')
        assign_url = reverse('fault_locator:crane_request_assign', args=[req.id])
        resp = self.client.post(assign_url, {
            'assigned_truck': truck.id,
            'assigned_operator': self.op.id,
            'status': 'assigned',
        })
        self.assertEqual(resp.status_code, 302)
        req.refresh_from_db()
        self.assertEqual(req.status, 'assigned')
        self.assertEqual(req.assigned_truck_id, truck.id)
        self.assertEqual(req.assigned_operator_id, self.op.id)

        # Operator submits job report with mileage update
        self.client.logout()
        self.client.login(username='op1', password='Passw0rd!')
        report_url = reverse('fault_locator:crane_job_report', args=[req.id])
        resp = self.client.post(report_url, {
            'completion_notes': 'Completed safely',
            'started_at': timezone.now().isoformat(timespec='minutes'),
            'start_mileage_km': 10000,
            'end_mileage_km': 10050,
        })
        self.assertEqual(resp.status_code, 302)
        req.refresh_from_db()
        truck.refresh_from_db()
        self.assertEqual(req.status, 'completed')
        self.assertEqual(truck.mileage_km, 10050)

    def test_permissions_truck_list_denied_for_non_manager(self):
        # Foreperson should not access truck list
        self.client.login(username='fp1', password='Passw0rd!')
        url = reverse('fault_locator:crane_truck_list')
        resp = self.client.get(url)
        # Expect redirect to dashboard due to permission check
        self.assertEqual(resp.status_code, 302)
