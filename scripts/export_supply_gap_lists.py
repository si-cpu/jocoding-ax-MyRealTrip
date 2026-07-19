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
CITY_COVERAGE = ANALYSIS / "city_supply_coverage.csv"
MATCHES = ANALYSIS / "official_mcp_anchor_matches.csv"
DETAIL_EVIDENCE = ANALYSIS / "detail_evidence" / "tour_detail_evidence.csv"
ANCHORS = ROOT / "data" / "official_tourism_sources" / "anchors" / "official_experience_anchors.csv"
AUTO_ALIASES = ANALYSIS / "auto_anchor_alias_candidates.csv"
ANALYSIS_CITY_IDS = {"jp-fukuoka", "jp-hiroshima"}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def read_json_if_exists(path: Path) -> dict:
    if not path.exists():
        return {}
    return json.loads(path.read_text(encoding="utf-8"))


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
        return "번역명/상세일정/파트너 후보 검토"
    return "번역명/상세일정/파트너 후보 검토"


def load_display_aliases() -> dict[str, str]:
    if not AUTO_ALIASES.exists():
        return {}
    aliases: dict[str, str] = {}
    with AUTO_ALIASES.open(encoding="utf-8-sig", newline="") as f:
        for row in csv.DictReader(f):
            try:
                confidence = float(row.get("confidence") or 0)
                matched_count = int(row.get("matched_product_count") or 0)
            except ValueError:
                continue
            if confidence < 0.75:
                continue
            aliases.setdefault(row["anchor_id"], row["alias_ko"])
    return aliases


def korean_display_name(anchor: dict[str, str], display_aliases: dict[str, str]) -> str:
    if anchor.get("anchor_name_ko"):
        return anchor["anchor_name_ko"]
    if anchor.get("anchor_id") in display_aliases:
        return display_aliases[anchor["anchor_id"]]
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
    scores = [
        row for row in read_csv(SCORES)
        if row.get("city_id") in ANALYSIS_CITY_IDS
    ]
    city_coverage = [
        row for row in (read_csv(CITY_COVERAGE) if CITY_COVERAGE.exists() else [])
        if row.get("city_id") in ANALYSIS_CITY_IDS
    ]
    matches = read_csv(MATCHES)
    detail_rows = read_csv(DETAIL_EVIDENCE) if DETAIL_EVIDENCE.exists() else []
    anchors = {row["anchor_id"]: row for row in read_csv(ANCHORS)}
    display_aliases = load_display_aliases()

    match_by_anchor: dict[str, list[dict[str, str]]] = {}
    for match in matches:
        match_by_anchor.setdefault(match["anchor_id"], []).append(match)
    detail_by_anchor_product = {
        (row["anchor_id"], row["product_id"]): row for row in detail_rows
    }

    fields = [
        "rank",
        "city",
        "official_name_ja",
        "display_name_ko",
        "official_name_en",
        "official_source_url",
        "anchor_type",
        "official_source_type",
        "classification",
        "mcp_one_to_one_status",
        "mcp_product_count",
        "gap_score",
        "matched_product_titles",
        "matched_product_urls",
        "evidence_levels",
        "tour_detail_evidence_levels",
        "evidence_policies",
        "match_evidence",
        "follow_up_action",
    ]
    rows = []
    for idx, row in enumerate(scores, start=1):
        anchor_matches = match_by_anchor.get(row["anchor_id"], [])
        anchor = anchors.get(row["anchor_id"], {})
        detail_levels = []
        for match in anchor_matches:
            detail = detail_by_anchor_product.get((match["anchor_id"], match["product_id"]))
            if detail and detail.get("detail_evidence_level"):
                detail_levels.append(detail["detail_evidence_level"])
        rows.append(
            {
                "rank": str(idx),
                "city": display_city(row["city_id"], row["city_name"]),
                "official_name_ja": anchor.get("anchor_name_local") or row["anchor_name"],
                "display_name_ko": korean_display_name(anchor, display_aliases),
                "official_name_en": anchor.get("anchor_name_en", ""),
                "official_source_url": anchor.get("source_url", ""),
                "anchor_type": row["anchor_type"],
                "official_source_type": row["official_source_type"],
                "classification": row["classification"],
                "mcp_one_to_one_status": one_to_one_status(row, anchor_matches),
                "mcp_product_count": row["mcp_product_count"],
                "gap_score": row["gap_score"],
                "matched_product_titles": " | ".join(m["product_title"] for m in anchor_matches) or "없음",
                "matched_product_urls": " | ".join(m["product_url"] for m in anchor_matches) or "없음",
                "evidence_levels": " | ".join(m.get("evidence_level", "") for m in anchor_matches if m.get("evidence_level")) or "없음",
                "tour_detail_evidence_levels": " | ".join(detail_levels) or "해당 없음",
                "evidence_policies": " | ".join(m.get("evidence_policy", "") for m in anchor_matches if m.get("evidence_policy")) or "없음",
                "match_evidence": " | ".join(m["evidence_text"] for m in anchor_matches) or "없음",
                "follow_up_action": action_for(row),
            }
        )

    write_csv(
        OUT / "fukuoka_hiroshima_city_supply_coverage.csv",
        list(city_coverage[0].keys()) if city_coverage else [],
        city_coverage,
    )
    write_csv(OUT / "supply_gap_exact_list.csv", fields, rows)
    write_csv(
        OUT / "matched_assets_exact_list.csv",
        fields,
        [
            row
            for row in rows
            if row["classification"] in {"부분 상품화 자산", "검증된 대표 경험"}
        ],
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
        f"- Scoped official assets (후쿠오카·히로시마 only; do not combine for a match rate): {len(rows)}",
        "- Matched/partial assets: "
        + str(
            sum(
                1
                for row in rows
                if row["classification"] in {"부분 상품화 자산", "검증된 대표 경험"}
            )
        ),
        f"- Under-connected assets: {sum(1 for row in rows if row['classification'] == '상품화 부족 자산')}",
        "",
        "## City-level coverage",
        "",
        "| City | Official scope | Official assets | MCP products | Confirmed | Detail pending | Confirmed match rate | Observed link rate | Status |",
        "|---|---|---:|---:|---:|---:|---:|---:|---|",
    ]
    for row in city_coverage:
        lines.append(
            f"| {row['city_name']} | {row['official_scope']} | {row['official_asset_count']} | {row['mcp_product_count']} | "
            f"{row['confirmed_anchor_count']} | {row['detail_pending_anchor_count']} | "
            f"{row['confirmed_match_rate_display']} | {row['observed_link_rate_display']} | "
            f"{row['rate_status']} |"
        )
    lines.extend(
        [
        "",
        "- City rates use separate city denominators. Never divide matches by a combined multi-city asset count.",
        "- Fukuoka uses places published in both the complete Japanese official catalog and the official Korean guide, after city-scope and non-tourism filtering.",
        "",
        "## City summary",
        "",
        "| City | Classification | Count |",
        "|---|---|---:|",
        ]
    )
    for (city, classification), count in sorted(counts.items()):
        lines.append(f"| {city} | {classification} | {count} |")

    lines.extend(
        [
            "",
            "## Matched / partially productized assets",
            "",
        "| City | Official asset (JA) | Display name (KO) | MCP status | Title evidence | Tour detail evidence | Product count | Matched products |",
        "|---|---|---|---|---|---|---:|---|",
        ]
    )
    for row in rows:
        if row["classification"] not in {"부분 상품화 자산", "검증된 대표 경험"}:
            continue
        lines.append(
            f"| {row['city']} | {row['official_name_ja']} | {row['display_name_ko']} | {row['mcp_one_to_one_status']} | {row['evidence_levels']} | {row['tour_detail_evidence_levels']} | {row['mcp_product_count']} | {row['matched_product_titles']} |"
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

    fukuoka_rows = [row for row in rows if row["city"] == "후쿠오카"]
    fukuoka_matched = [row for row in fukuoka_rows if int(row["mcp_product_count"]) > 0]
    detail_audit = read_json_if_exists(
        ANALYSIS / "audit" / "fukuoka_product_detail_inventory_summary.json"
    )
    city_scope_audit = read_json_if_exists(
        ANALYSIS / "audit" / "fukuoka_product_city_scope_summary.json"
    )
    confidence_audit = read_json_if_exists(
        ANALYSIS / "audit" / "fukuoka_match_confidence_summary.json"
    )
    fukuoka_lines = [
        "# 후쿠오카 공식 관광지 × 마이리얼트립 재분석",
        "",
        f"- Generated at: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- 공식 일본어 원천: 요카나비 `観る・遊ぶ` 전체 468건",
        f"- 분석 분모: 공식 한국어 가이드에도 발행되고, 후쿠오카시 범위·방문 관광지 기준을 통과한 {len(fukuoka_rows)}곳",
        f"- MCP 연결 확인: {len(fukuoka_matched)}곳",
        f"- 현재 미연결·미검증: {len(fukuoka_rows) - len(fukuoka_matched)}곳",
        f"- 잠정 확정 일치율: {len(fukuoka_matched) / len(fukuoka_rows) * 100:.1f}%",
        f"- MCP 검색 반환 감사 풀: {detail_audit.get('deduplicated_fukuoka_products', '미확인')}개 "
        f"(상세 원본 {detail_audit.get('products_with_cached_payload', '미확인')}개, "
        f"파싱 가능 {detail_audit.get('products_with_usable_sections', '미확인')}개)",
        f"- 엄격 장소×상품 연결: {confidence_audit.get('strict_links', '미확인')}건 "
        f"(조건부·포함·단순 언급 분리 전 "
        f"{confidence_audit.get('audited_place_product_links', '미확인')}건)",
        "- 상태: 180개는 후쿠오카시 공급량이 아니라 후쿠오카 검색 반환 풀이다. "
        "일부 카테고리 수집 오류와 미등록 번역 별칭 가능성이 남아 최종치가 아닌 잠정치다.",
        "",
        "## 연결 확인 장소",
        "",
        "| 일본어명 | 한국어명 | 연결 상품 수 | 판정 |",
        "|---|---|---:|---|",
    ]
    for row in fukuoka_matched:
        fukuoka_lines.append(
            f"| [{row['official_name_ja']}]({row['official_source_url']}) | "
            f"{row['display_name_ko']} | {row['mcp_product_count']} | "
            f"{row['classification']} |"
        )
    fukuoka_lines.extend(
        [
            "",
            f"## 전체 {len(fukuoka_rows)}곳 정확한 목록",
            "",
            "| 일본어명 | 한국어명 | MCP 상태 | 연결 상품 수 |",
            "|---|---|---|---:|",
        ]
    )
    for row in fukuoka_rows:
        fukuoka_lines.append(
            f"| [{row['official_name_ja']}]({row['official_source_url']}) | "
            f"{row['display_name_ko']} | {row['mcp_one_to_one_status']} | "
            f"{row['mcp_product_count']} |"
        )
    fukuoka_lines.extend(
        [
            "",
            "## 해석 주의",
            "",
            "- 투어는 제목만이 아니라 상세 일정·소개·포함사항의 실제 방문 근거를 사용한다.",
            "- 단순 인접·조망·연결 설명과 조건부 대체 장소는 긍정 연결에서 제외한다.",
            "- `없음`은 현재 MCP 수집 표본에서 직접 근거를 확인하지 못했다는 뜻이며, 상품이 절대 없다는 뜻이 아니다.",
            f"- 검색 반환 180개 중 보수적으로 후쿠오카시 콘텐츠를 확인한 상품은 "
            f"{sum(int(city_scope_audit.get('status_counts', {}).get(key, 0)) for key in ('confirmed_fukuoka_city', 'confirmed_fukuoka_city_content'))}개, "
            f"시외·광역 비투어 상품은 {city_scope_audit.get('status_counts', {}).get('outside_or_multi_region', '미확인')}개, "
            f"도시 범위 판정을 보류한 투어는 {city_scope_audit.get('status_counts', {}).get('unresolved_tour_query_pool', '미확인')}개다.",
            f"- 일본어 전용 공식 장소, 시외 장소, 체육·숙박·교통·개별 음식점은 원본과 제외 파일에 보존하지만 {len(fukuoka_rows)}곳 분모에는 넣지 않는다.",
            "- 역방향 `MCP만 있음` 판정은 상품명과 관광지명의 1대1 비교만으로 확정하지 않는다. 복합시설의 하위 경험, 거리·권역 안의 민간 시설, 공식 사이트의 투어·체험 등 다른 카탈로그, 실제 주소를 추가로 확인한다.",
            "- 팀랩·산리오·리버 크루즈 등의 계층 재분류는 [FUKUOKA_MCP_REVERSE_HIERARCHY_AUDIT.md](FUKUOKA_MCP_REVERSE_HIERARCHY_AUDIT.md)에 기록한다.",
            "- 전수 신뢰도 감사와 남은 한계는 [FUKUOKA_TRUST_AUDIT.md](FUKUOKA_TRUST_AUDIT.md)에 기록한다.",
        ]
    )
    (REPORTS / "FUKUOKA_REANALYSIS.md").write_text(
        "\n".join(fukuoka_lines) + "\n", encoding="utf-8"
    )
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "analysis_city_ids": sorted(ANALYSIS_CITY_IDS),
        "total_official_assets": len(rows),
        "matched_partial_assets": sum(
            1
            for row in rows
            if row["classification"] in {"부분 상품화 자산", "검증된 대표 경험"}
        ),
        "under_connected_assets": sum(1 for row in rows if row["classification"] == "상품화 부족 자산"),
        "by_city_coverage": city_coverage,
        "outputs": [
            "data/supply_gap_analysis/exports/fukuoka_hiroshima_city_supply_coverage.csv",
            "data/supply_gap_analysis/exports/supply_gap_exact_list.csv",
            "data/supply_gap_analysis/exports/matched_assets_exact_list.csv",
            "data/supply_gap_analysis/exports/under_connected_assets_exact_list.csv",
            "data/supply_gap_analysis/reports/SUPPLY_GAP_EXACT_LIST.md",
            "data/supply_gap_analysis/reports/FUKUOKA_REANALYSIS.md",
        ],
    }
    (REPORTS / "supply_gap_exact_list_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
