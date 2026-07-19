#!/usr/bin/env python3
"""Collect and filter Fukuoka City's official sightseeing-place catalog.

Primary source:
  https://yokanavi.com/spots

The Japanese catalog is the denominator because it exposes the current,
paginated place inventory with stable spot IDs, descriptions, areas and
sub-categories.  Korean display names are joined from the official multilingual
guide by the same spot ID when available.
"""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "official_tourism_sources"
RAW_DIR = BASE / "raw" / "fukuoka_official_guide"
ACCEPTED = BASE / "processed" / "accepted" / "fukuoka_official_guide_places.csv"
EXCLUDED = BASE / "processed" / "excluded" / "fukuoka_official_guide_excluded.csv"
SUMMARY = BASE / "reports" / "fukuoka_official_guide_collection_summary.json"

JAPANESE_LIST_URL = "https://yokanavi.com/spots"
KOREAN_LIST_URL = "https://www.gofukuoka.jp/ko/searches?story%5B%5D=spot"
USER_AGENT = (
    "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
    "AppleWebKit/537.36 Chrome/138.0.0.0 Safari/537.36"
)

FIELDS = [
    "spot_id",
    "name_local",
    "name_ko",
    "translation_status",
    "description",
    "areas",
    "categories",
    "source_url",
    "disposition",
    "classification",
    "reason",
]

PRIMARY_CATEGORIES = {
    "アートスポット",
    "歴史・神社・仏閣",
    "文化・芸術",
    "自然・景観",
    "建築物",
    "観る その他",
    "レジャー・アウトドア",
    "ファミリー",
    "遊ぶ その他",
}

OUTSIDE_CITY_AREA_PATTERN = re.compile(
    r"太宰府|糸島|北九州|久留米|宗像|福津|古賀|新宮|宇美|篠栗|"
    r"筑紫野|春日|大野城|那珂川|佐賀|長崎|熊本|大分|宮崎|鹿児島|"
    r"福岡市近郊|その他九州"
)

NON_TOURISM_NAME_RULES = (
    (
        "resident_sports_facility",
        re.compile(
            r"体育館|市民プール|屋内プール|運動場|陸上競技場|競技場|"
            r"野球場|球技場|テニスコート|スポーツセンター|"
            r"トレーニングセンター|ヨットハーバー|ゴルフ場|運動公園"
        ),
    ),
    (
        "transport_or_rental_service",
        re.compile(
            r"レンタサイクル|サイクル.*レンタル|レンタカー|駐車場|"
            r"観光案内所|案内処|インフォメーションセンター|"
            r"シカシマサイクル"
        ),
    ),
    (
        "lodging",
        re.compile(r"ホテル|旅館|民宿|ゲストハウス|宿泊|キャンプ場"),
    ),
    (
        "individual_food_business",
        re.compile(
            r"レストラン|カフェ|喫茶|食堂|料理店|ラーメン|うどん|そば|"
            r"寿司|鮨|焼肉|居酒屋|バー$|珈琲|コーヒー|ベーカリー|"
            r"味のめんたい|明太子"
        ),
    ),
)

SUPERSEDED_DUPLICATE_SPOT_IDS = {
    "26805": (
        "ABURAYAMA FUKUOKA（旧 油山市民の森・自然観察の森） is an old "
        "component page whose own description says it was unified into "
        "ABURAYAMA FUKUOKA (spot 26804)"
    ),
}


def clean(value: str | None) -> str:
    return re.sub(r"\s+", " ", str(value or "")).strip()


def fetch(url: str, *, timeout: int = 30) -> str:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": USER_AGENT,
            "Accept-Language": "ja,ko;q=0.9,en;q=0.8",
        },
    )
    with urllib.request.urlopen(request, timeout=timeout) as response:
        return response.read().decode("utf-8", errors="replace")


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as handle:
        writer = csv.DictWriter(handle, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def parse_japanese_cards(html: str) -> list[dict[str, str]]:
    soup = BeautifulSoup(html, "html.parser")
    rows: list[dict[str, str]] = []
    for card in soup.select(".card-list__item .card"):
        title_link = card.select_one("a.card-title[href*='/spots/']")
        if title_link is None:
            continue
        href = clean(title_link.get("href"))
        match = re.search(r"/spots/([^/?#]+)", href)
        if not match:
            continue
        spot_id = match.group(1)
        rows.append(
            {
                "spot_id": spot_id,
                "name_local": clean(title_link.get_text(" ", strip=True)),
                "description": clean(
                    card.select_one(".card-description").get_text(" ", strip=True)
                    if card.select_one(".card-description")
                    else ""
                ),
                "areas": "|".join(
                    dict.fromkeys(
                        clean(node.get_text(" ", strip=True))
                        for node in card.select(".card-area-list a")
                        if clean(node.get_text(" ", strip=True))
                    )
                ),
                "categories": "|".join(
                    dict.fromkeys(
                        clean(node.get_text(" ", strip=True)).lstrip("#")
                        for node in card.select(".tag-list a.--category")
                        if clean(node.get_text(" ", strip=True))
                    )
                ),
                "source_url": f"https://yokanavi.com/spots/{spot_id}",
            }
        )
    return rows


def parse_korean_names(html: str) -> dict[str, str]:
    soup = BeautifulSoup(html, "html.parser")
    names: dict[str, str] = {}
    for link in soup.select("a[href*='/ko/spots/detail/']"):
        href = clean(link.get("href"))
        match = re.search(r"/ko/spots/detail/([^/?#]+)", href)
        title = link.select_one("h3.ttl-link")
        if match and title:
            names[match.group(1)] = clean(title.get_text(" ", strip=True))
    return names


def classify(row: dict[str, str]) -> tuple[str, str, str]:
    name = row["name_local"]
    areas = set(filter(None, row["areas"].split("|")))
    categories = set(filter(None, row["categories"].split("|")))

    if row.get("spot_id") in SUPERSEDED_DUPLICATE_SPOT_IDS:
        return (
            "excluded",
            "superseded_duplicate",
            SUPERSEDED_DUPLICATE_SPOT_IDS[row["spot_id"]],
        )

    outside_areas = {area for area in areas if OUTSIDE_CITY_AREA_PATTERN.search(area)}
    if areas and outside_areas == areas:
        return (
            "excluded",
            "outside_fukuoka_city",
            f"all listed areas are outside Fukuoka City: {'|'.join(sorted(areas))}",
        )

    for classification, pattern in NON_TOURISM_NAME_RULES:
        if pattern.search(name):
            return (
                "excluded",
                classification,
                f"name matched non-primary rule: {pattern.pattern}",
            )

    if categories == {"スポーツ"}:
        return (
            "excluded",
            "sports_only",
            "official category is sports only; not a general visitor-facing tourism place",
        )

    if "スポーツ" in categories and re.search(
        r"公園|センター|競技場|球場|体育館|運動", name
    ):
        return (
            "excluded",
            "resident_sports_facility",
            "sports-tagged park/facility is not treated as a general tourism place",
        )

    if not row.get("name_ko"):
        return (
            "excluded",
            "not_published_in_official_korean_guide",
            (
                "preserved in the complete Japanese official catalog, but excluded "
                "from the Korean-traveler denominator because the official Korean "
                "guide does not publish this spot"
            ),
        )

    if not categories.intersection(PRIMARY_CATEGORIES):
        return (
            "excluded",
            "non_primary_category",
            f"no primary sightseeing category: {'|'.join(sorted(categories))}",
        )

    category_order = [
        ("歴史・神社・仏閣", "heritage_or_religious_site"),
        ("自然・景観", "nature_or_scenic_place"),
        ("アートスポット", "art_place"),
        ("文化・芸術", "culture_or_museum"),
        ("建築物", "architecture_or_landmark"),
        ("レジャー・アウトドア", "visitor_leisure"),
        ("ファミリー", "family_attraction"),
        ("観る その他", "other_sightseeing"),
        ("遊ぶ その他", "other_attraction"),
    ]
    classification = next(
        value for category, value in category_order if category in categories
    )
    return (
        "accepted",
        classification,
        "official sightseeing catalog and primary visitor-facing category",
    )


def collect_japanese_catalog() -> tuple[list[dict[str, str]], int]:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    all_rows: dict[str, dict[str, str]] = {}
    pages_fetched = 0
    for page in range(1, 60):
        url = JAPANESE_LIST_URL if page == 1 else f"{JAPANESE_LIST_URL}?page={page}"
        html = fetch(url)
        (RAW_DIR / f"yokanavi_spots_page_{page:02d}.html").write_text(
            html, encoding="utf-8"
        )
        rows = parse_japanese_cards(html)
        if not rows:
            break
        new_ids = {row["spot_id"] for row in rows}.difference(all_rows)
        if not new_ids:
            break
        for row in rows:
            all_rows[row["spot_id"]] = row
        pages_fetched += 1
        if len(rows) < 18:
            break
        time.sleep(0.12)
    return list(all_rows.values()), pages_fetched


def main() -> int:
    rows, pages_fetched = collect_japanese_catalog()
    korean_html = fetch(KOREAN_LIST_URL)
    (RAW_DIR / "gofukuoka_ko_spots.html").write_text(korean_html, encoding="utf-8")
    korean_names = parse_korean_names(korean_html)

    accepted: list[dict[str, str]] = []
    excluded: list[dict[str, str]] = []
    for row in rows:
        row["name_ko"] = korean_names.get(row["spot_id"], "")
        row["translation_status"] = (
            "official_korean" if row["name_ko"] else "official_korean_unavailable"
        )
        disposition, classification, reason = classify(row)
        row["disposition"] = disposition
        row["classification"] = classification
        row["reason"] = reason
        (accepted if disposition == "accepted" else excluded).append(row)

    accepted.sort(key=lambda row: (row["classification"], row["name_local"]))
    excluded.sort(key=lambda row: (row["classification"], row["name_local"]))
    write_csv(ACCEPTED, accepted)
    write_csv(EXCLUDED, excluded)

    summary = {
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "source": JAPANESE_LIST_URL,
        "korean_source": KOREAN_LIST_URL,
        "pages_fetched": pages_fetched,
        "catalog_rows": len(rows),
        "official_korean_names": len(korean_names),
        "accepted_rows": len(accepted),
        "excluded_rows": len(excluded),
        "accepted_classifications": dict(
            sorted(Counter(row["classification"] for row in accepted).items())
        ),
        "excluded_classifications": dict(
            sorted(Counter(row["classification"] for row in excluded).items())
        ),
        "policy": (
            "Use the complete official sightseeing catalog as the raw universe; "
            "exclude places wholly outside Fukuoka City, resident sports facilities, "
            "lodging, rental/transport services, individual food businesses and "
            "records without a visitor-facing sightseeing category. The primary "
            "MRT-comparison denominator is limited to records also published by the "
            "official Korean guide; Japanese-only records remain preserved and auditable."
        ),
        "accepted_file": str(ACCEPTED.relative_to(ROOT)),
        "excluded_file": str(EXCLUDED.relative_to(ROOT)),
        "raw_directory": str(RAW_DIR.relative_to(ROOT)),
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    print(json.dumps(summary, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
