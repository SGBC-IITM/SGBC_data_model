from datetime import datetime

from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils.timezone import make_aware

from app1.models import (
    AccessionInformation,
    Activity,
    ActivityEntity,
    ActivityInformationRecord,
    ActivityParameter,
    ActivityType,
    ActivityTypePort,
    Agent,
    Entity,
    EntityInformationRecord,
    EntityProvenance,
    EntityRelation,
    EntityRelationType,
    EntityType,
    ExternalReference,
    InformationRecordType,
    ParameterDefinition,
    Protocol,
    ProtocolParameter,
)
from app1.utils import (
    create_activity_node,
    create_activity_information_record,
    ensure_activity_port,
    link_activity_entities,
    log_activity_parameters,
)


NOW = make_aware(datetime(2026, 9, 5, 12, 0))
SAMPLE_OBJECTS = {}


def dt(value):
    return make_aware(datetime.fromisoformat(value)) if value else None


def sample_key(namespace, number):
    return f"{namespace}_{int(number):03d}"


def normalize_key(key):
    parts = str(key).split("-")
    if len(parts) == 4:
        return "-".join((*parts[:-1], "0000", parts[-1]))
    return str(key)


def put(model, key, **values):
    cache_key = (model._meta.label, str(key))
    if cache_key not in SAMPLE_OBJECTS:
        SAMPLE_OBJECTS[cache_key] = model.objects.create(**values)
    obj = SAMPLE_OBJECTS[cache_key]
    return obj


def sample_object(model, key):
    return SAMPLE_OBJECTS[(model._meta.label, str(key))]


class Command(BaseCommand):
    help = "Load the SGBC provenance demonstration data using the Django ORM."

    def add_arguments(self, parser):
        parser.add_argument(
            "--clear",
            action="store_true",
            help="Delete existing app1 data before loading the demonstration data.",
        )

    @transaction.atomic
    def handle(self, *args, **options):
        if options["clear"]:
            self.clear_data()

        entity_types = self.load_types(EntityType, [
            (sample_key("entity_type", 1), "biological_source", "Biological Source", "Source biological subject", None),
            (sample_key("entity_type", 2), "donor", "Donor", "Human donor", sample_key("entity_type", 1)),
            (sample_key("entity_type", 10), "material_entity", "Material Entity", "Physical biological material", None),
            (sample_key("entity_type", 11), "biospecimen", "Biospecimen", "Primary biological specimen", sample_key("entity_type", 10)),
            (sample_key("entity_type", 12), "whole_brain", "Whole Brain", "Whole human brain specimen", sample_key("entity_type", 11)),
            (sample_key("entity_type", 13), "slab", "Brain Slab", "Macroscopic brain slab", sample_key("entity_type", 11)),
            (sample_key("entity_type", 14), "biosample", "Biosample", "Sample derived from a biospecimen", sample_key("entity_type", 10)),
            (sample_key("entity_type", 15), "tissue_section", "Tissue Section", "Histological tissue section", sample_key("entity_type", 14)),
            (sample_key("entity_type", 20), "physical_artifact", "Physical Artifact", "Physical artifact used or produced by processing", None),
            (sample_key("entity_type", 21), "slide", "Glass Slide", "Mounted histology slide", sample_key("entity_type", 20)),
            (sample_key("entity_type", 30), "digital_entity", "Digital Entity", "Digital data artifact", None),
            (sample_key("entity_type", 31), "image", "Image", "Digital image", sample_key("entity_type", 30)),
            (sample_key("entity_type", 32), "segmentation", "Segmentation", "Derived segmentation mask", sample_key("entity_type", 30)),
        ])
        activity_types = self.load_types(ActivityType, [
            (sample_key("activity_type", 1), "acquisition", "Acquisition", "Entry or acquisition of material", None),
            (sample_key("activity_type", 2), "accession", "Accession", "Material enters local custody without requiring a modeled upstream entity", sample_key("activity_type", 1)),
            (sample_key("activity_type", 10), "preservation", "Preservation", "Preservation activities", None),
            (sample_key("activity_type", 11), "fixation", "Fixation", "Tissue fixation", sample_key("activity_type", 10)),
            (sample_key("activity_type", 20), "processing", "Processing", "Physical tissue processing", None),
            (sample_key("activity_type", 21), "slabbing", "Slabbing", "Subdivision of whole brain into slabs", sample_key("activity_type", 20)),
            (sample_key("activity_type", 22), "sectioning", "Sectioning", "Microtome/cryostat sectioning", sample_key("activity_type", 20)),
            (sample_key("activity_type", 23), "mounting", "Mounting", "Mount tissue section on glass slide", sample_key("activity_type", 20)),
            (sample_key("activity_type", 24), "staining", "Staining", "Histological staining", sample_key("activity_type", 20)),
            (sample_key("activity_type", 30), "imaging", "Imaging", "Image acquisition", None),
            (sample_key("activity_type", 31), "slide_scanning", "Slide Scanning", "Whole-slide image acquisition", sample_key("activity_type", 30)),
            (sample_key("activity_type", 40), "computational_processing", "Computational Processing", "Computational derivation", None),
            (sample_key("activity_type", 41), "segmentation", "Segmentation", "Computational image segmentation", sample_key("activity_type", 40)),
        ])
        record_types = self.load_simple(InformationRecordType, [
            (sample_key("record_type", 1), "general", "General", "General descriptive information"),
            (sample_key("record_type", 2), "anatomical", "Anatomical", "Anatomical description and interpretation"),
            (sample_key("record_type", 3), "storage", "Storage", "Storage location and condition"),
            (sample_key("record_type", 4), "quality_control", "Quality Control", "QC observations and status"),
            (sample_key("record_type", 5), "imaging", "Imaging", "Image-specific descriptive information"),
        ])

        agents = self.load_agents()
        parameter_definitions = self.load_parameter_definitions()
        protocols = self.load_protocols(parameter_definitions)
        entities = self.load_entities(entity_types)
        activities = self.load_activities(activity_types)
        self.load_activity_entities(activities, entities)
        self.load_entity_records(entities, record_types, agents)
        activity_records = self.load_activity_records(activities, agents, protocols)
        self.load_accession_information(activity_records, agents)
        self.load_activity_parameters(activity_records, parameter_definitions)
        self.load_external_references(entities, activities)
        self.load_provenance(entities, activities)
        self.load_entity_relations(entities, activities)

        self.stdout.write(self.style.SUCCESS("Sample data loaded with the Django ORM."))

    def clear_data(self):
        for model in (
            ActivityParameter, AccessionInformation, EntityInformationRecord,
            ActivityInformationRecord, ActivityEntity, EntityRelation,
            EntityProvenance, ExternalReference, ProtocolParameter, Entity,
            Activity, Protocol, ParameterDefinition, Agent, InformationRecordType,
            EntityRelationType, EntityType, ActivityTypePort, ActivityType,
        ):
            model.objects.all().delete()

    def load_types(self, model, rows):
        objects = {}
        objects_by_key = {}
        for identifier, code, name, description, parent_id in rows:
            objects[code] = put(model, identifier, code=code, name=name, description=description)
            objects_by_key[identifier] = objects[code]
        for identifier, code, name, description, parent_id in rows:
            if parent_id:
                objects[code].parent = objects_by_key[parent_id]
                objects[code].save(update_fields=["parent"])
        return objects

    def load_simple(self, model, rows):
        return {code: put(model, identifier, code=code, name=name, description=description) for identifier, code, name, description in rows}

    def load_agents(self):
        rows = [
            (sample_key("agent", 1), "ORG-SGBC", "organization", "SGBC Histology Facility", "SGBC", None),
            (sample_key("agent", 2), "ORG-EXT-001", "organization", "External Neuropathology Centre", "External Institution", None),
            (sample_key("agent", 3), "USR-TECH-001", "person", "Histology Technician 01", "SGBC", None),
            (sample_key("agent", 4), "USR-SCI-001", "person", "Researcher 01", "SGBC", None),
            (sample_key("agent", 5), "SW-SEG-001", "software", "Neurohistology Segmentation Pipeline", "SGBC", {"version": "0.1-demo"}),
        ]
        return {identifier: put(Agent, identifier, identifier=identifier, agent_type=agent_type, name=name, affiliation=affiliation, metadata=metadata) for _, identifier, agent_type, name, affiliation, metadata in rows}

    def load_parameter_definitions(self):
        rows = [
            (sample_key("parameter_definition", 1), "fixative", "Fixative", "Fixative formulation", "text", None),
            (sample_key("parameter_definition", 2), "fixation_temperature", "Fixation Temperature", "Temperature during fixation", "decimal", "degC"),
            (sample_key("parameter_definition", 3), "fixation_duration", "Fixation Duration", "Duration of fixation", "decimal", "h"),
            (sample_key("parameter_definition", 4), "section_thickness", "Section Thickness", "Nominal section thickness", "decimal", "um"),
            (sample_key("parameter_definition", 5), "stain", "Stain", "Histological stain", "categorical", None),
            (sample_key("parameter_definition", 6), "scan_resolution", "Scan Resolution", "Pixel size at acquisition", "decimal", "um_per_pixel"),
            (sample_key("parameter_definition", 7), "model_name", "Model Name", "Computational model used", "text", None),
            (sample_key("parameter_definition", 8), "model_version", "Model Version", "Computational model version", "text", None),
        ]
        return {code: put(ParameterDefinition, identifier, code=code, name=name, description=description, datatype=datatype, canonical_unit=unit) for identifier, code, name, description, datatype, unit in rows}

    def load_protocols(self, definitions):
        protocols = {}
        rows = [
            (sample_key("protocol", 1), "PROT-FIX-001", "Whole Brain Fixation", "1.0", "Demo whole-brain immersion fixation protocol"),
            (sample_key("protocol", 2), "PROT-SEC-001", "Cryostat Sectioning", "1.0", "Demo serial sectioning protocol"),
            (sample_key("protocol", 3), "PROT-NISSL-001", "Nissl Staining", "1.0", "Demo Nissl staining protocol"),
            (sample_key("protocol", 4), "PROT-SCAN-001", "Whole Slide Scanning", "1.0", "Demo WSI acquisition protocol"),
        ]
        for identifier, code, name, version, description in rows:
            protocols[code] = put(Protocol, identifier, identifier=code, name=name, version=version, description=description)
        values = [
            (sample_key("protocol_parameter", 1), "PROT-FIX-001", "fixative", 1, "10% neutral buffered formalin", None, None, "Expected fixative"),
            (sample_key("protocol_parameter", 2), "PROT-FIX-001", "fixation_temperature", 1, None, 4.0, "degC", "Target temperature"),
            (sample_key("protocol_parameter", 3), "PROT-FIX-001", "fixation_duration", 1, None, 72.0, "h", "Target duration"),
            (sample_key("protocol_parameter", 4), "PROT-SEC-001", "section_thickness", 1, None, 20.0, "um", "Nominal section thickness"),
            (sample_key("protocol_parameter", 5), "PROT-NISSL-001", "stain", 1, "Nissl", None, None, "Required stain"),
            (sample_key("protocol_parameter", 6), "PROT-SCAN-001", "scan_resolution", 1, None, 0.5, "um_per_pixel", "Target scan resolution"),
        ]
        for identifier, protocol_code, definition_code, required, text, decimal, unit, description in values:
            put(ProtocolParameter, identifier, protocol=protocols[protocol_code], parameter_definition=definitions[definition_code], required=required, default_value_text=text, default_value_decimal=decimal, unit=unit, description=description)
        return protocols

    def load_entities(self, types):
        rows = [
            (sample_key("entity", 1), "whole_brain", "BRN-2026-001", "PHY-BRAIN-001"),
            (sample_key("entity", 2), "whole_brain", "BRN-2026-001-FIXED", "PHY-BRAIN-001"),
            (sample_key("entity", 11), "slab", "BRN-2026-001-SLAB-01", "PHY-SLAB-001"),
            (sample_key("entity", 12), "slab", "BRN-2026-001-SLAB-02", "PHY-SLAB-002"),
            (sample_key("entity", 13), "slab", "BRN-2026-001-SLAB-03", "PHY-SLAB-003"),
            (sample_key("entity", 21), "tissue_section", "BRN-2026-001-S02-SEC-001", "PHY-SEC-001"),
            (sample_key("entity", 22), "tissue_section", "BRN-2026-001-S02-SEC-002", "PHY-SEC-002"),
            (sample_key("entity", 23), "tissue_section", "BRN-2026-001-S02-SEC-003", "PHY-SEC-003"),
            (sample_key("entity", 31), "slide", "BRN-2026-001-S02-SLIDE-001", "PHY-SLIDE-001"),
            (sample_key("entity", 41), "image", "IMG-2026-001-S02-NISSL-001", None),
            (sample_key("entity", 51), "segmentation", "SEG-2026-001-S02-001", None),
        ]
        return {identifier: put(Entity, identifier, entity_type=types[type_code], identifier=entity_identifier, physical_identity=physical_identity) for identifier, type_code, entity_identifier, physical_identity in rows}

    def load_activities(self, types):
        rows = [
            (sample_key("activity", 1), "accession", "ACC-2026-001"),
            (sample_key("activity", 2), "fixation", "FIX-2026-001"),
            (sample_key("activity", 3), "slabbing", "SLAB-2026-001"),
            (sample_key("activity", 4), "sectioning", "SEC-2026-001"),
            (sample_key("activity", 5), "mounting", "MOUNT-2026-001"),
            (sample_key("activity", 6), "staining", "STAIN-2026-001"),
            (sample_key("activity", 7), "slide_scanning", "SCAN-2026-001"),
            (sample_key("activity", 8), "segmentation", "SEG-2026-001"),
        ]
        activities = {}
        for identifier, type_code, activity_identifier in rows:
            activity = create_activity_node(
                types[type_code],
                identifier=activity_identifier,
            )
            activities[identifier] = activity
            activities[normalize_key(identifier)] = activity
        return activities

    def load_activity_entities(self, activities, entities):
        rows = [
            (sample_key("activity_entity", 1), sample_key("activity", 1), sample_key("entity", 1), "output", "accessioned_specimen", 1),
            (sample_key("activity_entity", 2), sample_key("activity", 2), sample_key("entity", 1), "input", "unfixed_brain", 1),
            (sample_key("activity_entity", 3), sample_key("activity", 2), sample_key("entity", 2), "output", "fixed_brain", 1),
            (sample_key("activity_entity", 4), sample_key("activity", 3), sample_key("entity", 2), "input", "whole_brain", 1),
            (sample_key("activity_entity", 5), sample_key("activity", 3), sample_key("entity", 11), "output", "slab", 1),
            (sample_key("activity_entity", 6), sample_key("activity", 3), sample_key("entity", 12), "output", "slab", 2),
            (sample_key("activity_entity", 7), sample_key("activity", 3), sample_key("entity", 13), "output", "slab", 3),
            (sample_key("activity_entity", 8), sample_key("activity", 4), sample_key("entity", 12), "input", "source_slab", 1),
            (sample_key("activity_entity", 9), sample_key("activity", 4), sample_key("entity", 21), "output", "serial_section", 1),
            (sample_key("activity_entity", 10), sample_key("activity", 4), sample_key("entity", 22), "output", "serial_section", 2),
            (sample_key("activity_entity", 11), sample_key("activity", 4), sample_key("entity", 23), "output", "serial_section", 3),
            (sample_key("activity_entity", 12), sample_key("activity", 5), sample_key("entity", 22), "input", "tissue_section", 1),
            (sample_key("activity_entity", 13), sample_key("activity", 5), sample_key("entity", 31), "output", "mounted_slide", 1),
            (sample_key("activity_entity", 14), sample_key("activity", 6), sample_key("entity", 31), "input", "unstained_slide", 1),
            (sample_key("activity_entity", 15), sample_key("activity", 6), sample_key("entity", 31), "output", "nissl_stained_slide", 1),
            (sample_key("activity_entity", 16), sample_key("activity", 7), sample_key("entity", 31), "input", "source_slide", 1),
            (sample_key("activity_entity", 17), sample_key("activity", 7), sample_key("entity", 41), "output", "whole_slide_image", 1),
            (sample_key("activity_entity", 18), sample_key("activity", 8), sample_key("entity", 41), "input", "source_image", 1),
            (sample_key("activity_entity", 19), sample_key("activity", 8), sample_key("entity", 51), "output", "segmentation_mask", 1),
        ]
        for identifier, activity_id, entity_id, direction, role, sequence_no in rows:
            activity = activities[activity_id]
            entity = entities[entity_id]
            port = ensure_activity_port(
                activity.activity_type,
                name=role,
                direction=direction,
                entity_type=entity.entity_type,
            )
            link_activity_entities(
                activity,
                port,
                [entity],
                sequence_start=sequence_no,
            )

    def load_entity_records(self, entities, record_types, agents):
        rows = [
            (sample_key("entity_record", 1), sample_key("entity", 1), "general", 1, "Accessioned whole brain", "Whole brain received from external neuropathology centre", "received", {"condition": "received chilled", "container": "sealed specimen container"}, None),
            (sample_key("entity_record", 2), sample_key("entity", 2), "general", 1, "Fixed whole brain", "Whole brain after fixation", "available", {"fixation_state": "fixed"}, None),
            (sample_key("entity_record", 11), sample_key("entity", 11), "anatomical", 1, "Slab 01", "Anterior brain slab", "available", {"slab_index": 1, "orientation": "coronal"}, None),
            (sample_key("entity_record", 12), sample_key("entity", 12), "anatomical", 1, "Slab 02", "Anatomical assignment pending", "provisional", {"slab_index": 2, "anatomical_region": "unknown"}, None),
            (sample_key("entity_record", 13), sample_key("entity", 12), "anatomical", 2, "Slab 02", "Anatomical assignment reviewed", "confirmed", {"slab_index": 2, "anatomical_region": "left frontal region"}, sample_key("entity_record", 12)),
            (sample_key("entity_record", 14), sample_key("entity", 13), "anatomical", 1, "Slab 03", "Posterior brain slab", "available", {"slab_index": 3, "orientation": "coronal"}, None),
        ]
        records = {}
        for identifier, entity_id, type_code, version, name, description, status, metadata, supersedes in rows:
            records[identifier] = put(EntityInformationRecord, identifier, entity=entities[entity_id], information_record_type=record_types[type_code], version=version, recorded_at=NOW, recorded_by_agent=agents["USR-SCI-001"], supersedes_record=sample_object(EntityInformationRecord, supersedes) if supersedes else None, name=name, description=description, status=status, metadata=metadata)
        return records

    def load_activity_records(self, activities, agents, protocols):
        rows = [
            (sample_key("activity_record", 1), sample_key("activity", 1), "completed", None, "Accession of externally supplied whole brain", "No upstream local entity created; external provenance retained as accession metadata"),
            (sample_key("activity_record", 2), sample_key("activity", 2), "completed", "PROT-FIX-001", "Whole brain fixation", "Initial record entered with duration transcribed as 48 h"),
            (sample_key("activity_record", 3), sample_key("activity", 2), "completed", "PROT-FIX-001", "Whole brain fixation", "Corrected from source worksheet: fixation duration was 72 h"),
            (sample_key("activity_record", 4), sample_key("activity", 3), "completed", None, "Whole brain slabbing", "Demo subdivision into three slabs"),
            (sample_key("activity_record", 5), sample_key("activity", 4), "completed", "PROT-SEC-001", "Serial sectioning of slab 02", "Three representative sections inserted for demo"),
            (sample_key("activity_record", 6), sample_key("activity", 5), "completed", None, "Mount section 002", "Section mounted on glass slide"),
            (sample_key("activity_record", 7), sample_key("activity", 6), "completed", "PROT-NISSL-001", "Nissl staining", "Routine Nissl stain"),
            (sample_key("activity_record", 8), sample_key("activity", 7), "completed", "PROT-SCAN-001", "Whole-slide scanning", "Digitization of Nissl slide"),
            (sample_key("activity_record", 9), sample_key("activity", 8), "completed", None, "Gross anatomy segmentation", "Demo computational derivative"),
        ]
        records = {}
        for identifier, activity_id, status, protocol_code, description, notes in rows:
            supersedes = sample_key("activity_record", 2) if identifier.endswith("003") else None
            record = create_activity_information_record(
                activities[normalize_key(activity_id)],
                version=2 if supersedes else 1,
                recorded_at=NOW,
                recorded_by_agent=agents["USR-SCI-001"],
                supersedes_record=sample_object(ActivityInformationRecord, supersedes) if supersedes else None,
                status=status,
                protocol=protocols.get(protocol_code),
                description=description,
                notes=notes,
            )
            SAMPLE_OBJECTS[(ActivityInformationRecord._meta.label, identifier)] = record
            records[identifier] = record
            records[normalize_key(identifier)] = record
        return records

    def load_accession_information(self, records, agents):
        put(AccessionInformation, sample_key("activity_record", 1), activity_information_record=records[sample_key("activity_record", 1)], accession_number="SGBC-ACC-2026-001", accessioned_at=dt("2026-08-01 09:30:00"), source_organization_agent=agents["ORG-EXT-001"], received_by_agent=agents["USR-TECH-001"], external_specimen_identifier="EXT-BRAIN-7842", shipment_reference="SHIP-DEMO-8841", transfer_reference="MTA-DEMO-2026-17", provenance_status="external", source_description="Whole brain extracted and handled at external institution before transfer to SGBC", metadata={"received_condition": "chilled", "upstream_protocols_available": False})

    def load_activity_parameters(self, records, definitions):
        rows = [
            (sample_key("activity_parameter", 1), sample_key("activity_record", 2), "fixative", "10% neutral buffered formalin", None, None),
            (sample_key("activity_parameter", 2), sample_key("activity_record", 2), "fixation_temperature", None, 4.0, "degC"),
            (sample_key("activity_parameter", 3), sample_key("activity_record", 2), "fixation_duration", None, 48.0, "h"),
            (sample_key("activity_parameter", 4), sample_key("activity_record", 3), "fixative", "10% neutral buffered formalin", None, None),
            (sample_key("activity_parameter", 5), sample_key("activity_record", 3), "fixation_temperature", None, 4.0, "degC"),
            (sample_key("activity_parameter", 6), sample_key("activity_record", 3), "fixation_duration", None, 72.0, "h"),
            (sample_key("activity_parameter", 7), sample_key("activity_record", 5), "section_thickness", None, 20.0, "um"),
            (sample_key("activity_parameter", 8), sample_key("activity_record", 7), "stain", "Nissl", None, None),
            (sample_key("activity_parameter", 9), sample_key("activity_record", 8), "scan_resolution", None, 0.5, "um_per_pixel"),
            (sample_key("activity_parameter", 10), sample_key("activity_record", 9), "model_name", "Demo U-Net", None, None),
            (sample_key("activity_parameter", 11), sample_key("activity_record", 9), "model_version", "0.1", None, None),
        ]
        parameters_by_record = {}
        for identifier, record_id, definition_code, text, decimal, unit in rows:
            parameters_by_record.setdefault(
                normalize_key(record_id), {}
            )[definitions[definition_code]] = (
                text if text is not None else decimal
            )

        for record_id, parameters in parameters_by_record.items():
            record = records[record_id]
            log_activity_parameters(
                record.activity,
                parameters,
                record=record,
                replace=True,
            )

    def load_external_references(self, entities, activities):
        put(ExternalReference, sample_key("external_reference", 1), subject_type="entity", entity=entities[sample_key("entity", 1)], namespace="external_pathology", external_id="EXT-BRAIN-7842", source_system="External Pathology LIMS", source_organization="External Neuropathology Centre", description="External specimen identifier retained at accession")
        put(ExternalReference, sample_key("external_reference", 2), subject_type="activity", activity=activities[sample_key("activity", 1)], namespace="external_transfer", external_id="MTA-DEMO-2026-17", source_system="Transfer Register", source_organization="External Neuropathology Centre", description="External transfer reference associated with accession")

    def load_provenance(self, entities, activities):
        entity = entities[sample_key("entity", 1)]
        EntityProvenance.objects.update_or_create(
            pk=entity.pk,
            defaults={
                "entity": entity,
                "provenance_status": "external",
                "provenance_boundary_activity": activities[sample_key("activity", 1)],
                "source_description": "Specimen provenance prior to SGBC accession is external to this database",
                "notes": "No artificial donor/source entity has been created.",
            },
        )

    def load_entity_relations(self, entities, activities):
        types = {}
        for identifier, code, name, description in [
            (sample_key("relation_type", 1), "part_of", "Part Of", "Source entity is physically part of target entity"),
            (sample_key("relation_type", 2), "derived_from", "Derived From", "Source entity is derived from target entity"),
            (sample_key("relation_type", 3), "same_physical_entity_as", "Same Physical Entity As", "Two entity states refer to the same persistent physical object"),
        ]:
            types[code] = put(EntityRelationType, identifier, code=code, name=name, description=description)
        rows = [
            (sample_key("entity_relation", 1), sample_key("entity", 2), sample_key("entity", 1), "same_physical_entity_as", sample_key("activity", 2)),
            (sample_key("entity_relation", 2), sample_key("entity", 11), sample_key("entity", 2), "part_of", sample_key("activity", 3)),
            (sample_key("entity_relation", 3), sample_key("entity", 12), sample_key("entity", 2), "part_of", sample_key("activity", 3)),
            (sample_key("entity_relation", 4), sample_key("entity", 13), sample_key("entity", 2), "part_of", sample_key("activity", 3)),
            (sample_key("entity_relation", 5), sample_key("entity", 22), sample_key("entity", 12), "derived_from", sample_key("activity", 4)),
            (sample_key("entity_relation", 6), sample_key("entity", 41), sample_key("entity", 31), "derived_from", sample_key("activity", 7)),
            (sample_key("entity_relation", 7), sample_key("entity", 51), sample_key("entity", 41), "derived_from", sample_key("activity", 8)),
        ]
        for identifier, source_id, target_id, type_code, activity_id in rows:
            put(EntityRelation, identifier, source_entity=entities[source_id], target_entity=entities[target_id], entity_relation_type=types[type_code], activity=activities[activity_id], created_at=NOW)
