# This is an auto-generated Django model module.
# You'll have to do the following manually to clean this up:
#   * Rearrange models' order
#   * Make sure each model has one field with primary_key=True
#   * Make sure each ForeignKey and OneToOneField has `on_delete` set to the desired behavior
#   * Remove `managed = False` lines if you wish to allow Django to create, modify, and delete the table
# Feel free to rename the models, but don't rename db_table values or field names.
from django.db import models


class EntityType(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    code = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    ontology_id = models.CharField(max_length=255, blank=True, null=True)
    ontology_uri = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'entity_type'
        db_table_comment = 'Hierarchical vocabulary describing entity classes.\n\nExample hierarchy:\n\nbiological_source\n  donor\n\nmaterial_entity\n  biospecimen\n    whole_brain\n    hemisphere\n    slab\n    tissue_block\n  biosample\n    tissue_section\n    tissue_curl\n    aliquot\n\nphysical_artifact\n  slide\n  container\n\ndigital_entity\n  image\n  volume\n  segmentation\n  feature_set\n  annotation\n'


class ActivityType(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    code = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    parent = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    ontology_id = models.CharField(max_length=255, blank=True, null=True)
    ontology_uri = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'activity_type'
        db_table_comment = 'Hierarchical vocabulary of activities.\n\nExample hierarchy:\n\nacquisition\n  accession\n  extraction\n\npreservation\n  perfusion\n  fixation\n  cryoprotection\n  freezing\n  storage\n\nprocessing\n  dissection\n  slabbing\n  sectioning\n  mounting\n  staining\n\nimaging\n  slide_scanning\n  MRI\n  microscopy\n\ncomputational_processing\n  registration\n  normalization\n  segmentation\n  feature_extraction\n'


class Entity(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    entity_type = models.ForeignKey(EntityType, models.DO_NOTHING)
    identifier = models.CharField(unique=True, max_length=255)
    physical_identity = models.ForeignKey('PhysicalIdentity', models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'entity'
        db_table_comment = 'Immutable provenance node representing a biological,\nphysical, or digital entity.\n\nMutable properties such as names, classifications,\nlocations, condition, status, etc. belong in\nentity_information_record.\n\nphysical_identity_id can associate multiple provenance\nstates with the same physical object.\n\nExample:\n\nfresh brain  -> P001\nfixed brain  -> P001\nfrozen brain -> P001\n\nAfter physical subdivision:\n\nleft hemisphere  -> P002\nright hemisphere -> P003\n'


class PhysicalIdentity(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    identifier = models.CharField(unique=True, max_length=255)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'physical_identity'
        db_table_comment = 'Represents persistent physical identity independently\nof processing state.\n'


class Activity(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    activity_type = models.ForeignKey(ActivityType, models.DO_NOTHING)
    identifier = models.CharField(unique=True, max_length=255)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'activity'
        db_table_comment = 'Immutable provenance event.\n\nActivity execution details are stored in\nactivity_information_record.\n\nActivities may have zero inputs or zero outputs.\n\nExample:\n  accession: 0 -> N\n  fixation:   N -> N\n  disposal:   N -> 0\n'


class ActivityEntity(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    activity = models.ForeignKey(Activity, models.DO_NOTHING)
    entity = models.ForeignKey(Entity, models.DO_NOTHING)
    direction = models.CharField(max_length=6)
    role = models.CharField(max_length=255, blank=True, null=True)
    sequence_no = models.IntegerField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'activity_entity'
        unique_together = (('activity', 'entity', 'direction', 'role'),)
        db_table_comment = 'Junction table implementing the provenance graph:\n\n     Entity -> Activity -> Entity\n\nNo database constraint requires an activity to have an\ninput. This intentionally supports accession activities.\n'


class EntityInformationRecord(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    entity = models.ForeignKey(Entity, models.DO_NOTHING)
    information_record_type = models.ForeignKey('InformationRecordType', models.DO_NOTHING, blank=True, null=True)
    version = models.IntegerField()
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    recorded_at = models.DateTimeField()
    recorded_by_agent = models.ForeignKey('Agent', models.DO_NOTHING, blank=True, null=True)
    supersedes_record = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    status = models.CharField(max_length=255, blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'entity_information_record'
        unique_together = (('entity', 'version'),)
        db_table_comment = 'Versioned sidecar record describing an Entity.\n\nChanges in knowledge create a new InformationRecord\nrather than modifying the Entity.\n\nExamples:\n  anatomical designation\n  specimen condition\n  storage location\n  QC state\n  custodian\n  availability\n  descriptive annotation\n'


class InformationRecordType(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    code = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'information_record_type'
        db_table_comment = 'Allows independent information sidecars.\n\nExamples:\n\n  general\n  anatomical\n  storage\n  quality_control\n  custody\n  clinical_annotation\n  imaging\n'


class ActivityInformationRecord(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    activity = models.ForeignKey(Activity, models.DO_NOTHING)
    version = models.IntegerField()
    valid_from = models.DateTimeField(blank=True, null=True)
    valid_until = models.DateTimeField(blank=True, null=True)
    recorded_at = models.DateTimeField()
    recorded_by_agent = models.ForeignKey('Agent', models.DO_NOTHING, blank=True, null=True)
    supersedes_record = models.ForeignKey('self', models.DO_NOTHING, blank=True, null=True)
    status = models.CharField(max_length=11, blank=True, null=True)
    started_at = models.DateTimeField(blank=True, null=True)
    ended_at = models.DateTimeField(blank=True, null=True)
    protocol = models.ForeignKey('Protocol', models.DO_NOTHING, blank=True, null=True)
    operator_agent = models.ForeignKey('Agent', models.DO_NOTHING, related_name='activityinformationrecord_operator_agent_set', blank=True, null=True)
    instrument = models.ForeignKey('Instrument', models.DO_NOTHING, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'activity_information_record'
        unique_together = (('activity', 'version'),)
        db_table_comment = 'Versioned sidecar describing Activity execution.\n\nThe Activity establishes that an event exists.\nThis record captures what is currently known\nabout that event.\n\nIncludes execution details such as:\n  timing\n  operator\n  instrument\n  protocol\n  status\n  notes\n\nProcess parameters are stored separately in\nactivity_parameter.\n'


class ParameterDefinition(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    code = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)
    datatype = models.CharField(max_length=11)
    canonical_unit = models.CharField(max_length=255, blank=True, null=True)
    ontology_id = models.CharField(max_length=255, blank=True, null=True)
    ontology_uri = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'parameter_definition'
        db_table_comment = 'Controlled definition of reusable process parameters.\n\nExamples:\n\n  fixation_temperature\n  fixation_duration\n  fixative_concentration\n  section_thickness\n  scanner_resolution\n  laser_power\n'


class ActivityParameter(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    activity_information_record = models.ForeignKey(ActivityInformationRecord, models.DO_NOTHING)
    parameter_definition = models.ForeignKey(ParameterDefinition, models.DO_NOTHING, blank=True, null=True)
    parameter_name = models.CharField(max_length=255, blank=True, null=True)
    value_text = models.TextField(blank=True, null=True)
    value_integer = models.BigIntegerField(blank=True, null=True)
    value_decimal = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    value_boolean = models.IntegerField(blank=True, null=True)
    value_datetime = models.DateTimeField(blank=True, null=True)
    value_json = models.JSONField(blank=True, null=True)
    unit = models.CharField(max_length=255, blank=True, null=True)
    sequence_no = models.IntegerField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'activity_parameter'
        db_table_comment = 'Captures actual execution parameters for an activity.\n\nExample:\n\n  fixation_temperature = 4.3 C\n  fixation_duration = 76.2 h\n  formalin_concentration = 10 %\n\nParameter_definition_id is preferred for controlled\nparameters.\n\nparameter_name permits ad-hoc parameters during\nexploratory workflows.\n'


class Protocol(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    identifier = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    version = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    uri = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()

    class Meta:
        db_table = 'protocol'
        db_table_comment = 'Protocol defines intended procedure:\n\n      what SHOULD happen.\n\nactivity_parameter captures execution:\n\n      what DID happen.\n'


class ProtocolParameter(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    protocol = models.ForeignKey(Protocol, models.DO_NOTHING)
    parameter_definition = models.ForeignKey(ParameterDefinition, models.DO_NOTHING)
    required = models.IntegerField(blank=True, null=True)
    default_value_text = models.TextField(blank=True, null=True)
    default_value_decimal = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    minimum_value = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    maximum_value = models.DecimalField(max_digits=10, decimal_places=0, blank=True, null=True)
    unit = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'protocol_parameter'
        unique_together = (('protocol', 'parameter_definition'),)


class Agent(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    identifier = models.CharField(unique=True, max_length=255)
    agent_type = models.CharField(max_length=12)
    name = models.CharField(max_length=255)
    affiliation = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'agent'
        db_table_comment = 'An Agent may be:\n\n  person\n  organization\n  software\n  service\n\nThis permits both wet-lab and computational provenance.\n'


class Instrument(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    identifier = models.CharField(unique=True, max_length=255)
    instrument_type = models.CharField(max_length=255, blank=True, null=True)
    manufacturer = models.CharField(max_length=255, blank=True, null=True)
    model = models.CharField(max_length=255, blank=True, null=True)
    serial_number = models.CharField(max_length=255, blank=True, null=True)
    software_version = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField()
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'instrument'


class AccessionInformation(models.Model):
    activity_information_record = models.OneToOneField(ActivityInformationRecord, models.DO_NOTHING, primary_key=True)
    accession_number = models.CharField(unique=True, max_length=255)
    accessioned_at = models.DateTimeField(blank=True, null=True)
    source_organization_agent = models.ForeignKey(Agent, models.DO_NOTHING, blank=True, null=True)
    received_by_agent = models.ForeignKey(Agent, models.DO_NOTHING, related_name='accessioninformation_received_by_agent_set', blank=True, null=True)
    external_specimen_identifier = models.CharField(max_length=255, blank=True, null=True)
    shipment_reference = models.CharField(max_length=255, blank=True, null=True)
    transfer_reference = models.CharField(max_length=255, blank=True, null=True)
    provenance_status = models.CharField(max_length=11)
    source_description = models.TextField(blank=True, null=True)
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'accession_information'
        db_table_comment = 'Activity-specific extension for accession.\n\nAn accession Activity does not require a locally\nrepresented input Entity.\n\nExample:\n\n   unknown external provenance\n             |\n         accession\n             |\n        whole brain\n\nExternal identifiers can still be retained without\ncreating artificial upstream entities.\n'


class ExternalReference(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    subject_type = models.CharField(max_length=8)
    entity = models.ForeignKey(Entity, models.DO_NOTHING, blank=True, null=True)
    activity = models.ForeignKey(Activity, models.DO_NOTHING, blank=True, null=True)
    namespace = models.CharField(max_length=255, blank=True, null=True)
    external_id = models.CharField(max_length=255)
    source_system = models.CharField(max_length=255, blank=True, null=True)
    source_organization = models.CharField(max_length=255, blank=True, null=True)
    uri = models.CharField(max_length=255, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    created_at = models.DateTimeField()
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'external_reference'
        db_table_comment = 'Provides traceability to external systems without\nimporting their complete provenance graph.\n\nExamples:\n\n  hospital pathology accession\n  LIMS identifier\n  collaborator specimen code\n  external imaging study ID\n'


class EntityProvenance(models.Model):
    entity = models.OneToOneField(Entity, models.DO_NOTHING, primary_key=True)
    provenance_status = models.CharField(max_length=11)
    provenance_boundary_activity = models.ForeignKey(Activity, models.DO_NOTHING, blank=True, null=True)
    source_description = models.TextField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'entity_provenance'
        db_table_comment = 'Describes completeness of provenance prior to the\nentity entering the locally managed provenance graph.\n\nEspecially useful for accessioned material.\n'


class EntityRelationType(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    code = models.CharField(unique=True, max_length=255)
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True, null=True)

    class Meta:
        db_table = 'entity_relation_type'
        db_table_comment = 'Useful relation examples:\n\n  part_of\n  same_physical_entity_as\n  derived_from\n  aliquot_of\n  version_of\n\nThese relationships provide convenient traversal,\nbut Activity remains the authoritative process\nprovenance mechanism.\n'


class EntityRelation(models.Model):
    id = models.CharField(primary_key=True, max_length=36)
    source_entity = models.ForeignKey(Entity, models.DO_NOTHING)
    target_entity = models.ForeignKey(Entity, models.DO_NOTHING, related_name='entityrelation_target_entity_set')
    entity_relation_type = models.ForeignKey(EntityRelationType, models.DO_NOTHING)
    activity = models.ForeignKey(Activity, models.DO_NOTHING, blank=True, null=True)
    created_at = models.DateTimeField()
    metadata = models.JSONField(blank=True, null=True)

    class Meta:
        db_table = 'entity_relation'
        unique_together = (('source_entity', 'target_entity', 'entity_relation_type'),)
