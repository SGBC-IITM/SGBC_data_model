from decimal import Decimal
from io import StringIO

from django.core.exceptions import ValidationError
from django.core.management import call_command
from django.test import TestCase

from .models import (
    Activity, ActivityEntity, ActivityType, ActivityTypePort, Entity,
    EntityType, EntityTypeRecordSlot, InformationRecordType,
    ParameterDefinition, Protocol, ProtocolParameter,
)
from .utils import (
    add_information_record, count_by_type, create_activity, create_entity,
    descendant_types, entries_of_type, group_by_type, latest_information_record,
    traverse_entities, validate_entry,
)


class SchemaUtilityTests(TestCase):
    def setUp(self):
        self.material = EntityType.objects.create(code="material", name="Material")
        self.brain = EntityType.objects.create(
            code="brain", name="Brain", parent=self.material, is_instantiable=True,
        )
        self.fixation = ActivityType.objects.create(
            code="fixation", name="Fixation", is_instantiable=True,
        )
        self.input = ActivityTypePort.objects.create(
            activity_type=self.fixation, name="specimen", direction="input",
            entity_type=self.brain, min_count=1, max_count=1,
        )
        self.output = ActivityTypePort.objects.create(
            activity_type=self.fixation, name="result", direction="output",
            entity_type=self.brain, min_count=1, max_count=1,
        )
        self.a = create_entity("brain", identifier="A")
        self.b = create_entity("brain", identifier="B")
        self.c = create_entity("brain", identifier="C")

    def activity(self, identifier="FIX-1", source=None, target=None, **kwargs):
        return create_activity("fixation", identifier=identifier, ports={
            "specimen": source or self.a, "result": target or self.b,
        }, **kwargs)

    def test_creation_does_not_overwrite_existing_activity(self):
        first = self.activity()
        second = self.activity("FIX-2")
        self.assertNotEqual(first.pk, second.pk)
        with self.assertRaises(ValidationError):
            self.activity()
        self.assertEqual(Activity.objects.count(), 2)
        self.assertEqual(ActivityEntity.objects.count(), 4)

    def test_abstract_types_rejected(self):
        with self.assertRaises(ValidationError):
            create_entity(self.material, identifier="abstract")
        self.assertFalse(Entity.objects.filter(identifier="abstract").exists())
        self.fixation.is_instantiable = False
        self.fixation.save()
        with self.assertRaises(ValidationError):
            self.activity()

    def test_invalid_ports_roll_back_activity_and_links(self):
        for ports in ({}, {"unknown": self.a}, {"specimen": [self.a, self.a], "result": self.b}):
            with self.subTest(ports=ports), self.assertRaises(ValidationError):
                create_activity(self.fixation, identifier="BAD", ports=ports)
        self.assertEqual(Activity.objects.count(), 0)
        self.assertEqual(ActivityEntity.objects.count(), 0)

    def test_wrong_entity_type_rolls_back(self):
        other = EntityType.objects.create(code="slide", name="Slide", is_instantiable=True)
        slide = create_entity(other, identifier="slide")
        with self.assertRaises(ValidationError):
            self.activity(target=slide)
        self.assertEqual(ActivityEntity.objects.count(), 0)

    def test_zero_input_activity(self):
        accession = ActivityType.objects.create(code="accession", name="Accession", is_instantiable=True)
        ActivityTypePort.objects.create(activity_type=accession, name="received", direction="output", entity_type=self.brain)
        activity = create_activity(accession, identifier="ACC", ports={"received": self.a})
        self.assertFalse(activity.inputs.exists())
        self.assertEqual(list(activity.outputs), [self.a])

    def test_traversal_depth_direction_and_cycles(self):
        first = self.activity()
        self.activity("FIX-2", self.b, self.c)
        self.assertEqual(list(first.inputs), [self.a])
        self.assertEqual(list(first.outputs), [self.b])
        self.assertEqual(list(traverse_entities(self.a, direction="downstream", max_depth=1)), [self.b])
        self.assertEqual(list(traverse_entities(self.c)), [self.a, self.b])
        self.assertFalse(traverse_entities(self.a, max_depth=0).exists())
        self.activity("CYCLE", self.c, self.a)
        self.assertEqual(set(traverse_entities(self.a)), {self.b, self.c})
        with self.assertRaises(ValueError):
            traverse_entities(self.a, max_depth=-1)

    def test_type_queries_grouping_and_counts(self):
        self.assertEqual(set(descendant_types(self.material)), {self.material, self.brain})
        self.assertEqual(entries_of_type(self.material).count(), 3)
        self.assertEqual(entries_of_type(self.material, include_descendants=False).count(), 0)
        self.assertEqual(group_by_type(Entity.objects.all()), {"brain": [self.a, self.b, self.c]})
        self.assertEqual(count_by_type(Entity.objects.all()), {"brain": 3})
        activity = self.activity()
        self.assertEqual(group_by_type(Activity.objects.all()), {"fixation": [activity]})

    def test_hierarchy_cycle_validation_and_safe_read(self):
        self.material.parent = self.brain
        with self.assertRaises(ValidationError):
            validate_entry(self.material)
        self.material.save()  # Simulate invalid data inserted outside the utilities.
        self.assertEqual(descendant_types(self.material).count(), 2)

    def test_record_revisions_are_append_only(self):
        activity = self.activity()
        first = add_information_record(activity, parameters={"note": "first"})
        second = add_information_record(activity, parameters={"note": "corrected"})
        first.refresh_from_db()
        self.assertEqual((first.version, second.version), (1, 2))
        self.assertEqual(second.supersedes_record, first)
        self.assertEqual(first.activityparameter_set.get().value_text, "first")
        self.assertEqual(latest_information_record(activity), second)

    def test_sidecars_use_global_versions_and_separate_predecessors(self):
        anatomy = InformationRecordType.objects.create(code="anatomy", name="Anatomy")
        storage = InformationRecordType.objects.create(code="storage", name="Storage")
        first = add_information_record(self.a, information_record_type=anatomy, name="Whole brain")
        second = add_information_record(self.a, information_record_type=storage)
        third = add_information_record(self.a, information_record_type="anatomy", name="Corrected")
        self.assertEqual((first.version, second.version, third.version), (1, 2, 3))
        self.assertIsNone(second.supersedes_record_id)
        self.assertEqual(third.supersedes_record, first)
        self.assertEqual(latest_information_record(self.a, record_type="storage"), second)

    def test_slot_counts_current_revisions_and_descendants(self):
        general = InformationRecordType.objects.create(code="general", name="General")
        anatomy = InformationRecordType.objects.create(code="anatomy", name="Anatomy", parent=general)
        EntityTypeRecordSlot.objects.create(entity_type=self.brain, record_type=general,
                                           min_count=1, max_count=1, match_mode="descendants")
        with self.assertRaises(ValidationError):
            create_entity(self.brain, identifier="missing")
        self.assertFalse(Entity.objects.filter(identifier="missing").exists())
        entity = create_entity(self.brain, identifier="complete", information_records=[{"information_record_type": anatomy}])
        add_information_record(entity, information_record_type=anatomy)
        validate_entry(entity)  # Two historical records are one current sidecar.

    def test_wrong_port_owner_is_detected(self):
        activity = self.activity()
        other_type = ActivityType.objects.create(code="other", name="Other", is_instantiable=True)
        foreign_port = ActivityTypePort.objects.create(activity_type=other_type, name="foreign",
                                                       direction="input", entity_type=self.brain)
        ActivityEntity.objects.create(activity=activity, entity=self.a, port=foreign_port)
        with self.assertRaises(ValidationError):
            validate_entry(activity)

    def test_typed_parameters_and_fractional_precision(self):
        ParameterDefinition.objects.create(code="temperature", name="Temperature", datatype="decimal", canonical_unit="degC")
        activity = self.activity()
        record = add_information_record(activity, parameters={"temperature": Decimal("4.0"), "ok": True})
        parameter = record.activityparameter_set.get(parameter_definition__code="temperature")
        self.assertEqual(parameter.value_decimal, Decimal("4"))
        self.assertEqual(parameter.unit, "degC")
        for value in (Decimal("4.3"), "four"):
            with self.subTest(value=value), self.assertRaises(ValidationError):
                add_information_record(activity, parameters={"temperature": value})
        self.assertEqual(activity.information_records.count(), 1)

    def test_protocol_required_and_bounds_rollback_entire_creation(self):
        definition = ParameterDefinition.objects.create(code="duration", name="Duration", datatype="integer", canonical_unit="h")
        protocol = Protocol.objects.create(identifier="P1", name="Fixation", version="1")
        ProtocolParameter.objects.create(protocol=protocol, parameter_definition=definition,
                                         required=1, minimum_value=24, maximum_value=80, unit="h")
        for parameters in ({}, {"duration": 12}, {"duration": 90}):
            with self.subTest(parameters=parameters), self.assertRaises(ValidationError):
                self.activity(information={"protocol": protocol}, parameters=parameters)
        self.assertEqual(Activity.objects.count(), 0)
        activity = self.activity(information={"protocol": protocol}, parameters={"duration": 72})
        self.assertEqual(latest_information_record(activity).protocol, protocol)

    def test_cross_subject_predecessor_and_date_validation(self):
        first = add_information_record(self.a)
        second = add_information_record(self.b)
        second.supersedes_record = first
        second.version = 2
        with self.assertRaises(ValidationError):
            validate_entry(second)
        with self.assertRaises(ValidationError):
            add_information_record(self.a, valid_from="2026-09-02T00:00:00Z", valid_until="2026-09-01T00:00:00Z")
        self.assertEqual(self.a.information_records.count(), 1)


class SampleLoaderUtilityTests(TestCase):
    def test_loader_uses_moved_helpers_and_preserves_fixation_revisions(self):
        from .management.commands.load_sample_data import SAMPLE_OBJECTS

        SAMPLE_OBJECTS.clear()
        self.addCleanup(SAMPLE_OBJECTS.clear)
        call_command("load_sample_data", stdout=StringIO())
        self.assertEqual(Activity.objects.count(), 8)
        fixation = Activity.objects.get(activity_type__code="fixation")
        self.assertEqual(list(fixation.information_records.order_by("version")
                              .values_list("version", flat=True)), [1, 2])
        self.assertEqual(fixation.inputs.count(), 1)
        self.assertEqual(fixation.outputs.count(), 1)
