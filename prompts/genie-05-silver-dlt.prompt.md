# /genie-05-silver-dlt

**Purpose:** Generate a Lakeflow DLT notebook for the Silver layer that reads `bronze.bronze_<dataset>` (from `/genie-04-bronze-dlt`), deduplicates by `primary_key`, applies the metadata-defined `silver_transforms`, and writes `silver.silver_<dataset>` (cleaned data).

**Reads:** `genie_accelerator/metadata/datasets.yaml` → `datasets[*].primary_key`, `datasets[*].silver_transforms`

---

## Prompt

```
You are generating a Lakeflow DLT Silver notebook.

INPUT: genie_accelerator/metadata/datasets.yaml
OUTPUT: notebooks/silver/05_silver_dlt.py

For EACH dataset:

  1. Read bronze as stream:
       @dlt.view
       def vw_bronze_{{dataset.name}}():
           return spark.readStream.table("LIVE.bronze_{{dataset.name}}")

  2. Deduplicate by {{dataset.primary_key}} keeping latest by __ingest_ts__:
       Use dlt.apply_changes() with:
         keys = {{dataset.primary_key}}
         sequence_by = "__ingest_ts__"
         stored_as_scd_type = 1
       Target: silver_{{dataset.name}}_dedup (intermediate)

  3. Build silver_{{dataset.name}} as a materialized view that applies
     each rule in {{dataset.silver_transforms}} verbatim. Each transform
     listed in metadata becomes one explicit .withColumn(...) or SQL CASE.

  4. Add table-level comment:
       comment = "Silver: cleansed + business-derived columns for {{dataset.name}}"
     Properties:
       pipelines.layer = silver, quality = silver

CONSTRAINTS:
  - Use dlt.apply_changes for SCD1 dedup — do NOT roll your own MERGE.
  - Every silver_transform line in the YAML MUST appear as a derived column;
    if a transform is ambiguous, add a TODO comment but still emit the column.
  - Preserve __ingest_ts__ and __source_file__ columns into silver.
  - For datasets with `same_schema_as`, reuse the resolved column list.
```

---

## Acceptance

- `silver.silver_<dataset>` exists for every dataset.
- Row count silver_<dataset> ≤ bronze_<dataset> (dedup applied).
- All derived columns from `silver_transforms` exist (`DESCRIBE TABLE`).
