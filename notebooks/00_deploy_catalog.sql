-- Databricks notebook source
-- MAGIC %md
-- MAGIC # 00 — Deploy Catalog
-- MAGIC
-- MAGIC Provisions the Unity Catalog catalog, schemas, and landing volume defined in
-- MAGIC `metadata/datasets.yaml`. Idempotent — safe to re-run.
-- MAGIC
-- MAGIC Generated from `/genie-01-deploy-catalog`.

-- COMMAND ----------
-- MAGIC %md ## 1. Catalog

-- COMMAND ----------
CREATE CATALOG IF NOT EXISTS kpi_testing
  COMMENT 'Genie accelerator demo catalog (sample CSV pipelines).';

-- COMMAND ----------
-- MAGIC %md ## 2. Schemas

-- COMMAND ----------
CREATE SCHEMA IF NOT EXISTS kpi_testing.landing
  COMMENT 'Raw files landed from source systems (volumes + raw tables).';

CREATE SCHEMA IF NOT EXISTS kpi_testing.bronze
  COMMENT 'Typed, parsed, append-only Delta tables. Minimal transformation.';

CREATE SCHEMA IF NOT EXISTS kpi_testing.silver
  COMMENT 'Cleansed, deduplicated, conformed business entities.';

CREATE SCHEMA IF NOT EXISTS kpi_testing.gold
  COMMENT 'Aggregated, KPI-ready tables for analytics and Genie consumption.';

CREATE SCHEMA IF NOT EXISTS kpi_testing.metadata
  COMMENT 'Pipeline metadata, run logs, expectations history, lineage.';

-- COMMAND ----------
-- MAGIC %md ## 3. Landing volume

-- COMMAND ----------
CREATE VOLUME IF NOT EXISTS kpi_testing.landing.raw_files
  COMMENT 'UC managed volume holding source CSVs.';

-- COMMAND ----------
-- MAGIC %md ## 4. Grants

-- COMMAND ----------
GRANT USE CATALOG ON CATALOG kpi_testing TO `account users`;
GRANT USE SCHEMA, SELECT ON SCHEMA kpi_testing.gold TO `account users`;
GRANT READ VOLUME ON VOLUME kpi_testing.landing.raw_files TO `account users`;

-- COMMAND ----------
-- MAGIC %md ## 5. Verify

-- COMMAND ----------
SHOW SCHEMAS IN kpi_testing;

-- COMMAND ----------
LIST '/Volumes/kpi_testing/landing/raw_files/';
