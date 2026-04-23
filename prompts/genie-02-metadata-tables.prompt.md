# /genie-02-metadata-tables

**Purpose:** Provision the four configuration metadata tables in `kpi_testing.metadata`, mirroring the schema used by the parent ISD-Data-Accelerator so its batch engine and agent queries can be ported with minimal change. Run once per environment, after `/genie-01-deploy-catalog` and before `/genie-03-landing-ingest`.

**Reads:** `metadata/datasets.yaml` → `catalog`, `schemas.metadata`

---

## Tables created

All tables live in `{{catalog}}.metadata` as managed Delta tables.

| Table | Purpose | Grain |
|---|---|---|
| `Datastore_Configuration` | Workspace / catalog / SQL-warehouse registry per medallion layer + external sources. | one row per datastore |
| `Data_Pipeline_Metadata_Orchestration` | What to process, in what order, where to write. | one row per `Table_ID` |
| `Data_Pipeline_Metadata_Primary_Configuration` | Source / target / watermark / cleansing key-value config. | one row per (Table_ID, Configuration_Category, Configuration_Name) |
| `Data_Pipeline_Metadata_Advanced_Configuration` | Multi-attribute configs for `data_transformation_steps` and `data_quality`. | one row per (Table_ID, Category, Name, Instance, Attribute) |

Column names match the ISD parent **exactly** so SQL/notebooks port over.

---

## Prompt to Genie / Databricks Assistant

```
You are deploying the configuration metadata schema for a metadata-driven medallion lakehouse.

INPUT: metadata/datasets.yaml
ACTION: Generate ONE SQL notebook that:

  1. USE CATALOG kpi_testing; USE SCHEMA metadata;

  2. CREATE TABLE IF NOT EXISTS Datastore_Configuration (
       Datastore_Name      STRING NOT NULL,
       Datastore_Kind      STRING,            -- 'databricks' | 'sql_server' | 'oracle' | ...
       Medallion_Layer     STRING,            -- 'bronze' | 'silver' | 'gold' | 'metadata' | NULL
       Workspace_ID        STRING,
       Workspace_URL       STRING,
       SQL_Warehouse_ID    STRING,
       Catalog_Name        STRING,
       Connection_Details  STRING             -- JSON blob for non-databricks kinds
     ) USING DELTA
     COMMENT 'Per-environment registry of datastores. Keyed by Datastore_Name.';

  3. CREATE TABLE IF NOT EXISTS Data_Pipeline_Metadata_Orchestration (
       Trigger_Name         STRING NOT NULL,
       Order_Of_Operations  INT    NOT NULL,
       Table_ID             BIGINT NOT NULL,  -- unique across all triggers
       Target_Datastore     STRING NOT NULL,  -- FK -> Datastore_Configuration.Datastore_Name
       Target_Entity        STRING NOT NULL,  -- bare table name OR schema.table OR catalog.schema.table
       Primary_Keys         STRING,           -- comma-separated
       Processing_Method    STRING NOT NULL,  -- batch | pipeline_stage_and_batch | pipeline_stage_only | execute_*
       Ingestion_Active     INT    NOT NULL   -- 0 | 1
     ) USING DELTA
     COMMENT 'What/where/order. Table_ID is the primary key linking to Primary/Advanced Configuration.';

  4. CREATE TABLE IF NOT EXISTS Data_Pipeline_Metadata_Primary_Configuration (
       Table_ID                BIGINT NOT NULL,
       Configuration_Category  STRING NOT NULL,  -- source_details | target_details | watermark_details | data_cleansing | ...
       Configuration_Name      STRING NOT NULL,
       Configuration_Value     STRING
     ) USING DELTA
     COMMENT 'Single-value configs per Table_ID.';

  5. CREATE TABLE IF NOT EXISTS Data_Pipeline_Metadata_Advanced_Configuration (
       Table_ID                            BIGINT NOT NULL,
       Configuration_Category              STRING NOT NULL,  -- data_transformation_steps | data_quality
       Configuration_Name                  STRING NOT NULL,  -- e.g. validate_condition, derived_column
       Configuration_Name_Instance_Number  INT    NOT NULL,  -- groups attributes for one instance
       Configuration_Attribute_Name        STRING NOT NULL,
       Configuration_Attribute_Value       STRING
     ) USING DELTA
     COMMENT 'Multi-attribute configs (transformations, DQ rules) per Table_ID.';

  6. GRANT USE SCHEMA, SELECT ON SCHEMA kpi_testing.metadata TO `account users`;

CONSTRAINTS:
  - Idempotent (CREATE TABLE IF NOT EXISTS).
  - Column names MUST match the ISD-Data-Accelerator parent verbatim.
  - Output ONE .sql notebook named `02_metadata_tables.sql`.
```

---

## Acceptance

```sql
SHOW TABLES IN kpi_testing.metadata;
-- Returns: Datastore_Configuration,
--          Data_Pipeline_Metadata_Orchestration,
--          Data_Pipeline_Metadata_Primary_Configuration,
--          Data_Pipeline_Metadata_Advanced_Configuration
```

Then a one-row smoke test:
```sql
INSERT INTO kpi_testing.metadata.Datastore_Configuration
VALUES ('bronze','databricks','bronze',NULL,NULL,NULL,'kpi_testing',NULL);
SELECT * FROM kpi_testing.metadata.Datastore_Configuration;
DELETE FROM kpi_testing.metadata.Datastore_Configuration WHERE Datastore_Name='bronze';
```

---

## Out of scope (run-history tables)

`Data_Pipeline_Logs`, `Data_Quality_Notifications`, `Schema_Changes`, and `Activity_Logs` are **not** created here. They are populated by the ISD batch engine at runtime; add them only when porting the engine.
