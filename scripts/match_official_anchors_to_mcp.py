#!/usr/bin/env python3
"""Match official experience anchors against collected MCP T&A products."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANCHORS = ROOT / "data" / "official_tourism_sources" / "anchors" / "official_experience_anchors.csv"
PRODUCTS = ROOT / "data" / "mcp_tna_products" / "processed" / "mcp_tna_products.csv"
OUT = ROOT / "data" / "supply_gap_analysis"
REPORTS = OUT / "reports"

MATCH_FIELDS = [
    "anchor_id",
    "city_id",
    "city_name",
    "anchor_name",
    "anchor_type",
    "official_source_type",
    "product_id",
    "product_title",
    "product_url",
    "product_category",
    "product_category_value",
    "match_type",
    "match_score",
    "evidence_level",
    "evidence_policy",
    "evidence_text",
]

SCORE_FIELDS = [
    "anchor_id",
    "city_id",
    "city_name",
    "anchor_name",
    "anchor_type",
    "official_source_type",
    "official_strength",
    "mcp_supply_strength",
    "mcp_product_count",
    "gap_score",
    "classification",
    "reason",
    "top_product_titles",
]

PRIMARY_SCORE_FIELDS = SCORE_FIELDS + ["analysis_scope"]
PARTNER_CANDIDATE_FIELDS = [
    "anchor_id",
    "city_id",
    "city_name",
    "anchor_name",
    "anchor_name_local",
    "anchor_name_en",
    "anchor_type",
    "official_source_type",
    "source_url",
    "address",
    "lat",
    "lng",
    "partner_candidate_reason",
]

OFFICIAL_ALIAS_MAP = {
    "広島城": ["히로시마성", "히로시마 성", "Hiroshima Castle"],
    "広島平和記念資料館": [
        "평화기념관",
        "평화 기념관",
        "평화기념자료관",
        "히로시마 평화기념관",
        "Hiroshima Peace Memorial Museum",
    ],
    "おりづるタワー": ["오리즈루 타워", "오리즈루타워", "Orizuru Tower"],
}


def is_partner_candidate_only(anchor: dict[str, str]) -> bool:
    return anchor.get("official_source_type") in {"official_yatai", "official_yatai_cluster"} or anchor.get(
        "anchor_type"
    ) in {"food_place", "place_cluster"}


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize(text: str | None) -> str:
    return re.sub(r"[^0-9a-z가-힣ぁ-んァ-ン一-龥]+", "", clean(text).casefold())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def city_to_query(city_id: str) -> str:
    if city_id == "jp-fukuoka":
        return "후쿠오카"
    if city_id == "jp-hiroshima":
        return "히로시마"
    return city_id


def alias_candidates(anchor: dict[str, str]) -> list[str]:
    values = [
        anchor.get("anchor_name"),
        anchor.get("anchor_name_local"),
        anchor.get("anchor_name_en"),
    ]
    values.extend(OFFICIAL_ALIAS_MAP.get(clean(anchor.get("anchor_name")), []))
    # Category-level aliases only for the aggregate yatai inventory.
    if anchor.get("official_source_type") == "official_yatai_cluster":
        values.extend(["야타이", "yatai", "포장마차", "나카스 포장마차", "후쿠오카 야타이"])
    return [v for v in dict.fromkeys(clean(v) for v in values) if v]


def match_score(anchor: dict[str, str], product: dict[str, str]) -> tuple[float, str, str]:
    title = clean(product.get("title"))
    raw = clean(product.get("raw_text"))
    haystack = normalize(f"{title} {raw}")
    title_norm = normalize(title)

    for alias in alias_candidates(anchor):
        alias_norm = normalize(alias)
        if not alias_norm or len(alias_norm) < 2:
            continue
        if alias_norm in title_norm:
            return 1.0, "title_alias", alias
        if alias_norm in haystack:
            return 0.75, "raw_text_alias", alias
    return 0.0, "", ""


def evidence_policy(product: dict[str, str], match_type: str) -> tuple[str, str]:
    category = clean(product.get("category_value"))
    title = clean(product.get("title"))
    if category in {"ticket", "ticket_v2"}:
        return (
            "ticket_product_confirmed",
            "입장권은 상품 자체가 해당 시설 이용권이므로 제목/상품명 매칭을 강한 근거로 본다.",
        )
    if category in {"tour", "suburb_tour", "sinae_tour", "cruise_tour"} or "투어" in title:
        return (
            "tour_title_needs_detail",
            "투어 상품은 제목 매칭만으로 방문 확정하지 않고, 상세 일정/포함사항의 긍정 근거 확인이 필요하다.",
        )
    return (
        "product_card_match",
        "현재는 상품 카드/제목 기준 매칭이며, 카테고리별 상세 근거 정책 추가 확인이 필요하다.",
    )


def classify(product_count: int, official_source_type: str) -> tuple[str, str, float, float, float]:
    official_strength = 1.0
    if official_source_type == "official_event":
        official_strength = 0.75
    if product_count >= 3:
        supply = 1.0
    elif product_count == 2:
        supply = 0.7
    elif product_count == 1:
        supply = 0.45
    else:
        supply = 0.0
    gap = round(max(official_strength - supply, 0), 2)
    if product_count >= 3:
        return "검증된 대표 경험", "official asset has multiple MCP-linked products", official_strength, supply, gap
    if product_count >= 1:
        return "부분 상품화 자산", "official asset has at least one MCP-linked product", official_strength, supply, gap
    return "상품화 부족 자산", "official asset has no direct MCP product match in collected sample", official_strength, supply, gap


def main() -> int:
    anchors = read_csv(ANCHORS)
    products = read_csv(PRODUCTS) if PRODUCTS.exists() else []
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    matches = []
    matched_by_anchor: dict[str, list[dict[str, str]]] = defaultdict(list)
    primary_anchors = [anchor for anchor in anchors if not is_partner_candidate_only(anchor)]
    partner_candidate_anchors = [anchor for anchor in anchors if is_partner_candidate_only(anchor)]
    for anchor in primary_anchors:
        city_query = city_to_query(anchor["city_id"])
        city_products = [p for p in products if p.get("city_query") == city_query]
        for product in city_products:
            score, mtype, evidence = match_score(anchor, product)
            if score <= 0:
                continue
            evidence_level, policy = evidence_policy(product, mtype)
            match = {
                "anchor_id": anchor["anchor_id"],
                "city_id": anchor["city_id"],
                "city_name": anchor["city_name"],
                "anchor_name": anchor["anchor_name"],
                "anchor_type": anchor["anchor_type"],
                "official_source_type": anchor["official_source_type"],
                "product_id": product.get("product_id", ""),
                "product_title": product.get("title", ""),
                "product_url": product.get("url", ""),
                "product_category": product.get("category_name", ""),
                "product_category_value": product.get("category_value", ""),
                "match_type": mtype,
                "match_score": str(score),
                "evidence_level": evidence_level,
                "evidence_policy": policy,
                "evidence_text": evidence,
            }
            matches.append(match)
            matched_by_anchor[anchor["anchor_id"]].append(match)

    scores = []
    for anchor in anchors:
        if is_partner_candidate_only(anchor):
            continue
        anchor_matches = matched_by_anchor.get(anchor["anchor_id"], [])
        unique_products = {}
        for match in anchor_matches:
            unique_products[match["product_url"] or match["product_title"]] = match
        product_count = len(unique_products)
        classification, reason, official_strength, supply, gap = classify(
            product_count, anchor["official_source_type"]
        )
        titles = " | ".join(m["product_title"] for m in list(unique_products.values())[:5])
        scores.append(
            {
                "anchor_id": anchor["anchor_id"],
                "city_id": anchor["city_id"],
                "city_name": anchor["city_name"],
                "anchor_name": anchor["anchor_name"],
                "anchor_type": anchor["anchor_type"],
                "official_source_type": anchor["official_source_type"],
                "official_strength": str(official_strength),
                "mcp_supply_strength": str(supply),
                "mcp_product_count": str(product_count),
                "gap_score": str(gap),
                "classification": classification,
                "reason": reason,
                "top_product_titles": titles,
            }
        )
    primary_scores = [{**row, "analysis_scope": "primary_tourism_asset"} for row in scores]
    partner_candidates = [
        {
            "anchor_id": anchor["anchor_id"],
            "city_id": anchor["city_id"],
            "city_name": anchor["city_name"],
            "anchor_name": anchor["anchor_name"],
            "anchor_name_local": anchor["anchor_name_local"],
            "anchor_name_en": anchor["anchor_name_en"],
            "anchor_type": anchor["anchor_type"],
            "official_source_type": anchor["official_source_type"],
            "source_url": anchor["source_url"],
            "address": anchor["address"],
            "lat": anchor["lat"],
            "lng": anchor["lng"],
            "partner_candidate_reason": "food/yatai asset; excluded from first-pass tourism-spot analysis and retained for later food/partner analysis",
        }
        for anchor in partner_candidate_anchors
    ]

    write_csv(OUT / "official_mcp_anchor_matches.csv", MATCH_FIELDS, matches)
    write_csv(OUT / "supply_gap_scores.csv", SCORE_FIELDS, scores)
    write_csv(OUT / "primary_tourism_asset_scores.csv", PRIMARY_SCORE_FIELDS, primary_scores)
    write_csv(OUT / "partner_candidate_yatai_stalls.csv", PARTNER_CANDIDATE_FIELDS, partner_candidates)
    with (OUT / "supply_gap_scores.jsonl").open("w", encoding="utf-8") as f:
        for row in scores:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "official_anchor_count": len(anchors),
        "primary_official_anchor_count": len(primary_anchors),
        "partner_candidate_anchor_count": len(partner_candidate_anchors),
        "mcp_product_count": len(products),
        "match_count": len(matches),
        "matched_anchor_count": len(matched_by_anchor),
        "classification_counts": dict(Counter(row["classification"] for row in scores)),
        "by_city_classification": {
            city: dict(Counter(row["classification"] for row in scores if row["city_id"] == city))
            for city in sorted(set(row["city_id"] for row in scores))
        },
    }
    (REPORTS / "supply_gap_match_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Supply Gap Match Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Official anchors: {summary['official_anchor_count']}",
        f"- Primary tourism-asset anchors: {summary['primary_official_anchor_count']}",
        f"- Partner-candidate anchors excluded from primary scoring: {summary['partner_candidate_anchor_count']}",
        f"- MCP products: {summary['mcp_product_count']}",
        f"- Direct matches: {summary['match_count']}",
        f"- Matched anchors: {summary['matched_anchor_count']}",
        f"- Classification counts: {summary['classification_counts']}",
        "",
        "## By city",
        "",
        "| City | Classification counts |",
        "|---|---|",
    ]
    for city, counts in summary["by_city_classification"].items():
        lines.append(f"| {city} | {counts} |")
    lines.extend(
        [
            "",
            "## Important interpretation",
            "",
            "- `상품화 부족 자산` means no direct MCP product match in the collected sample, not proof of zero market demand.",
            "- MCP collection was rate-limited for several non-tour categories, so the current match is a first-pass sample.",
            "- Generic Fukuoka yatai aliases such as `야타이` and `포장마차` apply only to the aggregate `후쿠오카 야타이` anchor.",
            "- Individual yatai stalls are kept as partner candidates and excluded from primary tourism-asset gap scoring to avoid restaurant-level overcounting.",
        ]
    )
    (REPORTS / "SUPPLY_GAP_MATCH_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
