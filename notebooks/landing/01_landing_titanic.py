# Databricks notebook source
# DBTITLE 1,Landing: titanic
# MAGIC %md
# MAGIC # 01 — Landing: titanic
# MAGIC
# MAGIC Batch CSV ingestion to bronze Delta table.
# MAGIC `/Volumes/kpi_testing/landing/raw_files/titanic.csv` → `kpi_testing.bronze.raw_titanic`

# COMMAND ----------

# DBTITLE 1,Ingest titanic CSV via Auto Loader
src = "/Volumes/kpi_testing/landing/raw_files/titanic.csv"
tgt = "kpi_testing.bronze.raw_titanic"

df = spark.read.csv(src, header=True, inferSchema=True)
df.write.mode("overwrite").saveAsTable(tgt)

print(f"Wrote {df.count()} rows to {tgt}")