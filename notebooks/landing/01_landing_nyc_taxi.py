# Databricks notebook source
# DBTITLE 1,Landing: nyc_taxi
# MAGIC %md
# MAGIC # 01 — Landing: nyc_taxi
# MAGIC
# MAGIC Batch CSV ingestion to bronze Delta table.
# MAGIC `/Volumes/kpi_testing/landing/raw_files/nyc_taxi.csv` → `kpi_testing.bronze.raw_nyc_taxi`

# COMMAND ----------

# DBTITLE 1,Ingest nyc_taxi CSV via Auto Loader
src = "/Volumes/kpi_testing/landing/raw_files/nyc_taxi.csv"
tgt = "kpi_testing.bronze.raw_nyc_taxi"

df = spark.read.csv(src, header=True, inferSchema=True)
df.write.mode("overwrite").saveAsTable(tgt)

print(f"Wrote {df.count()} rows to {tgt}")