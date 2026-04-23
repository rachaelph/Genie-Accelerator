# /genie-07-genie-views

**Purpose:** Validate the gold KPI tables and expose them via Genie-consumption SQL views in `gold` (could equally live in a `business_metrics` schema). Every view and every column must carry a business-friendly `COMMENT` so the Genie agent can reason over them. Run after `/genie-06-gold-dlt`.

**Reads:** `genie_accelerator/metadata/datasets.yaml` → `genie_views`

---

## Prompt

```
You are generating SQL views optimized for a Databricks Genie agent.

INPUT: genie_accelerator/metadata/datasets.yaml
OUTPUT: notebooks/views/07_genie_views.sql

For EACH entry in {{genie_views}}:

  CREATE OR REPLACE VIEW {{catalog}}.gold.{{view.name}}
  COMMENT '{{view.description}}'
  AS
  SELECT
    <explicit column list from {{catalog}}.gold.{{view.base}}, no SELECT *>
  FROM {{catalog}}.gold.{{view.base}}
  ORDER BY <deterministic column>;

  THEN apply column comments by reading the base table's column metadata:
    ALTER VIEW ... ALTER COLUMN <col> COMMENT '<plain-English meaning>';

CONSTRAINTS:
  - NEVER use SELECT *.
  - EVERY column must have a COMMENT (Genie uses these as glossary).
  - Use business names ("avg_value" -> "Average Median Home Value (USD 100k)").
  - Add a VIEW-level COMMENT including 1-2 example questions a user might ask:
      'Average home value and income by lat/lon bin.
       Sample questions: "Which region has the highest average value?"
                         "How does income correlate with value by region?"'
  - Order results deterministically (ORDER BY the primary group_by column).
```

---

## Genie agent setup (manual, after views exist)

1. **Genie Space** → New → name: `kpi_testing_demo`.
2. **Tables** → add every `gold.vw_*` view.
3. **Instructions** → paste:
   > Use the views in `kpi_testing.gold.vw_*`. Always cite the view name in answers. If a question requires joining two views and no shared key exists, say so.
4. **Sample questions** → seed 2-3 per view (use the comments).

---

## Acceptance

- `SHOW VIEWS IN kpi_testing.gold LIKE 'vw_*'` returns one row per `genie_views` entry.
- `DESCRIBE TABLE EXTENDED kpi_testing.gold.<view>` shows non-null comments on every column.
- Genie space answers a sample question for each view without hallucinating columns.
