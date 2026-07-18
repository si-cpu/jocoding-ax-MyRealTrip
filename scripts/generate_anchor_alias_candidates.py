#!/usr/bin/env python3
"""Generate automatic Korean alias candidates for official tourism anchors.

This is intentionally conservative. It does not pretend to be a full Japanese-
to-Korean translator. It creates reviewable alias candidates from repeatable
rules, then downstream matching can use accepted/high-confidence aliases.
"""

from __future__ import annotations

import csv
import json
import re
from collections import defaultdict
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANCHORS = ROOT / "data" / "official_tourism_sources" / "anchors" / "official_experience_anchors.csv"
PRODUCTS = ROOT / "data" / "mcp_tna_products" / "processed" / "mcp_tna_products.csv"
OUT = ROOT / "data" / "supply_gap_analysis"
REPORTS = OUT / "reports"
ALIAS_CSV = OUT / "auto_anchor_alias_candidates.csv"

FIELDS = [
    "anchor_id",
    "city_id",
    "city_name",
    "official_name_ja",
    "anchor_type",
    "official_source_type",
    "alias_ko",
    "alias_source",
    "confidence",
    "review_status",
    "matched_product_count",
    "matched_product_titles",
    "notes",
]

JP_KO_TERMS = [
    ("広島", "히로시마"),
    ("福岡", "후쿠오카"),
    ("宮島", "미야지마"),
    ("厳島", "이쓰쿠시마"),
    ("平和", "평화"),
    ("記念", "기념"),
    ("資料館", "자료관"),
    ("祈念館", "기념관"),
    ("美術館", "미술관"),
    ("博物館", "박물관"),
    ("図書館", "도서관"),
    ("動物公園", "동물공원"),
    ("植物公園", "식물공원"),
    ("公園", "공원"),
    ("庭園", "정원"),
    ("城", "성"),
    ("タワー", "타워"),
    ("おりづる", "오리즈루"),
]

GENERIC_SUFFIXES = [
    ("평화기념자료관", "평화기념관"),
    ("히로시마평화기념자료관", "히로시마평화기념관"),
]


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize(text: str | None) -> str:
    return re.sub(r"[^0-9a-z가-힣ぁ-んァ-ン一-龥]+", "", clean(text).casefold())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def is_primary_tourism_anchor(anchor: dict[str, str]) -> bool:
    return anchor.get("official_source_type") not in {"official_yatai", "official_yatai_cluster"} and anchor.get(
        "anchor_type"
    ) not in {"food_place", "place_cluster"}


def rule_translate_jp_to_ko(name: str) -> list[tuple[str, str, float]]:
    variants: list[tuple[str, str, float]] = []
    translated = name
    hits = 0
    for jp, ko in JP_KO_TERMS:
        if jp in translated:
            translated = translated.replace(jp, ko)
            hits += 1
    translated = re.sub(r"[「」『』（）()\\[\\]【】｢｣・･\\s]+", "", translated)
    if hits and re.search(r"[가-힣]", translated):
        variants.append((translated, "jp_term_rule", min(0.55 + hits * 0.08, 0.9)))
        spaced = re.sub(r"(히로시마|후쿠오카|미야지마|이쓰쿠시마)", r"\1 ", translated).strip()
        if spaced != translated:
            variants.append((spaced, "jp_term_rule_spaced", min(0.5 + hits * 0.07, 0.82)))
    for before, after in GENERIC_SUFFIXES:
        for base, _, conf in list(variants):
            if before in base:
                variants.append((base.replace(before, after), "ko_short_form_rule", min(conf + 0.03, 0.9)))
    return variants


def title_match_count(alias: str, products: list[dict[str, str]], city_name: str) -> tuple[int, str]:
    alias_norm = normalize(alias)
    if not alias_norm:
        return 0, ""
    matched = []
    for product in products:
        if product.get("city_query") != city_name:
            continue
        title = clean(product.get("title"))
        if alias_norm in normalize(title):
            matched.append(title)
    return len(set(matched)), " | ".join(list(dict.fromkeys(matched))[:5])


def main() -> int:
    anchors = [a for a in read_csv(ANCHORS) if is_primary_tourism_anchor(a)]
    products = read_csv(PRODUCTS) if PRODUCTS.exists() else []
    rows = []
    seen: set[tuple[str, str]] = set()
    for anchor in anchors:
        official_name = clean(anchor.get("anchor_name_local") or anchor.get("anchor_name"))
        candidates = []
        if anchor.get("anchor_name_en"):
            candidates.append((anchor["anchor_name_en"], "official_english_name", 0.7))
        candidates.extend(rule_translate_jp_to_ko(official_name))

        for alias, source, confidence in candidates:
            alias = clean(alias)
            if not alias or len(normalize(alias)) < 2:
                continue
            key = (anchor["anchor_id"], normalize(alias))
            if key in seen:
                continue
            seen.add(key)
            count, titles = title_match_count(alias, products, anchor["city_name"])
            adjusted_confidence = confidence + (0.08 if count else 0)
            review_status = "auto_candidate_matched" if count else "auto_candidate_unmatched"
            rows.append(
                {
                    "anchor_id": anchor["anchor_id"],
                    "city_id": anchor["city_id"],
                    "city_name": anchor["city_name"],
                    "official_name_ja": official_name,
                    "anchor_type": anchor["anchor_type"],
                    "official_source_type": anchor["official_source_type"],
                    "alias_ko": alias,
                    "alias_source": source,
                    "confidence": f"{min(adjusted_confidence, 0.95):.2f}",
                    "review_status": review_status,
                    "matched_product_count": str(count),
                    "matched_product_titles": titles,
                    "notes": "auto-generated alias candidate; review before treating as confirmed translation",
                }
            )

    rows.sort(key=lambda r: (-int(r["matched_product_count"]), r["city_name"], r["official_name_ja"], r["alias_ko"]))
    write_csv(ALIAS_CSV, rows)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "primary_anchor_count": len(anchors),
        "alias_candidate_count": len(rows),
        "matched_alias_candidate_count": sum(1 for r in rows if int(r["matched_product_count"]) > 0),
        "outputs": [str(ALIAS_CSV.relative_to(ROOT))],
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "auto_anchor_alias_candidate_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
