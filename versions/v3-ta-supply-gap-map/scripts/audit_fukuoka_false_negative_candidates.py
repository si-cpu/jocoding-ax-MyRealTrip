#!/usr/bin/env python3
"""Audit exact-name Fukuoka hits that the positive matcher intentionally rejects."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "supply_gap_analysis"
ANCHORS = (
    ROOT
    / "data"
    / "official_tourism_sources"
    / "anchors"
    / "official_experience_anchors.csv"
)
MATCHES = ANALYSIS / "official_mcp_anchor_matches.csv"
SECTIONS = ANALYSIS / "audit" / "fukuoka_product_detail_sections.csv"
SLOTS = ANALYSIS / "tour_details" / "public_itinerary_slots.csv"
PRODUCTS = ANALYSIS / "audit" / "fukuoka_product_detail_inventory.csv"
OUT = ANALYSIS / "audit" / "fukuoka_false_negative_candidate_audit.csv"
SUMMARY = ANALYSIS / "audit" / "fukuoka_false_negative_candidate_summary.json"

FIELDS = [
    "anchor_id",
    "anchor_name_ko",
    "product_id",
    "product_title",
    "matched_official_name",
    "evidence_sources",
    "evidence_excerpt",
    "review_disposition",
    "strict_match_eligible",
    "review_reason",
]

DISPOSITIONS: dict[tuple[str, str], tuple[str, str]] = {
    ("official-fukuoka-guide-27128", "3520869"): (
        "option_available",
        "자유 맞춤투어의 선택 가능한 코스 예시",
    ),
    ("official-fukuoka-guide-27128", "5735236"): (
        "replaced_itinerary",
        "해당 슬롯이 후쿠오카성터·마이즈루 공원으로 대체된다고 명시",
    ),
    ("official-fukuoka-guide-27159", "4157435"): (
        "relation_only",
        "우미노나카미치가 시카노시마를 연결한다는 지리 설명뿐",
    ),
    ("official-fukuoka-guide-27159", "4159277"): (
        "relation_only",
        "우미노나카미치가 시카노시마를 연결한다는 지리 설명뿐",
    ),
    ("official-fukuoka-guide-27159", "4159287"): (
        "relation_only",
        "우미노나카미치가 시카노시마를 연결한다는 지리 설명뿐",
    ),
    ("official-fukuoka-guide-27159", "5735236"): (
        "view_only",
        "후쿠오카 타워에서 보이는 섬으로만 언급",
    ),
    ("official-fukuoka-guide-26798", "4521749"): (
        "dropoff_only",
        "하차 희망자가 있을 때만 주변 정차하며 방문·입장은 아님",
    ),
    ("official-fukuoka-guide-26798", "5735236"): (
        "replaced_itinerary",
        "후쿠오카 타워 슬롯이 후쿠오카성터·마이즈루 공원으로 대체됨",
    ),
}


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize(text: str | None) -> str:
    return re.sub(
        r"[^0-9a-z가-힣ぁ-んァ-ン一-龥]+",
        "",
        clean(text).casefold(),
    )


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def official_names(anchor: dict[str, str]) -> list[str]:
    values = [
        anchor.get("anchor_name"),
        anchor.get("anchor_name_local"),
        anchor.get("anchor_name_ko"),
        anchor.get("anchor_name_en"),
    ]
    return list(
        dict.fromkeys(
            clean(value) for value in values if len(normalize(value)) >= 4
        )
    )


def main() -> int:
    anchors = [
        row
        for row in read_csv(ANCHORS)
        if row.get("city_id") == "jp-fukuoka"
        and row.get("anchor_type") == "place"
        and row.get("official_source_type") == "tourism_facility"
        and row.get("review_status") == "accepted"
        and row.get("match_ready") == "true"
    ]
    matched = {
        (row["anchor_id"], row["product_id"])
        for row in read_csv(MATCHES)
        if row.get("city_id") == "jp-fukuoka"
    }
    products = {row["product_id"]: row for row in read_csv(PRODUCTS)}
    sources = [
        (
            "product_title",
            read_csv(PRODUCTS),
            ("product_title",),
        ),
        (
            "detail_section",
            read_csv(SECTIONS),
            ("section_label", "section_text"),
        ),
        (
            "public_itinerary",
            read_csv(SLOTS),
            ("slot_title", "slot_description"),
        ),
    ]
    candidates: dict[tuple[str, str], dict[str, object]] = {}
    for anchor in anchors:
        names = official_names(anchor)
        for source_name, rows, text_fields in sources:
            for source_row in rows:
                product_id = source_row["product_id"]
                key = (anchor["anchor_id"], product_id)
                if key in matched:
                    continue
                text = clean(
                    " ".join(source_row.get(field, "") for field in text_fields)
                )
                hit = next(
                    (name for name in names if normalize(name) in normalize(text)),
                    "",
                )
                if not hit:
                    continue
                candidate = candidates.setdefault(
                    key,
                    {
                        "anchor_id": anchor["anchor_id"],
                        "anchor_name_ko": anchor["anchor_name_ko"],
                        "product_id": product_id,
                        "product_title": products.get(product_id, {}).get(
                            "product_title",
                            source_row.get("product_title", ""),
                        ),
                        "matched_official_name": hit,
                        "evidence_sources": [],
                        "evidence_excerpt": text[:600],
                    },
                )
                candidate["evidence_sources"].append(source_name)
    rows_out: list[dict[str, str]] = []
    for key, candidate in sorted(candidates.items()):
        disposition = DISPOSITIONS.get(key)
        if disposition:
            review_disposition, reason = disposition
        else:
            review_disposition, reason = (
                "unresolved_manual_review",
                "공식명 직접 일치가 있으나 자동 판정 사유가 없어 수동 검토 필요",
            )
        rows_out.append(
            {
                **{
                    field: str(candidate[field])
                    for field in (
                        "anchor_id",
                        "anchor_name_ko",
                        "product_id",
                        "product_title",
                        "matched_official_name",
                        "evidence_excerpt",
                    )
                },
                "evidence_sources": " | ".join(
                    sorted(set(candidate["evidence_sources"]))
                ),
                "review_disposition": review_disposition,
                "strict_match_eligible": "false",
                "review_reason": reason,
            }
        )
    write_csv(OUT, rows_out)
    unresolved = sum(
        row["review_disposition"] == "unresolved_manual_review" for row in rows_out
    )
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "official_places_scanned": len(anchors),
        "mcp_products_scanned": len(products),
        "exact_name_candidate_pairs": len(rows_out),
        "disposition_counts": dict(
            Counter(row["review_disposition"] for row in rows_out)
        ),
        "strict_matches_added": 0,
        "unresolved_candidates": unresolved,
        "method_limit": (
            "This gate audits official Japanese/Korean/English names only. "
            "Unregistered translations or aliases can still create false negatives."
        ),
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if unresolved == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
