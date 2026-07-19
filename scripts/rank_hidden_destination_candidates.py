#!/usr/bin/env python3
"""Rank first-pass hidden destination candidates from official Kyoto place data.

This is an opportunity shortlist, not a popularity verdict. MCP collection is
incomplete, so zero product matches are treated only as a current-sample signal.
"""

from __future__ import annotations

import csv
import json
import re
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "official_tourism_sources" / "processed" / "accepted" / "kyoto_tourism_facilities_city_only.csv"
AUDIT = ROOT / "data" / "official_tourism_sources" / "reports" / "kyoto_facility_classification_audit.csv"
MATCHES = ROOT / "data" / "supply_gap_analysis" / "official_mcp_anchor_matches.csv"
OUT = ROOT / "data" / "supply_gap_analysis" / "opportunity"
REPORT = ROOT / "data" / "supply_gap_analysis" / "reports" / "KYOTO_HIDDEN_DESTINATION_CANDIDATES.md"


SELECTED = {
    "妙心寺 退蔵院": {
        "reason": "중요문화재 방장, 두 종류의 정원, 수금굴과 말차를 한 장소에서 경험할 수 있다.",
        "fit": "정원·말차·조용한 사찰을 선호하는 여행자",
    },
    "並河靖之七宝記念館": {
        "reason": "칠보 작품뿐 아니라 옛 공방·교마치야·오가와 지헤이의 정원을 함께 볼 수 있다.",
        "fit": "공예·건축·정원을 한 번에 보고 싶은 여행자",
    },
    "法金剛院": {
        "reason": "특별명승 정원에 연꽃·벚꽃·단풍이라는 계절 방문 이유가 겹친다.",
        "fit": "계절 꽃과 고전 정원을 좋아하는 여행자",
    },
    "地蔵院（竹の寺）": {
        "reason": "대나무숲, 이끼, 고산수 정원이 결합돼 아라시야마 대나무숲과 다른 조용한 대안이 된다.",
        "fit": "대나무와 이끼 풍경을 한적하게 즐기고 싶은 여행자",
    },
    "角屋もてなしの文化美術館": {
        "reason": "교토 유곽 문화의 아게야 건축 유일 유구와 요사 부손 작품, 장식 좌敷을 함께 공개한다.",
        "fit": "화려한 에도 건축과 교토 접객문화를 보고 싶은 여행자",
    },
    "大沢池": {
        "reason": "현존하는 일본 최고(最古) 인공 정원 연못으로 산책·벚꽃·단풍·달맞이 서사가 선명하다.",
        "fit": "사찰 내부보다 넓은 수변 산책을 선호하는 여행자",
    },
    "真如堂（真正極楽寺）": {
        "reason": "한적한 경내, 삼중탑, 두 정원과 단풍을 함께 갖췄지만 대표 투어 제목에는 잡히지 않았다.",
        "fit": "유명 단풍 명소의 혼잡을 피하고 싶은 여행자",
    },
    "瑞峯院": {
        "reason": "시게모리 미레이의 독좌정·한면정과 십자가 석조라는 뚜렷한 정원 스토리가 있다.",
        "fit": "현대적 해석이 들어간 고산수 정원을 좋아하는 여행자",
    },
    "圓通寺": {
        "reason": "이끼 낀 고산수 너머로 히에이산을 끌어들이는 차경 자체가 독립 방문 목적이 된다.",
        "fit": "조용히 앉아 한 장면을 오래 감상하는 여행자",
    },
    "正伝寺": {
        "reason": "후시미성 혈천장과 히에이산 차경, 7·5·3 철쭉 배치 정원이 한곳에 있다.",
        "fit": "정원과 역사적 서사가 함께 있는 소규모 사찰을 찾는 여행자",
    },
    "光明院": {
        "reason": "‘무지개 이끼 절’로 불리는 이끼와 백사, 삼존석의 조합이 시각적으로 뚜렷하다.",
        "fit": "사진보다 현장 분위기와 이끼 정원을 중시하는 여행자",
    },
    "重森三玲邸庭園美術館": {
        "reason": "정원가 시게모리 미레이가 자기 집에 설계한 힘 있는 석조 고산수를 실내 시점에서 감상한다.",
        "fit": "정원 디자인과 근현대 건축에 관심 있는 여행자",
    },
}

# Product titles can omit the exact sub-place even when the supplied admission
# ticket covers it. Keep manually verified links here so incomplete MCP title
# matching cannot incorrectly promote those places as hidden opportunities.
VERIFIED_EXISTING_MRT_SUPPLY = {
    "妙心寺 退蔵院": [
        {
            "product_id": "5869394",
            "product_title": "교토 묘신지 템플 관람 & 하나고코로 런치 플랜",
            "product_url": "https://experiences.myrealtrip.com/products/5869394",
            "evidence": (
                "MRT title abbreviates the place to 묘신지, while the same "
                "하나고코로 관람권·점심 구성 is supplied as 退蔵院拝観."
            ),
        }
    ]
}


POSITIVE_SIGNALS = (
    ("official_designation", r"国宝|重要文化財|特別名勝|名勝|史跡|天然記念物|伝統的建造物群", 3.0, 2),
    ("distinctiveness", r"日本唯一|日本最古|京都最古|唯一|最古|三大|発祥|屈指", 2.5, 2),
    ("landscape", r"庭園|紅葉|桜|絶景|眺望|夜景|竹林|滝|池泉|枯山水|借景|渓谷|峡谷|苔", 1.5, 3),
    ("visitable_experience", r"体験|散策|見学|拝観|公開|展示|観賞|鑑賞|ハイキング", 1.0, 2),
    ("culture", r"建築|美術|工芸|伝統|舞妓|芸妓|茶道|能|歌舞伎", 0.8, 2),
)

MAINSTREAM_SIGNALS = (
    ("world_heritage", r"世界(?:文化)?遺産", 4.0),
    ("explicit_fame", r"有名|名高|知られる|代表する|人気|賑わ|シンボル|観光客", 2.0),
    ("major_head_temple", r"総本山|大本山", 1.0),
)


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def score(row: dict[str, str]) -> tuple[float, list[str], list[str]]:
    text = " ".join(clean(row.get(key)) for key in ["名称", "説明", "備考"])
    total = 0.0
    positive = []
    penalties = []
    for label, pattern, weight, cap in POSITIVE_SIGNALS:
        count = min(len(re.findall(pattern, text)), cap)
        if count:
            total += count * weight
            positive.append(f"{label}:{count}")
    for label, pattern, weight in MAINSTREAM_SIGNALS:
        count = min(len(re.findall(pattern, text)), 2)
        if count:
            total -= count * weight
            penalties.append(f"{label}:{count}")
    if clean(row.get("URL")):
        total += 0.5
        positive.append("official_url")
    if clean(row.get("アクセス方法")):
        total += 0.8
        positive.append("access_info")
    if clean(row.get("緯度")) and clean(row.get("経度")):
        total += 0.4
        positive.append("coordinates")
    if re.search(r"休館|休止|非公開|一般拝観.*不可|要予約", text):
        total -= 1.5
        penalties.append("access_restriction")
    return round(total, 1), positive, penalties


def has_verified_mrt_supply(official_name: str) -> bool:
    return bool(VERIFIED_EXISTING_MRT_SUPPLY.get(clean(official_name)))


def main() -> int:
    audit = {
        row["source_record_id"]: row
        for row in read_csv(AUDIT)
        if row["disposition"] == "primary"
    }
    matched_counts: dict[str, int] = {}
    for row in read_csv(MATCHES):
        if row["city_id"] != "jp-kyoto":
            continue
        matched_counts[row["anchor_id"]] = matched_counts.get(row["anchor_id"], 0) + 1

    candidates = []
    excluded_verified_supply = []
    for row in read_csv(RAW):
        official_name = clean(row.get("名称"))
        if official_name not in SELECTED:
            continue
        audit_row = audit.get(clean(row.get("NO")))
        if not audit_row:
            continue
        anchor_id = f"official-kyoto-facility-{clean(row.get('NO'))}"
        if has_verified_mrt_supply(official_name):
            excluded_verified_supply.append(
                {
                    "anchor_id": anchor_id,
                    "name_ko": audit_row["name_ko"],
                    "name_ja": official_name,
                    "verified_products": VERIFIED_EXISTING_MRT_SUPPLY[official_name],
                    "exclusion_reason": "MRT 상품 공급을 직접 확인해 숨은 여행지 후보에서 제외",
                }
            )
            continue
        value_score, positive, penalties = score(row)
        editorial = SELECTED[official_name]
        candidates.append(
            {
                "anchor_id": anchor_id,
                "name_ko": audit_row["name_ko"],
                "name_ja": official_name,
                "category": audit_row["classification"],
                "official_value_score": value_score,
                "positive_signals": positive,
                "mainstream_or_access_penalties": penalties,
                "current_mcp_title_match_count": matched_counts.get(anchor_id, 0),
                "selection_reason_ko": editorial["reason"],
                "traveler_fit_ko": editorial["fit"],
                "official_description_ja": clean(row.get("説明")),
                "access_ja": clean(row.get("アクセス方法")),
                "official_url": clean(row.get("URL")),
                "translation_status": audit_row["translation_status"],
                "underexposure_status": "현재 MCP 표본 미노출 후보",
                "confidence_note": "MCP 수집이 429로 중단되어 실제 미공급 확정 불가",
            }
        )

    candidates.sort(
        key=lambda row: (
            row["current_mcp_title_match_count"] == 0,
            row["official_value_score"],
        ),
        reverse=True,
    )
    for rank, row in enumerate(candidates, start=1):
        row["rank"] = rank

    OUT.mkdir(parents=True, exist_ok=True)
    REPORT.parent.mkdir(parents=True, exist_ok=True)
    (OUT / "kyoto_hidden_destination_candidates.json").write_text(
        json.dumps(candidates, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    (OUT / "kyoto_hidden_candidate_verified_exclusions.json").write_text(
        json.dumps(excluded_verified_supply, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )

    lines = [
        "# 교토 숨은 여행지 후보",
        "",
        f"- 생성 시각: {datetime.now().astimezone().isoformat(timespec='seconds')}",
        f"- 후보 수: {len(candidates)}",
        "- 정의: 공식 관광가치 근거가 있고 현재 수집된 MRT 상품 제목에는 직접 등장하지 않는 장소",
        "- 주의: 교토 MCP 수집이 429로 중단됐으므로 `미노출 후보`이지 `MRT 미공급 확정`이 아님",
        "- 대표 세계유산과 이미 MRT 제목에 반복 등장한 장소는 편집 단계에서 제외",
        f"- 직접 상품 검증으로 후보에서 추가 제외: {len(excluded_verified_supply)}곳",
        "",
        "| 순위 | 한국어명 | 일본어명 | 공식가치 점수 | 현재 MRT 제목 연결 | 핵심 방문 이유 |",
        "|---:|---|---|---:|---:|---|",
    ]
    for row in candidates:
        lines.append(
            f"| {row['rank']} | {row['name_ko']} | {row['name_ja']} | "
            f"{row['official_value_score']:.1f} | {row['current_mcp_title_match_count']} | "
            f"{row['selection_reason_ko']} |"
        )
    lines.extend(
        [
            "",
            "## 직접 확인 후 제외한 장소",
            "",
        ]
    )
    for row in excluded_verified_supply:
        for product in row["verified_products"]:
            lines.append(
                f"- {row['name_ko']} / {row['name_ja']}: "
                f"[{product['product_title']}]({product['product_url']})"
            )
    lines.extend(
        [
            "",
            "## 해석",
            "",
            "- 점수는 문화재·명승·희소성·경관·체험·접근성의 공식 설명 신호에서 계산했다.",
            "- 유명하다는 직접 표현, 세계유산, 총본산 표기는 숨은 선택지 점수에서 감점했다.",
            "- 실제 노출 부족 확정에는 MCP 전체 재수집과 투어 상세 일정 검증이 추가로 필요하다.",
        ]
    )
    REPORT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"candidate_count": len(candidates), "report": str(REPORT.relative_to(ROOT))}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
