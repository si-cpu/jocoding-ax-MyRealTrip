#!/usr/bin/env python3
"""Minimal MyRealTrip Partner REST API client.

The API key is read only from MYREALTRIP_API_KEY and is never printed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import json
import os
import re
import sys
import urllib.error
import urllib.request
from typing import Any


BASE_URL = "https://partner-ext-api.myrealtrip.com"
API_KEY_ENV = "MYREALTRIP_API_KEY"
IATA_PATTERN = re.compile(r"^[A-Z]{3}$")


class ApiError(RuntimeError):
    pass


def normalize_text(value: str) -> str:
    return re.sub(r"\s+", "", value).casefold()


def require_iata(value: str) -> str:
    code = value.strip().upper()
    if not IATA_PATTERN.fullmatch(code):
        raise ValueError(f"Expected a 3-letter IATA airport code, got: {value!r}")
    return code


def require_iso_date(value: str) -> str:
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Expected date in YYYY-MM-DD format, got: {value!r}") from exc
    return value


def require_trip_period(value: int) -> int:
    if not 3 <= value <= 7:
        raise ValueError("Flight period must be between 3 and 7 days")
    return value


def exact_city_regions(regions: list[dict[str, Any]], city: str) -> list[dict[str, Any]]:
    target = normalize_text(city)
    return [
        region
        for region in regions
        if region.get("type") == "CITY"
        and target
        in {
            normalize_text(str(region.get("name", ""))),
            normalize_text(str(region.get("enName", ""))),
        }
    ]


def item_city(description: str) -> str:
    return description.split("∙", 1)[0].strip()


def filter_tna_items_by_city(
    items: list[dict[str, Any]], city: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target = normalize_text(city)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item in items:
        declared_city = item_city(str(item.get("description", "")))
        if declared_city and normalize_text(declared_city) == target:
            accepted.append(item)
        else:
            rejected.append(
                {
                    "gid": item.get("gid"),
                    "itemName": item.get("itemName"),
                    "description": item.get("description"),
                    "reason": "CITY_MISMATCH_OR_MISSING",
                }
            )
    return accepted, rejected


def api_key() -> str:
    value = os.environ.get(API_KEY_ENV, "").strip()
    if not value:
        raise ApiError(
            f"{API_KEY_ENV} is not set. Configure it in the shell environment; "
            "never paste API keys into prompts or logs."
        )
    return value


def post(path: str, payload: dict[str, Any]) -> dict[str, Any]:
    request = urllib.request.Request(
        f"{BASE_URL}{path}",
        data=json.dumps(payload, ensure_ascii=False).encode("utf-8"),
        headers={
            "Authorization": f"Bearer {api_key()}",
            "Content-Type": "application/json",
            "Accept": "application/json",
        },
        method="POST",
    )
    try:
        with urllib.request.urlopen(request, timeout=30) as response:
            return json.loads(response.read().decode("utf-8"))
    except urllib.error.HTTPError as exc:
        body = exc.read().decode("utf-8", errors="replace")
        raise ApiError(f"MyRealTrip API HTTP {exc.code}: {body[:500]}") from exc
    except urllib.error.URLError as exc:
        raise ApiError(f"MyRealTrip API connection failed: {exc.reason}") from exc


def unwrap(response: dict[str, Any]) -> Any:
    result = response.get("result", {})
    if result.get("status") not in (None, 200):
        raise ApiError(
            f"MyRealTrip API error {result.get('status')}: "
            f"{result.get('code')} {result.get('message')}"
        )
    return response.get("data")


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("tna-categories")
    p.add_argument("--city", required=True)
    add_common_arguments(p)

    p = sub.add_parser("tna-search")
    p.add_argument("--keyword", required=True)
    p.add_argument("--city", help="Exact city used for deterministic post-filtering")
    p.add_argument("--category")
    p.add_argument("--sort", choices=["price_asc", "price_desc", "review_score_desc", "selling_count_desc"])
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--size", type=int, default=50)
    add_common_arguments(p)

    p = sub.add_parser("tna-detail")
    p.add_argument("--gid", required=True)
    add_common_arguments(p)

    p = sub.add_parser("tna-options")
    p.add_argument("--gid", required=True)
    p.add_argument("--date", required=True, help="Selected date in YYYY-MM-DD format")
    add_common_arguments(p)

    p = sub.add_parser("stay-regions")
    p.add_argument("--keyword", required=True)
    p.add_argument("--is-domestic", choices=["true", "false"], required=True)
    p.add_argument("--exact-city", action="store_true")
    add_common_arguments(p)

    p = sub.add_parser("stay-search")
    p.add_argument("--region-id", type=int, required=True)
    p.add_argument("--check-in", required=True)
    p.add_argument("--check-out", required=True)
    p.add_argument("--adults", type=int, default=1)
    p.add_argument("--children", type=int, default=0)
    p.add_argument("--star-rating")
    p.add_argument("--page", type=int, default=0)
    p.add_argument("--size", type=int, default=20)
    add_common_arguments(p)

    p = sub.add_parser("airport-autocomplete")
    p.add_argument("--keyword", required=True)
    p.add_argument("--size", type=int, default=20)
    add_common_arguments(p)

    p = sub.add_parser("flight-bulk-lowest")
    p.add_argument("--departure", required=True)
    p.add_argument("--period", type=int, required=True)
    add_common_arguments(p)

    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "tna-categories":
        return {"data": unwrap(post("/v1/products/tna/categories", {"city": args.city}))}

    if args.command == "tna-search":
        if args.page < 1 or not 1 <= args.size <= 100:
            raise ValueError("TNA page starts at 1 and size must be between 1 and 100")
        payload: dict[str, Any] = {
            "keyword": args.keyword,
            "page": args.page,
            "size": args.size,
        }
        for key in ("category", "sort"):
            value = getattr(args, key)
            if value:
                payload[key] = value
        data = unwrap(post("/v1/products/tna/search", payload)) or {}
        if not args.city:
            return {"data": data}
        accepted, rejected = filter_tna_items_by_city(data.get("items", []), args.city)
        filtered = dict(data)
        filtered["items"] = accepted
        return {
            "requestedCity": args.city,
            "data": filtered,
            "discardedCityMismatches": rejected,
        }

    if args.command == "tna-detail":
        return {"data": unwrap(post("/v1/products/tna/detail", {"gid": args.gid}))}

    if args.command == "tna-options":
        selected_date = require_iso_date(args.date)
        data = unwrap(
            post(
                "/v1/products/tna/options",
                {"gid": args.gid, "selectedDate": selected_date},
            )
        ) or {}
        options = data.get("options", [])
        return {
            "selectedDate": selected_date,
            "bookable": bool(options),
            "data": data,
        }

    if args.command == "stay-regions":
        domestic = args.is_domestic == "true"
        data = unwrap(
            post(
                "/v1/products/accommodation/region-autocomplete",
                {"keyword": args.keyword, "isDomestic": domestic},
            )
        ) or {}
        regions = data.get("regions", [])
        if args.exact_city:
            regions = exact_city_regions(regions, args.keyword)
        return {"data": {"regions": regions}}

    if args.command == "stay-search":
        if args.page < 0 or not 1 <= args.size <= 50:
            raise ValueError("Stay page starts at 0 and size must be between 1 and 50")
        payload = {
            "regionId": args.region_id,
            "checkIn": args.check_in,
            "checkOut": args.check_out,
            "adultCount": args.adults,
            "childCount": args.children,
            "page": args.page,
            "size": args.size,
        }
        if args.star_rating:
            payload["starRating"] = args.star_rating
        return {"data": unwrap(post("/v1/products/accommodation/search", payload))}

    if args.command == "airport-autocomplete":
        if not 1 <= args.size <= 100:
            raise ValueError("Airport autocomplete size must be between 1 and 100")
        data = unwrap(
            post(
                "/v1/products/flight/airport-autocomplete",
                {"keyword": args.keyword, "size": args.size},
            )
        ) or {}
        airports = []
        for entry in data.get("airports", []):
            airport = entry.get("airport", {})
            code = airport.get("code")
            if code:
                airports.append(
                    {
                        "airportCode": require_iata(str(code)),
                        "airportName": airport.get("koName") or airport.get("enName"),
                        "city": entry.get("city"),
                        "country": entry.get("country"),
                        "isoCode": entry.get("isoCode"),
                    }
                )
        return {
            "warning": "Use airportCode, never city.code, in flight API requests.",
            "data": {"airports": airports},
        }

    if args.command == "flight-bulk-lowest":
        departure = require_iata(args.departure)
        period = require_trip_period(args.period)
        data = unwrap(
            post(
                "/v1/products/flight/calendar/bulk-lowest",
                {"depCityCd": departure, "period": period},
            )
        )
        return {
            "departureAirportCode": departure,
            "tripPeriodDays": period,
            "scope": "INTERNATIONAL_ONLY",
            "priceType": "CALENDAR_LOWEST_NOT_LIVE_INVENTORY",
            "data": data,
        }

    raise ValueError(f"Unsupported command: {args.command}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run(args)
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
        return 0
    except (ApiError, ValueError, json.JSONDecodeError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
