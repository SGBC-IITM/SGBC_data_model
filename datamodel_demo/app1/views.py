from datetime import datetime
from decimal import Decimal
from collections.abc import Mapping
from uuid import uuid4

from django.shortcuts import render

# Create your views here.

from django.core.exceptions import ValidationError
from django.db import transaction
from django.utils import timezone

from .models import (
    ActivityType,
    Entity,
    Activity,
    ActivityEntity,
    ActivityTypePort,
    ActivityInformationRecord,
    ActivityParameter,
    ParameterDefinition,
)

def _validate_port(port, entities):
    count = len(entities)

    if count < port.min_count:
        raise ValidationError(
            f"{port.name} requires at least "
            f"{port.min_count} entities."
        )

    if (
        port.max_count is not None
        and count > port.max_count
    ):
        raise ValidationError(
            f"{port.name} allows at most "
            f"{port.max_count} entities."
        )

    for entity in entities:
        if entity.entity_type_id != port.entity_type_id:
            raise ValidationError(
                f"{port.name} requires EntityType "
                f"{port.entity_type.code}; "
                f"{entity.identifier} is "
                f"{entity.entity_type.code}."
            )


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


def create_activity_information_record(
    activity,
    *,
    record_id=None,
    recorded_at=None,
    version=None,
    **record_fields,
):
    if version is None:
        last_record = activity.information_records.order_by("-version").first()
        version = last_record.version + 1 if last_record else 1

    return ActivityInformationRecord.objects.update_or_create(
        pk=record_id or str(uuid4()),
        defaults={
            "activity": activity,
            "version": version,
            "recorded_at": recorded_at or timezone.now(),
            **record_fields,
        },
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
                id=str(uuid4()),
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


def create_activity(
    activity_type,
    *,
    activity_id=None,
    identifier,
):
    if isinstance(activity_type, str):
        activity_type = ActivityType.objects.get(code=activity_type)

    return Activity.objects.update_or_create(
        pk=activity_id or str(uuid4()),
        defaults={
            "activity_type": activity_type,
            "identifier": identifier,
        },
    )[0]


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
    _validate_port(port, values)
    links = []
    for sequence, entity in enumerate(values):
        defaults = {
            "activity": activity,
            "entity": entity,
            "port": port,
            "sequence_no": sequence_start + sequence,
        }
        link_id = link_ids[sequence] if link_ids else str(uuid4())
        links.append(
            ActivityEntity.objects.update_or_create(
                pk=link_id,
                defaults=defaults,
            )[0]
        )
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

        _validate_port(port, values)

        normalized[name] = values

    if identifier is None:
        raise ValueError("identifier is required")

    activity = create_activity(
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