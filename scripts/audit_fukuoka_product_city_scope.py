#!/usr/bin/env python3
"""Conservatively classify Fukuoka-query products by actual city scope."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "supply_gap_analysis"
INVENTORY = ANALYSIS / "audit" / "fukuoka_product_detail_inventory.csv"
LINK_AUDIT = ANALYSIS / "audit" / "fukuoka_place_product_link_audit.csv"
REVERSE_AUDIT = ANALYSIS / "exports" / "fukuoka_mcp_reverse_hierarchy_audit.csv"
OUT = ANALYSIS / "audit" / "fukuoka_product_city_scope_audit.csv"
SUMMARY = ANALYSIS / "audit" / "fukuoka_product_city_scope_summary.json"

FIELDS = [
    "product_id",
    "category_value",
    "product_title",
    "product_url",
    "city_scope_status",
    "city_scope_reason",
]

# The 42 non-tour products were reviewed against their collected detail place
# fields. This list is explicit so a future product refresh fails visibly
# instead of silently reusing title heuristics.
LOCAL_NON_TOUR_IDS = {
    "5869302",
    "125248",
    "6083008",
    "5869396",
    "5869542",
    "5869541",
    "6178107",
    "6057583",
    "6059955",
    "5505188",
    "5051632",
    "5024120",
    "6057611",
}

OUTSIDE_OR_MULTI_REGION_NON_TOUR_IDS = {
    "6083075",
    "6082914",
    "6082913",
    "165385",
    "3426959",
    "6082985",
    "5869260",
    "5542787",
    "5542047",
    "5542788",
    "5542368",
    "3603442",
    "5542371",
    "4961308",
    "5024107",
    "6082930",
    "6176632",
    "6082962",
    "6176426",
    "6176629",
    "5542798",
    "6176597",
    "6176425",
    "4798134",
    "4652646",
    "4422036",
    "4843937",
    "6082928",
    "5542740",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def main() -> int:
    products = read_csv(INVENTORY)
    non_tours = {
        row["product_id"] for row in products if row["category_value"] != "tour"
    }
    reviewed_non_tours = LOCAL_NON_TOUR_IDS | OUTSIDE_OR_MULTI_REGION_NON_TOUR_IDS
    missing_review = sorted(non_tours - reviewed_non_tours)
    stale_review = sorted(reviewed_non_tours - non_tours)

    city_link_products = {
        row["product_id"]
        for row in read_csv(LINK_AUDIT)
        if row["audited_connection_class"] != "mention_only"
    }
    reverse_city_products: set[str] = set()
    if REVERSE_AUDIT.exists():
        for row in read_csv(REVERSE_AUDIT):
            if row.get("city_scope") != "후쿠오카시":
                continue
            reverse_city_products.update(
                product_id
                for product_id in row.get("mcp_product_ids", "").split("|")
                if product_id
            )

    rows_out: list[dict[str, str]] = []
    for product in products:
        product_id = product["product_id"]
        if product_id in LOCAL_NON_TOUR_IDS:
            status = "confirmed_fukuoka_city"
            reason = "비투어 상세 이용 장소·주소 또는 시설 정체를 수동 확인"
        elif product_id in OUTSIDE_OR_MULTI_REGION_NON_TOUR_IDS:
            status = "outside_or_multi_region"
            reason = "비투어 상세 주소·시설이 후쿠오카시 밖이거나 광역 패스"
        elif product_id in city_link_products or product_id in reverse_city_products:
            status = "confirmed_fukuoka_city_content"
            reason = "공식 장소 연결 또는 역방향 장소 계층 감사에서 후쿠오카시 콘텐츠 확인"
        else:
            status = "unresolved_tour_query_pool"
            reason = (
                "후쿠오카 출발·검색 노출과 후쿠오카시 방문을 동일시하지 않고 "
                "도시 범위 판정을 보류"
            )
        rows_out.append(
            {
                "product_id": product_id,
                "category_value": product["category_value"],
                "product_title": product["product_title"],
                "product_url": product["product_url"],
                "city_scope_status": status,
                "city_scope_reason": reason,
            }
        )
    OUT.parent.mkdir(parents=True, exist_ok=True)
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows_out)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "fukuoka_query_product_pool": len(products),
        "status_counts": dict(Counter(row["city_scope_status"] for row in rows_out)),
        "non_tour_products": len(non_tours),
        "non_tour_manual_review_complete": not missing_review and not stale_review,
        "missing_non_tour_review_ids": missing_review,
        "stale_non_tour_review_ids": stale_review,
        "interpretation": (
            "180 is a search-result audit pool, not a count of Fukuoka City supply. "
            "Unresolved tours are not counted as city-confirmed content."
        ),
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if not missing_review and not stale_review else 2


if __name__ == "__main__":
    raise SystemExit(main())
