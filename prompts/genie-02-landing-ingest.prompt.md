# /genie-02-landing-ingest

**Purpose:** Generate one Auto Loader streaming notebook **per dataset** that ingests its CSV from the landing volume into a `landing.raw_<dataset>` Delta table. Schema-on-read; no transformations.

**Reads:** `genie_accelerator/metadata/datasets.yaml` → `datasets[*]`

---

## Prompt

```
You are generating Databricks Auto Loader ingestion notebooks.

INPUT: genie_accelerator/metadata/datasets.yaml
FOR EACH dataset in {{datasets}}:

  Generate notebook: notebooks/landing/01_landing_{{dataset.name}}.py

  Body:
    from pyspark.sql.functions import current_timestamp, lit, input_file_name, monotonically_increasing_id

    src  = "/Volumes/{{catalog}}/landing/raw_files/{{dataset.name}}/"
    tgt  = "{{catalog}}.landing.raw_{{dataset.name}}"
    chk  = "/Volumes/{{catalog}}/landing/raw_files/_checkpoints/raw_{{dataset.name}}"

    df = (spark.readStream
          .format("cloudFiles")
          .option("cloudFiles.format", "csv")
          .option("cloudFiles.schemaLocation", chk + "/schema")
          .option("header", "true")
          .option("inferSchema", "true")
          .load(src)
          .withColumn("__row_id__", monotonically_increasing_id())
          .withColumn("__ingest_ts__", current_timestamp())
          .withColumn("__source_file__", input_file_name())
          .withColumn("__dataset__", lit("{{dataset.name}}"))
         )

    (df.writeStream
       .option("checkpointLocation", chk)
       .option("mergeSchema", "true")
       .trigger(availableNow=True)
       .toTable(tgt))

CONSTRAINTS:
  - Use Auto Loader (cloudFiles), NOT spark.read.csv.
  - availableNow trigger so the notebook is rerunnable as a job.
  - Do NOT rename columns; bronze handles renames.
  - Always add the four metadata columns (__row_id__, __ingest_ts__, __source_file__, __dataset__).
  - One notebook per dataset; no shared code.
```

---

## Acceptance

For each dataset:
- `DESCRIBE TABLE EXTENDED kpi_testing.landing.raw_<dataset>` shows the four `__*__` columns.
- `SELECT COUNT(*)` matches the source CSV row count.
