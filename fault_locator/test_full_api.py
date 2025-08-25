from django.urls import reverse
from django.utils import timezone
from rest_framework.test import APITestCase, APIClient
from rest_framework.authtoken.models import Token
from it.users.models import UserProfile, Depots
from fault_locator.models import (
    FaultLocatorRole, FaultLocatorDevice, FaultLocatorTeam, Fault,
    FaultAssignment, FaultLocatorDeviceAssignment, TeamDeployment
)

class FaultLocatorFullAPITests(APITestCase):
    """Comprehensive integration tests for Fault Locator module."""

    def setUp(self):
        # Depots
        self.depot_a = Depots.objects.create(code='DA', depot='Depot A', region='North')
        self.depot_b = Depots.objects.create(code='DB', depot='Depot B', region='South')

        # Users
        self.senior = UserProfile.objects.create(username='senior', first_name='Senior', last_name='One')
        self.depot_fp = UserProfile.objects.create(username='dfp', first_name='Depot', last_name='Foreperson', depot=self.depot_a)
        self.team_leader = UserProfile.objects.create(username='tlead', first_name='Team', last_name='Lead')
        self.team_member = UserProfile.objects.create(username='tmem', first_name='Team', last_name='Member')
        self.other_user = UserProfile.objects.create(username='other', first_name='Other', last_name='User')

        # Roles
        FaultLocatorRole.objects.create(user=self.senior, role='senior_foreman')
        FaultLocatorRole.objects.create(user=self.depot_fp, role='depot_foreperson', depot=self.depot_a)
        FaultLocatorRole.objects.create(user=self.team_leader, role='team_leader')
        FaultLocatorRole.objects.create(user=self.team_member, role='team_member')

        # Auth tokens & clients
        self.client_senior = self._mk_client(self.senior)
        self.client_depot = self._mk_client(self.depot_fp)
        self.client_leader = self._mk_client(self.team_leader)
        self.client_member = self._mk_client(self.team_member)
        self.client_other = self._mk_client(self.other_user)  # no role

        # Seed device & team
        self.device1 = FaultLocatorDevice.objects.create(serial_number='SN-A', description='Primary', created_by=self.senior)
        self.device2 = FaultLocatorDevice.objects.create(serial_number='SN-B', description='Spare', created_by=self.senior)

        self.team = FaultLocatorTeam.objects.create(name='Alpha', team_leader=self.team_leader, created_by=self.senior, current_depot=self.depot_a)
        self.team.members.add(self.team_member)

        # Seed fault
        self.fault = Fault.objects.create(description='Line down at sector 12', depot=self.depot_a, reported_by=self.depot_fp)

    def _mk_client(self, user):
        token = Token.objects.create(user=user)
        c = APIClient()
        c.credentials(HTTP_AUTHORIZATION='Token ' + token.key)
        return c

    # ========== Device Tests ========== #
    def test_device_list_visibility(self):
        # Senior sees all
        resp = self.client_senior.get(reverse('fl-device-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 2)
        # Team member no assignment yet -> empty
        resp_mem = self.client_member.get(reverse('fl-device-list'))
        self.assertEqual(resp_mem.status_code, 200)
        self.assertEqual(len(resp_mem.data), 0)

    def test_device_create_requires_role(self):
        resp = self.client_other.post(reverse('fl-device-list'), {"serial_number": "SN-X", "description": "X"}, format='json')
        self.assertEqual(resp.status_code, 403)
        resp2 = self.client_senior.post(reverse('fl-device-list'), {"serial_number": "SN-C", "description": "New"}, format='json')
        self.assertEqual(resp2.status_code, 201)

    # ========== Team Tests ========== #
    def test_team_list_visibility(self):
        resp = self.client_senior.get(reverse('fl-team-list'))
        self.assertEqual(len(resp.data), 1)
        resp_lead = self.client_leader.get(reverse('fl-team-list'))
        self.assertEqual(len(resp_lead.data), 1)
        resp_other = self.client_other.get(reverse('fl-team-list'))
        self.assertEqual(resp_other.status_code, 403)

    def test_add_and_remove_member(self):
        add_url = reverse('fl-team-detail', args=[self.team.id]) + 'add_member/'
        rem_url = reverse('fl-team-detail', args=[self.team.id]) + 'remove_member/'
        # Senior adds other user as member
        resp = self.client_senior.post(add_url, {"user_id": self.other_user.id}, format='json')
        self.assertEqual(resp.status_code, 200, resp.data)
        # Remove
        resp2 = self.client_senior.post(rem_url, {"user_id": self.other_user.id}, format='json')
        self.assertEqual(resp2.status_code, 200, resp2.data)

    # ========== Fault Tests ========== #
    def test_fault_create_and_prioritize(self):
        list_url = reverse('fl-fault-list')
        # Team member create (has role) allowed? Should be 201 if allowed by broad HasFaultLocatorRole
        create_resp = self.client_member.post(list_url, {"description": "Fuse blown", "depot_id": self.depot_a.id}, format='json')
        self.assertEqual(create_resp.status_code, 201, create_resp.data)
        fault_id = create_resp.data['id']
        # Prioritize by senior
        prio_url = reverse('fl-fault-detail', args=[fault_id]) + 'prioritize/'
        prio_resp = self.client_senior.post(prio_url, {"priority": 4}, format='json')
        self.assertEqual(prio_resp.status_code, 200)
        # Invalid priority
        bad_resp = self.client_senior.post(prio_url, {"priority": 9}, format='json')
        self.assertEqual(bad_resp.status_code, 400)

    def test_fault_status_transition_located(self):
        # Assign fault then mark located
        assign = FaultAssignment.objects.create(fault=self.fault, team=self.team, device=self.device1, assigned_by=self.senior)
        status_url = reverse('fl-fault-detail', args=[self.fault.id]) + 'update_status/'
        resp = self.client_leader.post(status_url, {"status": "located"}, format='json')
        self.assertEqual(resp.status_code, 200, resp.data)
        assign.refresh_from_db()
        self.assertIsNotNone(assign.located_at)

    def test_fault_list_filters_team_scope(self):
        # Fault is in depot A; team has assignment => should appear after assignment
        FaultAssignment.objects.create(fault=self.fault, team=self.team, device=self.device1, assigned_by=self.senior)
        resp = self.client_leader.get(reverse('fl-fault-list'))
        self.assertEqual(resp.status_code, 200)
        ids = [f['id'] for f in resp.data]
        self.assertIn(self.fault.id, ids)

    # ========== Assignment Tests ========== #
    def test_create_fault_assignment(self):
        url = reverse('fl-assignment-list')
        data = {"fault_id": self.fault.id, "team_id": self.team.id, "device_id": self.device1.id}
        resp = self.client_senior.post(url, data, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        # Team leader should now see assignment
        resp2 = self.client_leader.get(url)
        self.assertEqual(len(resp2.data), 1)

    # ========== Device Assignment Tests ========== #
    def test_create_device_assignment_and_visibility(self):
        url = reverse('fl-device-assignment-list')
        resp = self.client_senior.post(url, {"device_id": self.device2.id, "team_id": self.team.id}, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        # Team leader sees it
        leader_resp = self.client_leader.get(url)
        self.assertEqual(len(leader_resp.data), 1)

    # ========== Deployment Tests ========== #
    def test_deployment_create_and_recall(self):
        url = reverse('fl-deployment-list')
        resp = self.client_senior.post(url, {"team_id": self.team.id, "depot_id": self.depot_a.id, "deployment_notes": "Cover area"}, format='json')
        self.assertEqual(resp.status_code, 201, resp.data)
        dep_id = resp.data['id']
        recall_url = reverse('fl-deployment-detail', args=[dep_id]) + 'recall/'
        recall_resp = self.client_senior.post(recall_url, {}, format='json')
        self.assertEqual(recall_resp.status_code, 200)
        # Double recall should fail
        recall_resp2 = self.client_senior.post(recall_url, {}, format='json')
        self.assertEqual(recall_resp2.status_code, 400)

    # ========== Role ViewSet Tests ========== #
    def test_role_creation_restricted(self):
        url = reverse('fl-role-list')
        # Non-senior should be forbidden
        deny = self.client_leader.post(url, {"user_id": self.team_member.id, "role": "team_member"}, format='json')
        self.assertEqual(deny.status_code, 403)
        allow = self.client_senior.post(url, {"user_id": self.other_user.id, "role": "team_member"}, format='json')
        self.assertEqual(allow.status_code, 201, allow.data)

    # ========== Negative / Edge Cases ========== #
    def test_invalid_status(self):
        status_url = reverse('fl-fault-detail', args=[self.fault.id]) + 'update_status/'
        resp = self.client_senior.post(status_url, {"status": "badstate"}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_unauthorized_access_blocked(self):
        # device list should block other_user (no role) through HasFaultLocatorRole
        resp = self.client_other.get(reverse('fl-device-list'))
        self.assertEqual(resp.status_code, 403)

    def test_invalid_priority_type(self):
        prio_url = reverse('fl-fault-detail', args=[self.fault.id]) + 'prioritize/'
        resp = self.client_senior.post(prio_url, {"priority": "abc"}, format='json')
        self.assertEqual(resp.status_code, 400)

    def test_assignment_visibility_for_depot_foreperson(self):
        # create assignment and confirm depot foreperson sees it (same depot)
        FaultAssignment.objects.create(fault=self.fault, team=self.team, device=self.device1, assigned_by=self.senior)
        resp = self.client_depot.get(reverse('fl-assignment-list'))
        self.assertEqual(resp.status_code, 200)
        self.assertEqual(len(resp.data), 1)

    def test_depot_foreperson_cannot_see_other_depot_fault(self):
        other_fault = Fault.objects.create(description='Remote issue', depot=self.depot_b, reported_by=self.senior)
        resp = self.client_depot.get(reverse('fl-fault-list'))
        ids = [f['id'] for f in resp.data]
        self.assertNotIn(other_fault.id, ids)

    def test_team_member_fault_visibility_requires_assignment_or_reporter(self):
        # Team member not reporter and no assignment -> should not see fault created earlier by depot foreperson
        resp = self.client_member.get(reverse('fl-fault-list'))
        ids = [f['id'] for f in resp.data]
        self.assertNotIn(self.fault.id, ids)
        # After assignment they should see it
        FaultAssignment.objects.create(fault=self.fault, team=self.team, device=self.device1, assigned_by=self.senior)
        resp2 = self.client_member.get(reverse('fl-fault-list'))
        ids2 = [f['id'] for f in resp2.data]
        self.assertIn(self.fault.id, ids2)
