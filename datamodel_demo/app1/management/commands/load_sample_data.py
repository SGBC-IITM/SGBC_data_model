from datetime import datetime
from uuid import NAMESPACE_URL, uuid5

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


NOW = make_aware(datetime(2026, 9, 5, 12, 0))
SAMPLE_NAMESPACE = uuid5(NAMESPACE_URL, "https://sgbc-iitm.org/sgbc-data-model/sample-data")


def dt(value):
    return make_aware(datetime.fromisoformat(value)) if value else None


def sample_uuid(key):
    return uuid5(SAMPLE_NAMESPACE, str(key))


def normalize_key(key):
    parts = str(key).split("-")
    if len(parts) == 4:
        return "-".join((*parts[:-1], "0000", parts[-1]))
    return str(key)


def put(model, key, **values):
    obj, _ = model.objects.update_or_create(pk=sample_uuid(key), defaults=values)
    return obj


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
            ("10000000-0000-0000-0000-000000000001", "biological_source", "Biological Source", "Source biological subject", None),
            ("10000000-0000-0000-0000-000000000002", "donor", "Donor", "Human donor", "10000000-0000-0000-0000-000000000001"),
            ("10000000-0000-0000-0000-000000000010", "material_entity", "Material Entity", "Physical biological material", None),
            ("10000000-0000-0000-0000-000000000011", "biospecimen", "Biospecimen", "Primary biological specimen", "10000000-0000-0000-0000-000000000010"),
            ("10000000-0000-0000-0000-000000000012", "whole_brain", "Whole Brain", "Whole human brain specimen", "10000000-0000-0000-0000-000000000011"),
            ("10000000-0000-0000-0000-000000000013", "slab", "Brain Slab", "Macroscopic brain slab", "10000000-0000-0000-0000-000000000011"),
            ("10000000-0000-0000-0000-000000000014", "biosample", "Biosample", "Sample derived from a biospecimen", "10000000-0000-0000-0000-000000000010"),
            ("10000000-0000-0000-0000-000000000015", "tissue_section", "Tissue Section", "Histological tissue section", "10000000-0000-0000-0000-000000000014"),
            ("10000000-0000-0000-0000-000000000020", "physical_artifact", "Physical Artifact", "Physical artifact used or produced by processing", None),
            ("10000000-0000-0000-0000-000000000021", "slide", "Glass Slide", "Mounted histology slide", "10000000-0000-0000-0000-000000000020"),
            ("10000000-0000-0000-0000-000000000030", "digital_entity", "Digital Entity", "Digital data artifact", None),
            ("10000000-0000-0000-0000-000000000031", "image", "Image", "Digital image", "10000000-0000-0000-0000-000000000030"),
            ("10000000-0000-0000-0000-000000000032", "segmentation", "Segmentation", "Derived segmentation mask", "10000000-0000-0000-0000-000000000030"),
        ])
        activity_types = self.load_types(ActivityType, [
            ("20000000-0000-0000-0000-000000000001", "acquisition", "Acquisition", "Entry or acquisition of material", None),
            ("20000000-0000-0000-0000-000000000002", "accession", "Accession", "Material enters local custody without requiring a modeled upstream entity", "20000000-0000-0000-0000-000000000001"),
            ("20000000-0000-0000-0000-000000000010", "preservation", "Preservation", "Preservation activities", None),
            ("20000000-0000-0000-0000-000000000011", "fixation", "Fixation", "Tissue fixation", "20000000-0000-0000-0000-000000000010"),
            ("20000000-0000-0000-0000-000000000020", "processing", "Processing", "Physical tissue processing", None),
            ("20000000-0000-0000-0000-000000000021", "slabbing", "Slabbing", "Subdivision of whole brain into slabs", "20000000-0000-0000-0000-000000000020"),
            ("20000000-0000-0000-0000-000000000022", "sectioning", "Sectioning", "Microtome/cryostat sectioning", "20000000-0000-0000-0000-000000000020"),
            ("20000000-0000-0000-0000-000000000023", "mounting", "Mounting", "Mount tissue section on glass slide", "20000000-0000-0000-0000-000000000020"),
            ("20000000-0000-0000-0000-000000000024", "staining", "Staining", "Histological staining", "20000000-0000-0000-0000-000000000020"),
            ("20000000-0000-0000-0000-000000000030", "imaging", "Imaging", "Image acquisition", None),
            ("20000000-0000-0000-0000-000000000031", "slide_scanning", "Slide Scanning", "Whole-slide image acquisition", "20000000-0000-0000-0000-000000000030"),
            ("20000000-0000-0000-0000-000000000040", "computational_processing", "Computational Processing", "Computational derivation", None),
            ("20000000-0000-0000-0000-000000000041", "segmentation", "Segmentation", "Computational image segmentation", "20000000-0000-0000-0000-000000000040"),
        ])
        record_types = self.load_simple(InformationRecordType, [
            ("30000000-0000-0000-0000-000000000001", "general", "General", "General descriptive information"),
            ("30000000-0000-0000-0000-000000000002", "anatomical", "Anatomical", "Anatomical description and interpretation"),
            ("30000000-0000-0000-0000-000000000003", "storage", "Storage", "Storage location and condition"),
            ("30000000-0000-0000-0000-000000000004", "quality_control", "Quality Control", "QC observations and status"),
            ("30000000-0000-0000-0000-000000000005", "imaging", "Imaging", "Image-specific descriptive information"),
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
            EntityRelationType, EntityType, ActivityType,
        ):
            model.objects.all().delete()

    def load_types(self, model, rows):
        objects = {}
        for identifier, code, name, description, parent_id in rows:
            objects[code] = put(model, identifier, code=code, name=name, description=description)
        for identifier, code, name, description, parent_id in rows:
            if parent_id:
                objects[code].parent = model.objects.get(pk=sample_uuid(parent_id))
                objects[code].save(update_fields=["parent"])
        return objects

    def load_simple(self, model, rows):
        return {code: put(model, identifier, code=code, name=name, description=description) for identifier, code, name, description in rows}

    def load_agents(self):
        rows = [
            ("40000000-0000-0000-0000-000000000001", "ORG-SGBC", "organization", "SGBC Histology Facility", "SGBC", None),
            ("40000000-0000-0000-0000-000000000002", "ORG-EXT-001", "organization", "External Neuropathology Centre", "External Institution", None),
            ("40000000-0000-0000-0000-000000000003", "USR-TECH-001", "person", "Histology Technician 01", "SGBC", None),
            ("40000000-0000-0000-0000-000000000004", "USR-SCI-001", "person", "Researcher 01", "SGBC", None),
            ("40000000-0000-0000-0000-000000000005", "SW-SEG-001", "software", "Neurohistology Segmentation Pipeline", "SGBC", {"version": "0.1-demo"}),
        ]
        return {identifier: put(Agent, identifier, identifier=identifier, agent_type=agent_type, name=name, affiliation=affiliation, metadata=metadata) for _, identifier, agent_type, name, affiliation, metadata in rows}

    def load_parameter_definitions(self):
        rows = [
            ("60000000-0000-0000-0000-000000000001", "fixative", "Fixative", "Fixative formulation", "text", None),
            ("60000000-0000-0000-0000-000000000002", "fixation_temperature", "Fixation Temperature", "Temperature during fixation", "decimal", "degC"),
            ("60000000-0000-0000-0000-000000000003", "fixation_duration", "Fixation Duration", "Duration of fixation", "decimal", "h"),
            ("60000000-0000-0000-0000-000000000004", "section_thickness", "Section Thickness", "Nominal section thickness", "decimal", "um"),
            ("60000000-0000-0000-0000-000000000005", "stain", "Stain", "Histological stain", "categorical", None),
            ("60000000-0000-0000-0000-000000000006", "scan_resolution", "Scan Resolution", "Pixel size at acquisition", "decimal", "um_per_pixel"),
            ("60000000-0000-0000-0000-000000000007", "model_name", "Model Name", "Computational model used", "text", None),
            ("60000000-0000-0000-0000-000000000008", "model_version", "Model Version", "Computational model version", "text", None),
        ]
        return {code: put(ParameterDefinition, identifier, code=code, name=name, description=description, datatype=datatype, canonical_unit=unit) for identifier, code, name, description, datatype, unit in rows}

    def load_protocols(self, definitions):
        protocols = {}
        rows = [
            ("70000000-0000-0000-0000-000000000001", "PROT-FIX-001", "Whole Brain Fixation", "1.0", "Demo whole-brain immersion fixation protocol"),
            ("70000000-0000-0000-0000-000000000002", "PROT-SEC-001", "Cryostat Sectioning", "1.0", "Demo serial sectioning protocol"),
            ("70000000-0000-0000-0000-000000000003", "PROT-NISSL-001", "Nissl Staining", "1.0", "Demo Nissl staining protocol"),
            ("70000000-0000-0000-0000-000000000004", "PROT-SCAN-001", "Whole Slide Scanning", "1.0", "Demo WSI acquisition protocol"),
        ]
        for identifier, code, name, version, description in rows:
            protocols[code] = put(Protocol, identifier, identifier=code, name=name, version=version, description=description)
        values = [
            ("71000000-0000-0000-0000-000000000001", "PROT-FIX-001", "fixative", 1, "10% neutral buffered formalin", None, None, "Expected fixative"),
            ("71000000-0000-0000-0000-000000000002", "PROT-FIX-001", "fixation_temperature", 1, None, 4.0, "degC", "Target temperature"),
            ("71000000-0000-0000-0000-000000000003", "PROT-FIX-001", "fixation_duration", 1, None, 72.0, "h", "Target duration"),
            ("71000000-0000-0000-0000-000000000004", "PROT-SEC-001", "section_thickness", 1, None, 20.0, "um", "Nominal section thickness"),
            ("71000000-0000-0000-0000-000000000005", "PROT-NISSL-001", "stain", 1, "Nissl", None, None, "Required stain"),
            ("71000000-0000-0000-0000-000000000006", "PROT-SCAN-001", "scan_resolution", 1, None, 0.5, "um_per_pixel", "Target scan resolution"),
        ]
        for identifier, protocol_code, definition_code, required, text, decimal, unit, description in values:
            put(ProtocolParameter, identifier, protocol=protocols[protocol_code], parameter_definition=definitions[definition_code], required=required, default_value_text=text, default_value_decimal=decimal, unit=unit, description=description)
        return protocols

    def load_entities(self, types):
        rows = [
            ("90000000-0000-0000-0000-000000000001", "whole_brain", "BRN-2026-001", "PHY-BRAIN-001"),
            ("90000000-0000-0000-0000-000000000002", "whole_brain", "BRN-2026-001-FIXED", "PHY-BRAIN-001"),
            ("90000000-0000-0000-0000-000000000011", "slab", "BRN-2026-001-SLAB-01", "PHY-SLAB-001"),
            ("90000000-0000-0000-0000-000000000012", "slab", "BRN-2026-001-SLAB-02", "PHY-SLAB-002"),
            ("90000000-0000-0000-0000-000000000013", "slab", "BRN-2026-001-SLAB-03", "PHY-SLAB-003"),
            ("90000000-0000-0000-0000-000000000021", "tissue_section", "BRN-2026-001-S02-SEC-001", "PHY-SEC-001"),
            ("90000000-0000-0000-0000-000000000022", "tissue_section", "BRN-2026-001-S02-SEC-002", "PHY-SEC-002"),
            ("90000000-0000-0000-0000-000000000023", "tissue_section", "BRN-2026-001-S02-SEC-003", "PHY-SEC-003"),
            ("90000000-0000-0000-0000-000000000031", "slide", "BRN-2026-001-S02-SLIDE-001", "PHY-SLIDE-001"),
            ("90000000-0000-0000-0000-000000000041", "image", "IMG-2026-001-S02-NISSL-001", None),
            ("90000000-0000-0000-0000-000000000051", "segmentation", "SEG-2026-001-S02-001", None),
        ]
        return {identifier: put(Entity, identifier, entity_type=types[type_code], identifier=entity_identifier, physical_identity=physical_identity) for identifier, type_code, entity_identifier, physical_identity in rows}

    def load_activities(self, types):
        rows = [
            ("a0000000-0000-0000-0000-000000000001", "accession", "ACC-2026-001"),
            ("a0000000-0000-0000-0000-000000000002", "fixation", "FIX-2026-001"),
            ("a0000000-0000-0000-0000-000000000003", "slabbing", "SLAB-2026-001"),
            ("a0000000-0000-0000-0000-000000000004", "sectioning", "SEC-2026-001"),
            ("a0000000-0000-0000-0000-000000000005", "mounting", "MOUNT-2026-001"),
            ("a0000000-0000-0000-0000-000000000006", "staining", "STAIN-2026-001"),
            ("a0000000-0000-0000-0000-000000000007", "slide_scanning", "SCAN-2026-001"),
            ("a0000000-0000-0000-0000-000000000008", "segmentation", "SEG-2026-001"),
        ]
        activities = {}
        for identifier, type_code, activity_identifier in rows:
            activity = put(Activity, identifier, activity_type=types[type_code], identifier=activity_identifier)
            activities[identifier] = activity
            activities[normalize_key(identifier)] = activity
        return activities

    def load_activity_entities(self, activities, entities):
        rows = [
            ("b0000000-0000-0000-0000-000000000001", "a0000000-0000-0000-0000-000000000001", "90000000-0000-0000-0000-000000000001", "output", "accessioned_specimen", 1),
            ("b0000000-0000-0000-0000-000000000002", "a0000000-0000-0000-0000-000000000002", "90000000-0000-0000-0000-000000000001", "input", "unfixed_brain", 1),
            ("b0000000-0000-0000-0000-000000000003", "a0000000-0000-0000-0000-000000000002", "90000000-0000-0000-0000-000000000002", "output", "fixed_brain", 1),
            ("b0000000-0000-0000-0000-000000000004", "a0000000-0000-0000-0000-000000000003", "90000000-0000-0000-0000-000000000002", "input", "whole_brain", 1),
            ("b0000000-0000-0000-0000-000000000005", "a0000000-0000-0000-0000-000000000003", "90000000-0000-0000-0000-000000000011", "output", "slab", 1),
            ("b0000000-0000-0000-0000-000000000006", "a0000000-0000-0000-0000-000000000003", "90000000-0000-0000-0000-000000000012", "output", "slab", 2),
            ("b0000000-0000-0000-0000-000000000007", "a0000000-0000-0000-0000-000000000003", "90000000-0000-0000-0000-000000000013", "output", "slab", 3),
            ("b0000000-0000-0000-0000-000000000008", "a0000000-0000-0000-0000-000000000004", "90000000-0000-0000-0000-000000000012", "input", "source_slab", 1),
            ("b0000000-0000-0000-0000-000000000009", "a0000000-0000-0000-0000-000000000004", "90000000-0000-0000-0000-000000000021", "output", "serial_section", 1),
            ("b0000000-0000-0000-0000-000000000010", "a0000000-0000-0000-0000-000000000004", "90000000-0000-0000-0000-000000000022", "output", "serial_section", 2),
            ("b0000000-0000-0000-0000-000000000011", "a0000000-0000-0000-0000-000000000004", "90000000-0000-0000-0000-000000000023", "output", "serial_section", 3),
            ("b0000000-0000-0000-0000-000000000012", "a0000000-0000-0000-0000-000000000005", "90000000-0000-0000-0000-000000000022", "input", "tissue_section", 1),
            ("b0000000-0000-0000-0000-000000000013", "a0000000-0000-0000-0000-000000000005", "90000000-0000-0000-0000-000000000031", "output", "mounted_slide", 1),
            ("b0000000-0000-0000-0000-000000000014", "a0000000-0000-0000-0000-000000000006", "90000000-0000-0000-0000-000000000031", "input", "unstained_slide", 1),
            ("b0000000-0000-0000-0000-000000000015", "a0000000-0000-0000-0000-000000000006", "90000000-0000-0000-0000-000000000031", "output", "nissl_stained_slide", 1),
            ("b0000000-0000-0000-0000-000000000016", "a0000000-0000-0000-0000-000000000007", "90000000-0000-0000-0000-000000000031", "input", "source_slide", 1),
            ("b0000000-0000-0000-0000-000000000017", "a0000000-0000-0000-0000-000000000007", "90000000-0000-0000-0000-000000000041", "output", "whole_slide_image", 1),
            ("b0000000-0000-0000-0000-000000000018", "a0000000-0000-0000-0000-000000000008", "90000000-0000-0000-0000-000000000041", "input", "source_image", 1),
            ("b0000000-0000-0000-0000-000000000019", "a0000000-0000-0000-0000-000000000008", "90000000-0000-0000-0000-000000000051", "output", "segmentation_mask", 1),
        ]
        for identifier, activity_id, entity_id, direction, role, sequence_no in rows:
            put(ActivityEntity, identifier, activity=activities[activity_id], entity=entities[entity_id], direction=direction, role=role, sequence_no=sequence_no)

    def load_entity_records(self, entities, record_types, agents):
        rows = [
            ("c0000000-0000-0000-0000-000000000001", "90000000-0000-0000-0000-000000000001", "general", 1, "Accessioned whole brain", "Whole brain received from external neuropathology centre", "received", {"condition": "received chilled", "container": "sealed specimen container"}, None),
            ("c0000000-0000-0000-0000-000000000002", "90000000-0000-0000-0000-000000000002", "general", 1, "Fixed whole brain", "Whole brain after fixation", "available", {"fixation_state": "fixed"}, None),
            ("c0000000-0000-0000-0000-000000000011", "90000000-0000-0000-0000-000000000011", "anatomical", 1, "Slab 01", "Anterior brain slab", "available", {"slab_index": 1, "orientation": "coronal"}, None),
            ("c0000000-0000-0000-0000-000000000012", "90000000-0000-0000-0000-000000000012", "anatomical", 1, "Slab 02", "Anatomical assignment pending", "provisional", {"slab_index": 2, "anatomical_region": "unknown"}, None),
            ("c0000000-0000-0000-0000-000000000013", "90000000-0000-0000-0000-000000000012", "anatomical", 2, "Slab 02", "Anatomical assignment reviewed", "confirmed", {"slab_index": 2, "anatomical_region": "left frontal region"}, "c0000000-0000-0000-0000-000000000012"),
            ("c0000000-0000-0000-0000-000000000014", "90000000-0000-0000-0000-000000000013", "anatomical", 1, "Slab 03", "Posterior brain slab", "available", {"slab_index": 3, "orientation": "coronal"}, None),
        ]
        records = {}
        for identifier, entity_id, type_code, version, name, description, status, metadata, supersedes in rows:
            records[identifier] = put(EntityInformationRecord, identifier, entity=entities[entity_id], information_record_type=record_types[type_code], version=version, recorded_at=NOW, recorded_by_agent=agents["USR-SCI-001"], supersedes_record=EntityInformationRecord.objects.filter(pk=sample_uuid(supersedes)).first() if supersedes else None, name=name, description=description, status=status, metadata=metadata)
        return records

    def load_activity_records(self, activities, agents, protocols):
        rows = [
            ("d0000000-0000-0000-0000-000000000001", "a0000000-0000-0000-0000-000000000001", "completed", None, "Accession of externally supplied whole brain", "No upstream local entity created; external provenance retained as accession metadata"),
            ("d0000000-0000-0000-0000-000000000002", "a0000000-0000-0000-0000-000000000002", "completed", "PROT-FIX-001", "Whole brain fixation", "Initial record entered with duration transcribed as 48 h"),
            ("d0000000-0000-0000-0000-000000000003", "a0000000-0000-0000-0000-000000000002", "completed", "PROT-FIX-001", "Whole brain fixation", "Corrected from source worksheet: fixation duration was 72 h"),
            ("d0000000-0000-0000-0000-000000000004", "a0000000-0000-0000-0000-000000000003", "completed", None, "Whole brain slabbing", "Demo subdivision into three slabs"),
            ("d0000000-0000-0000-0000-000000000005", "a0000000-0000-0000-0000-000000000004", "completed", "PROT-SEC-001", "Serial sectioning of slab 02", "Three representative sections inserted for demo"),
            ("d0000000-0000-0000-0000-000000000006", "a0000000-0000-0000-000000000005", "completed", None, "Mount section 002", "Section mounted on glass slide"),
            ("d0000000-0000-0000-0000-000000000007", "a0000000-0000-0000-000000000006", "completed", "PROT-NISSL-001", "Nissl staining", "Routine Nissl stain"),
            ("d0000000-0000-0000-000000000008", "a0000000-0000-0000-000000000007", "completed", "PROT-SCAN-001", "Whole-slide scanning", "Digitization of Nissl slide"),
            ("d0000000-0000-0000-0000-000000000009", "a0000000-0000-0000-0000-000000000008", "completed", None, "Gross anatomy segmentation", "Demo computational derivative"),
        ]
        records = {}
        for identifier, activity_id, status, protocol_code, description, notes in rows:
            supersedes = "d0000000-0000-0000-0000-000000000002" if identifier.endswith("003") else None
            record = put(ActivityInformationRecord, identifier, activity=activities[normalize_key(activity_id)], version=2 if supersedes else 1, recorded_at=NOW, recorded_by_agent=agents["USR-SCI-001"], supersedes_record=ActivityInformationRecord.objects.filter(pk=sample_uuid(supersedes)).first() if supersedes else None, status=status, protocol=protocols.get(protocol_code), description=description, notes=notes)
            records[identifier] = record
            records[normalize_key(identifier)] = record
        return records

    def load_accession_information(self, records, agents):
        put(AccessionInformation, "d0000000-0000-0000-0000-000000000001", activity_information_record=records["d0000000-0000-0000-0000-000000000001"], accession_number="SGBC-ACC-2026-001", accessioned_at=dt("2026-08-01 09:30:00"), source_organization_agent=agents["ORG-EXT-001"], received_by_agent=agents["USR-TECH-001"], external_specimen_identifier="EXT-BRAIN-7842", shipment_reference="SHIP-DEMO-8841", transfer_reference="MTA-DEMO-2026-17", provenance_status="external", source_description="Whole brain extracted and handled at external institution before transfer to SGBC", metadata={"received_condition": "chilled", "upstream_protocols_available": False})

    def load_activity_parameters(self, records, definitions):
        rows = [
            ("e0000000-0000-0000-0000-000000000001", "d0000000-0000-0000-0000-000000000002", "fixative", "10% neutral buffered formalin", None, None),
            ("e0000000-0000-0000-0000-000000000002", "d0000000-0000-0000-0000-000000000002", "fixation_temperature", None, 4.0, "degC"),
            ("e0000000-0000-0000-0000-000000000003", "d0000000-0000-0000-0000-000000000002", "fixation_duration", None, 48.0, "h"),
            ("e0000000-0000-0000-0000-000000000004", "d0000000-0000-0000-0000-000000000003", "fixative", "10% neutral buffered formalin", None, None),
            ("e0000000-0000-0000-0000-000000000005", "d0000000-0000-0000-0000-000000000003", "fixation_temperature", None, 4.0, "degC"),
            ("e0000000-0000-0000-0000-000000000006", "d0000000-0000-0000-0000-000000000003", "fixation_duration", None, 72.0, "h"),
            ("e0000000-0000-0000-0000-000000000007", "d0000000-0000-0000-0000-000000000005", "section_thickness", None, 20.0, "um"),
            ("e0000000-0000-0000-0000-000000000008", "d0000000-0000-0000-0000-000000000007", "stain", "Nissl", None, None),
            ("e0000000-0000-0000-0000-000000000009", "d0000000-0000-0000-0000-000000000008", "scan_resolution", None, 0.5, "um_per_pixel"),
            ("e0000000-0000-0000-0000-000000000010", "d0000000-0000-0000-0000-000000000009", "model_name", "Demo U-Net", None, None),
            ("e0000000-0000-0000-0000-000000000011", "d0000000-0000-0000-0000-000000000009", "model_version", "0.1", None, None),
        ]
        for identifier, record_id, definition_code, text, decimal, unit in rows:
            put(ActivityParameter, identifier, activity_information_record=records[normalize_key(record_id)], parameter_definition=definitions[definition_code], value_text=text, value_decimal=decimal, unit=unit)

    def load_external_references(self, entities, activities):
        put(ExternalReference, "f0000000-0000-0000-0000-000000000001", subject_type="entity", entity=entities["90000000-0000-0000-0000-000000000001"], namespace="external_pathology", external_id="EXT-BRAIN-7842", source_system="External Pathology LIMS", source_organization="External Neuropathology Centre", description="External specimen identifier retained at accession")
        put(ExternalReference, "f0000000-0000-0000-0000-000000000002", subject_type="activity", activity=activities["a0000000-0000-0000-0000-000000000001"], namespace="external_transfer", external_id="MTA-DEMO-2026-17", source_system="Transfer Register", source_organization="External Neuropathology Centre", description="External transfer reference associated with accession")

    def load_provenance(self, entities, activities):
        entity = entities["90000000-0000-0000-0000-000000000001"]
        EntityProvenance.objects.update_or_create(
            pk=entity.pk,
            defaults={
                "entity": entity,
                "provenance_status": "external",
                "provenance_boundary_activity": activities["a0000000-0000-0000-0000-000000000001"],
                "source_description": "Specimen provenance prior to SGBC accession is external to this database",
                "notes": "No artificial donor/source entity has been created.",
            },
        )

    def load_entity_relations(self, entities, activities):
        types = {}
        for identifier, code, name, description in [
            ("aa000000-0000-0000-0000-000000000001", "part_of", "Part Of", "Source entity is physically part of target entity"),
            ("aa000000-0000-0000-0000-000000000002", "derived_from", "Derived From", "Source entity is derived from target entity"),
            ("aa000000-0000-0000-0000-000000000003", "same_physical_entity_as", "Same Physical Entity As", "Two entity states refer to the same persistent physical object"),
        ]:
            types[code] = put(EntityRelationType, identifier, code=code, name=name, description=description)
        rows = [
            ("ab000000-0000-0000-0000-000000000001", "90000000-0000-0000-0000-000000000002", "90000000-0000-0000-0000-000000000001", "same_physical_entity_as", "a0000000-0000-0000-0000-000000000002"),
            ("ab000000-0000-0000-0000-000000000002", "90000000-0000-0000-0000-000000000011", "90000000-0000-0000-0000-000000000002", "part_of", "a0000000-0000-0000-0000-000000000003"),
            ("ab000000-0000-0000-0000-000000000003", "90000000-0000-0000-0000-000000000012", "90000000-0000-0000-0000-000000000002", "part_of", "a0000000-0000-0000-0000-000000000003"),
            ("ab000000-0000-0000-0000-000000000004", "90000000-0000-0000-0000-000000000013", "90000000-0000-0000-0000-000000000002", "part_of", "a0000000-0000-0000-0000-000000000003"),
            ("ab000000-0000-0000-0000-000000000005", "90000000-0000-0000-0000-000000000022", "90000000-0000-0000-0000-000000000012", "derived_from", "a0000000-0000-0000-0000-000000000004"),
            ("ab000000-0000-0000-0000-000000000006", "90000000-0000-0000-0000-000000000041", "90000000-0000-0000-0000-000000000031", "derived_from", "a0000000-0000-0000-0000-000000000007"),
            ("ab000000-0000-0000-0000-000000000007", "90000000-0000-0000-0000-000000000051", "90000000-0000-0000-0000-000000000041", "derived_from", "a0000000-0000-0000-0000-000000000008"),
        ]
        for identifier, source_id, target_id, type_code, activity_id in rows:
            put(EntityRelation, identifier, source_entity=entities[source_id], target_entity=entities[target_id], entity_relation_type=types[type_code], activity=activities[activity_id], created_at=NOW)
