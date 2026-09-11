from datetime import datetime
from decimal import Decimal

from django.test import TestCase
from django.utils.timezone import make_aware

from .models import (
	Activity,
	ActivityInformationRecord,
	ActivityParameter,
	ActivityType,
	ParameterDefinition,
)
from .utils import create_activity_node, log_activity_parameters

class LogActivityParametersTests(TestCase):
	def setUp(self):
		activity_type = ActivityType.objects.create(
			code="fixation",
			name="Fixation",
		)
		self.activity = Activity.objects.create(
			activity_type=activity_type,
			identifier="FIX-001",
		)
		ParameterDefinition.objects.create(
			code="temperature",
			name="Temperature",
			datatype="decimal",
			canonical_unit="degC",
		)

	def test_creates_record_and_typed_parameters(self):
		record = log_activity_parameters(
			self.activity,
			{
				"temperature": Decimal("4.0"),
				"operator_note": "cold room",
				"is_valid": True,
				"started": make_aware(datetime(2026, 9, 5, 12, 0)),
			},
		)

		self.assertEqual(record.version, 1)
		self.assertEqual(record.activity, self.activity)
		parameters = list(record.activityparameter_set.order_by("sequence_no"))
		self.assertEqual(parameters[0].value_decimal, Decimal("4.0"))
		self.assertEqual(parameters[0].unit, "degC")
		self.assertEqual(parameters[1].parameter_name, "operator_note")
		self.assertEqual(parameters[1].value_text, "cold room")
		self.assertEqual(parameters[2].value_boolean, 1)
		self.assertEqual(parameters[3].value_datetime.year, 2026)

	def test_increments_record_version(self):
		first = log_activity_parameters(self.activity, {"temperature": 4})
		second = log_activity_parameters(self.activity, {"temperature": 5})

		self.assertEqual(first.version, 1)
		self.assertEqual(second.version, 2)
		self.assertEqual(
			ActivityInformationRecord.objects.filter(activity=self.activity).count(),
			2,
		)
		self.assertEqual(ActivityParameter.objects.count(), 2)

	def test_creating_activity_without_id_preserves_existing_activity(self):
		second = create_activity_node(self.activity.activity_type, identifier="FIX-002")
		self.activity.refresh_from_db()
		self.assertNotEqual(second.pk, self.activity.pk)
		self.assertEqual(self.activity.identifier, "FIX-001")
