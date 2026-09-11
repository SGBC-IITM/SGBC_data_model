"""Schema operations. Writers validate and commit atomically; readers return querysets.

These checks are opt-in: direct ORM/admin writes do not call this module.
"""

import hashlib
import secrets

from collections import defaultdict
from collections.abc import Mapping
from datetime import datetime
from decimal import Decimal

from django.core.exceptions import ValidationError
from django.db import transaction
from django.db.models import Count
from django.utils import timezone
import json

from .models import (
    Activity, ActivityEntity, ActivityInformationRecord, ActivityParameter,
    ActivityType, ActivityTypePort, Entity, EntityInformationRecord,
    EntityType, EntityTypeRecordSlot, InformationRecordType, ParameterDefinition,
    Protocol, Agent,
)


FIXTURE_MODELS = {
    "entity_type": EntityType,
    "activity_type": ActivityType,
    "information_record_type": InformationRecordType,
    "parameter_definition": ParameterDefinition,
    "protocol": Protocol,
    "agent": Agent,
    "entity": Entity,
    "activity": Activity,
}


def _fixture_ref(value, cache):
    if isinstance(value, str) and value.startswith("$"):
        key = value[1:]
        if key not in cache:
            raise ValidationError(f"Unknown fixture reference: {value}")
        return cache[key]
    return value


def _resolve_nested(value, cache):
    if isinstance(value, Mapping):
        return {key: _resolve_nested(item, cache) for key, item in value.items()}
    if isinstance(value, list):
        return [_resolve_nested(item, cache) for item in value]
    return _fixture_ref(value, cache)


@transaction.atomic
def load_json_fixture(source, *, clear=False):
    """Load a JSON fixture transactionally and return objects keyed by ``key``.

    The document is ``{"objects": [{"model": "entity_type", "key": "brain",
    "fields": {...}}, ...]}``. Foreign keys use ``"$key"`` references.
    Activities use ``ports`` and ``information`` fields; entities may use
    ``information_records``. Existing rows are never overwritten: duplicate
    identifiers/codes fail and roll back the complete import.
    """
    if hasattr(source, "read"):
        document = json.load(source)
    elif isinstance(source, (str, bytes, bytearray)):
        document = json.loads(source)
    else:
        document = source
    if not isinstance(document, Mapping) or not isinstance(document.get("objects"), list):
        raise ValidationError("Fixture must contain an objects list.")
    cache = {}
    created = []
    for number, item in enumerate(document["objects"], 1):
        if not isinstance(item, Mapping):
            raise ValidationError(f"Object {number} must be an object.")
        model_name, key = item.get("model"), item.get("key")
        fields = item.get("fields", {})
        if model_name not in FIXTURE_MODELS or not isinstance(key, str) or not isinstance(fields, Mapping):
            raise ValidationError(f"Object {number} requires model, string key, and fields.")
        model = FIXTURE_MODELS[model_name]
        if key in cache:
            raise ValidationError(f"Duplicate fixture key: {key}")
        values = {name: _resolve_nested(value, cache) for name, value in fields.items()}
        if model is Entity:
            records = values.pop("information_records", ())
            obj = create_entity(values.pop("entity_type"), information_records=records, **values)
        elif model is Activity:
            ports = values.pop("ports", None)
            information = values.pop("information", None)
            parameters = values.pop("parameters", None)
            obj = create_activity(values.pop("activity_type"), identifier=values.pop("identifier"),
                                  ports=ports, information=information, parameters=parameters)
        else:
            obj = model(**values)
            validate_entry(obj, complete=False)
            obj.save()
        cache[key] = obj
        created.append(obj)
    return cache


def _resolve(model, value):
    if isinstance(value, str):
        return model.objects.get(code=value)
    if not isinstance(value, model) or value.pk is None or value._state.adding:
        raise ValidationError(f"Expected a saved {model.__name__} or its code.")
    return value


def descendant_types(type_node, *, include_self=True):
    """Return descendants of any hierarchical vocabulary node, safely across cycles."""
    model = type(type_node)
    _resolve(model, type_node)
    visited = {type_node.pk}
    frontier = visited.copy()
    while frontier:
        frontier = set(model.objects.filter(parent_id__in=frontier)
                       .values_list("pk", flat=True)) - visited
        visited.update(frontier)
    if not include_self:
        visited.remove(type_node.pk)
    return model.objects.filter(pk__in=visited).order_by("code")


def entries_of_type(type_node, *, include_descendants=True):
    """Return Entity or Activity rows classified under a saved type node."""
    if isinstance(type_node, EntityType):
        model, field = Entity, "entity_type"
    elif isinstance(type_node, ActivityType):
        model, field = Activity, "activity_type"
    else:
        raise TypeError("Expected EntityType or ActivityType")
    types = descendant_types(type_node) if include_descendants else [_resolve(type(type_node), type_node)]
    return model.objects.filter(**{f"{field}__in": types}).order_by("pk")


def group_by_type(entries):
    """Materialize Entity/Activity entries as {exact_type_code: [entries]}."""
    model = entries.model if hasattr(entries, "model") else None
    if model in (Entity, Activity):
        entries = entries.select_related("entity_type" if model is Entity else "activity_type")
    groups = defaultdict(list)
    kind = None
    for entry in entries:
        if not isinstance(entry, (Entity, Activity)):
            raise TypeError("Expected Entity or Activity entries")
        if kind is not None and type(entry) is not kind:
            raise TypeError("Group entities and activities separately")
        kind = type(entry)
        node = entry.entity_type if isinstance(entry, Entity) else entry.activity_type
        groups[node.code].append(entry)
    return dict(groups)


def count_by_type(entries):
    """Database aggregation for an Entity/Activity queryset, using exact types."""
    if entries.model not in (Entity, Activity):
        raise TypeError("Expected an Entity or Activity queryset")
    field = "entity_type__code" if entries.model is Entity else "activity_type__code"
    return dict(entries.order_by().values(field).annotate(count=Count("pk", distinct=True))
                .values_list(field, "count"))


def traverse_entities(entity, *, direction="upstream", max_depth=None):
    """Return reachable entities through activities, excluding the starting entity.

    One depth step crosses one activity. Cycles terminate; depth zero is empty.
    Additional EntityRelation edges are deliberately not followed.
    """
    _resolve(Entity, entity)
    if direction not in ("upstream", "downstream"):
        raise ValueError("direction must be upstream or downstream")
    if max_depth is not None and (type(max_depth) is not int or max_depth < 0):
        raise ValueError("max_depth must be a nonnegative integer or None")
    source, target = ("output", "input") if direction == "upstream" else ("input", "output")
    visited, frontier, depth = {entity.pk}, {entity.pk}, 0
    while frontier and (max_depth is None or depth < max_depth):
        activities = ActivityEntity.objects.filter(
            entity_id__in=frontier, port__direction=source,
        ).values_list("activity_id", flat=True)
        frontier = set(ActivityEntity.objects.filter(
            activity_id__in=activities, port__direction=target,
        ).values_list("entity_id", flat=True)) - visited
        visited.update(frontier)
        depth += 1
    visited.remove(entity.pk)
    return Entity.objects.filter(pk__in=visited).order_by("pk")


def latest_information_record(subject, *, record_type=None):
    """Latest recorded revision (not a valid-time/as-of query)."""
    if not isinstance(subject, (Entity, Activity)):
        raise TypeError("Expected Entity or Activity")
    _resolve(type(subject), subject)
    records = subject.information_records.all()
    if record_type is not None:
        if not isinstance(subject, Entity):
            raise TypeError("Only entity records have an information record type")
        records = records.filter(information_record_type=_resolve(InformationRecordType, record_type))
    return records.order_by("-version").first()


def _count_rule(label, count, minimum, maximum):
    if maximum is not None and maximum < minimum:
        raise ValidationError(f"{label}: maximum cannot be below minimum.")
    if count < minimum or (maximum is not None and count > maximum):
        raise ValidationError(f"{label}: found {count}; expected {minimum}..{maximum if maximum is not None else 'unbounded'}.")


def validate_port(port, entities, *, activity=None):
    """Ports accept their declared entity type exactly (no implicit subtype match)."""
    port.full_clean()
    if activity is not None and port.activity_type_id != activity.activity_type_id:
        raise ValidationError("Port belongs to another activity type.")
    entities = list(entities)
    for entity in entities:
        _resolve(Entity, entity)
        if entity.entity_type_id != port.entity_type_id:
            raise ValidationError(f"{port.name}: {entity.identifier} has the wrong entity type.")
    if len({entity.pk for entity in entities}) != len(entities):
        raise ValidationError(f"{port.name}: duplicate entities.")
    _count_rule(port.name, len(entities), port.min_count, port.max_count)


def _validate_record(record):
    if record.version < 1:
        raise ValidationError("Record version must be positive.")
    if record.valid_from and record.valid_until and record.valid_from > record.valid_until:
        raise ValidationError("valid_until precedes valid_from.")
    subject_field = "entity_id" if isinstance(record, EntityInformationRecord) else "activity_id"
    previous = record.supersedes_record
    if previous:
        if getattr(previous, subject_field) != getattr(record, subject_field):
            raise ValidationError("A revision must supersede a record for the same subject.")
        if previous.version >= record.version:
            raise ValidationError("A revision must have a higher version than its predecessor.")
        if isinstance(record, EntityInformationRecord) and previous.information_record_type_id != record.information_record_type_id:
            raise ValidationError("A revision must retain its information record type.")
    if isinstance(record, ActivityInformationRecord):
        if record.started_at and record.ended_at and record.started_at > record.ended_at:
            raise ValidationError("ended_at precedes started_at.")
    elif record.information_record_type and not record.information_record_type.is_instantiable:
        raise ValidationError("Cannot instantiate an abstract information record type.")


def _validate_slots(entity):
    # Count current revision heads, not historical versions. Rules apply to the
    # entity's exact type; match_mode governs the information record type.
    records = list(entity.information_records.all())
    superseded = {record.supersedes_record_id for record in records}
    heads = [record for record in records if record.pk not in superseded]
    for rule in EntityTypeRecordSlot.objects.filter(entity_type=entity.entity_type).select_related("record_type"):
        allowed = {rule.record_type_id}
        if rule.match_mode == "descendants":
            allowed = set(descendant_types(rule.record_type).values_list("pk", flat=True))
        _count_rule(rule.record_type.code, sum(r.information_record_type_id in allowed for r in heads),
                    rule.min_count, rule.max_count)


_VALUE_FIELDS = {
    "text": "value_text", "integer": "value_integer", "decimal": "value_decimal",
    "boolean": "value_boolean", "datetime": "value_datetime", "json": "value_json",
}


def _validate_parameter(parameter):
    populated = [field for field in _VALUE_FIELDS.values() if getattr(parameter, field) is not None]
    if len(populated) != 1:
        raise ValidationError("A parameter must have exactly one value.")
    if parameter.parameter_definition_id:
        definition = parameter.parameter_definition
        expected_field = "value_text" if definition.datatype == "categorical" else _VALUE_FIELDS.get(definition.datatype)
        if expected_field != populated[0]:
            raise ValidationError(f"{definition.code}: value does not match datatype {definition.datatype}.")
        if definition.canonical_unit and parameter.unit != definition.canonical_unit:
            raise ValidationError(f"{definition.code}: expected unit {definition.canonical_unit}.")
    elif not parameter.parameter_name:
        raise ValidationError("An ad-hoc parameter requires a name.")
    if parameter.value_boolean not in (None, 0, 1):
        raise ValidationError("Boolean values must be 0 or 1.")


def validate_protocol_parameters(record):
    """Check required parameters, units, and numeric bounds; never fill defaults."""
    rows = list(record.activityparameter_set.select_related("parameter_definition"))
    for row in rows:
        validate_entry(row)
    if not record.protocol_id:
        return
    for rule in record.protocol.protocolparameter_set.select_related("parameter_definition"):
        matches = [row for row in rows if row.parameter_definition_id == rule.parameter_definition_id]
        if rule.required and not matches:
            raise ValidationError(f"Missing protocol parameter: {rule.parameter_definition.code}.")
        for row in matches:
            if rule.unit and row.unit != rule.unit:
                raise ValidationError(f"{rule.parameter_definition.code}: protocol unit mismatch.")
            value = row.value_decimal if row.value_decimal is not None else row.value_integer
            if rule.minimum_value is not None or rule.maximum_value is not None:
                if value is None:
                    raise ValidationError("Protocol numeric bounds require a numeric parameter.")
                if rule.minimum_value is not None and value < rule.minimum_value:
                    raise ValidationError(f"{rule.parameter_definition.code}: below protocol minimum.")
                if rule.maximum_value is not None and value > rule.maximum_value:
                    raise ValidationError(f"{rule.parameter_definition.code}: above protocol maximum.")


def validate_entry(entry, *, complete=True):
    """Raise ValidationError for field/uniqueness and supported cross-row rules.

    complete=False skips activity port cardinality, entity slot counts, and
    protocol requirements while assembling a new object.
    """
    entry.full_clean()
    if isinstance(entry, (Entity, Activity)):
        node = entry.entity_type if isinstance(entry, Entity) else entry.activity_type
        if not node.is_instantiable:
            raise ValidationError(f"Cannot instantiate abstract type {node.code}.")
        if complete and entry.pk:
            if isinstance(entry, Entity):
                _validate_slots(entry)
            else:
                links = list(entry.entity_links.select_related("port", "entity"))
                if any(link.port.activity_type_id != entry.activity_type_id for link in links):
                    raise ValidationError("Activity has a port belonging to another activity type.")
                for port in entry.activity_type.ports.all():
                    validate_port(port, [link.entity for link in links if link.port_id == port.pk], activity=entry)
    elif isinstance(entry, (EntityInformationRecord, ActivityInformationRecord)):
        _validate_record(entry)
        if complete and isinstance(entry, ActivityInformationRecord) and entry.pk:
            validate_protocol_parameters(entry)
    elif isinstance(entry, ActivityEntity):
        if entry.port.activity_type_id != entry.activity.activity_type_id:
            raise ValidationError("Port belongs to another activity type.")
        if entry.entity.entity_type_id != entry.port.entity_type_id:
            raise ValidationError("Entity does not match port type.")
    elif isinstance(entry, ActivityParameter):
        _validate_parameter(entry)
    elif isinstance(entry, (EntityType, ActivityType, InformationRecordType)):
        visited = {entry.pk} if entry.pk else set()
        parent = entry.parent
        while parent:
            if parent.pk in visited:
                raise ValidationError("Type hierarchy contains a cycle.")
            visited.add(parent.pk)
            parent = parent.parent
    elif isinstance(entry, (ActivityTypePort, EntityTypeRecordSlot)):
        if entry.max_count is not None and entry.max_count < entry.min_count:
            raise ValidationError("Maximum cannot be below minimum.")
    return entry


@transaction.atomic
def create_entity(entity_type, *, identifier, information_records=(), **fields):
    """Create an entity and optional sidecars, checking required slots at the end."""
    entity = Entity(entity_type=_resolve(EntityType, entity_type), identifier=identifier, **fields)
    validate_entry(entity, complete=False)
    entity.save()
    for values in information_records:
        add_information_record(entity, **values)
    validate_entry(entity)
    return entity


@transaction.atomic
def create_activity(activity_type, *, identifier, ports=None, information=None, parameters=None):
    """Create a complete activity. ports maps port names to entities or iterables."""
    activity = Activity(activity_type=_resolve(ActivityType, activity_type), identifier=identifier)
    validate_entry(activity, complete=False)
    configured = {port.name: port for port in activity.activity_type.ports.all()}
    supplied = {} if ports is None else ports
    if not isinstance(supplied, Mapping):
        raise TypeError("ports must be a mapping")
    unknown = set(supplied) - set(configured)
    if unknown:
        raise ValidationError(f"Unknown ports: {sorted(unknown)}.")
    activity.save()
    for name, port in configured.items():
        values = supplied.get(name, [])
        values = [values] if isinstance(values, Entity) else list(values)
        validate_port(port, values, activity=activity)
        for sequence, entity in enumerate(values, 1):
            ActivityEntity.objects.create(activity=activity, port=port, entity=entity, sequence_no=sequence)
    if information is not None or parameters is not None:
        add_information_record(activity, parameters=parameters, **(information or {}))
    validate_entry(activity)
    return activity


def _typed_value(value, definition):
    datatype = definition.datatype if definition else None
    if datatype == "decimal" and type(value) in (int, float, Decimal):
        return {"value_decimal": Decimal(str(value)).normalize()}
    if isinstance(value, bool):
        return {"value_boolean": int(value)}
    if isinstance(value, int):
        return {"value_integer": value}
    if isinstance(value, (float, Decimal)):
        return {"value_decimal": Decimal(str(value)).normalize()}
    if isinstance(value, datetime):
        return {"value_datetime": value}
    if isinstance(value, (dict, list)):
        return {"value_json": value}
    if isinstance(value, str):
        return {"value_text": value}
    raise ValidationError(f"Unsupported parameter value type: {type(value).__name__}.")


@transaction.atomic
def add_information_record(subject, *, parameters=None, **fields):
    """Append a revision; entity versions are global across sidecar types.

    Parameters are a complete snapshot for this revision, never copied from the
    predecessor. Lock the subject to serialize version allocation on MySQL.
    """
    if not isinstance(subject, (Entity, Activity)):
        raise TypeError("Expected Entity or Activity")
    _resolve(type(subject), subject)
    if set(fields) & {"id", "pk", "entity", "entity_id", "activity", "activity_id", "version", "supersedes_record", "supersedes_record_id"}:
        raise TypeError("Identity, version, and predecessor are assigned automatically")
    subject = type(subject).objects.select_for_update().get(pk=subject.pk)
    latest = latest_information_record(subject)
    previous = latest
    if isinstance(subject, Entity):
        if parameters is not None:
            raise TypeError("Parameters belong to activities")
        record_type = fields.get("information_record_type")
        if record_type is not None:
            record_type = _resolve(InformationRecordType, record_type)
            fields["information_record_type"] = record_type
        if "information_record_type_id" in fields:
            raise TypeError("Use information_record_type with a saved type or code")
        previous = subject.information_records.filter(information_record_type=record_type).order_by("-version").first()
        record = EntityInformationRecord(entity=subject, **fields)
    else:
        record = ActivityInformationRecord(activity=subject, **fields)
    record.version = latest.version + 1 if latest else 1
    record.supersedes_record = previous
    if record.recorded_at is None:
        record.recorded_at = timezone.now()
    validate_entry(record, complete=False)
    record.save()
    if parameters is not None:
        if not isinstance(parameters, Mapping):
            raise TypeError("parameters must map names or definitions to values")
        for sequence, (key, value) in enumerate(parameters.items(), 1):
            definition = _resolve(ParameterDefinition, key) if isinstance(key, ParameterDefinition) else ParameterDefinition.objects.filter(code=key).first()
            parameter = ActivityParameter(
                activity_information_record=record, parameter_definition=definition,
                parameter_name=None if definition else str(key),
                unit=definition.canonical_unit if definition else None,
                sequence_no=sequence, **_typed_value(value, definition),
            )
            validate_entry(parameter)
            parameter.save()
    validate_entry(record)
    return record


# Incremental/import helpers retained from views.py. These allow partial rows
# and explicit-ID updates; use create_activity/add_information_record for validation.

ALPHABET = "23456789ABCDEFGHJKLMNPQRSTUVWXYZ"


def _parameter_values(value):
    if isinstance(value, bool):
        return {"value_boolean": int(value)}
    if isinstance(value, int):
        return {"value_integer": value}
    if isinstance(value, (Decimal, float)):
        return {"value_decimal": value}
    if isinstance(value, datetime):
        return {"value_datetime": value}
    if isinstance(value, (dict, list, tuple)):
        return {"value_json": value}
    return {"value_text": value}


@transaction.atomic
def create_activity_information_record(
    activity,
    *,
    record_id=None,
    recorded_at=None,
    version=None,
    **record_fields,
):
    activity = Activity.objects.select_for_update().get(pk=activity.pk)
    if version is None:
        last_record = activity.information_records.order_by("-version").first()
        version = last_record.version + 1 if last_record else 1

    values = {
        "activity": activity,
        "version": version,
        "recorded_at": recorded_at or timezone.now(),
        **record_fields,
    }
    if record_id is None:
        return ActivityInformationRecord.objects.create(**values)
    return ActivityInformationRecord.objects.update_or_create(
        pk=record_id, defaults=values,
    )[0]


@transaction.atomic
def log_activity_parameters(
    activity,
    parameters,
    *,
    record=None,
    replace=False,
    **record_fields,
):
    """Create an activity information record and its execution parameters."""
    if not isinstance(parameters, Mapping):
        raise TypeError("parameters must be a mapping of names to values")

    if record is None:
        record = create_activity_information_record(
            activity,
            **record_fields,
        )
    elif replace:
        ActivityParameter.objects.filter(
            activity_information_record=record
        ).delete()

    parameter_rows = []
    for sequence_no, (parameter, value) in enumerate(parameters.items(), start=1):
        definition = (
            parameter
            if isinstance(parameter, ParameterDefinition)
            else ParameterDefinition.objects.filter(code=parameter).first()
        )
        values = _parameter_values(value)
        parameter_rows.append(
            ActivityParameter(
                activity_information_record=record,
                parameter_definition=definition,
                parameter_name=None if definition else str(parameter),
                unit=definition.canonical_unit if definition else None,
                sequence_no=sequence_no,
                **values,
            )
        )

    ActivityParameter.objects.bulk_create(parameter_rows)
    return record


def create_activity_node(
    activity_type,
    *,
    activity_id=None,
    identifier,
):
    if isinstance(activity_type, str):
        activity_type = ActivityType.objects.get(code=activity_type)

    values = {"activity_type": activity_type, "identifier": identifier}
    if activity_id is None:
        return Activity.objects.create(**values)
    return Activity.objects.update_or_create(pk=activity_id, defaults=values)[0]


def ensure_activity_port(
    activity_type,
    *,
    name,
    direction,
    entity_type,
):
    if isinstance(activity_type, str):
        activity_type = ActivityType.objects.get(code=activity_type)

    return ActivityTypePort.objects.get_or_create(
        activity_type=activity_type,
        name=name,
        defaults={
            "direction": direction,
            "entity_type": entity_type,
        },
    )[0]


def link_activity_entities(
    activity,
    port,
    entities,
    *,
    sequence_start=1,
    link_ids=None,
):
    values = list(entities)
    validate_port(port, values)
    links = []
    for sequence, entity in enumerate(values):
        defaults = {
            "activity": activity,
            "entity": entity,
            "port": port,
            "sequence_no": sequence_start + sequence,
        }
        if link_ids:
            links.append(
                ActivityEntity.objects.update_or_create(
                    pk=link_ids[sequence],
                    defaults=defaults,
                )[0]
            )
        else:
            links.append(ActivityEntity.objects.create(**defaults))
    return links


@transaction.atomic
def log_activity(
    activity_type,
    *,
    parameters=None,
    activity_id=None,
    identifier=None,
    **entities,
):
    if isinstance(activity_type, str):
        activity_type = ActivityType.objects.get(
            code=activity_type
        )

    ports = {
        port.name: port
        for port in activity_type.ports.select_related(
            "entity_type"
        )
    }

    # Check unknown arguments
    unknown = set(entities) - set(ports)

    if unknown:
        raise ValidationError(
            f"Unknown ports for {activity_type.code}: "
            f"{sorted(unknown)}"
        )

    normalized = {}

    for name, port in ports.items():
        value = entities.get(name)

        if value is None:
            values = []
        elif isinstance(value, Entity):
            values = [value]
        else:
            values = list(value)

        validate_port(port, values)

        normalized[name] = values

    if identifier is None:
        raise ValueError("identifier is required")

    activity = create_activity_node(
        activity_type,
        activity_id=activity_id,
        identifier=identifier,
    )

    for name, values in normalized.items():
        port = ports[name]

        link_activity_entities(activity, port, values)

    if parameters:
        log_activity_parameters(
            activity,
            parameters,
        )

    return activity


def make_token(length=10):
    return "".join(
        secrets.choice(ALPHABET)
        for _ in range(length)
    )


def deterministic_token(user_id, timestamp, namespace, length=10):
    material = f"{namespace}:{user_id}:{timestamp}".encode()
    return hashlib.sha256(material).hexdigest()[:length].upper()
