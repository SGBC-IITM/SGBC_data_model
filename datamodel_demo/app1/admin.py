from django.contrib import admin
from .models import *

class InformativeModelAdmin(admin.ModelAdmin):
	"""Choose useful columns for generated models without per-model classes."""

	preferred_fields = (
		"code",
		"name",
		"identifier",
		"parent",
		"status",
		"direction",
		"version",
		"created_at",
	)

	def get_list_display(self, request):
		field_names = {field.name for field in self.model._meta.get_fields()}
		display = []

		for field_name in self.preferred_fields:
			if field_name not in field_names:
				continue
			display.append(f"display_{field_name}")

		if not display:
			display.append("display_id")

		return tuple(display)

	@staticmethod
	def _related_label(value):
		if value is None:
			return "-"
		for field_name in ("code", "name", "identifier"):
			label = getattr(value, field_name, None)
			if label:
				return label
		return str(value)

	@admin.display(description="Code", ordering="code")
	def display_code(self, obj):
		return obj.code

	@admin.display(description="Name", ordering="name")
	def display_name(self, obj):
		return obj.name

	@admin.display(description="Identifier", ordering="identifier")
	def display_identifier(self, obj):
		return obj.identifier

	@admin.display(description="Parent", ordering="parent")
	def display_parent(self, obj):
		return self._related_label(obj.parent)

	@admin.display(description="Status", ordering="status")
	def display_status(self, obj):
		return obj.status

	@admin.display(description="Direction", ordering="direction")
	def display_direction(self, obj):
		return obj.direction

	@admin.display(description="Version", ordering="version")
	def display_version(self, obj):
		return obj.version

	@admin.display(description="Created", ordering="created_at")
	def display_created_at(self, obj):
		return obj.created_at

	@admin.display(description="ID", ordering="id")
	def display_id(self, obj):
		return obj.pk
	
TIER_1_MODELS = [
    Entity,
    Activity,
    ActivityEntity,
    EntityInformationRecord,
    ActivityInformationRecord,
    EntityRelation,
]

TIER_2_MODELS = [
    EntityType,
    ActivityType,
    InformationRecordType,
    ParameterDefinition,
    ProtocolParameter,
    EntityRelationType,
]

TIER_3_MODELS = [
    # later
]

class AutoListDisplayMixin:
    def get_list_display(self, request):
        fields = [
            field.name
            for field in self.model._meta.fields
        ]
        return tuple(
			"display_parent" if field_name == "parent" else field_name
			for field_name in fields[:8]
		)

    @admin.display(description="Parent", ordering="parent")
    def display_parent(self, obj):
        return obj.parent.code if obj.parent else "-"

class Tier1Admin(AutoListDisplayMixin, admin.ModelAdmin):
    pass


class ActivityInformationRecordInline(admin.StackedInline):
	model = ActivityInformationRecord
	extra = 0
	show_change_link = True
	fields = (
		"version",
		"status",
		"valid_from",
		"valid_until",
		"recorded_at",
		"recorded_by_agent",
		"supersedes_record",
		"protocol",
		"operator_agent",
		"started_at",
		"ended_at",
		"description",
		"notes",
		"metadata",
	)


class ActivityEntityInline(admin.TabularInline):
	model = ActivityEntity
	extra = 0
	show_change_link = True
	fields = ("entity", "direction", "role", "sequence_no")


class EntityInformationRecordInline(admin.StackedInline):
	model = EntityInformationRecord
	extra = 0
	show_change_link = True
	fields = (
		"version",
		"information_record_type",
		"valid_from",
		"valid_until",
		"recorded_at",
		"recorded_by_agent",
		"supersedes_record",
		"name",
		"description",
		"status",
		"metadata",
	)


class ActivityAdmin(Tier1Admin):
	inlines = (ActivityInformationRecordInline, ActivityEntityInline)


class EntityAdmin(Tier1Admin):
	inlines = (EntityInformationRecordInline,)


class Tier2Admin(AutoListDisplayMixin, admin.ModelAdmin):
    pass


class ProtocolParameterInline(admin.TabularInline):
	model = ProtocolParameter
	extra = 0
	show_change_link = True
	fields = (
		"parameter_definition",
		"required",
		"default_value_text",
		"default_value_decimal",
		"minimum_value",
		"maximum_value",
		"unit",
		"description",
	)


class ProtocolAdmin(Tier2Admin):
	inlines = (ProtocolParameterInline,)


class Tier3Admin(admin.ModelAdmin):
    pass

admin.site.register(Activity, ActivityAdmin)
admin.site.register(Entity, EntityAdmin)
admin.site.register(Protocol, ProtocolAdmin)

for model in TIER_1_MODELS:
	if model not in (Activity, Entity):
		admin.site.register(model, Tier1Admin)

for model in TIER_2_MODELS:
	admin.site.register(model, Tier2Admin)
