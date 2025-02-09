from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.models import User
from it.users.models import UserProfile, Regions, Sections, Roles
from .models import Ace2, AssetBudget, Transactions
from approve.models import Process, Workflow, Step

class AceDetailViewTest(TestCase):
    def setUp(self):
        # Create a user and user profile
        self.user = User.objects.create_user(username='testuser', password='testpass')
        self.region = Regions.objects.create(region='Test Region')
        self.section = Sections.objects.create(section='Test Section')
        self.user_profile = UserProfile.objects.create(user=self.user, region=self.region, section=self.section)
        self.role = Roles.objects.create(role='approve', application='ace')
        self.user_profile.roles.add(self.role)

        # Create a budget
        self.budget = AssetBudget.objects.create(budget_name='Test Budget', period=2024, region=self.region, balance=1000)

        # Create a process and workflow
        self.workflow = Workflow.objects.create(name='Test Workflow')
        self.process = Process.objects.create(workflow=self.workflow)
        self.step = Step.objects.create(step=1, workflow=self.workflow, approver=self.role)

        # Create an Ace2 object
        self.ace = Ace2.objects.create(Ace_id2='ACE2023001', region=self.region, section=self.section, budget_id=self.budget, amount=500, process=self.process)

        # Create a transaction
        self.transaction = Transactions.objects.create(Ace_id2=self.ace, details_of_expenditure='Test Expenditure', approval_status='created', region=self.region, amount=500, budget=self.budget, section=self.section)

    def test_clear_minus_logic(self):
        self.client.login(username='testuser', password='testpass')
        response = self.client.get(reverse('Ace:ace_detail', args=[self.ace.Ace_id2]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'ACE2023001')
        self.assertContains(response, 'clear_minus')
