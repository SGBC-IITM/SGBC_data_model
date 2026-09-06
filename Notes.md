## Comparison with ISA data model

| Your model                               | ISA model                             | Comment                                                                                             |
| ---------------------------------------- | ------------------------------------- | --------------------------------------------------------------------------------------------------- |
| `Entity`                                 | `Material` or `Data`                  | Your Entity is broader and more generic                                                             |
| `Activity`                               | `Process`                             | Very close conceptual match                                                                         |
| `ActivityEntity(direction=input/output)` | graph edges into/out of `Process`     | Essentially the same provenance structure                                                           |
| `EntityType`                             | `Material Type` / node subtype        | ISA distinguishes Source/Sample/Data more explicitly                                                |
| `ActivityType`                           | protocol/application type             | ISA Process is tied strongly to Protocol                                                            |
| Activity parameters                      | `Parameter Values`                    | Direct correspondence                                                                               |
| `Protocol`                               | `Protocol`                            | Direct correspondence                                                                               |
| `Agent` / operator                       | `Performer` / Contact                 | Similar, though your Agent abstraction is broader                                                   |
| `Vocabulary`                             | Ontology Annotation + Ontology Source | Same semantic-control role                                                                          |
| zero-input `Accession`                   | Process with zero inputs              | ISA explicitly permits Process nodes with zero or more inputs and outputs ([ISA Specifications][1]) |
| InformationRecord sidecar                | no strong direct ISA equivalent       | One of your main extensions                                                                         |

[1]: https://isa-specs.readthedocs.io/en/latest/isamodel.html "1. ISA Abstract Model — ISA Model and Serialization Specifications 1.0 documentation"


Investigation captures overall purpose/context; Study captures subjects, design, factors and treatments; Assay captures measurement/test workflows and technology.

I would consider borrowing this idea, but perhaps with a simpler abstraction:

<pre>
Project
   └── Study
        └── Experiment / Workflow
</pre>

<pre>
Study: Whole-brain ischemic stroke characterization

Workflow:
    histological processing

Activities:
    fixation
    slabbing
    sectioning
    staining
    imaging
</pre>

<pre>
Workflow:
    computational analysis

Activities:
    registration
    segmentation
    feature extraction
</pre>

The SGBC model's core provenance abstraction is strongly compatible with the ISA Process graph. SGBC generalizes ISA's Material/Process/Data pattern into Entity/Activity/Entity, adds explicit versioned Information Records, and separates domain-specific semantics into controlled vocabularies and materialized models.

You can potentially build an ISA import/export adapter:
<pre>
ISA Source/Material/Data
        ↕
      Entity

ISA Process
        ↕
     Activity

ISA Characteristics
        ↕
EntityInformationRecord

ISA ParameterValue
        ↕
ActivityInformationRecord.data

ISA OntologyAnnotation
        ↕
VocabularyTerm
</pre>

