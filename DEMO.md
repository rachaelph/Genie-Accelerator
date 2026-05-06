# Genie Accelerator — Demo Runbook

End-to-end smoke test + live demo script. Read this top-to-bottom before you
present.

---

## 0. Prerequisites (do these once, BEFORE the demo)

| # | Action | How to verify |
|---|---|---|
| 0.1 | Install the **new** Databricks CLI (the legacy Python `databricks` CLI does **not** support `bundle`). See <https://docs.databricks.com/dev-tools/cli/install.html>. | `databricks --version` shows `v0.2x.x` or newer |
| 0.2 | Authenticate to the workspace: `databricks auth login --host https://adb-7405606904496964.4.azuredatabricks.net` | `databricks current-user me` returns your user |
| 0.3 | Create or pick a **SQL warehouse** in the workspace. Note its ID. | Visible under SQL Warehouses; copy the ID (looks like `1234abcd5678efgh`) |
| 0.4 | Confirm **serverless DLT** is enabled in the workspace. If not, edit `databricks.yml` and replace `serverless: true` on each pipeline with a `clusters:` block (single-node Photon is fine). | Workspace admin settings → Compute → Serverless |
| 0.5 | Place the four CSVs (`housing_price.csv`, `titanic.csv`, `nyc_taxi.csv`, `london_taxi.csv`) in a single workspace folder. Default expected: `/Workspace/Shared/sample_data/`. Override via the `csv_source_dir` bundle variable if elsewhere. | Workspace UI shows all four files in one folder |
| 0.6 | `python validate_metadata.py` returns OK. | Already passing as of this writing |

---

## 1. Live-author the missing DLT notebooks (prompts 04–07)

These notebooks do not exist in the repo yet and are intentionally generated
live during the demo. Run each prompt in Copilot Chat against this workspace:

| Prompt | Generates |
|---|---|
| `/genie-04-bronze-dlt`  | `notebooks/bronze/04_bronze_dlt.py` |
| `/genie-05-silver-dlt`  | `notebooks/silver/05_silver_dlt.py` |
| `/genie-06-gold-dlt`    | `notebooks/gold/06_gold_dlt.py`     |
| `/genie-07-genie-views` | `notebooks/views/07_genie_views.sql` |

Each prompt reads `metadata/datasets.yaml` and emits exactly one notebook.
After each generation, re-run `python validate_metadata.py` (still OK) and
spot-check the generated file matches the spec in
[skills/dlt-notebook-authoring/SKILL.md](skills/dlt-notebook-authoring/SKILL.md)
and [skills/genie-view-authoring/SKILL.md](skills/genie-view-authoring/SKILL.md).

> **Test pass:** before the demo, run prompts 04–07 once yourself, commit the
> output, then delete it again so the live demo regenerates clean. Confirms the
> prompts still produce valid notebooks against the current YAML.

---

## 2. Deploy the bundle

```powershell
cd "c:\Users\rphillips\OneDrive - Microsoft\Repos\Genie-Accelerator"

# Variables required by the job tasks (SQL tasks need a warehouse).
$env:BUNDLE_VAR_sql_warehouse_id = "<paste-warehouse-id>"
$env:BUNDLE_VAR_csv_source_dir   = "/Workspace/Shared/sample_data"   # adjust if needed

databricks bundle validate -t dev
databricks bundle deploy   -t dev
```

What `deploy` does:
- Uploads all `notebooks/**` to `/Workspace/Users/<you>/.bundle/genie-accelerator/dev/files/notebooks/`
- Creates 3 DLT pipelines: `genie-dev-bronze`, `genie-dev-silver`, `genie-dev-gold`
- Creates 1 multi-task job: `genie-dev-e2e`

---

## 3. End-to-end test run (single command)

```powershell
databricks bundle run genie_demo_e2e -t dev
```

This runs the full DAG (deploy_catalog → upload_csvs → metadata_tables →
4 landing tasks → bronze DLT → silver DLT → gold DLT → genie_views).
Watch progress in the Workflows UI. Total wall-clock on serverless: ~10–15 min
the first time (DLT pipeline cold start), ~5 min subsequent runs.

### Acceptance checks (run in a SQL editor against the warehouse)

```sql
-- 3.1 catalog + schemas
SHOW SCHEMAS IN kpi_testing;
-- expect: bronze, gold, landing, metadata, silver

-- 3.2 landing volume populated
LIST '/Volumes/kpi_testing/landing/raw_files/';
-- expect: housing_price/, titanic/, nyc_taxi/, london_taxi/  (+ _checkpoints/)

-- 3.3 metadata config tables
SHOW TABLES IN kpi_testing.metadata;
-- expect 4 rows: Datastore_Configuration + 3x Data_Pipeline_Metadata_*

-- 3.4 raw bronze (Auto Loader output) row counts
SELECT '__counts__' AS marker,
       (SELECT COUNT(*) FROM kpi_testing.bronze.raw_housing_price) AS housing,
       (SELECT COUNT(*) FROM kpi_testing.bronze.raw_titanic)       AS titanic,
       (SELECT COUNT(*) FROM kpi_testing.bronze.raw_nyc_taxi)      AS nyc,
       (SELECT COUNT(*) FROM kpi_testing.bronze.raw_london_taxi)   AS london;
-- all four should match the source CSV row counts

-- 3.5 typed bronze (DLT bronze pipeline output)
SHOW TABLES IN kpi_testing.bronze LIKE 'bronze_*';
-- expect 4 tables; row count <= matching raw_* (drops applied)

-- 3.6 silver
SHOW TABLES IN kpi_testing.silver LIKE 'silver_*';
-- expect 4 tables with derived columns from silver_transforms

-- 3.7 gold (per-dataset + cross-dataset)
SHOW TABLES IN kpi_testing.gold LIKE 'gold_*';
-- expect 5: gold_housing_by_region, gold_titanic_survival_by_class_sex,
--           gold_nyc_taxi_demand_by_hour, gold_london_taxi_demand_by_hour,
--           gold_global_taxi_demand
SELECT DISTINCT city_tag FROM kpi_testing.gold.gold_global_taxi_demand;
-- expect: NYC, LONDON

-- 3.8 Genie views (ALL columns must have COMMENTs)
SHOW VIEWS IN kpi_testing.gold LIKE 'vw_*';
-- expect 4 rows
DESCRIBE TABLE EXTENDED kpi_testing.gold.vw_taxi_demand_heatmap;
-- every column row has a non-null comment
```

If any check fails, see **Troubleshooting** below.

---

## 4. Genie space (manual one-time setup)

1. Workspace → **Genie** → **New space** → name `kpi_testing_demo`.
2. **Tables** → add all 4 views from `kpi_testing.gold.vw_*`.
3. **Instructions:**
   > Use the views in `kpi_testing.gold.vw_*`. Always cite the view name in
   > answers. If a question requires joining two views and no shared key
   > exists, say so.
4. **Sample questions** (seed 2 per view from the view-level COMMENTs):
   - "Which region has the highest average home value?"
   - "How does income correlate with value by region?"
   - "What is the survival rate for women in 1st class vs 3rd class?"
   - "Which weekday-hour has the highest taxi demand in NYC?"
   - "How does London demand at 8am compare to NYC at 8am?"

---

## 5. The actual demo flow (recommended ~20 min script)

| Min | What you show | Why it matters |
|---|---|---|
| 0–2 | Open `metadata/datasets.yaml`. Highlight that this is the single source of truth. | Establishes the "metadata-driven" thesis. |
| 2–3 | Run `python validate_metadata.py` in the terminal. | Pre-flight gate; catches contract drift before any compute spins. |
| 3–6 | In Copilot Chat, run `/genie-04-bronze-dlt`. Show the generated `04_bronze_dlt.py` — typed columns + DLT expectations come directly from YAML. | Demonstrates the prompt-driven authoring loop. |
| 6–8 | Repeat briefly for `/genie-05`, `/genie-06`, `/genie-07`. | Whole medallion + Genie views generated in minutes. |
| 8–10 | `databricks bundle deploy -t dev`. Show the workspace tree fill in. | One command, infra-as-config. |
| 10–13 | `databricks bundle run genie_demo_e2e -t dev`. Switch to the Workflows UI; walk the DAG as it runs. | End-to-end automation. |
| 13–17 | Run the section 3 SQL acceptance checks. | Proof of correctness, not just green tasks. |
| 17–20 | Switch to the Genie space. Ask 2–3 sample questions. Show how it cites the `vw_*` views. | The payoff: business users get governed self-serve KPIs. |

---

## 6. Troubleshooting

| Symptom | Likely cause | Fix |
|---|---|---|
| `bundle validate` fails: `notebook path does not exist: notebooks/bronze/04_bronze_dlt.py` | Step 1 not done — DLT notebooks not generated yet. | Run prompts 04–07 first. |
| `upload_csvs` task: `FileNotFoundError` | Wrong `csv_source_dir` or filenames don't match. | Update `BUNDLE_VAR_csv_source_dir`, or rename the CSVs, or edit the `FILES` dict in [`notebooks/landing/00_upload_csvs_to_volume.py`](notebooks/landing/00_upload_csvs_to_volume.py). |
| `cloudFiles` schema-inference error | First Auto Loader run on a new path; checkpoint not yet written. | Re-run the landing task once. |
| DLT pipeline error: `cannot find table LIVE.bronze_<x>` in silver | Silver pipeline ran before bronze finished. | The `genie-dev-e2e` job already orders these; only happens if you trigger pipelines manually out of order. |
| Genie says "no rows" or "column not found" | View comments missing → Genie hallucinated. | Confirm `DESCRIBE TABLE EXTENDED gold.vw_*` shows comments on every column. Re-run `07_genie_views.sql` if not. |
| Serverless DLT not available in workspace | Workspace not enabled for serverless. | Edit `databricks.yml`: replace each pipeline's `serverless: true` with a `clusters:` block (single-node Photon, autoscale 1–2). |

---

## 7. Resetting between rehearsal runs

```sql
-- Idempotent teardown so you can re-rehearse from a clean state.
DROP CATALOG IF EXISTS kpi_testing CASCADE;
```

Then re-run from step 2 (`databricks bundle deploy`).
The four upload paths and DLT checkpoints will be recreated automatically.
