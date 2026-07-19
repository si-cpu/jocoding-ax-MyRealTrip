#!/usr/bin/env python3
"""Build a consolidated, evidence-backed Fukuoka trust audit report."""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
OFFICIAL = ROOT / "data" / "official_tourism_sources"
ANALYSIS = ROOT / "data" / "supply_gap_analysis"
REPORT = ANALYSIS / "reports" / "FUKUOKA_TRUST_AUDIT.md"


def load(path: Path) -> dict:
    return json.loads(path.read_text(encoding="utf-8"))


def main() -> int:
    guide = load(OFFICIAL / "reports" / "fukuoka_official_guide_collection_summary.json")
    tours = load(OFFICIAL / "reports" / "fukuoka_official_tour_collection_summary.json")
    details = load(ANALYSIS / "audit" / "fukuoka_product_detail_inventory_summary.json")
    scope = load(ANALYSIS / "audit" / "fukuoka_product_city_scope_summary.json")
    confidence = load(ANALYSIS / "audit" / "fukuoka_match_confidence_summary.json")
    false_negatives = load(
        ANALYSIS / "audit" / "fukuoka_false_negative_candidate_summary.json"
    )
    reverse_list = load(
        ANALYSIS / "reports" / "fukuoka_mcp_minus_official81_summary.json"
    )
    error_files = sorted(
        (ROOT / "data" / "mcp_tna_products" / "raw").glob("후쿠오카*_error.json")
    )
    status_counts = scope["status_counts"]
    city_confirmed = sum(
        int(status_counts.get(key, 0))
        for key in ("confirmed_fukuoka_city", "confirmed_fukuoka_city_content")
    )
    lines = [
        "# 후쿠오카 분석 신뢰도 전수 감사",
        "",
        f"- 생성 시각: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- 결론: 현재 12.3%는 재현 가능한 **엄격 일치율 잠정치**다. "
        "연결된 10곳의 근거 정확도는 높아졌지만, MCP 카테고리 누락과 "
        "미등록 번역 별칭 때문에 후쿠오카 전체 시장의 최종 일치율로 쓰면 안 된다.",
        "",
        "## 1. 공식 장소 분모",
        "",
        f"- 요카나비 공식 장소 원본: {guide['catalog_rows']}건 / {guide['pages_fetched']}페이지",
        f"- 공식 한국어명이 확인된 장소: {guide['official_korean_names']}건",
        f"- 후쿠오카시·방문 관광지·한국어 발행 기준을 통과한 분모: {guide['accepted_rows']}곳",
        f"- 제외 보존: {guide['excluded_rows']}건",
        "- 분모 신뢰도: 높음. 원본·수용·제외 파일과 제외 사유가 모두 보존된다.",
        "- 범위 주의: 이 81곳은 `장소` 분모다. 공식 투어·체험 상품을 같은 "
        "분모에 섞지 않는다.",
        "",
        "## 2. 공식 체험 카탈로그 범위",
        "",
        f"- 요카나비 현재 공식 투어: 선언 {tours['declared_result_count']}건 / "
        f"수집 {tours['collected_result_count']}건",
        f"- 일정 텍스트 확보: {tours['rows_with_itinerary']}건",
        "- 공식 투어는 별도 비교군으로 저장했다. 외부 Jalan 예약 목록과 "
        "후쿠오카현 전체 체험 카탈로그는 아직 전수 비교하지 않았으므로, "
        "이번 12.3%에 포함하지 않는다.",
        "",
        "## 3. MCP 상품 완전성",
        "",
        f"- 후쿠오카 검색 반환 감사 풀: {details['deduplicated_fukuoka_products']}개",
        f"- 상세 원본 확보: {details['products_with_cached_payload']}개",
        f"- 파싱 가능한 상세: {details['products_with_usable_sections']}개",
        "- 파싱 불가 2개는 구형 `/offers/` 입장권이며, 상품 제목의 시설명은 "
        "입장권 직접 근거로만 사용한다.",
        f"- 과거 수집 오류 파일: {len(error_files)}개 "
        f"({', '.join(path.stem.replace('후쿠오카_', '') for path in error_files)})",
        "- 따라서 180은 후쿠오카시 상품 수가 아니라 검색 반환 감사 풀이다.",
        "",
        "## 4. 도시 혼입 감사",
        "",
        f"- 후쿠오카시 콘텐츠 확인: {city_confirmed}개",
        f"- 시외·광역 비투어 상품: {status_counts.get('outside_or_multi_region', 0)}개",
        f"- 도시 범위 판정 보류 투어: {status_counts.get('unresolved_tour_query_pool', 0)}개",
        f"- 비투어 42개 수동 범위 검토 완료: "
        f"{str(scope['non_tour_manual_review_complete']).lower()}",
        "- 하우스텐보스·하모니랜드·기타큐슈·나가사키·사가·야마구치·"
        "가고시마·히로시마 상품을 후쿠오카시 공급으로 세지 않는다.",
        "",
        "## 5. 장소×상품 연결 감사",
        "",
        f"- 기존 긍정 연결: {confidence['audited_place_product_links']}건",
        f"- 엄격 연결: {confidence['strict_links']}건 / "
        f"{confidence['strict_unique_products']}개 상품",
        f"- 분류: {confidence['connection_class_counts']}",
        f"- 엄격 연결 장소: {confidence['strict_matched_places']}/{confidence['official_place_denominator']}",
        f"- 엄격 일치율: {confidence['strict_match_rate_pct']:.1f}%",
        "- 일치율이 그대로인 이유: 옵션·상위 포함·단순 언급 6건을 내려도 "
        "해당 장소마다 다른 엄격 상품이 남아 장소 단위 분자는 10곳으로 유지된다.",
        "",
        "## 6. 거짓 음성 감사",
        "",
        f"- 공식명 직접 일치 미채택 후보: {false_negatives['exact_name_candidate_pairs']}쌍",
        f"- 수동 판정: {false_negatives['disposition_counts']}",
        f"- 미해결 직접 일치 후보: {false_negatives['unresolved_candidates']}건",
        "- 캐널시티의 상품 내 오기 `히카타`는 검토 별칭으로 추가해 장기 투어 "
        "2건을 연결했다. 반면 시카노시마 조망·연결 설명, 타워 주변 하차, "
        "대체 일정은 계속 제외한다.",
        "- 남은 한계: 공식명과 등록 별칭에 없는 번역은 이 감사로도 발견하지 못할 수 있다.",
        "",
        "## 7. MCP 장소 − 공식 81곳 역방향 리스트",
        "",
        f"- 수동 검토 장소 후보: {reverse_list['reviewed_place_candidates']}곳",
        f"- 확정 차집합: {reverse_list['list_status_counts'].get('included', 0)}곳",
        f"- 상위 여행지 기준 중복 제거 확정 차집합: {reverse_list['included_canonical_places']}곳",
        f"- 플랫폼 고유 가능성 추가 검토: {reverse_list['list_status_counts'].get('review_needed', 0)}곳",
        f"- 음식·중복·시외 등 제외: {reverse_list['list_status_counts'].get('excluded', 0)}곳",
        "- 확정 차집합도 일본어 공식 원본 또는 다른 공식 체험 카탈로그에 있는지 "
        "구분했으므로 곧바로 숨은 여행지라고 부르지 않는다.",
        "- 상세 목록: `exports/fukuoka_mcp_minus_official81_destinations.csv`",
        "",
        "## 8. 사용 가능한 결론과 금지되는 결론",
        "",
        "사용 가능:",
        "",
        "- 현재 공식 장소 81곳 중 적어도 10곳은 MCP 상품과 엄격하게 연결된다.",
        "- 연결된 10곳 안에서도 직접 입장권, 고정 투어 일정, 선택 옵션을 구분할 수 있다.",
        "- 미연결 71곳은 신규 상품 조사 후보군을 만드는 출발점으로 사용할 수 있다.",
        "",
        "아직 금지:",
        "",
        "- `후쿠오카 상품은 180개다`",
        "- `미연결 71곳에는 마이리얼트립 상품이 절대 없다`",
        "- `12.3%가 최종 시장 일치율이다`",
        "- `일치율이 낮으므로 수요가 높다`",
        "",
        "## 9. 다음 신뢰도 상승 조건",
        "",
        "1. 오류가 남은 MCP 카테고리 9개를 재수집한다.",
        "2. 도시 범위가 보류된 투어 126개의 실제 방문 도시를 구조화한다.",
        "3. 후쿠오카현 공식 체험과 외부 예약 카탈로그를 별도 분모로 전수 비교한다.",
        "4. 일본어·한국어 별칭 사전을 독립 검수 표본으로 평가한다.",
        "5. 내부 예약·전환 데이터가 있을 때만 수요 우선순위를 결합한다.",
        "",
        "## 감사 산출물",
        "",
        "- `audit/fukuoka_product_detail_inventory.csv`: 180개 상세 완전성",
        "- `audit/fukuoka_product_city_scope_audit.csv`: 도시 혼입",
        "- `audit/fukuoka_place_product_link_audit.csv`: 연결 강도",
        "- `audit/fukuoka_false_negative_candidate_audit.csv`: 미채택 직접 일치 후보",
        "- `exports/fukuoka_mcp_minus_official81_destinations.csv`: 역방향 장소 차집합과 제외 근거",
        "- `processed/accepted/fukuoka_official_tours.csv`: 공식 체험 11건",
    ]
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "report": str(REPORT.relative_to(ROOT)),
                "strict_match_rate_pct": confidence["strict_match_rate_pct"],
                "remaining_category_errors": len(error_files),
                "unresolved_tour_city_scope": status_counts.get(
                    "unresolved_tour_query_pool",
                    0,
                ),
            },
            ensure_ascii=False,
        )
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
