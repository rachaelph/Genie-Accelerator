# Genie Accelerator (Databricks)

Metadata-driven scaffold mirroring the parent ISD Data Accelerator pattern, but targeting **Databricks Unity Catalog + Lakeflow DLT + Genie**.

## Layout

| Path | Purpose |
|---|---|
| [metadata/datasets.yaml](metadata/datasets.yaml) | Single source of truth: catalog, schemas, datasets, quality, transforms, gold, views. |
| [validate_metadata.py](validate_metadata.py) | Pre-flight validator. Run before generating notebooks. |
| [prompts/](prompts) | Six `/genie-*` prompts driving the lifecycle. |
| [skills/](skills) | Authoring rules for DLT and Genie views, plus validation rules. |

## Lifecycle

| Stage | Command | Output |
|---|---|---|
| 1. Deploy catalog   | [genie-01-deploy-catalog](prompts/genie-01-deploy-catalog.prompt.md)     | UC catalog `kpi_testing`, 5 schemas, landing volume |
| 2. Metadata tables  | [genie-02-metadata-tables](prompts/genie-02-metadata-tables.prompt.md)   | 4 config tables in `metadata.*` (Datastore + Orchestration / Primary / Advanced) |
| 3. Land CSVs        | [genie-03-landing-ingest](prompts/genie-03-landing-ingest.prompt.md)     | Auto Loader notebook per dataset → `bronze.raw_*` (raw data) |
| 4. Bronze DLT       | [genie-04-bronze-dlt](prompts/genie-04-bronze-dlt.prompt.md)             | Typed + expectations → `bronze.bronze_*` |
| 5. Silver DLT       | [genie-05-silver-dlt](prompts/genie-05-silver-dlt.prompt.md)             | SCD1 dedup + transforms → `silver.silver_*` (cleaned data) |
| 6. Gold DLT         | [genie-06-gold-dlt](prompts/genie-06-gold-dlt.prompt.md)                 | Per-dataset + cross-dataset KPI aggregates → `gold.gold_*` |
| 7. Genie views      | [genie-07-genie-views](prompts/genie-07-genie-views.prompt.md)           | Validation + commented `gold.vw_*` views for the Genie space |

## Datasets in scope (from `sample_data/`, excluding `apartments-train.csv`)

| Dataset | File | Domain |
|---|---|---|
| `housing_price` | `housing_price.csv` | real_estate |
| `titanic`       | `titanic.csv`       | historical |
| `nyc_taxi`      | `nyc_taxi.csv`      | transportation |
| `london_taxi`   | `london_taxi.csv`   | transportation (same schema as `nyc_taxi`) |

## Workflow

```powershell
# 1. Edit metadata
code genie_accelerator/metadata/datasets.yaml

# 2. Validate
python genie_accelerator/validate_metadata.py

# 3. Run /genie-01 .. /genie-07 in order, feeding each prompt to Copilot or Genie.
#    Each prompt READS the validated metadata and EMITS a single notebook.
```

## Why this mirrors the parent accelerator

| Parent (`/fdp-*`) | Genie equivalent (`/genie-*`) |
|---|---|
| Metadata SQL contract | `metadata/datasets.yaml` |
| `validate_metadata_sql.py` | `validate_metadata.py` |
| Skills under `.github/skills/` | `genie_accelerator/skills/` |
| Author → Convert → Deploy → Run → Investigate | Deploy → Land → Bronze → Silver → Gold → Views |
| Custom functions (`databricks_batch_engine/custom_functions/`) | `silver_transforms` block in YAML |
| Genie target = Fabric Warehouse + reports | Genie target = UC `gold.vw_*` + Genie space |

## Adding a new dataset

1. Drop `<file>.csv` into `/Volumes/kpi_testing/landing/raw_files/<dataset>/`.
2. Add a `datasets:` entry in `metadata/datasets.yaml`.
3. `python genie_accelerator/validate_metadata.py`
4. Re-run prompts 02 → 06.
