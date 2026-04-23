# /genie-00-add-dataset

**Purpose:** Add a new dataset to `metadata/datasets.yaml` automatically, given only a CSV file (local path or volume path). Infers column types from a sample, generates a starter quality/silver_transforms/gold_aggregates block, appends it to the YAML, and re-runs the validator.

**Run before:** `/genie-03-landing-ingest` through `/genie-07-genie-views` (the downstream prompts then regenerate notebooks for the new dataset automatically).

**Reads:** The CSV file + `metadata/datasets.yaml`
**Writes:** Appends one `datasets:` block to `metadata/datasets.yaml`

---

## Inputs

| Name | Required | Example | Notes |
|---|---|---|---|
| `csv_path` | yes | `sample_data/orders.csv` OR `/Volumes/kpi_testing/landing/raw_files/orders/orders.csv` | Local path preferred for fast inference. |
| `dataset_name` | no | `orders` | Defaults to the CSV filename (snake_case, no extension). |
| `primary_key` | no | `order_id` | If omitted, try to auto-detect (first column that is unique + non-null). Else add a synthetic `<dataset>_id BIGINT` surrogate. |
| `business_domain` | no | `sales` | Free-text tag. |
| `description` | no | "Customer orders exported daily." | 1 sentence. |

---

## Prompt

```
You are adding a new dataset to metadata/datasets.yaml for the Genie Accelerator.

INPUT:
  - csv_path:         {{csv_path}}
  - dataset_name:     {{dataset_name | default: derived from csv_path}}
  - primary_key:      {{primary_key  | default: auto-detect}}
  - business_domain:  {{business_domain | default: "unspecified"}}
  - description:      {{description | default: "TODO: describe the dataset."}}

STEPS:

1. READ the CSV (first ~1000 rows) to infer:
   - header row -> source column names
   - type per column using this precedence (check all sampled non-null values):
       INT        if every value parses as a 32-bit signed integer
       BIGINT     if every value parses as a 64-bit signed integer
       DOUBLE     if every value parses as a float (and not covered above)
       BOOLEAN    if every value is in {true,false,0,1,yes,no}
       DATE       if every value parses as YYYY-MM-DD
       TIMESTAMP  if every value parses as ISO 8601 datetime
       STRING     otherwise

2. NORMALIZE column names to snake_case for the `name` field; keep the
   original header in the `source` field. Produce one `columns:` entry:
     - { name: <snake>, type: <INFERRED>, source: <ORIGINAL_HEADER>, comment: "TODO: describe." }

3. PRIMARY KEY resolution:
   - If `primary_key` was provided, use it (validate it exists in columns).
   - Else scan columns left-to-right for the first column that is unique and non-null across the sample; use that.
   - Else synthesize a surrogate: prepend a column
       { name: <dataset_name>_id, type: BIGINT, source: "__row_id__", comment: "Synthetic surrogate key." }
     and set primary_key: [<dataset_name>_id].

4. STARTER quality rules (emit at minimum these, skip if not applicable):
   - For every BIGINT/INT/DOUBLE PK column: { rule: pk_not_null, expr: "<pk> IS NOT NULL", severity: fail }
   - For every column named like *latitude*:  { rule: valid_<col>, expr: "<col> BETWEEN -90 AND 90",  severity: drop }
   - For every column named like *longitude*: { rule: valid_<col>, expr: "<col> BETWEEN -180 AND 180", severity: drop }
   - For every numeric column with "count" / "qty" / "amount" / "price" in the name:
       { rule: nonneg_<col>, expr: "<col> IS NULL OR <col> >= 0", severity: warn }

5. STARTER silver_transforms:
   - Add a placeholder:
       "TODO: add silver transforms (dedup by primary_key handled by /genie-05)."

6. STARTER gold_aggregates (one entry):
   - name: gold_<dataset_name>_summary
   - group_by:
       * if a DATE/TIMESTAMP column exists, use date_trunc('day', <ts>) AS day
       * else use the first STRING column AS <col>_bin
   - metrics:
       * COUNT(*) AS row_count
       * plus AVG(<col>) AS avg_<col> for up to 3 numeric columns

7. APPEND the new YAML block under the existing `datasets:` list in
   metadata/datasets.yaml. Preserve file ordering and indentation (2 spaces).
   Do NOT touch other datasets.

8. RUN validation:
     python validate_metadata.py
   Must print "OK: ...". If it fails, fix the emitted block and re-run once.

9. PRINT a short summary:
   - dataset name
   - column count
   - primary_key chosen (and whether synthesized)
   - suggested next command: `/genie-03-landing-ingest`

CONSTRAINTS:
  - Do NOT create the notebooks. The downstream /genie-03..07 prompts own that.
  - Do NOT modify catalog/schemas/landing_volume blocks.
  - Keep comments as "TODO: ..." placeholders so the user can edit before production use.
  - Emit valid YAML: quote strings that contain colons, commas, or # characters.
```

---

## Example invocation

```
/genie-00-add-dataset
csv_path: sample_data/orders.csv
dataset_name: orders
primary_key: order_id
business_domain: sales
description: "Customer orders exported daily from the OMS."
```

Expected outcome:
- `metadata/datasets.yaml` gains an `orders` block.
- `python validate_metadata.py` prints `OK: ...`.
- You then run `/genie-03-landing-ingest` through `/genie-07-genie-views` to materialize everything.

---

## Acceptance

- Diff on `metadata/datasets.yaml` shows ONLY a new block appended under `datasets:`.
- `validate_metadata.py` returns exit 0.
- `yq '.datasets[-1].name' metadata/datasets.yaml` prints the new dataset name.
