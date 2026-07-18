#!/usr/bin/env python3
"""Build normalized official experience anchors from filtered official data."""

from __future__ import annotations

import csv
import json
import re
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
PROCESSED = ROOT / "data" / "official_tourism_sources" / "processed"
OUT = ROOT / "data" / "official_tourism_sources" / "anchors"
REPORTS = ROOT / "data" / "official_tourism_sources" / "reports"


ANCHOR_FIELDS = [
    "anchor_id",
    "city_id",
    "city_name",
    "country_code",
    "anchor_name",
    "anchor_name_local",
    "anchor_name_en",
    "anchor_type",
    "official_source_type",
    "source_dataset",
    "source_record_id",
    "source_url",
    "description",
    "category",
    "address",
    "lat",
    "lng",
    "start_date",
    "end_date",
    "price_text",
    "evidence_text",
    "confidence",
    "review_status",
    "match_ready",
    "notes",
]

KYOTO_NON_PRIMARY_NAME_TERMS = (
    "ホテル",
    "旅館",
    "お宿",
    "宿",
    "民宿",
    "ペンション",
    "ロッジ",
    "ゲストハウス",
    "レストラン",
    "食堂",
    "料理",
    "カフェ",
    "喫茶",
    "茶屋",
    "菓",
    "餅",
    "豆腐",
    "とうふ",
    "納豆",
    "甘味",
    "グリル",
    "パーク",
    "駐車場",
)

KYOTO_NON_PRIMARY_TEXT_TERMS = (
    "宿泊",
    "客室",
    "朝食",
    "レストラン",
    "食事",
    "料理",
    "菓子",
    "甘味",
    "ランチ",
    "駐車場",
    "コインパーキング",
)


def clean(text: str | None) -> str:
    if not text:
        return ""
    return re.sub(r"\s+", " ", str(text)).strip()


def slug(text: str) -> str:
    value = re.sub(r"[^0-9A-Za-z가-힣ぁ-んァ-ン一-龥]+", "-", text)
    value = re.sub(r"-+", "-", value).strip("-")
    return value[:80] or "unknown"


def read_csv(path: Path) -> list[dict[str, str]]:
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                return [dict(row) for row in csv.DictReader(f)]
        except UnicodeDecodeError:
            continue
    raise RuntimeError(f"Could not decode {path}")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=ANCHOR_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def fukuoka_yatai_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "curated" / "fukuoka_yatai_curated.csv"
    rows = read_csv(path)
    anchors = []
    anchors.append(
        {
            "anchor_id": "official-fukuoka-yatai-cluster",
            "city_id": "jp-fukuoka",
            "city_name": "후쿠오카",
            "country_code": "JP",
            "anchor_name": "후쿠오카 야타이",
            "anchor_name_local": "福岡市 屋台",
            "anchor_name_en": "Fukuoka Yatai",
            "anchor_type": "place_cluster",
            "official_source_type": "official_yatai_cluster",
            "source_dataset": "fukuoka_yatai_curated",
            "source_record_id": "cluster",
            "source_url": "https://data.bodik.jp/dataset/401307_yataiopendata",
            "description": f"福岡市 official yatai inventory with {len(rows)} deduplicated stalls.",
            "category": "야타이/포장마차",
            "address": "福岡県福岡市",
            "lat": "",
            "lng": "",
            "start_date": "",
            "end_date": "",
            "price_text": "",
            "evidence_text": f"福岡市 official yatai dataset / {len(rows)} stalls / deduplicated by 屋台ID",
            "confidence": "0.98",
            "review_status": "accepted",
            "match_ready": "true",
            "notes": "Place-based aggregate anchor for Fukuoka yatai area/stall network; product format such as tour is not used as the analysis unit.",
        }
    )
    for row in rows:
        name = clean(row.get("名称"))
        yatai_id = clean(row.get("屋台ID"))
        if not name:
            continue
        category = clean(row.get("カテゴリー"))
        description = clean(row.get("リード文") or row.get("本文"))
        official_url = clean(row.get("よかなびURL") or row.get("URL") or row.get("Google Map"))
        evidence = " / ".join(x for x in [name, category, clean(row.get("エリア")), description[:160]] if x)
        anchors.append(
            {
                "anchor_id": f"official-fukuoka-yatai-{yatai_id or slug(name)}",
                "city_id": "jp-fukuoka",
                "city_name": "후쿠오카",
                "country_code": "JP",
                "anchor_name": name,
                "anchor_name_local": name,
                "anchor_name_en": clean(row.get("名称_英語")),
                "anchor_type": "food_place",
                "official_source_type": "official_yatai",
                "source_dataset": "fukuoka_yatai_curated",
                "source_record_id": yatai_id,
                "source_url": official_url,
                "description": description,
                "category": category,
                "address": clean(row.get("所在地_連結表記") or row.get("住所")),
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "start_date": "",
                "end_date": "",
                "price_text": clean(row.get("予算")),
                "evidence_text": evidence,
                "confidence": "0.95",
                "review_status": "accepted",
                "match_ready": "true",
                "notes": "Fukuoka official yatai dataset; deduplicated by 屋台ID",
            }
        )
    return anchors


def hiroshima_facility_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "accepted" / "hiroshima_tourism_facilities_city_only.csv"
    rows = read_csv(path)
    anchors = []
    for row in rows:
        name = clean(row.get("名称"))
        no = clean(row.get("NO"))
        if not name:
            continue
        description = clean(row.get("説明"))
        evidence = " / ".join(x for x in [name, description[:160], clean(row.get("アクセス方法"))] if x)
        anchors.append(
            {
                "anchor_id": f"official-hiroshima-facility-{no or slug(name)}",
                "city_id": "jp-hiroshima",
                "city_name": "히로시마",
                "country_code": "JP",
                "anchor_name": name,
                "anchor_name_local": name,
                "anchor_name_en": "",
                "anchor_type": "place",
                "official_source_type": "tourism_facility",
                "source_dataset": "hiroshima_tourism_facilities_city_only",
                "source_record_id": no,
                "source_url": clean(row.get("URL")),
                "description": description,
                "category": "관광시설",
                "address": clean(row.get("住所")),
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "start_date": "",
                "end_date": "",
                "price_text": clean(row.get("料金（詳細）") or row.get("料金（基本）")),
                "evidence_text": evidence,
                "confidence": "0.9",
                "review_status": "accepted",
                "match_ready": "true",
                "notes": "Hiroshima official tourism facility; city-code filtered",
            }
        )
    return anchors


def hiroshima_event_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "accepted" / "hiroshima_events.csv"
    rows = read_csv(path)
    anchors = []
    seen: set[str] = set()
    for row in rows:
        name = clean(row.get("イベント名"))
        no = clean(row.get("NO"))
        place = clean(row.get("場所名称"))
        start = clean(row.get("開始日"))
        if not name:
            continue
        key = f"{name}|{place}|{start}"
        if key in seen:
            continue
        seen.add(key)
        description = clean(row.get("説明"))
        category = clean(row.get("カテゴリー"))
        evidence = " / ".join(x for x in [name, place, start, category, description[:160]] if x)
        anchors.append(
            {
                "anchor_id": f"official-hiroshima-event-{no or slug(key)}",
                "city_id": "jp-hiroshima",
                "city_name": "히로시마",
                "country_code": "JP",
                "anchor_name": name,
                "anchor_name_local": name,
                "anchor_name_en": clean(row.get("イベント名_英語")),
                "anchor_type": "event",
                "official_source_type": "official_event",
                "source_dataset": "hiroshima_events",
                "source_record_id": no,
                "source_url": clean(row.get("URL") or row.get("追加URL")),
                "description": description,
                "category": category,
                "address": clean(row.get("住所") or place),
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "start_date": start,
                "end_date": clean(row.get("終了日")),
                "price_text": clean(row.get("料金(詳細)") or row.get("料金(基本)")),
                "evidence_text": evidence,
                "confidence": "0.78",
                "review_status": "accepted_time_sensitive",
                "match_ready": "true",
                "notes": "Hiroshima official event; time-sensitive, discount or exclude if expired",
            }
        )
    return anchors


def kyoto_facility_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "accepted" / "kyoto_tourism_facilities_city_only.csv"
    if not path.exists():
        return []
    rows = read_csv(path)
    anchors = []
    skipped_non_primary = 0
    for row in rows:
        name = clean(row.get("名称"))
        no = clean(row.get("NO"))
        if not name:
            continue
        text_for_filter = " ".join(
            clean(row.get(key))
            for key in ["名称", "説明", "アクセス方法", "連絡先名称", "住所"]
        )
        if any(term in name for term in KYOTO_NON_PRIMARY_NAME_TERMS) or any(
            term in text_for_filter for term in KYOTO_NON_PRIMARY_TEXT_TERMS
        ):
            skipped_non_primary += 1
            continue
        description = clean(row.get("説明"))
        evidence = " / ".join(x for x in [name, description[:160], clean(row.get("アクセス方法"))] if x)
        anchors.append(
            {
                "anchor_id": f"official-kyoto-facility-{no or slug(name)}",
                "city_id": "jp-kyoto",
                "city_name": "교토",
                "country_code": "JP",
                "anchor_name": name,
                "anchor_name_local": name,
                "anchor_name_en": clean(row.get("名称_英語")),
                "anchor_type": "place",
                "official_source_type": "tourism_facility",
                "source_dataset": "kyoto_tourism_facilities_city_only",
                "source_record_id": no,
                "source_url": clean(row.get("URL")),
                "description": description,
                "category": "관광시설",
                "address": clean(row.get("住所")),
                "lat": clean(row.get("緯度")),
                "lng": clean(row.get("経度")),
                "start_date": "",
                "end_date": "",
                "price_text": clean(row.get("料金（詳細）") or row.get("料金（基本）")),
                "evidence_text": evidence,
                "confidence": "0.9",
                "review_status": "accepted",
                "match_ready": "true",
                "notes": "Kyoto Prefecture official tourism facility; filtered to municipality names starting with 京都市. Lodging/restaurant-like records are excluded from primary tourism-place anchors by name terms.",
            }
        )
    if skipped_non_primary:
        (REPORTS / "kyoto_anchor_non_primary_skip_summary.json").write_text(
            json.dumps(
                {
                    "source": str(path.relative_to(ROOT)),
                    "skipped_non_primary_rows": skipped_non_primary,
                    "skip_terms": list(KYOTO_NON_PRIMARY_NAME_TERMS),
                },
                ensure_ascii=False,
                indent=2,
            ),
            encoding="utf-8",
        )
    return anchors


def multicity_seed_anchors() -> list[dict[str, str]]:
    path = PROCESSED / "curated" / "multicity_tourism_seed_assets.csv"
    if not path.exists():
        return []
    rows = read_csv(path)
    anchors = []
    for idx, row in enumerate(rows, start=1):
        city_id = clean(row.get("city_id"))
        local_name = clean(row.get("official_name_local"))
        display_name_ko = clean(row.get("display_name_ko"))
        if not city_id or not local_name:
            continue
        anchors.append(
            {
                "anchor_id": f"official-seed-{city_id}-{slug(local_name)}",
                "city_id": city_id,
                "city_name": clean(row.get("city_name")),
                "country_code": clean(row.get("country_code")),
                "anchor_name": local_name,
                "anchor_name_local": local_name,
                "anchor_name_en": clean(row.get("official_name_en")),
                "anchor_type": "place",
                "official_source_type": "tourism_seed",
                "source_dataset": "multicity_tourism_seed_assets",
                "source_record_id": str(idx),
                "source_url": clean(row.get("source_url")),
                "description": clean(row.get("notes")),
                "category": clean(row.get("category")),
                "address": "",
                "lat": "",
                "lng": "",
                "start_date": "",
                "end_date": "",
                "price_text": "",
                "evidence_text": " / ".join(x for x in [local_name, display_name_ko, clean(row.get("source_url"))] if x),
                "confidence": "0.82",
                "review_status": "seed_for_first_pass",
                "match_ready": "true",
                "notes": f"First-pass multi-city tourism seed. Korean display name: {display_name_ko}",
            }
        )
    return anchors


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    anchors = []
    anchors.extend(fukuoka_yatai_anchors())
    anchors.extend(kyoto_facility_anchors())
    anchors.extend(hiroshima_facility_anchors())
    anchors.extend(hiroshima_event_anchors())
    seed_anchors = multicity_seed_anchors()

    write_csv(OUT / "official_experience_anchors.csv", anchors)
    write_csv(OUT / "multicity_seed_candidate_anchors.csv", seed_anchors)
    with (OUT / "official_experience_anchors.jsonl").open("w", encoding="utf-8") as f:
        for row in anchors:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")
    with (OUT / "multicity_seed_candidate_anchors.jsonl").open("w", encoding="utf-8") as f:
        for row in seed_anchors:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "anchor_count": len(anchors),
        "by_city": dict(Counter(row["city_id"] for row in anchors)),
        "by_type": dict(Counter(row["anchor_type"] for row in anchors)),
        "by_source": dict(Counter(row["official_source_type"] for row in anchors)),
        "outputs": [
            str((OUT / "official_experience_anchors.csv").relative_to(ROOT)),
            str((OUT / "official_experience_anchors.jsonl").relative_to(ROOT)),
            str((OUT / "multicity_seed_candidate_anchors.csv").relative_to(ROOT)),
            str((OUT / "multicity_seed_candidate_anchors.jsonl").relative_to(ROOT)),
        ],
        "seed_candidate_count_excluded_from_primary_anchors": len(seed_anchors),
    }
    (REPORTS / "official_anchor_build_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Official Experience Anchor Build Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Anchor count: {summary['anchor_count']}",
        f"- By city: {summary['by_city']}",
        f"- By type: {summary['by_type']}",
        f"- By source: {summary['by_source']}",
        "",
        "## Outputs",
        "",
        "- `data/official_tourism_sources/anchors/official_experience_anchors.csv`",
        "- `data/official_tourism_sources/anchors/official_experience_anchors.jsonl`",
        "- `data/official_tourism_sources/anchors/multicity_seed_candidate_anchors.csv`",
        "- `data/official_tourism_sources/anchors/multicity_seed_candidate_anchors.jsonl`",
        "",
        "## Notes",
        "",
        "- Fukuoka yatai anchors are deduplicated by `屋台ID`.",
        "- Hiroshima tourism facilities are filtered to Hiroshima city code `341002`.",
        "- Kyoto tourism facilities are filtered to municipality names starting with `京都市`; lodging/restaurant-like records are excluded from primary place anchors by name terms.",
        "- Hiroshima event anchors are time-sensitive and should be discounted or excluded when expired.",
        "- Multi-city seed anchors are exported separately as candidate/demo anchors and are excluded from the primary official anchor file to avoid analysis contamination.",
    ]
    (REPORTS / "OFFICIAL_ANCHOR_BUILD_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
