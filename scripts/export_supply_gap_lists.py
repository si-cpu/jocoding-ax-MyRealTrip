#!/usr/bin/env python3
"""Export exact first-pass supply-gap lists for review."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "supply_gap_analysis"
OUT = ANALYSIS / "exports"
REPORTS = ANALYSIS / "reports"
SCORES = ANALYSIS / "supply_gap_scores.csv"
MATCHES = ANALYSIS / "official_mcp_anchor_matches.csv"
ANCHORS = ROOT / "data" / "official_tourism_sources" / "anchors" / "official_experience_anchors.csv"

KOREAN_DISPLAY_NAME_MAP = {
    "후쿠오카 야타이": "후쿠오카 야타이",
    "福岡市 屋台": "후쿠오카 야타이",
    "広島城": "히로시마성",
    "広島平和記念資料館": "히로시마 평화기념자료관",
    "おりづるタワー": "오리즈루 타워",
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def display_city(city_id: str, city_name: str) -> str:
    if city_id == "jp-fukuoka":
        return "후쿠오카"
    if city_id == "jp-hiroshima":
        return "히로시마"
    return city_name or city_id


def action_for(row: dict[str, str]) -> str:
    if row["classification"] == "부분 상품화 자산":
        return "연결 상품 유지/확장 검토"
    if row["official_source_type"] == "official_event":
        return "이벤트 유효기간 확인 후 상품화 후보 검토"
    if row["anchor_type"] == "food_place":
        return "별칭/상세일정/파트너 후보 검토"
    return "별칭/상세일정/파트너 후보 검토"


def korean_display_name(anchor: dict[str, str]) -> str:
    for key in (anchor.get("anchor_name"), anchor.get("anchor_name_local")):
        value = KOREAN_DISPLAY_NAME_MAP.get(key or "")
        if value:
            return value
    if anchor.get("city_id") == "jp-fukuoka" and anchor.get("official_source_type") == "official_yatai_cluster":
        return "후쿠오카 야타이"
    return "미정"


def one_to_one_status(row: dict[str, str], anchor_matches: list[dict[str, str]]) -> str:
    if len(anchor_matches) == 1:
        return "1대1 대응 확인"
    if len(anchor_matches) > 1:
        return "1대다 대응 확인"
    return "없음"


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)
    scores = read_csv(SCORES)
    matches = read_csv(MATCHES)
    anchors = {row["anchor_id"]: row for row in read_csv(ANCHORS)}

    match_by_anchor: dict[str, list[dict[str, str]]] = {}
    for match in matches:
        match_by_anchor.setdefault(match["anchor_id"], []).append(match)

    fields = [
        "rank",
        "city",
        "official_name_ja",
        "display_name_ko",
        "official_name_en",
        "anchor_type",
        "official_source_type",
        "classification",
        "mcp_one_to_one_status",
        "mcp_product_count",
        "gap_score",
        "matched_product_titles",
        "matched_product_urls",
        "evidence_levels",
        "evidence_policies",
        "match_evidence",
        "follow_up_action",
    ]
    rows = []
    for idx, row in enumerate(scores, start=1):
        anchor_matches = match_by_anchor.get(row["anchor_id"], [])
        anchor = anchors.get(row["anchor_id"], {})
        rows.append(
            {
                "rank": str(idx),
                "city": display_city(row["city_id"], row["city_name"]),
                "official_name_ja": anchor.get("anchor_name_local") or row["anchor_name"],
                "display_name_ko": korean_display_name(anchor),
                "official_name_en": anchor.get("anchor_name_en", ""),
                "anchor_type": row["anchor_type"],
                "official_source_type": row["official_source_type"],
                "classification": row["classification"],
                "mcp_one_to_one_status": one_to_one_status(row, anchor_matches),
                "mcp_product_count": row["mcp_product_count"],
                "gap_score": row["gap_score"],
                "matched_product_titles": " | ".join(m["product_title"] for m in anchor_matches) or "없음",
                "matched_product_urls": " | ".join(m["product_url"] for m in anchor_matches) or "없음",
                "evidence_levels": " | ".join(m.get("evidence_level", "") for m in anchor_matches if m.get("evidence_level")) or "없음",
                "evidence_policies": " | ".join(m.get("evidence_policy", "") for m in anchor_matches if m.get("evidence_policy")) or "없음",
                "match_evidence": " | ".join(m["evidence_text"] for m in anchor_matches) or "없음",
                "follow_up_action": action_for(row),
            }
        )

    write_csv(OUT / "supply_gap_exact_list.csv", fields, rows)
    write_csv(
        OUT / "matched_assets_exact_list.csv",
        fields,
        [row for row in rows if row["classification"] == "부분 상품화 자산"],
    )
    write_csv(
        OUT / "under_connected_assets_exact_list.csv",
        fields,
        [row for row in rows if row["classification"] == "상품화 부족 자산"],
    )

    counts = Counter((row["city"], row["classification"]) for row in rows)
    lines = [
        "# Supply Gap Exact List",
        "",
        f"- Generated at: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- Total official assets: {len(rows)}",
        f"- Matched/partial assets: {sum(1 for row in rows if row['classification'] == '부분 상품화 자산')}",
        f"- Under-connected assets: {sum(1 for row in rows if row['classification'] == '상품화 부족 자산')}",
        "",
        "## City summary",
        "",
        "| City | Classification | Count |",
        "|---|---|---:|",
    ]
    for (city, classification), count in sorted(counts.items()):
        lines.append(f"| {city} | {classification} | {count} |")

    lines.extend(
        [
            "",
            "## Matched / partially productized assets",
            "",
        "| City | Official asset (JA) | Display name (KO) | MCP status | Evidence level | Product count | Matched products |",
        "|---|---|---|---|---|---:|---|",
        ]
    )
    for row in rows:
        if row["classification"] != "부분 상품화 자산":
            continue
        lines.append(
            f"| {row['city']} | {row['official_name_ja']} | {row['display_name_ko']} | {row['mcp_one_to_one_status']} | {row['evidence_levels']} | {row['mcp_product_count']} | {row['matched_product_titles']} |"
        )

    lines.extend(
        [
            "",
            "## Under-connected assets - full list",
            "",
            "| Rank | City | Official asset (JA) | Display name (KO) | MCP status | Type | Follow-up action |",
            "|---:|---|---|---|---|---|---|",
        ]
    )
    for row in rows:
        if row["classification"] != "상품화 부족 자산":
            continue
        lines.append(
            f"| {row['rank']} | {row['city']} | {row['official_name_ja']} | {row['display_name_ko']} | {row['mcp_one_to_one_status']} | {row['anchor_type']} | {row['follow_up_action']} |"
        )

    (REPORTS / "SUPPLY_GAP_EXACT_LIST.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "total_official_assets": len(rows),
        "matched_partial_assets": sum(1 for row in rows if row["classification"] == "부분 상품화 자산"),
        "under_connected_assets": sum(1 for row in rows if row["classification"] == "상품화 부족 자산"),
        "outputs": [
            "data/supply_gap_analysis/exports/supply_gap_exact_list.csv",
            "data/supply_gap_analysis/exports/matched_assets_exact_list.csv",
            "data/supply_gap_analysis/exports/under_connected_assets_exact_list.csv",
            "data/supply_gap_analysis/reports/SUPPLY_GAP_EXACT_LIST.md",
        ],
    }
    (REPORTS / "supply_gap_exact_list_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
