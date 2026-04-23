# /genie-04-bronze-dlt

**Purpose:** Generate a Lakeflow DLT notebook that reads each `bronze.raw_<dataset>` table (produced by `/genie-03-landing-ingest`), casts to typed columns per the metadata `columns` block, applies the metadata `quality` expectations, and writes `bronze.bronze_<dataset>`.

**Reads:** `genie_accelerator/metadata/datasets.yaml` → `datasets[*].columns`, `datasets[*].quality`

---

## Prompt

```
You are generating a Lakeflow Delta Live Tables (DLT) Bronze notebook.

INPUT: genie_accelerator/metadata/datasets.yaml
OUTPUT: One Python notebook: notebooks/bronze/04_bronze_dlt.py

For EACH dataset in {{datasets}} (resolve same_schema_as references first):

  1. Define a streaming view reading the raw bronze table:
       @dlt.view(name="vw_raw_{{dataset.name}}")
       def vw_raw_{{dataset.name}}():
           return spark.readStream.table("{{catalog}}.bronze.raw_{{dataset.name}}")

  2. Define the bronze streaming table with typed projection.
     Build the SELECT list from {{dataset.columns}}:
        CAST(`{{col.source}}` AS {{col.type}}) AS {{col.name}}
     Always carry through __ingest_ts__, __source_file__.

  3. Apply expectations from {{dataset.quality}}:
        severity=warn  -> @dlt.expect("{{rule.rule}}", "{{rule.expr}}")
        severity=drop  -> @dlt.expect_or_drop(...)
        severity=fail  -> @dlt.expect_or_fail(...)

  4. Decorator block:
       @dlt.table(
         name="bronze_{{dataset.name}}",
         comment="{{dataset.description}}",
         table_properties={
           "pipelines.layer": "bronze",
           "delta.enableChangeDataFeed": "true",
           "quality": "bronze"
         },
         partition_cols=[]      # add only if a natural date partition exists
       )

CONSTRAINTS:
  - Streaming tables only (append-only landing).
  - One function per dataset; do NOT loop dynamically inside DLT.
  - Use ONLY columns listed in metadata; ignore any extra source columns.
  - Comment every table with {{dataset.description}}.
  - Add COMMENT to every column via spark.sql ALTER TABLE in a separate post-step
    notebook (DLT does not support per-column comments natively yet).
```

---

## Acceptance

- DLT pipeline runs green; `event_log` shows `flow_progress` for every `bronze_*` table.
- `SELECT * FROM event_log(...) WHERE event_type='flow_progress'` shows 0 `failed_records` for `expect_or_fail` rules.
- Row counts: bronze ≤ raw bronze (drops applied).
