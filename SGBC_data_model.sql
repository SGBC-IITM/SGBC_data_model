CREATE TABLE `entity_type` (
  `id` uuid PRIMARY KEY,
  `code` varchar(255) UNIQUE NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text,
  `parent_id` uuid,
  `ontology_id` varchar(255),
  `ontology_uri` varchar(255),
  `created_at` timestamp NOT NULL
);

CREATE TABLE `activity_type` (
  `id` uuid PRIMARY KEY,
  `code` varchar(255) UNIQUE NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text,
  `parent_id` uuid,
  `ontology_id` varchar(255),
  `ontology_uri` varchar(255),
  `created_at` timestamp NOT NULL
);

CREATE TABLE `entity` (
  `id` uuid PRIMARY KEY,
  `entity_type_id` uuid NOT NULL,
  `identifier` varchar(255) UNIQUE NOT NULL,
  `physical_identity_id` uuid,
  `created_at` timestamp NOT NULL
);

CREATE TABLE `physical_identity` (
  `id` uuid PRIMARY KEY,
  `identifier` varchar(255) UNIQUE NOT NULL,
  `created_at` timestamp NOT NULL
);

CREATE TABLE `activity` (
  `id` uuid PRIMARY KEY,
  `activity_type_id` uuid NOT NULL,
  `identifier` varchar(255) UNIQUE NOT NULL,
  `created_at` timestamp NOT NULL
);

CREATE TABLE `activity_entity` (
  `id` uuid PRIMARY KEY,
  `activity_id` uuid NOT NULL,
  `entity_id` uuid NOT NULL,
  `direction` ENUM ('input', 'output') NOT NULL,
  `role` varchar(255),
  `sequence_no` integer,
  `created_at` timestamp NOT NULL
);

CREATE TABLE `entity_information_record` (
  `id` uuid PRIMARY KEY,
  `entity_id` uuid NOT NULL,
  `information_record_type_id` uuid,
  `version` integer NOT NULL,
  `valid_from` timestamp,
  `valid_until` timestamp,
  `recorded_at` timestamp NOT NULL,
  `recorded_by_agent_id` uuid,
  `supersedes_record_id` uuid,
  `name` varchar(255),
  `description` text,
  `status` varchar(255),
  `metadata` jsonb
);

CREATE TABLE `information_record_type` (
  `id` uuid PRIMARY KEY,
  `code` varchar(255) UNIQUE NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text,
  `created_at` timestamp NOT NULL
);

CREATE TABLE `activity_information_record` (
  `id` uuid PRIMARY KEY,
  `activity_id` uuid NOT NULL,
  `version` integer NOT NULL,
  `valid_from` timestamp,
  `valid_until` timestamp,
  `recorded_at` timestamp NOT NULL,
  `recorded_by_agent_id` uuid,
  `supersedes_record_id` uuid,
  `status` ENUM ('planned', 'in_progress', 'completed', 'failed', 'cancelled'),
  `started_at` timestamp,
  `ended_at` timestamp,
  `protocol_id` uuid,
  `operator_agent_id` uuid,
  `instrument_id` uuid,
  `description` text,
  `notes` text,
  `metadata` jsonb
);

CREATE TABLE `parameter_definition` (
  `id` uuid PRIMARY KEY,
  `code` varchar(255) UNIQUE NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text,
  `datatype` ENUM ('text', 'integer', 'decimal', 'boolean', 'datetime', 'categorical', 'json') NOT NULL,
  `canonical_unit` varchar(255),
  `ontology_id` varchar(255),
  `ontology_uri` varchar(255),
  `created_at` timestamp NOT NULL
);

CREATE TABLE `activity_parameter` (
  `id` uuid PRIMARY KEY,
  `activity_information_record_id` uuid NOT NULL,
  `parameter_definition_id` uuid,
  `parameter_name` varchar(255),
  `value_text` text,
  `value_integer` bigint,
  `value_decimal` decimal,
  `value_boolean` boolean,
  `value_datetime` timestamp,
  `value_json` jsonb,
  `unit` varchar(255),
  `sequence_no` integer,
  `metadata` jsonb
);

CREATE TABLE `protocol` (
  `id` uuid PRIMARY KEY,
  `identifier` varchar(255) UNIQUE NOT NULL,
  `name` varchar(255) NOT NULL,
  `version` varchar(255),
  `description` text,
  `uri` varchar(255),
  `created_at` timestamp NOT NULL
);

CREATE TABLE `protocol_parameter` (
  `id` uuid PRIMARY KEY,
  `protocol_id` uuid NOT NULL,
  `parameter_definition_id` uuid NOT NULL,
  `required` boolean DEFAULT false,
  `default_value_text` text,
  `default_value_decimal` decimal,
  `minimum_value` decimal,
  `maximum_value` decimal,
  `unit` varchar(255),
  `description` text
);

CREATE TABLE `agent` (
  `id` uuid PRIMARY KEY,
  `identifier` varchar(255) UNIQUE NOT NULL,
  `agent_type` ENUM ('person', 'organization', 'software', 'service') NOT NULL,
  `name` varchar(255) NOT NULL,
  `affiliation` varchar(255),
  `created_at` timestamp NOT NULL,
  `metadata` jsonb
);

CREATE TABLE `instrument` (
  `id` uuid PRIMARY KEY,
  `identifier` varchar(255) UNIQUE NOT NULL,
  `instrument_type` varchar(255),
  `manufacturer` varchar(255),
  `model` varchar(255),
  `serial_number` varchar(255),
  `software_version` varchar(255),
  `created_at` timestamp NOT NULL,
  `metadata` jsonb
);

CREATE TABLE `accession_information` (
  `activity_information_record_id` uuid PRIMARY KEY,
  `accession_number` varchar(255) UNIQUE NOT NULL,
  `accessioned_at` timestamp,
  `source_organization_agent_id` uuid,
  `received_by_agent_id` uuid,
  `external_specimen_identifier` varchar(255),
  `shipment_reference` varchar(255),
  `transfer_reference` varchar(255),
  `provenance_status` ENUM ('complete', 'partial', 'external', 'unavailable', 'unknown') NOT NULL,
  `source_description` text,
  `metadata` jsonb
);

CREATE TABLE `external_reference` (
  `id` uuid PRIMARY KEY,
  `subject_type` ENUM ('entity', 'activity') NOT NULL,
  `entity_id` uuid,
  `activity_id` uuid,
  `namespace` varchar(255),
  `external_id` varchar(255) NOT NULL,
  `source_system` varchar(255),
  `source_organization` varchar(255),
  `uri` varchar(255),
  `description` text,
  `created_at` timestamp NOT NULL,
  `metadata` jsonb
);

CREATE TABLE `entity_provenance` (
  `entity_id` uuid PRIMARY KEY,
  `provenance_status` ENUM ('complete', 'partial', 'external', 'unavailable', 'unknown') NOT NULL,
  `provenance_boundary_activity_id` uuid,
  `source_description` text,
  `notes` text
);

CREATE TABLE `entity_relation_type` (
  `id` uuid PRIMARY KEY,
  `code` varchar(255) UNIQUE NOT NULL,
  `name` varchar(255) NOT NULL,
  `description` text
);

CREATE TABLE `entity_relation` (
  `id` uuid PRIMARY KEY,
  `source_entity_id` uuid NOT NULL,
  `target_entity_id` uuid NOT NULL,
  `entity_relation_type_id` uuid NOT NULL,
  `activity_id` uuid,
  `created_at` timestamp NOT NULL,
  `metadata` jsonb
);

CREATE UNIQUE INDEX `activity_entity_index_0` ON `activity_entity` (`activity_id`, `entity_id`, `direction`, `role`);

CREATE INDEX `activity_entity_index_1` ON `activity_entity` (`activity_id`);

CREATE INDEX `activity_entity_index_2` ON `activity_entity` (`entity_id`);

CREATE UNIQUE INDEX `entity_information_record_index_3` ON `entity_information_record` (`entity_id`, `version`);

CREATE INDEX `entity_information_record_index_4` ON `entity_information_record` (`entity_id`, `valid_from`);

CREATE INDEX `entity_information_record_index_5` ON `entity_information_record` (`entity_id`);

CREATE UNIQUE INDEX `activity_information_record_index_6` ON `activity_information_record` (`activity_id`, `version`);

CREATE INDEX `activity_information_record_index_7` ON `activity_information_record` (`activity_id`);

CREATE INDEX `activity_parameter_index_8` ON `activity_parameter` (`activity_information_record_id`);

CREATE INDEX `activity_parameter_index_9` ON `activity_parameter` (`parameter_definition_id`);

CREATE UNIQUE INDEX `protocol_parameter_index_10` ON `protocol_parameter` (`protocol_id`, `parameter_definition_id`);

CREATE INDEX `external_reference_index_11` ON `external_reference` (`namespace`, `external_id`);

CREATE INDEX `external_reference_index_12` ON `external_reference` (`entity_id`);

CREATE INDEX `external_reference_index_13` ON `external_reference` (`activity_id`);

CREATE UNIQUE INDEX `entity_relation_index_14` ON `entity_relation` (`source_entity_id`, `target_entity_id`, `entity_relation_type_id`);

ALTER TABLE `entity_type` COMMENT = 'Hierarchical vocabulary describing entity classes.

Example hierarchy:

biological_source
  donor

material_entity
  biospecimen
    whole_brain
    hemisphere
    slab
    tissue_block
  biosample
    tissue_section
    tissue_curl
    aliquot

physical_artifact
  slide
  container

digital_entity
  image
  volume
  segmentation
  feature_set
  annotation
';

ALTER TABLE `activity_type` COMMENT = 'Hierarchical vocabulary of activities.

Example hierarchy:

acquisition
  accession
  extraction

preservation
  perfusion
  fixation
  cryoprotection
  freezing
  storage

processing
  dissection
  slabbing
  sectioning
  mounting
  staining

imaging
  slide_scanning
  MRI
  microscopy

computational_processing
  registration
  normalization
  segmentation
  feature_extraction
';

ALTER TABLE `entity` COMMENT = 'Immutable provenance node representing a biological,
physical, or digital entity.

Mutable properties such as names, classifications,
locations, condition, status, etc. belong in
entity_information_record.

physical_identity_id can associate multiple provenance
states with the same physical object.

Example:

fresh brain  -> P001
fixed brain  -> P001
frozen brain -> P001

After physical subdivision:

left hemisphere  -> P002
right hemisphere -> P003
';

ALTER TABLE `physical_identity` COMMENT = 'Represents persistent physical identity independently
of processing state.
';

ALTER TABLE `activity` COMMENT = 'Immutable provenance event.

Activity execution details are stored in
activity_information_record.

Activities may have zero inputs or zero outputs.

Example:
  accession: 0 -> N
  fixation:   N -> N
  disposal:   N -> 0
';

ALTER TABLE `activity_entity` COMMENT = 'Junction table implementing the provenance graph:

     Entity -> Activity -> Entity

No database constraint requires an activity to have an
input. This intentionally supports accession activities.
';

ALTER TABLE `entity_information_record` COMMENT = 'Versioned sidecar record describing an Entity.

Changes in knowledge create a new InformationRecord
rather than modifying the Entity.

Examples:
  anatomical designation
  specimen condition
  storage location
  QC state
  custodian
  availability
  descriptive annotation
';

ALTER TABLE `information_record_type` COMMENT = 'Allows independent information sidecars.

Examples:

  general
  anatomical
  storage
  quality_control
  custody
  clinical_annotation
  imaging
';

ALTER TABLE `activity_information_record` COMMENT = 'Versioned sidecar describing Activity execution.

The Activity establishes that an event exists.
This record captures what is currently known
about that event.

Includes execution details such as:
  timing
  operator
  instrument
  protocol
  status
  notes

Process parameters are stored separately in
activity_parameter.
';

ALTER TABLE `parameter_definition` COMMENT = 'Controlled definition of reusable process parameters.

Examples:

  fixation_temperature
  fixation_duration
  fixative_concentration
  section_thickness
  scanner_resolution
  laser_power
';

ALTER TABLE `activity_parameter` COMMENT = 'Captures actual execution parameters for an activity.

Example:

  fixation_temperature = 4.3 C
  fixation_duration = 76.2 h
  formalin_concentration = 10 %

Parameter_definition_id is preferred for controlled
parameters.

parameter_name permits ad-hoc parameters during
exploratory workflows.
';

ALTER TABLE `protocol` COMMENT = 'Protocol defines intended procedure:

      what SHOULD happen.

activity_parameter captures execution:

      what DID happen.
';

ALTER TABLE `agent` COMMENT = 'An Agent may be:

  person
  organization
  software
  service

This permits both wet-lab and computational provenance.
';

ALTER TABLE `accession_information` COMMENT = 'Activity-specific extension for accession.

An accession Activity does not require a locally
represented input Entity.

Example:

   unknown external provenance
             |
         accession
             |
        whole brain

External identifiers can still be retained without
creating artificial upstream entities.
';

ALTER TABLE `external_reference` COMMENT = 'Provides traceability to external systems without
importing their complete provenance graph.

Examples:

  hospital pathology accession
  LIMS identifier
  collaborator specimen code
  external imaging study ID
';

ALTER TABLE `entity_provenance` COMMENT = 'Describes completeness of provenance prior to the
entity entering the locally managed provenance graph.

Especially useful for accessioned material.
';

ALTER TABLE `entity_relation_type` COMMENT = 'Useful relation examples:

  part_of
  same_physical_entity_as
  derived_from
  aliquot_of
  version_of

These relationships provide convenient traversal,
but Activity remains the authoritative process
provenance mechanism.
';

ALTER TABLE `entity_type` ADD FOREIGN KEY (`parent_id`) REFERENCES `entity_type` (`id`);

ALTER TABLE `activity_type` ADD FOREIGN KEY (`parent_id`) REFERENCES `activity_type` (`id`);

ALTER TABLE `entity` ADD FOREIGN KEY (`entity_type_id`) REFERENCES `entity_type` (`id`);

ALTER TABLE `entity` ADD FOREIGN KEY (`physical_identity_id`) REFERENCES `physical_identity` (`id`);

ALTER TABLE `activity` ADD FOREIGN KEY (`activity_type_id`) REFERENCES `activity_type` (`id`);

ALTER TABLE `activity_entity` ADD FOREIGN KEY (`activity_id`) REFERENCES `activity` (`id`);

ALTER TABLE `activity_entity` ADD FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`);

ALTER TABLE `entity_information_record` ADD FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`);

ALTER TABLE `entity_information_record` ADD FOREIGN KEY (`supersedes_record_id`) REFERENCES `entity_information_record` (`id`);

ALTER TABLE `entity_information_record` ADD FOREIGN KEY (`information_record_type_id`) REFERENCES `information_record_type` (`id`);

ALTER TABLE `activity_information_record` ADD FOREIGN KEY (`activity_id`) REFERENCES `activity` (`id`);

ALTER TABLE `activity_information_record` ADD FOREIGN KEY (`supersedes_record_id`) REFERENCES `activity_information_record` (`id`);

ALTER TABLE `activity_parameter` ADD FOREIGN KEY (`activity_information_record_id`) REFERENCES `activity_information_record` (`id`);

ALTER TABLE `activity_parameter` ADD FOREIGN KEY (`parameter_definition_id`) REFERENCES `parameter_definition` (`id`);

ALTER TABLE `protocol_parameter` ADD FOREIGN KEY (`protocol_id`) REFERENCES `protocol` (`id`);

ALTER TABLE `protocol_parameter` ADD FOREIGN KEY (`parameter_definition_id`) REFERENCES `parameter_definition` (`id`);

ALTER TABLE `activity_information_record` ADD FOREIGN KEY (`protocol_id`) REFERENCES `protocol` (`id`);

ALTER TABLE `entity_information_record` ADD FOREIGN KEY (`recorded_by_agent_id`) REFERENCES `agent` (`id`);

ALTER TABLE `activity_information_record` ADD FOREIGN KEY (`recorded_by_agent_id`) REFERENCES `agent` (`id`);

ALTER TABLE `activity_information_record` ADD FOREIGN KEY (`operator_agent_id`) REFERENCES `agent` (`id`);

ALTER TABLE `activity_information_record` ADD FOREIGN KEY (`instrument_id`) REFERENCES `instrument` (`id`);

ALTER TABLE `activity_information_record` ADD FOREIGN KEY (`id`) REFERENCES `accession_information` (`activity_information_record_id`);

ALTER TABLE `accession_information` ADD FOREIGN KEY (`source_organization_agent_id`) REFERENCES `agent` (`id`);

ALTER TABLE `accession_information` ADD FOREIGN KEY (`received_by_agent_id`) REFERENCES `agent` (`id`);

ALTER TABLE `external_reference` ADD FOREIGN KEY (`entity_id`) REFERENCES `entity` (`id`);

ALTER TABLE `external_reference` ADD FOREIGN KEY (`activity_id`) REFERENCES `activity` (`id`);

ALTER TABLE `entity` ADD FOREIGN KEY (`id`) REFERENCES `entity_provenance` (`entity_id`);

ALTER TABLE `entity_provenance` ADD FOREIGN KEY (`provenance_boundary_activity_id`) REFERENCES `activity` (`id`);

ALTER TABLE `entity_relation` ADD FOREIGN KEY (`source_entity_id`) REFERENCES `entity` (`id`);

ALTER TABLE `entity_relation` ADD FOREIGN KEY (`target_entity_id`) REFERENCES `entity` (`id`);

ALTER TABLE `entity_relation` ADD FOREIGN KEY (`entity_relation_type_id`) REFERENCES `entity_relation_type` (`id`);

ALTER TABLE `entity_relation` ADD FOREIGN KEY (`activity_id`) REFERENCES `activity` (`id`);
