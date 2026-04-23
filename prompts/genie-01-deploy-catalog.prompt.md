# /genie-01-deploy-catalog

**Purpose:** Provision the Unity Catalog catalog, schemas, and landing volume defined in `metadata/datasets.yaml`. Run once per environment.

**Reads:** `genie_accelerator/metadata/datasets.yaml` → `catalog`, `schemas`, `landing_volume`

---

## Prompt to Genie / Databricks Assistant

```
You are deploying a metadata-driven medallion lakehouse.

INPUT: genie_accelerator/metadata/datasets.yaml
ACTION: Generate a single SQL notebook that:

  1. CREATE CATALOG IF NOT EXISTS {{catalog}}
       COMMENT 'Genie accelerator demo catalog (sample CSV pipelines).';

  2. For each entry in {{schemas}}:
       CREATE SCHEMA IF NOT EXISTS {{catalog}}.{{schema}}
         COMMENT '{{schemas[*].comment}}';

  3. CREATE VOLUME IF NOT EXISTS {{catalog}}.{{landing_volume.schema}}.{{landing_volume.name}}
       COMMENT '{{landing_volume.comment}}';

  4. GRANT USE CATALOG ON CATALOG {{catalog}} TO `account users`;
     GRANT USE SCHEMA, SELECT ON SCHEMA {{catalog}}.gold TO `account users`;
     GRANT READ VOLUME ON VOLUME {{catalog}}.landing.raw_files TO `account users`;

CONSTRAINTS:
  - Idempotent (use IF NOT EXISTS everywhere).
  - Add COMMENT clauses on every catalog/schema/volume.
  - Do NOT create tables in this notebook — that is /genie-02..05.
  - Output ONE .sql notebook named `00_deploy_catalog.sql`.
```

---

## Post-deploy manual step

Upload these files from `sample_data/` to the volume `/Volumes/kpi_testing/landing/raw_files/`:

| Local file | Volume path |
|---|---|
| `sample_data/housing_price.csv` | `/Volumes/kpi_testing/landing/raw_files/housing_price/housing_price.csv` |
| `sample_data/titanic.csv`       | `/Volumes/kpi_testing/landing/raw_files/titanic/titanic.csv` |
| `sample_data/nyc_taxi.csv`      | `/Volumes/kpi_testing/landing/raw_files/nyc_taxi/nyc_taxi.csv` |
| `sample_data/london_taxi.csv`   | `/Volumes/kpi_testing/landing/raw_files/london_taxi/london_taxi.csv` |

> `apartments-train.csv` is intentionally excluded.

---

## Acceptance

- `SHOW SCHEMAS IN kpi_testing` returns: bronze, gold, landing, metadata, silver.
- `LIST '/Volumes/kpi_testing/landing/raw_files/'` returns 4 dataset folders.
