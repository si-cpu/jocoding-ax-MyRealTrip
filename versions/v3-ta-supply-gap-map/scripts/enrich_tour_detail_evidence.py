#!/usr/bin/env python3
"""Verify title-level tour matches against MCP detail text.

This script intentionally keeps detail verification separate from the first-pass
anchor match. A tour title can name a place even when the detail payload only
mentions that place in exclusions or does not expose the itinerary at all.
"""

from __future__ import annotations

import csv
import json
import re
import urllib.request
from datetime import datetime
from pathlib import Path
from typing import Any


ROOT = Path(__file__).resolve().parents[1]
ANALYSIS = ROOT / "data" / "supply_gap_analysis"
MATCHES = ANALYSIS / "official_mcp_anchor_matches.csv"
AUTO_ALIASES = ANALYSIS / "auto_anchor_alias_candidates.csv"
DETAIL_DIR = ANALYSIS / "detail_evidence"
RAW_DIR = DETAIL_DIR / "raw"
REPORTS = ANALYSIS / "reports"
OUT_CSV = DETAIL_DIR / "tour_detail_evidence.csv"
OUT_JSON = REPORTS / "tour_detail_evidence_summary.json"
OUT_MD = REPORTS / "TOUR_DETAIL_EVIDENCE_REPORT.md"
MCP_URL = "https://mcp-servers.myrealtrip.com/mcp"

FIELDS = [
    "anchor_id",
    "city_name",
    "anchor_name",
    "product_id",
    "product_title",
    "product_url",
    "title_evidence_text",
    "detail_evidence_level",
    "positive_alias_hits",
    "negative_alias_hits",
    "neutral_alias_hits",
    "positive_evidence_excerpt",
    "negative_evidence_excerpt",
    "detail_status",
]

NEGATIVE_LABELS = ("불포함", "취소", "환불", "유의", "제외")
POSITIVE_LABELS = ("일정", "코스", "포함", "이용 안내", "장소", "만나는", "집결", "상품")


def clean(text: str | None) -> str:
    return re.sub(r"\s+", " ", str(text or "")).strip()


def normalize(text: str | None) -> str:
    return re.sub(r"[^0-9a-z가-힣ぁ-んァ-ン一-龥]+", "", clean(text).casefold())


def read_csv(path: Path) -> list[dict[str, str]]:
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def write_csv(path: Path, fields: list[str], rows: list[dict[str, str]]) -> None:
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open("w", encoding="utf-8-sig", newline="") as f:
        writer = csv.DictWriter(f, fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


def load_auto_aliases() -> dict[str, list[str]]:
    if not AUTO_ALIASES.exists():
        return {}
    aliases: dict[str, list[str]] = {}
    for row in read_csv(AUTO_ALIASES):
        try:
            confidence = float(row.get("confidence") or 0)
            matched_count = int(row.get("matched_product_count") or 0)
        except ValueError:
            continue
        if confidence < 0.75 or matched_count <= 0:
            continue
        aliases.setdefault(row["anchor_id"], []).append(clean(row.get("alias_ko")))
    return aliases


def alias_candidates(match: dict[str, str], auto_aliases: dict[str, list[str]]) -> list[str]:
    values = [
        match.get("anchor_name"),
        match.get("evidence_text"),
        *auto_aliases.get(match["anchor_id"], []),
    ]
    extra: list[str] = []
    for value in values:
        value = clean(value)
        if value.endswith("성") and len(value) > 2:
            extra.append(value[:-1] + " 성")
        if "기념관" in value:
            extra.append(value.replace("기념관", " 기념관"))
            extra.append(value.replace("기념관", "기념자료관"))
            extra.append(value.replace("기념관", " 기념자료관"))
    values.extend(extra)
    return [v for v in dict.fromkeys(clean(v) for v in values) if len(normalize(v)) >= 2]


def request_detail(product_id: str, product_url: str) -> tuple[dict[str, Any] | None, str]:
    payload = {
        "jsonrpc": "2.0",
        "id": int(product_id) if product_id.isdigit() else 1,
        "method": "tools/call",
        "params": {
            "name": "getTnaDetail",
            "arguments": {"gid": product_id, "url": product_url},
        },
    }
    req = urllib.request.Request(
        MCP_URL,
        data=json.dumps(payload).encode("utf-8"),
        headers={"Accept": "application/json, text/event-stream", "Content-Type": "application/json"},
        method="POST",
    )
    try:
        with urllib.request.urlopen(req, timeout=60) as resp:
            text = resp.read().decode("utf-8", errors="replace")
    except Exception as exc:  # pragma: no cover - network availability varies
        return None, f"request_failed: {exc}"
    try:
        return json.loads(text), "ok"
    except json.JSONDecodeError as exc:
        return {"raw_response": text}, f"json_parse_failed: {exc}"


def parse_detail_payload(raw: dict[str, Any]) -> dict[str, Any]:
    content = raw.get("result", {}).get("content", [])
    if content and isinstance(content[0], dict):
        text = content[0].get("text") or ""
    else:
        text = raw.get("raw_response", "")
    try:
        inner = json.loads(text)
    except Exception:
        inner = {"copy_text": text}
    return inner


def collect_widget_sections(node: Any, current_label: str = "") -> list[tuple[str, str]]:
    sections: list[tuple[str, str]] = []
    if isinstance(node, dict):
        typ = node.get("type")
        value = clean(node.get("value") or node.get("label"))
        next_label = current_label
        if typ in {"Title", "Heading"} and value:
            next_label = value
        elif value:
            sections.append((current_label, value))
        child_label = next_label
        for child in node.get("children") or []:
            if isinstance(child, dict) and child.get("type") in {"Title", "Heading"} and clean(child.get("value")):
                child_label = clean(child.get("value"))
                continue
            child_sections = collect_widget_sections(child, child_label)
            sections.extend(child_sections)
    elif isinstance(node, list):
        child_label = current_label
        for child in node:
            if isinstance(child, dict) and child.get("type") in {"Title", "Heading"} and clean(child.get("value")):
                child_label = clean(child.get("value"))
                continue
            sections.extend(collect_widget_sections(child, child_label))
    return sections


def sections_from_detail(inner: dict[str, Any]) -> list[tuple[str, str, str]]:
    result: list[tuple[str, str, str]] = []
    for label, text in collect_widget_sections(inner.get("widget", {})):
        label_norm = clean(label)
        if any(word in label_norm for word in NEGATIVE_LABELS):
            section_type = "negative"
        elif any(word in label_norm for word in POSITIVE_LABELS):
            section_type = "positive"
        else:
            section_type = "neutral"
        result.append((section_type, label_norm, clean(text)))
    copy_text = clean(inner.get("copy_text"))
    if copy_text:
        result.append(("neutral", "copy_text", copy_text))
    return result


def find_hits(sections: list[tuple[str, str, str]], aliases: list[str]) -> dict[str, list[str]]:
    hits = {"positive": [], "negative": [], "neutral": []}
    norm_aliases = [(alias, normalize(alias)) for alias in aliases]
    for section_type, label, text in sections:
        haystack = normalize(f"{label} {text}")
        for alias, alias_norm in norm_aliases:
            if alias_norm and alias_norm in haystack:
                hits[section_type].append(alias)
    return {key: sorted(set(values)) for key, values in hits.items()}


def excerpt_for_hit(sections: list[tuple[str, str, str]], aliases: list[str], wanted_type: str) -> str:
    norm_aliases = [normalize(alias) for alias in aliases]
    for section_type, label, text in sections:
        if section_type != wanted_type:
            continue
        haystack = normalize(f"{label} {text}")
        if any(alias and alias in haystack for alias in norm_aliases):
            return clean(f"{label}: {text}")[:240]
    return ""


def md_cell(text: str) -> str:
    return clean(text).replace("|", ",")


def classify(hits: dict[str, list[str]], status: str) -> str:
    if status != "ok":
        return "detail_unavailable"
    if hits["positive"]:
        return "detail_confirmed"
    if hits["negative"] and not hits["positive"]:
        return "exclusion_only"
    if hits["neutral"]:
        return "detail_text_neutral_only"
    return "detail_unavailable"


def main() -> int:
    DETAIL_DIR.mkdir(parents=True, exist_ok=True)
    RAW_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS.mkdir(parents=True, exist_ok=True)

    auto_aliases = load_auto_aliases()
    matches = [
        row
        for row in read_csv(MATCHES)
        if row.get("evidence_level") == "tour_title_needs_detail"
    ]

    rows = []
    for match in matches:
        product_id = match["product_id"]
        raw_path = RAW_DIR / f"{product_id}.json"
        raw_needs_refresh = False
        if raw_path.exists():
            raw = json.loads(raw_path.read_text(encoding="utf-8"))
            if "error" in raw:
                raw_needs_refresh = True
                status = raw.get("error", "cached_error")
            else:
                status = "ok_cached"
        if raw_needs_refresh or not raw_path.exists():
            raw, status = request_detail(product_id, match["product_url"])
            if raw is None:
                raw = {"error": status}
            raw_path.write_text(json.dumps(raw, ensure_ascii=False, indent=2), encoding="utf-8")
        inner = parse_detail_payload(raw)
        sections = sections_from_detail(inner)
        aliases = alias_candidates(match, auto_aliases)
        hits = find_hits(sections, aliases)
        level = classify(hits, "ok" if status == "ok_cached" else status)
        rows.append(
            {
                "anchor_id": match["anchor_id"],
                "city_name": match["city_name"],
                "anchor_name": match["anchor_name"],
                "product_id": product_id,
                "product_title": match["product_title"],
                "product_url": match["product_url"],
                "title_evidence_text": match.get("evidence_text", ""),
                "detail_evidence_level": level,
                "positive_alias_hits": " | ".join(hits["positive"]),
                "negative_alias_hits": " | ".join(hits["negative"]),
                "neutral_alias_hits": " | ".join(hits["neutral"]),
                "positive_evidence_excerpt": excerpt_for_hit(sections, hits["positive"], "positive"),
                "negative_evidence_excerpt": excerpt_for_hit(sections, hits["negative"], "negative"),
                "detail_status": status,
            }
        )

    write_csv(OUT_CSV, FIELDS, rows)
    counts: dict[str, int] = {}
    for row in rows:
        counts[row["detail_evidence_level"]] = counts.get(row["detail_evidence_level"], 0) + 1
    summary = {
        "generated_at": datetime.now().astimezone().isoformat(timespec="seconds"),
        "checked_tour_title_matches": len(rows),
        "detail_evidence_counts": counts,
        "raw_detail_dir": str(RAW_DIR.relative_to(ROOT)),
        "output_csv": str(OUT_CSV.relative_to(ROOT)),
    }
    OUT_JSON.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")

    lines = [
        "# Tour Detail Evidence Report",
        "",
        f"- Generated at: {summary['generated_at']}",
        f"- Checked title-level tour matches: {summary['checked_tour_title_matches']}",
        f"- Detail evidence counts: {summary['detail_evidence_counts']}",
        "",
        "## Interpretation rule",
        "",
        "- `detail_confirmed`: positive detail/itinerary/inclusion text directly names the place.",
        "- `exclusion_only`: the place appears only in exclusion text; never treat this as a confirmed visit.",
        "- `detail_text_neutral_only`: the detail payload mentions the place, but not in a strong positive section.",
        "- `detail_unavailable`: MCP detail failed or did not expose enough text.",
        "",
        "## Checked products",
        "",
        "| City | Official place | Product | Detail evidence | Positive hits | Negative hits | Note |",
        "|---|---|---|---|---|---|---|",
    ]
    for row in rows:
        note = row["positive_evidence_excerpt"] or row["negative_evidence_excerpt"] or row["detail_status"]
        lines.append(
            "| {city} | {place} | {product} | `{level}` | {pos} | {neg} | {note} |".format(
                city=row["city_name"],
                place=row["anchor_name"],
                product=row["product_title"].replace("|", "/"),
                level=row["detail_evidence_level"],
                pos=md_cell(row["positive_alias_hits"] or "-"),
                neg=md_cell(row["negative_alias_hits"] or "-"),
                note=md_cell(note),
            )
        )
    OUT_MD.write_text("\n".join(lines) + "\n", encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
