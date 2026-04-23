# Databricks notebook source
# DBTITLE 1,Landing: london_taxi
# MAGIC %md
# MAGIC # 01 — Landing: london_taxi
# MAGIC
# MAGIC Batch CSV ingestion to bronze Delta table.
# MAGIC `/Volumes/kpi_testing/landing/raw_files/london_taxi.csv` → `kpi_testing.bronze.raw_london_taxi`

# COMMAND ----------

# DBTITLE 1,Ingest london_taxi CSV via Auto Loader
src = "/Volumes/kpi_testing/landing/raw_files/london_taxi.csv"
tgt = "kpi_testing.bronze.raw_london_taxi"

df = spark.read.csv(src, header=True, inferSchema=True)
df.write.mode("overwrite").saveAsTable(tgt)

print(f"Wrote {df.count()} rows to {tgt}")