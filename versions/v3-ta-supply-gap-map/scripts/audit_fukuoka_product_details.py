#!/usr/bin/env python3
"""Build a complete, resumable detail inventory for Fukuoka MCP products.

The existing tour collector intentionally covers only tour products. This audit
adds ticket/activity/class details without changing the production tour files,
and records exactly which of the 180 deduplicated products have usable detail.
"""

from __future__ import annotations

import argparse
import csv
import json
import time
from collections import Counter
from datetime import datetime
from pathlib import Path

from collect_city_tour_details import collect_one, promote_product_description
from enrich_tour_detail_evidence import parse_detail_payload, sections_from_detail


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = (
    ROOT
    / "data"
    / "mcp_tna_products"
    / "processed"
    / "후쿠오카_mcp_tna_products.csv"
)
TOUR_RAW = ROOT / "data" / "supply_gap_analysis" / "tour_details" / "raw"
AUDIT_DIR = ROOT / "data" / "supply_gap_analysis" / "audit"
RAW_DIR = AUDIT_DIR / "fukuoka_product_details" / "raw"
INVENTORY_OUT = AUDIT_DIR / "fukuoka_product_detail_inventory.csv"
SECTIONS_OUT = AUDIT_DIR / "fukuoka_product_detail_sections.csv"
SUMMARY_OUT = AUDIT_DIR / "fukuoka_product_detail_inventory_summary.json"

INVENTORY_FIELDS = [
    "product_id",
    "category_name",
    "category_value",
    "product_title",
    "product_url",
    "search_city_match_status",
    "detail_status",
    "detail_cache_source",
    "section_count",
    "positive_section_count",
    "negative_section_count",
    "neutral_section_count",
]
SECTION_FIELDS = [
    "product_id",
    "category_name",
    "category_value",
    "product_title",
    "product_url",
    "section_type",
    "section_label",
    "section_text",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--retry-wait", type=float, default=45.0)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def deduplicated_products() -> list[dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for row in read_csv(PRODUCTS):
        product_id = row.get("product_id", "")
        if product_id and product_id not in by_id:
            by_id[product_id] = {
                "product_id": product_id,
                "category_name": row["category_name"],
                "category_value": row["category_value"],
                "product_title": row["title"],
                "product_url": row["url"],
                "search_city_match_status": row["city_match_status"],
            }
    return list(by_id.values())


def raw_path_for(product: dict[str, str]) -> tuple[Path, str]:
    product_id = product["product_id"]
    tour_path = TOUR_RAW / f"{product_id}.json"
    if tour_path.exists():
        return tour_path, "tour_detail_cache"
    return RAW_DIR / f"{product_id}.json", "audit_detail_cache"


def collect_missing(
    products: list[dict[str, str]],
    retry_wait: float,
    max_retries: int,
    delay: float,
) -> dict[str, str]:
    statuses: dict[str, str] = {}
    missing = [product for product in products if not raw_path_for(product)[0].exists()]
    for index, product in enumerate(missing, start=1):
        # collect_one writes to collect_city_tour_details.RAW_DIR. Temporarily
        # point that module-level directory at the audit cache.
        import collect_city_tour_details as collector

        original = collector.RAW_DIR
        collector.RAW_DIR = RAW_DIR
        try:
            raw, status, used_cache = collect_one(
                product,
                retry_wait=retry_wait,
                max_retries=max_retries,
            )
        finally:
            collector.RAW_DIR = original
        statuses[product["product_id"]] = status
        print(
            json.dumps(
                {
                    "event": "fukuoka_detail_audit_progress",
                    "completed": index,
                    "missing_total": len(missing),
                    "product_id": product["product_id"],
                    "status": status,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if raw is not None and not used_cache and index < len(missing):
            time.sleep(delay)
    return statuses


def build_outputs(
    products: list[dict[str, str]],
    collected_statuses: dict[str, str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    inventory: list[dict[str, str]] = []
    section_rows: list[dict[str, str]] = []
    for product in products:
        raw_path, cache_source = raw_path_for(product)
        sections: list[tuple[str, str, str]] = []
        detail_status = collected_statuses.get(product["product_id"], "not_collected")
        if raw_path.exists():
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            sections = [
                promote_product_description(*section)
                for section in sections_from_detail(parse_detail_payload(raw))
            ]
            if detail_status == "not_collected":
                detail_status = "ok_cached"
        counts = Counter(section_type for section_type, _, _ in sections)
        inventory.append(
            {
                **product,
                "detail_status": detail_status,
                "detail_cache_source": cache_source if raw_path.exists() else "",
                "section_count": str(len(sections)),
                "positive_section_count": str(counts["positive"]),
                "negative_section_count": str(counts["negative"]),
                "neutral_section_count": str(counts["neutral"]),
            }
        )
        for section_type, label, text in sections:
            section_rows.append(
                {
                    "product_id": product["product_id"],
                    "category_name": product["category_name"],
                    "category_value": product["category_value"],
                    "product_title": product["product_title"],
                    "product_url": product["product_url"],
                    "section_type": section_type,
                    "section_label": label,
                    "section_text": text,
                }
            )
    return inventory, section_rows


def main() -> int:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    products = deduplicated_products()
    if args.limit:
        products = products[: args.limit]
    statuses = collect_missing(
        products,
        retry_wait=args.retry_wait,
        max_retries=args.max_retries,
        delay=args.delay,
    )
    inventory, sections = build_outputs(products, statuses)
    write_csv(INVENTORY_OUT, INVENTORY_FIELDS, inventory)
    write_csv(SECTIONS_OUT, SECTION_FIELDS, sections)
    usable = sum(int(row["section_count"]) > 0 for row in inventory)
    missing = sum(not row["detail_cache_source"] for row in inventory)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "deduplicated_fukuoka_products": len(products),
        "products_with_cached_payload": len(products) - missing,
        "products_with_usable_sections": usable,
        "products_without_cached_payload": missing,
        "category_counts": dict(Counter(row["category_value"] for row in inventory)),
        "detail_status_counts": dict(Counter(row["detail_status"] for row in inventory)),
        "section_rows": len(sections),
    }
    SUMMARY_OUT.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if missing == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
