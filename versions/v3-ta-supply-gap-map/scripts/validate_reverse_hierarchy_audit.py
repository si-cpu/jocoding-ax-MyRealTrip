#!/usr/bin/env python3
"""Validate the reviewed MCP-to-official place hierarchy audit.

Hierarchy relations are a human-review gate, not a fuzzy-match output. This
validator makes the reviewed CSV reproducible by checking its schema, product
references, classifications, and evidence URLs against the collected MCP data.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
AUDIT = (
    ROOT
    / "data"
    / "supply_gap_analysis"
    / "exports"
    / "fukuoka_mcp_reverse_hierarchy_audit.csv"
)
PRODUCTS = (
    ROOT
    / "data"
    / "mcp_tna_products"
    / "processed"
    / "후쿠오카_mcp_tna_products.csv"
)
OUT = (
    ROOT
    / "data"
    / "supply_gap_analysis"
    / "reports"
    / "fukuoka_mcp_reverse_hierarchy_audit_summary.json"
)

REQUIRED_FIELDS = {
    "mcp_experience",
    "product_ids",
    "child_place",
    "parent_place",
    "parent_type",
    "official_scope",
    "official_reference",
    "match_level",
    "city_scope",
    "final_classification",
    "confidence",
    "note",
}
ALLOWED_CLASSIFICATIONS = {
    "official_raw_exact_and_nested",
    "official_other_catalog_and_nested",
    "mcp_private_content_in_official_district",
    "outside_fukuoka_city",
    "unresolved",
}
ALLOWED_CONFIDENCE = {"high", "medium", "low"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def main() -> int:
    errors: list[str] = []
    if not AUDIT.exists():
        errors.append(f"missing audit file: {AUDIT.relative_to(ROOT)}")
        rows: list[dict[str, str]] = []
    else:
        rows = read_csv(AUDIT)

    fields = set(rows[0]) if rows else set()
    missing_fields = sorted(REQUIRED_FIELDS - fields)
    if missing_fields:
        errors.append(f"missing fields: {', '.join(missing_fields)}")

    product_ids = {
        row["product_id"]
        for row in read_csv(PRODUCTS)
        if row.get("product_id")
    } if PRODUCTS.exists() else set()
    if not product_ids:
        errors.append("Fukuoka MCP product inventory is missing or empty")

    reviewed_product_ids: set[str] = set()
    for index, row in enumerate(rows, start=2):
        label = row.get("mcp_experience") or f"row {index}"
        classification = row.get("final_classification", "")
        confidence = row.get("confidence", "")
        if classification not in ALLOWED_CLASSIFICATIONS:
            errors.append(f"{label}: invalid classification {classification!r}")
        if confidence not in ALLOWED_CONFIDENCE:
            errors.append(f"{label}: invalid confidence {confidence!r}")
        if not row.get("official_reference", "").startswith("https://"):
            errors.append(f"{label}: official/evidence reference must be HTTPS")
        ids = [value.strip() for value in row.get("product_ids", "").split("|") if value.strip()]
        if not ids:
            errors.append(f"{label}: no product IDs")
        for product_id in ids:
            reviewed_product_ids.add(product_id)
            if product_id not in product_ids:
                errors.append(f"{label}: product {product_id} not found in Fukuoka MCP inventory")
        if classification == "outside_fukuoka_city" and row.get("city_scope") == "후쿠오카시":
            errors.append(f"{label}: outside-city row cannot use 후쿠오카시 city_scope")

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "status": "passed" if not errors else "failed",
        "reviewed_experiences": len(rows),
        "reviewed_product_ids": len(reviewed_product_ids),
        "classification_counts": dict(
            Counter(row.get("final_classification", "") for row in rows)
        ),
        "confidence_counts": dict(Counter(row.get("confidence", "") for row in rows)),
        "errors": errors,
        "audit_file": str(AUDIT.relative_to(ROOT)),
    }
    OUT.parent.mkdir(parents=True, exist_ok=True)
    OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
