#!/usr/bin/env python3
"""Collect the complete current Yokanavi official tour/experience catalog.

This catalog is separate from Yokanavi's 468 sightseeing-place records. Keeping
it separate prevents place-level match rates from silently claiming that
official tours and participatory experiences were also audited.
"""

from __future__ import annotations

import csv
import json
import re
import time
import urllib.request
from datetime import datetime
from pathlib import Path

from bs4 import BeautifulSoup


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "official_tourism_sources"
RAW_DIR = BASE / "raw" / "fukuoka_official_tours"
OUT = BASE / "processed" / "accepted" / "fukuoka_official_tours.csv"
SUMMARY = BASE / "reports" / "fukuoka_official_tour_collection_summary.json"
LIST_URL = "https://yokanavi.com/tours"
FIELDS = [
    "official_tour_id",
    "title_ja",
    "official_url",
    "reservation_status_ja",
    "areas_ja",
    "tags_ja",
    "ended",
    "itinerary_text_ja",
    "address_ja",
    "source_scope",
]


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def fetch(url: str) -> str:
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 Chrome/138.0.0.0 Safari/537.36"},
    )
    with urllib.request.urlopen(request, timeout=60) as response:
        return response.read().decode("utf-8", errors="replace")


def section_text(soup: BeautifulSoup, heading_text: str) -> str:
    heading = next(
        (
            tag
            for tag in soup.find_all(["h2", "h3"])
            if heading_text in clean(tag.get_text(" ", strip=True))
        ),
        None,
    )
    if not heading:
        return ""
    chunks: list[str] = []
    for node in heading.find_all_next():
        if node is not heading and node.name in {"h2", "h3"}:
            break
        if node.name in {"p", "li", "dd"}:
            value = clean(node.get_text(" ", strip=True))
            if value:
                chunks.append(value)
    return clean(" ".join(dict.fromkeys(chunks)))


def labeled_value(soup: BeautifulSoup, label: str) -> str:
    for term in soup.find_all(["dt", "th"]):
        if clean(term.get_text(" ", strip=True)) != label:
            continue
        sibling = term.find_next_sibling(["dd", "td"])
        if sibling:
            return clean(sibling.get_text(" ", strip=True))
    return ""


def parse_list(html: str) -> tuple[int, list[dict[str, str]]]:
    soup = BeautifulSoup(html, "html.parser")
    count_text = clean(
        soup.select_one(".fw-bold").get_text(" ", strip=True)
        if soup.select_one(".fw-bold")
        else ""
    )
    count_match = re.search(r"(\d+)件中", count_text)
    declared_count = int(count_match.group(1)) if count_match else 0
    rows: list[dict[str, str]] = []
    for card in soup.select(".card-list__item[data-rspec='tour']"):
        link = card.select_one("a.card-title[href^='/tours/']")
        if not link:
            continue
        href = str(link.get("href"))
        tour_id = href.rstrip("/").split("/")[-1]
        rows.append(
            {
                "official_tour_id": tour_id,
                "title_ja": clean(link.get_text(" ", strip=True)),
                "official_url": f"https://yokanavi.com{href}",
                "reservation_status_ja": clean(
                    card.select_one(".card-reservation .txt").get_text(" ", strip=True)
                    if card.select_one(".card-reservation .txt")
                    else ""
                ),
                "areas_ja": " | ".join(
                    clean(tag.get_text(" ", strip=True))
                    for tag in card.select(".card-area-list .txt")
                ),
                "tags_ja": " | ".join(
                    clean(tag.get_text(" ", strip=True)).lstrip("#")
                    for tag in card.select(".tag-list__item")
                ),
            }
        )
    return declared_count, rows


def main() -> int:
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    OUT.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    list_html = fetch(LIST_URL)
    (RAW_DIR / "tours.html").write_text(list_html, encoding="utf-8")
    declared_count, rows = parse_list(list_html)
    for index, row in enumerate(rows, start=1):
        detail_path = RAW_DIR / f"{row['official_tour_id']}.html"
        if detail_path.exists():
            detail_html = detail_path.read_text(encoding="utf-8")
        else:
            detail_html = fetch(row["official_url"])
            detail_path.write_text(detail_html, encoding="utf-8")
            if index < len(rows):
                time.sleep(0.5)
        soup = BeautifulSoup(detail_html, "html.parser")
        page_text = clean(soup.get_text(" ", strip=True))
        row.update(
            {
                "ended": str("このツアーは終了しました" in page_text).lower(),
                "itinerary_text_ja": section_text(soup, "ツアー行程"),
                "address_ja": labeled_value(soup, "住所"),
                "source_scope": "Yokanavi current /tours result set",
            }
        )
    with OUT.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=FIELDS)
        writer.writeheader()
        writer.writerows(rows)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "source_url": LIST_URL,
        "declared_result_count": declared_count,
        "collected_result_count": len(rows),
        "complete_against_declared_count": declared_count == len(rows),
        "ended_count": sum(row["ended"] == "true" for row in rows),
        "rows_with_itinerary": sum(bool(row["itinerary_text_ja"]) for row in rows),
        "scope_note": (
            "Current Yokanavi Select tours only; external Jalan reservations and "
            "Fukuoka Prefecture experience catalog are separate source families."
        ),
    }
    SUMMARY.write_text(
        json.dumps(summary, ensure_ascii=False, indent=2),
        encoding="utf-8",
    )
    print(json.dumps(summary, ensure_ascii=False))
    return 0 if declared_count == len(rows) else 2


if __name__ == "__main__":
    raise SystemExit(main())
