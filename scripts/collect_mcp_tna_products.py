#!/usr/bin/env python3
"""Collect MyRealTrip MCP T&A product cards for supply-gap matching."""

from __future__ import annotations

import csv
import argparse
import json
import re
import time
import urllib.request
import urllib.error
from collections import Counter
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
OUT = ROOT / "data" / "mcp_tna_products"
RAW = OUT / "raw"
PROCESSED = OUT / "processed"
REPORTS = OUT / "reports"
MCP_URL = "https://mcp-servers.myrealtrip.com/mcp"

CITIES = ["오사카", "도쿄", "교토", "서울", "부산", "여수", "대전"]

EXCLUDED_CATEGORY_VALUES = {
    "all",
    "transportation",
    "transportation_v2",
    "travel_goods",
    "usimwifi",
    "convenience",
    "convenience_v2",
    "golf_cc",
}

DEDUPED_CATEGORY_PRIORITY = [
    "tour",
    "suburb_tour",
    "sinae_tour",
    "cruise_tour",
    "ticket_v2",
    "ticket",
    "foodie",
    "delicacies",
    "activity_class",
    "activity",
    "snap_v2",
    "snap",
    "spamassage",
    "spa_healing",
    "class",
    "kids",
]

PRODUCT_FIELDS = [
    "city_query",
    "category_name",
    "category_value",
    "page",
    "rank_in_page",
    "title",
    "url",
    "product_id",
    "price_text",
    "rating_text",
    "image_url",
    "city_match_status",
    "raw_text",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="Collect MyRealTrip MCP T&A product cards.")
    parser.add_argument("--city", action="append", help="City query to collect. Can be repeated.")
    parser.add_argument("--category", action="append", help="Category value to collect. Can be repeated.")
    parser.add_argument("--max-pages", type=int, default=7, help="Maximum pages per category.")
    parser.add_argument("--delay", type=float, default=0.6, help="Delay seconds between MCP search calls.")
    parser.add_argument("--use-cache", action="store_true", help="Reuse existing raw MCP responses instead of calling again.")
    parser.add_argument("--stop-on-429", action="store_true", help="Stop the current city as soon as MCP returns HTTP 429.")
    parser.add_argument(
        "--merge-existing",
        action="store_true",
        help="Merge newly collected rows with existing processed/mcp_tna_products.csv.",
    )
    return parser.parse_args()


def ensure_dirs() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)


def call_mcp(tool: str, arguments: dict[str, Any], call_id: int) -> dict[str, Any]:
    payload = {
        "jsonrpc": "2.0",
        "id": call_id,
        "method": "tools/call",
        "params": {"name": tool, "arguments": arguments},
    }
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
            "User-Agent": "TNA-Supply-Gap-Map/0.1",
        },
        method="POST",
    )
    with urllib.request.urlopen(req, timeout=60) as resp:
        outer = json.loads(resp.read().decode("utf-8"))
    text = outer["result"]["content"][0]["text"]
    return json.loads(text)


def is_rate_limit_error(exc: Exception) -> bool:
    return isinstance(exc, urllib.error.HTTPError) and exc.code == 429 or "HTTP Error 429" in str(exc)


def walk(node: Any):
    if isinstance(node, dict):
        yield node
        for value in node.values():
            yield from walk(value)
    elif isinstance(node, list):
        for item in node:
            yield from walk(item)


def product_id_from_url(url: str) -> str:
    match = re.search(r"/(?:products|offers)/([0-9]+)", url or "")
    return match.group(1) if match else ""


def parse_products(response: dict[str, Any]) -> list[dict[str, str]]:
    widget = response.get("widget") or {}
    items = []
    for item in walk(widget):
        if item.get("type") != "ListViewItem":
            continue
        texts = [
            clean(n.get("value"))
            for n in walk(item)
            if isinstance(n, dict) and n.get("type") == "Text" and n.get("value")
        ]
        urls = [
            clean(n.get("url"))
            for n in walk(item)
            if isinstance(n, dict) and n.get("url")
        ]
        images = [
            clean(n.get("src"))
            for n in walk(item)
            if isinstance(n, dict) and n.get("type") == "Image" and n.get("src")
        ]
        title = next((t for t in texts if not re.match(r"^(⭐|[0-9,]+원~)", t)), "")
        rating = next((t for t in texts if t.startswith("⭐")), "")
        price = next((t for t in texts if "원" in t), "")
        url = next((u for u in urls if "myrealtrip.com" in u), "")
        if not title and not url:
            continue
        items.append(
            {
                "title": title,
                "url": url,
                "product_id": product_id_from_url(url),
                "price_text": price,
                "rating_text": rating,
                "image_url": images[0] if images else "",
                "raw_text": " | ".join(texts),
            }
        )
    return items


def clean(value: Any) -> str:
    if value is None:
        return ""
    return re.sub(r"\s+", " ", str(value)).strip()


def select_categories(categories: list[dict[str, Any]], requested_values: set[str] | None = None) -> list[dict[str, str]]:
    by_value = {c.get("value"): {"name": c.get("name", ""), "value": c.get("value", "")} for c in categories}
    selected = []
    for value in DEDUPED_CATEGORY_PRIORITY:
        if requested_values and value not in requested_values:
            continue
        if value in by_value and value not in EXCLUDED_CATEGORY_VALUES:
            selected.append(by_value[value])
    if requested_values:
        for value in sorted(requested_values):
            if value in by_value and value not in EXCLUDED_CATEGORY_VALUES and value not in {c["value"] for c in selected}:
                selected.append(by_value[value])
    return selected


def city_match(title: str, city: str) -> str:
    if city in title:
        return "title_contains_city"
    aliases = {
        "오사카": ["USJ", "유니버설", "도톤보리", "난바", "우메다", "교토", "고베", "나라", "Osaka"],
        "도쿄": ["Tokyo", "스카이트리", "시부야", "신주쿠", "아사쿠사", "디즈니", "팀랩"],
        "교토": ["Kyoto", "기요미즈", "후시미", "아라시야마", "금각사", "기온"],
        "서울": ["Seoul", "경복궁", "한강", "북촌", "남산", "N서울타워", "롯데월드"],
        "부산": ["Busan", "해운대", "광안리", "감천", "자갈치", "태종대"],
        "여수": ["Yeosu", "오동도", "해상케이블카", "밤바다", "향일암"],
        "대전": ["Daejeon", "유성", "오월드", "엑스포", "한밭", "계족산"],
    }
    if any(token in title for token in aliases.get(city, [])):
        return "title_alias_match"
    if city == "후쿠오카" and any(token in title for token in ["하카타", "나카스", "Hakata", "Fukuoka"]):
        return "title_alias_match"
    if city == "히로시마" and any(token in title for token in ["Hiroshima", "미야지마", "Miyajima"]):
        return "title_alias_match"
    return "unknown_or_other_city"


def write_csv(path: Path, rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=PRODUCT_FIELDS)
        writer.writeheader()
        writer.writerows(rows)


def collect_city(
    city: str,
    call_id_start: int,
    requested_categories: set[str] | None = None,
    max_pages: int = 7,
    delay: float = 0.6,
    use_cache: bool = False,
    stop_on_429: bool = False,
) -> tuple[list[dict[str, str]], dict[str, Any]]:
    category_path = RAW / f"{city}_categories.json"
    if use_cache and category_path.exists():
        categories_response = json.loads(category_path.read_text(encoding="utf-8"))
    else:
        categories_response = call_mcp("getCategoryList", {"city": city}, call_id_start)
    categories = categories_response.get("categories", [])
    selected_categories = select_categories(categories, requested_categories)
    category_path.write_text(
        json.dumps(categories_response, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    products: list[dict[str, str]] = []
    call_id = call_id_start + 1
    for category in selected_categories:
        seen_urls: set[str] = set()
        empty_or_duplicate_pages = 0
        for page in range(1, max_pages + 1):
            args = {"query": city, "category": category["value"], "page": page, "perPage": 20}
            raw_path = RAW / f"{city}_{category['value']}_page{page}.json"
            try:
                if use_cache and raw_path.exists():
                    response = json.loads(raw_path.read_text(encoding="utf-8"))
                else:
                    response = call_mcp("searchTnas", args, call_id)
            except Exception as exc:
                (RAW / f"{city}_{category['value']}_page{page}_error.json").write_text(
                    json.dumps({"args": args, "error": str(exc)}, ensure_ascii=False, indent=2),
                    encoding="utf-8",
                )
                if stop_on_429 and is_rate_limit_error(exc):
                    return dedupe_products(products), {
                        "city": city,
                        "category_count": len(categories),
                        "selected_categories": selected_categories,
                        "raw_product_rows": len(products),
                        "deduped_product_rows": len(dedupe_products(products)),
                        "city_match_status": dict(Counter(row["city_match_status"] for row in dedupe_products(products))),
                        "error": str(exc),
                        "stopped_on_rate_limit": True,
                    }
                break
            call_id += 1
            raw_path.write_text(
                json.dumps(response, ensure_ascii=False, indent=2), encoding="utf-8"
            )
            parsed = parse_products(response)
            new_count = 0
            for idx, product in enumerate(parsed, start=1):
                key = product["url"] or f"{product['title']}|{category['value']}|{page}|{idx}"
                if key in seen_urls:
                    continue
                seen_urls.add(key)
                new_count += 1
                products.append(
                    {
                        "city_query": city,
                        "category_name": category["name"],
                        "category_value": category["value"],
                        "page": str(page),
                        "rank_in_page": str(idx),
                        **product,
                        "city_match_status": city_match(product["title"], city),
                    }
                )
            if not parsed or new_count == 0:
                empty_or_duplicate_pages += 1
            else:
                empty_or_duplicate_pages = 0
            if empty_or_duplicate_pages >= 2:
                break
            time.sleep(delay)

    deduped = dedupe_products(products)
    summary = {
        "city": city,
        "category_count": len(categories),
        "selected_categories": selected_categories,
        "raw_product_rows": len(products),
        "deduped_product_rows": len(deduped),
        "city_match_status": dict(Counter(row["city_match_status"] for row in deduped)),
    }
    return deduped, summary


def dedupe_products(products: list[dict[str, str]]) -> list[dict[str, str]]:
    by_url: dict[str, dict[str, str]] = {}
    for row in products:
        key = row["url"] or f"{row['title']}|{row['category_value']}"
        by_url.setdefault(key, row)
    return list(by_url.values())


def read_existing_rows() -> list[dict[str, str]]:
    path = PROCESSED / "mcp_tna_products.csv"
    if not path.exists():
        return []
    with path.open("r", encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def dedupe_rows(rows: list[dict[str, str]]) -> list[dict[str, str]]:
    by_key: dict[str, dict[str, str]] = {}
    for row in rows:
        key = row.get("url") or row.get("product_id") or f"{row.get('city_query')}|{row.get('title')}|{row.get('category_value')}"
        by_key[key] = row
    return list(by_key.values())


def main() -> int:
    args = parse_args()
    ensure_dirs()
    cities = args.city or CITIES
    requested_categories = set(args.category) if args.category else None
    all_rows: list[dict[str, str]] = read_existing_rows() if args.merge_existing else []
    new_rows: list[dict[str, str]] = []
    summaries = []
    call_id = 1000
    for city in cities:
        try:
            rows, summary = collect_city(
                city,
                call_id,
                requested_categories=requested_categories,
                max_pages=args.max_pages,
                delay=args.delay,
                use_cache=args.use_cache,
                stop_on_429=args.stop_on_429,
            )
        except Exception as exc:
            rows = []
            summary = {
                "city": city,
                "category_count": 0,
                "selected_categories": [],
                "raw_product_rows": 0,
                "deduped_product_rows": 0,
                "city_match_status": {},
                "error": str(exc),
            }
            (RAW / f"{city}_collection_error.json").write_text(
                json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
            )
        call_id += 500
        new_rows.extend(rows)
        summaries.append(summary)
        write_csv(PROCESSED / f"{city}_mcp_tna_products.csv", rows)

    all_rows = dedupe_rows(all_rows + new_rows)
    write_csv(PROCESSED / "mcp_tna_products.csv", all_rows)
    with (PROCESSED / "mcp_tna_products.jsonl").open("w", encoding="utf-8") as f:
        for row in all_rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    report = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "city_summaries": summaries,
        "new_products": len(new_rows),
        "total_products": len(all_rows),
        "merge_existing": bool(args.merge_existing),
        "requested_cities": cities,
        "requested_categories": sorted(requested_categories) if requested_categories else [],
        "max_pages": args.max_pages,
        "delay": args.delay,
        "use_cache": bool(args.use_cache),
        "stop_on_429": bool(args.stop_on_429),
        "outputs": [
            str((PROCESSED / "mcp_tna_products.csv").relative_to(ROOT)),
            str((PROCESSED / "mcp_tna_products.jsonl").relative_to(ROOT)),
        ],
    }
    REPORTS.mkdir(parents=True, exist_ok=True)
    (REPORTS / "mcp_tna_collection_summary.json").write_text(
        json.dumps(report, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    lines = [
        "# MCP TNA Product Collection Report",
        "",
        f"- Generated at: {report['generated_at']}",
        f"- Newly collected products: {report['new_products']}",
        f"- Total deduped products: {report['total_products']}",
        f"- Merge existing: {report['merge_existing']}",
        f"- Requested cities: {report['requested_cities']}",
        f"- Requested categories: {report['requested_categories'] or 'default priority categories'}",
        f"- Max pages per category: {report['max_pages']}",
        f"- Delay seconds: {report['delay']}",
        "",
        "## City summaries",
        "",
        "| City | Categories | Raw rows | Deduped rows | City match status |",
        "|---|---:|---:|---:|---|",
    ]
    for s in summaries:
        lines.append(
            f"| {s['city']} | {len(s['selected_categories'])}/{s['category_count']} | {s['raw_product_rows']} | {s['deduped_product_rows']} | {s['city_match_status']} |"
        )
    (REPORTS / "MCP_TNA_COLLECTION_REPORT.md").write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps({"total_products": len(all_rows), "summaries": summaries}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
