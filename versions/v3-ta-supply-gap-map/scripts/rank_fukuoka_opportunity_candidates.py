#!/usr/bin/env python3
"""Build a reviewed Fukuoka T&A product-development opportunity shortlist.

The shortlist combines official place evidence with current confirmed MRT
place-product links. It ranks validation opportunities, not customer demand.
"""

from __future__ import annotations

import csv
import json
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
ANCHORS = (
    ROOT
    / "data"
    / "official_tourism_sources"
    / "anchors"
    / "official_experience_anchors.csv"
)
MATCHES = ROOT / "data" / "supply_gap_analysis" / "official_mcp_anchor_matches.csv"
OUT = ROOT / "data" / "supply_gap_analysis" / "opportunity"
REPORT = (
    ROOT
    / "data"
    / "supply_gap_analysis"
    / "reports"
    / "FUKUOKA_PRODUCT_OPPORTUNITY_CANDIDATES.md"
)

CANDIDATES = [
    {
        "rank": 1,
        "name": "시카노시마·긴인 공원",
        "anchor_ids": [
            "official-fukuoka-guide-27159",
            "official-fukuoka-guide-26826",
        ],
        "opportunity_type": "new_route",
        "reason": "바다·고대 교류사·해산물이라는 서로 다른 방문 이유가 한 권역에 있고, 기존 우미노나카미치 공급과 연결해 코스를 확장할 수 있다.",
        "concept": "우미노나카미치 → 시카노시마 → 긴인 공원 → 해산물 → 일몰",
    },
    {
        "rank": 2,
        "name": "ABURAYAMA FUKUOKA",
        "anchor_ids": ["official-fukuoka-guide-26804"],
        "opportunity_type": "new_half_day_product",
        "reason": "도심 근교에서 자연·목장·식음·어드벤처를 한 번에 구성할 수 있어 가족·커플 반일 상품 가설이 선명하다.",
        "concept": "도심 왕복 이동 + 목장·자연 체험 + 식음 또는 어드벤처 옵션",
    },
    {
        "rank": 3,
        "name": "하카타 전통공예·전통예능",
        "anchor_ids": [
            "official-fukuoka-guide-27178",
            "official-fukuoka-guide-119804",
        ],
        "opportunity_type": "partner_experience",
        "reason": "시설 관람보다 하카타오리·하카타인형·전통공연을 예약 가능한 체험으로 전환할 여지가 있다.",
        "concept": "구시다신사·하카타 옛 거리 + 공예 체험 + 공연일 지정 전통예능",
    },
    {
        "rank": 4,
        "name": "후쿠오카 장난감 미술관",
        "anchor_ids": ["official-fukuoka-guide-235901"],
        "opportunity_type": "family_experience",
        "reason": "라라포트 안의 체험형 가족 시설로, 입장과 워크숍을 결합한 부모·아동 상품을 검토할 수 있다.",
        "concept": "장난감 미술관 입장 + 목육 워크숍 + 라라포트 자유시간",
    },
    {
        "rank": 5,
        "name": "후쿠오카시 미술관·쇼후엔",
        "anchor_ids": [
            "official-fukuoka-guide-26815",
            "official-fukuoka-guide-27157",
        ],
        "opportunity_type": "quiet_city_theme",
        "reason": "공급이 확인된 오호리공원 주변을 미술·정원·다도 테마로 확장해 도심의 조용한 대안을 만들 수 있다.",
        "concept": "오호리공원 → 후쿠오카시 미술관 → 쇼후엔 정원·다도",
    },
    {
        "rank": 6,
        "name": "노코노시마",
        "anchor_ids": ["official-fukuoka-guide-26970"],
        "opportunity_type": "expand_existing_supply",
        "reason": "실제 방문 투어가 확인됐지만 현재 연결 상품이 1개뿐이라 신규 발굴이 아니라 공급 확대 후보로 분류한다.",
        "concept": "계절 꽃·섬 체류 시간을 명시한 정규 소그룹 또는 페리 결합 상품",
    },
]


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def main() -> int:
    anchors = {row["anchor_id"]: row for row in read_csv(ANCHORS)}
    matches_by_anchor: dict[str, list[dict[str, str]]] = {}
    for row in read_csv(MATCHES):
        matches_by_anchor.setdefault(row["anchor_id"], []).append(row)

    output_rows = []
    errors = []
    for candidate in CANDIDATES:
        candidate_anchors = []
        product_ids: set[str] = set()
        product_titles: set[str] = set()
        for anchor_id in candidate["anchor_ids"]:
            anchor = anchors.get(anchor_id)
            if not anchor:
                errors.append(f"{candidate['name']}: missing anchor {anchor_id}")
                continue
            candidate_anchors.append(
                {
                    "anchor_id": anchor_id,
                    "name_ja": anchor.get("anchor_name_local", ""),
                    "name_ko": anchor.get("anchor_name_ko", ""),
                    "official_url": anchor.get("source_url", ""),
                }
            )
            for match in matches_by_anchor.get(anchor_id, []):
                if match.get("evidence_level") == "tour_title_needs_detail":
                    continue
                product_ids.add(match.get("product_id", ""))
                product_titles.add(match.get("product_title", ""))
        output_rows.append(
            {
                **candidate,
                "official_places": candidate_anchors,
                "confirmed_mcp_product_count": len(product_ids),
                "confirmed_product_ids": sorted(value for value in product_ids if value),
                "confirmed_product_titles": sorted(value for value in product_titles if value),
                "demand_status": "unvalidated",
                "decision_status": (
                    "existing_supply_expansion"
                    if candidate["opportunity_type"] == "expand_existing_supply"
                    else "bd_validation_candidate"
                ),
            }
        )

    OUT.mkdir(parents=True, exist_ok=True)
    OUT_JSON = OUT / "fukuoka_product_opportunity_candidates.json"
    OUT_JSON.write_text(
        json.dumps(output_rows, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# 후쿠오카 상품개발 기회 후보",
        "",
        f"- 생성 시각: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 후보: {len(output_rows)}개",
        "- 정의: 공식 관광 근거와 현재 확인된 MCP 공급 차이를 이용해 만든 BD 검증 우선순위",
        "- 주의: 이 순위는 수요·예약 가능성을 증명하지 않으며, 내부 고객행동·가격·운영 가능성 검증 전 상품 출시 결론으로 사용하지 않는다.",
        "",
        "| 순위 | 후보 | 유형 | 확인 상품 | 개발 가설 |",
        "|---:|---|---|---:|---|",
    ]
    for row in output_rows:
        lines.append(
            f"| {row['rank']} | {row['name']} | {row['opportunity_type']} | "
            f"{row['confirmed_mcp_product_count']} | {row['concept']} |"
        )
    lines.extend(
        [
            "",
            "## 해석",
            "",
            "- `확인 상품 0`은 현재 수집·매칭 범위의 미확인을 뜻하며 절대적인 미공급이 아니다.",
            "- 시카노시마처럼 연결·조망 설명에만 등장한 장소는 방문 공급으로 세지 않는다.",
            "- 노코노시마는 상세 일정에서 실제 방문이 확인됐으므로 숨은 여행지가 아니라 기존 공급 확대 후보로 분리한다.",
            "- 다음 검증은 이동시간, 영업일, 단체 수용, 한국어 운영, 파트너 의향, 예상 가격과 내부 수요 데이터 순서로 진행한다.",
        ]
    )
    if errors:
        lines.extend(["", "## 데이터 오류", "", *[f"- {error}" for error in errors]])
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(
        json.dumps(
            {
                "status": "passed" if not errors else "failed",
                "candidate_count": len(output_rows),
                "errors": errors,
                "report": str(REPORT.relative_to(ROOT)),
            },
            ensure_ascii=False,
        )
    )
    return 0 if not errors else 1


if __name__ == "__main__":
    raise SystemExit(main())
