#!/usr/bin/env python3
"""Collect full itinerary slots embedded in public MRT product pages."""

from __future__ import annotations

import argparse
import csv
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from collect_city_tour_details import load_tours


ROOT = Path(__file__).resolve().parents[1]
OUT_DIR = ROOT / "data" / "supply_gap_analysis" / "tour_details"
RAW_DIR = OUT_DIR / "public_itinerary_raw"
SLOT_OUT = OUT_DIR / "public_itinerary_slots.csv"
PRODUCT_OUT = OUT_DIR / "public_itinerary_products.csv"
SUMMARY_OUT = OUT_DIR / "public_itinerary_collection_summary.json"

SLOT_FIELDS = [
    "product_id",
    "city_queries",
    "product_title",
    "product_url",
    "itinerary_index",
    "itinerary_title",
    "slot_index",
    "slot_title",
    "slot_description",
    "slot_duration",
]
PRODUCT_FIELDS = [
    "product_id",
    "city_queries",
    "product_title",
    "product_url",
    "status",
    "itinerary_count",
    "slot_count",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cities", nargs="+", default=["후쿠오카", "히로시마"])
    parser.add_argument("--delay", type=float, default=1.0)
    parser.add_argument("--retry-wait", type=float, default=20.0)
    parser.add_argument("--max-retries", type=int, default=4)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def fetch_html(url: str) -> tuple[str | None, str]:
    request = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0",
        },
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            return response.read().decode("utf-8", errors="replace"), "ok"
    except urllib.error.HTTPError as exc:
        return None, f"http_{exc.code}"
    except Exception as exc:
        return None, f"request_failed:{type(exc).__name__}"


def next_data_from_html(html_text: str) -> dict[str, Any] | None:
    match = re.search(
        r'<script id="__NEXT_DATA__" type="application/json">(.*?)</script>',
        html_text,
        flags=re.S,
    )
    if not match:
        return None
    try:
        return json.loads(match.group(1))
    except json.JSONDecodeError:
        return None


def extract_itineraries(next_data: dict[str, Any]) -> list[dict[str, Any]]:
    queries = (
        next_data.get("props", {})
        .get("pageProps", {})
        .get("dehydratedState", {})
        .get("queries", [])
    )
    itineraries: list[dict[str, Any]] = []
    for query in queries:
        data = query.get("state", {}).get("data", {}).get("data", {})
        if not isinstance(data, dict):
            continue
        for partition in data.get("partitions") or []:
            partition_data = partition.get("partitionData") or {}
            for itinerary in partition_data.get("itineraries") or []:
                if isinstance(itinerary, dict) and itinerary.get("slots"):
                    itineraries.append(itinerary)
    return itineraries


def collect_product(
    product: dict[str, str],
    retry_wait: float,
    max_retries: int,
) -> tuple[list[dict[str, Any]], str, bool]:
    raw_path = RAW_DIR / f"{product['product_id']}.json"
    if raw_path.exists():
        cached = json.loads(raw_path.read_text(encoding="utf-8"))
        if (
            isinstance(cached, dict)
            and cached.get("source") == "full_next_data"
            and int(cached.get("hydration_query_count") or 0) >= 1
            and isinstance(cached.get("itineraries"), list)
        ):
            return cached["itineraries"], "ok_cached", True
    for attempt in range(max_retries + 1):
        html_text, status = fetch_html(product["product_url"])
        if html_text is not None:
            next_data = next_data_from_html(html_text)
            if next_data is None:
                return [], "next_data_unavailable", False
            hydration_queries = (
                next_data.get("props", {})
                .get("pageProps", {})
                .get("dehydratedState", {})
                .get("queries", [])
            )
            if not hydration_queries:
                return [], "hydration_unavailable", False
            itineraries = extract_itineraries(next_data)
            raw_path.write_text(
                json.dumps(
                    {
                        "source": "full_next_data",
                        "hydration_query_count": len(hydration_queries),
                        "itineraries": itineraries,
                    },
                    ensure_ascii=False,
                    indent=2,
                ),
                encoding="utf-8",
            )
            return itineraries, "ok", False
        if status not in {"http_429", "http_502", "http_503", "http_504"}:
            return [], status, False
        if attempt >= max_retries:
            return [], status, False
        print(
            json.dumps(
                {
                    "event": "retry",
                    "product_id": product["product_id"],
                    "status": status,
                    "retry": attempt + 1,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        time.sleep(retry_wait)
    return [], "retry_exhausted", False


def main() -> int:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tours = load_tours(args.cities)
    if args.limit:
        tours = tours[: args.limit]
    product_rows: list[dict[str, str]] = []
    slot_rows: list[dict[str, str]] = []
    failed = 0
    cached = 0
    for index, product in enumerate(tours, start=1):
        itineraries, status, used_cache = collect_product(
            product, args.retry_wait, args.max_retries
        )
        cached += int(used_cache)
        failed += int(status not in {"ok", "ok_cached"})
        slot_count = 0
        for itinerary_index, itinerary in enumerate(itineraries, start=1):
            for slot_index, slot in enumerate(itinerary.get("slots") or [], start=1):
                slot_count += 1
                slot_rows.append(
                    {
                        **product,
                        "itinerary_index": str(itinerary_index),
                        "itinerary_title": str(itinerary.get("title") or ""),
                        "slot_index": str(slot_index),
                        "slot_title": str(slot.get("title") or ""),
                        "slot_description": str(slot.get("description") or ""),
                        "slot_duration": str(slot.get("duration") or ""),
                    }
                )
        product_rows.append(
            {
                **product,
                "status": status,
                "itinerary_count": str(len(itineraries)),
                "slot_count": str(slot_count),
            }
        )
        if index % 20 == 0 or index == len(tours):
            print(
                json.dumps(
                    {
                        "event": "progress",
                        "completed": index,
                        "total": len(tours),
                        "cached": cached,
                        "failed": failed,
                        "slots": len(slot_rows),
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        if not used_cache:
            time.sleep(args.delay)

    write_csv(PRODUCT_OUT, PRODUCT_FIELDS, product_rows)
    write_csv(SLOT_OUT, SLOT_FIELDS, slot_rows)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "unique_tour_products": len(tours),
        "successful_pages": sum(
            row["status"] in {"ok", "ok_cached"} for row in product_rows
        ),
        "failed_pages": failed,
        "products_with_itineraries": sum(
            int(row["itinerary_count"]) > 0 for row in product_rows
        ),
        "itinerary_count": sum(int(row["itinerary_count"]) for row in product_rows),
        "slot_count": len(slot_rows),
    }
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if failed == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
