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
MCP_RAW = ROOT / "data" / "mcp_tna_products" / "raw"
AUTO_ALIASES = ROOT / "data" / "supply_gap_analysis" / "auto_anchor_alias_candidates.csv"
VERIFIED_LINKS = ROOT / "data" / "supply_gap_analysis" / "verified_product_place_links.csv"
GENERATED_DETAIL_LINKS = (
    ROOT
    / "data"
    / "supply_gap_analysis"
    / "tour_details"
    / "tour_detail_official_place_matches.csv"
)
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
    "confirmed_product_count",
    "detail_pending_product_count",
    "korean_name_ready",
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

def is_partner_candidate_only(anchor: dict[str, str]) -> bool:
    return anchor.get("official_source_type") in {"official_yatai", "official_yatai_cluster"} or anchor.get(
    "anchor_type"
    ) in {"food_place", "place_cluster"}


def is_primary_tourism_asset(anchor: dict[str, str]) -> bool:
    return anchor.get("official_source_type") == "tourism_facility" and anchor.get("anchor_type") == "place"


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize(text: str | None) -> str:
    return re.sub(r"[^0-9a-z가-힣ぁ-んァ-ン一-龥]+", "", clean(text).casefold())


def is_review_ready_korean_alias(text: str | None) -> bool:
    value = clean(text)
    return bool(re.search(r"[가-힣]", value)) and not bool(
        re.search(r"[ぁ-んァ-ン一-龥]", value)
    )


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
    mapping = {
        "jp-osaka": "오사카",
        "jp-tokyo": "도쿄",
        "jp-kyoto": "교토",
        "jp-fukuoka": "후쿠오카",
        "jp-hiroshima": "히로시마",
        "kr-seoul": "서울",
        "kr-busan": "부산",
        "kr-yeosu": "여수",
        "kr-daejeon": "대전",
    }
    if city_id in mapping:
        return mapping[city_id]
    return city_id


def city_collection_complete(city_query: str) -> bool:
    if not MCP_RAW.exists():
        return False
    return not any(MCP_RAW.glob(f"{city_query}_*_error.json")) and not (
        MCP_RAW / f"{city_query}_collection_error.json"
    ).exists()


def load_auto_aliases() -> dict[str, list[str]]:
    if not AUTO_ALIASES.exists():
        return {}
    aliases: dict[str, list[str]] = defaultdict(list)
    for row in read_csv(AUTO_ALIASES):
        try:
            confidence = float(row.get("confidence") or 0)
            matched_count = int(row.get("matched_product_count") or 0)
        except ValueError:
            continue
        if confidence < 0.75:
            continue
        alias = clean(row.get("alias_ko"))
        if not is_review_ready_korean_alias(alias):
            continue
        aliases[row["anchor_id"]].append(alias)
    return aliases


def alias_candidates(anchor: dict[str, str], auto_aliases: dict[str, list[str]]) -> list[str]:
    values = [
        anchor.get("anchor_name"),
        anchor.get("anchor_name_local"),
        anchor.get("anchor_name_ko"),
        anchor.get("anchor_name_en"),
    ]
    values.extend(auto_aliases.get(anchor["anchor_id"], []))
    # Category-level aliases only for the aggregate yatai inventory.
    if anchor.get("official_source_type") == "official_yatai_cluster":
        values.extend(["야타이", "yatai", "포장마차", "나카스 포장마차", "후쿠오카 야타이"])
    korean_name = clean(anchor.get("anchor_name_ko"))
    if korean_name:
        values.extend(
            part.strip()
            for part in re.split(r"[()（）/·]", korean_name)
            if part.strip()
        )
    return [v for v in dict.fromkeys(clean(v) for v in values) if v]


def match_score(anchor: dict[str, str], product: dict[str, str], auto_aliases: dict[str, list[str]]) -> tuple[float, str, str]:
    title = clean(product.get("title"))
    raw = clean(product.get("raw_text"))
    haystack = normalize(f"{title} {raw}")
    title_norm = normalize(title)

    for alias in alias_candidates(anchor, auto_aliases):
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


def classify(
    confirmed_product_count: int,
    detail_pending_product_count: int,
    official_source_type: str,
    city_product_count: int,
    korean_name_ready: bool,
    collection_complete: bool = True,
) -> tuple[str, str, float, float, str]:
    official_strength = 1.0
    if official_source_type == "official_event":
        official_strength = 0.75
    if city_product_count == 0:
        return (
            "MCP 미수집 자산",
            "MCP collection has no products for this city; retry collection before scoring supply gap",
            official_strength,
            0.0,
            "",
        )
    if confirmed_product_count >= 3:
        supply = 1.0
    elif confirmed_product_count == 2:
        supply = 0.7
    elif confirmed_product_count == 1:
        supply = 0.45
    else:
        supply = 0.0
    gap = round(max(official_strength - supply, 0), 2)
    if confirmed_product_count >= 3:
        return "검증된 대표 경험", "official asset has multiple confirmed MCP-linked products", official_strength, supply, str(gap)
    if confirmed_product_count >= 1:
        return "부분 상품화 자산", "official asset has at least one confirmed MCP-linked product", official_strength, supply, str(gap)
    if detail_pending_product_count >= 1:
        return (
            "연결 후보(투어 상세 확인 필요)",
            "tour title contains the place alias, but itinerary/inclusion detail has not been collected",
            official_strength,
            0.0,
            "",
        )
    if not korean_name_ready:
        return (
            "매칭 보류(한국어 번역 부족)",
            "official Japanese place name has no Korean translated name; no-match is not supply-gap evidence",
            official_strength,
            0.0,
            "",
        )
    if not collection_complete:
        return (
            "MCP 추가 수집 필요",
            "Korean translated name is ready, but MCP collection stopped with category/page errors",
            official_strength,
            0.0,
            "",
        )
    return (
        "수집 표본 내 미연결 후보",
        "review-ready Korean alias exists but no direct MCP match was found in the rate-limited sample",
        official_strength,
        0.0,
        str(official_strength),
    )


def main() -> int:
    anchors = read_csv(ANCHORS)
    products = read_csv(PRODUCTS) if PRODUCTS.exists() else []
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    matches = []
    matched_by_anchor: dict[str, list[dict[str, str]]] = defaultdict(list)
    auto_aliases = load_auto_aliases()
    primary_anchors = [anchor for anchor in anchors if is_primary_tourism_asset(anchor)]
    partner_candidate_anchors = [anchor for anchor in anchors if is_partner_candidate_only(anchor)]
    for anchor in primary_anchors:
        city_query = city_to_query(anchor["city_id"])
        city_products = [p for p in products if p.get("city_query") == city_query]
        for product in city_products:
            score, mtype, evidence = match_score(anchor, product, auto_aliases)
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

    primary_by_id = {anchor["anchor_id"]: anchor for anchor in primary_anchors}
    existing_match_keys = {
        (match["anchor_id"], match["product_id"])
        for match in matches
    }
    verified_link_sources = [
        # Generated detail links are loaded first so manually reviewed evidence
        # can replace the same anchor-product pair when both are available.
        path for path in (GENERATED_DETAIL_LINKS, VERIFIED_LINKS) if path.exists()
    ]
    for verified_link_source in verified_link_sources:
        for row in read_csv(verified_link_source):
            anchor = primary_by_id.get(clean(row.get("anchor_id")))
            product_id = clean(row.get("product_id"))
            if not anchor or not product_id:
                continue
            key = (anchor["anchor_id"], product_id)
            if key in existing_match_keys:
                matches = [
                    match
                    for match in matches
                    if (match["anchor_id"], match["product_id"]) != key
                ]
                matched_by_anchor[anchor["anchor_id"]] = [
                    match
                    for match in matched_by_anchor[anchor["anchor_id"]]
                    if match["product_id"] != product_id
                ]
            match = {
                "anchor_id": anchor["anchor_id"],
                "city_id": anchor["city_id"],
                "city_name": anchor["city_name"],
                "anchor_name": anchor["anchor_name"],
                "anchor_type": anchor["anchor_type"],
                "official_source_type": anchor["official_source_type"],
                "product_id": product_id,
                "product_title": clean(row.get("product_title")),
                "product_url": clean(row.get("product_url")),
                "product_category": clean(row.get("product_category")),
                "product_category_value": clean(row.get("product_category_value")),
                "match_type": "verified_detail",
                "match_score": "1.0",
                "evidence_level": "tour_detail_confirmed",
                "evidence_policy": "투어 상세 일정·소개·포함사항에서 실제 장소 방문을 직접 확인했다.",
                "evidence_text": clean(row.get("evidence_text")),
            }
            matches.append(match)
            matched_by_anchor[anchor["anchor_id"]].append(match)
            existing_match_keys.add(key)

    scores = []
    for anchor in primary_anchors:
        anchor_matches = matched_by_anchor.get(anchor["anchor_id"], [])
        unique_products = {}
        for match in anchor_matches:
            unique_products[match["product_url"] or match["product_title"]] = match
        product_count = len(unique_products)
        confirmed_product_count = sum(
            match["evidence_level"] != "tour_title_needs_detail"
            for match in unique_products.values()
        )
        detail_pending_product_count = sum(
            match["evidence_level"] == "tour_title_needs_detail"
            for match in unique_products.values()
        )
        korean_name_ready = is_review_ready_korean_alias(anchor.get("anchor_name_ko")) or any(
            is_review_ready_korean_alias(alias)
            for alias in auto_aliases.get(anchor["anchor_id"], [])
        ) or is_review_ready_korean_alias(anchor.get("anchor_name"))
        city_product_count = sum(1 for product in products if product.get("city_query") == city_to_query(anchor["city_id"]))
        collection_complete = city_collection_complete(city_to_query(anchor["city_id"]))
        classification, reason, official_strength, supply, gap = classify(
            confirmed_product_count,
            detail_pending_product_count,
            anchor["official_source_type"],
            city_product_count,
            korean_name_ready,
            collection_complete,
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
                "confirmed_product_count": str(confirmed_product_count),
                "detail_pending_product_count": str(detail_pending_product_count),
                "korean_name_ready": str(korean_name_ready).lower(),
                "gap_score": gap,
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
        "auto_alias_anchor_count": len(auto_aliases),
        "auto_alias_count": sum(len(v) for v in auto_aliases.values()),
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
        f"- Auto alias anchors used: {summary['auto_alias_anchor_count']}",
        f"- Auto aliases used: {summary['auto_alias_count']}",
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
            "- Every Kyoto primary asset is matched with a Korean translated name generated from its official kana reading; curated standard translations are marked separately from automatic transliterations.",
            "- `매칭 보류(한국어 번역 부족)` is not a supply gap. Japanese-to-Korean translation must be completed first.",
            "- `연결 후보(투어 상세 확인 필요)` is title-level evidence only; itinerary/inclusion detail must confirm an actual visit.",
            "- `수집 표본 내 미연결 후보` means a Korean translated name had no direct match after a complete MCP collection. It is still not proof of zero market demand.",
            "- `MCP 추가 수집 필요` means the Korean translated name is ready, but category/page errors prevent a supply-gap conclusion.",
            "- Multi-city manual/DMO seed candidates are excluded from this primary scoring file to avoid contaminating official-data analysis.",
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
