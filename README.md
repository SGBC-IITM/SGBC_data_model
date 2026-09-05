# SGBC Data Model

Django-first provenance model for biospecimens, biosamples, activities, and
their versioned information records.

## Development

The project uses Django-managed models with MySQL. The Compose database is
named `sgbc_django`.

```bash
docker compose up -d --build
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Open the admin at <http://localhost:8000/admin/>.

Models are declared in `datamodel_demo/app1/models.py`; migrations are the
source of truth for the database schema. Do not use `inspectdb` or import the
legacy SQL files for this branch.

## Useful commands

```bash
docker compose exec web python manage.py makemigrations app1
docker compose exec web python manage.py migrate
docker compose exec web python manage.py check
```

The legacy conceptual DBML and SQL artifacts remain in the repository for
reference.
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

## Django demo project and app

<pre>
pip install django mysqlclient django-unfold

django-admin startproject datamodel_demo

cd datamodel_demo

python manage.py startapp app1
</pre>

## Django development environment

The demo Django project uses MySQL through Docker Compose. Start the database
and development server from the repository root:

```bash
docker compose up --build
```

The Django server is available at http://localhost:8000. Open the admin at
http://localhost:8000/admin/ and run management
commands in the web container, for example:

```bash
docker compose exec web python manage.py migrate
docker compose exec web python manage.py createsuperuser
```

Run Django management commands through `docker compose exec web` so the
Compose hostname `db` resolves correctly. If running them directly on the
host, use `python manage.py ...`; the settings default to `127.0.0.1`, which
uses the published MySQL port.

The Compose database service includes the MySQL client CLI. To instantiate the
schema and load the sample data, run these commands from the repository root,
in this order:

```bash
docker compose exec -T db mysql -usgbc -psgbc_dev_password sgbc < SGBC_data_model.sql
docker compose exec -T db mysql -usgbc -psgbc_dev_password sgbc < SGBC_sample_data.sql
```

You can connect interactively with:

```bash
docker compose exec db mysql -usgbc -psgbc_dev_password sgbc
```

Stop the services with `docker compose down`. The named `mysql_data` volume
keeps the database between restarts; use `docker compose down -v` to remove it.

### Generate Django models and admin

After creating the schema, regenerate the unmanaged Django models with:

```bash
./scripts/inspectdb.sh
```

The script reads the table names from `SGBC_data_model.sql`, runs `inspectdb`
inside the web container, writes `datamodel_demo/app1/models.py`, and runs
`manage.py check`. The models are automatically registered in Django admin.



