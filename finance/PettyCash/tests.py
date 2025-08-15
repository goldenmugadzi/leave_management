from django.test import TestCase
from django.core.exceptions import ValidationError
from django.contrib.auth import get_user_model

from it.users.models import Regions, Sections, UserProfile
from approve.models import Process
from .models import Pettycash
from .forms import CashierDisbursementForm


class CashierDisbursementValidationTests(TestCase):
	def setUp(self):
		# Minimal fixtures to create a Pettycash instance
		self.region = Regions.objects.create(region="TEST-REGION", code="TR")
		self.section = Sections.objects.create(section="TEST-SECTION", code="TS", region=self.region)

		# Create a dummy user profile if required by FK; using username field present on UserProfile
		self.user_profile = UserProfile.objects.create(username="tester")

		# Dummy process (nullable, but create to mirror reality)
		self.process = Process.objects.create(workflow=None)

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
