#!/usr/bin/env python3
"""Collect MCP detail payloads for every tour product in selected cities.

The collector is intentionally resumable. Successful raw payloads are cached by
product ID, while rate-limit and transient failures are retried without being
written as successful detail data.
"""

from __future__ import annotations

import argparse
import csv
import html
import json
import re
import time
import urllib.error
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any

from enrich_tour_detail_evidence import parse_detail_payload, sections_from_detail


ROOT = Path(__file__).resolve().parents[1]
PRODUCT_DIR = ROOT / "data" / "mcp_tna_products" / "processed"
OUT_DIR = ROOT / "data" / "supply_gap_analysis" / "tour_details"
RAW_DIR = OUT_DIR / "raw"
PRODUCT_OUT = OUT_DIR / "tour_detail_products.csv"
SECTION_OUT = OUT_DIR / "tour_detail_sections.csv"
SUMMARY_OUT = OUT_DIR / "tour_detail_collection_summary.json"
MCP_URL = "https://mcp-servers.myrealtrip.com/mcp"

PRODUCT_FIELDS = [
    "product_id",
    "city_queries",
    "product_title",
    "product_url",
    "detail_status",
    "section_count",
    "positive_section_count",
    "negative_section_count",
    "neutral_section_count",
]
SECTION_FIELDS = [
    "product_id",
    "city_queries",
    "product_title",
    "product_url",
    "section_type",
    "section_label",
    "section_text",
]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser()
    parser.add_argument("--cities", nargs="+", default=["후쿠오카", "히로시마"])
    parser.add_argument("--delay", type=float, default=3.0)
    parser.add_argument("--retry-wait", type=float, default=45.0)
    parser.add_argument("--max-retries", type=int, default=5)
    parser.add_argument("--limit", type=int)
    return parser.parse_args()


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_tours(cities: list[str]) -> list[dict[str, str]]:
    by_id: dict[str, dict[str, str]] = {}
    for city in cities:
        path = PRODUCT_DIR / f"{city}_mcp_tna_products.csv"
        for row in read_csv(path):
            if row.get("category_value") != "tour" or not row.get("product_id"):
                continue
            product_id = row["product_id"]
            if product_id not in by_id:
                by_id[product_id] = {
                    "product_id": product_id,
                    "city_queries": city,
                    "product_title": row["title"],
                    "product_url": row["url"],
                }
            else:
                current = by_id[product_id]["city_queries"].split(" | ")
                if city not in current:
                    by_id[product_id]["city_queries"] += f" | {city}"
    return list(by_id.values())


def request_detail(product: dict[str, str]) -> tuple[dict[str, Any] | None, str]:
    product_id = product["product_id"]
    payload = {
        "jsonrpc": "2.0",
        "id": int(product_id) if product_id.isdigit() else 1,
        "method": "tools/call",
        "params": {
            "name": "getTnaDetail",
            "arguments": {"gid": product_id, "url": product["product_url"]},
        },
    }
    request = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={
            "Accept": "application/json, text/event-stream",
            "Content-Type": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=60) as response:
            text = response.read().decode("utf-8", errors="replace")
    except urllib.error.HTTPError as exc:
        return None, f"http_{exc.code}"
    except Exception as exc:
        return None, f"request_failed:{type(exc).__name__}"
    try:
        return json.loads(text), "ok"
    except json.JSONDecodeError:
        return {"raw_response": text}, "json_parse_failed"


def collect_one(
    product: dict[str, str],
    retry_wait: float,
    max_retries: int,
) -> tuple[dict[str, Any] | None, str, bool]:
    raw_path = RAW_DIR / f"{product['product_id']}.json"
    if raw_path.exists():
        return json.loads(raw_path.read_text(encoding="utf-8")), "ok_cached", True
    for attempt in range(max_retries + 1):
        raw, status = request_detail(product)
        if raw is not None and status in {"ok", "json_parse_failed"}:
            raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
            return raw, status, False
        if status != "http_429" or attempt >= max_retries:
            return None, status, False
        print(
            json.dumps(
                {
                    "event": "rate_limited",
                    "product_id": product["product_id"],
                    "retry": attempt + 1,
                    "wait_seconds": retry_wait,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        time.sleep(retry_wait)
    return None, "retry_exhausted", False


def clean_detail_text(text: str) -> str:
    text = re.sub(r"<[^>]+>", " ", html.unescape(text or ""))
    return re.sub(r"\s+", " ", text).strip()


def promote_product_description(
    section_type: str,
    label: str,
    raw_text: str,
) -> tuple[str, str, str]:
    text = clean_detail_text(raw_text)
    has_html_description = bool(
        re.search(r"<(?:p|div|h[1-6]|figure|span|br)\b", raw_text or "", flags=re.I)
    )
    if section_type == "neutral" and has_html_description and len(text) >= 40:
        return "positive", f"상품 설명 · {label}", text
    return section_type, label, text


def build_outputs(
    tours: list[dict[str, str]],
    statuses: dict[str, str],
) -> tuple[list[dict[str, str]], list[dict[str, str]]]:
    product_rows: list[dict[str, str]] = []
    section_rows: list[dict[str, str]] = []
    for product in tours:
        product_id = product["product_id"]
        raw_path = RAW_DIR / f"{product_id}.json"
        sections: list[tuple[str, str, str]] = []
        if raw_path.exists():
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            sections = [
                promote_product_description(*section)
                for section in sections_from_detail(parse_detail_payload(raw))
            ]
        counts = {
            section_type: sum(section[0] == section_type for section in sections)
            for section_type in ("positive", "negative", "neutral")
        }
        product_rows.append(
            {
                **product,
                "detail_status": statuses.get(
                    product_id, "ok_cached" if raw_path.exists() else "not_collected"
                ),
                "section_count": str(len(sections)),
                "positive_section_count": str(counts["positive"]),
                "negative_section_count": str(counts["negative"]),
                "neutral_section_count": str(counts["neutral"]),
            }
        )
        for section_type, label, text in sections:
            section_rows.append(
                {
                    **product,
                    "section_type": section_type,
                    "section_label": label,
                    "section_text": text,
                }
            )
    return product_rows, section_rows


def main() -> int:
    args = parse_args()
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    tours = load_tours(args.cities)
    if args.limit:
        tours = tours[: args.limit]
    statuses: dict[str, str] = {}
    cache_count = 0
    network_count = 0
    failed_count = 0
    for index, product in enumerate(tours, start=1):
        raw, status, used_cache = collect_one(product, args.retry_wait, args.max_retries)
        statuses[product["product_id"]] = status
        cache_count += int(used_cache)
        network_count += int(not used_cache and raw is not None)
        failed_count += int(raw is None)
        if index % 10 == 0 or index == len(tours):
            print(
                json.dumps(
                    {
                        "event": "progress",
                        "completed": index,
                        "total": len(tours),
                        "cached": cache_count,
                        "network_success": network_count,
                        "failed": failed_count,
                    },
                    ensure_ascii=False,
                ),
                flush=True,
            )
        if not used_cache and raw is not None:
            time.sleep(args.delay)

    product_rows, section_rows = build_outputs(tours, statuses)
    write_csv(PRODUCT_OUT, PRODUCT_FIELDS, product_rows)
    write_csv(SECTION_OUT, SECTION_FIELDS, section_rows)
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "cities": args.cities,
        "source_tour_rows": sum(
            1
            for city in args.cities
            for row in read_csv(PRODUCT_DIR / f"{city}_mcp_tna_products.csv")
            if row.get("category_value") == "tour"
        ),
        "unique_tour_products": len(tours),
        "cached_products": cache_count,
        "network_success_products": network_count,
        "failed_products": failed_count,
        "products_with_sections": sum(int(row["section_count"]) > 0 for row in product_rows),
        "section_rows": len(section_rows),
    }
    SUMMARY_OUT.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return 0 if failed_count == 0 else 2


if __name__ == "__main__":
    raise SystemExit(main())
