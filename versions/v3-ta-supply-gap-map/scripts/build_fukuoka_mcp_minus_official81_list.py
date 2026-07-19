#!/usr/bin/env python3
"""Build the reviewed Fukuoka MCP-place minus official-81 destination list.

The two sides use different units: MCP contains products while the official
denominator contains places.  This report therefore uses a small, explicit
human-reviewed place registry.  It preserves broader-official matches and
rejections instead of calling every unmatched product a hidden destination.
"""

from __future__ import annotations

import csv
import json
from collections import Counter
from dataclasses import asdict, dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PRODUCTS = (
    ROOT
    / "data"
    / "mcp_tna_products"
    / "processed"
    / "후쿠오카_mcp_tna_products.csv"
)
OFFICIAL_81 = (
    ROOT
    / "data"
    / "official_tourism_sources"
    / "processed"
    / "accepted"
    / "fukuoka_official_guide_places.csv"
)
OUT_CSV = (
    ROOT
    / "data"
    / "supply_gap_analysis"
    / "exports"
    / "fukuoka_mcp_minus_official81_destinations.csv"
)
OUT_REPORT = (
    ROOT
    / "data"
    / "supply_gap_analysis"
    / "reports"
    / "FUKUOKA_MCP_MINUS_OFFICIAL81_DESTINATIONS.md"
)
OUT_SUMMARY = (
    ROOT
    / "data"
    / "supply_gap_analysis"
    / "reports"
    / "fukuoka_mcp_minus_official81_summary.json"
)


@dataclass(frozen=True)
class Candidate:
    name_ko: str
    name_ja: str
    product_ids: str
    evidence_type: str
    evidence_excerpt: str
    city_scope: str
    official_81_status: str
    broader_official_status: str
    broader_official_reference: str
    final_bucket: str
    list_status: str
    decision_reason: str


CANDIDATES = [
    Candidate(
        "팀랩 포레스트 후쿠오카",
        "チームラボフォレスト 福岡",
        "5869396|5869541",
        "direct_ticket",
        "팀랩 포레스트 후쿠오카 입장권",
        "후쿠오카시",
        "not_in_81",
        "official_japanese_spot_exact",
        "https://yokanavi.com/spots/257499",
        "official_raw_not_in_81",
        "included",
        "한국어 공식 가이드 미발행으로 81곳에서는 빠졌지만 일본어 공식 관광지 원본에 직접 존재",
    ),
    Candidate(
        "산리오 캐릭터즈 드리밍파크",
        "Sanrio characters Dream!ng Park",
        "5869542",
        "direct_ticket",
        "산리오 캐릭터즈 드리밍파크 입장권",
        "후쿠오카시",
        "not_in_81",
        "official_japanese_spot_exact",
        "https://yokanavi.com/spots/257391",
        "official_raw_not_in_81",
        "included",
        "한국어 공식 가이드 미발행으로 81곳에서는 빠졌지만 일본어 공식 관광지 원본에 직접 존재",
    ),
    Candidate(
        "카와바타 상점가",
        "川端通商店街",
        "3841906|4298416",
        "confirmed_scheduled_visit",
        "카와바타 상점가·가와바타 쇼핑 아케이드 산책",
        "후쿠오카시",
        "not_in_81",
        "official_korean_spot_non_primary_and_official_tour",
        "https://yokanavi.com/spots/27148",
        "official_raw_not_in_81",
        "included",
        "공식 관광지 원본과 공식 도보투어에 있으나 분모 필터에서 비주요 카테고리로 제외",
    ),
    Candidate(
        "마이즈루 공원",
        "舞鶴公園",
        "5735236",
        "confirmed_scheduled_visit",
        "후쿠오카성터 & 마이즈루 공원",
        "후쿠오카시",
        "not_in_81",
        "official_japanese_spot_exact",
        "https://yokanavi.com/spots/26832",
        "official_raw_not_in_81",
        "included",
        "후쿠오카 성터와 인접하지만 별도 공원이며 일본어 공식 관광지 원본에 직접 존재",
    ),
    Candidate(
        "나카스 리버 야카타부네 디너 크루즈",
        "中洲リバー屋形船ディナークルーズ",
        "5505188|5051632",
        "direct_experience",
        "나카스 리버 야카타부네 디너 크루즈",
        "후쿠오카시",
        "not_in_81",
        "official_city_tour_family",
        "https://yokanavi.com/tours/273923",
        "official_other_catalog_not_in_81",
        "included",
        "관광지 spots 81곳에는 없지만 후쿠오카시 공식 투어 카탈로그에 야카타부네 체험이 존재",
    ),
    Candidate(
        "나카가와 리버 크루즈",
        "那珂川リバークルーズ",
        "5869386",
        "direct_experience",
        "나카가와 리버 크루즈",
        "후쿠오카시",
        "not_in_81",
        "official_prefecture_experience_exact",
        "https://www.crossroadfukuoka.jp/kr/experience/11452",
        "official_other_catalog_not_in_81",
        "included",
        "후쿠오카현 공식 체험 카탈로그에 나카가와 수상버스 경험이 직접 존재",
    ),
    Candidate(
        "하카타강 래프팅 크루즈",
        "博多川ラフティングクルーズ",
        "5024120",
        "direct_experience",
        "하카타 강 래프팅 크루즈",
        "후쿠오카시",
        "not_in_81",
        "official_prefecture_experience_family",
        "https://www.crossroadfukuoka.jp/kr/experience/11452",
        "official_other_catalog_not_in_81",
        "included",
        "공식 현 체험의 하카타·나카스 수상버스 경험군과 대응하나 동일 운영사 여부는 미확인",
    ),
    Candidate(
        "라라포트 후쿠오카",
        "三井ショッピングパーク ららぽーと福岡",
        "4944164|4944183",
        "confirmed_scheduled_visit",
        "라라포트 후쿠오카 40분 방문",
        "후쿠오카시",
        "not_in_81",
        "not_found_as_independent_official_spot",
        "https://experiences.myrealtrip.com/products/4944164",
        "platform_only_review_candidate",
        "review_needed",
        "두 MCP 일정에서 방문하지만 상업시설이며 공식 81곳의 후쿠오카 장난감 미술관을 포함하는 상위 시설",
    ),
    Candidate(
        "신텐초 상점가",
        "新天町商店街",
        "6057583",
        "direct_activity_location",
        "신텐초 상점가 기모노 산책",
        "후쿠오카시",
        "not_in_81",
        "not_found_in_collected_official_catalogs",
        "https://experiences.myrealtrip.com/products/6057583",
        "platform_only_review_candidate",
        "review_needed",
        "MCP 체험의 직접 장소이나 수집한 공식 장소·투어 카탈로그에서 독립 관광지로 확인되지 않음",
    ),
    Candidate(
        "나카스 야타이 거리",
        "中洲屋台街",
        "3885344|3841906|4298416",
        "food_experience",
        "포장마차 거리·나카스 야타이",
        "후쿠오카시",
        "not_in_81",
        "district_food_culture",
        "https://yokanavi.com/yatai",
        "excluded_foodplace",
        "excluded",
        "이번 분석은 관광 장소 중심이며 야타이·개별 식당 계열은 별도 음식 분석으로 분리",
    ),
    Candidate(
        "카와바타 젠자이 광장",
        "川端ぜんざい広場",
        "4298416",
        "food_stop",
        "가와바타 젠자이 히로바에서 젠자이 시식",
        "후쿠오카시",
        "not_in_81",
        "contained_in_kawabata_shopping_arcade",
        "https://yokanavi.com/spots/27148",
        "excluded_foodplace_or_child",
        "excluded",
        "음식 시식 장소이며 카와바타 상점가의 하위 장소이므로 독립 관광지로 중복 집계하지 않음",
    ),
    Candidate(
        "CLUB Rebellion",
        "CLUB Rebellion",
        "6057611",
        "private_nightlife_experience",
        "나카스의 사적 호스트클럽 체험",
        "후쿠오카시",
        "not_in_81",
        "not_found_as_official_spot",
        "https://experiences.myrealtrip.com/products/6057611",
        "excluded_private_nightlife",
        "excluded",
        "플랫폼 고유 민간 콘텐츠이지만 일반 관광지 발굴 목록과 성격이 달라 별도 검토",
    ),
    Candidate(
        "코로나 온천",
        "コロナの湯 小倉店",
        "5542371",
        "direct_ticket",
        "상세 주소: 기타큐슈시 고쿠라키타구",
        "기타큐슈시",
        "not_applicable",
        "outside_fukuoka_city",
        "https://experiences.myrealtrip.com/products/5542371",
        "excluded_outside_city",
        "excluded",
        "후쿠오카 검색에 반환됐지만 실제 장소는 기타큐슈시",
    ),
    Candidate(
        "가요이초 공원",
        "駕与丁公園",
        "5896489",
        "confirmed_scheduled_visit",
        "가요이초 공원 80분 방문",
        "가스야정",
        "not_applicable",
        "outside_fukuoka_city",
        "https://experiences.myrealtrip.com/products/5896489",
        "excluded_outside_city",
        "excluded",
        "후쿠오카 검색에 반환됐지만 실제 장소는 가스야정",
    ),
]


FIELDS = [
    "name_ko",
    "name_ja",
    "canonical_place_ko",
    "canonical_place_ja",
    "canonical_group_id",
    "product_ids",
    "product_count",
    "product_urls",
    "evidence_type",
    "evidence_excerpt",
    "city_scope",
    "official_81_status",
    "broader_official_status",
    "broader_official_reference",
    "final_bucket",
    "list_status",
    "decision_reason",
]

CANONICAL_GROUPS = {
    "팀랩 포레스트 후쿠오카": (
        "BOSS E・ZO FUKUOKA",
        "BOSS E・ZO FUKUOKA",
        "boss-ezo-fukuoka",
    ),
    "산리오 캐릭터즈 드리밍파크": (
        "BOSS E・ZO FUKUOKA",
        "BOSS E・ZO FUKUOKA",
        "boss-ezo-fukuoka",
    ),
    "나카스 리버 야카타부네 디너 크루즈": (
        "나카스 수변 권역",
        "中洲リバーフロント",
        "nakasu-riverfront",
    ),
    "나카가와 리버 크루즈": (
        "나카스 수변 권역",
        "中洲リバーフロント",
        "nakasu-riverfront",
    ),
    "하카타강 래프팅 크루즈": (
        "나카스 수변 권역",
        "中洲リバーフロント",
        "nakasu-riverfront",
    ),
}


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def enriched_rows() -> list[dict[str, str | int]]:
    product_inventory = {
        row["product_id"]: row for row in read_csv(PRODUCTS) if row.get("product_id")
    }
    official_names = {
        row["name_ko"].strip() for row in read_csv(OFFICIAL_81) if row.get("name_ko")
    }
    rows: list[dict[str, str | int]] = []
    for candidate in CANDIDATES:
        product_ids = [value for value in candidate.product_ids.split("|") if value]
        missing = [value for value in product_ids if value not in product_inventory]
        if missing:
            raise ValueError(f"{candidate.name_ko}: unknown MCP product IDs {missing}")
        if candidate.list_status != "excluded" and candidate.name_ko in official_names:
            raise ValueError(f"{candidate.name_ko}: already exists in official 81")
        row = asdict(candidate)
        canonical = CANONICAL_GROUPS.get(
            candidate.name_ko,
            (
                candidate.name_ko,
                candidate.name_ja,
                candidate.name_ko.lower().replace(" ", "-"),
            ),
        )
        row["canonical_place_ko"] = canonical[0]
        row["canonical_place_ja"] = canonical[1]
        row["canonical_group_id"] = canonical[2]
        row["product_count"] = len(product_ids)
        row["product_urls"] = "|".join(
            product_inventory[value].get("product_url")
            or f"https://experiences.myrealtrip.com/products/{value}"
            for value in product_ids
        )
        rows.append(row)
    return rows


def write_csv(rows: list[dict[str, str | int]]) -> None:
    OUT_CSV.parent.mkdir(parents=True, exist_ok=True)
    with OUT_CSV.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def markdown_table(rows: list[dict[str, str | int]]) -> list[str]:
    lines = [
        "| 장소(한국어 / 일본어) | MCP 상품 | 공식 데이터 관계 | 판정 |",
        "|---|---:|---|---|",
    ]
    for row in rows:
        product_links = []
        for product_id, url in zip(
            str(row["product_ids"]).split("|"),
            str(row["product_urls"]).split("|"),
        ):
            product_links.append(f"[{product_id}]({url})")
        lines.append(
            f"| {row['name_ko']} / {row['name_ja']} "
            f"| {', '.join(product_links)} "
            f"| {row['broader_official_status']} "
            f"| {row['decision_reason']} |"
        )
    return lines


def write_report(rows: list[dict[str, str | int]]) -> None:
    included = [row for row in rows if row["list_status"] == "included"]
    review = [row for row in rows if row["list_status"] == "review_needed"]
    excluded = [row for row in rows if row["list_status"] == "excluded"]
    official_raw = [
        row for row in included if row["final_bucket"] == "official_raw_not_in_81"
    ]
    other_catalog = [
        row
        for row in included
        if row["final_bucket"] == "official_other_catalog_not_in_81"
    ]
    included_groups: dict[str, list[dict[str, str | int]]] = {}
    for row in included:
        included_groups.setdefault(str(row["canonical_group_id"]), []).append(row)
    review_groups = {
        str(row["canonical_group_id"]) for row in review
    }
    canonical_lines = [
        "| 중복 제거 여행지 | 묶인 세부 장소·경험 | 연결 상품 수 |",
        "|---|---|---:|",
    ]
    for grouped_rows in included_groups.values():
        product_ids = {
            product_id
            for row in grouped_rows
            for product_id in str(row["product_ids"]).split("|")
            if product_id
        }
        canonical_lines.append(
            f"| {grouped_rows[0]['canonical_place_ko']} / "
            f"{grouped_rows[0]['canonical_place_ja']} "
            f"| {', '.join(str(row['name_ko']) for row in grouped_rows)} "
            f"| {len(product_ids)} |"
        )
    lines = [
        "# 후쿠오카 MCP 장소 − 공식 관광지 81곳 리스트",
        "",
        f"- 생성 시각: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        "- 비교 단위: MCP 상품이 아니라 상품 제목·상세·고정 일정에서 확인된 **장소**",
        f"- 확정 목록: {len(included)}곳",
        f"- 상위 여행지 기준 중복 제거 확정 목록: {len(included_groups)}곳",
        f"- 플랫폼 고유 가능성 추가 검토: {len(review)}곳",
        f"- 추가 검토까지 포함한 중복 제거 목록: {len(included_groups) + len(review_groups)}곳",
        f"- 음식·중복·시외 등 제외 기록: {len(excluded)}곳",
        "",
        "## 먼저 읽을 결론",
        "",
        f"`180개 MCP 상품 − 81개 공식 장소 = 99개`가 아니다. 상품과 장소는 단위가 다르다. "
        f"현재 직접 근거를 수동 검토한 결과, 공식 81곳에는 없지만 장소로 유지할 수 있는 항목은 "
        f"{len(included)}곳이다. 이 중 {len(official_raw)}곳은 일본어 공식 원본 등에 이미 있고, "
        f"{len(other_catalog)}곳은 공식 투어·체험 카탈로그에 있다. 따라서 이 {len(included)}곳을 "
        "모두 '마이리얼트립이 새로 발견한 숨은 여행지'라고 부르면 안 된다.",
        "",
        "## 상위 여행지 기준 중복 제거 결과",
        "",
        *canonical_lines,
        "",
        "팀랩과 산리오는 서로 다른 유료 체험이지만 같은 복합시설 안에 있으므로 "
        "`여행지`를 세는 표에서는 BOSS E・ZO FUKUOKA 1곳으로 묶었다. 세 크루즈도 "
        "상품 방식은 다르지만 나카스의 나카가와·하카타강 수변을 이용하므로 나카스 "
        "수변 권역 1곳으로 묶었다. 사용자가 실제로 선택하는 체험 화면에서는 다시 "
        "세부 항목으로 펼칠 수 있다.",
        "",
        "## A. 일본어 공식 원본에는 있으나 공식 81곳에는 없는 장소",
        "",
        *markdown_table(official_raw),
        "",
        "## B. 관광지 81곳이 아닌 다른 공식 투어·체험 카탈로그에 있는 장소·경험",
        "",
        *markdown_table(other_catalog),
        "",
        "## C. 현재 MCP에서만 확인되어 공식 교차검증이 더 필요한 후보",
        "",
        *markdown_table(review),
        "",
        "이 두 곳은 곧바로 숨은 여행지로 확정하지 않는다. 상업시설·상점가라는 성격과 "
        "공식 데이터 수집 범위 밖에 존재할 가능성을 추가 검증해야 한다.",
        "",
        "## D. 후보에서 제외했지만 감사 추적을 위해 남긴 항목",
        "",
        *markdown_table(excluded),
        "",
        "## 해석 원칙",
        "",
        "1. `included`는 공식 81곳과의 차집합이라는 뜻이지, 모든 공식 관광 데이터에 없다는 뜻이 아니다.",
        "2. `review_needed`만 플랫폼 고유 후보로 볼 여지가 있으며, 이조차 공식 원본 범위와 관광지성을 추가 확인한다.",
        "3. 야타이·식당은 이번 관광지 분석에서 제외하고 별도 음식 분석으로 분리한다.",
        "4. 집결지·하차·할인쿠폰·주변 언급·선택 옵션은 방문 장소로 세지 않는다.",
        "5. 후쿠오카 검색 결과에 섞인 기타큐슈·가스야 등 후쿠오카시 밖 장소는 제외한다.",
        "",
        "행 단위 근거와 공식 URL·MCP 상품 URL은 "
        "`data/supply_gap_analysis/exports/fukuoka_mcp_minus_official81_destinations.csv`에 보존한다.",
        "",
        "## 남은 한계",
        "",
        "후쿠오카 검색 풀 180개 중 도시 범위가 아직 보류된 투어 126개가 있으므로 이 목록은 "
        "**검증 완료 후보 목록**이지 전체 MCP 장소 추출의 완결판은 아니다. 126개 투어의 방문 도시와 "
        "고정 일정을 모두 구조화하면 후보가 추가되거나 기존 후보의 근거 상품 수가 늘 수 있다.",
        "",
    ]
    OUT_REPORT.parent.mkdir(parents=True, exist_ok=True)
    OUT_REPORT.write_text("\n".join(lines), encoding="utf-8")


def write_summary(rows: list[dict[str, str | int]]) -> None:
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "mcp_search_pool_products": len(read_csv(PRODUCTS)),
        "official_denominator_places": len(read_csv(OFFICIAL_81)),
        "reviewed_place_candidates": len(rows),
        "list_status_counts": dict(Counter(str(row["list_status"]) for row in rows)),
        "final_bucket_counts": dict(Counter(str(row["final_bucket"]) for row in rows)),
        "included_detail_places": sum(row["list_status"] == "included" for row in rows),
        "included_canonical_places": len(
            {
                str(row["canonical_group_id"])
                for row in rows
                if row["list_status"] == "included"
            }
        ),
        "included_and_review_canonical_places": len(
            {
                str(row["canonical_group_id"])
                for row in rows
                if row["list_status"] in {"included", "review_needed"}
            }
        ),
        "important_caveat": "products and places are different units; 180 minus 81 is invalid",
        "csv": str(OUT_CSV.relative_to(ROOT)),
        "report": str(OUT_REPORT.relative_to(ROOT)),
    }
    OUT_SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False))


def main() -> int:
    rows = enriched_rows()
    write_csv(rows)
    write_report(rows)
    write_summary(rows)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
