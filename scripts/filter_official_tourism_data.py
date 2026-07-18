#!/usr/bin/env python3
"""Filter collected official tourism datasets into usable MVP buckets."""

from __future__ import annotations

import csv
import json
from collections import Counter
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
RAW = ROOT / "data" / "official_tourism_sources" / "raw"
PROCESSED = ROOT / "data" / "official_tourism_sources" / "processed"
REPORTS = ROOT / "data" / "official_tourism_sources" / "reports"

FUKUOKA_CITY_CODES = {"401307"}
HIROSHIMA_CITY_CODES = {"341002"}


def read_csv_rows(path: Path) -> tuple[list[str], list[dict[str, str]], str]:
    last_error = None
    for encoding in ("utf-8-sig", "utf-8", "cp932"):
        try:
            with path.open("r", encoding=encoding, newline="") as f:
                reader = csv.DictReader(f)
                fieldnames = list(reader.fieldnames or [])
                rows = [dict(row) for row in reader]
            return fieldnames, rows, encoding
        except UnicodeDecodeError as exc:
            last_error = exc
    raise RuntimeError(f"Could not decode {path}: {last_error}")


def write_csv(path: Path, fieldnames: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(rows)


def read_all_csv(path: Path) -> tuple[list[str], list[dict[str, str]]]:
    fieldnames, rows, _ = read_csv_rows(path)
    return fieldnames, rows


def find_first(row: dict[str, str], keys: list[str]) -> str:
    for key in keys:
        if key in row and row[key]:
            return str(row[key]).strip()
    return ""


def row_city_code(row: dict[str, str]) -> str:
    return find_first(
        row,
        [
            "全国地方公共団体コード",
            "都道府県コード又は市区町村コード",
            "市区町村コード",
            "市町村コード",
            "観光ポイント_全国地方公共団体コード",
            "所在地_全国地方公共団体コード",
        ],
    )


def row_city_name(row: dict[str, str]) -> str:
    return find_first(
        row,
        [
            "市区町村名",
            "地方公共団体名",
            "所在地_市区町村",
            "市町村名",
        ],
    )


def classify_fukuoka_file(path: Path, meta: dict, rows: list[dict[str, str]]) -> tuple[str, str]:
    dataset = meta.get("dataset_name", "")
    note = meta.get("note", "")
    url = meta.get("url", "")
    text = f"{dataset} {note} {url} {path.name}"

    if "401307_yataiopendata" in text or "福岡市　屋台基本情報" in dataset or path.name == "fukuoka_yatai_basic_info.csv":
        return "accepted", "Fukuoka yatai dataset directly tied to 福岡市 / 401307"

    codes = Counter(row_city_code(row) for row in rows if row_city_code(row))
    names = Counter(row_city_name(row) for row in rows if row_city_name(row))

    if codes and set(codes).issubset(FUKUOKA_CITY_CODES):
        return "accepted", "All detected municipality codes are 401307"
    if names and set(names).issubset({"福岡市", "福岡県福岡市"}):
        return "accepted", "All detected municipality names are 福岡市"

    if codes:
        return "rejected_or_later_city", f"Detected non-Fukuoka municipality codes: {dict(codes.most_common(5))}"
    if names:
        return "needs_review", f"No reliable code; detected city names: {dict(names.most_common(5))}"
    return "needs_review", "No city code/name columns detected"


def classify_hiroshima_file(path: Path, meta: dict, rows: list[dict[str, str]]) -> tuple[str, str]:
    if path.name == "hiroshima_public_wifi.csv":
        return "secondary", "Official Hiroshima public Wi-Fi; useful as convenience data, not a tourism anchor by default"
    codes = Counter(row_city_code(row) for row in rows if row_city_code(row))
    if codes and set(codes).issubset(HIROSHIMA_CITY_CODES):
        return "accepted", "All detected municipality codes are 341002"
    return "needs_review", f"Hiroshima source but code validation incomplete: {dict(codes.most_common(5))}"


def main() -> int:
    PROCESSED.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    manifest = []
    outputs = []

    for path in sorted(RAW.glob("*.csv")):
        meta_path = RAW / f"{path.stem}.meta.json"
        meta = json.loads(meta_path.read_text(encoding="utf-8")) if meta_path.exists() else {}
        fieldnames, rows, encoding = read_csv_rows(path)

        if path.name.startswith("digital_agency_"):
            bucket = "reference"
            reason = "Digital Agency open-data local-government reference list"
        elif path.name.startswith("hiroshima_"):
            bucket, reason = classify_hiroshima_file(path, meta, rows)
            if path.name == "hiroshima_tourism_facilities.csv":
                city_rows = [row for row in rows if row_city_code(row) in HIROSHIMA_CITY_CODES]
                other_rows = [row for row in rows if row_city_code(row) not in HIROSHIMA_CITY_CODES]
                if city_rows:
                    out_path = PROCESSED / "accepted" / "hiroshima_tourism_facilities_city_only.csv"
                    write_csv(out_path, fieldnames, city_rows)
                    manifest.append(
                        {
                            "source_file": str(path.relative_to(ROOT)),
                            "processed_file": str(out_path.relative_to(ROOT)),
                            "dataset_name": f"{meta.get('dataset_name', '')} / city-only split",
                            "source_url": meta.get("url", ""),
                            "bucket": "accepted",
                            "reason": f"Row-level split: kept {len(city_rows)} rows with municipality code 341002",
                            "row_count": len(city_rows),
                            "encoding": encoding,
                        }
                    )
                if other_rows:
                    out_path = PROCESSED / "rejected_or_later_city" / "hiroshima_tourism_facilities_non_city_rows.csv"
                    write_csv(out_path, fieldnames, other_rows)
                    manifest.append(
                        {
                            "source_file": str(path.relative_to(ROOT)),
                            "processed_file": str(out_path.relative_to(ROOT)),
                            "dataset_name": f"{meta.get('dataset_name', '')} / non-city rows",
                            "source_url": meta.get("url", ""),
                            "bucket": "rejected_or_later_city",
                            "reason": f"Row-level split: stored {len(other_rows)} rows outside Hiroshima city as later-city candidates",
                            "row_count": len(other_rows),
                            "encoding": encoding,
                        }
                    )
                continue
        elif path.name.startswith("Fukuoka") or path.name == "fukuoka_yatai_basic_info.csv":
            bucket, reason = classify_fukuoka_file(path, meta, rows)
        else:
            bucket = "needs_review"
            reason = "No filter rule"

        rel_out = ""
        if bucket in {"accepted", "secondary", "reference", "rejected_or_later_city"}:
            out_dir = PROCESSED / bucket
            out_path = out_dir / path.name
            write_csv(out_path, fieldnames, rows)
            rel_out = str(out_path.relative_to(ROOT))
            outputs.append(out_path)

        manifest.append(
            {
                "source_file": str(path.relative_to(ROOT)),
                "processed_file": rel_out,
                "dataset_name": meta.get("dataset_name", ""),
                "source_url": meta.get("url", ""),
                "bucket": bucket,
                "reason": reason,
                "row_count": len(rows),
                "encoding": encoding,
            }
        )

    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "total_csv_files": len(manifest),
        "bucket_counts": dict(Counter(item["bucket"] for item in manifest)),
        "accepted_rows": sum(item["row_count"] for item in manifest if item["bucket"] == "accepted"),
        "secondary_rows": sum(item["row_count"] for item in manifest if item["bucket"] == "secondary"),
        "reference_rows": sum(item["row_count"] for item in manifest if item["bucket"] == "reference"),
        "items": manifest,
    }

    (REPORTS / "official_data_filter_summary.json").write_text(
        json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8"
    )

    build_curated_yatai()

    lines = [
        "# Official Tourism Data Filter Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- CSV files inspected: {summary['total_csv_files']}",
        f"- Bucket counts: {summary['bucket_counts']}",
        f"- Accepted rows: {summary['accepted_rows']}",
        f"- Secondary rows: {summary['secondary_rows']}",
        f"- Reference rows: {summary['reference_rows']}",
        "",
        "## Filtered files",
        "",
        "| Bucket | Rows | Source file | Processed file | Reason |",
        "|---|---:|---|---|---|",
    ]
    for item in manifest:
        lines.append(
            f"| {item['bucket']} | {item['row_count']} | `{item['source_file']}` | `{item['processed_file']}` | {item['reason'].replace('|', '/')} |"
        )
    (REPORTS / "OFFICIAL_DATA_FILTER_REPORT.md").write_text(
        "\n".join(lines) + "\n", encoding="utf-8"
    )

    print(json.dumps({k: summary[k] for k in ["total_csv_files", "bucket_counts", "accepted_rows"]}, ensure_ascii=False))
    return 0


def build_curated_yatai() -> None:
    candidates = [
        RAW / "fukuoka_yatai_basic_info.csv",
        RAW / "Fukuoka___401307_yataiopendata_328edbc1-6967-4d0a-8f6d-6678420f4fe2.csv",
        RAW / "Fukuoka___isit_yartai_e03a1f32-25ab-42ec-80c3-e7369e11dadd.csv",
        RAW / "Fukuoka___isit_yatai_4f07763f-bc6e-4c4a-8e2c-314eb9032247.csv",
    ]
    merged: dict[str, dict[str, str]] = {}
    fieldnames: list[str] = []
    for path in candidates:
        if not path.exists():
            continue
        headers, rows = read_all_csv(path)
        if len(headers) > len(fieldnames):
            fieldnames = headers
        for row in rows:
            key = row.get("屋台ID") or row.get("名称") or json.dumps(row, ensure_ascii=False)
            # Prefer newer/full official 20260703 files by processing them last in candidates order above.
            merged[key] = row

    if not merged:
        return

    curated = list(merged.values())
    out_path = PROCESSED / "curated" / "fukuoka_yatai_curated.csv"
    write_csv(out_path, fieldnames, curated)

    summary_path = REPORTS / "fukuoka_yatai_curated_summary.json"
    summary_path.write_text(
        json.dumps(
            {
                "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
                "source_files": [str(p.relative_to(ROOT)) for p in candidates if p.exists()],
                "dedupe_key": "屋台ID",
                "row_count": len(curated),
                "output": str(out_path.relative_to(ROOT)),
            },
            ensure_ascii=False,
            indent=2,
        ),
        encoding="utf-8",
    )


if __name__ == "__main__":
    raise SystemExit(main())
