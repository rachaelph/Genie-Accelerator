# /genie-06-gold-dlt

**Purpose:** Generate the Gold (KPI) layer DLT notebook covering both **per-dataset** aggregates (`datasets[*].gold_aggregates`) and **cross-dataset** unions (`cross_dataset_gold`). Reads `silver.silver_<dataset>` produced by `/genie-05-silver-dlt`.

**Reads:** `genie_accelerator/metadata/datasets.yaml` → `datasets[*].gold_aggregates`, `cross_dataset_gold`

---

## Prompt

```
You are generating a Lakeflow DLT Gold notebook.

INPUT: genie_accelerator/metadata/datasets.yaml
OUTPUT: notebooks/gold/06_gold_dlt.py

PART A — Per-dataset gold tables
For EACH dataset and EACH entry in dataset.gold_aggregates:

  @dlt.table(
    name = "{{agg.name}}",
    comment = "Gold aggregate for {{dataset.name}} ({{agg.name}}).",
    table_properties = {"pipelines.layer":"gold","quality":"gold"}
  )
  def {{agg.name}}():
      return spark.sql(f\"\"\"
        SELECT {{ ", ".join(agg.group_by) }},
               {{ ", ".join(agg.metrics) }}
        FROM   LIVE.silver_{{dataset.name}}
        GROUP BY {{ ", ".join(agg.group_by) }}
      \"\"\")

PART B — Cross-dataset gold tables
For EACH entry in cross_dataset_gold:

  Build a UNION ALL from {{entry.sources}} selecting only
  {{entry.columns_from_silver}}, then GROUP BY {{entry.aggregates.group_by}}
  applying {{entry.aggregates.metrics}}.

  Same decorator pattern; comment="{{entry.description}}".

CONSTRAINTS:
  - All gold tables are MATERIALIZED VIEWS (no streaming aggregates here).
  - Names taken VERBATIM from metadata; do not pluralize or rename.
  - Every metric must include an explicit AS alias (already in metadata).
  - Add @dlt.expect("nonneg_count", "trip_count >= 0") on demand-style aggregates.
```

---

## Acceptance

- `gold.gold_*` tables exist for every metadata-declared aggregate.
- `gold.gold_global_taxi_demand` contains both `NYC` and `LONDON` `city_tag` values.
- All gold tables have a non-empty `comment` and `pipelines.layer='gold'` property.
