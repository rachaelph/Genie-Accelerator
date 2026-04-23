-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 02 — Metadata Tables
-- MAGIC
-- MAGIC Provisions the four configuration metadata tables in `kpi_testing.metadata`,
-- MAGIC mirroring the schema of the parent ISD-Data-Accelerator so its batch engine
-- MAGIC and agent queries port over with minimal change. Idempotent — safe to re-run.
-- MAGIC
-- MAGIC Generated from `/genie-02-metadata-tables`. Requires `/genie-01-deploy-catalog`
-- MAGIC to have run first (creates the catalog + `metadata` schema).

-- COMMAND ----------
USE CATALOG kpi_testing;
USE SCHEMA metadata;

-- COMMAND ----------
-- MAGIC %md ## 1. Datastore_Configuration
-- MAGIC Per-environment registry of datastores (medallion layers + external sources).
-- MAGIC Keyed by `Datastore_Name`. `Connection_Details` is a JSON blob for non-Databricks kinds.

-- COMMAND ----------
CREATE TABLE IF NOT EXISTS Datastore_Configuration (
  Datastore_Name      STRING  NOT NULL  COMMENT 'Logical name (e.g. bronze, silver, gold, metadata, oracle_sales).',
  Datastore_Kind      STRING            COMMENT 'databricks | sql_server | oracle | postgre_sql | my_sql | db2 | rest_api | sftp | file',
  Medallion_Layer     STRING            COMMENT 'bronze | silver | gold | metadata | NULL for external sources.',
  Workspace_ID        STRING            COMMENT 'Databricks workspace numeric ID.',
  Workspace_URL       STRING            COMMENT 'https://adb-<id>.<region>.azuredatabricks.net',
  SQL_Warehouse_ID    STRING            COMMENT 'Default SQL warehouse for queries against this datastore.',
  Catalog_Name        STRING            COMMENT 'Unity Catalog name (Databricks datastores only).',
  Connection_Details  STRING            COMMENT 'JSON blob with kind-specific connection fields (host, secret scope, base URL, ...).'
)
USING DELTA
COMMENT 'Per-environment registry of datastores. Keyed by Datastore_Name.';

-- COMMAND ----------
-- MAGIC %md ## 2. Data_Pipeline_Metadata_Orchestration
-- MAGIC One row per `Table_ID`. Defines **what** to process, in **what order**, and **where** to write.
-- MAGIC `Table_ID` is the primary key linking to Primary/Advanced Configuration.

-- COMMAND ----------
CREATE TABLE IF NOT EXISTS Data_Pipeline_Metadata_Orchestration (
  Trigger_Name         STRING  NOT NULL  COMMENT 'Identifier for a set of data movements (data product / source system).',
  Order_Of_Operations  INT     NOT NULL  COMMENT 'Lower numbers run first. Equal numbers run in parallel.',
  Table_ID             BIGINT  NOT NULL  COMMENT 'Unique positive integer. Primary key across all triggers.',
  Target_Datastore     STRING  NOT NULL  COMMENT 'FK -> Datastore_Configuration.Datastore_Name.',
  Target_Entity        STRING  NOT NULL  COMMENT 'Bare table name, schema.table, or catalog.schema.table.',
  Primary_Keys         STRING            COMMENT 'Comma-separated list of PK columns (e.g. customer_id,order_id).',
  Processing_Method    STRING  NOT NULL  COMMENT 'batch | pipeline_stage_and_batch | pipeline_stage_only | execute_warehouse_sp | execute_databricks_notebook | execute_databricks_job',
  Ingestion_Active     INT     NOT NULL  COMMENT '0 = disabled, 1 = active.'
)
USING DELTA
COMMENT 'What/where/order for every data movement. Table_ID is the join key.';

-- COMMAND ----------
-- MAGIC %md ## 3. Data_Pipeline_Metadata_Primary_Configuration
-- MAGIC Single-value configs per `Table_ID`. Categories include `source_details`, `target_details`,
-- MAGIC `watermark_details`, `data_cleansing`, `performance_settings`.

-- COMMAND ----------
CREATE TABLE IF NOT EXISTS Data_Pipeline_Metadata_Primary_Configuration (
  Table_ID                BIGINT  NOT NULL  COMMENT 'FK -> Data_Pipeline_Metadata_Orchestration.Table_ID.',
  Configuration_Category  STRING  NOT NULL  COMMENT 'source_details | target_details | watermark_details | data_cleansing | performance_settings',
  Configuration_Name      STRING  NOT NULL  COMMENT 'Attribute key (e.g. table_name, merge_type, column_name).',
  Configuration_Value     STRING            COMMENT 'Attribute value as string (booleans use lowercase true/false).'
)
USING DELTA
COMMENT 'Single-value configs keyed by (Table_ID, Configuration_Category, Configuration_Name).';

-- COMMAND ----------
-- MAGIC %md ## 4. Data_Pipeline_Metadata_Advanced_Configuration
-- MAGIC Multi-attribute configs (transformations + data-quality rules) per `Table_ID`.
-- MAGIC `Configuration_Name_Instance_Number` groups attributes that belong to the same instance.

-- COMMAND ----------
CREATE TABLE IF NOT EXISTS Data_Pipeline_Metadata_Advanced_Configuration (
  Table_ID                            BIGINT  NOT NULL  COMMENT 'FK -> Data_Pipeline_Metadata_Orchestration.Table_ID.',
  Configuration_Category              STRING  NOT NULL  COMMENT 'data_transformation_steps | data_quality',
  Configuration_Name                  STRING  NOT NULL  COMMENT 'Step / rule name (e.g. derived_column, validate_condition, validate_not_null).',
  Configuration_Name_Instance_Number  INT     NOT NULL  COMMENT 'Groups attributes for one instance. Increment for each new step / rule on the same Table_ID.',
  Configuration_Attribute_Name        STRING  NOT NULL  COMMENT 'Attribute key (e.g. column_name, expression, condition, if_not_compliant, message).',
  Configuration_Attribute_Value       STRING            COMMENT 'Attribute value as string.'
)
USING DELTA
COMMENT 'Multi-attribute configs (transformations, DQ rules) per Table_ID.';

-- COMMAND ----------
-- MAGIC %md ## 5. Grants

-- COMMAND ----------
GRANT USE SCHEMA, SELECT ON SCHEMA kpi_testing.metadata TO `account users`;

-- COMMAND ----------
-- MAGIC %md ## 6. Verify

-- COMMAND ----------
SHOW TABLES IN kpi_testing.metadata;
