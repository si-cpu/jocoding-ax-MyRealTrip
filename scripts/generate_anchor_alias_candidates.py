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
    ("京都", "교토"),
    ("清水寺", "청수사"),
    ("金閣寺", "금각사"),
    ("銀閣寺", "은각사"),
    ("鹿苑寺", "로쿠온지"),
    ("慈照寺", "지쇼지"),
    ("伏見稲荷大社", "후시미이나리"),
    ("伏見稲荷", "후시미이나리"),
    ("稲荷", "이나리"),
    ("嵐山", "아라시야마"),
    ("祇園", "기온"),
    ("二条城", "니조성"),
    ("北野天満宮", "키타노텐만구"),
    ("三千院", "산젠인"),
    ("延暦寺", "엔랴쿠지"),
    ("大原", "오하라"),
    ("寺", "사"),
    ("神社", "신사"),
    ("天満宮", "텐만구"),
    ("大社", "대사"),
    ("広島", "히로시마"),
    ("福岡", "후쿠오카"),
    ("宮島", "미야지마"),
    ("厳島", "이쓰쿠시마"),
    ("縮景園", "슛케이엔"),
    ("緑化センター", "녹화센터"),
    ("森林公園", "삼림공원"),
    ("半べえ庭園", "한베에 정원"),
    ("渝華園", "유화원"),
    ("中国庭園", "중국정원"),
    ("大芝公園", "오시바공원"),
    ("交通ランド", "교통랜드"),
    ("安佐動物公園", "아사동물공원"),
    ("花みどり公園", "하나미도리공원"),
    ("県立美術館", "현립미술관"),
    ("映像文化ライブラリー", "영상문화라이브러리"),
    ("美術館", "미술관"),
    ("こども文化科学館", "어린이문화과학관"),
    ("プラネタリウム", "플라네타리움"),
    ("原爆死没者追悼平和祈念館", "원폭사망자추도평화기념관"),
    ("放射線影響研究所", "방사선영향연구소"),
    ("本川小学校平和資料館", "혼카와초등학교평화자료관"),
    ("袋町小学校平和資料館", "후쿠로마치초등학교평화자료관"),
    ("健康づくりセンター健康科学館", "건강과학관"),
    ("江波山気象館", "에바야마기상관"),
    ("頼山陽史跡資料館", "라이산요사적자료관"),
    ("現代美術館", "현대미술관"),
    ("郷土資料館", "향토자료관"),
    ("医学資料館", "의학자료관"),
    ("交通ミュージアム", "교통뮤지엄"),
    ("交通科学館", "교통과학관"),
    ("泉美術館", "이즈미미술관"),
    ("まんが図書館", "만화도서관"),
    ("水産振興センター", "수산진흥센터"),
    ("水道資料館", "수도자료관"),
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
    ("ひろしま", "히로시마"),
    ("ヌマジ", "누마지"),
]

GENERIC_SUFFIXES = [
    ("평화기념자료관", "평화기념관"),
    ("히로시마평화기념자료관", "히로시마평화기념관"),
    ("히로시마시", "히로시마"),
]

CURATED_KO_NAMES = {
    "鹿苑寺（金閣寺）": ["금각사", "킨카쿠지"],
    "清水寺": ["청수사", "기요미즈데라"],
    "伏見稲荷大社": ["후시미이나리", "후시미 이나리"],
    "嵐山": "아라시야마",
    "慈照寺（銀閣寺）": ["은각사", "긴카쿠지"],
    "元離宮二条城": "니조성",
    "北野天満宮": "키타노텐만구",
    "三千院": "산젠인",
    "延暦寺": "엔랴쿠지",
    "祇園": "기온",
    "縮景園": "슛케이엔",
    "ひろしま遊学の森 広島県緑化センター": "히로시마 유학의 숲 히로시마현 녹화센터",
    "ひろしま遊学の森 広島市森林公園（こんちゅう館）": "히로시마 유학의 숲 히로시마시 삼림공원 곤충관",
    "半べえ庭園": "한베에 정원",
    "渝華園(中国庭園)": "유화원 중국정원",
    "大芝公園｢交通ランド」": "오시바공원 교통랜드",
    "広島市安佐動物公園": "히로시마시 아사동물공원",
    "花みどり公園": "하나미도리공원",
    "広島市植物公園": "히로시마시 식물공원",
    "広島県立美術館": "히로시마현립미술관",
    "広島市映像文化ライブラリー": "히로시마시 영상문화라이브러리",
    "ひろしま美術館": "히로시마미술관",
    "5-Daysこども文化科学館（プラネタリウム）": "5-Days 어린이문화과학관 플라네타리움",
    "広島城": "히로시마성",
    "広島平和記念資料館": "히로시마평화기념자료관",
    "国立広島原爆死没者追悼平和祈念館": "국립히로시마원폭사망자추도평화기념관",
    "公益財団法人放射線影響研究所": "방사선영향연구소",
    "本川小学校平和資料館": "혼카와초등학교평화자료관",
    "袋町小学校平和資料館": "후쿠로마치초등학교평화자료관",
    "広島市健康づくりセンター健康科学館": "히로시마시 건강과학관",
    "広島市江波山気象館": "히로시마시 에바야마기상관",
    "頼山陽史跡資料館": "라이산요사적자료관",
    "広島市現代美術館": "히로시마시 현대미술관",
    "広島市郷土資料館": "히로시마시 향토자료관",
    "広島大学医学部医学資料館": "히로시마대학 의학부 의학자료관",
    "ヌマジ交通ミュージアム（広島市交通科学館）": "누마지 교통뮤지엄 히로시마시 교통과학관",
    "泉美術館": "이즈미미술관",
    "広島市まんが図書館": "히로시마시 만화도서관",
    "広島市まんが図書館あさ閲覧室": "히로시마시 만화도서관 아사 열람실",
    "広島市水産振興センター(魚と漁業の資料展示室)": "히로시마시 수산진흥센터 물고기와 어업 자료전시실",
    "広島市水道資料館": "히로시마시 수도자료관",
    "おりづるタワー": "오리즈루 타워",
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


def is_primary_tourism_anchor(anchor: dict[str, str]) -> bool:
    return anchor.get("official_source_type") == "tourism_facility" and anchor.get("anchor_type") == "place"


def rule_translate_jp_to_ko(name: str) -> list[tuple[str, str, float]]:
    variants: list[tuple[str, str, float]] = []
    curated = CURATED_KO_NAMES.get(clean(name))
    if curated:
        curated_values = curated if isinstance(curated, list) else [curated]
        for curated_value in curated_values:
            variants.append((curated_value, "curated_ko_name", 0.95))
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
