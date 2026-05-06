# Databricks notebook source
# MAGIC %md
# MAGIC # 03 — Landing: titanic
# MAGIC
# MAGIC Auto Loader streaming ingest of `titanic.csv` from the UC volume into
# MAGIC `kpi_testing.bronze.raw_titanic`. Schema-on-read, no transformations.
# MAGIC
# MAGIC Generated from `/genie-03-landing-ingest`. Trigger is `availableNow=True`
# MAGIC so the notebook is rerunnable as a job task.

# COMMAND ----------

from pyspark.sql.functions import current_timestamp, lit, input_file_name, monotonically_increasing_id

src = "/Volumes/kpi_testing/landing/raw_files/titanic/"
tgt = "kpi_testing.bronze.raw_titanic"
chk = "/Volumes/kpi_testing/landing/raw_files/_checkpoints/raw_titanic"

df = (
    spark.readStream
        .format("cloudFiles")
        .option("cloudFiles.format", "csv")
        .option("cloudFiles.schemaLocation", chk + "/schema")
        .option("header", "true")
        .option("inferSchema", "true")
        .load(src)
        .withColumn("__row_id__",      monotonically_increasing_id())
        .withColumn("__ingest_ts__",   current_timestamp())
        .withColumn("__source_file__", input_file_name())
        .withColumn("__dataset__",     lit("titanic"))
)

(
    df.writeStream
        .option("checkpointLocation", chk)
        .option("mergeSchema", "true")
        .trigger(availableNow=True)
        .toTable(tgt)
)

# COMMAND ----------

print(spark.table(tgt).count(), "rows in", tgt)
