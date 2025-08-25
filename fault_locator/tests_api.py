from django.urls import reverse
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from it.users.models import UserProfile, Depots
from .models import FaultLocatorRole, FaultLocatorDevice, Fault

class FaultLocatorAPITestCase(APITestCase):
    def setUp(self):
        self.depot = Depots.objects.create(code='X1', depot='Test Depot', region='Test Region')
        self.senior = UserProfile.objects.create(username='senior1', first_name='Senior', last_name='User')
        self.role = FaultLocatorRole.objects.create(user=self.senior, role='senior_foreman')
        self.token = Token.objects.create(user=self.senior)
        self.client = APIClient()
        self.client.credentials(HTTP_AUTHORIZATION='Token ' + self.token.key)

    def test_create_device(self):
        url = reverse('fl-device-list')
        resp = self.client.post(url, {"serial_number": "SN123", "description": "Primary device"}, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)

    def test_create_fault(self):
        url = reverse('fl-fault-list')
        resp = self.client.post(url, {"description": "Line down", "depot_id": self.depot.id}, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
