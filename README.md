# SGBC_data_model

*I want to make a data model including biospecimen and biosample, which models relationships through the abstraction of Activity - eg in post mortem whole brain histology, the biospecimen is the donor, and the activity of extraction produces the biosample 'brain'. Now the biosample can again be acted upon, like perfusion, fixation, freezing, storing, etc, each producing an artifact. I want to model this using dbml*

Source discussion:
https://chatgpt.com/share/6a9bee09-d694-83ee-aecf-85ab059ac5a2

## High level ontology
<pre>
                    ENTITY
                      │
          ┌───────────┼──────────────┐
          │           │              │
 BiologicalSource  Material       Digital
     Donor          Entity         Entity
                     │
             ┌───────┴───────┐
          Biospecimen      Biosample

                     ↑
                     │
                   input
                     │
                  ACTIVITY
                     │
                   output
                     ↓

                    ENTITY
</pre>

### Accessioning 

                 ENTITY ORIGIN
                      │
          ┌───────────┼─────────────┐
          │           │             │
       Derived     Accessioned    Created
          │           │             │
    known input    no local       no material
      entities      input           input
          │           │             │
    sectioning     tissue         annotation
    extraction     received       segmentation
    staining       externally     generated data

## Activity type
<pre>
processing
├── extraction
├── preservation
│   ├── perfusion
│   ├── fixation
│   ├── cryoprotection
│   ├── freezing
│   └── storage
├── dissection
│   ├── hemisphere_separation
│   ├── slabbing
│   └── block_extraction
├── sectioning
├── staining
│   ├── Nissl
│   ├── H&E
│   ├── Myelin
│   └── IHC
└── acquisition
    ├── slide_scanning
    ├── MRI
    └── spatial_transcriptomics
</pre>

## Information sidecars
*i want to implement sidecar information records for all entities and also activities. The information record decouples the entity's mutable fields from the immutable ones (which will be attributes in the entity). Also the information record for the activity captures the set of process parameters (name,value pairs)*

<pre>
ENTITY
    immutable assertion:
    "this thing exists"

INFORMATION RECORD
    temporal assertion:
    "these facts are currently known about this thing"

ACTIVITY
    immutable assertion:
    "this event exists"

INFORMATION RECORD
    temporal assertion:
    "these are the currently known properties of that event"
</pre>

Example:

<pre>
Brain B001
   │
   ├── AnatomicalInformationRecord
   │      whole brain
   │      hemisphere status
   │      orientation
   │
   ├── StorageInformationRecord
   │      freezer
   │      shelf
   │      temperature
   │
   └── QCInformationRecord
          tissue integrity
          fixation quality
</pre>

<pre>
                         ┌────────────────────┐
                         │       Entity       │
                         │ immutable identity │
                         └─────────┬──────────┘
                                   │
                            has information
                                   │
                    ┌──────────────▼──────────────┐
                    │ Entity Information Record   │
                    │ versioned / mutable state   │
                    └─────────────────────────────┘
</pre>

<pre>
Entity ── input ──► Activity ── output ──► Entity
                        │
                        │ has information
                        ▼
              ┌──────────────────────────┐
              │ Activity Information     │
              │ Record                   │
              └────────────┬─────────────┘
                           │
                         has
                           ▼
                  Activity Parameter
                  name/value/unit
</pre>

<pre>
                   no known input
                        │
                        ▼
                  Accession Activity
                        │
             ActivityInformationRecord
                        │
         source institution = ...
         received date = ...
         external id = ...
                        │
                        ▼
                   Brain Entity
                        │
                        ▼
             EntityInformationRecord
</pre>


## DB diagram
<pre>
                               Agent
                                 |
                                 |
EntityInformationRecord       ActivityInformationRecord
          |                         |
          |                         +---- ActivityParameter
          |                         |
          v                         v
       ENTITY ---- input ----> ACTIVITY ---- output ----> ENTITY
                                   |
                                   |
                               Protocol
</pre>
https://dbdiagram.io/d/SGBC_data_model-6a9bea4f5450bea1bef885bb


## Summary

| Situation                        | Representation                                  |
| -------------------------------- | ----------------------------------------------- |
| Tissue extracted internally      | `Donor → Extraction → Brain`                    |
| Tissue received externally       | `0 → Accession → Brain`                         |
| Brain fixed                      | `Brain → Fixation → Fixed Brain state`          |
| Brain physically divided         | `Brain → Dissection → Hemisphere(s)`            |
| Metadata correction              | new `EntityInformationRecord`                   |
| Process parameter correction     | new `ActivityInformationRecord` + parameter set |
| Protocol changed                 | new/versioned `Protocol`                        |
| Unknown upstream source          | provenance boundary at `Accession`              |
| External source identifier known | `ExternalReference`                             |
| Image derived from tissue        | `Slide → Imaging → Image`                       |
| Segmentation derived from image  | `Image → Segmentation Activity → Mask`          |


