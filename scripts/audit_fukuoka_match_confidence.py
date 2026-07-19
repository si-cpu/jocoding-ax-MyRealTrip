#!/usr/bin/env python3
"""Reclassify every accepted Fukuoka place-product link by evidence strength."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "supply_gap_analysis"
MATCHES = ANALYSIS / "official_mcp_anchor_matches.csv"
ANCHORS = (
    ROOT
    / "data"
    / "official_tourism_sources"
    / "anchors"
    / "official_experience_anchors.csv"
)
OUT = ANALYSIS / "audit" / "fukuoka_place_product_link_audit.csv"
SUMMARY = ANALYSIS / "audit" / "fukuoka_match_confidence_summary.json"
REPORT = ANALYSIS / "reports" / "FUKUOKA_MATCH_CONFIDENCE_AUDIT.md"

FIELDS = [
    "anchor_id",
    "anchor_name",
    "product_id",
    "product_title",
    "product_url",
    "product_category_value",
    "previous_evidence_level",
    "audited_connection_class",
    "strict_match_eligible",
    "audited_reason",
    "evidence_text",
]

# These overrides are intentionally explicit and reviewable. They cover every
# known conditional/parent hit in the current 25-link Fukuoka result set.
OVERRIDES: dict[tuple[str, str], tuple[str, str]] = {
    (
        "official-fukuoka-guide-26798",
        "3520869",
    ): (
        "option_available",
        "상품이 자유 맞춤투어이며 후쿠오카 타워는 가능한 코스 예시이지 고정 방문지가 아님",
    ),
    (
        "official-fukuoka-guide-26798",
        "3521464",
    ): (
        "option_available",
        "일정 제목이 '가이드 추천 옵션 선택'으로 명시되어 고정 방문으로 볼 수 없음",
    ),
    (
        "official-fukuoka-guide-26800",
        "4159277",
    ): (
        "option_available",
        "일정에 '(옵션) 마린월드'로 명시됨",
    ),
    (
        "official-fukuoka-guide-26800",
        "4159287",
    ): (
        "option_available",
        "일정에 '(옵션) 마린월드'로 명시됨",
    ),
    (
        "official-fukuoka-guide-26825",
        "3841906",
    ): (
        "mention_only",
        "상세가 '여행 일정을 고려하여 방문 여부를 결정'하라고 명시함",
    ),
    (
        "official-fukuoka-guide-26825",
        "4435009",
    ): (
        "parent_contained",
        "직접 방문지는 오호리 공원 전체가 아니라 공원 내부의 일본정원으로 명시됨",
    ),
}

STRICT_CLASSES = {"direct_ticket", "confirmed_scheduled_visit"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def classify(row: dict[str, str]) -> tuple[str, str]:
    override = OVERRIDES.get((row["anchor_id"], row["product_id"]))
    if override:
        return override
    if row["product_category_value"] in {"ticket", "ticket_v2"}:
        return (
            "direct_ticket",
            "시설명이 상품 제목에 직접 등장하는 단독 입장권",
        )
    return (
        "confirmed_scheduled_visit",
        "공개 일정 또는 MCP 상세에서 고정 방문 코스로 직접 확인",
    )


def main() -> int:
    anchors = {
        row["anchor_id"]: row
        for row in read_csv(ANCHORS)
        if row.get("city_id") == "jp-fukuoka"
        and row.get("anchor_type") == "place"
        and row.get("official_source_type") == "tourism_facility"
        and row.get("review_status") == "accepted"
        and row.get("match_ready") == "true"
    }
    source_rows = [
        row for row in read_csv(MATCHES) if row.get("city_id") == "jp-fukuoka"
    ]
    rows: list[dict[str, str]] = []
    for row in source_rows:
        connection_class, reason = classify(row)
        anchor = anchors[row["anchor_id"]]
        rows.append(
            {
                "anchor_id": row["anchor_id"],
                "anchor_name": anchor["anchor_name_ko"],
                "product_id": row["product_id"],
                "product_title": row["product_title"],
                "product_url": row["product_url"],
                "product_category_value": row["product_category_value"],
                "previous_evidence_level": row["evidence_level"],
                "audited_connection_class": connection_class,
                "strict_match_eligible": str(
                    connection_class in STRICT_CLASSES
                ).lower(),
                "audited_reason": reason,
                "evidence_text": row["evidence_text"],
            }
        )
    write_csv(OUT, rows)
    strict_rows = [
        row for row in rows if row["strict_match_eligible"] == "true"
    ]
    strict_anchors = {row["anchor_id"] for row in strict_rows}
    observed_anchors = {
        row["anchor_id"]
        for row in rows
        if row["audited_connection_class"] != "mention_only"
    }
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "official_place_denominator": len(anchors),
        "audited_place_product_links": len(rows),
        "connection_class_counts": dict(
            Counter(row["audited_connection_class"] for row in rows)
        ),
        "strict_links": len(strict_rows),
        "strict_unique_products": len({row["product_id"] for row in strict_rows}),
        "strict_matched_places": len(strict_anchors),
        "strict_match_rate_pct": round(len(strict_anchors) / len(anchors) * 100, 1),
        "observed_linked_places_including_options_and_containment": len(
            observed_anchors
        ),
        "observed_link_rate_pct": round(
            len(observed_anchors) / len(anchors) * 100, 1
        ),
        "note": (
            "Anchor-level rate can remain unchanged even when inflated product-link "
            "counts are corrected; the same place may still have another strict product."
        ),
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    lines = [
        "# 후쿠오카 장소×상품 연결 신뢰도 감사",
        "",
        f"- 공식 장소 분모: {len(anchors)}곳",
        f"- 기존 연결: {len(rows)}건",
        f"- 엄격 연결: {len(strict_rows)}건 / {len(strict_anchors)}곳",
        f"- 엄격 일치율: {summary['strict_match_rate_pct']:.1f}%",
        f"- 옵션·포함관계까지 관측 연결: {len(observed_anchors)}곳 "
        f"({summary['observed_link_rate_pct']:.1f}%)",
        "",
        "엄격 일치는 단독 입장권 또는 고정 일정 방문만 포함한다. 선택 옵션, "
        "상위 장소 포함관계, 단순 언급은 상품 수를 부풀리지 않도록 분리한다.",
        "",
        "| 장소 | 상품 | 감사 분류 | 엄격 포함 | 이유 |",
        "|---|---|---|---:|---|",
    ]
    for row in rows:
        lines.append(
            f"| {row['anchor_name']} | [{row['product_title']}]({row['product_url']}) "
            f"| {row['audited_connection_class']} | {row['strict_match_eligible']} "
            f"| {row['audited_reason']} |"
        )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
