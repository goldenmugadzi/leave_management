from unittest.mock import patch

from django.test import TestCase
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.http import HttpResponse

from it.users.models import UserProfile, Regions, Sections, Roles, Application
from .models import Ace2, AssetBudget, Transactions
from approve.models import Process, Workflow, Step, Approval


User = get_user_model()


class AceApprovalAfterActionTests(TestCase):
    def setUp(self):
        # Region/Section
        self.region = Regions.objects.create(region='Test Region')
        self.section = Sections.objects.create(section='Test Section', code='TS', district_id='D1', region_id='R1')

        # Application and Roles
        self.app = Application.objects.create(name='ace', fullname='ace')
        self.role_pass = Roles.objects.create(role='pass', name='Section Head', description='Section Head', application='ace', app_id=self.app)
        self.role_gm = Roles.objects.create(role='approve', name='GM', description='General Manager', application='ace', app_id=self.app)

        # Users
        self.user_pass = User.objects.create_user(username='sh001', password='testpass')
        # Since AUTH_USER_MODEL is users.UserProfile, use the created user object directly
        self.user_pass.region = self.region
        self.user_pass.section = self.section
        self.user_pass.save()
        self.user_pass.roles.add(self.role_pass)

        self.user_gm = User.objects.create_user(username='gm001', password='testpass')
        self.user_gm.region = self.region
        self.user_gm.section = self.section
        self.user_gm.save()
        self.user_gm.roles.add(self.role_gm)

        # Budget
        self.budget = AssetBudget.objects.create(
            budget_name='Test Budget', period=2025, region=self.region, balance=1000, to_be_withdrawn=0
        )

        # Workflow and process with two steps (section head then GM)
        self.workflow = Workflow.objects.create(name='ace', application=self.app)
        self.process = Process.objects.create(workflow=self.workflow)
        self.step1 = Step.objects.create(step=1, workflow=self.workflow, approver=self.role_pass, to='GM')
        self.step2 = Step.objects.create(step=2, workflow=self.workflow, approver=self.role_gm, to='END')

        # ACE and initial transaction
        self.ace = Ace2.objects.create(
            Ace_id2='ACE25010101',
            region=self.region,
            section=self.section,
            budget_id=self.budget,
            amount=300,
            process=self.process,
            details_of_expenditure='Test exp',
        )
        self.txn = Transactions.objects.create(
            Ace_id2=self.ace,
            details_of_expenditure='Test Expenditure',
            approval_status='created',
            region=self.region,
            amount=300,
            budget=self.budget,
            section=self.section,
        )

        # Reserve budget in to_be_withdrawn like during creation
        self.budget.to_be_withdrawn = 300
        self.budget.save()

    def _approve_step_as(self, user, step: int):
        self.client.login(username=user.username, password='testpass')
        # simulate that the user approves current next step via view
        # create an approval record to advance the process state
        step_obj = Step.objects.get(workflow=self.workflow, step=step)
        Approval.objects.create(
            step=step_obj,
            user=UserProfile.objects.get(id=user.id),
            process=self.process,
            approved='Approved'
        )

    def test_after_action_notification_failure_does_not_crash(self):
        # First approval by section head
        self._approve_step_as(self.user_pass, 1)

        # Before final approval, ensure approve_now triggers after last step
        # Last approval by GM; patch notify_user to raise
        with patch('ACE2.views.notify_user', side_effect=RuntimeError('notify failed')):
            # Create approval for final step to set approve_now
            self._approve_step_as(self.user_gm, 2)
            # Access detail view to execute approve_now block
            with patch('ACE2.views.render', side_effect=lambda req, tpl, ctx: HttpResponse('ok')):
                resp = self.client.get(reverse('Ace:ace_detail', args=[self.ace.Ace_id2]))
            self.assertEqual(resp.status_code, 200)

        # Validate no crash and budget/transaction updated
        self.budget.refresh_from_db()
        self.txn.refresh_from_db()
        self.assertEqual(self.txn.approval_status, 'approved by General Manager')
        self.assertAlmostEqual(self.budget.balance, 700)
        self.assertAlmostEqual(self.budget.withdrawn, 300)
        self.assertAlmostEqual(self.budget.to_be_withdrawn, 0)

    def test_after_action_no_transaction_does_not_crash(self):
        # Remove transaction deliberately
        Transactions.objects.filter(Ace_id2=self.ace).delete()

        # Approvals to reach final step
        self._approve_step_as(self.user_pass, 1)
        self._approve_step_as(self.user_gm, 2)

        # Ensure view loads without exception and doesn't crash
        with patch('ACE2.views.render', side_effect=lambda req, tpl, ctx: HttpResponse('ok')):
            resp = self.client.get(reverse('Ace:ace_detail', args=[self.ace.Ace_id2]))
        self.assertEqual(resp.status_code, 200)

        # Budget should not change since there is no transaction to mark
        self.budget.refresh_from_db()
        self.assertAlmostEqual(self.budget.balance, 1000)
        self.assertAlmostEqual(self.budget.to_be_withdrawn, 300)
