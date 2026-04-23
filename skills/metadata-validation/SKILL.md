# SKILL: Genie Metadata Validation

Apply before delivering any change to `genie_accelerator/metadata/datasets.yaml` or before generating notebooks.

## Run
```powershell
python genie_accelerator/validate_metadata.py
```

## What it checks
1. `catalog` is a non-empty identifier (lowercase, snake_case).
2. Required schemas present: `landing`, `bronze`, `silver`, `gold`, `metadata`.
3. `landing_volume.schema == 'landing'`.
4. Each dataset has: `name`, `source_file`, `primary_key`, `business_domain`.
5. Either `columns` is present OR `same_schema_as` points to a sibling dataset that has `columns`.
6. Every `columns[*]` entry has `name`, `type`, `source`, `comment`.
7. Column `type` ∈ {STRING, INT, BIGINT, DOUBLE, FLOAT, BOOLEAN, DATE, TIMESTAMP}.
8. `quality[*].severity` ∈ {warn, drop, fail}.
9. Quality rule names are unique within a dataset.
10. Every `gold_aggregates[*].name` starts with `gold_`.
11. Every `genie_views[*].name` starts with `vw_` and `base` resolves to a known gold table.
12. `cross_dataset_gold[*].sources` reference existing silver tables (`silver_<dataset>`).
13. No duplicate dataset `name`.
14. No reserved column names (`__row_id__`, `__ingest_ts__`, `__source_file__`, `__dataset__`) used by user columns.

## On failure
Print every violation and exit non-zero. Do NOT generate notebooks until validator passes.
