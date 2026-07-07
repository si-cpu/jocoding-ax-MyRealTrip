#!/usr/bin/env python3
"""MyRealTrip TNA collector for evidence-backed content indexing.

The API key is read only from MYREALTRIP_API_KEY and is never printed.
"""

from __future__ import annotations

import argparse
import datetime as dt
import html
import json
import os
import re
import sys
import urllib.error
import urllib.parse
import urllib.request
from typing import Any


BASE_URL = "https://partner-ext-api.myrealtrip.com"
API_KEY_ENV = "MYREALTRIP_API_KEY"
ALLOWED_PRODUCT_HOSTS = {"myrealtrip.com"}


class ApiError(RuntimeError):
    pass


class UnsafeRedirectError(RuntimeError):
    pass


class SafeProductRedirectHandler(urllib.request.HTTPRedirectHandler):
    def redirect_request(
        self,
        request: urllib.request.Request,
        file_pointer: Any,
        code: int,
        message: str,
        headers: Any,
        new_url: str,
    ) -> urllib.request.Request | None:
        try:
            validate_product_url(new_url)
        except ValueError as exc:
            raise UnsafeRedirectError(new_url) from exc
        return super().redirect_request(
            request, file_pointer, code, message, headers, new_url
        )


def normalize_text(value: str) -> str:
    return re.sub(r"[^0-9a-z가-힣]+", "", value.casefold())


def strip_html(value: str) -> str:
    without_tags = re.sub(r"<[^>]+>", " ", value or "")
    return re.sub(r"\s+", " ", html.unescape(without_tags)).strip()


def require_iso_date(value: str) -> str:
    try:
        dt.date.fromisoformat(value)
    except ValueError as exc:
        raise ValueError(f"Expected date in YYYY-MM-DD format, got: {value!r}") from exc
    return value


def item_city(description: str) -> str:
    return description.split("∙", 1)[0].strip()


def classify_purchase_form(item: dict[str, Any]) -> str:
    """Describe how an experience is sold without treating it as the experience."""
    text = normalize_text(
        " ".join(
            str(item.get(field, ""))
            for field in ("category", "itemName", "title", "description")
        )
    )
    rules = (
        ("PASS", ("패스", "pass")),
        ("FOOD", ("식사권", "레스토랑", "푸드투어", "쿠킹", "미식")),
        ("TOUR", ("투어", "가이드")),
        ("ACTIVITY", ("액티비티", "체험", "클래스", "워크숍")),
        ("SCENIC_TRANSPORT", ("로프웨이", "케이블카", "크루즈", "유람선", "관광열차", "스카이캡슐", "해변열차")),
        ("TRANSPORT", ("이동교통", "교통편의", "공항철도", "공항버스", "픽업", "샌딩", "렌터카")),
        ("ADMISSION", ("입장권", "티켓", "관람권")),
    )
    for form, tokens in rules:
        if any(normalize_text(token) in text for token in tokens):
            return form
    return "OTHER"


def is_allowed_product_host(hostname: str | None) -> bool:
    host = (hostname or "").rstrip(".").casefold()
    return any(host == allowed or host.endswith(f".{allowed}") for allowed in ALLOWED_PRODUCT_HOSTS)


def validate_product_url(value: str) -> str:
    url = value.strip()
    parsed = urllib.parse.urlsplit(url)
    if parsed.scheme != "https":
        raise ValueError("Product URL must use HTTPS")
    if parsed.username or parsed.password or parsed.port:
        raise ValueError("Product URL must not contain credentials or a custom port")
    if not is_allowed_product_host(parsed.hostname):
        raise ValueError("Product URL must use an official MyRealTrip domain")
    if not parsed.path or parsed.path == "/":
        raise ValueError("Product URL must point to a product path")
    return url


def open_product_request(
    request: urllib.request.Request, timeout: int
) -> Any:
    opener = urllib.request.build_opener(SafeProductRedirectHandler())
    return opener.open(request, timeout=timeout)


def check_product_url(value: str, timeout: int = 15) -> dict[str, Any]:
    url = validate_product_url(value)
    request = urllib.request.Request(
        url,
        headers={"User-Agent": "Mozilla/5.0 MyRealTripContentMap/0.5"},
        method="HEAD",
    )
    try:
        response = open_product_request(request, timeout)
    except UnsafeRedirectError as exc:
        return {
            "url": url,
            "finalUrl": str(exc),
            "reachable": False,
            "status": None,
            "reason": "UNSAFE_REDIRECT",
        }
    except urllib.error.HTTPError as exc:
        if exc.code not in (403, 405):
            return {"url": url, "reachable": False, "status": exc.code, "reason": "HTTP_ERROR"}
        request = urllib.request.Request(
            url,
            headers={
                "User-Agent": "Mozilla/5.0 MyRealTripContentMap/0.5",
                "Range": "bytes=0-0",
            },
            method="GET",
        )
        try:
            response = open_product_request(request, timeout)
        except UnsafeRedirectError as retry_exc:
            return {
                "url": url,
                "finalUrl": str(retry_exc),
                "reachable": False,
                "status": None,
                "reason": "UNSAFE_REDIRECT",
            }
        except urllib.error.HTTPError as retry_exc:
            return {
                "url": url,
                "reachable": False,
                "status": retry_exc.code,
                "reason": "HTTP_ERROR",
            }
        except urllib.error.URLError as retry_exc:
            return {"url": url, "reachable": False, "status": None, "reason": str(retry_exc.reason)}
    except urllib.error.URLError as exc:
        return {"url": url, "reachable": False, "status": None, "reason": str(exc.reason)}

    with response:
        final_url = response.geturl()
        status = response.getcode()
    try:
        validate_product_url(final_url)
    except ValueError:
        return {
            "url": url,
            "finalUrl": final_url,
            "reachable": False,
            "status": status,
            "reason": "UNSAFE_REDIRECT",
        }
    return {
        "url": url,
        "finalUrl": final_url,
        "reachable": 200 <= status < 400,
        "status": status,
        "reason": None if 200 <= status < 400 else "HTTP_ERROR",
    }


def partition_tna_items(
    items: list[dict[str, Any]], city: str
) -> tuple[list[dict[str, Any]], list[dict[str, Any]]]:
    target = normalize_text(city)
    accepted: list[dict[str, Any]] = []
    rejected: list[dict[str, Any]] = []
    for item in items:
        declared_city = item_city(str(item.get("description", "")))
        reason = None
        if not declared_city or normalize_text(declared_city) != target:
            reason = "CITY_MISMATCH_OR_MISSING"
        else:
            try:
                validate_product_url(str(item.get("productUrl", "")))
            except ValueError:
                reason = "INVALID_PRODUCT_URL"

        if reason:
            rejected.append(
                {
                    "gid": item.get("gid"),
                    "itemName": item.get("itemName"),
                    "description": item.get("description"),
                    "category": item.get("category"),
                    "reason": reason,
                }
            )
        else:
            enriched = dict(item)
            enriched["purchaseForm"] = classify_purchase_form(item)
            accepted.append(enriched)
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


def search_page(
    city: str,
    page: int,
    size: int,
    category: str | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    payload: dict[str, Any] = {"keyword": city, "page": page, "size": size}
    if category:
        payload["category"] = category
    if sort:
        payload["sort"] = sort
    return unwrap(post("/v1/products/tna/search", payload)) or {}


def collect_search(
    city: str,
    *,
    size: int = 100,
    max_pages: int = 3,
    category: str | None = None,
    sort: str | None = None,
) -> dict[str, Any]:
    if not 1 <= size <= 100:
        raise ValueError("TNA size must be between 1 and 100")
    if max_pages < 0:
        raise ValueError("max_pages must be 0 (unlimited) or a positive integer")

    page = 1
    raw_items: list[dict[str, Any]] = []
    has_next = False
    reported_total = 0
    while True:
        data = search_page(city, page, size, category, sort)
        raw_items.extend(data.get("items", []))
        reported_total = int(data.get("totalCount", reported_total) or reported_total)
        has_next = bool(data.get("hasNextPage"))
        if not has_next or (max_pages and page >= max_pages):
            break
        page += 1

    deduplicated: dict[str, dict[str, Any]] = {}
    for item in raw_items:
        gid = str(item.get("gid", "")).strip()
        if gid:
            deduplicated[gid] = item
    accepted, rejected = partition_tna_items(list(deduplicated.values()), city)
    return {
        "city": city,
        "items": accepted,
        "discarded": rejected,
        "coverage": {
            "reportedTotal": reported_total,
            "pagesFetched": page,
            "rawItemsFetched": len(raw_items),
            "eligibleItems": len(accepted),
            "completeSearch": not has_next,
            "truncatedByPageLimit": has_next,
        },
    }


def category_entries(data: Any) -> list[dict[str, str]]:
    """Normalize documented and defensively supported category response shapes."""
    if isinstance(data, dict):
        raw = data.get("categories", data.get("items", []))
    else:
        raw = data
    entries: list[dict[str, str]] = []
    for entry in raw or []:
        if isinstance(entry, str):
            entries.append({"name": entry, "value": entry})
        elif isinstance(entry, dict):
            value = str(entry.get("value") or entry.get("code") or entry.get("name") or "").strip()
            name = str(entry.get("name") or entry.get("label") or value).strip()
            if value:
                entries.append({"name": name, "value": value})
    return entries


def collect_category_shelves(
    city: str, *, size: int = 100, max_pages_per_category: int = 1
) -> dict[str, Any]:
    """Collect each official product category separately to reduce popularity bias."""
    raw_categories = unwrap(post("/v1/products/tna/categories", {"city": city})) or []
    categories = category_entries(raw_categories)
    shelves: list[dict[str, Any]] = []
    seen: set[str] = set()
    all_discarded: list[dict[str, Any]] = []
    for category in categories:
        collected = collect_search(
            city,
            size=size,
            max_pages=max_pages_per_category,
            category=category["value"],
            sort=None,
        )
        unique_items = []
        for item in collected["items"]:
            gid = str(item.get("gid", "")).strip()
            if gid and gid not in seen:
                seen.add(gid)
                unique_items.append(item)
        all_discarded.extend(collected["discarded"])
        shelves.append(
            {
                "category": category,
                "items": unique_items,
                "coverage": collected["coverage"],
            }
        )
    return {
        "city": city,
        "shelves": shelves,
        "discarded": all_discarded,
        "coverage": {
            "categoriesReturned": len(categories),
            "categoriesCollected": len(shelves),
            "uniqueEligibleItems": len(seen),
            "completeCategories": bool(shelves) and all(
                shelf["coverage"]["completeSearch"] for shelf in shelves
            ),
        },
    }


def clean_detail(data: dict[str, Any]) -> dict[str, Any]:
    return {
        "gid": data.get("gid"),
        "title": strip_html(str(data.get("title", ""))),
        "description": strip_html(str(data.get("description", ""))),
        "included": [strip_html(str(value)) for value in data.get("included", [])],
        "excluded": [strip_html(str(value)) for value in data.get("excluded", [])],
        "itineraries": [
            {
                "title": strip_html(str(entry.get("title", ""))),
                "description": strip_html(str(entry.get("description", ""))),
            }
            for entry in data.get("itineraries", [])
        ],
    }


def collect_corpus(
    city: str,
    *,
    size: int = 100,
    max_pages: int = 3,
    detail_limit: int = 100,
    category: str | None = None,
) -> dict[str, Any]:
    collected = collect_search(
        city, size=size, max_pages=max_pages, category=category
    )
    items = collected["items"]
    if detail_limit < 0:
        raise ValueError("detail_limit must be 0 (unlimited) or a positive integer")
    selected = items if detail_limit == 0 else items[:detail_limit]
    details: list[dict[str, Any]] = []
    failures: list[dict[str, str]] = []
    for item in selected:
        gid = str(item["gid"])
        try:
            detail = clean_detail(
                unwrap(post("/v1/products/tna/detail", {"gid": gid})) or {}
            )
            detail["productUrl"] = item.get("productUrl")
            detail["category"] = item.get("category")
            details.append(detail)
        except ApiError as exc:
            failures.append({"gid": gid, "error": str(exc)})

    collected["details"] = details
    collected["detailFailures"] = failures
    collected["coverage"].update(
        {
            "detailsRequested": len(selected),
            "detailsReturned": len(details),
            "completeDetails": len(selected) == len(items) and not failures,
            "truncatedByDetailLimit": len(selected) < len(items),
        }
    )
    return collected


def add_common_arguments(parser: argparse.ArgumentParser) -> None:
    parser.add_argument("--pretty", action="store_true", help="Pretty-print JSON")


def build_parser() -> argparse.ArgumentParser:
    parser = argparse.ArgumentParser(description=__doc__)
    sub = parser.add_subparsers(dest="command", required=True)

    p = sub.add_parser("tna-categories")
    p.add_argument("--city", required=True)
    add_common_arguments(p)

    p = sub.add_parser("tna-search")
    p.add_argument("--city", required=True)
    p.add_argument("--category")
    p.add_argument(
        "--sort",
        choices=["price_asc", "price_desc", "review_score_desc", "selling_count_desc"],
    )
    p.add_argument("--page", type=int, default=1)
    p.add_argument("--size", type=int, default=100)
    add_common_arguments(p)

    p = sub.add_parser("tna-collect")
    p.add_argument("--city", required=True)
    p.add_argument("--category")
    p.add_argument("--size", type=int, default=100)
    p.add_argument("--max-pages", type=int, default=3, help="0 means all pages")
    p.add_argument("--with-details", action="store_true")
    p.add_argument("--detail-limit", type=int, default=100, help="0 means all eligible items")
    add_common_arguments(p)

    p = sub.add_parser("tna-shelves")
    p.add_argument("--city", required=True)
    p.add_argument("--size", type=int, default=100)
    p.add_argument(
        "--max-pages-per-category", type=int, default=1, help="0 means all pages"
    )
    add_common_arguments(p)

    p = sub.add_parser("tna-detail")
    p.add_argument("--gid", required=True)
    add_common_arguments(p)

    p = sub.add_parser("tna-options")
    p.add_argument("--gid", required=True)
    p.add_argument("--date", required=True)
    add_common_arguments(p)

    p = sub.add_parser("url-check")
    p.add_argument("--url", required=True)
    p.add_argument("--timeout", type=int, default=15)
    add_common_arguments(p)

    return parser


def run(args: argparse.Namespace) -> dict[str, Any]:
    if args.command == "tna-categories":
        return {"data": unwrap(post("/v1/products/tna/categories", {"city": args.city}))}

    if args.command == "tna-search":
        if args.page < 1:
            raise ValueError("TNA page starts at 1")
        data = search_page(args.city, args.page, args.size, args.category, args.sort)
        accepted, rejected = partition_tna_items(data.get("items", []), args.city)
        filtered = dict(data)
        filtered["items"] = accepted
        return {"city": args.city, "data": filtered, "discarded": rejected}

    if args.command == "tna-collect":
        if args.with_details:
            return collect_corpus(
                args.city,
                size=args.size,
                max_pages=args.max_pages,
                detail_limit=args.detail_limit,
                category=args.category,
            )
        return collect_search(
            args.city,
            size=args.size,
            max_pages=args.max_pages,
            category=args.category,
        )

    if args.command == "tna-shelves":
        return collect_category_shelves(
            args.city,
            size=args.size,
            max_pages_per_category=args.max_pages_per_category,
        )

    if args.command == "tna-detail":
        data = unwrap(post("/v1/products/tna/detail", {"gid": args.gid})) or {}
        return {"data": clean_detail(data)}

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

    if args.command == "url-check":
        if not 1 <= args.timeout <= 60:
            raise ValueError("timeout must be between 1 and 60 seconds")
        return check_product_url(args.url, timeout=args.timeout)

    raise ValueError(f"Unsupported command: {args.command}")


def main() -> int:
    parser = build_parser()
    args = parser.parse_args()
    try:
        result = run(args)
        print(json.dumps(result, ensure_ascii=False, indent=2 if args.pretty else None))
        return 0
    except (ApiError, ValueError) as exc:
        print(json.dumps({"error": str(exc)}, ensure_ascii=False), file=sys.stderr)
        return 2


if __name__ == "__main__":
    raise SystemExit(main())
