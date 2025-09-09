from django.test import TestCase
from django.core.exceptions import ValidationError
from django.urls import reverse
from django.http import HttpResponse
from unittest.mock import patch
from io import BytesIO

from it.users.models import Regions, Sections, UserProfile, Roles, Application
from approve.models import Process, Workflow, Step, Approval
from .models import Pettycash
from .forms import CashierDisbursementForm, RequesterClearForm
from .views import send_uncleared_pettycash_reminders


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

	@patch("finance.PettyCash.views.QuotationFormSet")
	@patch("finance.PettyCash.views.notify_user")
	def test_create_pettycash_sends_section_head_notifications(self, mock_notify, mock_qfs):
		# Provide a dummy valid formset to bypass file upload requirements
		class _DummyFormSet:
			errors = []
			def __iter__(self):
				return iter([])
			def __len__(self):
				return 0
			def is_valid(self):
				return True
		mock_qfs.return_value = _DummyFormSet()
		# Ensure creator has pettycash 'create' role already from setUp
		self.client.force_login(self.creator)
		create_url = reverse('pettycash:create_pettycash')
		# Minimal valid POST for creation
		post_data = {
			'details_of_expenditure': 'Stationery',
			'amount': '100.00',
			'currency': 'ZIG',
			'section': str(self.section.id),
			'region': str(self.region.id),
		}
		# No quotations required because formset is min_num=1 but our create view tolerates empty cleaned_data in loop
		resp = self.client.post(create_url, data=post_data)
		# Redirect to detail on success
		self.assertEqual(resp.status_code, 302)
		# At least one notification should be attempted (to requester's section head or pettycash section head)
		self.assertTrue(mock_notify.called)
		# Validate signature: (user, msg, "PettyCash", url, petty_id, request)
		args, kwargs = mock_notify.call_args
		self.assertGreaterEqual(len(args), 6)
		self.assertEqual(args[2], "PettyCash")
		self.assertIn("/pettycash/pettycash_detail/", args[3])

	@patch("finance.PettyCash.views.notify_user")
	def test_cashier_disbursement_notifies_requester(self, mock_notify):
		# Give current user cashier role
		cashier_role = Roles.objects.create(name="Cashier", role="disburse", application="pettycash", description="")
		self.creator.roles.clear()
		self.creator.roles.add(cashier_role)
		self.client.force_login(self.creator)
		# Access detail and post disbursement
		detail_url = reverse('pettycash:pettycash_detail', args=[self.pc.petty_id])
		post_data = {
			'payment_mode': 'ZIG Cash',
			'amount_disbursed': '50.00',
		}
		resp = self.client.post(detail_url, data=post_data)
		# On success it redirects back to detail
		self.assertEqual(resp.status_code, 302)
		self.assertTrue(mock_notify.called)
		args, kwargs = mock_notify.call_args
		self.assertGreaterEqual(len(args), 6)
		self.assertEqual(args[2], "PettyCash")
		self.assertIn(self.pc.petty_id, args[3])


class PettyCashReminderTests(TestCase):
	def setUp(self):
		# Regions/Sections
		self.region = Regions.objects.create(region="R", code="R")
		self.section = Sections.objects.create(section="S", code="S", district_id="D", region_id=str(self.region.id))

		# Application and Roles
		self.app = Application.objects.create(name="pettycash")
		self.role_create = Roles.objects.create(name="Creator", role="create", application="pettycash", description="")
		self.role_disburse = Roles.objects.create(name="Cashier", role="disburse", application="pettycash", description="")

		# Users
		self.requester = UserProfile.objects.create(username="req", section=self.section, region=self.region)
		self.requester.roles.add(self.role_create)
		self.cashier = UserProfile.objects.create(username="cash", section=self.section, region=self.region)
		self.cashier.roles.add(self.role_disburse)

		# Workflow/Process and steps
		self.workflow = Workflow.objects.create(name="pc-rem", application=self.app)
		# Step numbers are arbitrary here; only role match matters
		self.step_disburse = Step.objects.create(workflow=self.workflow, approver=self.role_disburse, step=3)
		self.process = Process.objects.create(workflow=self.workflow)

		# Pettycash disbursed but not cleared
		self.pc = Pettycash.objects.create(
			petty_id="PCREM1",
			section=self.section,
			region=self.region,
			requested_by=self.requester,
			amount=100.0,
			amount_disbursed=100.0,
			process=self.process,
			currency="ZIG",
		)

	@patch("finance.PettyCash.views.notify_user")
	def test_uncleared_reminder_sent_when_overdue(self, mock_notify):
		# Create an approval at the disburse step older than cutoff
		from datetime import timedelta
		from django.utils import timezone as dj_timezone
		past_time = dj_timezone.now() - timedelta(days=10)
		appr = Approval.objects.create(step=self.step_disburse, user=self.cashier, process=self.process, approved='Approved')
		# Override auto_now_add by updating after creation
		appr.approved_at = past_time
		appr.save(update_fields=["approved_at"])

		count = send_uncleared_pettycash_reminders(None, days_overdue=3)
		self.assertEqual(count, 1)
		self.assertTrue(mock_notify.called)

	@patch("finance.PettyCash.views.notify_user")
	def test_no_reminder_when_recent(self, mock_notify):
		from datetime import timedelta
		from django.utils import timezone as dj_timezone
		recent = dj_timezone.now() - timedelta(days=1)
		appr = Approval.objects.create(step=self.step_disburse, user=self.cashier, process=self.process, approved='Approved')
		appr.approved_at = recent
		appr.save(update_fields=["approved_at"])

		count = send_uncleared_pettycash_reminders(None, days_overdue=3)
		self.assertEqual(count, 0)
		mock_notify.assert_not_called()
