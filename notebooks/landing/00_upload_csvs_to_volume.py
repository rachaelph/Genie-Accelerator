# Databricks notebook source
# MAGIC %md
# MAGIC # 00 — Upload sample CSVs into the landing volume
# MAGIC
# MAGIC Copies the four source CSVs from a workspace folder into per-dataset
# MAGIC subfolders under `/Volumes/kpi_testing/landing/raw_files/`, which is
# MAGIC where the `03_landing_*.py` Auto Loader notebooks read from.
# MAGIC
# MAGIC **Default `source_dir`:** `/Workspace/Shared/sample_data`.
# MAGIC Override with the `source_dir` widget or job parameter if your CSVs
# MAGIC live elsewhere (workspace files, DBFS, another volume, ...).
# MAGIC
# MAGIC Idempotent — safe to re-run; existing files are overwritten.

# COMMAND ----------

dbutils.widgets.text("source_dir", "/Workspace/Shared/sample_data",
                     "Folder containing the 4 source CSVs")
SRC_DIR  = dbutils.widgets.get("source_dir").rstrip("/")
DEST_VOL = "/Volumes/kpi_testing/landing/raw_files"

# dataset_name -> source filename (rename here if your CSVs use different names)
FILES = {
    "housing_price": "housing_price.csv",
    "titanic":       "titanic.csv",
    "nyc_taxi":      "nyc_taxi.csv",
    "london_taxi":   "london_taxi.csv",
}

# COMMAND ----------

import os

def _src_uri(path: str) -> str:
    # /Workspace/... and /Volumes/... are readable directly by dbutils.fs.cp
    # without a scheme; local FS paths need the file: scheme.
    if path.startswith(("/Workspace/", "/Volumes/", "dbfs:/", "abfss:", "s3:", "gs:")):
        return path
    return "file:" + path

missing = []
for dataset, fname in FILES.items():
    src  = f"{SRC_DIR}/{fname}"
    dest_dir  = f"{DEST_VOL}/{dataset}"
    dest_file = f"{dest_dir}/{fname}"

    try:
        dbutils.fs.ls(_src_uri(src))
    except Exception:
        missing.append(src)
        continue

    dbutils.fs.mkdirs(dest_dir)
    dbutils.fs.cp(_src_uri(src), dest_file, recurse=False)
    print(f"OK  {src}  ->  {dest_file}")

if missing:
    raise FileNotFoundError(
        "These source files were not found. Update `source_dir` or rename them:\n  - "
        + "\n  - ".join(missing)
    )

# COMMAND ----------

display(dbutils.fs.ls(DEST_VOL))
