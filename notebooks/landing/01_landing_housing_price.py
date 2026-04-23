# Databricks notebook source
# DBTITLE 1,Landing: housing_price
# MAGIC %md
# MAGIC # 01 — Landing: housing_price
# MAGIC
# MAGIC Batch CSV ingestion to bronze Delta table.
# MAGIC `/Volumes/kpi_testing/landing/raw_files/housing_price.csv` → `kpi_testing.bronze.raw_housing_price`

# COMMAND ----------

# DBTITLE 1,Auto Loader ingestion
src = "/Volumes/kpi_testing/landing/raw_files/housing_price.csv"
tgt = "kpi_testing.bronze.raw_housing_price"

df = spark.read.csv(src, header=True, inferSchema=True)
df.write.mode("overwrite").saveAsTable(tgt)

print(f"Wrote {df.count()} rows to {tgt}")