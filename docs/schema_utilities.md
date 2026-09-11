# Schema utilities

Use `app1.utils` from scripts, commands, or application services. Creation
functions validate and run in a transaction: a failed port, record, or parameter
check rolls back the whole operation. They create new identities and revisions;
they do not upsert existing provenance nodes.

## Create entities and activities

### JSON fixtures

For repeatable imports, use `load_json_fixture` or the management command:

```bash
python manage.py load_json_fixture docs/example_fixture.json
cat docs/example_fixture.json | python manage.py load_json_fixture -
```

The top-level value must contain an `objects` array. Each entry has a unique
local `key`, a supported `model`, and a `fields` object. Objects are created in
array order, so references can point only to earlier entries. Foreign keys use
`"$key"`; references also work inside nested activity fields. Imports are
atomic: malformed references, duplicate identifiers, invalid ports, abstract
types, or protocol violations roll back the complete document. Existing rows
are never updated.

The vocabulary and ports must already exist. Entity and activity types must have
`is_instantiable=True`. Types can be passed as saved model instances or codes.

```python
from app1.utils import create_entity, create_activity, add_information_record

fresh = create_entity("whole_brain", identifier="B001-fresh", physical_identity="P001")
fixed = create_entity("whole_brain", identifier="B001-fixed", physical_identity="P001")

# These port names must be configured on the fixation ActivityType.
activity = create_activity(
    "fixation",
    identifier="FIX-001",
    ports={"specimen": fresh, "result": [fixed]},
    information={"protocol": protocol, "operator_agent": operator},
    parameters={"fixation_duration": 72, "operator_note": "cold room"},
)

revision = add_information_record(
    activity,
    protocol=protocol,
    operator_agent=operator,
    notes="Corrected duration",
    parameters={"fixation_duration": 76, "operator_note": "cold room"},
)
```

`protocol` and `operator` above are saved `Protocol` and `Agent` instances.
Parameter keys may be a `ParameterDefinition` instance or code. Unknown codes
become ad-hoc parameter names. Values are native Python strings, integers,
decimals/floats, booleans, datetimes, dictionaries, or lists. Known definitions
determine datatype validation and the canonical unit. Defaults from protocols
are not substituted for observed execution values.

Ports accept their declared entity type exactly, matching the existing helper's
behavior. Omitted ports have zero entities and must permit that count. Repeated
entities within a port, unknown ports, wrong types, and invalid cardinalities
raise `ValidationError`. An accession may have output ports with no input ports.

For entities with required information slots, create their records atomically:

```python
brain = create_entity(
    "whole_brain",
    identifier="B002",
    information_records=[
        {"information_record_type": "anatomical", "name": "Whole brain"},
        {"information_record_type": "storage", "metadata": {"freezer": "F1"}},
    ],
)
```

Each `add_information_record` call appends a new row. Version numbers are global
per entity/activity, as required by the schema's uniqueness constraints. Entity
revisions supersede the latest record of the same information record type;
activity revisions supersede the latest activity record. The subject row is
locked during version allocation on databases supporting row locks. All writers
must follow that locking convention for it to coordinate concurrent writes.

Every revision is a complete supplied snapshot: omitted metadata, protocol,
operator, and parameter values are **not copied** from the previous revision.
Historical records are not modified or automatically given a `valid_until` date.

## Traverse and group

```python
from app1.models import Entity, EntityType
from app1.utils import (
    descendant_types, entries_of_type, group_by_type, count_by_type,
    traverse_entities, latest_information_record,
)

inputs = activity.inputs
outputs = activity.outputs
ancestors = traverse_entities(fixed)  # upstream by default
children = traverse_entities(fresh, direction="downstream", max_depth=1)

material_type = EntityType.objects.get(code="material_entity")
types = descendant_types(material_type)  # includes the root by default
materials = entries_of_type(material_type)  # includes descendant types
exact = entries_of_type(material_type, include_descendants=False)
groups = group_by_type(materials)  # {type_code: [Entity, ...]}
counts = count_by_type(materials)  # {type_code: count}, aggregated in the DB

latest = latest_information_record(activity)
storage = latest_information_record(brain, record_type="storage")
```

Traversal follows input/output ports through activities, one activity per depth
step. It deduplicates entities, excludes the starting entity, and terminates
even if existing data contains cycles. It does not follow `EntityRelation`
edges. Depth zero returns no entities. Results are querysets ordered by primary
key, not traversal distance. Type traversal is also cycle-safe.

Grouping and counts use exact assigned type codes. First use `entries_of_type`
to select an entire type subtree. Group entities and activities separately.
`group_by_type` materializes objects; `count_by_type` takes a queryset.
The latest record is selected by version, not by validity dates.

## Validate existing entries

```python
from django.core.exceptions import ValidationError
from app1.utils import validate_entry, validate_protocol_parameters

try:
    validate_entry(activity)
    validate_entry(brain)
    validate_protocol_parameters(revision)
except ValidationError as error:
    print(error.messages)
```

`validate_entry` calls Django field and uniqueness validation and adds checks for:

- Instantiable entity/activity/record types and cycles in type hierarchies.
- Activity port ownership, entity types, counts, and count configuration.
- Positive revision numbers, date ordering, and same-subject/type predecessors.
- Exactly one parameter value, its declared datatype, and canonical units.
- Required protocol parameters and their declared units and numeric bounds.
- Entity information slots, counting revision heads rather than historical rows.

Slot rules apply to the entity's exact type; they are not inherited from ancestor
entity types. A slot's `match_mode` controls exact/descendant **record type**
matching. All declared rules are evaluated independently. Slots do not prohibit
additional unlisted record types. Standalone `add_information_record` calls
validate the new record; call `validate_entry(entity)` after assembling sidecars
to check the complete slot configuration. `create_entity` does this automatically.

Validation is opt-in and is not automatically invoked by admin or direct ORM
writes. It is not a recursive audit of every related object. `complete=False`
skips aggregate completeness checks while an object is being assembled.
The utilities do not enforce provenance acyclicity or immutability of direct
ORM writes. They do not yet add specialized rules for external references,
accession extensions, or entity relations beyond Django's model validation.

The current decimal fields have `decimal_places=0`. Integral decimal values are
accepted; fractional values are rejected rather than rounded. Supporting
fractional measurements requires a separate schema migration.

The helpers previously in `app1.views` now also live in `app1.utils`:

| Helper | Purpose |
| --- | --- |
| `create_activity_node` | Create a bare activity before adding links, or update by explicit `activity_id`; formerly `views.create_activity`. |
| `ensure_activity_port` | Get or create a named port. |
| `link_activity_entities` | Add entities to a port, optionally using explicit link IDs. |
| `create_activity_information_record` | Create a record with optional explicit version/ID, for imports. |
| `log_activity_parameters` | Add parameters to a new or supplied record; supports replacement. |
| `log_activity` | Incrementally assemble an activity using port names as keyword arguments. |
| `make_token`, `deterministic_token` | Generate random or deterministic identifier tokens. |

These incremental/import helpers retain their original behavior and do not
provide the full validation contract of `create_activity` and
`add_information_record`. In particular, explicit IDs can update existing rows,
and link validation checks the supplied batch rather than all existing links.
Use `validate_entry` to check completeness after incremental assembly.
`views.py` is reserved for HTTP views, and the sample loader imports from `utils`.

## Local tests

```bash
cd datamodel_demo
python manage.py test app1 --settings=datamodel_demo.test_settings
```

The test settings use an isolated in-memory SQLite database built from the model
definitions. No staging database, MySQL service, or Docker is required. These
tests exercise utility behavior but do not verify MySQL locking or migrations.
