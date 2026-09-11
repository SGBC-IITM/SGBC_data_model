"""HTTP views for app1. Schema utilities live in app1.utils."""

from django.http import JsonResponse
from django.shortcuts import render

from .models import Activity, ActivityEntity, Entity


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
