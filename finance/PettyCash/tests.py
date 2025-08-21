from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http import HttpResponse
from unittest.mock import patch

from it.users.models import Regions, Sections, UserProfile, Roles, Application
from approve.models import Process, Workflow, Step, Approval
from .models import Pettycash
from .forms import CashierDisbursementForm, RequesterClearForm


class CashierDisbursementValidationTests(TestCase):
	def setUp(self):
		# Minimal fixtures to create a Pettycash instance
		self.region = Regions.objects.create(region="TEST-REGION", code="TR")
		self.section = Sections.objects.create(section="TEST-SECTION", code="TS", district_id="D", region_id=str(self.region.id))

		# Create a dummy user profile if required by FK; using username field present on UserProfile
		self.user_profile = UserProfile.objects.create(username="tester")

		# Minimal workflow/process required by Process FK
		self.app = Application.objects.create(name="pettycash")
		self.workflow = Workflow.objects.create(name="pc-test", application=self.app)
		self.process = Process.objects.create(workflow=self.workflow)

		self.petty = Pettycash.objects.create(
			section=self.section,
			amount=100.00,
			requested_by=self.user_profile,
			petty_id="PCTEST1",
			process=self.process,
			region=self.region,
			currency="ZIG",
		)

	def test_form_rejects_amount_over_requested(self):
		form = CashierDisbursementForm(
			data={"payment_mode": "ZIG Cash", "amount_disbursed": 150.00}, pettycash=self.petty
		)
		self.assertFalse(form.is_valid())
		self.assertIn("amount_disbursed", form.errors)

	def test_model_clean_rejects_amount_over_requested(self):
		self.petty.amount_disbursed = 150.0
		with self.assertRaises(ValidationError):
			self.petty.full_clean()

	def test_model_clean_accepts_amount_equal_requested(self):
		self.petty.amount_disbursed = 100.0
		# Should not raise
		self.petty.full_clean()

	def test_model_clean_rejects_negative_amount(self):
		self.petty.amount_disbursed = -1.0
		with self.assertRaises(ValidationError):
			self.petty.full_clean()


class PettyCashAfterActionTests(TestCase):
	def setUp(self):
		# Regions/Sections
		self.region = Regions.objects.create(region="R", code="R")
		self.section = Sections.objects.create(section="S", code="S", district_id="D", region_id=str(self.region.id))

		# Minimal Applications and Roles for workflow
		self.app = Application.objects.create(name="pettycash")
		self.role_creator = Roles.objects.create(name="Creator", role="create", application="pettycash", description="")
		self.role_approver = Roles.objects.create(name="Approver", role="approve", application="pettycash", description="")

		# Users
		self.creator = UserProfile.objects.create(username="creator", section=self.section, region=self.region)
		self.creator.roles.add(self.role_creator)
		self.approver = UserProfile.objects.create(username="approver", section=self.section, region=self.region)
		self.approver.roles.add(self.role_approver)

		# Workflow/Process with two steps
		self.workflow = Workflow.objects.create(name="pc", application=self.app)
		self.step1 = Step.objects.create(workflow=self.workflow, approver=self.role_creator, step=1)
		self.step2 = Step.objects.create(workflow=self.workflow, approver=self.role_approver, step=2)
		self.process = Process.objects.create(workflow=self.workflow)

		# Pettycash
		self.pc = Pettycash.objects.create(
			petty_id="PC25010101",
			section=self.section,
			region=self.region,
			requested_by=self.creator,
			amount=50.0,
			process=self.process,
			currency="ZIG",
		)

		# First step approved by creator
		Approval.objects.create(step=self.step1, user=self.creator, process=self.process, approved='Approved')

		# Log creator in
		self.client.force_login(self.creator)

	def _final_approve(self):
		Approval.objects.create(step=self.step2, user=self.approver, process=self.process, approved='Approved')

	@patch("finance.PettyCash.views.render", autospec=True)
	@patch("finance.PettyCash.views.notify_user", side_effect=Exception("notify boom"))
	def test_pettycash_detail_notification_failure_does_not_crash(self, _notify, mock_render):
		mock_render.side_effect = lambda request, template, ctx: HttpResponse("OK")
		self._final_approve()
		resp = self.client.get(reverse('pettycash:pettycash_detail', args=[self.pc.petty_id]))
		self.assertEqual(resp.status_code, 200)

	@patch("finance.PettyCash.views.render", autospec=True)
	def test_pettycash_detail_missing_process_data_does_not_crash(self, mock_render):
		mock_render.side_effect = lambda request, template, ctx: HttpResponse("OK")
		# Remove approvals to simulate edge state and ensure view still responds
		self.process.approval_set.all().delete()
		resp = self.client.get(reverse('pettycash:pettycash_detail', args=[self.pc.petty_id]))
		self.assertEqual(resp.status_code, 200)
