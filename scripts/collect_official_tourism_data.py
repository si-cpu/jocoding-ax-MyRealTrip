#!/usr/bin/env python3
"""Collect official tourism/public asset datasets for T&A Supply Gap Map.

The script intentionally records both successful downloads and failures so the
remaining gaps can be solved manually later.
"""

from __future__ import annotations

import csv
import json
import re
import sys
import time
import urllib.parse
import urllib.request
from dataclasses import dataclass, asdict
from pathlib import Path
from typing import Iterable


ROOT = Path(__file__).resolve().parents[1]
BASE = ROOT / "data" / "official_tourism_sources"
RAW = BASE / "raw"
REPORTS = BASE / "reports"


@dataclass
class Target:
    city: str
    source_key: str
    dataset_name: str
    url: str
    expected_kind: str
    priority: str
    note: str


DIRECT_TARGETS = [
    Target(
        city="Japan",
        source_key="digital_agency_pref_open_data_list",
        dataset_name="Digital Agency prefecture open-data list",
        url="https://www.digital.go.jp/assets/contents/node/basic_page/field_ref_resources/2b1128e2-c699-4aa0-9206-37169a6697c8/7192f365/20260228_resources_opendata_lg_pref_list_02.csv",
        expected_kind="csv",
        priority="A2",
        note="Find prefectural open-data portals.",
    ),
    Target(
        city="Japan",
        source_key="digital_agency_municipality_open_data_list",
        dataset_name="Digital Agency municipality open-data list",
        url="https://www.digital.go.jp/assets/contents/node/basic_page/field_ref_resources/2b1128e2-c699-4aa0-9206-37169a6697c8/821f1348/20260228_resources_opendata_lg_mani_list_03.csv",
        expected_kind="csv",
        priority="A2",
        note="Find municipal open-data portals.",
    ),
    Target(
        city="Osaka",
        source_key="osaka_mapnavi_culture_tourism",
        dataset_name="Map Navi Osaka facility points: culture/tourism",
        url="https://www.mapnavi.city.osaka.lg.jp/osakacity/osakacity/opendatafile/map_1/CSV/opendata_1005.csv",
        expected_kind="csv",
        priority="A3",
        note="Culture/tourism facilities.",
    ),
    Target(
        city="Osaka",
        source_key="osaka_mapnavi_historic_sites",
        dataset_name="Map Navi Osaka facility points: famous/historic sites",
        url="https://www.mapnavi.city.osaka.lg.jp/osakacity/osakacity/opendatafile/map_1/CSV/opendata_1008.csv",
        expected_kind="csv",
        priority="A3",
        note="Shrines, temples, famous places, historic sites.",
    ),
    Target(
        city="Osaka",
        source_key="osaka_mapnavi_parks_sports",
        dataset_name="Map Navi Osaka facility points: parks/sports",
        url="https://www.mapnavi.city.osaka.lg.jp/osakacity/osakacity/opendatafile/map_1/CSV/opendata_1003.csv",
        expected_kind="csv",
        priority="A3",
        note="Parks and sports facilities; useful as secondary official assets.",
    ),
    Target(
        city="Hiroshima",
        source_key="hiroshima_tourism_facilities",
        dataset_name="Hiroshima open data: tourism facilities",
        url="https://hiroshima-opendata.dataeye.jp/resource_download/9858",
        expected_kind="csv",
        priority="A6",
        note="Official Hiroshima tourism open-data resource linked from Hiroshima city page.",
    ),
    Target(
        city="Hiroshima",
        source_key="hiroshima_events",
        dataset_name="Hiroshima open data: events",
        url="https://hiroshima-opendata.dataeye.jp/resource_download/9846",
        expected_kind="csv",
        priority="A6",
        note="Official Hiroshima event open-data resource linked from Hiroshima city page.",
    ),
    Target(
        city="Hiroshima",
        source_key="hiroshima_public_wifi",
        dataset_name="Hiroshima open data: public Wi-Fi access points",
        url="https://hiroshima-opendata.dataeye.jp/resource_download/9855",
        expected_kind="csv",
        priority="C",
        note="Official Hiroshima public Wi-Fi resource; collected as secondary data, not tourism anchor by default.",
    ),
    Target(
        city="Fukuoka",
        source_key="fukuoka_yatai_basic_info",
        dataset_name="Fukuoka open data: yatai basic information",
        url="https://data.bodik.jp/dataset/87ff2527-7486-42de-84c4-bc21e352d456/resource/328edbc1-6967-4d0a-8f6d-6678420f4fe2/download/20260703_yatai_opendata_r2.csv",
        expected_kind="csv",
        priority="A4",
        note="Official Fukuoka yatai basic information dataset; found via data.bodik.jp CKAN.",
    ),
]


CKAN_BASES = [
    {
        "city": "Fukuoka",
        "base": "https://data.bodik.jp",
        "priority": "A4/A5",
        "queries": ["屋台", "観光", "文化財", "イベント", "地域の魅力"],
        "note": "Fukuoka city BODIK/CKAN catalog.",
    },
    {
        "city": "Hiroshima",
        "base": "https://hiroshima-city.dataeye.jp",
        "priority": "A6",
        "queries": ["観光施設", "イベント", "文化財", "観光"],
        "note": "Candidate Hiroshima open-data CKAN endpoint.",
    },
    {
        "city": "Hiroshima",
        "base": "https://www.city.hiroshima.lg.jp",
        "priority": "A6",
        "queries": ["観光施設", "イベント", "文化財", "観光"],
        "note": "Fallback if official site exposes CKAN-compatible endpoint.",
    },
]


MANUAL_TARGETS = [
    {
        "city": "Nara",
        "source_key": "nara_official_tourism_assets",
        "need": "Find Nara prefecture/city official open-data resources for tourist facilities, events, cultural properties.",
        "reason": "No verified direct resource URL yet.",
        "priority": "B1",
    },
    {
        "city": "Beppu/Yufuin",
        "source_key": "oita_beppu_yufu_official_tourism_assets",
        "need": "Find Oita/Beppu/Yufu official open-data resources for onsen, tourist facilities, events.",
        "reason": "No verified direct resource URL yet.",
        "priority": "B2",
    },
]


def ensure_dirs() -> None:
    RAW.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)


def request_url(url: str, timeout: int = 12) -> tuple[bytes, dict[str, str]]:
    req = urllib.request.Request(
        url,
        headers={
            "User-Agent": "Mozilla/5.0 TNA-Supply-Gap-Map/0.1 (+portfolio research)",
            "Accept": "*/*",
        },
    )
    with urllib.request.urlopen(req, timeout=timeout) as resp:
        headers = {k.lower(): v for k, v in resp.headers.items()}
        return resp.read(), headers


def safe_name(name: str) -> str:
    return re.sub(r"[^A-Za-z0-9_.-]+", "_", name).strip("_")


def save_bytes(target: Target, data: bytes, headers: dict[str, str]) -> Path:
    suffix = ".csv" if target.expected_kind == "csv" else ".dat"
    out = RAW / f"{target.source_key}{suffix}"
    out.write_bytes(data)
    meta = {
        **asdict(target),
        "saved_path": str(out.relative_to(ROOT)),
        "bytes": len(data),
        "content_type": headers.get("content-type", ""),
        "downloaded_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
    }
    (RAW / f"{target.source_key}.meta.json").write_text(
        json.dumps(meta, ensure_ascii=False, indent=2), encoding="utf-8"
    )
    return out


def count_csv_rows(path: Path) -> int | None:
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                return max(sum(1 for _ in csv.reader(f)) - 1, 0)
        except UnicodeDecodeError:
            continue
        except Exception:
            return None
    return None


def ckan_action(base: str, action: str, params: dict[str, str]) -> dict:
    query = urllib.parse.urlencode(params)
    url = f"{base.rstrip('/')}/api/3/action/{action}?{query}"
    body, _ = request_url(url)
    return json.loads(body.decode("utf-8"))


def iter_ckan_resource_targets() -> Iterable[Target]:
    seen_resource_urls: set[str] = set()
    for catalog in CKAN_BASES:
        base = catalog["base"]
        for query in catalog["queries"]:
            try:
                result = ckan_action(base, "package_search", {"q": query, "rows": "5"})
            except Exception as exc:
                yield Target(
                    city=catalog["city"],
                    source_key=f"failed_catalog_{safe_name(catalog['city'])}_{safe_name(query)}",
                    dataset_name=f"FAILED CKAN search: {query}",
                    url=f"{base}/api/3/action/package_search?q={urllib.parse.quote(query)}",
                    expected_kind="error",
                    priority=catalog["priority"],
                    note=f"{catalog['note']} Error: {exc}",
                )
                continue
            if not result.get("success"):
                continue
            for package in result.get("result", {}).get("results", []):
                package_title = package.get("title") or package.get("name") or "untitled"
                for resource in package.get("resources", []):
                    resource_url = resource.get("url") or ""
                    fmt = (resource.get("format") or "").lower()
                    name = resource.get("name") or package_title
                    if not resource_url or resource_url in seen_resource_urls:
                        continue
                    if not any(token in fmt or resource_url.lower().endswith(f".{token}") for token in ["csv", "json", "xlsx"]):
                        continue
                    seen_resource_urls.add(resource_url)
                    ext = "json" if "json" in fmt or resource_url.lower().endswith(".json") else "csv"
                    if "xlsx" in fmt or resource_url.lower().endswith(".xlsx"):
                        ext = "xlsx"
                    source_key = safe_name(f"{catalog['city']}_{query}_{package.get('name','package')}_{resource.get('id','res')}")
                    yield Target(
                        city=catalog["city"],
                        source_key=source_key,
                        dataset_name=f"{package_title} / {name}",
                        url=resource_url,
                        expected_kind=ext,
                        priority=catalog["priority"],
                        note=f"CKAN search query={query}; package={package.get('name')}",
                    )


def collect() -> int:
    ensure_dirs()
    successes = []
    failures = []

    targets = list(DIRECT_TARGETS)
    ckan_targets = list(iter_ckan_resource_targets())
    downloadable_ckan_targets = [t for t in ckan_targets if t.expected_kind != "error"]
    targets.extend(downloadable_ckan_targets)
    failures.extend(
        {
            "city": t.city,
            "source_key": t.source_key,
            "dataset_name": t.dataset_name,
            "url": t.url,
            "priority": t.priority,
            "status": "catalog_failed",
            "reason": t.note,
        }
        for t in ckan_targets
        if t.expected_kind == "error"
    )

    for target in targets:
        try:
            data, headers = request_url(target.url)
            if len(data) == 0:
                raise RuntimeError("empty response")
            path = save_bytes(target, data, headers)
            successes.append(
                {
                    "city": target.city,
                    "source_key": target.source_key,
                    "dataset_name": target.dataset_name,
                    "url": target.url,
                    "priority": target.priority,
                    "path": str(path.relative_to(ROOT)),
                    "bytes": len(data),
                    "row_count": count_csv_rows(path) if path.suffix == ".csv" else None,
                    "content_type": headers.get("content-type", ""),
                    "note": target.note,
                }
            )
        except Exception as exc:
            failures.append(
                {
                    "city": target.city,
                    "source_key": target.source_key,
                    "dataset_name": target.dataset_name,
                    "url": target.url,
                    "priority": target.priority,
                    "status": "download_failed",
                    "reason": str(exc),
                    "note": target.note,
                }
            )

    failures.extend({**item, "status": "manual_lookup_needed"} for item in MANUAL_TARGETS)

    summary = {
        "generated_at": time.strftime("%Y-%m-%dT%H:%M:%S%z"),
        "success_count": len(successes),
        "failure_count": len(failures),
        "successes": successes,
        "failures": failures,
    }
    (REPORTS / "official_data_collection_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    lines = [
        "# Official Tourism Data Collection Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Successful downloads: {len(successes)}",
        f"- Failed/manual items: {len(failures)}",
        "",
        "## Successful downloads",
        "",
        "| City | Dataset | Rows | File | Source |",
        "|---|---|---:|---|---|",
    ]
    for item in successes:
        rows = "" if item["row_count"] is None else str(item["row_count"])
        lines.append(
            f"| {item['city']} | {item['dataset_name']} | {rows} | `{item['path']}` | {item['url']} |"
        )
    lines.extend(["", "## Failed or manual lookup needed", "", "| City | Dataset/Need | Status | Reason | URL |", "|---|---|---|---|---|"])
    for item in failures:
        lines.append(
            f"| {item.get('city','')} | {item.get('dataset_name') or item.get('need','')} | {item.get('status','')} | {str(item.get('reason','')).replace('|','/')} | {item.get('url','')} |"
        )
    (REPORTS / "OFFICIAL_DATA_COLLECTION_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(json.dumps({"success_count": len(successes), "failure_count": len(failures)}, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    sys.exit(collect())
