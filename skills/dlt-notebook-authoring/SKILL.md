# SKILL: DLT Notebook Authoring

Apply when generating any Lakeflow DLT notebook (Bronze, Silver, Gold).

## Naming
- Tables: `<layer>_<dataset>` (e.g. `bronze_titanic`, `silver_nyc_taxi`).
- Views: `vw_<purpose>_<dataset>` (e.g. `vw_raw_titanic`).
- File names: `0N_<layer>_dlt.py`.

## Streaming vs materialized
| Layer  | Mode               | Reason |
|--------|--------------------|--------|
| Bronze | streaming table    | Append-only landing source. |
| Silver | apply_changes (SCD1) + materialized view for derivations | Dedup + derive. |
| Gold   | materialized view  | Aggregates over full silver. |

## Expectation severity mapping
| Metadata `severity` | Decorator                          | Effect |
|---------------------|------------------------------------|--------|
| `warn`              | `@dlt.expect`                      | Records logged, kept. |
| `drop`              | `@dlt.expect_or_drop`              | Failing rows dropped. |
| `fail`              | `@dlt.expect_or_fail`              | Pipeline fails. |

Rule names: `snake_case`, unique per table.

## Required table_properties on every DLT table
```python
table_properties={
  "pipelines.layer": "<bronze|silver|gold>",
  "quality":         "<bronze|silver|gold>",
}
```
Also: `delta.enableChangeDataFeed=true` on bronze.

## Forbidden
- `spark.read.csv` / `spark.read.parquet` inside DLT — use `dlt.read*` or `spark.readStream.table`.
- Cross-pipeline references via 3-part names — use `LIVE.<table>`.
- Per-column COMMENTs inside `@dlt.table` — apply via `ALTER TABLE` post-step.
- Dynamic for-loops generating tables inside DLT — write one function per table.

## Required header on every DLT notebook
```python
# Databricks notebook source
# MAGIC %md
# MAGIC ## Layer: <bronze|silver|gold>
# MAGIC Generated from: genie_accelerator/metadata/datasets.yaml
import dlt
from pyspark.sql import functions as F
```
