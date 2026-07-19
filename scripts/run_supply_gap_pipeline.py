#!/usr/bin/env python3
"""Run the T&A Supply Gap Map collection, rebuild, reporting, and QA pipeline."""

from __future__ import annotations

import argparse
import csv
import json
import subprocess
import sys
import time
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
SUMMARY = (
    ROOT
    / "data"
    / "supply_gap_analysis"
    / "reports"
    / "pipeline_run_summary.json"
)


@dataclass
class Step:
    name: str
    script: str
    args: list[str]
    kind: str
    network: bool = False

    def command(self) -> list[str]:
        return [sys.executable, "-B", str(ROOT / self.script), *self.args]


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="Reproduce the T&A Supply Gap Map from stored data or refresh network sources."
    )
    parser.add_argument(
        "--mode",
        choices=["rebuild", "refresh", "report", "verify"],
        default="rebuild",
        help="rebuild is deterministic from stored inputs; refresh performs network collection.",
    )
    parser.add_argument(
        "--cities",
        nargs="+",
        default=["후쿠오카", "히로시마"],
        help="MCP/detail collection cities used only in refresh mode.",
    )
    parser.add_argument("--max-pages", type=int, default=7)
    parser.add_argument("--mcp-delay", type=float, default=0.8)
    parser.add_argument("--detail-delay", type=float, default=3.0)
    parser.add_argument("--itinerary-delay", type=float, default=1.0)
    parser.add_argument(
        "--skip-official-refresh",
        action="store_true",
        help="In refresh mode, keep stored official source files.",
    )
    parser.add_argument("--skip-pdf", action="store_true")
    parser.add_argument("--skip-tests", action="store_true")
    parser.add_argument("--dry-run", action="store_true")
    return parser.parse_args()


def script_step(name: str, script_name: str, *, args: list[str] | None = None, kind: str, network: bool = False) -> Step:
    return Step(name, f"scripts/{script_name}", args or [], kind, network)


def rebuild_steps() -> list[Step]:
    return [
        script_step("filter_official_data", "filter_official_tourism_data.py", kind="transform"),
        script_step("build_official_anchors", "build_official_experience_anchors.py", kind="transform"),
        script_step("generate_alias_candidates", "generate_anchor_alias_candidates.py", kind="transform"),
        script_step("audit_fukuoka_product_details", "audit_fukuoka_product_details.py", kind="audit"),
        script_step("match_tour_details", "match_tour_details_to_official_places.py", kind="match"),
        script_step("match_official_to_mcp", "match_official_anchors_to_mcp.py", kind="match"),
        script_step("validate_reverse_hierarchy", "validate_reverse_hierarchy_audit.py", kind="human_review_gate"),
        script_step("audit_fukuoka_match_confidence", "audit_fukuoka_match_confidence.py", kind="audit"),
        script_step("audit_fukuoka_false_negatives", "audit_fukuoka_false_negative_candidates.py", kind="audit"),
        script_step("audit_fukuoka_city_scope", "audit_fukuoka_product_city_scope.py", kind="audit"),
        script_step("build_fukuoka_mcp_minus_official81", "build_fukuoka_mcp_minus_official81_list.py", kind="report"),
        script_step("export_exact_lists", "export_supply_gap_lists.py", kind="report"),
        script_step("build_fukuoka_trust_report", "build_fukuoka_trust_audit_report.py", kind="report"),
        script_step("rank_fukuoka_opportunities", "rank_fukuoka_opportunity_candidates.py", kind="report"),
        script_step("rank_kyoto_candidates", "rank_hidden_destination_candidates.py", kind="report"),
    ]


def report_steps() -> list[Step]:
    return [
        script_step("validate_reverse_hierarchy", "validate_reverse_hierarchy_audit.py", kind="human_review_gate"),
        script_step("audit_fukuoka_match_confidence", "audit_fukuoka_match_confidence.py", kind="audit"),
        script_step("audit_fukuoka_false_negatives", "audit_fukuoka_false_negative_candidates.py", kind="audit"),
        script_step("audit_fukuoka_city_scope", "audit_fukuoka_product_city_scope.py", kind="audit"),
        script_step("build_fukuoka_mcp_minus_official81", "build_fukuoka_mcp_minus_official81_list.py", kind="report"),
        script_step("export_exact_lists", "export_supply_gap_lists.py", kind="report"),
        script_step("build_fukuoka_trust_report", "build_fukuoka_trust_audit_report.py", kind="report"),
        script_step("rank_fukuoka_opportunities", "rank_fukuoka_opportunity_candidates.py", kind="report"),
        script_step("rank_kyoto_candidates", "rank_hidden_destination_candidates.py", kind="report"),
    ]


def refresh_steps(args: argparse.Namespace) -> list[Step]:
    steps: list[Step] = []
    if not args.skip_official_refresh:
        steps.extend(
            [
                script_step("collect_official_open_data", "collect_official_tourism_data.py", kind="collect", network=True),
                script_step("collect_fukuoka_official_guide", "collect_fukuoka_official_guide.py", kind="collect", network=True),
                script_step("collect_fukuoka_official_tours", "collect_fukuoka_official_tours.py", kind="collect", network=True),
            ]
        )
    steps.extend(
        [
            script_step("filter_official_data", "filter_official_tourism_data.py", kind="transform"),
            script_step("build_official_anchors", "build_official_experience_anchors.py", kind="transform"),
        ]
    )
    mcp_args: list[str] = []
    for city in args.cities:
        mcp_args.extend(["--city", city])
    mcp_args.extend(
        [
            "--max-pages",
            str(args.max_pages),
            "--delay",
            str(args.mcp_delay),
            "--merge-existing",
            "--stop-on-429",
        ]
    )
    steps.extend(
        [
            script_step("collect_mcp_products", "collect_mcp_tna_products.py", args=mcp_args, kind="collect", network=True),
            script_step("generate_alias_candidates", "generate_anchor_alias_candidates.py", kind="transform"),
            script_step(
                "collect_tour_details",
                "collect_city_tour_details.py",
                args=["--cities", *args.cities, "--delay", str(args.detail_delay)],
                kind="collect",
                network=True,
            ),
            script_step(
                "collect_public_itineraries",
                "collect_public_tour_itineraries.py",
                args=["--cities", *args.cities, "--delay", str(args.itinerary_delay)],
                kind="collect",
                network=True,
            ),
            script_step("audit_fukuoka_product_details", "audit_fukuoka_product_details.py", kind="collect", network=True),
            script_step("match_tour_details", "match_tour_details_to_official_places.py", kind="match"),
            script_step("match_official_to_mcp", "match_official_anchors_to_mcp.py", kind="match"),
            script_step("enrich_pending_detail_evidence", "enrich_tour_detail_evidence.py", kind="collect", network=True),
            script_step("validate_reverse_hierarchy", "validate_reverse_hierarchy_audit.py", kind="human_review_gate"),
            script_step("audit_fukuoka_match_confidence", "audit_fukuoka_match_confidence.py", kind="audit"),
            script_step("audit_fukuoka_false_negatives", "audit_fukuoka_false_negative_candidates.py", kind="audit"),
            script_step("audit_fukuoka_city_scope", "audit_fukuoka_product_city_scope.py", kind="audit"),
            script_step("build_fukuoka_mcp_minus_official81", "build_fukuoka_mcp_minus_official81_list.py", kind="report"),
            script_step("export_exact_lists", "export_supply_gap_lists.py", kind="report"),
            script_step("build_fukuoka_trust_report", "build_fukuoka_trust_audit_report.py", kind="report"),
            script_step("rank_fukuoka_opportunities", "rank_fukuoka_opportunity_candidates.py", kind="report"),
            script_step("rank_kyoto_candidates", "rank_hidden_destination_candidates.py", kind="report"),
        ]
    )
    return steps


def verification_steps() -> list[Step]:
    return [
        Step(
            "unit_tests",
            "",
            [],
            "verify",
        )
    ]


def command_for(step: Step) -> list[str]:
    if step.name == "unit_tests":
        return [
            sys.executable,
            "-m",
            "unittest",
            "discover",
            "-s",
            str(ROOT / "tests"),
            "-p",
            "test_*.py",
        ]
    return step.command()


def read_city_metrics() -> list[dict[str, str]]:
    path = ROOT / "data" / "supply_gap_analysis" / "city_supply_coverage.csv"
    if not path.exists():
        return []
    with path.open(encoding="utf-8-sig", newline="") as f:
        return [dict(row) for row in csv.DictReader(f)]


def main() -> int:
    args = parse_args()
    if args.mode == "refresh":
        steps = refresh_steps(args)
    elif args.mode == "rebuild":
        steps = rebuild_steps()
    elif args.mode == "report":
        steps = report_steps()
    else:
        steps = []

    if not args.skip_pdf and args.mode in {"rebuild", "refresh", "report"}:
        steps.append(script_step("render_pdf", "render_supply_gap_pdf.py", kind="report"))
    if not args.skip_tests and args.mode in {"rebuild", "refresh", "verify"}:
        steps.extend(verification_steps())

    started = datetime.now().astimezone()
    results = []
    exit_code = 0
    for index, step in enumerate(steps, start=1):
        command = command_for(step)
        print(
            json.dumps(
                {
                    "event": "pipeline_step",
                    "index": index,
                    "total": len(steps),
                    "name": step.name,
                    "kind": step.kind,
                    "network": step.network,
                    "command": command,
                },
                ensure_ascii=False,
            ),
            flush=True,
        )
        if args.dry_run:
            results.append({"name": step.name, "status": "dry_run", "seconds": 0})
            continue
        step_started = time.monotonic()
        completed = subprocess.run(command, cwd=ROOT, check=False)
        elapsed = round(time.monotonic() - step_started, 3)
        status = "passed" if completed.returncode == 0 else "failed"
        results.append(
            {
                "name": step.name,
                "kind": step.kind,
                "network": step.network,
                "status": status,
                "returncode": completed.returncode,
                "seconds": elapsed,
            }
        )
        if completed.returncode != 0:
            exit_code = completed.returncode
            break

    finished = datetime.now().astimezone()
    summary = {
        "mode": args.mode,
        "status": "dry_run" if args.dry_run else ("passed" if exit_code == 0 else "failed"),
        "started_at": started.isoformat(timespec="seconds"),
        "finished_at": finished.isoformat(timespec="seconds"),
        "elapsed_seconds": round((finished - started).total_seconds(), 3),
        "cities": args.cities,
        "network_steps_requested": [
            step.name for step in steps if step.network
        ],
        "steps": results,
        "city_metrics": read_city_metrics() if not args.dry_run else [],
    }
    SUMMARY.parent.mkdir(parents=True, exist_ok=True)
    SUMMARY.write_text(json.dumps(summary, ensure_ascii=False, indent=2), encoding="utf-8")
    print(json.dumps(summary, ensure_ascii=False), flush=True)
    return exit_code


if __name__ == "__main__":
    raise SystemExit(main())
