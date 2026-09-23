import json
from django.test import TestCase
from .utils import compile_json_draft


class DraftCompilerTests(TestCase):
    def test_explicit_inputs_outputs_compile(self):
        result = compile_json_draft({
            "entity_types": [{"id": "material_entity", "name": "Material"}],
            "activity_types": [{"id": "fixation", "name": "Fixation"}],
            "entities": [{"id": "a", "type": "material_entity"}, {"id": "b", "type": "material_entity"}],
            "activities": [{"id": "fix", "type": "fixation", "inputs": ["a"], "outputs": ["b"]}],
        })
        activity = next(item for item in result["objects"] if item["key"] == "fix")
        self.assertEqual(activity["fields"]["ports"], {"input": ["$a"], "output": ["$b"]})
        self.assertEqual(len(result["objects"]), 7)
