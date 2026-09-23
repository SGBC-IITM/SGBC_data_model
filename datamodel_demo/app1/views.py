"""HTTP views for app1. Schema utilities live in app1.utils."""

from django.contrib import admin
from django.core.paginator import Paginator
from django.db.models import Prefetch, Q
from django.http import HttpResponse, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.template.loader import render_to_string

from .models import Activity, ActivityEntity, ActivityInformationRecord, Entity, EntityInformationRecord


def _timeline_rows(entity_page):
    """Turn prefetched entities into presentation-friendly timeline rows."""
    rows = []
    for entity in entity_page:
        activities = {}
        for link in entity.timeline_links:
            activity = link.activity
            # An entity can occupy more than one port on the same activity.
            activities.setdefault(activity.pk, activity)

        def activity_time(activity):
            sidecar = activity.timeline_sidecars[0] if activity.timeline_sidecars else None
            value = sidecar.started_at if sidecar and sidecar.started_at else activity.created_at
            return value.timestamp()

        ordered = sorted(activities.values(), key=activity_time)
        rows.append({"entity": entity, "activities": ordered})
    return rows


def _timeline_entities():
    """Entity queryset with everything needed to render a timeline lane."""
    entity_sidecars = EntityInformationRecord.objects.order_by("-version", "-recorded_at")
    sidecars = ActivityInformationRecord.objects.select_related(
        "protocol", "operator_agent", "recorded_by_agent"
    ).order_by("-version", "-recorded_at")
    outputs = ActivityEntity.objects.filter(port__direction="output").select_related(
        "entity", "entity__entity_type", "port"
    ).prefetch_related(
        Prefetch("entity__information_records", queryset=entity_sidecars, to_attr="timeline_sidecars")
    ).order_by("sequence_no", "entity__identifier")
    links = ActivityEntity.objects.select_related(
        "activity", "activity__activity_type", "port"
    ).prefetch_related(
        Prefetch("activity__information_records", queryset=sidecars, to_attr="timeline_sidecars"),
        Prefetch("activity__entity_links", queryset=outputs, to_attr="timeline_output_links"),
    ).order_by("activity__created_at")
    return Entity.objects.select_related("entity_type").prefetch_related(
        Prefetch("activity_links", queryset=links, to_attr="timeline_links")
    )


def activity_timeline_dashboard(request):
    """Paginated Unfold dashboard of entity activity swimlanes."""
    query = request.GET.get("q", "").strip()
    entity_type = request.GET.get("entity_type", "").strip()
    if entity_type and not entity_type.isdecimal():
        entity_type = ""

    entities = _timeline_entities().order_by("identifier")

    if query:
        entities = entities.filter(
            Q(identifier__icontains=query)
            | Q(physical_identity__icontains=query)
            | Q(entity_type__name__icontains=query)
            | Q(entity_type__code__icontains=query)
        )
    if entity_type:
        entities = entities.filter(entity_type_id=entity_type)

    page = Paginator(entities, 12).get_page(request.GET.get("page"))
    context = {
        **admin.site.each_context(request),
        "title": "Activity timelines",
        "subtitle": "Physical entities and their subsequent provenance activities",
        "page": page,
        "rows": _timeline_rows(page.object_list),
        "query": query,
        "selected_entity_type": entity_type,
        "entity_types": Entity.objects.values_list(
            "entity_type_id", "entity_type__name"
        ).distinct().order_by("entity_type__name"),
    }
    return render(request, "app1/activity_timeline_dashboard.html", context)


def activity_timeline_lane(request, entity_id):
    """Render one additional lane for progressive provenance exploration."""
    entity = get_object_or_404(_timeline_entities(), pk=entity_id)
    row = _timeline_rows([entity])[0]
    html = render_to_string("app1/_activity_timeline_lane.html", {"row": row}, request=request)
    return HttpResponse(html)


def graph_explorer(request):
    return render(request, "app1/graph_explorer.html")


def graph_data(request):
    """Return the provenance graph in a D3-friendly node/link shape."""
    nodes = []
    for entity in Entity.objects.select_related("entity_type"):
        nodes.append({"id": f"entity:{entity.pk}", "kind": "entity",
                      "label": entity.identifier, "type": entity.entity_type.code,
                      "type_name": entity.entity_type.name,
                      "annotation": entity.physical_identity or ""})
    for activity in Activity.objects.select_related("activity_type"):
        nodes.append({"id": f"activity:{activity.pk}", "kind": "activity",
                      "label": activity.identifier, "type": activity.activity_type.code,
                      "type_name": activity.activity_type.name})
    links = []
    for edge in ActivityEntity.objects.select_related("activity", "entity", "port"):
        source = f"entity:{edge.entity_id}" if edge.port.direction == "input" else f"activity:{edge.activity_id}"
        target = f"activity:{edge.activity_id}" if edge.port.direction == "input" else f"entity:{edge.entity_id}"
        links.append({"source": source, "target": target, "direction": edge.port.direction,
                      "role": edge.port.name, "sequence": edge.sequence_no})
    return JsonResponse({"nodes": nodes, "links": links})
