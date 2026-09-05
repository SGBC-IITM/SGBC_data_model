-- SGBC sample data for provenance model demonstration
-- Generated for the schema in SGBC_data_model.sql
--
-- IMPORTANT SCHEMA NOTE:
-- dbdiagram.io exported two 1:1 foreign keys in the reverse direction:
--   activity_information_record.id -> accession_information.activity_information_record_id
--   entity.id -> entity_provenance.entity_id
-- For the intended optional-extension semantics these should instead be:
--   accession_information.activity_information_record_id -> activity_information_record.id
--   entity_provenance.entity_id -> entity.id
--
-- This sample assumes those two foreign keys have been corrected.
-- MySQL also uses JSON rather than JSONB. If you are using MySQL (not PostgreSQL),
-- change jsonb columns in the schema to JSON before creating the database.

SET @now = '2026-09-05 12:00:00';

START TRANSACTION;

-- ============================================================
-- 1. CONTROLLED VOCABULARIES: ENTITY TYPES
-- ============================================================
INSERT INTO entity_type (id, code, name, description, parent_id, created_at) VALUES
('10000000-0000-0000-0000-000000000001','biological_source','Biological Source','Source biological subject',NULL,@now),
('10000000-0000-0000-0000-000000000002','donor','Donor','Human donor','10000000-0000-0000-0000-000000000001',@now),
('10000000-0000-0000-0000-000000000010','material_entity','Material Entity','Physical biological material',NULL,@now),
('10000000-0000-0000-0000-000000000011','biospecimen','Biospecimen','Primary biological specimen','10000000-0000-0000-0000-000000000010',@now),
('10000000-0000-0000-0000-000000000012','whole_brain','Whole Brain','Whole human brain specimen','10000000-0000-0000-0000-000000000011',@now),
('10000000-0000-0000-0000-000000000013','slab','Brain Slab','Macroscopic brain slab','10000000-0000-0000-0000-000000000011',@now),
('10000000-0000-0000-0000-000000000014','biosample','Biosample','Sample derived from a biospecimen','10000000-0000-0000-0000-000000000010',@now),
('10000000-0000-0000-0000-000000000015','tissue_section','Tissue Section','Histological tissue section','10000000-0000-0000-0000-000000000014',@now),
('10000000-0000-0000-0000-000000000020','physical_artifact','Physical Artifact','Physical artifact used or produced by processing',NULL,@now),
('10000000-0000-0000-0000-000000000021','slide','Glass Slide','Mounted histology slide','10000000-0000-0000-0000-000000000020',@now),
('10000000-0000-0000-0000-000000000030','digital_entity','Digital Entity','Digital data artifact',NULL,@now),
('10000000-0000-0000-0000-000000000031','image','Image','Digital image','10000000-0000-0000-0000-000000000030',@now),
('10000000-0000-0000-0000-000000000032','segmentation','Segmentation','Derived segmentation mask','10000000-0000-0000-0000-000000000030',@now);

-- ============================================================
-- 2. CONTROLLED VOCABULARIES: ACTIVITY TYPES
-- ============================================================
INSERT INTO activity_type (id, code, name, description, parent_id, created_at) VALUES
('20000000-0000-0000-0000-000000000001','acquisition','Acquisition','Entry or acquisition of material',NULL,@now),
('20000000-0000-0000-0000-000000000002','accession','Accession','Material enters local custody without requiring a modeled upstream entity','20000000-0000-0000-0000-000000000001',@now),
('20000000-0000-0000-0000-000000000010','preservation','Preservation','Preservation activities',NULL,@now),
('20000000-0000-0000-0000-000000000011','fixation','Fixation','Tissue fixation','20000000-0000-0000-0000-000000000010',@now),
('20000000-0000-0000-0000-000000000020','processing','Processing','Physical tissue processing',NULL,@now),
('20000000-0000-0000-0000-000000000021','slabbing','Slabbing','Subdivision of whole brain into slabs','20000000-0000-0000-0000-000000000020',@now),
('20000000-0000-0000-0000-000000000022','sectioning','Sectioning','Microtome/cryostat sectioning','20000000-0000-0000-0000-000000000020',@now),
('20000000-0000-0000-0000-000000000023','mounting','Mounting','Mount tissue section on glass slide','20000000-0000-0000-0000-000000000020',@now),
('20000000-0000-0000-0000-000000000024','staining','Staining','Histological staining','20000000-0000-0000-0000-000000000020',@now),
('20000000-0000-0000-0000-000000000030','imaging','Imaging','Image acquisition',NULL,@now),
('20000000-0000-0000-0000-000000000031','slide_scanning','Slide Scanning','Whole-slide image acquisition','20000000-0000-0000-0000-000000000030',@now),
('20000000-0000-0000-0000-000000000040','computational_processing','Computational Processing','Computational derivation',NULL,@now),
('20000000-0000-0000-0000-000000000041','segmentation','Segmentation','Computational image segmentation','20000000-0000-0000-0000-000000000040',@now);

-- ============================================================
-- 3. INFORMATION RECORD TYPES
-- ============================================================
INSERT INTO information_record_type (id, code, name, description, created_at) VALUES
('30000000-0000-0000-0000-000000000001','general','General','General descriptive information',@now),
('30000000-0000-0000-0000-000000000002','anatomical','Anatomical','Anatomical description and interpretation',@now),
('30000000-0000-0000-0000-000000000003','storage','Storage','Storage location and condition',@now),
('30000000-0000-0000-0000-000000000004','quality_control','Quality Control','QC observations and status',@now),
('30000000-0000-0000-0000-000000000005','imaging','Imaging','Image-specific descriptive information',@now);

-- ============================================================
-- 4. AGENTS AND INSTRUMENTS
-- ============================================================
INSERT INTO agent (id, identifier, agent_type, name, affiliation, created_at, metadata) VALUES
('40000000-0000-0000-0000-000000000001','ORG-SGBC','organization','SGBC Histology Facility','SGBC',@now,NULL),
('40000000-0000-0000-0000-000000000002','ORG-EXT-001','organization','External Neuropathology Centre','External Institution',@now,NULL),
('40000000-0000-0000-0000-000000000003','USR-TECH-001','person','Histology Technician 01','SGBC',@now,NULL),
('40000000-0000-0000-0000-000000000004','USR-SCI-001','person','Researcher 01','SGBC',@now,NULL),
('40000000-0000-0000-0000-000000000005','SW-SEG-001','software','Neurohistology Segmentation Pipeline','SGBC',@now,'{"version":"0.1-demo"}');

INSERT INTO instrument (id, identifier, instrument_type, manufacturer, model, serial_number, software_version, created_at, metadata) VALUES
('50000000-0000-0000-0000-000000000001','INST-CRYO-001','cryostat','Leica Biosystems','CM3050 S','DEMO-CRYO-001',NULL,@now,NULL),
('50000000-0000-0000-0000-000000000002','INST-SCANNER-001','whole_slide_scanner','Leica Biosystems','Aperio GT 450','DEMO-SCAN-001','demo',@now,NULL);

-- ============================================================
-- 5. PARAMETER DEFINITIONS
-- ============================================================
INSERT INTO parameter_definition (id, code, name, description, datatype, canonical_unit, created_at) VALUES
('60000000-0000-0000-0000-000000000001','fixative','Fixative','Fixative formulation','text',NULL,@now),
('60000000-0000-0000-0000-000000000002','fixation_temperature','Fixation Temperature','Temperature during fixation','decimal','degC',@now),
('60000000-0000-0000-0000-000000000003','fixation_duration','Fixation Duration','Duration of fixation','decimal','h',@now),
('60000000-0000-0000-0000-000000000004','section_thickness','Section Thickness','Nominal section thickness','decimal','um',@now),
('60000000-0000-0000-0000-000000000005','stain','Stain','Histological stain','categorical',NULL,@now),
('60000000-0000-0000-0000-000000000006','scan_resolution','Scan Resolution','Pixel size at acquisition','decimal','um_per_pixel',@now),
('60000000-0000-0000-0000-000000000007','model_name','Model Name','Computational model used','text',NULL,@now),
('60000000-0000-0000-0000-000000000008','model_version','Model Version','Computational model version','text',NULL,@now);

-- ============================================================
-- 6. PROTOCOLS AND EXPECTED PARAMETERS
-- ============================================================
INSERT INTO protocol (id, identifier, name, version, description, uri, created_at) VALUES
('70000000-0000-0000-0000-000000000001','PROT-FIX-001','Whole Brain Fixation','1.0','Demo whole-brain immersion fixation protocol',NULL,@now),
('70000000-0000-0000-0000-000000000002','PROT-SEC-001','Cryostat Sectioning','1.0','Demo serial sectioning protocol',NULL,@now),
('70000000-0000-0000-0000-000000000003','PROT-NISSL-001','Nissl Staining','1.0','Demo Nissl staining protocol',NULL,@now),
('70000000-0000-0000-0000-000000000004','PROT-SCAN-001','Whole Slide Scanning','1.0','Demo WSI acquisition protocol',NULL,@now);

INSERT INTO protocol_parameter (id, protocol_id, parameter_definition_id, required, default_value_text, default_value_decimal, unit, description) VALUES
('71000000-0000-0000-0000-000000000001','70000000-0000-0000-0000-000000000001','60000000-0000-0000-0000-000000000001',TRUE,'10% neutral buffered formalin',NULL,NULL,'Expected fixative'),
('71000000-0000-0000-0000-000000000002','70000000-0000-0000-0000-000000000001','60000000-0000-0000-0000-000000000002',TRUE,NULL,4.0,'degC','Target temperature'),
('71000000-0000-0000-0000-000000000003','70000000-0000-0000-0000-000000000001','60000000-0000-0000-0000-000000000003',TRUE,NULL,72.0,'h','Target duration'),
('71000000-0000-0000-0000-000000000004','70000000-0000-0000-0000-000000000002','60000000-0000-0000-0000-000000000004',TRUE,NULL,20.0,'um','Nominal section thickness'),
('71000000-0000-0000-0000-000000000005','70000000-0000-0000-0000-000000000003','60000000-0000-0000-0000-000000000005',TRUE,'Nissl',NULL,NULL,'Required stain'),
('71000000-0000-0000-0000-000000000006','70000000-0000-0000-0000-000000000004','60000000-0000-0000-0000-000000000006',TRUE,NULL,0.5,'um_per_pixel','Target scan resolution');

-- ============================================================
-- 7. PHYSICAL IDENTITIES
-- Same identity is retained across state transformations.
-- ============================================================
INSERT INTO physical_identity (id, identifier, created_at) VALUES
('80000000-0000-0000-0000-000000000001','PHY-BRAIN-001',@now),
('80000000-0000-0000-0000-000000000002','PHY-SLAB-001',@now),
('80000000-0000-0000-0000-000000000003','PHY-SLAB-002',@now),
('80000000-0000-0000-0000-000000000004','PHY-SLAB-003',@now),
('80000000-0000-0000-0000-000000000005','PHY-SEC-001',@now),
('80000000-0000-0000-0000-000000000006','PHY-SEC-002',@now),
('80000000-0000-0000-0000-000000000007','PHY-SEC-003',@now),
('80000000-0000-0000-0000-000000000008','PHY-SLIDE-001',@now);

-- ============================================================
-- 8. ENTITIES
-- Whole brain is accessioned from an external source; there is deliberately
-- no local donor/source entity upstream of it.
-- ============================================================
INSERT INTO entity (id, entity_type_id, identifier, physical_identity_id, created_at) VALUES
('90000000-0000-0000-0000-000000000001','10000000-0000-0000-0000-000000000012','BRN-2026-001','80000000-0000-0000-0000-000000000001','2026-08-01 09:30:00'),
('90000000-0000-0000-0000-000000000002','10000000-0000-0000-0000-000000000012','BRN-2026-001-FIXED','80000000-0000-0000-0000-000000000001','2026-08-04 10:00:00'),
('90000000-0000-0000-0000-000000000011','10000000-0000-0000-0000-000000000013','BRN-2026-001-SLAB-01','80000000-0000-0000-0000-000000000002','2026-08-05 10:00:00'),
('90000000-0000-0000-0000-000000000012','10000000-0000-0000-0000-000000000013','BRN-2026-001-SLAB-02','80000000-0000-0000-0000-000000000003','2026-08-05 10:00:00'),
('90000000-0000-0000-0000-000000000013','10000000-0000-0000-0000-000000000013','BRN-2026-001-SLAB-03','80000000-0000-0000-0000-000000000004','2026-08-05 10:00:00'),
('90000000-0000-0000-0000-000000000021','10000000-0000-0000-0000-000000000015','BRN-2026-001-S02-SEC-001','80000000-0000-0000-0000-000000000005','2026-08-06 10:00:00'),
('90000000-0000-0000-0000-000000000022','10000000-0000-0000-0000-000000000015','BRN-2026-001-S02-SEC-002','80000000-0000-0000-0000-000000000006','2026-08-06 10:01:00'),
('90000000-0000-0000-0000-000000000023','10000000-0000-0000-0000-000000000015','BRN-2026-001-S02-SEC-003','80000000-0000-0000-0000-000000000007','2026-08-06 10:02:00'),
('90000000-0000-0000-0000-000000000031','10000000-0000-0000-0000-000000000021','BRN-2026-001-S02-SLIDE-001','80000000-0000-0000-0000-000000000008','2026-08-06 11:00:00'),
('90000000-0000-0000-0000-000000000041','10000000-0000-0000-0000-000000000031','IMG-2026-001-S02-NISSL-001',NULL,'2026-08-07 15:00:00'),
('90000000-0000-0000-0000-000000000051','10000000-0000-0000-0000-000000000032','SEG-2026-001-S02-001',NULL,'2026-08-08 12:00:00');

-- ============================================================
-- 9. ACTIVITIES
-- ============================================================
INSERT INTO activity (id, activity_type_id, identifier, created_at) VALUES
('a0000000-0000-0000-0000-000000000001','20000000-0000-0000-0000-000000000002','ACC-2026-001','2026-08-01 09:30:00'),
('a0000000-0000-0000-0000-000000000002','20000000-0000-0000-0000-000000000011','FIX-2026-001','2026-08-01 10:00:00'),
('a0000000-0000-0000-0000-000000000003','20000000-0000-0000-0000-000000000021','SLAB-2026-001','2026-08-05 09:00:00'),
('a0000000-0000-0000-0000-000000000004','20000000-0000-0000-0000-000000000022','SEC-2026-001','2026-08-06 09:00:00'),
('a0000000-0000-0000-0000-000000000005','20000000-0000-0000-0000-000000000023','MOUNT-2026-001','2026-08-06 10:30:00'),
('a0000000-0000-0000-0000-000000000006','20000000-0000-0000-0000-000000000024','STAIN-2026-001','2026-08-07 09:00:00'),
('a0000000-0000-0000-0000-000000000007','20000000-0000-0000-0000-000000000031','SCAN-2026-001','2026-08-07 14:30:00'),
('a0000000-0000-0000-0000-000000000008','20000000-0000-0000-0000-000000000041','SEG-2026-001','2026-08-08 11:00:00');

-- ============================================================
-- 10. ACTIVITY <-> ENTITY PROVENANCE EDGES
-- Accession has no input edge by design.
-- ============================================================
INSERT INTO activity_entity (id, activity_id, entity_id, direction, role, sequence_no, created_at) VALUES
('b0000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000001','90000000-0000-0000-0000-000000000001','output','accessioned_specimen',1,'2026-08-01 09:30:00'),
('b0000000-0000-0000-0000-000000000002','a0000000-0000-0000-0000-000000000002','90000000-0000-0000-0000-000000000001','input','unfixed_brain',1,'2026-08-01 10:00:00'),
('b0000000-0000-0000-0000-000000000003','a0000000-0000-0000-0000-000000000002','90000000-0000-0000-0000-000000000002','output','fixed_brain',1,'2026-08-04 10:00:00'),
('b0000000-0000-0000-0000-000000000004','a0000000-0000-0000-0000-000000000003','90000000-0000-0000-0000-000000000002','input','whole_brain',1,'2026-08-05 09:00:00'),
('b0000000-0000-0000-0000-000000000005','a0000000-0000-0000-0000-000000000003','90000000-0000-0000-0000-000000000011','output','slab',1,'2026-08-05 10:00:00'),
('b0000000-0000-0000-0000-000000000006','a0000000-0000-0000-0000-000000000003','90000000-0000-0000-0000-000000000012','output','slab',2,'2026-08-05 10:00:00'),
('b0000000-0000-0000-0000-000000000007','a0000000-0000-0000-0000-000000000003','90000000-0000-0000-0000-000000000013','output','slab',3,'2026-08-05 10:00:00'),
('b0000000-0000-0000-0000-000000000008','a0000000-0000-0000-0000-000000000004','90000000-0000-0000-0000-000000000012','input','source_slab',1,'2026-08-06 09:00:00'),
('b0000000-0000-0000-0000-000000000009','a0000000-0000-0000-0000-000000000004','90000000-0000-0000-0000-000000000021','output','serial_section',1,'2026-08-06 10:00:00'),
('b0000000-0000-0000-0000-000000000010','a0000000-0000-0000-0000-000000000004','90000000-0000-0000-0000-000000000022','output','serial_section',2,'2026-08-06 10:01:00'),
('b0000000-0000-0000-0000-000000000011','a0000000-0000-0000-0000-000000000004','90000000-0000-0000-0000-000000000023','output','serial_section',3,'2026-08-06 10:02:00'),
('b0000000-0000-0000-0000-000000000012','a0000000-0000-0000-0000-000000000005','90000000-0000-0000-0000-000000000022','input','tissue_section',1,'2026-08-06 10:30:00'),
('b0000000-0000-0000-0000-000000000013','a0000000-0000-0000-0000-000000000005','90000000-0000-0000-0000-000000000031','output','mounted_slide',1,'2026-08-06 11:00:00'),
('b0000000-0000-0000-0000-000000000014','a0000000-0000-0000-0000-000000000006','90000000-0000-0000-0000-000000000031','input','unstained_slide',1,'2026-08-07 09:00:00'),
('b0000000-0000-0000-0000-000000000015','a0000000-0000-0000-0000-000000000006','90000000-0000-0000-0000-000000000031','output','nissl_stained_slide',1,'2026-08-07 12:00:00'),
('b0000000-0000-0000-0000-000000000016','a0000000-0000-0000-0000-000000000007','90000000-0000-0000-0000-000000000031','input','source_slide',1,'2026-08-07 14:30:00'),
('b0000000-0000-0000-0000-000000000017','a0000000-0000-0000-0000-000000000007','90000000-0000-0000-0000-000000000041','output','whole_slide_image',1,'2026-08-07 15:00:00'),
('b0000000-0000-0000-0000-000000000018','a0000000-0000-0000-0000-000000000008','90000000-0000-0000-0000-000000000041','input','source_image',1,'2026-08-08 11:00:00'),
('b0000000-0000-0000-0000-000000000019','a0000000-0000-0000-0000-000000000008','90000000-0000-0000-0000-000000000051','output','segmentation_mask',1,'2026-08-08 12:00:00');

-- ============================================================
-- 11. ENTITY INFORMATION RECORDS
-- Includes a deliberate anatomical-information revision for Slab 02.
-- ============================================================
INSERT INTO entity_information_record
(id, entity_id, information_record_type_id, version, valid_from, valid_until, recorded_at, recorded_by_agent_id, supersedes_record_id, name, description, status, metadata) VALUES
('c0000000-0000-0000-0000-000000000001','90000000-0000-0000-0000-000000000001','30000000-0000-0000-0000-000000000001',1,'2026-08-01 09:30:00',NULL,'2026-08-01 09:35:00','40000000-0000-0000-0000-000000000003',NULL,'Accessioned whole brain','Whole brain received from external neuropathology centre','received','{"condition":"received chilled","container":"sealed specimen container"}'),
('c0000000-0000-0000-0000-000000000002','90000000-0000-0000-0000-000000000002','30000000-0000-0000-0000-000000000001',1,'2026-08-04 10:00:00',NULL,'2026-08-04 10:10:00','40000000-0000-0000-0000-000000000003',NULL,'Fixed whole brain','Whole brain after fixation','available','{"fixation_state":"fixed"}'),
('c0000000-0000-0000-0000-000000000011','90000000-0000-0000-0000-000000000011','30000000-0000-0000-0000-000000000002',1,'2026-08-05 10:00:00',NULL,'2026-08-05 11:00:00','40000000-0000-0000-0000-000000000004',NULL,'Slab 01','Anterior brain slab','available','{"slab_index":1,"orientation":"coronal"}'),
('c0000000-0000-0000-0000-000000000012','90000000-0000-0000-0000-000000000012','30000000-0000-0000-0000-000000000002',1,'2026-08-05 10:00:00','2026-08-06 16:00:00','2026-08-05 11:00:00','40000000-0000-0000-0000-000000000004',NULL,'Slab 02','Anatomical assignment pending','provisional','{"slab_index":2,"anatomical_region":"unknown"}'),
('c0000000-0000-0000-0000-000000000013','90000000-0000-0000-0000-000000000012','30000000-0000-0000-0000-000000000002',2,'2026-08-06 16:00:00',NULL,'2026-08-06 16:05:00','40000000-0000-0000-0000-000000000004','c0000000-0000-0000-0000-000000000012','Slab 02','Anatomical assignment reviewed','confirmed','{"slab_index":2,"anatomical_region":"left frontal region"}'),
('c0000000-0000-0000-0000-000000000014','90000000-0000-0000-0000-000000000013','30000000-0000-0000-0000-000000000002',1,'2026-08-05 10:00:00',NULL,'2026-08-05 11:00:00','40000000-0000-0000-0000-000000000004',NULL,'Slab 03','Posterior brain slab','available','{"slab_index":3,"orientation":"coronal"}'),
('c0000000-0000-0000-0000-000000000021','90000000-0000-0000-0000-000000000021','30000000-0000-0000-0000-000000000001',1,'2026-08-06 10:00:00',NULL,'2026-08-06 10:10:00','40000000-0000-0000-0000-000000000003',NULL,'Serial section 001','First demo section from slab 02','available','{"section_index":1}'),
('c0000000-0000-0000-0000-000000000022','90000000-0000-0000-0000-000000000022','30000000-0000-0000-0000-000000000001',1,'2026-08-06 10:01:00',NULL,'2026-08-06 10:11:00','40000000-0000-0000-0000-000000000003',NULL,'Serial section 002','Second demo section from slab 02','available','{"section_index":2}'),
('c0000000-0000-0000-0000-000000000023','90000000-0000-0000-0000-000000000023','30000000-0000-0000-0000-000000000001',1,'2026-08-06 10:02:00',NULL,'2026-08-06 10:12:00','40000000-0000-0000-0000-000000000003',NULL,'Serial section 003','Third demo section from slab 02','available','{"section_index":3}'),
('c0000000-0000-0000-0000-000000000031','90000000-0000-0000-0000-000000000031','30000000-0000-0000-0000-000000000004',1,'2026-08-07 12:00:00',NULL,'2026-08-07 12:10:00','40000000-0000-0000-0000-000000000003',NULL,'Nissl slide','Mounted section after Nissl staining','qc_passed','{"stain":"Nissl","tissue_integrity":"good"}'),
('c0000000-0000-0000-0000-000000000041','90000000-0000-0000-0000-000000000041','30000000-0000-0000-0000-000000000005',1,'2026-08-07 15:00:00',NULL,'2026-08-07 15:05:00','40000000-0000-0000-0000-000000000004',NULL,'Nissl whole-slide image','Digitized Nissl section','available','{"format":"SVS","resolution_um_per_pixel":0.5}'),
('c0000000-0000-0000-0000-000000000051','90000000-0000-0000-0000-000000000051','30000000-0000-0000-0000-000000000004',1,'2026-08-08 12:00:00',NULL,'2026-08-08 12:05:00','40000000-0000-0000-0000-000000000004',NULL,'Gross anatomy segmentation','Demo segmentation derived from WSI','generated','{"classes":["cortex","white_matter","ventricle"]}');

-- ============================================================
-- 12. ACTIVITY INFORMATION RECORDS
-- Fixation has v1 + corrected v2 to demonstrate sidecar versioning.
-- ============================================================
INSERT INTO activity_information_record
(id, activity_id, version, valid_from, valid_until, recorded_at, recorded_by_agent_id, supersedes_record_id, status, started_at, ended_at, protocol_id, operator_agent_id, instrument_id, description, notes, metadata) VALUES
('d0000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000001',1,'2026-08-01 09:30:00',NULL,'2026-08-01 09:35:00','40000000-0000-0000-0000-000000000003',NULL,'completed','2026-08-01 09:30:00','2026-08-01 09:45:00',NULL,'40000000-0000-0000-0000-000000000003',NULL,'Accession of externally supplied whole brain','No upstream local entity created; external provenance retained as accession metadata',NULL),
('d0000000-0000-0000-0000-000000000002','a0000000-0000-0000-0000-000000000002',1,'2026-08-01 10:00:00','2026-08-04 11:00:00','2026-08-04 10:15:00','40000000-0000-0000-0000-000000000003',NULL,'completed','2026-08-01 10:00:00','2026-08-03 10:00:00','70000000-0000-0000-0000-000000000001','40000000-0000-0000-0000-000000000003',NULL,'Whole brain fixation','Initial record entered with duration transcribed as 48 h',NULL),
('d0000000-0000-0000-0000-000000000003','a0000000-0000-0000-0000-000000000002',2,'2026-08-04 11:00:00',NULL,'2026-08-04 11:05:00','40000000-0000-0000-0000-000000000004','d0000000-0000-0000-0000-000000000002','completed','2026-08-01 10:00:00','2026-08-04 10:00:00','70000000-0000-0000-0000-000000000001','40000000-0000-0000-0000-000000000003',NULL,'Whole brain fixation','Corrected from source worksheet: fixation duration was 72 h',NULL),
('d0000000-0000-0000-0000-000000000004','a0000000-0000-0000-0000-000000000003',1,'2026-08-05 09:00:00',NULL,'2026-08-05 10:05:00','40000000-0000-0000-0000-000000000003',NULL,'completed','2026-08-05 09:00:00','2026-08-05 10:00:00',NULL,'40000000-0000-0000-0000-000000000003',NULL,'Whole brain slabbing','Demo subdivision into three slabs',NULL),
('d0000000-0000-0000-0000-000000000005','a0000000-0000-0000-0000-000000000004',1,'2026-08-06 09:00:00',NULL,'2026-08-06 10:15:00','40000000-0000-0000-0000-000000000003',NULL,'completed','2026-08-06 09:00:00','2026-08-06 10:02:00','70000000-0000-0000-0000-000000000002','40000000-0000-0000-0000-000000000003','50000000-0000-0000-0000-000000000001','Serial sectioning of slab 02','Three representative sections inserted for demo',NULL),
('d0000000-0000-0000-0000-000000000006','a0000000-0000-0000-0000-000000000005',1,'2026-08-06 10:30:00',NULL,'2026-08-06 11:05:00','40000000-0000-0000-0000-000000000003',NULL,'completed','2026-08-06 10:30:00','2026-08-06 11:00:00',NULL,'40000000-0000-0000-0000-000000000003',NULL,'Mount section 002','Section mounted on glass slide',NULL),
('d0000000-0000-0000-0000-000000000007','a0000000-0000-0000-0000-000000000006',1,'2026-08-07 09:00:00',NULL,'2026-08-07 12:10:00','40000000-0000-0000-0000-000000000003',NULL,'completed','2026-08-07 09:00:00','2026-08-07 12:00:00','70000000-0000-0000-0000-000000000003','40000000-0000-0000-0000-000000000003',NULL,'Nissl staining','Routine Nissl stain',NULL),
('d0000000-0000-0000-0000-000000000008','a0000000-0000-0000-0000-000000000007',1,'2026-08-07 14:30:00',NULL,'2026-08-07 15:05:00','40000000-0000-0000-0000-000000000004',NULL,'completed','2026-08-07 14:30:00','2026-08-07 15:00:00','70000000-0000-0000-0000-000000000004','40000000-0000-0000-0000-000000000003','50000000-0000-0000-0000-000000000002','Whole-slide scanning','Digitization of Nissl slide',NULL),
('d0000000-0000-0000-0000-000000000009','a0000000-0000-0000-0000-000000000008',1,'2026-08-08 11:00:00',NULL,'2026-08-08 12:05:00','40000000-0000-0000-0000-000000000004',NULL,'completed','2026-08-08 11:00:00','2026-08-08 12:00:00',NULL,'40000000-0000-0000-0000-000000000005',NULL,'Gross anatomy segmentation','Demo computational derivative',NULL);

-- ============================================================
-- 13. ACCESSION-SPECIFIC INFORMATION
-- ============================================================
INSERT INTO accession_information
(activity_information_record_id, accession_number, accessioned_at, source_organization_agent_id, received_by_agent_id, external_specimen_identifier, shipment_reference, transfer_reference, provenance_status, source_description, metadata) VALUES
('d0000000-0000-0000-0000-000000000001','SGBC-ACC-2026-001','2026-08-01 09:30:00','40000000-0000-0000-0000-000000000002','40000000-0000-0000-0000-000000000003','EXT-BRAIN-7842','SHIP-DEMO-8841','MTA-DEMO-2026-17','external','Whole brain extracted and handled at external institution before transfer to SGBC','{"received_condition":"chilled","upstream_protocols_available":false}');

-- ============================================================
-- 14. ACTIVITY PARAMETERS
-- v1 vs v2 fixation parameters demonstrate corrected information.
-- ============================================================
INSERT INTO activity_parameter
(id, activity_information_record_id, parameter_definition_id, parameter_name, value_text, value_integer, value_decimal, value_boolean, value_datetime, value_json, unit, sequence_no, metadata) VALUES
('e0000000-0000-0000-0000-000000000001','d0000000-0000-0000-0000-000000000002','60000000-0000-0000-0000-000000000001',NULL,'10% neutral buffered formalin',NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),
('e0000000-0000-0000-0000-000000000002','d0000000-0000-0000-0000-000000000002','60000000-0000-0000-0000-000000000002',NULL,NULL,NULL,4.0,NULL,NULL,NULL,'degC',2,NULL),
('e0000000-0000-0000-0000-000000000003','d0000000-0000-0000-0000-000000000002','60000000-0000-0000-0000-000000000003',NULL,NULL,NULL,48.0,NULL,NULL,NULL,'h',3,'{"record_status":"superseded transcription"}'),
('e0000000-0000-0000-0000-000000000004','d0000000-0000-0000-0000-000000000003','60000000-0000-0000-0000-000000000001',NULL,'10% neutral buffered formalin',NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),
('e0000000-0000-0000-0000-000000000005','d0000000-0000-0000-0000-000000000003','60000000-0000-0000-0000-000000000002',NULL,NULL,NULL,4.0,NULL,NULL,NULL,'degC',2,NULL),
('e0000000-0000-0000-0000-000000000006','d0000000-0000-0000-0000-000000000003','60000000-0000-0000-0000-000000000003',NULL,NULL,NULL,72.0,NULL,NULL,NULL,'h',3,'{"record_status":"corrected"}'),
('e0000000-0000-0000-0000-000000000007','d0000000-0000-0000-0000-000000000005','60000000-0000-0000-0000-000000000004',NULL,NULL,NULL,20.0,NULL,NULL,NULL,'um',1,NULL),
('e0000000-0000-0000-0000-000000000008','d0000000-0000-0000-0000-000000000007','60000000-0000-0000-0000-000000000005',NULL,'Nissl',NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),
('e0000000-0000-0000-0000-000000000009','d0000000-0000-0000-0000-000000000008','60000000-0000-0000-0000-000000000006',NULL,NULL,NULL,0.5,NULL,NULL,NULL,'um_per_pixel',1,NULL),
('e0000000-0000-0000-0000-000000000010','d0000000-0000-0000-0000-000000000009','60000000-0000-0000-0000-000000000007',NULL,'Demo U-Net',NULL,NULL,NULL,NULL,NULL,NULL,1,NULL),
('e0000000-0000-0000-0000-000000000011','d0000000-0000-0000-0000-000000000009','60000000-0000-0000-0000-000000000008',NULL,'0.1',NULL,NULL,NULL,NULL,NULL,NULL,2,NULL);

-- ============================================================
-- 15. EXTERNAL REFERENCE AND PROVENANCE BOUNDARY
-- ============================================================
INSERT INTO external_reference
(id, subject_type, entity_id, activity_id, namespace, external_id, source_system, source_organization, uri, description, created_at, metadata) VALUES
('f0000000-0000-0000-0000-000000000001','entity','90000000-0000-0000-0000-000000000001',NULL,'external_pathology','EXT-BRAIN-7842','External Pathology LIMS','External Neuropathology Centre',NULL,'External specimen identifier retained at accession','2026-08-01 09:35:00',NULL),
('f0000000-0000-0000-0000-000000000002','activity',NULL,'a0000000-0000-0000-0000-000000000001','external_transfer','MTA-DEMO-2026-17','Transfer Register','External Neuropathology Centre',NULL,'External transfer reference associated with accession','2026-08-01 09:35:00',NULL);

INSERT INTO entity_provenance
(entity_id, provenance_status, provenance_boundary_activity_id, source_description, notes) VALUES
('90000000-0000-0000-0000-000000000001','external','a0000000-0000-0000-0000-000000000001','Specimen provenance prior to SGBC accession is external to this database','No artificial donor/source entity has been created.');

-- ============================================================
-- 16. OPTIONAL DIRECT ENTITY RELATIONS
-- These are convenience relations; Activity remains authoritative.
-- ============================================================
INSERT INTO entity_relation_type (id, code, name, description) VALUES
('aa000000-0000-0000-0000-000000000001','part_of','Part Of','Source entity is physically part of target entity'),
('aa000000-0000-0000-0000-000000000002','derived_from','Derived From','Source entity is derived from target entity'),
('aa000000-0000-0000-0000-000000000003','same_physical_entity_as','Same Physical Entity As','Two entity states refer to the same persistent physical object');

INSERT INTO entity_relation
(id, source_entity_id, target_entity_id, entity_relation_type_id, activity_id, created_at, metadata) VALUES
('ab000000-0000-0000-0000-000000000001','90000000-0000-0000-0000-000000000002','90000000-0000-0000-0000-000000000001','aa000000-0000-0000-0000-000000000003','a0000000-0000-0000-0000-000000000002','2026-08-04 10:00:00',NULL),
('ab000000-0000-0000-0000-000000000002','90000000-0000-0000-0000-000000000011','90000000-0000-0000-0000-000000000002','aa000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000003','2026-08-05 10:00:00',NULL),
('ab000000-0000-0000-0000-000000000003','90000000-0000-0000-0000-000000000012','90000000-0000-0000-0000-000000000002','aa000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000003','2026-08-05 10:00:00',NULL),
('ab000000-0000-0000-0000-000000000004','90000000-0000-0000-0000-000000000013','90000000-0000-0000-0000-000000000002','aa000000-0000-0000-0000-000000000001','a0000000-0000-0000-0000-000000000003','2026-08-05 10:00:00',NULL),
('ab000000-0000-0000-0000-000000000005','90000000-0000-0000-0000-000000000022','90000000-0000-0000-0000-000000000012','aa000000-0000-0000-0000-000000000002','a0000000-0000-0000-0000-000000000004','2026-08-06 10:01:00',NULL),
('ab000000-0000-0000-0000-000000000006','90000000-0000-0000-0000-000000000041','90000000-0000-0000-0000-000000000031','aa000000-0000-0000-0000-000000000002','a0000000-0000-0000-0000-000000000007','2026-08-07 15:00:00',NULL),
('ab000000-0000-0000-0000-000000000007','90000000-0000-0000-0000-000000000051','90000000-0000-0000-0000-000000000041','aa000000-0000-0000-0000-000000000002','a0000000-0000-0000-0000-000000000008','2026-08-08 12:00:00',NULL);

COMMIT;

-- ============================================================
-- USEFUL DEMO QUERIES
-- ============================================================

-- 1. Show all inputs/outputs of each activity
-- SELECT a.identifier AS activity, at.name AS activity_type,
--        ae.direction, ae.role, e.identifier AS entity
-- FROM activity a
-- JOIN activity_type at ON at.id = a.activity_type_id
-- JOIN activity_entity ae ON ae.activity_id = a.id
-- JOIN entity e ON e.id = ae.entity_id
-- ORDER BY a.created_at, ae.direction, ae.sequence_no;

-- 2. Show version history of fixation activity
-- SELECT a.identifier, air.version, air.recorded_at, air.notes,
--        pd.name AS parameter_name,
--        COALESCE(ap.value_text, CAST(ap.value_decimal AS CHAR)) AS value,
--        ap.unit
-- FROM activity a
-- JOIN activity_information_record air ON air.activity_id = a.id
-- LEFT JOIN activity_parameter ap ON ap.activity_information_record_id = air.id
-- LEFT JOIN parameter_definition pd ON pd.id = ap.parameter_definition_id
-- WHERE a.identifier = 'FIX-2026-001'
-- ORDER BY air.version, ap.sequence_no;

-- 3. Show accession provenance boundary
-- SELECT e.identifier, ep.provenance_status, ep.source_description,
--        a.identifier AS boundary_activity
-- FROM entity_provenance ep
-- JOIN entity e ON e.id = ep.entity_id
-- LEFT JOIN activity a ON a.id = ep.provenance_boundary_activity_id;
