#!/usr/bin/env python3
"""Match positive tour-detail sections to reviewed official tourism places."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter, defaultdict
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
SECTIONS = ANALYSIS / "tour_details" / "tour_detail_sections.csv"
PUBLIC_SLOTS = ANALYSIS / "tour_details" / "public_itinerary_slots.csv"
AUTO_ALIASES = ANALYSIS / "auto_anchor_alias_candidates.csv"
OUT = ANALYSIS / "tour_details" / "tour_detail_official_place_matches.csv"
NEGATIVE_OUT = ANALYSIS / "tour_details" / "tour_detail_negative_place_mentions.csv"
SUMMARY_OUT = ANALYSIS / "tour_details" / "tour_detail_place_match_summary.json"
REPORT_OUT = ANALYSIS / "reports" / "FUKUOKA_HIROSHIMA_TOUR_DETAIL_MATCHES.md"

FIELDS = [
    "anchor_id",
    "city_id",
    "city_name",
    "anchor_name_local",
    "anchor_name_ko",
    "product_id",
    "product_title",
    "product_url",
    "product_category",
    "product_category_value",
    "matched_alias",
    "section_label",
    "evidence_text",
    "evidence_source",
]

MANUAL_ALIASES = {
    "official-fukuoka-guide-26792": [
        "캐널시티 하카타",
        "캐널 시티 하카타",
        "캐널시티 히카타",
        "캐널 시티 히카타",
    ],
    "official-fukuoka-guide-26798": ["후쿠오카타워", "후쿠오카 타워"],
    "official-fukuoka-guide-26825": ["오호리공원", "오호리 공원"],
    "official-fukuoka-guide-26906": ["구시다신사", "구시다 신사", "쿠시다 신사"],
    "official-fukuoka-guide-26815": ["후쿠오카시 미술관", "후쿠오카 미술관"],
    "official-fukuoka-guide-26794": ["후쿠오카 아시아 미술관", "아시아미술관"],
    "official-fukuoka-guide-26814": ["후쿠오카시 박물관", "후쿠오카 박물관"],
    "official-fukuoka-guide-26950": ["아카렌가 문화관", "붉은벽돌 문화관"],
    "official-fukuoka-guide-26800": ["마린월드", "마린 월드", "우미노나카미치 마린월드"],
    "official-fukuoka-guide-26799": ["우미노나카미치 해변공원", "우미노나카미치"],
    "official-fukuoka-guide-26970": ["노코노시마"],
    "official-hiroshima-facility-1": ["슛케이엔", "슈케이엔", "축경원"],
    "official-hiroshima-facility-7": ["아사동물공원", "아사 동물원"],
    "official-hiroshima-facility-10": ["히로시마 현립 미술관"],
    "official-hiroshima-facility-12": ["히로시마 미술관"],
    "official-hiroshima-facility-14": ["히로시마 성"],
    "official-hiroshima-facility-15": [
        "히로시마 평화기념자료관",
        "히로시마 평화기념관",
        "평화기념자료관",
        "평화 기념 박물관",
        "원폭 자료관",
        "원폭 박물관",
        "원자력 박물관",
    ],
    "official-hiroshima-facility-16": ["국립 원폭사망자 추도평화기념관"],
    "official-hiroshima-facility-23": ["히로시마 현대미술관", "현대 미술관"],
    "official-hiroshima-facility-26": ["누마지 교통 박물관", "교통과학관"],
    "official-hiroshima-facility-28": ["히로시마 만화도서관", "만화 도서관"],
    "official-hiroshima-facility-33": ["오리즈루타워", "오리즈루 타워"],
}

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


def load_auto_aliases() -> dict[str, list[str]]:
    aliases: dict[str, list[str]] = defaultdict(list)
    if not AUTO_ALIASES.exists():
        return aliases
    for row in read_csv(AUTO_ALIASES):
        try:
            confidence = float(row.get("confidence") or 0)
        except ValueError:
            continue
        alias = clean(row.get("alias_ko"))
        if confidence >= 0.75 and len(normalize(alias)) >= 4:
            aliases[row["anchor_id"]].append(alias)
    return aliases


def reviewed_anchors() -> list[dict[str, str]]:
    return [
        row
        for row in read_csv(ANCHORS)
        if row.get("city_id") in {"jp-fukuoka", "jp-hiroshima"}
        and row.get("anchor_type") == "place"
        and row.get("official_source_type") == "tourism_facility"
        and row.get("review_status") == "accepted"
        and row.get("match_ready") == "true"
    ]


def alias_candidates(
    anchor: dict[str, str],
    auto_aliases: dict[str, list[str]],
) -> list[str]:
    values = [
        anchor.get("anchor_name"),
        anchor.get("anchor_name_local"),
        anchor.get("anchor_name_ko"),
        anchor.get("anchor_name_en"),
        *MANUAL_ALIASES.get(anchor["anchor_id"], []),
        *auto_aliases.get(anchor["anchor_id"], []),
    ]
    for value in list(values):
        value = clean(value)
        without_parentheses = clean(re.sub(r"[（(].*?[）)]", "", value))
        if without_parentheses and without_parentheses != value:
            values.append(without_parentheses)
    accepted = []
    for value in values:
        value = clean(value)
        normalized = normalize(value)
        if not normalized:
            continue
        contains_korean = bool(re.search(r"[가-힣]", value))
        minimum = 4 if contains_korean else 3
        if len(normalized) >= minimum:
            accepted.append(value)
    return list(dict.fromkeys(accepted))


def matched_alias(text: str, aliases: list[str]) -> str:
    haystack = normalize(text)
    matches = [alias for alias in aliases if normalize(alias) in haystack]
    return max(matches, key=lambda value: len(normalize(value))) if matches else ""


AMBIGUOUS_HIROSHIMA_ALIASES = {
    normalize(value)
    for value in ("원폭 자료관", "원폭 박물관", "원자력 박물관")
}


def has_required_city_context(
    anchor: dict[str, str],
    section: dict[str, str],
    alias: str,
) -> bool:
    if (
        anchor["anchor_id"] == "official-hiroshima-facility-15"
        and normalize(alias) in AMBIGUOUS_HIROSHIMA_ALIASES
    ):
        context = normalize(f"{section['product_title']} {section['section_text']}")
        return "히로시마" in context or "広島" in context
    return True


def is_visit_evidence_section(section_type: str, section_label: str) -> bool:
    if section_type == "negative":
        return True
    return section_type == "positive" and "이용 안내" not in section_label


def is_visit_itinerary_slot(slot: dict[str, str], alias: str) -> bool:
    title = clean(slot.get("slot_title"))
    description = clean(slot.get("slot_description"))
    text = f"{title} {description}"
    if not matched_alias(text, [alias]):
        return False
    logistics_markers = (
        "미팅",
        "집결",
        "픽업",
        "탑승",
        "출발",
        "해산",
        "복귀",
        "정차",
    )
    visit_markers = (
        "방문",
        "관람",
        "입장",
        "둘러",
        "산책",
        "체험",
        "자유시간",
        "감상",
        "견학",
    )
    has_logistics = any(marker in text for marker in logistics_markers)
    alias_in_title = normalize(alias) in normalize(title)
    titled_itinerary_course = alias_in_title and any(
        marker in title for marker in ("코스", "일정", "관광")
    )
    compact_alias = normalize(alias)
    compact_text = normalize(text)
    alias_index = compact_text.find(compact_alias)
    compact_context = (
        compact_text[max(0, alias_index - 80) : alias_index + len(compact_alias) + 100]
        if alias_index >= 0
        else compact_text
    )
    has_contextual_visit = any(
        normalize(marker) in compact_context for marker in visit_markers
    )
    relation_only_markers = (
        "연결",
        "조망",
        "전망",
        "바라",
        "보이는",
        "인접",
        "근처",
        "주변",
        "위치",
    )
    relation_only = any(
        normalize(marker) in compact_context for marker in relation_only_markers
    )
    replacement_markers = ("대체됩니다", "대체 예정", "대체될", "대체 가능")
    replacement_text = any(marker in text for marker in replacement_markers)
    replacement_target = bool(
        re.search(
            rf"{re.escape(compact_alias)}(?:은|는|이|가)?(?:으로|로)대체",
            compact_text,
        )
    )
    conditional_replacement = replacement_text and any(
        marker in text for marker in ("경우", "악천후", "휴장", "상황에 따라")
    )

    # A slot whose advertised place is explicitly replaced does not confirm a
    # visit to that advertised place. The replacement target itself may count.
    if alias_in_title and replacement_text and not replacement_target:
        return False
    if conditional_replacement and not alias_in_title:
        return False
    if has_logistics and not has_contextual_visit and not titled_itinerary_course:
        return False
    if alias_in_title:
        return True
    if replacement_target:
        return True
    return has_contextual_visit and not relation_only


def evidence_excerpt(label: str, text: str, alias: str) -> str:
    direct_index = text.casefold().find(alias.casefold())
    if direct_index >= 0:
        start = max(0, direct_index - 180)
        end = min(len(text), direct_index + len(alias) + 260)
        excerpt = text[start:end]
    else:
        excerpt = text[:800]
    return clean(f"{label}: {excerpt}")


def build_match(
    anchor: dict[str, str],
    section: dict[str, str],
    alias: str,
) -> dict[str, str]:
    return {
        "anchor_id": anchor["anchor_id"],
        "city_id": anchor["city_id"],
        "city_name": anchor["city_name"],
        "anchor_name_local": anchor["anchor_name_local"],
        "anchor_name_ko": anchor["anchor_name_ko"],
        "product_id": section["product_id"],
        "product_title": section["product_title"],
        "product_url": section["product_url"],
        "product_category": "투어",
        "product_category_value": "tour",
        "matched_alias": alias,
        "section_label": section["section_label"],
        "evidence_text": evidence_excerpt(
            section["section_label"], section["section_text"], alias
        ),
        "evidence_source": "MCP getTnaDetail positive section",
    }


def main() -> int:
    anchors = reviewed_anchors()
    auto_aliases = load_auto_aliases()
    aliases_by_anchor = {
        anchor["anchor_id"]: alias_candidates(anchor, auto_aliases) for anchor in anchors
    }
    sections = read_csv(SECTIONS)
    positive_matches: dict[tuple[str, str], dict[str, str]] = {}
    negative_matches: dict[tuple[str, str], dict[str, str]] = {}
    for section in sections:
        section_type = section["section_type"]
        if not is_visit_evidence_section(section_type, section["section_label"]):
            # Meeting/pick-up points are not proof that the tour visits the place.
            continue
        for anchor in anchors:
            alias = matched_alias(section["section_text"], aliases_by_anchor[anchor["anchor_id"]])
            if not alias or not has_required_city_context(anchor, section, alias):
                continue
            match = build_match(anchor, section, alias)
            key = (anchor["anchor_id"], section["product_id"])
            target = positive_matches if section_type == "positive" else negative_matches
            current = target.get(key)
            if current is None or len(match["evidence_text"]) > len(current["evidence_text"]):
                target[key] = match

    if PUBLIC_SLOTS.exists():
        for slot in read_csv(PUBLIC_SLOTS):
            slot_text = clean(f"{slot['slot_title']} {slot['slot_description']}")
            for anchor in anchors:
                aliases = aliases_by_anchor[anchor["anchor_id"]]
                # Prefer an alias in the itinerary title. A canonical spelling
                # in the description must not hide a reviewed title typo such
                # as 캐널 시티 히카타, because title placement is the stronger
                # evidence that the slot is actually a course stop.
                alias = matched_alias(slot["slot_title"], aliases) or matched_alias(
                    slot_text, aliases
                )
                if (
                    not alias
                    or not is_visit_itinerary_slot(slot, alias)
                    or not has_required_city_context(
                        anchor,
                        {
                            "product_title": slot["product_title"],
                            "section_text": slot_text,
                        },
                        alias,
                    )
                ):
                    continue
                section = {
                    "product_id": slot["product_id"],
                    "product_title": slot["product_title"],
                    "product_url": slot["product_url"],
                    "section_label": clean(
                        f"전체 일정 · {slot['itinerary_title']} · {slot['slot_title']}"
                    ),
                    "section_text": slot_text,
                }
                match = build_match(anchor, section, alias)
                match["evidence_source"] = (
                    "MRT public product __NEXT_DATA__ itinerary slot"
                )
                positive_matches[(anchor["anchor_id"], slot["product_id"])] = match

    positive_rows = sorted(
        positive_matches.values(),
        key=lambda row: (row["city_id"], row["anchor_id"], row["product_id"]),
    )
    negative_rows = sorted(
        (
            row
            for key, row in negative_matches.items()
            if key not in positive_matches
        ),
        key=lambda row: (row["city_id"], row["anchor_id"], row["product_id"]),
    )
    write_csv(OUT, positive_rows)
    write_csv(NEGATIVE_OUT, negative_rows)

    products_by_city: dict[str, set[str]] = defaultdict(set)
    anchors_by_city: dict[str, set[str]] = defaultdict(set)
    for row in positive_rows:
        products_by_city[row["city_name"]].add(row["product_id"])
        anchors_by_city[row["city_name"]].add(row["anchor_id"])
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "reviewed_official_places": len(anchors),
        "positive_place_product_links": len(positive_rows),
        "negative_only_place_product_mentions": len(negative_rows),
        "matched_official_places": len({row["anchor_id"] for row in positive_rows}),
        "by_city": {
            city: {
                "matched_official_places": len(anchors_by_city[city]),
                "matched_tour_products": len(products_by_city[city]),
                "place_product_links": sum(row["city_name"] == city for row in positive_rows),
            }
            for city in sorted({anchor["city_name"] for anchor in anchors})
        },
        "matched_alias_counts": dict(Counter(row["matched_alias"] for row in positive_rows)),
    }
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# 후쿠오카·히로시마 투어 상세 장소 매칭",
        "",
        f"- 공식 장소 기준: {len(anchors)}곳",
        f"- 상세에서 확인된 공식 장소: {summary['matched_official_places']}곳",
        f"- 장소×투어 연결: {len(positive_rows)}건",
        f"- 불포함 영역에만 등장해 제외한 연결: {len(negative_rows)}건",
        "",
        "| 도시 | 공식 장소 | 투어 상품 | 상세 근거 |",
        "|---|---|---|---|",
    ]
    for row in positive_rows:
        lines.append(
            f"| {row['city_name']} | {row['anchor_name_ko']} / {row['anchor_name_local']} "
            f"| [{row['product_title']}]({row['product_url']}) "
            f"| {row['evidence_text'].replace('|', ',')} |"
        )
    REPORT_OUT.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
