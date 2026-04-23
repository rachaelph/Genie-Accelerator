"""Validate genie_accelerator/metadata/datasets.yaml.

Usage: python genie_accelerator/validate_metadata.py
Exits non-zero on any rule violation.
"""
from __future__ import annotations

import re
import sys
from pathlib import Path

try:
    import yaml  # type: ignore
except ImportError:
    sys.stderr.write("ERROR: PyYAML required. Install: pip install pyyaml\n")
    sys.exit(2)

META_PATH = Path(__file__).parent / "metadata" / "datasets.yaml"

REQUIRED_SCHEMAS = {"landing", "bronze", "silver", "gold", "metadata"}
ALLOWED_TYPES = {
    "STRING", "INT", "BIGINT", "DOUBLE", "FLOAT",
    "BOOLEAN", "DATE", "TIMESTAMP",
}
ALLOWED_SEVERITY = {"warn", "drop", "fail"}
RESERVED_COLS = {"__row_id__", "__ingest_ts__", "__source_file__", "__dataset__"}
IDENT_RE = re.compile(r"^[a-z][a-z0-9_]*$")


def main() -> int:
    if not META_PATH.exists():
        print(f"FAIL: metadata file not found: {META_PATH}")
        return 1

    with META_PATH.open("r", encoding="utf-8") as fh:
        meta = yaml.safe_load(fh)

    errors: list[str] = []

    # 1. catalog
    catalog = meta.get("catalog", "")
    if not IDENT_RE.match(catalog):
        errors.append(f"catalog '{catalog}' must be snake_case identifier")

    # 2. schemas
    schemas = set((meta.get("schemas") or {}).keys())
    missing = REQUIRED_SCHEMAS - schemas
    if missing:
        errors.append(f"missing required schemas: {sorted(missing)}")

    # 3. landing volume
    lv = meta.get("landing_volume") or {}
    if lv.get("schema") != "landing":
        errors.append("landing_volume.schema must be 'landing'")

    # datasets
    datasets = meta.get("datasets") or []
    by_name: dict[str, dict] = {}
    for ds in datasets:
        name = ds.get("name", "")
        if not IDENT_RE.match(name):
            errors.append(f"dataset name '{name}' must be snake_case")
        if name in by_name:
            errors.append(f"duplicate dataset name: {name}")
        by_name[name] = ds

    for name, ds in by_name.items():
        for key in ("source_file", "primary_key", "business_domain"):
            if not ds.get(key):
                errors.append(f"[{name}] missing required field: {key}")

        # 5. columns OR same_schema_as
        cols = ds.get("columns")
        sib = ds.get("same_schema_as")
        if not cols and not sib:
            errors.append(f"[{name}] must define either 'columns' or 'same_schema_as'")
        if sib and sib not in by_name:
            errors.append(f"[{name}] same_schema_as '{sib}' is not a known dataset")
        if sib and not by_name.get(sib, {}).get("columns"):
            errors.append(f"[{name}] same_schema_as target '{sib}' has no columns")

        # 6/7. column shape
        for col in cols or []:
            for k in ("name", "type", "source", "comment"):
                if k not in col:
                    errors.append(f"[{name}] column missing '{k}': {col}")
            if col.get("type") not in ALLOWED_TYPES:
                errors.append(f"[{name}] column '{col.get('name')}' bad type: {col.get('type')}")
            if col.get("name") in RESERVED_COLS:
                errors.append(f"[{name}] column '{col.get('name')}' uses reserved name")

        # 8/9. quality
        rule_names = set()
        for q in ds.get("quality") or []:
            if q.get("severity") not in ALLOWED_SEVERITY:
                errors.append(f"[{name}] quality rule '{q.get('rule')}' bad severity: {q.get('severity')}")
            if q.get("rule") in rule_names:
                errors.append(f"[{name}] duplicate quality rule name: {q.get('rule')}")
            rule_names.add(q.get("rule"))

        # 10. gold aggregate names
        for agg in ds.get("gold_aggregates") or []:
            if not (agg.get("name") or "").startswith("gold_"):
                errors.append(f"[{name}] gold_aggregate name must start with 'gold_': {agg.get('name')}")

    # 11. genie_views
    gold_table_names: set[str] = set()
    for ds in datasets:
        for agg in ds.get("gold_aggregates") or []:
            if agg.get("name"):
                gold_table_names.add(agg["name"])
    for x in meta.get("cross_dataset_gold") or []:
        if x.get("name"):
            gold_table_names.add(x["name"])

    for v in meta.get("genie_views") or []:
        if not (v.get("name") or "").startswith("vw_"):
            errors.append(f"genie_view name must start with 'vw_': {v.get('name')}")
        if v.get("base") not in gold_table_names:
            errors.append(f"genie_view '{v.get('name')}' base '{v.get('base')}' not a known gold table")

    # 12. cross-dataset sources
    silver_table_names = {f"silver_{ds['name']}" for ds in datasets if ds.get("name")}
    for x in meta.get("cross_dataset_gold") or []:
        for s in x.get("sources") or []:
            if s not in silver_table_names:
                errors.append(f"cross_dataset_gold '{x.get('name')}' source '{s}' not a known silver table")

    if errors:
        print("FAIL: metadata validation errors:")
        for e in errors:
            print(f"  - {e}")
        return 1

    print(f"OK: {META_PATH.name} — {len(datasets)} datasets, "
          f"{sum(len(ds.get('gold_aggregates') or []) for ds in datasets)} per-dataset gold tables, "
          f"{len(meta.get('cross_dataset_gold') or [])} cross-dataset gold tables, "
          f"{len(meta.get('genie_views') or [])} Genie views.")
    return 0


if __name__ == "__main__":
    sys.exit(main())
