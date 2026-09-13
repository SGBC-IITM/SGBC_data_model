import json

from django.core.exceptions import ValidationError
from django.test import TestCase

from .models import Entity
from .utils import load_json_fixture
from pathlib import Path


class JsonFixtureTests(TestCase):
    def test_supplied_sample_fixture_is_valid(self):
        path = Path(__file__).parents[1].parent / "docs" / "sample_data_fixture.json"
        result = load_json_fixture(path.read_text(encoding="utf-8"))
        self.assertEqual(result["act_extraction"].identifier, "1949/26:extraction")
        self.assertEqual(Entity.objects.count(), 7)

    def test_references_and_atomic_rollback(self):
        fixture = {"objects": [
            {"model": "entity_type", "key": "brain", "fields": {
                "code": "brain", "name": "Brain", "is_instantiable": True}},
            {"model": "entity", "key": "one", "fields": {
                "entity_type": "$brain", "identifier": "B-001"}},
        ]}
        result = load_json_fixture(json.dumps(fixture))
        self.assertEqual(result["one"].entity_type.code, "brain")

        bad = {"objects": [
            {"model": "entity", "key": "two", "fields": {
                "entity_type": "$missing", "identifier": "B-002"}},
        ]}
        with self.assertRaises(ValidationError):
            load_json_fixture(bad)
        self.assertEqual(Entity.objects.count(), 1)
