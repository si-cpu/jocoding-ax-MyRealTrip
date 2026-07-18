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


def main() -> int:
    OUT.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    anchors = []
    anchors.extend(fukuoka_yatai_anchors())
    anchors.extend(hiroshima_facility_anchors())
    anchors.extend(hiroshima_event_anchors())

    write_csv(OUT / "official_experience_anchors.csv", anchors)
    with (OUT / "official_experience_anchors.jsonl").open("w", encoding="utf-8") as f:
        for row in anchors:
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
        ],
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
        "",
        "## Notes",
        "",
        "- Fukuoka yatai anchors are deduplicated by `屋台ID`.",
        "- Hiroshima tourism facilities are filtered to Hiroshima city code `341002`.",
        "- Hiroshima event anchors are time-sensitive and should be discounted or excluded when expired.",
    ]
    (REPORTS / "OFFICIAL_ANCHOR_BUILD_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")

    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
