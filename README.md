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
| 1. Deploy catalog | [genie-01-deploy-catalog](prompts/genie-01-deploy-catalog.prompt.md) | UC catalog `kpi_testing`, 5 schemas, landing volume |
| 2. Land CSVs      | [genie-02-landing-ingest](prompts/genie-02-landing-ingest.prompt.md) | Auto Loader notebook per dataset → `landing.raw_*` |
| 3. Bronze DLT     | [genie-03-bronze-dlt](prompts/genie-03-bronze-dlt.prompt.md)         | Typed + expectations → `bronze.bronze_*` |
| 4. Silver DLT     | [genie-04-silver-dlt](prompts/genie-04-silver-dlt.prompt.md)         | SCD1 dedup + transforms → `silver.silver_*` |
| 5. Gold DLT       | [genie-05-gold-dlt](prompts/genie-05-gold-dlt.prompt.md)             | Per-dataset + cross-dataset aggregates → `gold.gold_*` |
| 6. Genie views    | [genie-06-genie-views](prompts/genie-06-genie-views.prompt.md)       | Commented `gold.vw_*` views for the Genie space |
| 7. Metadata tables | [genie-07-metadata-tables](prompts/genie-07-metadata-tables.prompt.md) | 4 config tables in `metadata.*` mirroring the ISD parent (Datastore_Configuration + Orchestration / Primary / Advanced Configuration) |

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

# 3. Run /genie-01 .. /genie-06 in order, feeding each prompt to Copilot or Genie.
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
